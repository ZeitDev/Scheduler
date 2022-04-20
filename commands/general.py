from nextcord.ext import commands

class General(commands.Cog):
    @commands.command(usage='')
    async def hello(self, ctx):
        """Testing command"""
        await ctx.message.delete()
        member = ctx.author
        await ctx.channel.send(f'Hello {member}!')     

def setup(bot):
    bot.add_cog(General(bot))