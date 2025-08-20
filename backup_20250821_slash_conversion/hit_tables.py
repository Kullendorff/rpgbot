# hit_tables.py

import random
from enum import Enum
from typing import Tuple, Optional

class WeaponType(Enum):
    HUGG = "hugg"
    KROSS = "kross"
    STICK = "stick"
    AVSTAND = "avstand"

class AttackLevel(Enum):
    NORMAL = "normal"
    HIGH = "hög"
    LOW = "låg"

#
# ====== R2-45: Träfftabell för Hugg & Kross vs. Stick & Avstånd ======
#

HUGG_KROSS_NORMAL = [
    ((1, 8),   ("huvud",       "ansikte",    "1")),
    ((9, 16),  ("huvud",       "skalle",     "2")),
    ((17, 20), ("huvud",       "hals",       "3")),
    ((21, 24), ("vänster arm", "skuldra",    "4")),
    ((25, 28), ("vänster arm", "överarm",    "6")),
    ((29, 30), ("vänster arm", "armbage",    "8")),
    ((31, 36), ("vänster arm", "underarm",   "10")),
    ((37, 40), ("vänster arm", "hand",       "12")),
    ((41, 44), ("höger arm",   "skuldra",    "5")),
    ((45, 48), ("höger arm",   "överarm",    "7")),
    ((49, 50), ("höger arm",   "armbage",    "9")),
    ((51, 56), ("höger arm",   "underarm",   "11")),
    ((57, 60), ("höger arm",   "hand",       "13")),
    ((61, 70), ("bröstkorg",   "bröstkorg",  "14")),
    ((71, 78), ("buk",         "mage",       "15")),
    ((79, 80), ("buk",         "underliv",   "16")),
    ((81, 82), ("vänster ben", "höft",       "17")),
    ((83, 84), ("vänster ben", "lår",        "19")),
    ((85, 86), ("vänster ben", "knä",        "21")),
    ((87, 89), ("vänster ben", "vad",        "23")),
    ((90, 90), ("vänster ben", "fot",        "25")),
    ((91, 92), ("höger ben",   "höft",       "18")),
    ((93, 94), ("höger ben",   "lår",        "20")),
    ((95, 96), ("höger ben",   "knä",        "22")),
    ((97, 99), ("höger ben",   "vad",        "24")),
    ((100,100),("höger ben",   "fot",        "26"))
]

HUGG_KROSS_HIGH = [
    ((1, 12),  ("huvud",       "ansikte",    "1")),
    ((13,24),  ("huvud",       "skalle",     "2")),
    ((25,30),  ("huvud",       "hals",       "3")),
    ((31,36),  ("vänster arm", "skuldra",    "4")),
    ((37,42),  ("vänster arm", "överarm",    "6")),
    ((43,45),  ("vänster arm", "armbage",    "8")),
    ((46,54),  ("vänster arm", "underarm",   "10")),
    ((55,60),  ("vänster arm", "hand",       "12")),
    ((61,66),  ("höger arm",   "skuldra",    "5")),
    ((67,72),  ("höger arm",   "överarm",    "7")),
    ((73,75),  ("höger arm",   "armbage",    "9")),
    ((76,84),  ("höger arm",   "underarm",   "11")),
    ((85,90),  ("höger arm",   "hand",       "13")),
    ((91,100), ("bröstkorg",   "bröstkorg",  "14"))
]

HUGG_KROSS_LOW = [
    ((1, 16),   ("buk",         "mage",       "15")),
    ((17, 20),  ("buk",         "underliv",   "16")),
    ((21, 28),  ("vänster ben", "höft",       "17")),
    ((29, 36),  ("vänster ben", "lår",        "19")),
    ((37, 44),  ("vänster ben", "knä",        "21")),
    ((45, 56),  ("vänster ben", "vad",        "23")),
    ((57, 60),  ("vänster ben", "fot",        "25")),
    ((61, 68),  ("höger ben",   "höft",       "18")),
    ((69, 76),  ("höger ben",   "lår",        "20")),
    ((77, 84),  ("höger ben",   "knä",        "22")),
    ((85, 96),  ("höger ben",   "vad",        "24")),
    ((97, 100), ("höger ben",   "fot",        "26"))
]

STICK_AVSTAND_NORMAL = [
    ((1, 4),   ("huvud",       "ansikte",    "1")),
    ((5, 8),   ("huvud",       "skalle",     "2")),
    ((9, 10),  ("huvud",       "hals",       "3")),
    ((11,12),  ("vänster arm", "skuldra",    "4")),
    ((13,14),  ("vänster arm", "överarm",    "6")),
    ((15,15),  ("vänster arm", "armbage",    "8")),
    ((16,18),  ("vänster arm", "underarm",   "10")),
    ((19,20),  ("vänster arm", "hand",       "12")),
    ((21,22),  ("höger arm",   "skuldra",    "5")),
    ((23,24),  ("höger arm",   "överarm",    "7")),
    ((25,25),  ("höger arm",   "armbage",    "9")),
    ((26,28),  ("höger arm",   "underarm",   "11")),
    ((29,30),  ("höger arm",   "hand",       "13")),
    ((31,36),  ("bröstkorg",   "bröstkorg",  "14")),
    ((51,58),  ("buk",         "mage",       "15")),
    ((59,60),  ("buk",         "underliv",   "16")),
    ((65,68),  ("vänster ben", "höft",       "17")),
    ((69,72),  ("vänster ben", "lår",        "19")),
    ((73,78),  ("vänster ben", "knä",        "21")),
    ((79,80),  ("vänster ben", "vad",        "23")),
    ((81,84),  ("vänster ben", "fot",        "25")),
    ((85,88),  ("höger ben",   "höft",       "18")),
    ((89,92),  ("höger ben",   "lår",        "20")),
    ((93,98),  ("höger ben",   "knä",        "22")),
    ((99,100), ("höger ben",   "fot",        "26"))
]

STICK_AVSTAND_HIGH = [
    ((1, 8),    ("huvud",        "ansikte",    "1")),
    ((9, 16),   ("huvud",        "skalle",     "2")),
    ((17, 20),  ("huvud",        "hals",       "3")),
    ((21, 24),  ("vänster arm",  "skuldra",    "4")),
    ((25, 28),  ("vänster arm",  "överarm",    "6")),
    ((29, 30),  ("vänster arm",  "armbage",    "8")),
    ((31, 36),  ("vänster arm",  "underarm",   "10")),
    ((37, 40),  ("vänster arm",  "hand",       "12")),
    ((41, 44),  ("höger arm",    "skuldra",    "5")),
    ((45, 48),  ("höger arm",    "överarm",    "7")),
    ((49, 50),  ("höger arm",    "armbage",    "9")),
    ((51, 56),  ("höger arm",    "underarm",   "11")),
    ((57, 60),  ("höger arm",    "hand",       "13")),
    ((61, 90),  ("bröstkorg",    "bröstkorg",  "14")),
    ((91, 98),  ("buk",          "mage",       "15")),
    ((99, 100), ("buk",          "underliv",   "16"))
]

STICK_AVSTAND_LOW = [
    ((1, 2),    ("vänster arm", "skuldra",    "4")),
    ((3, 4),    ("vänster arm", "överarm",    "6")),
    ((5, 5),    ("vänster arm", "armbage",    "8")),
    ((6, 8),    ("vänster arm", "underarm",   "10")),
    ((9, 10),   ("vänster arm", "hand",       "12")),
    ((11, 12),  ("höger arm",   "skuldra",    "5")),
    ((13, 14),  ("höger arm",   "överarm",    "7")),
    ((15, 15),  ("höger arm",   "armbage",    "9")),
    ((16, 18),  ("höger arm",   "underarm",   "11")),
    ((19, 20),  ("höger arm",   "hand",       "13")),
    ((21, 30),  ("bröstkorg",   "bröstkorg",  "14")),
    ((31, 50),  ("buk",         "mage",       "15")),
    ((51, 58),  ("vänster ben", "höft",       "17")),
    ((59, 60),  ("vänster ben", "lår",        "19")),
    ((61, 64),  ("vänster ben", "knä",        "21")),
    ((65, 68),  ("vänster ben", "vad",        "23")),
    ((69, 72),  ("vänster ben", "fot",        "25")),
    ((73, 78),  ("höger ben",   "höft",       "18")),
    ((79, 80),  ("höger ben",   "lår",        "20")),
    ((81, 84),  ("höger ben",   "knä",        "22")),
    ((85, 88),  ("höger ben",   "vad",        "24")),
    ((89, 92),  ("höger ben",   "fot",        "26")),
    ((93, 98),  ("höger ben",   "vad",        "24")),
    ((99, 100), ("höger ben",   "fot",        "26"))
]

# Tabeller för ryttare och riddjur
MOUNTED_HIT_TABLE = {
    "hugg_kross": {
        (1,2):   "normal",  # => Ryttaren, normal
        (3,7):   "låg",     # => Ryttaren, låg
        (8,10):  "ridsadel" # => Riddjuret
    },
    "stick_avstand": {
        (1,5):   "normal",
        (6,8):   "låg",
        (9,10):  "ridsadel"
    }
}

MOUNT_HIT_TABLE = {
    "hugg_kross": {
        1:       "normal",
        (2,3):   "låg",
        (4,10):  "ridsadel"
    },
    "stick_avstand": {
        (1,2):   "normal",
        3:       "låg",
        (4,10):  "ridsadel"
    }
}

QUADRUPED_HIT_TABLE = {
    "framifran": {
        (1,2):  "huvud",
        (3,5):  "v_framben",
        (6,7):  "h_framben",
        (8,10): "bringa"
    },
    "hoger": {
        (1,2):  "huvud",
        (3,4):  "framben",
        (5,6):  "bringa",
        (7,8):  "buk",
        (9,10): "bakben"
    },
    "vanster": {
        (1,2):  "huvud",
        (3,4):  "framben",
        (5,6):  "bringa",
        (7,8):  "buk",
        (9,10): "bakben"
    },
    "bakifran": {
        (1,6):  "buk",
        (7,8):  "v_bakben",
        (9,10): "h_bakben"
    }
}

# Huvudtabell som samlar hugg/kross och stick/avstånd tabellerna
BASE_HIT_TABLE = {
    "hugg_kross": {
        "normal": HUGG_KROSS_NORMAL,
        "hög":    HUGG_KROSS_HIGH,
        "låg":    HUGG_KROSS_LOW
    },
    "stick_avstand": {
        "normal": STICK_AVSTAND_NORMAL,
        "hög":    STICK_AVSTAND_HIGH,
        "låg":    STICK_AVSTAND_LOW
    }
}

# Funktioner för att slå på tabellerna
def get_hit_location(weapon_type: WeaponType, attack_level: AttackLevel, roll_1to100: int) -> Tuple[str, str, str]:
    """
    Returnerar (location, sublocation, code) från träfftabellen.
    """
    # Välj vilken tabell som används
    if weapon_type in (WeaponType.HUGG, WeaponType.KROSS):
        table_key = "hugg_kross"
    else:
        table_key = "stick_avstand"

    # Hämta träfftabell för vald attacknivå
    table = BASE_HIT_TABLE[table_key][attack_level.value]

    # Matcha rullning i tabellen
    for (min_val, max_val), (loc, subloc, code) in table:
        if min_val <= roll_1to100 <= max_val:
            return (loc, subloc, code)

    raise ValueError(f"Ogiltigt slag {roll_1to100} för {weapon_type} / {attack_level}")

def get_mounted_hit_modification(weapon_type: WeaponType, roll_1to10: int) -> str:
    """
    Tabell R2-46: Träff mot ryttare => "normal", "låg" eller "ridsadel"
    """
    if weapon_type in (WeaponType.HUGG, WeaponType.KROSS):
        table = MOUNTED_HIT_TABLE["hugg_kross"]
    else:
        table = MOUNTED_HIT_TABLE["stick_avstand"]

    for rng, result in table.items():
        if isinstance(rng, tuple):
            if rng[0] <= roll_1to10 <= rng[1]:
                return result
        else:
            if roll_1to10 == rng:
                return result

    raise ValueError(f"Ogiltigt slag {roll_1to10} för get_mounted_hit_modification.")

def get_mount_hit_location(weapon_type: WeaponType, roll_1to10: int) -> str:
    """
    Tabell R2-47: Träff mot riddjur => "normal", "låg" eller "ridsadel"
    """
    if weapon_type in (WeaponType.HUGG, WeaponType.KROSS):
        table = MOUNT_HIT_TABLE["hugg_kross"]
    else:
        table = MOUNT_HIT_TABLE["stick_avstand"]

    for rng, result in table.items():
        if isinstance(rng, tuple):
            if rng[0] <= roll_1to10 <= rng[1]:
                return result
        else:
            if roll_1to10 == rng:
                return result

    raise ValueError(f"Ogiltigt slag {roll_1to10} för get_mount_hit_location.")


def get_quadruped_hit_location(direction: str, roll_1to10: int) -> str:
    """
    Tabell R2-48: Träffområden för fyrbenta djur.
    direction kan vara 'framifran', 'hoger', 'vanster', 'bakifran'.
    Returnerar en str (t.ex. "huvud", "framben", "bringa", "buk", "bakben" osv.).
    """
    if direction not in QUADRUPED_HIT_TABLE:
        raise ValueError(f"Ogiltig riktning '{direction}' för fyrbent djur.")

    table = QUADRUPED_HIT_TABLE[direction]
    for rng, loc in table.items():
        if isinstance(rng, tuple):
            if rng[0] <= roll_1to10 <= rng[1]:
                return loc
        else:
            if rng == roll_1to10:
                return loc

    raise ValueError(f"Ogiltigt slag {roll_1to10} i get_quadruped_hit_location.")
