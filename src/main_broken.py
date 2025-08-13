import os
import random
import re
from typing import Tuple, Optional, List, Any, Dict, Union
import time
import discord
import numpy as np
import tiktoken
from discord.ext import commands
from dotenv import load_dotenv
from pinecone import Pinecone
from sentence_transformers import SentenceTransformer
import anthropic
from whoosh.index import open_dir
from whoosh.qparser import QueryParser

# Importera lokala moduler
from color_handler import ColorHandler
from roll_tracker import RollTracker
from combat_manager import CombatManager
from damage_tables import DamageType
from hit_tables import WeaponType  # om du vill ha typ-checking
from fumble_tables import FUMBLE_TABLES, WEAPON_TYPE_ALIASES

# Import för ytterligare moduler
import stats_commands
# Import för Skjut dom i huvudet
from skjutdomihuvudet import commands as sdih_commands
# Import för nya kommandomoduler
from commands import admin_commands
from commands.dice_commands import register_dice_commands
from commands.knowledge_commands import register_knowledge_commands
from commands.combat_commands import register_combat_commands
from commands.utility_commands import register_utility_commands

# Import för rollpersonsskapande
import character_creation
import interactive_chargen

# Import för nya modulära komponenter
from core.constants import (
    UMNATAK_ID, MAX_DICE, MAX_SIDES, MAX_MESSAGE_LENGTH, 
    MAX_TOKENS, UMNATAK_SUCCESS_COMMENTS
)
from utils.text_utils import clean_unicode, split_message, count_tokens
from core.dice_parser import parse_dice_string
from core.dice_engine import unlimited_d6s, simulate_unlimited_dice
from core.knowledge_base import KnowledgeBase

# Ladda miljövariabler från .env-filen
load_dotenv()

# Hämta tokens och API-nycklar från miljövariablerna
DISCORD_TOKEN: Optional[str] = os.getenv('DISCORD_TOKEN')
CHANNEL_IDS: Optional[str] = os.getenv('CHANNEL_IDS')
PINECONE_API_KEY: Optional[str] = os.getenv("PINECONE_API_KEY")
ANTHROPIC_API_KEY: Optional[str] = os.getenv("ANTHROPIC_API_KEY")
PINECONE_INDEX_NAME: str = os.getenv("PINECONE_INDEX_NAME", "rpg-knowledge")

# Konfigurera Discord-boten med nödvändiga behörigheter
intents: discord.Intents = discord.Intents.default()
intents.message_content = True
bot: commands.Bot = commands.Bot(command_prefix='!', intents=intents)

# Initiera hjälputrustning
color_handler: ColorHandler = ColorHandler()
roll_tracker: RollTracker = RollTracker()
combat_manager: CombatManager = CombatManager()

# Konfigurera mappar för regler och kunskapsindex
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
RULES_FOLDER: str = os.path.join(project_root, "data", "rules")
INDEX_FOLDER: str = os.path.join(project_root, "data", "knowledge_index")

# Skapa mappen om den inte finns
if not os.path.exists(RULES_FOLDER):
    os.makedirs(RULES_FOLDER)

# Globala objekt
knowledge_base = KnowledgeBase()

# Umnatak-relaterade variabler nu importerade från src.core.constants

def load_umnatak_comments():
    """
    Laddar in syrliga kommentarer för Umnatak från en textfil.
    Varje rad i filen blir en separat kommentar.
    """
    comments_file = os.path.join(project_root, "data", "config", "umnak_comments.txt")
    try:
        if os.path.exists(comments_file):
            with open(comments_file, 'r', encoding='utf-8') as f:
                # Läs in alla rader och filtrera bort tomma rader
                global UMNATAK_SUCCESS_COMMENTS
                UMNATAK_SUCCESS_COMMENTS = [line.strip() for line in f.readlines() if line.strip()]
            print(f"Laddade {len(UMNATAK_SUCCESS_COMMENTS)} kommentarer för Umnatak")
        else:
            print(f"Varning: Kunde inte hitta kommentarsfilen: {comments_file}")
            # Sätt några standardkommentarer om filen saknas
            UMNATAK_SUCCESS_COMMENTS = [
                "Wow, du lyckades faktiskt!",
                "Statistisk anomali - Umnatak lyckades.",
                "En högst oväntad framgång."
            ]
    except Exception as e:
        print(f"Fel vid inläsning av Umnatak-kommentarer: {e}")
        UMNATAK_SUCCESS_COMMENTS = ["Ovanligt att se dig lyckas, Umnatak!"]

def get_sarcastic_comment_for_umnatak() -> Optional[str]:
    """
    Returnerar en slumpmässig syrlig kommentar om Umnatak, men endast cirka 30% av gångerna.
    Övriga gånger returneras None för att inte överanvända skämten.
    """
    # Använd tidsbaserat seed för att variera sannolikheten
    random.seed(int(time.time()))
    
    # Endast cirka 30% av gångerna returnera en kommentar
    if random.random() < 0.3:  # 30% chans
        return random.choice(UMNATAK_SUCCESS_COMMENTS)
    return None

# Kunskapsbasfunktioner nu i core.knowledge_base.KnowledgeBase-klassen

# Funktioner count_tokens, clean_unicode, split_message nu importerade från src.utils.text_utils

# parse_dice_string nu importerad från src.core.dice_parser

# unlimited_d6s och simulate_unlimited_dice nu importerade från src.core.dice_engine

# Bot event handlers and commands

@bot.event
async def on_ready() -> None:
    """Skriver ut ett meddelande när boten har kopplat upp sig mot Discord."""
    print(f"{bot.user} has connected to Discord!")
    print(f"Working directory: {os.getcwd()}")
    print(f"Rules folder: {RULES_FOLDER}")
    print(f"Index folder: {INDEX_FOLDER}")
    
        # LÄGG TILL DESSA RADER HÄR, INNE I FUNKTIONEN
    try:
        bot.tree.clear_commands(guild=None)
        await bot.tree.sync()
        print('Cleared all slash commands - only prefix commands (!ex) will work now')
    except Exception as e:
        print(f'Failed to clear slash commands: {e}')
    # SLUT PÅ NYA RADER
    
    
    # Ladda in Umnatak-kommentarer
    load_umnatak_comments()
    
    # Initiera kunskapsbasen vid start
    success = knowledge_base.initialize_knowledge_base()
    if success:
        print("Kunskapsbasen initierad och redo att användas.")
    else:
        print("Kunde inte initiera kunskapsbasen. Kommandot !ask kommer inte att fungera korrekt.")
        
    # Registrera statistikkommandona
    stats_commands.register_commands(bot, roll_tracker, color_handler)
    print("Statistikkommandon har registrerats (allstats, mystatsall).")
    
    # Registrera Skjut dom i huvudet-kommandon
    sdih_commands.register_commands(bot, roll_tracker, color_handler)
    print("Skjut dom i huvudet-kommandon har registrerats (rull, fördel, nackdel, etc.).")
    
    # Registrera admin-kommandon
    admin_commands.register_admin_commands(bot, roll_tracker, color_handler, knowledge_base)
    print("Admin-kommandon har registrerats (startsession, endsession, showsession, secret).")
    
    # Registrera nya modulära kommandon
    register_dice_commands(bot, roll_tracker, color_handler, knowledge_base)
    print("Tärningskommandon har registrerats (roll, ex, count, chance).")
    
    register_knowledge_commands(bot, knowledge_base, color_handler)
    print("Kunskapskommandon har registrerats (ask, allt, sök).")
    
    register_combat_commands(bot, combat_manager, color_handler)
    print("Stridskommandon har registrerats (hugg, stick, kross, fummel).")
    
    register_utility_commands(bot, roll_tracker, color_handler)
    print("Verktygskommandon har registrerats (dicehelp, stats, mystats, regel, höj).")
    

        
        
        










# ex command nu registrerat via dice_commands modul

    color: int = color_handler.get_user_color(ctx.author.id)
    embed: discord.Embed = discord.Embed(
        title="Session Statistics",
        description=(
            f"Session: {session_id or roll_tracker.current_session}\n"
            f"Total Players: {stats['session_info']['unique_players']}\n"
            f"Total Rolls: {stats['session_info']['total_rolls']}"
        ),
        color=color
    )
    session_info: dict = stats["session_info"]
    embed.add_field(
        name="Session Info",
        value=(
            f"Started: {session_info['start_time']}\n"
            f"{'Ended: ' + session_info['end_time'] if session_info['end_time'] else 'Still active'}\n"
            f"Description: {session_info['description'] or 'No description'}"
        ),
        inline=False
    )

    players_text: str = ""
    for player in stats["player_stats"]:
        players_text += (
            f"**{player['name']}**\n"
            f"Rolls: {player['total_rolls']}"
        )
        if player['successes'] + player['failures'] > 0:
            players_text += f" (Success rate: {player['success_rate']}%)"
        players_text += "\n"
    if players_text:
        embed.add_field(name="Player Statistics", value=players_text, inline=False)

    if stats["command_stats"]:
        cmd_text: str = "\n".join(
            f"{cmd['command']}: {cmd['uses']} uses" +
            (f" ({cmd['success_rate']}% success)" if cmd['success_rate'] is not None else "")
            for cmd in stats["command_stats"]
        )
        embed.add_field(name="Command Usage", value=cmd_text, inline=False)

    if stats["popular_dice"]:
        dice_text: str = "\n".join(
            f"{dice['type']}: {dice['uses']} times"
            for dice in stats["popular_dice"]
        )
        embed.add_field(name="Most Used Dice", value=dice_text, inline=False)

    await ctx.send(embed=embed)

    color: int = color_handler.get_user_color(ctx.author.id)
    embed: discord.Embed = discord.Embed(
        title=f"Stats for {ctx.author.display_name}",
        description=f"Session: {session_id or roll_tracker.current_session}",
        color=color
    )

    recent_rolls: List[dict] = stats["rolls"][:5]
    if recent_rolls:
        roll_text: str = "\n".join(
            f"{r['command']} {r['dice']}" +
            (f" (Target: {r['target']})" if r['target'] else "") +
            f": {r['values']}" +
            (f" {'✅' if r['success'] else '❌'}" if r['success'] is not None else "")
            for r in recent_rolls
        )
        embed.add_field(name="Recent Rolls", value=roll_text, inline=False)
    else:
        embed.add_field(name="Recent Rolls", value="No rolls yet", inline=False)

    await ctx.send(embed=embed)

        response: str = "**Tillgängliga regler:**\n"
        for i, rule_file in enumerate(rules, start=1):
            rule_name: str = os.path.splitext(rule_file)[0]
            response += f"{i}. {rule_name}\n"
        await ctx.send(response)
    else:
        identifier: str = args[0].lower()
        rules: List[str] = os.listdir(RULES_FOLDER)
        try:
            if identifier.isdigit():
                rule_index: int = int(identifier) - 1
                if rule_index < 0 or rule_index >= len(rules):
                    raise IndexError
                rule_file: str = rules[rule_index]
            else:
                rule_file = f"{identifier}.txt"
                if rule_file not in rules:
                    raise FileNotFoundError

            with open(os.path.join(RULES_FOLDER, rule_file), "r", encoding="utf-8") as f:
                content: str = f.read()

            rule_name: str = os.path.splitext(rule_file)[0]
            if len(content) <= 2000:
                await ctx.send(f"**{rule_name}**:\n{content}")
            else:
                chunks: List[str] = [content[i:i+2000] for i in range(0, len(content), 2000)]
                await ctx.send(f"**{rule_name}**: (uppdelat i flera meddelanden)")
                for chunk in chunks:
                    await ctx.send(chunk)
        except (IndexError, FileNotFoundError):
            await ctx.send("Regeln kunde inte hittas. Kontrollera namnet eller numret.")

character_creation.register_commands(bot, roll_tracker, color_handler)

        # Logga slaget i statistiken
        roll_tracker.log_roll(
            user_id=str(ctx.author.id),
            user_name=ctx.author.display_name,
            command_type='höj',
            num_dice=num_dice,
            sides=6,
            roll_values=all_rolls,
            modifier=0,
            target=skill_chance,
            success=success
        )
            
        await ctx.send(embed=embed)
        
    except ValueError as e:
        await ctx.send(f"Fel: {str(e)}\nAnvändning: `!höj [färdighetschans] [--ll om lättlärd]`")

def main():
    """
    Huvudfunktion som initierar och startar Discord-boten.
    """
    # Kontrollera att tokens finns
    if not DISCORD_TOKEN:
        print("Fel: DISCORD_TOKEN saknas i .env-filen!")
        return
    
    # Skriv ut startinformation
    print(f"Startar Diceroller Bot")
    print(f"Working directory: {os.getcwd()}")
    print(f"Rules folder: {RULES_FOLDER}")
    print(f"Index folder: {INDEX_FOLDER}")
    
    # Visa tillgängliga kanaler
    if CHANNEL_IDS:
        channels = CHANNEL_IDS.split(',')
        print(f"Bot konfigurerad för {len(channels)} kanaler: {', '.join(channels)}")

    # Starta boten
    print(f"Ansluter till Discord...")
    bot.run(DISCORD_TOKEN)

if __name__ == "__main__":
    main()