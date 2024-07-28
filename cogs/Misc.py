import os
from dotenv import load_dotenv
import discord
from discord import app_commands
from discord.ext import commands
from discord.ext.commands import Context

load_dotenv()
GUILD_ID = int(os.getenv("GUILD_ID"))


class Misc(commands.Cog, name="misc"):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.hybrid_command(name="ping", description="Check the bot's latency.")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def ping(self, ctx: Context) -> None:
        await ctx.send(f"Pong! {round(self.bot.latency * 1000)}ms")

    @commands.hybrid_command(name="git", description="Sends the GitHub repository link.")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def git(self, ctx: Context) -> None:
        await ctx.send("https://github.com/MessyPrincy/Upsilon")


async def setup(bot) -> None:
    await bot.add_cog(Misc(bot))
