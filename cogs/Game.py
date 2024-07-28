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


def color_spray(caster, target, game):
    poorer_wizards = [p for p in game["players"].values() if p["gold"] < target["gold"]]
    target["gold"] -= len(poorer_wizards)
    return f"{target['display_name']} loses {len(poorer_wizards)} gold."


def fireball(caster, target, game):
    target["position"] = max(0, min(10, target["position"] - 5))
    return f"{target['display_name']} gets pushed 5 positions."


def ice_storm(caster, target, game):
    target["position"] = max(0, min(10, target["position"] - 4))
    affected_players = []
    player_ids = list(game["players"].keys())
    target_index = player_ids.index(target["member"].id)

    # Check the player above the target
    if target_index > 0:
        above_player = game["players"][player_ids[target_index - 1]]
        above_player["position"] = max(0, min(10, above_player["position"] + 2))
        affected_players.append(above_player["display_name"])

    # Check the player below the target
    if target_index < len(player_ids) - 1:
        below_player = game["players"][player_ids[target_index + 1]]
        below_player["position"] = max(0, min(10, below_player["position"] + 2))
        affected_players.append(below_player["display_name"])

    return f"{target['display_name']} gets pushed 4 positions. {', '.join(affected_players)} get pushed 2 positions."


def vampire_touch(caster, target, game):
    target["position"] = max(0, min(10, target["position"] - 2))
    caster["position"] = max(0, min(10, caster["position"] + 2))
    return f"{target['display_name']} gets pushed 2 positions. {caster['display_name']} advances 2 positions."


def polymorph(caster, target, game):
    gold_difference = abs(caster["gold"] - target["gold"])
    target["position"] = max(0, min(10, target["position"] - gold_difference))
    return f"{target['display_name']} gets pushed {gold_difference} positions."


def passwall(caster, target, game):
    caster["position"] = max(0, min(10, caster["position"] + 3))
    target["position"] = max(0, min(10, target["position"] + 2))
    return f"{caster['display_name']} advances 3 positions. {target['display_name']} advances 2 positions."


def dimension_door(caster, target, game):
    caster["position"], target["position"] = target["position"], caster["position"]
    return f"{caster['display_name']} and {target['display_name']} swap positions."


def chain_lightning(caster, target, game):
    target["position"] = max(0, min(10, target["position"] - 3))
    target_of_target = game["players"].get(target["target"])
    if target_of_target:
        target_of_target["position"] = max(0, min(10, target_of_target["position"] - 2))
        return f"{target['display_name']} gets pushed 3 positions. {target_of_target['display_name']} gets pushed 2 positions."
    return f"{target['display_name']} gets pushed 3 positions."


def imprisonment(caster, target, game):
    poorer_wizards = [p for p in game["players"].values() if p["gold"] < target["gold"]]
    for wizard in poorer_wizards:
        target["gold"] -= 1
        wizard["gold"] += 1
    return f"{target['display_name']} loses {len(poorer_wizards)} gold, distributed among poorer wizards."


def wall_of_force(caster, target, game):
    caster["position"] = max(0, min(10, caster["position"] + 2))
    target["position"] = max(0, min(10, target["position"] - 2))
    return f"{caster['display_name']} advances 2 positions. {target['display_name']} gets pushed 2 positions."


def confusion(caster, target, game):
    caster["position"] = max(0, min(10, caster["position"] + 2))
    target_of_target = game["players"].get(target["target"])
    if target_of_target:
        player_ids = list(game["players"].keys())
        current_index = player_ids.index(target["target"])
        next_index = (current_index + 1) % len(player_ids)
        target["target"] = player_ids[next_index]
        return (f"{caster['display_name']} advances 2 positions. {target['display_name']}'s target is now "
                f"{game['players'][target['target']]['display_name']}.")
    return f"{caster['display_name']} advances 2 positions."


def burning_hands(caster, target, game):
    target["position"] = max(0, min(10, target["position"] - 1))
    target["gold"] -= 1
    return f"{target['display_name']} gets pushed 1 position and loses 1 gold."


def dominate_person(caster, target, game):
    target["position"] = max(0, min(10, target["position"] - 3))
    target["gold"] -= 1
    caster["gold"] += 1
    return f"{target['display_name']} gets pushed 3 positions and loses 1 gold. {caster['display_name']} gains 1 gold."


def fear(caster, target, game):
    poorer_wizards = [p for p in game["players"].values() if p["gold"] < target["gold"]]
    target["position"] = max(0, min(10, target["position"] - 2 * len(poorer_wizards)))
    return f"{target['display_name']} gets pushed {2 * len(poorer_wizards)} positions."


def meteor_swarm(caster, target, game):
    decrement = 1
    meteor_swarm_index = next((i for i, spell in enumerate(game["grimoire"]) if spell["emoji"] == "🖐️"), -1)

    if meteor_swarm_index != -1:
        for spell in game["grimoire"][meteor_swarm_index + 1:]:
            decrement += 2

    target["position"] = max(0, min(10, target["position"] - decrement))
    return f"{target['display_name']} gets pushed {decrement} positions."


def counterspell(caster, target, game):
    caster["position"] = max(0, min(10, caster["position"] + 2))
    target["chosen_spell"] = "❌"
    target.pop("target", None)
    return f"{caster['display_name']} advances 2 positions. {target['display_name']}'s spell is negated."


def feeblemind(caster, target, game):
    total_gold = caster["gold"] + target["gold"]
    caster["gold"] = total_gold // 2
    target["gold"] = total_gold - caster["gold"]
    return f"{caster['display_name']} and {target['display_name']} split their gold equally."


def charm_person(caster, target, game):
    poorer_wizards = [p for p in game["players"].values() if p["gold"] < target["gold"]]
    if poorer_wizards:
        chosen_wizard = random.choice(poorer_wizards)
        target["gold"] -= 2
        chosen_wizard["gold"] += 2
        return f"{target['display_name']} loses 2 gold. {chosen_wizard['display_name']} gains 2 gold."
    else:
        target["gold"] -= 2
        return f"{target['display_name']} loses 2 gold."


def telekinesis(caster, target, game):
    target["position"] = max(0, min(10, caster["position"] + 1))
    return f"{target['display_name']} gets pushed to {caster['display_name']}'s position + 1."


def stinking_cloud(caster, target, game):
    target["position"] = max(0, min(10, target["position"] - 3))
    affected_players = []
    for player in game["players"].values():
        if player != target and abs(player["position"] - target["position"]) == 1:
            player["position"] = max(0, min(10, player["position"] - 1))
            affected_players.append(player["display_name"])
    return f"{target['display_name']} gets pushed 3 positions. {', '.join(affected_players)} get pushed 1 position."


def antimagic_field(caster, target, game):
    caster["position"] = max(0, min(10, caster["position"] + 2))
    random_spell = random.choice(SPELLS)
    target["chosen_spell"] = random_spell["emoji"]
    spell_effects[random_spell["emoji"]](caster, target, game)
    return (f"{caster['display_name']} advances 2 positions. {target['display_name']}'s spell is transformed into a "
            f"wild surge!")


def misty_step(caster, target, game):
    caster["position"] = max(0, min(10, target["position"]))
    return f"{caster['display_name']} teleports to {target['display_name']}'s position."


spell_effects = {
    "🫳": color_spray,
    "✊️": fireball,
    "🫴": ice_storm,
    "🤭": vampire_touch,
    "🖖": polymorph,
    "🫲": passwall,
    "🤞": dimension_door,
    "🙏": chain_lightning,
    "🙌": imprisonment,
    "👌": wall_of_force,
    "🤙": confusion,
    "🤟": burning_hands,
    "🖕": dominate_person,
    "👈": fear,
    "🖐️": meteor_swarm,
    "🫷": counterspell,
    "🤌": feeblemind,
    "🫶": charm_person,
    "🤏": telekinesis,
    "✌️": stinking_cloud,
    "👎": antimagic_field,
    "👍": misty_step,
}


class Game(commands.Cog, name="game"):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.active_games = {}
        self.player_order = {}

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
        await ctx.send("Game started! Use `/join_rpw` to join. Waiting for 3 to 6 players...")

    @commands.hybrid_command(name="join_rpw", description="Join an active game.")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def join_rpw(self, ctx: Context) -> None:
        if ctx.guild.id not in self.active_games:
            await ctx.send("No active game to join. Start a new game with `/start_rpw`.", ephemeral=True, delete_after=20)
            return

        game = self.active_games[ctx.guild.id]
        if ctx.author.id in game["players"]:
            await ctx.send("You have already joined the game.", ephemeral=True, delete_after=20)
            return

        display_name = ctx.author.display_name

        game["players"][ctx.author.id] = {
            "member": ctx.author,
            "gold": 3,
            "position": 5,
            "display_name": display_name
        }
        if ctx.guild.id not in self.player_order:
            self.player_order[ctx.guild.id] = []
        self.player_order[ctx.guild.id].append(ctx.author.id)
        await ctx.send(f"{ctx.author.mention} has joined the game! ({len(game['players'])}/6 players)")

        if 1 <= len(game["players"]) <= 6 and not game.get("game_started"):
            game["game_started"] = True
            await self.check_and_start_game(ctx.guild.id)

    @commands.hybrid_command(name="end_game", description="Ends the current game.")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def end_game(self, ctx: Context) -> None:
        if ctx.guild.id not in self.active_games:
            await ctx.send("No active game to end.")
            return

        del self.active_games[ctx.guild.id]
        del self.player_order[ctx.guild.id]
        await ctx.send("The game has been ended.")

    async def check_and_start_game(self, guild_id: int) -> None:
        await asyncio.sleep(10)
        game = self.active_games[guild_id]
        if 1 <= len(game["players"]) <= 6:
            await self.start_game_with_players(guild_id)

    async def start_game_with_players(self, guild_id: int) -> None:
        game = self.active_games[guild_id]
        channel = game["channel"]
        players = game["players"]

        if not game.get("start_message_sent"):
            player_mentions = [player_data["member"].mention for player_data in players.values()]
            await channel.send(f"Game starting with {len(players)} players: {', '.join(player_mentions)}")
            game["start_message_sent"] = True

        await self.update_game_board(guild_id)

        await channel.send("First round starting!", delete_after=20)

    async def update_game_board(self, guild_id: int) -> None:
        game = self.active_games[guild_id]
        channel = game["channel"]
        board = [" "] * 11

        position_dict = {i: [] for i in range(11)}

        for player_data in game["players"].values():
            display_name = player_data["display_name"]
            position_dict[player_data["position"]].append(display_name)

        for position, names in position_dict.items():
            board[position] = ", ".join(names)

        embed = discord.Embed(title="Game Board")
        board_str = "🛑 |" + "|".join(board) + "| 💰"
        embed.add_field(name="Board", value=f"`{board_str}`", inline=False)

        grimoire_str = " | ".join([spell["emoji"] for spell in game["grimoire"]])
        embed.add_field(name="Grimoire", value=grimoire_str, inline=False)

        spell_order = [game["players"][player_id]["display_name"] for player_id in self.player_order[guild_id]]
        spell_order_str = " -> ".join(spell_order)
        embed.add_field(name="Spell Order", value=spell_order_str, inline=False)

        for player_data in game["players"].values():
            embed.add_field(name=player_data["display_name"], value=f"Gold: {player_data['gold']}", inline=True)

        if "message" in game:
            await game["message"].edit(embed=embed)
        else:
            game["message"] = await channel.send(embed=embed)

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

        if target.id == ctx.author.id:
            await ctx.send("You cannot cast a spell on yourself.", ephemeral=True)
            return

        spell = spell.lower()
        valid_spells = {s["name"].lower(): s["emoji"] for s in game["grimoire"]}
        valid_spells.update({s["emoji"]: s["emoji"] for s in game["grimoire"]})

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
        order = [game["players"][player_id] for player_id in self.player_order[guild_id]]
        spell_pairs = {}
        processed_players = set()

        async def send_embed(title, description, color, delete_after):
            embed = discord.Embed(title=title, description=description, color=color)
            await channel.send(embed=embed, delete_after=delete_after)

        for player_data in order:
            player_id = player_data["member"].id
            target_id = player_data.get("target")
            spell = player_data["chosen_spell"]

            if target_id and target_id in spell_pairs and spell_pairs[target_id] == player_id:
                if game["players"][target_id]["chosen_spell"] == spell:
                    random_spell_1, random_spell_2 = random.sample(SPELLS, 2)
                    player_data["chosen_spell"] = random_spell_1["emoji"]
                    game["players"][target_id]["chosen_spell"] = random_spell_2["emoji"]

                    description = (
                        f"{player_data['member'].display_name} gets {random_spell_1['name']} {random_spell_1['emoji']}.\n"
                        f"{game['players'][target_id]['member'].display_name} gets {random_spell_2['name']} {random_spell_2['emoji']}."
                    )
                    await send_embed("Wild Surge!", description, 0xFF0000, 20)
            else:
                if target_id:
                    spell_pairs[player_id] = target_id

        # Reveal spells
        for player_data in order:
            player_id = player_data["member"].id
            if player_id in processed_players:
                continue

            player = player_data["member"]
            spell = player_data["chosen_spell"]
            target_id = player_data.get("target")

            if not target_id:
                continue

            target = game["players"][target_id]["member"]
            spell_name = next(s["name"] for s in SPELLS if s["emoji"] == spell)
            description = f"{player.display_name} casts {spell_name} {spell} on {target.display_name}."
            await send_embed("Spell Cast", description, 0x00FF00, 30)

            result = ""
            if spell == "❌":
                result = f"The spell of {player.display_name} was negated."
            else:
                try:
                    result = spell_effects[spell](player_data, game["players"][target_id], game)
                except KeyError:
                    result = f"The spell of {player.display_name} was negated."

            await self.update_game_board(guild_id)
            await send_embed("Spell Effect", result, 0x00FF00, 30)

            processed_players.add(player_id)
            await asyncio.sleep(10)

        for player_data in game["players"].values():
            player_data.pop("chosen_spell", None)
            player_data.pop("target", None)

        await self.end_round(guild_id)

    async def end_round(self, guild_id: int) -> None:
        game = self.active_games[guild_id]
        channel = game["channel"]

        await channel.send("End of the round!", delete_after=20)

        positions = sorted(game["players"].values(), key=lambda p: p["position"], reverse=True)
        first_place = [p for p in positions if p["position"] == positions[0]["position"]]
        second_place = [p for p in positions if
                        len(positions) > len(first_place) and p["position"] == positions[len(first_place)]["position"]]

        first_gold = 0
        second_gold = 0

        if not second_place or len(first_place) == len(game["players"]):
            total_gold = 6
            gold_per_player = (total_gold + len(game["players"]) - 1) // len(game["players"])
            for player in game["players"].values():
                player["gold"] += gold_per_player
            first_gold = gold_per_player
        else:
            gold_split = lambda total, count: (total // count, total % count)
            first_gold, first_remainder = gold_split(4, len(first_place))
            second_gold, second_remainder = gold_split(2, len(second_place))

            for player in first_place:
                player["gold"] += first_gold + (1 if first_remainder > 0 else 0)
                first_remainder -= 1

            for player in second_place:
                player["gold"] += second_gold + (1 if second_remainder > 0 else 0)
                second_remainder -= 1

        embed = discord.Embed(title="Round Results", color=0x00FF00)
        first_place_names = ", ".join([p["member"].display_name for p in first_place])
        second_place_names = ", ".join([p["member"].display_name for p in second_place])
        if first_place:
            embed.add_field(name="First Place", value=f"{first_place_names} gained {first_gold} gold.", inline=False)
        if second_place:
            embed.add_field(name="Second Place", value=f"{second_place_names} gained {second_gold} gold.", inline=False)
        await channel.send(embed=embed, delete_after=30)

        for player_data in game["players"].values():
            if player_data["position"] in [0, 1, 2]:
                player_data["position"] = 3
            elif player_data["position"] in [8, 9, 10]:
                player_data["position"] = 7

        winners = [p for p in game["players"].values() if p["gold"] >= 25]
        if winners:
            winner_mentions = ", ".join([p["member"].mention for p in winners])
            await channel.send(f"Game over! The winner(s): {winner_mentions}")
            del self.active_games[guild_id]
            del self.player_order[guild_id]
        else:
            new_spell = random.choice([spell for spell in SPELLS if spell not in game["grimoire"]])
            game["grimoire"].pop(0)
            game["grimoire"].append(new_spell)

            self.player_order[guild_id].append(self.player_order[guild_id].pop(0))
            await self.update_game_board(guild_id)

            await channel.send("Next round starting!", delete_after=20)

    @commands.hybrid_command(name="spell_book", description="Displays all spells with their emojis and effects.")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def spell_book(self, ctx: Context) -> None:
        embed = discord.Embed(title="Spell Book", color=0x00FF00)
        for spell in SPELLS:
            embed.add_field(
                name=f"{spell['emoji']} {spell['name']}",
                value=spell['description'],
                inline=False
            )
        await ctx.send(embed=embed, ephemeral=True)


async def setup(bot) -> None:
    await bot.add_cog(Game(bot))
    await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
