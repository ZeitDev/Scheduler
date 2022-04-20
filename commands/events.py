import config

from nextcord.ext import commands
from functions import _events

class Events(commands.Cog):
    @commands.command(usage='Heute 18:00 / .create Fr 18 Uhr / .create 12.12. 18:00')
    async def event(self, ctx, *args):
        """Creation of an event"""
        await ctx.message.delete()
        await _events.Events().Initialize(ctx.channel, args)
    
    @commands.command(usage='')
    async def automatic(self, ctx, *args):
        """Toggle automatic weekly event creation"""
        await ctx.message.delete()
        if config.VariableDict['automatic_event_creation']: 
            config.VariableDict['automatic_event_creation'] = False
            await ctx.channel.send(f'Automatic weekly event creation is now off')
        else: 
            config.VariableDict['automatic_event_creation'] = True
            await ctx.channel.send(f'Automatic weekly event creation is now on')
        

    @commands.command(usage='18:00')
    async def setdefaulttime(self, ctx, *args):
        """Set default time for automatic weekly event creation"""
        await ctx.message.delete()
        if len(list(args)) == 0: return
        config.VariableDict['default_event_time'] = list(args)[0]

        default = config.VariableDict['default_event_time']
        await ctx.channel.send(f'Default time for automatic event creation set at {default}')

def setup(bot):
    bot.add_cog(Events(bot))