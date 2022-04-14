import time
import config
import nextcord
import asyncio
import datetime
import warnings

from dateparser.search import search_dates as parse
from functions import _statistics

class Events():
    def __init__(self):
        self.SettingsDict = config.SettingsDict
        self.bot = config.VariableDict['bot']

    async def InitializeEvent(self, channel, args):
        if channel.id != self.SettingsDict['appointment_channel']: return

        event_title = (' ').join(args)
        date = ParseDate(args)

        error = await CheckForValidArguments(channel, args, date)
        if error == 1: return

        await MentionMembers(channel)
        await self.CreateEvent(channel, event_title, date)

    async def CreateEvent(self, channel, event_title, date):
        print('Creating new event')
        num_members = len(GatherAllMembers())
        description = f'''
        {event_title}
        missing votes: {num_members}/{num_members} | reminder in X | {date.strftime('%d.%m. %H:%M')}
        '''
        embed = nextcord.Embed(description=description, color=config.SettingsDict['embed_color'])
        message = await channel.send(embed=embed)

        time_to_event = time.mktime(date.timetuple()) - int(time.time())

        EventData = {
            'message': message,
            'event_title': event_title,
            'date': date,
            'start_time': int(time.time()),
            'confirmed': False,
            'reminder_times': [(time_to_event/3)*2, time_to_event/3, self.SettingsDict['reminder_uncertain'], 0],
            'reminder_status': 0
        }
        self.LoopEvent(EventData)

    def LoopEvent(self, EventData):
        try:
            loop = asyncio.get_event_loop()
            asyncio.ensure_future(self.TrackEmbed(EventData))
            loop.run_until_complete
            loop.close()
        except:
            pass

    async def TrackEmbed(self, EventData):
        while True:
            message = await FetchMessage(EventData['message'])
            if message == 1: return 

            EventMemberData = await GatherReactionMembers(message)
            if EventMemberData == 1: return

            if not EventData['confirmed']:
                await CheckEventConfirmation(EventData, EventMemberData)
            
            reminder_passed = await CheckReminderTimePassed(EventData)
            if reminder_passed: 
                await SendReminderToMembers(EventData, EventMemberData)
                await UpdateStats(EventData, EventMemberData)

            await UpdateEmbed(EventData, EventMemberData)

            finished = await CheckIfFinished(EventData, EventMemberData)
            if finished: return

            await asyncio.sleep(self.SettingsDict['update'])

    async def AutomaticWeeklyEventCreation(self):
        channel = config.VariableDict['bot'].get_channel(config.SettingsDict['appointment_channel'])
        
        for i in range(5):
            args = [SwitchWeekday(i), config.VariableDict['default_event_time']]
            await self.InitializeEvent(channel, args)
            await asyncio.sleep(1)

# Helper Functions
async def CheckForValidArguments(channel, args, date):
    args = list(args)

    # Check for empty arguments
    if len(args) == 0:
        await channel.send('Missing arguments -> canceling event creation', delete_after=5)
        return 1

    # Can not parse date
    
    if date is None:
        await channel.send('can not detect event date -> canceling event creation', delete_after=5)
        return 1

    # Check for date in the past
    if int(time.mktime(date.timetuple()) - time.time()) <= 0:
        await channel.send('detected date in the past -> canceling event creation', delete_after=5)
        return 1

    return 0

def ParseDate(args):
    # detect today, lazy datetime, single digits and german date specification
    weekday_num = datetime.datetime.today().weekday()
    for i in range(len(args)):
        if args[i].lower() in SwitchWeekday(weekday_num):
            args[i] = 'heute'
        if args[i].lower() == 'uhr':
            if not ':' in args[i-1]:
                args[i-1] += ':00'
        if args[i].isdigit():
            if 1 <= int(args[i]) <= 9:
                args[i] = 'XXX'
    args = [arg.replace('.', '-') for arg in args]
    
    settings={'PREFER_DATES_FROM': 'future', 'DATE_ORDER': 'DMY', 'PREFER_LOCALE_DATE_ORDER': False, 'TIMEZONE': 'Europe/Berlin'}#, 'RETURN_AS_TIMEZONE_AWARE': True}
    matches = parse((' ').join(args), languages=['de'], settings=settings)

    if matches is not None: return matches[-1][1]

def SwitchWeekday(argument):
    switcher = {
        0: 'montag',
        1: 'dienstag',
        2: 'mittwoch',
        3: 'donnerstag',
        4: 'freitag',
        5: 'samstag',
        6: 'sonntag',
    }
    return switcher.get(argument, "Invalid day")

async def MentionMembers(channel):
    last_message_timedelta = int(time.time()) - config.VariableDict['last_message_time']
    if last_message_timedelta > config.SettingsDict['mention']:
        mention_role = config.SettingsDict['role_members']
        await channel.send(f'<@&{mention_role}>')
        config.VariableDict['last_message_time'] = int(time.time())

def GatherAllMembers():
    guild = config.VariableDict['bot'].get_guild(config.SettingsDict['server_id'])
    for role in guild.roles:
        if role.id == config.SettingsDict['role_reminder']:
            return role.members

async def FetchMessage(msg):
    try:
        message = await msg.channel.fetch_message(msg.id)
        return message
    except Exception as e:
        await msg.channel.send('Please do not delete bot messages. Use ❌ for deleting an active event.\nThis message is deleting itself in 300 seconds!', delete_after=300)
        warnings.warn('Bot message got deleted')
        return 1

async def GatherReactionMembers(message):
    EventMemberData = {
        'members_reacted': [],
        'members_uncertain': [],
        'members_confirmed': [],
        'members_canceled': []
    }

    for reaction in message.reactions:
        if reaction.emoji == '❌':
            embed = nextcord.Embed(description='Event deleted. Embed deleting itself in 5 seconds.', color=0xFF0000)
            await message.edit(embed=embed, delete_after=5)
            return 1

        async for user in reaction.users():
                EventMemberData['members_reacted'].append(user)

        if reaction.emoji != '🤏' or reaction.emoji != '👎':
            async for user in reaction.users():
                EventMemberData['members_confirmed'].append(user)

        if reaction.emoji == '🤏':
            async for user in reaction.users():
                EventMemberData['members_uncertain'].append(user)
        
        if reaction.emoji == '👎':
            async for user in reaction.users():
                EventMemberData['members_canceled'].append(user)

    EventMemberData['members_missing'] = [x for x in GatherAllMembers() if x not in EventMemberData['members_reacted']]

    return EventMemberData  

async def CheckEventConfirmation(EventData, EventMemberData):
    if len(EventMemberData['members_confirmed']) >= 5:
        ConfirmedEventData = {'event_date': EventData['date'], 'members_confirmed': EventMemberData['members_confirmed']}
        config.VariableDict['confirmed_events'].append(ConfirmedEventData)

        EventData['confirmed'] = True
        await SendEventConfirmation(EventData, EventMemberData)

async def SendEventConfirmation(EventData, EventMemberData):
    guild = config.VariableDict['bot'].get_guild(config.SettingsDict['server_id'])

    title = 'FlexQ'
    event_entity = nextcord.ScheduledEventEntityType.external
    event_metadata = nextcord.EntityMetadata(location='Summoners Rift')
    event_start_time = EventData['date'] - datetime.timedelta(hours=2)
    event_end_time = EventData['date'] 
    event_description = ''
    for member in EventMemberData['members_confirmed']:
        event_description += member.display_name

    await guild.create_scheduled_event(name=title, entity_type=event_entity ,start_time=event_start_time, metadata=event_metadata, end_time=event_end_time, description=event_description)

    #alert_channel = bot.get_channel(config.SettingsDict['alert_channel'])
    #weekdays = ['Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa', 'So']
    #members_confirmed_string = ''
    #for member in members_confirmed:
    #    members_confirmed_string += member.display_name + '\n'
    #await alert_channel.send(f"```\n{len(members_confirmed)} at {weekdays[date.weekday()]} {date.strftime('%H:%M')}\n{members_confirmed_string}\n```")
        
async def TimeToNextReminder(EventData):
    reminder_times = EventData['reminder_times']
    for reminder_time in reminder_times:
        time_to_event = time.mktime(EventData['date'].timetuple()) - int(time.time())
        reminder_delta = time_to_event - reminder_time
        if reminder_delta > 0: return reminder_delta
    return

async def UpdateEmbed(EventData, EventMemberData):
    event_title = EventData['event_title']
    num_members = len(GatherAllMembers())
    num_members_missing = len(EventMemberData['members_missing'])
    reminder_status = EventData['reminder_status']

    next_reminder = await TimeToNextReminder(EventData)
    if next_reminder != None and (reminder_status == 0 or reminder_status == 1): reminder_string = f'next reminder in {round((next_reminder/3600), 2)} h'
    elif next_reminder != None: reminder_string = f'next reminder for uncertain in {round((next_reminder/3600), 2)} h'
    else: reminder_string = 'no reminder remaining'

    description = f'''
    {event_title}
    missing votes: {num_members_missing}/{num_members} | {reminder_string} | {EventData['date'].strftime('%d.%m. %H:%M')}
    '''
    embed = nextcord.Embed(description=description, color=config.SettingsDict['embed_color'])
    await EventData['message'].edit(embed=embed)    

async def CheckReminderTimePassed(EventData):
    reminder_times = EventData['reminder_times']
    time_to_event = time.mktime(EventData['date'].timetuple()) - int(time.time())
    reminder_delta = time_to_event - reminder_times[EventData['reminder_status']]

    if reminder_delta < 0 and EventData['reminder_status'] <= 2:
        EventData['reminder_status'] += 1
        if time_to_event > config.SettingsDict['reminder_protection']:
            return True
    return

async def SendReminderToMembers(EventData, EventMemberData):
    event_title = EventData['event_title']
    channel = EventData['message'].channel
    
    if EventData['reminder_status'] == 1 or EventData['reminder_status'] == 2:
        members = EventMemberData['members_missing']
        message_content = f'Missing vote on event: **{event_title}** in {channel.mention}'
    else:
        members = EventMemberData['members_uncertain']
        message_content = f'Remaining 🤏 on event: **{event_title}** in {channel.mention}'

    for member in members:
        if not member.bot: await member.send(message_content)
        await asyncio.sleep(1)

async def UpdateStats(EventData, EventMemberData):
    if EventData['reminder_status'] == 1 or EventData['reminder_status'] == 2: members = EventMemberData['members_missing']
    else: members = EventMemberData['members_uncertain']

    _statistics.Stats().AddPointToReminderLeaderboard(members)

async def CheckIfFinished(EventData, EventMemberData):
    members_missing = EventMemberData['members_missing']
    members_uncertain = EventMemberData['members_uncertain']

    if len(members_missing) == 0 and len(members_uncertain) == 0:
        print('Finished event successfully')
        event_title = EventData['event_title']

        embed = nextcord.Embed(description=event_title, color=0x00FF00)
        await EventData['message'].edit(embed=embed) 
        return True


    if int(time.mktime(EventData['date'].timetuple()) - time.time()) > config.SettingsDict['event_finish']: return
    else:
        print(f'Finished event with {len(members_missing)} missing votes and {len(members_uncertain)} uncertain votes')

        event_title = EventData['event_title']
        embed = nextcord.Embed(description=event_title, color=0xFF0000)
        await EventData['message'].edit(embed=embed)

        time_of_creation = int(time.mktime(EventData['date'].timetuple()) - EventData['start_time'])
        if time_of_creation > config.SettingsDict['reminder_protection']:
            _statistics.Stats().AddPointToReminderLeaderboard(members_missing)
            _statistics.Stats().AddPointToReminderLeaderboard(members_uncertain)
        
        return True
