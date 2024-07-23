import discord
from discord.ext import commands
from discord.ui import Button, Select, View
import asyncio

class MySelect(Select):
    def __init__(self):
        self.main_options = [
            discord.SelectOption(label="Main Option 1", value="main1"),
            discord.SelectOption(label="Main Option 2", value="main2"),
            discord.SelectOption(label="Main Option 3", value="main3"),
            discord.SelectOption(label="Main Option 4", value="main4"),
        ]
        super().__init__(placeholder="Choose an option...", min_values=1, max_values=1, options=self.main_options)
        self.selected_values = []

    def reset_to_main_options(self):
        self.options = self.main_options
        self.placeholder = "Choose an option..."

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        selected_option = self.values[0]

        if selected_option in ["main1", "main2", "main3", "main4"]:
            sub_options_map = {
                "main1": ["Sub-option 1.1", "Sub-option 1.2"],
                "main2": ["Sub-option 2.1", "Sub-option 2.2"],
                "main3": ["Sub-option 3.1", "Sub-option 3.2"],
                "main4": ["Sub-option 4.1", "Sub-option 4.2"],
            }
            sub_options = [discord.SelectOption(label=sub_option, value=f"{selected_option}_{sub_option}") for sub_option in sub_options_map[selected_option]]
            self.options = sub_options
            self.placeholder = "Choose a sub-option..."
            await interaction.message.edit(view=self.view)
        else:
            if selected_option.startswith("main1_"):
                # Process for main option 1 that requires additional number input
                def check(m):
                    return m.author == interaction.user and m.channel == interaction.channel and m.content.isdigit() and 1 <= int(m.content) <= 255

                await interaction.followup.send("Please enter a number between 1-255 in the chat.", ephemeral=True)
                try:
                    number_message = await interaction.client.wait_for('message', check=check, timeout=60.0)  # Use interaction.client to access the bot instance
                    # Confirm the input and save it
                    selected_option = f"{selected_option}_{number_message.content}"
                    await interaction.followup.send(f"Number {number_message.content} received and saved.", ephemeral=True)
                    await number_message.delete()  # Delete the user's message
                except asyncio.TimeoutError:
                    await interaction.followup.send("You did not enter a number in time.", ephemeral=True)
                    return  # Exit the method if the user fails to input a number in time

            # Append the selected option (or modified option for main1) to selected_values
            self.selected_values.append(selected_option)
            await interaction.followup.send(f"Selection {selected_option} received and saved. Please select another option or confirm your selection", ephemeral=True)

class ConfirmButton(Button):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def callback(self, interaction: discord.Interaction):
        view = self.view
        select_menu = next((item for item in view.children if isinstance(item, MySelect)), None)
        if select_menu and select_menu.selected_values:
            # Process the selected values for confirmation
            confirmation_message = "You have confirmed the following selections: " + ", ".join(select_menu.selected_values)
            await interaction.response.send_message(confirmation_message, ephemeral=True)
            select_menu.reset_to_main_options()
            await interaction.message.edit(view=view)
        else:
            # No selection made to confirm
            await interaction.response.send_message("Please make a selection before confirming.", ephemeral=True)

class MyView(View):
    def __init__(self, user_message=""):
        super().__init__()
        self.user_message = user_message  # Store the user's message
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
            
            # Include the user's input message in the final message
            combined_message += f"\nUser's input: {view.user_message.content}"

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
        view = MyView(user_message=msg)  # Ensure MyView is defined or imported appropriately
        await ctx.send(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(Minecraft(bot))
