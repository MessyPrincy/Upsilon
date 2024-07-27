import os
import random
import asyncio
from dotenv import load_dotenv
import discord
from discord import app_commands
from discord.ext import commands
from discord.ext.commands import Context

load_dotenv()
GUILD_ID = int(os.getenv("GUILD_ID"))

SPELLS = [
    {"name": "Color Spray", "emoji": "🫳", "description": "Target loses 1 gold per poorer wizard."},
    {"name": "Fireball", "emoji": "✊️", "description": "Target gets pushed 5."},
    {"name": "Ice Storm", "emoji": "🫴", "description": "Target gets pushed 4; players seated next to target each "
                                                       "advances 2."},
    {"name": "Vampire Touch", "emoji": "🤭", "description": "Target gets pushed 2; caster "
                                                           "advances 2."},
    {"name": "Polymorph", "emoji": "🖖", "description": "Target gets pushed spaces equal to the gold difference "
                                                       "between target and caster."},
    {"name": "Passwall", "emoji": "🫲", "description": "Caster advances 3; target advances 2."},
    {"name": "Dimension Door", "emoji": "🤞", "description": "Caster and target swap position."},
    {"name": "Chain lightning", "emoji": "🙏",
     "description": "Target gets pushed 3; target's target gets pushed 2."},
    {"name": "Imprisonment", "emoji": "🙌", "description": "Target gives 1 gold to each poorer wizard."},
    {"name": "Wall of Force", "emoji": "👌", "description": "Caster advances 2; target reverses gesture to point back "
                                                           "at self."},
    {"name": "Confusion", "emoji": "🤙", "description": "Caster advances 2; target's target shifts 1 player turnwise. "
                                                       "(Player after the target)"},
    {"name": "Burning hands", "emoji": "🤟", "description": "Target gets pushed 1 and looses 1 gold."},
    {"name": "Dominate Person", "emoji": "🖕", "description": "Target gets pushed 3 and gives caster 1 gold"},
    {"name": "Fear", "emoji": "👈", "description": "Target gets pushed 2 per poorer wizard."},
    {"name": "Meteor swarm", "emoji": "🖐️", "description": "Target gets pushed 1, plus 2 more per spell to the right "
                                                           "of this one in the grimoire."},
    {"name": "Counterspell", "emoji": "🫷", "description": "Caster advances 2; target's spell is negated."},
    {"name": "Feeblemind", "emoji": "🤌", "description": "Target and caster pool gold then split it evenly; remainder "
                                                        "to caster."},
    {"name": "Charm person", "emoji": "🫶", "description": "Target gives 2 gp to the poorer wizard of "
                                                          "their choice."},
    {"name": "Telekenesis", "emoji": "🤏", "description": "Target moves one space closer to the exit "
                                                         "than the caster."},
    {"name": "Stinking cloud", "emoji": "✌️", "description": "Target gets pushed 3 and players seated next to target "
                                                             "each gets pushed 1."},
    {"name": "Antimagic Field", "emoji": "👎", "description": "Caster advances 2; target's gesture turns into a Wild "
                                                             "Surge"},
    {"name": "Misty step", "emoji": "👍", "description": "Caster moves to the same space as the target."},
]


class Game(commands.Cog, name="game"):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.active_games = {}

    @commands.hybrid_command(name="start_rpw",
                             description="Starts a new game of Rock, Paper, Wizard and waits for players to join.")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def start_game(self, ctx: Context) -> None:
        if ctx.guild.id in self.active_games:
            await ctx.send("A game is already in progress in this server.")
            return

        self.active_games[ctx.guild.id] = {
            "players": {},
            "channel": ctx.channel,
            "board": [" "] * 11,
            "grimoire": random.sample(SPELLS, 4)
        }
        await ctx.send("Game started! Use `/join_game` to join. Waiting for 3 to 6 players...")

    @commands.hybrid_command(name="join_game", description="Join an active game.")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def join_game(self, ctx: Context) -> None:
        if ctx.guild.id not in self.active_games:
            await ctx.send("No active game to join. Start a new game with `/start_game`.")
            return

        game = self.active_games[ctx.guild.id]
        if ctx.author.id in game["players"]:
            await ctx.send("You have already joined the game.")
            return

        display_name = ctx.author.display_name
        if not any("*" in player["member"].display_name for player in game["players"].values()):
            display_name = "*" + display_name

        game["players"][ctx.author.id] = {
            "member": ctx.author,
            "gold": 3,
            "position": 5,
            "display_name": display_name
        }
        await ctx.send(f"{ctx.author.mention} has joined the game! ({len(game['players'])}/6 players)")

        if 3 <= len(game["players"]) <= 6:
            await self.check_and_start_game(ctx.guild.id)

    @commands.hybrid_command(name="end_game", description="Ends the current game.")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def end_game(self, ctx: Context) -> None:
        if ctx.guild.id not in self.active_games:
            await ctx.send("No active game to end.")
            return

        del self.active_games[ctx.guild.id]
        await ctx.send("The game has been ended.")

    async def check_and_start_game(self, guild_id: int) -> None:
        await asyncio.sleep(10)
        game = self.active_games[guild_id]
        if 3 <= len(game["players"]) <= 6:
            await self.start_game_with_players(guild_id)

    async def start_game_with_players(self, guild_id: int) -> None:
        game = self.active_games[guild_id]
        channel = game["channel"]
        players = game["players"]

        if not any("*" in player["display_name"] for player in players.values()):
            first_player_id = next(iter(players))
            players[first_player_id]["display_name"] = "*" + players[first_player_id]["display_name"]

        player_mentions = [player_data["member"].mention for player_data in players.values()]
        await channel.send(f"Game starting with {len(players)} players: {', '.join(player_mentions)}")

        await self.update_game_board(guild_id)

    async def update_game_board(self, guild_id: int) -> None:
        game = self.active_games[guild_id]
        channel = game["channel"]
        board = [" "] * 11

        for player_data in game["players"].values():
            display_name = player_data["display_name"]
            if "*" in display_name:
                display_name = f"*{display_name.replace('*', '')}"
            board[player_data["position"]] = display_name

        board[2] = "┃" if board[2] == " " else board[2]
        board[8] = "┃" if board[8] == " " else board[8]

        embed = discord.Embed(title="Game Board")
        board_str = "🛑 |" + "|".join(board) + "| 💰"
        embed.add_field(name="Board", value=f"`{board_str}`", inline=False)

        grimoire_str = " | ".join([spell["emoji"] for spell in game["grimoire"]])
        embed.add_field(name="Grimoire", value=grimoire_str, inline=False)

        for player_data in game["players"].values():
            embed.add_field(name=player_data["display_name"], value=f"Gold: {player_data['gold']}", inline=True)

        if "message" in game:
            await game["message"].edit(embed=embed)
        else:
            game["message"] = await channel.send(embed=embed)

    @commands.hybrid_command(name="update_grimoire",
                             description="Change the grimoire by shifting spells to the left and adding a new one.")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def change_grimoire(self, ctx: Context) -> None:
        if ctx.guild.id not in self.active_games:
            await ctx.send("No active game to change the grimoire for.", ephemeral=True)
            return

        game = self.active_games[ctx.guild.id]
        new_spell = random.choice([spell for spell in SPELLS if spell not in game["grimoire"]])
        game["grimoire"].pop(0)
        game["grimoire"].append(new_spell)
        await ctx.send("The grimoire has been changed.", delete_after=20)
        await self.update_game_board(ctx.guild.id)

    @commands.hybrid_command(name="info", description="Get information about a spell.")
    @app_commands.describe(emoji="The emoji of the spell you want information about")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def spell_info(self, ctx: Context, emoji: str) -> None:
        for spell in SPELLS:
            if spell["emoji"] == emoji:
                embed = discord.Embed(
                    title=f"Spell: {spell['name']}",
                    description=f"{spell['emoji']}\n{spell['description']}",
                    color=0x00FF00
                )
                await ctx.send(embed=embed, ephemeral=True)
                return
        await ctx.send("Spell not found.", ephemeral=True)

    @commands.hybrid_command(name="move", description="Move your character on the board.")
    @app_commands.describe(direction="The direction to move (left or right)", amount="The number of spaces to move")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def move(self, ctx: Context, direction: str, amount: int) -> None:
        if ctx.guild.id not in self.active_games:
            await ctx.send("No active game to move in.", ephemeral=True)
            return

        game = self.active_games[ctx.guild.id]
        if ctx.author.id not in game["players"]:
            await ctx.send("You are not part of the current game.", ephemeral=True)
            return

        player = game["players"][ctx.author.id]
        if direction.lower() == "left":
            player["position"] = max(0, player["position"] - amount)
        elif direction.lower() == "right":
            player["position"] = min(10, player["position"] + amount)
        else:
            await ctx.send("Invalid direction. Use 'left' or 'right'.", ephemeral=True)
            return

        await self.update_game_board(ctx.guild.id)
        await ctx.send(f"{ctx.author.mention} moved {amount} spaces {direction}.", delete_after=20)

    @commands.hybrid_command(name="gain_gold", description="Gain gold.")
    @app_commands.describe(amount="The amount of gold to gain")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def gain_gold(self, ctx: Context, amount: int) -> None:
        if ctx.guild.id not in self.active_games:
            await ctx.send("No active game to gain gold in.", ephemeral=True)
            return

        game = self.active_games[ctx.guild.id]
        if ctx.author.id not in game["players"]:
            await ctx.send("You are not part of the current game.", ephemeral=True)
            return

        player = game["players"][ctx.author.id]
        player["gold"] += amount

        await self.update_game_board(ctx.guild.id)
        await ctx.send(f"{ctx.author.mention} gained {amount} gold.", delete_after=20)

    @commands.hybrid_command(name="lose_gold", description="Lose gold.")
    @app_commands.describe(amount="The amount of gold to lose")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def lose_gold(self, ctx: Context, amount: int) -> None:
        if ctx.guild.id not in self.active_games:
            await ctx.send("No active game to lose gold in.", ephemeral=True)
            return

        game = self.active_games[ctx.guild.id]
        if ctx.author.id not in game["players"]:
            await ctx.send("You are not part of the current game.", ephemeral=True)
            return

        player = game["players"][ctx.author.id]
        player["gold"] -= amount

        await self.update_game_board(ctx.guild.id)
        await ctx.send(f"{ctx.author.mention} lost {amount} gold.", delete_after=20)

    @commands.hybrid_command(name="steal_gold", description="Steal gold from another player.")
    @app_commands.describe(target="The player to steal gold from", amount="The amount of gold to steal")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def steal_gold(self, ctx: Context, target: discord.Member, amount: int) -> None:
        if ctx.guild.id not in self.active_games:
            await ctx.send("No active game to steal gold in.")
            return

        game = self.active_games[ctx.guild.id]
        if ctx.author.id not in game["players"]:
            await ctx.send("You are not part of the current game.", ephemeral=True)
            return

        if target.id not in game["players"]:
            await ctx.send(f"{target.mention} is not part of the current game.", ephemeral=True)
            return

        player = game["players"][ctx.author.id]
        target_player = game["players"][target.id]

        if target_player["gold"] < amount:
            await ctx.send(f"{target.mention} does not have enough gold to steal.", delete_after=20)
            return

        target_player["gold"] -= amount
        player["gold"] += amount

        await self.update_game_board(ctx.guild.id)
        await ctx.send(f"{ctx.author.mention} stole {amount} gold from {target.mention}.", delete_after=20)

    @commands.hybrid_command(name="cast_spell", description="Cast a spell on a target.")
    @app_commands.describe(spell="The spell to cast (name or emoji)", target="The target player")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def cast_spell(self, ctx: Context, spell: str, target: discord.Member) -> None:
        if ctx.guild.id not in self.active_games:
            await ctx.send("No active game to cast a spell in.", ephemeral=True)
            return

        game = self.active_games[ctx.guild.id]
        if ctx.author.id not in game["players"]:
            await ctx.send("You are not part of the current game.", ephemeral=True)
            return

        if target.id not in game["players"]:
            await ctx.send(f"{target.mention} is not part of the current game.", ephemeral=True)
            return

        valid_spells = {s["name"]: s["emoji"] for s in SPELLS}
        valid_spells.update({s["emoji"]: s["emoji"] for s in SPELLS})

        if spell not in valid_spells:
            await ctx.send("Invalid spell.", ephemeral=True)
            return

        player = game["players"][ctx.author.id]
        player["chosen_spell"] = valid_spells[spell]
        player["target"] = target.id

        await ctx.send(f"{ctx.author.mention} has chosen a spell and a target.", delete_after=20)

        if all("chosen_spell" in p for p in game["players"].values()):
            await self.reveal_spells(ctx.guild.id)

    async def reveal_spells(self, guild_id: int) -> None:
        game = self.active_games[guild_id]
        channel = game["channel"]

        order = sorted(game["players"].values(), key=lambda p: "*" in p["member"].display_name)
        for player_data in order:
            player = player_data["member"]
            spell = player_data["chosen_spell"]
            target = game["players"][player_data["target"]]["member"]
            await channel.send(f"{player.mention} casts {spell} on {target.mention}.", delete_after=200)

        first_player = order.pop(0)
        first_player["member"].display_name = first_player["member"].display_name.replace("*", "")
        order.append(first_player)
        order[0]["member"].display_name = "*" + order[0]["member"].display_name

        for player_data in game["players"].values():
            del player_data["chosen_spell"]
            del player_data["target"]

        await self.update_game_board(guild_id)

    @commands.hybrid_command(name="wild_surge", description="Get a random spell.")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def wild_surge(self, ctx: Context) -> None:
        random_spell = random.choice(SPELLS)
        spell_name = random_spell["name"]
        spell_emoji = random_spell["emoji"]
        spell_description = random_spell["description"]

        embed = discord.Embed(
            title="Wild Surge!",
            description=f"**{spell_name}** {spell_emoji}\n{spell_description}",
            color=0x00FF00
        )
        await ctx.send(embed=embed, delete_after=50)


async def setup(bot) -> None:
    await bot.add_cog(Game(bot))
    await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
