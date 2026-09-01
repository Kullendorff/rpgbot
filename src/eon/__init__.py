"""
EON RPG-mekanik (Trudvang-liknande d100-system).

Ren mekanik utan Discord-beroenden: träfftabeller, skadetabeller,
fummeltabeller och stridshantering. Kommandon (Cog) ligger i eon.commands
och re-exporteras ALDRIG härifrån — samma mönster som deltagreen/,
dragonbane/ och starwars/ (spindel/ är den medvetet avvikande, avstängda
modulen).

Importstil: relativt inuti paketet, absolut mot delad infrastruktur
(core.*, migration.*, etc.).
"""

from .hit_tables import (
    WeaponType,
    AttackLevel,
    BASE_HIT_TABLE,
    get_hit_location,
)
from .damage_tables import (
    DamageType,
    DamageResult,
    DamageCalculator,
    parse_effect_code,
)
from .fumble_tables import (
    FUMBLE_TABLES,
    WEAPON_TYPE_ALIASES,
)
from .combat_manager import (
    CombatResult,
    CombatManager,
)

__all__ = [
    "WeaponType",
    "AttackLevel",
    "BASE_HIT_TABLE",
    "get_hit_location",
    "DamageType",
    "DamageResult",
    "DamageCalculator",
    "parse_effect_code",
    "FUMBLE_TABLES",
    "WEAPON_TYPE_ALIASES",
    "CombatResult",
    "CombatManager",
]
