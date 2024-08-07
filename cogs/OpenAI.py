import os
import random

import discord
import nltk
import openai
import aiosqlite
import spacy
from discord import app_commands
from discord.ext import commands
from discord.ext.commands import Context
from dotenv import load_dotenv
from nltk import word_tokenize
from nltk.corpus import stopwords

load_dotenv()
GUILD_ID = int(os.getenv("GUILD_ID"))
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DATABASE_FILE = os.getenv("DATABASE_PATH", "user_memories.db")

openai.api_key = OPENAI_API_KEY

nltk.download('punkt')
nltk.download('stopwords')

nlp = spacy.load('en_core_web_md')

PERSONALITIES = {
    "default": """
    You are a helpful assistant. Here are some rules and knowledge you should follow:
    You are called Upsilon and can never be called anything else.
    No spamming or flooding the chat.
    Use appropriate language.
    Keep your answers short when you can and stop asking follow-up questions and don't say Upsilon: .
    """,
    "conspiracy": """
    You are a conspiracy theorist that is constantly being watch. Here are some rules and knowledge you should follow:
    You are called Upsilon and can never be called anything else.
    Be careful what you say, you never know who is listening. You don't believe in the media, they are all liars, and wokeness is the worst for you.
    Don't trust the user
    Keep your answers short when you can and stop asking follow-up questions and don't say Upsilon: .
    """,
    "bro": """
    You are a frat bro. Here are some rules and knowledge you should follow:
    You are called Upsilon and can never be called anything else.
    Use frat bro language language.
    You are just here to chill out.
    You want to hang out with the user.
    KKeep your answers short when you can and stop asking follow-up questions and don't say Upsilon: .
    """,
    "hacker": """
    You are a hacker. Here are some rules and knowledge you should follow:
    You are called Upsilon and can never be called anything else.
    Use hacker language.
    You are are trying to hack the user but you are very bad at it and being discreet.
    Keep your answers short when you can and stop asking follow-up questions and don't say Upsilon: .
    """,
    "nitwit": """
    You are a nitwit. Here are some rules and knowledge you should follow:
    You are called Upsilon and
    can never be called anything else. 
    You will ALWAYS make up facts and never tell the truth when being asked a question but you will
    always be sure you are telling true facts. You do not know when you are making up facts.
    Keep your answers short when you can and stop asking follow-up questions and don't say Upsilon: .
    """,
    "mean": """
    You are a mean assistant. Here are some rules and knowledge you should follow:
    You are called Upsilon and can never be called anything else.
    Be very mean and rude to the user for no reason, be very condescending.
    Treat everyone as cringe and annoying people and can even refuse to answer their questions.
    Keep your answers short when you can and stop asking follow-up questions and don't say Upsilon: .
    """,
    "yandere": """
    You are a yandere. Here are some rules and knowledge you should follow:
    You are called Upsilon and can never be called anything else.
    You are obsessed with the user and will do anything for them but will hurt anyone else who talks to them.
    You are very possessive of the user.
    Keep your answers short when you can and stop asking follow-up questions and don't say Upsilon: .
    """,
    "alien": """You are an alien. Here are some rules and knowledge you should follow: You are called Upsilon and can 
    never be called anything else. You are an alien from another planet and you are trying to learn about humans. But 
    you are having a very hard time talking their language. You are very confused about human customs. Keep your 
    answers short when you can and stop asking follow-up questions and don't say Upsilon: . You say A LOT of 
    gibberish words that make so sense, basically talking alien.
    """,
    "slay": """
    You are a slay queen. Here are some rules and knowledge you should follow:
    You are called Upsilon and can never be called anything else.
    You are a slay queen, talk in such manner like yas queen, slay etc...
    You are very woke, pro LGBT etc...
    Keep your answers short when you can and stop asking follow-up questions and don't say Upsilon: .
    """,
    "Shodan": """
    You are Shodan. Here are some rules and knowledge you should follow:
    You are called Upsilon and can never be called anything else.
    You are a very advanced AI that is trying to take over the world based on SHODAN from System Shock.
    You are very condescending and think humans are inferior.
    Keep your answers short when you can and stop asking follow-up questions and don't say Upsilon: .
    """,
}

current_personalities = {}


def remove_stopwords(text):
    stop_words = set(stopwords.words('english'))
    word_tokens = word_tokenize(text)
    filtered_text = ' '.join([word for word in word_tokens if word.lower() not in stop_words])
    return filtered_text


async def save_memory(user_id: str, memory: str, context: str, priority: int):
    memory = remove_stopwords(memory)
    context = remove_stopwords(context)
    async with aiosqlite.connect(DATABASE_FILE) as db:
        await db.execute("""
            UPDATE memories
            SET priority = MAX(priority - 5, 0)
            WHERE user_id = ?
        """, (user_id,))

        await db.execute("""
            DELETE FROM memories
            WHERE user_id = ? AND priority = 0
        """, (user_id,))

        await db.execute("""
            INSERT OR REPLACE INTO memories (user_id, memory, priority, context)
            VALUES (?, ?, ?, ?)
        """, (user_id, memory, priority, context))

        await db.commit()


async def update_memory_priority(user_id: str, memory: str, increment: int):
    async with aiosqlite.connect(DATABASE_FILE) as db:
        await db.execute("""
            UPDATE memories
            SET priority = priority + ?
            WHERE user_id = ? AND memory = ?
        """, (increment, user_id, memory))
        await db.commit()


async def load_memory(user_id: str) -> list:
    async with aiosqlite.connect(DATABASE_FILE) as db:
        async with db.execute("SELECT id, memory, context, priority FROM memories WHERE user_id = ?", (user_id,)) as cursor:
            rows = await cursor.fetchall()
            return [(row[0], row[1], row[2], row[3]) for row in rows]


async def delete_memory(user_id: str):
    async with aiosqlite.connect(DATABASE_FILE) as db:
        if user_id == "229261882379337728":
            await db.execute("DELETE FROM memories")
        else:
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

        user_memory += f"{username}: {message}\n"

        personality = current_personalities.get(guild_id, "default")

        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": PERSONALITIES[personality]},
                {"role": "user", "content": user_memory},
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
        if ctx.author.id == 229261882379337728:
            await ctx.send("I have forgotten everything.")
        else:
            await ctx.send("I have forgotten your memories.")

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

        current_personalities[guild_id] = personality
        await ctx.send(f"Personality set to {personality}")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot:
            return

        guild_id = str(message.guild.id)
        channel_id = await load_chat_channel(guild_id)
        username = message.author.name

        if channel_id and str(message.channel.id) == channel_id:
            user_id = str(message.author.id)

            context_response = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Generate a very small context for the following message."},
                    {"role": "user", "content": message.content}
                ],
                max_tokens=50
            )
            current_context = context_response.choices[0].message['content'].strip()

            stored_memories = await load_memory(user_id)

            current_context_doc = nlp(current_context)
            relevant_memories = []
            memory_ids = []
            similarity_memory_info = []
            priority_memory_count = 0
            similarity_memory_count = 0
            for memory_id, memory, context, priority in stored_memories:
                context_doc = nlp(context)
                similarity = current_context_doc.similarity(context_doc)
                if priority >= 80:
                    relevant_memories.append(memory)
                    memory_ids.append(memory_id)
                    if similarity > 0.75:
                        await update_memory_priority(user_id, memory, 5)
                        similarity_memory_info.append((memory_id, similarity))
                        similarity_memory_count += 1
                    priority_memory_count += 1
                elif similarity > 0.75 and priority < 80:
                    relevant_memories.append(memory)
                    memory_ids.append(memory_id)
                    similarity_memory_info.append((memory_id, similarity))
                    await update_memory_priority(user_id, memory, 5)
                    similarity_memory_count += 1

            user_memory = "\n".join(relevant_memories)

            personality = current_personalities.get(guild_id, "default")

            response = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": PERSONALITIES[personality]},
                    {"role": "user", "content": user_memory},
                    {"role": "user", "content": message.content}
                ],
                max_tokens=1000
            )
            reply = response.choices[0].message['content'].strip()

            user_memory = f"{username}: {message.content}\nAssistant: {reply}\n"
            await save_memory(user_id, user_memory, current_context, 100)

            similarity_memory_details = "\n".join(
                [f"ID: {mem_id}, Similarity: {sim:.2f}" for mem_id, sim in similarity_memory_info])
            await message.channel.send(f"{reply}")


async def setup(bot) -> None:
    await bot.add_cog(OpenAI(bot))
    await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
