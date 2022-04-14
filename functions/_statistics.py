import json
import config
import nextcord

class Stats():
    def CheckForExisitingStatsFile(self):
        try:
            print('Loading stats.json')
            json.load(open("stats.json"))
        except:
            print('No stats found. Creating new one.')
            self.InitializeAll()

    def ResetUptime(self):
        stats = json.load(open("stats.json"))
        stats['server_stats']['uptime'] = 0
        json.dump(stats, open("stats.json", "w"))

    def InitializeAll(self):
        reminder_leaderboard, wasted_time_leaderboard = InitLeaderboards(config.VariableDict['bot'])
        server_stats = {'uptime': 0, 'server_cost': 0}
        
        stats = {
            'reminder_leaderboard': reminder_leaderboard,
            'wasted_time_leaderboard': wasted_time_leaderboard,
            'server_stats': server_stats}

        json.dump(stats, open('stats.json', 'w'))

    async def ShowStats(self, ctx):
        embed = CreateStatsEmbed()
        await ctx.channel.send(embed=embed)

    def AddPointToReminderLeaderboard(self, members):
        stats = json.load(open('stats.json'))

        for member in members:
            stats['reminder_leaderboard'][f'{member.display_name}'] += 1

        json.dump(stats, open('stats.json', 'w'))

    async def AddTimeToWastedTimeLeaderboard(self, ctx, args):
        stats = json.load(open('stats.json'))

        member = ctx.message.mentions[0]

        try:
            minutes = int(args[0])
        except:
            await ctx.channel.send(f'Error: can not parse the number {args[0]}')
            return

        stats['wasted_time_leaderboard'][f'{member.display_name}'] += minutes*60
        await ctx.channel.send(f'Adding {minutes} minutes to {member.display_name}')

        json.dump(stats, open('stats.json', 'w'))

    async def AddingServerStats(self, stat, value):
        stats = json.load(open("stats.json"))
        stats['server_stats'][stat] += value
        json.dump(stats, open("stats.json", "w"))

# Helper Functions
def InitLeaderboards(bot):
    guild = bot.get_guild(config.SettingsDict['server_id'])
    for role in guild.roles:
        if role.id == config.SettingsDict['role_members']:
            members = role.members

    reminder_leaderboard = {}
    wasted_time_leaderboard = {}
    for member in members:
        reminder_leaderboard[f'{member.display_name}'] = 0
        wasted_time_leaderboard[f'{member.display_name}'] = 0

    return reminder_leaderboard, wasted_time_leaderboard

def CreateStatsEmbed():
    StatsDict = FormatStats()

    embed = nextcord.Embed(title='Statistics', color=0xFF9B00)

    embed.add_field(name='Reminders received', value=StatsDict['reminder_members'], inline=True)
    embed.add_field(name='\u200b', value=StatsDict['reminder_scores'], inline=True)
    embed.add_field(name='\u200b', value='\u200b', inline=False)

    embed.add_field(name='Time of others wasted', value=StatsDict['wasted_time_members'], inline=True)
    embed.add_field(name='\u200b', value=StatsDict['wasted_time_scores'], inline=True)
    embed.add_field(name='\u200b', value='\u200b', inline=False)

    embed.add_field(name='Server Stats', value=StatsDict['server_stats_titles'], inline=True)
    embed.add_field(name='\u200b', value=StatsDict['server_stats_values'], inline=True)

    return embed

def FormatStats():
    stats = json.load(open('stats.json'))
    reminder_leaderboard = dict(sorted(stats['reminder_leaderboard'].items(), key=lambda item: item[1], reverse=True))
    wasted_time_leaderboard = dict(sorted(stats['wasted_time_leaderboard'].items(), key=lambda item: item[1], reverse=True))
    server_stats = stats['server_stats']

    StatsDict = {
        'reminder_members': '',
        'reminder_scores': '',
        'wasted_time_members': '',
        'wasted_time_scores': '',
        'server_stats_titles': '',
        'server_stats_values': '',
    }

    for key, value in reminder_leaderboard.items():
        StatsDict['reminder_members'] += (key + '\n')
        StatsDict['reminder_scores'] += (str(value) + '\n')

    for key, value in wasted_time_leaderboard.items():
        StatsDict['wasted_time_members'] += (key + '\n')
        StatsDict['wasted_time_scores'] += (ConvertSecondsToReadable(value, skips=1) + '\n')


    StatsDict['server_stats_titles'] = 'Uptime' + '\n' + 'Server Costs'
    StatsDict['server_stats_values'] = str(ConvertSecondsToReadable(int(server_stats['uptime']))) + '\n' + ConvertCentsToReadable(server_stats['server_cost'])

    return StatsDict

def ConvertSecondsToReadable(seconds, skips=0):
    intervals = (
        ('weeks', 604800),  # 60 * 60 * 24 * 7
        ('days', 86400),    # 60 * 60 * 24
        ('hours', 3600),    # 60 * 60
        ('minutes', 60),
        #('seconds', 1),
    )

    result = []
    if seconds == 0: return 'none'
    else:
        for name, count in intervals[skips:]:
            value = seconds // count
            if value:
                seconds -= value * count
                if value == 1:
                    name = name.rstrip('s')
                result.append("{} {}".format(value, name))
        return ', '.join(result)

def ConvertCentsToReadable(cents):
    return '{:,.2f} €'.format(cents/100)
