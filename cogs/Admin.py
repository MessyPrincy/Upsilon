from discord.ext import commands

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='reload', hidden=True)
    @commands.is_owner()
    async def reload_command(self, ctx):
        try:
            cogs_to_reload = [c for c in self.bot.cogs if c != 'Admin']
            reloaded_cogs = []

            for cog_name in cogs_to_reload:
                cog = self.bot.get_cog(cog_name)
                if cog and hasattr(cog, '__cog_name__'):
                    extension = cog.__module__
                    await self.bot.reload_extension(extension)
                    reloaded_cogs.append(cog_name)

            if reloaded_cogs:
                await ctx.send(f"Reloaded cogs: {', '.join(reloaded_cogs)}")
            else:
                await ctx.send("No cogs were reloaded.")
        except Exception as e:
            await ctx.send(f"Error reloading cogs: {e}")

async def setup(bot):
    await bot.add_cog(Admin(bot))