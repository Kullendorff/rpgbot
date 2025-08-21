import os
os.environ['FOR_DISABLE_CONSOLE_CTRL_HANDLER'] = '1'
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

# Importera gamla moduler (ska flyttas till utils/)
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
    MAX_DICE, MAX_SIDES, MAX_MESSAGE_LENGTH, 
    MAX_TOKENS
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

# Skapa embed factory (MÅSTE komma efter color_handler)
from core.embed_factory import EmbedFactory
embed_factory = EmbedFactory(color_handler)

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

# Lägg till nya kommentarsystem
from core.user_settings import UserSettingsManager
from core.comment_styles import CommentGenerator
user_settings = UserSettingsManager()
comment_generator = CommentGenerator()

# Lägg till hemligt manipulationssystem
from core.manipulation_manager import ManipulationManager
manipulation_manager = ManipulationManager()


@bot.event
async def on_ready() -> None:
    """Skriver ut ett meddelande när boten har kopplat upp sig mot Discord."""
    print(f"{bot.user} has connected to Discord!")
    print(f"Working directory: {os.getcwd()}")
    print(f"Rules folder: {RULES_FOLDER}")
    print(f"Index folder: {INDEX_FOLDER}")
    
    # Registrera slash commands enligt feature flags
    import sys
    sys.path.append(os.path.join(project_root))
    from config.feature_flags import FEATURE_FLAGS, is_command_enabled
    if FEATURE_FLAGS["slash_dice_enabled"]:
        from commands.slash_dice_commands import register_slash_dice_commands
        await register_slash_dice_commands(bot, roll_tracker, color_handler, embed_factory, knowledge_base)
    
    if FEATURE_FLAGS["slash_knowledge_enabled"]:
        from commands.slash_knowledge_commands import register_slash_knowledge_commands
        await register_slash_knowledge_commands(bot, knowledge_base, color_handler, embed_factory)
    
    if FEATURE_FLAGS["slash_combat_enabled"]:
        from commands.slash_combat_commands import register_slash_combat_commands
        await register_slash_combat_commands(bot, combat_manager, color_handler, embed_factory)
    
    if FEATURE_FLAGS["slash_utility_enabled"]:
        from commands.slash_utility_commands import register_slash_utility_commands
        await register_slash_utility_commands(bot, roll_tracker, color_handler, embed_factory)
    
    # Synka slash commands EN gång i slutet
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} slash commands with Discord")
    except Exception as e:
        print(f'Failed to sync slash commands: {e}')
    
    # Initiera kunskapsbasen vid start
    success = knowledge_base.initialize_knowledge_base()
    if success:
        print("Kunskapsbasen initierad och redo att användas.")
    else:
        print("Kunde inte initiera kunskapsbasen. Kommandot !ask kommer inte att fungera korrekt.")
        
    # Registrera statistikkommandona
    stats_commands.register_commands(bot, roll_tracker, color_handler, embed_factory)
    print("Statistikkommandon har registrerats (allstats, mystatsall).")
    
    # Registrera Skjut dom i huvudet-kommandon
    sdih_commands.register_commands(bot, roll_tracker, color_handler)
    print("Skjut dom i huvudet-kommandon har registrerats (rull, fördel, nackdel, etc.).")
    
    # Registrera admin-kommandon
    admin_commands.register_admin_commands(bot, roll_tracker, color_handler, embed_factory, knowledge_base)
    print("Admin-kommandon har registrerats (startsession, endsession, showsession, secret).")
    
    # Registrera nya modulära kommandon
    register_dice_commands(bot, roll_tracker, color_handler, embed_factory, knowledge_base)
    print("Tärningskommandon har registrerats (roll, ex, count, chance).")
    
    register_knowledge_commands(bot, knowledge_base, color_handler, embed_factory)
    print("Kunskapskommandon har registrerats (ask, allt, sök).")
    
    register_combat_commands(bot, combat_manager, color_handler, embed_factory)
    print("Stridskommandon har registrerats (hugg, stick, kross, fummel).")
    
    register_utility_commands(bot, roll_tracker, color_handler, embed_factory)
    print("Verktygskommandon har registrerats (dicehelp, stats, mystats, regel, höj).")

    # Registrera kommentarkommandon
    from commands.slash_comment_commands import register_slash_comment_commands
    register_slash_comment_commands(bot, user_settings, comment_generator, color_handler)
    print("✅ Slash kommentarkommandon registrerade (/kommentarer).")

    # Registrera hemliga manipulationskommandon
    from commands.slash_manipulation_commands import register_slash_manipulation_commands
    register_slash_manipulation_commands(bot, manipulation_manager, color_handler)
    print("✅ Slash manipulationskommandon registrerade (hemliga).")

    # Registrera karaktärsgenereringskommandon
    character_creation.register_commands(bot, roll_tracker, color_handler, embed_factory)
    print("Karaktärsgenereringskommandon har registrerats.")
    
    print("Alla kommandon har registrerats och boten är redo!")

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