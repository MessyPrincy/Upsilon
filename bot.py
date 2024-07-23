import discord
from discord.ext import commands
from discord.ui import Button, Select, View
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

@bot.command(aliases=['git', 'source'])
async def github(ctx):
    await ctx.send('https://github.com/MessyPrincy/Upsilon')

class MySelect(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Option 1", value="option1"),
            discord.SelectOption(label="Option 2", value="option2"),
            discord.SelectOption(label="Option 3", value="option3"),
        ]
        super().__init__(placeholder="Choose an option...", min_values=1, max_values=3, options=options)
        self.selected_values = []

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        self.selected_values = self.values

class ConfirmButton(Button):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def callback(self, interaction: discord.Interaction):
        view = self.view  
        select_menu = next((item for item in view.children if isinstance(item, MySelect)), None)
        if select_menu:
            messages = []  
            for selected_value in select_menu.selected_values:
                if selected_value == "option1":
                    messages.append("Option 1 specific message.")
                elif selected_value == "option2":
                    messages.append("Option 2 specific message.")
                elif selected_value == "option3":
                    messages.append("Option 3 specific message.")
            
            combined_message = " ".join(messages)  
            if not messages:  
                combined_message = f"Selections confirmed: {', '.join(select_menu.selected_values)}"
            
            await interaction.response.send_message(combined_message)
        else:
            await interaction.response.send_message("No selections to confirm.")

class FinalizeButton(Button):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def callback(self, interaction: discord.Interaction):
        view = self.view  
        select_menu = next((item for item in view.children if isinstance(item, MySelect)), None)
        if select_menu:
            messages = [] 
            for selected_value in select_menu.selected_values:
                if selected_value == "option1":
                    messages.append("Option 1 specific message.")
                elif selected_value == "option2":
                    messages.append("Option 2 specific message.")
                elif selected_value == "option3":
                    messages.append("Option 3 specific message.")
            
            combined_message = " ".join(messages) 
            if not messages: 
                combined_message = f"Final selections: {', '.join(select_menu.selected_values)}"
            
           
            await interaction.response.send_message(combined_message)
            
            await interaction.message.delete()
        else:
            await interaction.response.send_message("No selections to finalize.", ephemeral=True)

class MyView(View):
    def __init__(self):
        super().__init__()
        self.add_item(MySelect())
        self.add_item(ConfirmButton(label="Confirm Selections", style=discord.ButtonStyle.primary, custom_id="confirm_button"))
        self.add_item(FinalizeButton(label="Finalize Selections", style=discord.ButtonStyle.danger, custom_id="finalize_button"))

@bot.command(aliases=['dd'])
async def dropdown(ctx):
    embed = discord.Embed(
        title="Dropdown Menu",
        description="Please select options from the dropdown menu below and then press the button to confirm.",
        color=discord.Color.blue()
    )
    view = MyView()
    await ctx.send(embed=embed, view=view)



bot.run(os.getenv('DISCORD_TOKEN'))