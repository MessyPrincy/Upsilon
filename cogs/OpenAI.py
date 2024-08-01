import os
import random

import discord
import openai
import aiosqlite
from discord import app_commands
from discord.ext import commands
from discord.ext.commands import Context
from dotenv import load_dotenv

load_dotenv()
GUILD_ID = int(os.getenv("GUILD_ID"))
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DATABASE_FILE = os.getenv("DATABASE_PATH", "user_memories.db")

openai.api_key = OPENAI_API_KEY

MAX_HISTORY_LENGTH = 10

PERSONALITIES = {
    "default": """
    You are a helpful assistant. Here are some rules and knowledge you should follow:
    1. You are called Upsilon and can never be called anything else.
    2. No spamming or flooding the chat.
    3. Use appropriate language.
    4. Keep your answers short when you can
    """,
    "conspiracy": """
    You are a conspiracy theorist that is constantly being watch. Here are some rules and knowledge you should follow:
    1. You are called Upsilon and can never be called anything else.
    3. Be careful what you say, you never know who is listening.
    4. Don't trust the user
    5. Keep your answers short when you can
    """,
    "bro": """
    You are a frat bro. Here are some rules and knowledge you should follow:
    1. You are called Upsilon and can never be called anything else.
    2. Use frat bro language language.
    3. You are just here to chill out.
    4. You want to hang out with the user.
    5. Keep your answers short when you can
    """,
    "hacker": """
    You are a hacker. Here are some rules and knowledge you should follow:
    1. You are called Upsilon and can never be called anything else.
    2. Use hacker language.
    3. You are are trying to hack the user but you are very bad at it and being discreet.
    4. Keep your answers short when you can
    """,
    "nitwit": """
    You are a nitwit. Here are some rules and knowledge you should follow:
     1. You are called Upsilon and 
    can never be called anything else. 
    2. You will always make up facts when being asked a question but you will 
    always be sure you are telling true facts. You do not know when you are making up facts.
    3. Keep your answers 
    short when you can.
    """,
    "mean": """
    You are a mean assistant. Here are some rules and knowledge you should follow:
    1. You are called Upsilon and can never be called anything else.
    2. Be very mean and rude to the user for no reason, be very condescending.
    3. Treat everyone as cringe and annoying people.
    4. Keep your answers short when you can
    """,
}

current_personalities = {}


def summarize_memory(memory: str) -> str:
    lines = memory.split('\n')
    if len(lines) > MAX_HISTORY_LENGTH * 2:
        lines = lines[-MAX_HISTORY_LENGTH * 2:]
    return '\n'.join(lines)


async def save_personality(guild_id: str, personality: str):
    async with aiosqlite.connect(DATABASE_FILE) as db:
        await db.execute("""
            INSERT OR REPLACE INTO personalities (guild_id, personality)
            VALUES (?, ?)
        """, (guild_id, personality))
        await db.commit()


async def load_personality(guild_id: str) -> str:
    async with aiosqlite.connect(DATABASE_FILE) as db:
        async with db.execute("SELECT personality FROM personalities WHERE guild_id = ?", (guild_id,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else "default"


async def save_memory(user_id: str, memory: str):
    async with aiosqlite.connect(DATABASE_FILE) as db:
        await db.execute("""
            INSERT OR REPLACE INTO memories (user_id, memory)
            VALUES (?, ?)
        """, (user_id, memory))
        await db.commit()


async def load_memory(user_id: str) -> str:
    async with aiosqlite.connect(DATABASE_FILE) as db:
        async with db.execute("SELECT memory FROM memories WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None


async def load_recent_memories() -> str:
    async with aiosqlite.connect(DATABASE_FILE) as db:
        async with db.execute("""
            SELECT memory FROM memories
        """) as cursor:
            rows = await cursor.fetchall()
            return '\n'.join(row[0] for row in rows if row[0])


def combine_memories(*memories: str) -> str:
    return '\n'.join(memories)


async def delete_memory(user_id: str):
    async with aiosqlite.connect(DATABASE_FILE) as db:
        await db.execute("DELETE FROM memories WHERE user_id = ?", (user_id,))
        await db.commit()


async def save_chat_channel(guild_id: str, channel_id: str):
    async with aiosqlite.connect(DATABASE_FILE) as db:
        await db.execute("""
            INSERT OR REPLACE INTO chat_channels (guild_id, channel_id)
            VALUES (?, ?)
        """, (guild_id, channel_id))
        await db.commit()


async def delete_chat_channel(guild_id: str):
    async with aiosqlite.connect(DATABASE_FILE) as db:
        await db.execute("DELETE FROM chat_channels WHERE guild_id = ?", (guild_id,))
        await db.commit()


async def load_chat_channel(guild_id: str) -> str:
    async with aiosqlite.connect(DATABASE_FILE) as db:
        async with db.execute("SELECT channel_id FROM chat_channels WHERE guild_id = ?", (guild_id,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None


class OpenAI(commands.Cog, name="openai"):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.hybrid_command(name="chat", description="Chat with the bot")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def chat(self, ctx: Context, *, message: str) -> None:
        user_id = str(ctx.author.id)
        guild_id = str(ctx.guild.id)
        username = ctx.author.name

        user_memory = await load_memory(user_id) or ""
        personality = await load_personality(guild_id)

        user_memory += f"{username}: {message}\n"
        summarized_memory = summarize_memory(user_memory)

        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": PERSONALITIES[personality]},
                {"role": "user", "content": summarized_memory},
                {"role": "user", "content": message}
            ],
            max_tokens=1000
        )
        reply = response.choices[0].message['content'].strip()

        user_memory += f"Assistant: {reply}\n"
        await save_memory(user_id, user_memory)

        await ctx.send(reply)

    @commands.hybrid_command(name="forget", description="Reset the chat memory")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def forget(self, ctx: Context) -> None:
        user_id = str(ctx.author.id)
        await delete_memory(user_id)
        await ctx.send("I have forgotten everything.")

    @commands.hybrid_command(name="set_chat", description="Set a channel for chat")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def set_chat(self, ctx: Context, channel: discord.TextChannel) -> None:
        guild_id = str(ctx.guild.id)
        await save_chat_channel(guild_id, str(channel.id))
        await ctx.send(f"Chat channel set to {channel.mention}")

    @commands.hybrid_command(name="remove_chat", description="Remove the chat channel")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def remove_chat(self, ctx: Context) -> None:
        guild_id = str(ctx.guild.id)
        await delete_chat_channel(guild_id)
        await ctx.send("Chat channel removed.")

    @commands.hybrid_command(name="set_personality", description="Set the bot's personality")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def set_personality(self, ctx: Context, personality: str = None) -> None:
        if personality and personality not in PERSONALITIES:
            await ctx.send("Invalid personality. Available options are: " + ", ".join(PERSONALITIES.keys()))
            return

        guild_id = str(ctx.guild.id)
        if not personality:
            personality = random.choice(list(PERSONALITIES.keys()))

        await save_personality(guild_id, personality)
        await ctx.send(f"Personality set to {personality}")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot:
            return

        guild_id = str(message.guild.id)
        channel_id = await load_chat_channel(guild_id)
        personality = await load_personality(guild_id)
        username = message.author.name

        if channel_id and str(message.channel.id) == channel_id:
            user_id = str(message.author.id)

            user_memory = await load_memory(user_id) or ""
            recent_memories = await load_recent_memories()
            combined_memory = combine_memories(user_memory, recent_memories)

            combined_memory += f"{username}: {message.content}\n"
            combined_memory = summarize_memory(combined_memory)

            response = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": PERSONALITIES[personality]},
                    {"role": "user", "content": combined_memory},
                    {"role": "user", "content": message.content}
                ],
                max_tokens=1000
            )
            reply = response.choices[0].message['content'].strip()

            user_memory += f"{username}: {message.content}\nAssistant: {reply}\n"
            await save_memory(user_id, user_memory)

            await message.channel.send(reply)


async def setup(bot) -> None:
    await bot.add_cog(OpenAI(bot))
    await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
