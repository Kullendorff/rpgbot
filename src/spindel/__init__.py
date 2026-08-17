"""
Spindel-modul: gigantspindel- och småspindelstrid för EON.

Flyttad hit som en egen paketmodul (2026-08-16) från löst utspridda filer i
src/ och src/commands/. Modulen är AVSTÄNGD tills vidare — se
config/feature_flags.py ("slash_spindel_enabled": False). Sätt flaggan till
True och starta om boten för att slå på den igen; ingen annan kod behöver
ändras.

Innehåll:
  * spider_damage_tables.py / spider_combat_manager.py — gigantspindel
  * small_spider_tables.py / small_spider_manager.py — småspindlar
  * slash_spider_commands.py / slash_small_spider_commands.py — Discord-lagret

Till skillnad från deltagreen/dragonbane/starwars använder spindelkommandona
inte Cog-mönstret utan registrerar löst via bot.tree.command i respektive
register_slash_*-funktion (äldre mönster, oförändrat vid flytten).
"""

from .slash_spider_commands import register_slash_spider_commands
from .slash_small_spider_commands import register_slash_small_spider_commands

__all__ = [
    'register_slash_spider_commands',
    'register_slash_small_spider_commands',
    'register_slash_spindel_commands',
]


async def register_slash_spindel_commands(bot, color_handler) -> None:
    """Registrera hela spindelavsnittet (gigantspindel + småspindlar) i ett anrop."""
    await register_slash_spider_commands(bot, color_handler)
    await register_slash_small_spider_commands(bot, color_handler)
