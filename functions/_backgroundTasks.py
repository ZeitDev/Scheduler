import time
import datetime
import config
import asyncio

from functions import _statistics
from functions import _events

class BackgroundTasks():
    def __init__(self):
        self.end_of_week = False
        self.triggered = False

    def initialize(self):
        try:
            loop = asyncio.get_event_loop()
            asyncio.ensure_future(BackgroundTasks().TriggerAutomaticEventCreation())
            asyncio.ensure_future(BackgroundTasks().AlertStartingEvent())
            asyncio.ensure_future(BackgroundTasks().UpdateServerCost())
            asyncio.ensure_future(BackgroundTasks().UpdateServerUptime())
            loop.run_forever()
            loop.close()
        except:
            pass

    async def TriggerAutomaticEventCreation(self):
        while True:
            if datetime.datetime.today().weekday() == 0: self.triggered = False
            if datetime.datetime.today().weekday() == 6 and not self.triggered:
                self.end_of_week = True
                self.triggered = True

            if self.end_of_week and config.VariableDict['automatic_event_creation']:
                await _events.Events().AutomaticWeeklyEventCreation()
                self.end_of_week = False
            

            await asyncio.sleep(3600)

    async def AlertStartingEvent(self):
        while True:
            confirmed_events = config.VariableDict['confirmed_events']
            
            for i in range(len(confirmed_events)):
                ConfirmedEventData = confirmed_events[i]
                event_time = time.mktime(ConfirmedEventData['event_date'].timetuple())
                
                if int(event_time - time.time()) < config.SettingsDict['event_finish']:
                    alert_channel = config.VariableDict['bot'].get_channel(config.SettingsDict['alert_channel'])

                    members_confirmed_string = ''
                    for member in ConfirmedEventData['members_confirmed']:
                        members_confirmed_string += member.display_name + '\n'
                    await alert_channel.send(f"```\nUpcoming Event in 15min\n{members_confirmed_string}\n```")

                    del config.VariableDict['confirmed_events'][i]

            await asyncio.sleep(60)

    async def UpdateServerCost(self):
        while True:
            price = 42

            cost = (price/2628000) * 3600
            await _statistics.Stats().AddingServerStats('server_cost', cost)

            await asyncio.sleep(3600)

    async def UpdateServerUptime(self):
        while True:
            await _statistics.Stats().AddingServerStats('uptime', 900)
            await asyncio.sleep(900)