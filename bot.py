import asyncio
import time

import discord
from discord.ext import commands, tasks
from discord.ext.commands import Context
from dotenv import load_dotenv
import os
import logging
import random
import aiosqlite

intents = discord.Intents.default()
intents.message_content = True

DATABASE_FILE = "data/user_memories.db"
os.makedirs(os.path.dirname(DATABASE_FILE), exist_ok=True)


class LoggingFormatter(logging.Formatter):
    black = "\x1b[30m"
    red = "\x1b[31m"
    green = "\x1b[32m"
    yellow = "\x1b[33m"
    blue = "\x1b[34m"
    gray = "\x1b[38m"
    reset = "\x1b[0m"
    bold = "\x1b[1m"

    COLORS = {
        logging.DEBUG: gray + bold,
        logging.INFO: blue + bold,
        logging.WARNING: yellow + bold,
        logging.ERROR: red,
        logging.CRITICAL: red + bold,
    }

    def format(self, record):
        log_color = self.COLORS[record.levelno]
        formatting = "(black){asctime}(reset) (levelcolor){levelname:<8}(reset) (green){name}(reset) {message}"
        formatting = formatting.replace("(black)", self.black + self.bold)
        formatting = formatting.replace("(reset)", self.reset)
        formatting = formatting.replace("(levelcolor)", log_color)
        formatting = formatting.replace("(green)", self.green + self.bold)
        formatter = logging.Formatter(formatting, "%Y-%m-%d %H:%M:%S", style="{")
        return formatter.format(record)


logger = logging.getLogger("Upsilon")
logger.setLevel(logging.INFO)

console_handler = logging.StreamHandler()
console_handler.setFormatter(LoggingFormatter())

file_handler = logging.FileHandler(filename="discord.log", encoding="utf-8", mode="w")
file_handler_formatter = logging.Formatter(
    "[{asctime}] [{levelname:<8}] {name}: {message}", "%Y-%m-%d %H:%M:%S", style="{"
)
file_handler.setFormatter(file_handler_formatter)

logger.addHandler(console_handler)
logger.addHandler(file_handler)


async def setup_database():
    async with aiosqlite.connect(DATABASE_FILE) as db:
        await db.execute("""
                CREATE TABLE IF NOT EXISTS memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    priority INTEGER,
                    user_id TEXT,
                    memory TEXT,
                    context TEXT
                )
                """)
        await db.execute("""
                CREATE TABLE IF NOT EXISTS chat_channels (
                    guild_id TEXT PRIMARY KEY,
                    channel_id TEXT
                )
                """)
        await db.commit()


async def main():
    await setup_database()
    logger.info("Database setup complete.")


class MyBot(commands.Bot):
    def __init__(self) -> None:
        super().__init__(
            command_prefix='.',
            intents=intents,
            help_command=None
        )
        self.logger = logger
        self.commands_synced = False
        self.last_sync_time = 0
        self.sync_interval = 3600  # Sync every hour

    async def load_cogs(self) -> None:
        for file in os.listdir(f"{os.path.realpath(os.path.dirname(__file__))}/cogs"):
            if file.endswith(".py"):
                extension = file[:-3]
                try:
                    await self.load_extension(f"cogs.{extension}")
                    self.logger.info(f"Loaded cog '{extension}'")
                except Exception as e:
                    exception = f"{type(e).__name__}: {e}"
                    self.logger.error(
                        f"Failed to load cog {extension}\n{exception}"
                    )

    @tasks.loop(minutes=1.0)
    async def status(self) -> None:
        statuses = ["with py-cord", "with you humans", "to win", "on a linux computer"]
        await self.change_presence(activity=discord.Game(name=random.choice(statuses)))

    @status.before_loop
    async def before_status(self) -> None:
        await self.wait_until_ready()

    async def on_ready(self):
        self.logger.info(f'Logged in as {self.user}')
        synced = await bot.tree.sync()
        self.logger.info(f"Commands synced: {synced}")
        await self.load_cogs()
        await main()
        self.status.start()

    async def sync_commands_with_backoff(self):
        current_time = time.time()
        if current_time - self.last_sync_time < self.sync_interval:
            self.logger.info("Sync interval not reached, skipping sync.")
            return

        delay = 1
        max_delay = 60

        while True:
            try:
                guild_id = os.getenv('GUILD_ID')
                guild = discord.Object(id=guild_id)
                self.tree.clear_commands(guild=guild)
                await self.tree.sync()
                self.logger.info("Commands synced successfully.")
                self.last_sync_time = time.time()
                break
            except discord.HTTPException as e:
                if e.status == 429:  # Rate limited
                    retry_after = int(e.response.headers.get("Retry-After", delay))
                    self.logger.warning(f"Rate limited. Retrying in {retry_after} seconds.")
                    await asyncio.sleep(retry_after)
                    delay = min(delay * 2, max_delay)  # Exponential backoff
                else:
                    self.logger.error(f"Failed to sync commands: {e}")
                    break

    async def on_command_completion(self, context: Context) -> None:
        full_command_name = context.command.qualified_name
        split = full_command_name.split(" ")
        executed_command = str(split[0])
        if context.guild is not None:
            self.logger.info(
                f"Executed {executed_command} command in {context.guild.name} (ID: {context.guild.id}) by {context.author} (ID: {context.author.id})"
            )
        else:
            self.logger.info(
                f"Executed {executed_command} command by {context.author} (ID: {context.author.id}) in DMs"
            )

    async def on_command_error(self, context: Context, error) -> None:
        if isinstance(error, commands.CommandOnCooldown):
            minutes, seconds = divmod(error.retry_after, 60)
            hours, minutes = divmod(minutes, 60)
            hours = hours % 24
            embed = discord.Embed(
                description=f"**Please slow down** - You can use this command again in {f'{round(hours)} hours' if round(hours) > 0 else ''} {f'{round(minutes)} minutes' if round(minutes) > 0 else ''} {f'{round(seconds)} seconds' if round(seconds) > 0 else ''}.",
                color=0xE02B2B,
            )
            await context.send(embed=embed)
        elif isinstance(error, commands.NotOwner):
            embed = discord.Embed(
                description="You are not the owner of the bot!", color=0xE02B2B
            )
            await context.send(embed=embed)
            if context.guild:
                self.logger.warning(
                    f"{context.author} (ID: {context.author.id}) tried to execute an owner only command in the guild {context.guild.name} (ID: {context.guild.id}), but the user is not an owner of the bot."
                )
            else:
                self.logger.warning(
                    f"{context.author} (ID: {context.author.id}) tried to execute an owner only command in the bot's "
                    f"DMs, but the user is not an owner of the bot."
                )
        elif isinstance(error, commands.MissingPermissions):
            embed = discord.Embed(
                description="You are missing the permission(s) `"
                            + ", ".join(error.missing_permissions)
                            + "` to execute this command!",
                color=0xE02B2B,
            )
            await context.send(embed=embed)
        elif isinstance(error, commands.BotMissingPermissions):
            embed = discord.Embed(
                description="I am missing the permission(s) `"
                            + ", ".join(error.missing_permissions)
                            + "` to fully perform this command!",
                color=0xE02B2B,
            )
            await context.send(embed=embed)
        elif isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(
                title="Error!",
                description=str(error).capitalize(),
                color=0xE02B2B,
            )
            await context.send(embed=embed)
        else:
            raise error


load_dotenv()
bot = MyBot()
bot.run(os.getenv('DISCORD_TOKEN'))

# Mostly copied from https://github.com/kkrypt0nn/Python-Discord-Bot-Template?tab=readme-ov-file by kkrypt0nn
