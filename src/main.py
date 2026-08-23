import os
os.environ['FOR_DISABLE_CONSOLE_CTRL_HANDLER'] = '1'
import asyncio
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

# Initialize logging FIRST before any other imports
from core.logging_config import setup_logging, get_logger

# Set up logging
setup_logging()
logger = get_logger(__name__)

# Importera gamla moduler (ska flyttas till utils/)
from color_handler import ColorHandler
from roll_tracker import RollTracker
from combat_manager import CombatManager
from damage_tables import DamageType
from hit_tables import WeaponType  # om du vill ha typ-checking
from fumble_tables import FUMBLE_TABLES, WEAPON_TYPE_ALIASES

# Import för ytterligare moduler
# Import för Skjut dom i huvudet
from skjutdomihuvudet import commands as sdih_commands

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


# Global felhantering: utan dessa fick oväntade fel användaren att se tysta
# "The application did not respond" eftersom ingen handler fångade dem.
# Medvetet minimalt — per-cog-hantering och _send_error()-helpers är
# robusthetsfasen, inte detta skyddsnät.
@bot.event
async def on_app_command_error(interaction: discord.Interaction, error: discord.app_commands.AppCommandError) -> None:
    """Fångar oväntade fel i alla slash-kommandon: logga full stacktrace, svara generiskt."""
    cmd_name = getattr(getattr(interaction, "command", None), "name", "?")
    logger.error(f"Oväntat fel i /{cmd_name}: {error}", exc_info=error)
    try:
        if interaction.response.is_done():
            await interaction.followup.send("Ett internt fel uppstod. Det har loggats.", ephemeral=True)
        else:
            await interaction.response.send_message("Ett internt fel uppstod. Det har loggats.", ephemeral=True)
    except discord.HTTPException:
        pass


@bot.event
async def on_command_error(ctx: commands.Context, error: commands.CommandError) -> None:
    """Fångar oväntade fel i prefix-kommandon: logga full stacktrace, meddela användaren."""
    if isinstance(error, commands.CommandNotFound):
        return  # okända kommandon hanteras tyst, som tidigare
    logger.error(f"Oväntat fel i '{ctx.command}': {error}", exc_info=error)
    try:
        await ctx.send("Ett internt fel uppstod. Det har loggats.")
    except discord.HTTPException:
        pass


@bot.event
async def on_ready() -> None:
    """Skriver ut ett meddelande när boten har kopplat upp sig mot Discord."""
    logger.info(f"{bot.user} has connected to Discord!")
    logger.info(f"Working directory: {os.getcwd()}")
    logger.info(f"Rules folder: {RULES_FOLDER}")
    logger.info(f"Index folder: {INDEX_FOLDER}")
    
    # Registrera slash commands enligt feature flags
    # Lägg till project_root till sys.path för att hitta config-modulen
    import sys
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
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
    
    if FEATURE_FLAGS["slash_admin_enabled"]:
        from commands.slash_admin_commands import register_slash_admin_commands
        await register_slash_admin_commands(bot, roll_tracker, color_handler, embed_factory, knowledge_base)

    # Registrera Delta Green kommandon
    if FEATURE_FLAGS.get("slash_deltagreen_enabled", False):
        from deltagreen.commands import register_slash_dg_commands
        from deltagreen import AgentManager, SessionManager
        dg_agent_manager = AgentManager()
        dg_session_manager = SessionManager()
        await register_slash_dg_commands(bot, embed_factory, dg_agent_manager, dg_session_manager)
        logger.info("Delta Green kommandon registrerade (/dgcheck, /dgluck, /dgstat, /dglethality, /dgsan, /dgagent, /dgroll, /dggmroll, /dggmstatus, /dggmset, /dgstartsession, /dgendsession).")

    # Registrera Dragonbane kommandon (modul av Jonas, github.com/jonsal/dragonbane)
    if FEATURE_FLAGS.get("slash_dragonbane_enabled", False):
        from dragonbane.commands import register_slash_dragonbane_commands
        await register_slash_dragonbane_commands(bot, embed_factory)
        logger.info("Dragonbane kommandon registrerade (/dod_slag, /dod_fv, /dod_skada, /dod_pressa, /dod_hoj, /dod_skrack, /dod_mumie, /dod_init).")

    # Registrera Star Wars D6 kommandon (WEG40120, 2nd Ed. Revised & Expanded)
    if FEATURE_FLAGS.get("slash_starwars_enabled", False):
        from starwars.commands import register_slash_starwars_commands
        await register_slash_starwars_commands(bot, embed_factory)
        logger.info("Star Wars D6 kommandon registrerade (/sw_slag, /sw_motstand, /sw_svarighet, /sw_init).")

    # Registrera kommentarkommandon FÖRE sync
    from commands.slash_comment_commands import register_slash_comment_commands
    register_slash_comment_commands(bot, user_settings, comment_generator, color_handler)
    logger.info("Slash kommentarkommandon registrerade (/kommentarer).")

    # Registrera hemliga manipulationskommandon FÖRE sync
    from commands.slash_manipulation_commands import register_slash_manipulation_commands
    register_slash_manipulation_commands(bot, manipulation_manager, color_handler)
    logger.info("Slash manipulationskommandon registrerade (hemliga).")
    
    # DEBUG: Lägg till debug kommando för att testa användarpermissions (endast om DEBUG miljövariabel är satt)
    DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"
    if DEBUG_MODE:
        from debug_user_info import register_debug_command
        register_debug_command(bot)
        logger.debug("DEBUG MODE: Debug kommando registrerat")

    # Registrera Skjut dom i huvudet-kommandon
    sdih_commands.register_commands(bot, roll_tracker, color_handler)
    logger.info("Skjut dom i huvudet-kommandon har registrerats (rull, fördel, nackdel, etc.).")

    # Registrera spindelkommandon (gigantspindlar och små spindlar).
    # Flyttade till en egen paketmodul (src/spindel/) och avstängda tills
    # vidare — sätt slash_spindel_enabled: True i config/feature_flags.py
    # för att slå på dem igen.
    if FEATURE_FLAGS.get("slash_spindel_enabled", False):
        from spindel import register_slash_spindel_commands
        await register_slash_spindel_commands(bot, color_handler)
        logger.info("Spindelkommandon registrerade (gigantspindel + småspindlar).")

    # Synka slash commands EFTER alla registreringar
    try:
        # Försök guild-specific sync först (instant) om GUILD_ID finns i .env
        guild_id = os.getenv("GUILD_ID")
        if guild_id:
            guild = discord.Object(id=int(guild_id))
            # VIKTIGT: Kopiera globala kommandon till guilden först!
            bot.tree.copy_global_to(guild=guild)
            # Rensa globala kommandon för att undvika dubbletter
            bot.tree.clear_commands(guild=None)
            synced = await bot.tree.sync(guild=guild)
            logger.info(f"Synced {len(synced)} slash commands to guild {guild_id} (instant)")
            # Synka tomma globala kommandon
            await bot.tree.sync()
        else:
            synced = await bot.tree.sync()
            logger.info(f"Synced {len(synced)} slash commands globally (may take up to 1 hour)")

        # Debug: Lista alla synkade kommandon
        logger.info("SYNKADE KOMMANDON:")
        for cmd in synced:
            logger.info(f"  - /{cmd.name}: {cmd.description}")
    except Exception as e:
        logger.error(f'Failed to sync slash commands: {e}', exc_info=True)

    # Ladda kunskapsbasen i bakgrunden — INTE synkront. Ett synkront anrop
    # här blockerade tidigare event-loopen i ~6 sekunder direkt efter att
    # kommandona synkats, vilket gjorde att interaktioner som kom in under
    # den tiden dog med "404 Unknown Interaction" (Discords 3-sekundersgräns
    # för interaktions-token hann gå ut innan loopen var fri att svara).
    # knowledge_base.ensure_ready() kör den tunga initieringen via
    # asyncio.to_thread och är race-säker mot samtidiga anrop från /ask etc.
    async def _load_knowledge_base_in_background() -> None:
        success = await knowledge_base.ensure_ready()
        if success:
            logger.info("Kunskapsbasen initierad och redo att användas.")
        else:
            logger.warning("Kunde inte initiera kunskapsbasen. Kommandot /ask kommer inte att fungera korrekt.")

    asyncio.create_task(_load_knowledge_base_in_background())
    logger.info("Alla kommandon har registrerats och boten är redo! (Kunskapsbasen laddas i bakgrunden.)")

def main():
    """
    Huvudfunktion som initierar och startar Discord-boten.
    """
    # Kontrollera att tokens finns
    if not DISCORD_TOKEN:
        logger.error("Fel: DISCORD_TOKEN saknas i .env-filen!")
        return

    # Skriv ut startinformation
    logger.info(f"Startar Diceroller Bot")
    logger.info(f"Working directory: {os.getcwd()}")
    logger.info(f"Rules folder: {RULES_FOLDER}")
    logger.info(f"Index folder: {INDEX_FOLDER}")

    # Visa tillgängliga kanaler
    if CHANNEL_IDS:
        channels = CHANNEL_IDS.split(',')
        logger.info(f"Bot konfigurerad för {len(channels)} kanaler: {', '.join(channels)}")

    # Starta boten
    logger.info(f"Ansluter till Discord...")
    bot.run(DISCORD_TOKEN)

if __name__ == "__main__":
    main()