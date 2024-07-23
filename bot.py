import discord
from discord.ext import commands, tasks
import os
import random
import platform
from dotenv import load_dotenv
import logging

CYAN = '\033[96m'
RED = '\033[91m'
RESET = '\033[0m'

class CustomFormatter(logging.Formatter):
    """Custom logging formatter to add colors based on log level."""
    
    def format(self, record):
        if record.levelno == logging.INFO:
            prefix = CYAN
        elif record.levelno >= logging.ERROR:
            prefix = RED
        else:
            prefix = RESET
        # Original format
        original_format = super().format(record)
        # Reset color at the end
        return f"{prefix}{original_format}{RESET}"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('Upsilon')
logger.propagate = False
handler = logging.StreamHandler()
handler.setFormatter(CustomFormatter('%(levelname)s - %(message)s'))
logger.addHandler(handler)

intents = discord.Intents.default()
intents.message_content = True

class MyBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logger

    async def load_cogs(self):
        for file in os.listdir(f"{os.path.realpath(os.path.dirname(__file__))}/cogs"):
            if file.endswith(".py"):
                extension = file[:-3]
                try:
                    await self.load_extension(f"cogs.{extension}")
                    self.logger.info(f"Loaded extension '{extension}'")
                except Exception as e:
                    exception = f"{type(e).__name__}: {e}"
                    self.logger.error(f"Failed to load extension {extension}\n{exception}")

    async def reload_cogs(self):
        for file in os.listdir(f"{os.path.realpath(os.path.dirname(__file__))}/cogs"):
            if file.endswith(".py"):
                extension = file[:-3]
                try:
                    await self.reload_extension(f"cogs.{extension}")
                    self.logger.info(f"Reloaded extension '{extension}'")
                except commands.ExtensionNotLoaded:
                    try:
                        await self.load_extension(f"cogs.{extension}")
                        self.logger.info(f"Loaded extension '{extension}' because it was not loaded before")
                    except Exception as e:
                        exception = f"{type(e).__name__}: {e}"
                        self.logger.error(f"Failed to load extension {extension}\n{exception}")
                except Exception as e:
                    exception = f"{type(e).__name__}: {e}"
                    self.logger.error(f"Failed to reload extension {extension}\n{exception}")


    @tasks.loop(minutes=1.0)
    async def status_task(self):
        statuses = ["with you!", "with humans!"]
        await self.change_presence(activity=discord.Game(random.choice(statuses)))

    @status_task.before_loop
    async def before_status_task(self):
        await self.wait_until_ready()

    async def setup_hook(self):
        self.logger.info(f"Logged in as {self.user.name}")
        self.logger.info(f"discord.py API version: {discord.__version__}")
        self.logger.info(f"Python version: {platform.python_version()}")
        self.logger.info(f"Running on: {platform.system()} {platform.release()} ({os.name})")
        await self.load_cogs()
        self.status_task.start()

bot = MyBot(command_prefix='.', intents=intents)

load_dotenv()

bot.run(os.getenv('DISCORD_TOKEN'))