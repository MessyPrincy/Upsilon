import os

import discord
from discord import app_commands
from discord.ext import commands
from discord.ext.commands import Context
from dotenv import load_dotenv

load_dotenv()
GUILD_ID = int(os.getenv("GUILD_ID"))


class Utils(commands.Cog, name="utils"):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.hybrid_command(name="joinvc", description="Join the voice channel.")
    async def join_vc(self, ctx: Context) -> None:
        if ctx.author.voice:
            channel = ctx.author.voice.channel
            try:
                await channel.connect()
                await ctx.send(f"Joined {channel.name}")
            except discord.ClientException:
                await ctx.send("Already connected to a voice channel.")
            except discord.HTTPException as e:
                await ctx.send(f"Failed to connect: {e}")
        else:
            await ctx.send("You are not in a voice channel.")

    @commands.hybrid_command(name="leavevc", description="Leave the voice channel.")
    async def leave_vc(self, ctx: Context) -> None:
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
            await ctx.send("Left the voice channel.")
        else:
            await ctx.send("I am not connected to a voice channel.")


async def setup(bot) -> None:
    await bot.add_cog(Utils(bot))
