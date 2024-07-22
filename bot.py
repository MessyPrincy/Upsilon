import discord
from discord.ext import commands
from discord.ui import Button, View
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

intents = discord.Intents.default()
# Enable message content intent
intents.message_content = True

bot = commands.Bot(command_prefix='.', intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}!')

@bot.command()
async def ping(ctx):
    await ctx.send('Pong!')

class MyView(View):
    def __init__(self):
        super().__init__()

    @discord.ui.button(label="Click me!", style=discord.ButtonStyle.primary, custom_id="interact_button")
    async def button_callback(self, interaction: discord.Interaction, button: Button):
        await interaction.response.defer()
        await interaction.followup.send("You clicked the button!")

@bot.command()
async def interactive(ctx):
    embed = discord.Embed(
        title="Interactive Embed",
        description="Click the button below to interact!",
        color=discord.Color.blue()
    )
    view = MyView()
    await ctx.send(embed=embed, view=view)

bot.run(os.getenv('DISCORD_TOKEN'))