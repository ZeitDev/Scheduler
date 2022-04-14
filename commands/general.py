from nextcord.ext import commands

class General(commands.Cog):
    """General commands without a specific category"""
    def __init__(self, bot):
        self.bot = bot

    @commands.command(usage='')
    async def hello(self, ctx):
        """Testing command"""
        await ctx.message.delete()
        member = ctx.author
        await ctx.channel.send(f'Hello {member}!')     

def setup(bot):
    bot.add_cog(General(bot))