# import
import os
import time
import json
import nextcord
import warnings

from dotenv import load_dotenv
from nextcord.ext import commands

import config
from functions import _statistics
from functions import _backgroundTasks

# Initialize
try:
    os.environ['TZ'] = 'UTC-2' #'Europe/Berlin' 'change to 'UTC-1' at winter time'
    time.tzset()
except:
    warnings.warn('Could not change timezone')

load_dotenv()
token = os.getenv('nextcord_token')
prefix = config.prefix

intents = nextcord.Intents.default()
intents.members = True

description = '''
Bot zur Terminerstellung und -verfolgung.
- Rolle 'Terminerinnerung' kann für Urlaub entfernt werden.
'''

bot = commands.Bot(command_prefix=commands.when_mentioned_or(prefix), description=description, intents=intents)
config.VariableDict['bot'] = bot

print('> Loading Commands')
for filename in os.listdir('./commands'):
    if filename.endswith('.py'):
        bot.load_extension(f'commands.{os.path.splitext(filename)[0]}')
        print(f'{os.path.splitext(filename)[0]} loaded')
print()


# main
@bot.event
async def on_ready():
    print(f'> Starting nextcord Bot = {bot.user}')
    print('-'*40)
    await bot.change_presence(activity=nextcord.Activity(type=nextcord.ActivityType.watching, name=f'{prefix}help'))
    if config.VariableDict['first_startup']:
        _statistics.Stats().CheckForExisitingStatsFile()
        _statistics.Stats().ResetUptime()
        _backgroundTasks.BackgroundTasks().initialize()

        config.VariableDict['first_startup'] = False

bot.run(token)