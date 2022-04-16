import config

from nextcord.ext import commands
from functions import _statistics

class Statistics(commands.Cog):
    """All commands about statistics"""
    def __init__(self, bot):
        self.bot = bot

    @commands.command(usage='')
    async def stats(self, ctx):
        """Display all statistics"""
        await ctx.message.delete()
        await _statistics.Stats().ShowStats(ctx)

    @commands.command(usage='minutes @user => .wasted 60 @Shiro')
    async def wasted(self, ctx, *args):
        """Adds time to the wasted time account"""
        await _statistics.Stats().AddTimeToWastedTimeLeaderboard(ctx, args)

def setup(bot):
    bot.add_cog(Statistics(bot))