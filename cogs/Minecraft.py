import discord
from discord.ext import commands
from discord.ui import Button, Select, View
import asyncio

class MySelect(Select):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sub_selected = [] 
        self.main_options = [
            discord.SelectOption(label="Enchantements", value="enchantements"),
            discord.SelectOption(label="Main Option 2", value="main2"),
            discord.SelectOption(label="Main Option 3", value="main3"),
            discord.SelectOption(label="Main Option 4", value="main4"),
        ]
        super().__init__(placeholder="Choose an option...", min_values=1, max_values=1, options=self.main_options)
        self.main_selected = {
            "enchantements": False,
            "main2": False,
            "main3": False,
            "main4": False
        }

    def reset_to_main_options(self):
        self.options = self.main_options
        self.placeholder = "Choose an option..."

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        selected_option = self.values[0]

        if selected_option in ["enchantements", "main2", "main3", "main4"]:
            self.main_selected[selected_option] = True

            sub_options_map = {
                "enchantements": [
                    "Protection", "Feather Falling", "Respiration", "Aqua Affinity", "Thorns", "Depth Strider",
                    "Curse of Binding", "Sharpness", "Knockback", "Fire Aspect", "Looting", "Sweeping Edge",
                    "Efficiency", "Silk Touch", "Unbreaking", "Fortune", "Punch", "Flame", "Infinity",
                    "Loyalty", "Riptide", "Channeling", "Multishot", "Mending", "Curse of Vanishing"
                ],
                "main2": ["Sub-option 2.1", "Sub-option 2.2"],
                "main3": ["Sub-option 3.1", "Sub-option 3.2"],
                "main4": ["Sub-option 4.1", "Sub-option 4.2"],
            }

            sub_options = [discord.SelectOption(label=sub_option, value=f"{selected_option}_{sub_option}") for sub_option in sub_options_map[selected_option]]
            self.options = sub_options
            self.placeholder = "Choose a sub-option..."
            await interaction.message.edit(view=self.view)
        else:
            if selected_option.startswith("enchantements_"):
                def check(m):
                    return m.author == interaction.user and m.channel == interaction.channel and m.content.isdigit() and 1 <= int(m.content) <= 255

                await interaction.followup.send("Please enter a number between 1-255 in the chat.", ephemeral=True)
                try:
                    number_message = await interaction.client.wait_for('message', check=check, timeout=60.0)
                    new_sub_option = f"{selected_option}_{number_message.content}"
                    if new_sub_option not in self.sub_selected:
                        self.sub_selected.append(new_sub_option)
                        await interaction.followup.send(f"Number {number_message.content} received and saved.", ephemeral=True)
                    else:
                        await interaction.followup.send(f"{new_sub_option} is already selected.", ephemeral=True)
                    await number_message.delete()
                except asyncio.TimeoutError:
                    await interaction.followup.send("You did not enter a number in time.", ephemeral=True)
                    return
            else:
                new_sub_option = selected_option
                if new_sub_option not in self.sub_selected:
                    self.sub_selected.append(new_sub_option)

            # Send response about saved selections
            main_selections = [key for key, value in self.main_selected.items() if value]
            sub_options_str = ", ".join(self.sub_selected)
            await interaction.followup.send(
                f"Main selections: {', '.join(main_selections)}\nSub-options selected: {sub_options_str}",
                ephemeral=True
            )

class ConfirmButton(Button):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def callback(self, interaction: discord.Interaction):
        view = self.view
        select_menu = next((item for item in view.children if isinstance(item, MySelect)), None)
        if select_menu:
            messages = []
            confirmation_message = "" 
            for key, value in select_menu.main_selected.items():
                if value:
                    messages.append(f"Main option {key} selected.")
            if select_menu.sub_selected:
                sub_options_str = ", ".join(select_menu.sub_selected)
                messages.append(f"\nSub-options selected: {sub_options_str}")
                confirmation_message += f"\nSub-option selected: {select_menu.sub_selected}"
            
            await interaction.response.send_message(confirmation_message, ephemeral=True)
            select_menu.reset_to_main_options()
            await interaction.message.edit(view=view)
        else:
            await interaction.response.send_message("Please make a selection before confirming.", ephemeral=True)

class MyView(View):
    def __init__(self, user_message=""):
        super().__init__()
        self.user_message = user_message
        self.add_item(MySelect())
        self.add_item(ConfirmButton(label="Confirm Selection", style=discord.ButtonStyle.primary, custom_id="confirm_button"))
        self.add_item(FinalizeButton(label="Finalize Selections", style=discord.ButtonStyle.danger, custom_id="finalize_button"))

class FinalizeButton(Button):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def callback(self, interaction: discord.Interaction):
        view = self.view
        select_menu = next((item for item in view.children if isinstance(item, MySelect)), None)
        if select_menu:
            messages = []
            for key, value in select_menu.main_selected.items():
                if value:
                    messages.append(f"Main option {key} selected.")
            if select_menu.sub_selected:
                sub_options_str = ", ".join(select_menu.sub_selected)
                messages.append(f"\nSub-options selected: {sub_options_str}")

            combined_message = " ".join(messages)
            if not messages:
                combined_message = f"Final selections: {', '.join([key for key, value in select_menu.main_selected.items() if value])}"
            
            combined_message += f"\nid: minecraft:{view.user_message.content}"

            await interaction.response.send_message(combined_message)
            await interaction.message.delete()
        else:
            await interaction.response.send_message("No selections to finalize.", ephemeral=True)

class Minecraft(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['dd'])
    async def dropdown(self, ctx):
        await ctx.send("Please type your input before the dropdown menu is shown.")

        msg = await self.bot.wait_for('message', check=lambda message: message.author == ctx.author and message.channel == ctx.channel)

        embed = discord.Embed(
            title="Dropdown Menu",
            description="Please select options from the dropdown menu below and then press the button to confirm.",
            color=discord.Color.blue()
        )
        view = MyView(user_message=msg)
        await ctx.send(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(Minecraft(bot))
