import config

from nextcord.ext import commands
from functions import _statistics

class Statistics(commands.Cog):
    """All commands about the event functionality"""
    def __init__(self, bot):
        self.bot = bot

    @commands.command(usage='')
    async def stats(self, ctx):
        """Statistics"""
        await ctx.message.delete()
        await _statistics.Stats().ShowStats(ctx)

    @commands.command(usage='minutes @user => .add 60 @Shiro')
    async def wasted(self, ctx, *args):
        """Wasted Lifetime Tracking"""
        await _statistics.Stats().AddTimeToWastedTimeLeaderboard(ctx, args)

def setup(bot):
    bot.add_cog(Statistics(bot))