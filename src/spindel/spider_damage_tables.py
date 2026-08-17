# src/spindel/spider_damage_tables.py
"""
Skadetabeller för Gigantspindel - EON RPG
Dramaturgiskt och actionbetonat fokus

Del av src/spindel/ — se __init__.py. Modulen är avstängd tills vidare
(config/feature_flags.py: slash_spindel_enabled).
"""

from enum import Enum
from typing import List, Optional, Tuple, Dict

class SpiderDamageType(Enum):
    HUGG = "hugg"
    KROSS = "kross"
    STICK = "stick"

# ============================================================================
# ÖGON (Rustning: 0)
# Balanserad: Låg T, hög S - inte lätt instakill
# ============================================================================

SPIDER_OGON_DAMAGE = {
    "ytlig": {
        "effekt": "T+1, S+3, B+1",
        "beskrivning": "Ytlig skada på ögonyta, vätska sipprar"
    },
    "allvarlig": [
        (1, "ÖGONKLOT KROSSAT", "T/2, S*2, B*2", ["Öga förstört", "Panik", "Skriker"]),
        (2, "Genomborrat öga", "T/2, S*2, B*1", ["Öga förstört", "Chock av smärta"]),
        (3, "Lins sprängd", "T/10, S*2, B*2", ["Öga bländat", "Förvirrad"]),
        (4, "Djup skada i ögonklot", "T/10, S*1, B*2", ["Öga skadat", "Blöder"]),
        (5, "Ögonvätska läcker", "T/10, S*1, B*2", ["Irriterat", "Blinkar"]),
        (6, "Repad lins", "T/10, S/2, B*1", ["Suddig syn"]),
        (7, "Ytlig punktering", "T/10, S/2, B/10", ["Tårande"]),
        (8, "Stöt mot öga", "T/10, S/10, B*1", None),
        (9, "Nära miss", "T/10, S/10, B/10", None),
        (10, "Glansande träff", "T/10, S/10, B/10", None),
    ]
}

# ============================================================================
# BEN (Rustning: 8)
# Högt T möjligt - kan huggas av för dramatik
# ============================================================================

SPIDER_BEN_HUGG = {
    "ytlig": {
        "effekt": "T+1, S+2, B+1",
        "beskrivning": "Chitinpansar repad, lätt hemolypmfläckage"
    },
    "allvarlig": [
        (1, "BEN AVHUGGET!", "T*2, S*1, B*3", ["Ben avskuret", "Tappar balansen", "Krasande ljud"]),
        (2, "LED KROSSAD", "T*1, S*2, B*2", ["Led sönderkrossad", "Kan ej röra ben", "Hänger"]),
        (3, "Djupt hugg i femur", "T/2, S*1, B*2", ["Sprucken", "Blöder kraftigt"]),
        (4, "Klor avhuggna", "T/2, S/2, B*1", ["Tappar grepp", "Halkar"]),
        (5, "Muskelsträngar av", "T/2, S*2, B/2", ["Ben hänger", "Oskadligt"]),
        (6, "Tibia splittrad", "T/10, S*1, B*2", ["Instabilt", "Vinglar"]),
        (7, "Ytlig hemolypmf", "T/10, S/2, B*2", ["Blöder", "Drypper"]),
        (8, "Coxa skadad", "T/2, S*1, B/10", ["Svagt fäste", "Lossnar"]),
        (9, "Djup skåra", "T/10, S/10, B*1", None),
        (10, "Chitinspricka", "T/10, S/10, B/10", None),
    ]
}

SPIDER_BEN_KROSS = {
    "ytlig": {
        "effekt": "T+2, S+3, B+1",
        "beskrivning": "Bucklig chitin, intern kompression"
    },
    "allvarlig": [
        (1, "LED PULVERISERAD", "T*2, S*2, B/2", ["Led sönderkrossad", "Ben hänger", "Knakar högt"]),
        (2, "BEN KROSSAT", "T*2, S*1, B*1", ["Brutit", "Faller åt sidan", "Kollaps"]),
        (3, "Femur krossad", "T*1, S*2, B/10", ["Brutit", "Kan ej röra", "Stelnar"]),
        (4, "Multipla sprickor", "T/2, S*2, B/10", ["Instabilt", "Spricker"]),
        (5, "Led dislocerad", "T/2, S*1, B/10", ["Ben vrids", "Vanskapt"]),
        (6, "Chitin bucklig", "T/10, S*1, B/10", ["Stukad", "Haltande"]),
        (7, "Intern skada", "T/10, S/2, B/10", ["Muskelvävnad skadad"]),
        (8, "Coxa kompression", "T/10, S/10, B/10", ["Svag"]),
        (9, "Ytlig kross", "T/10, S/10, B/10", None),
        (10, "Blåmärke", "T/10, S/10, B/10", None),
    ]
}

SPIDER_BEN_STICK = {
    "ytlig": {
        "effekt": "T+1, S+2, B+2",
        "beskrivning": "Punktering genom chitin, läckande hemolypmf"
    },
    "allvarlig": [
        (1, "GENOM LEDEN!", "T*1, S*2, B*2", ["Led sönderkrossad", "Fastnar", "Läcker vätska"]),
        (2, "Genomborrad femur", "T/2, S*2, B*2", ["Hål", "Stelnar", "Instabil"]),
        (3, "Led perforerad", "T/2, S*1, B*2", ["Läcker", "Svag", "Hänger"]),
        (4, "Muskulatur trasig", "T/2, S/2, B*1", ["Kan ej röra", "Slakt ben"]),
        (5, "Hemolypmfläckage", "T/10, S/10, B*3", ["Blöder kraftigt", "Drypper"]),
        (6, "Djup punktering", "T/10, S/2, B*2", ["Läcker", "Rinner"]),
        (7, "Genom chitin", "T/10, S/10, B*2", ["Hål"]),
        (8, "Ytlig punktering", "T/10, S/10, B*1", None),
        (9, "Repad yta", "T/10, S/10, B/10", None),
        (10, "Knappt igenom", "T/10, S/10, B/10", None),
    ]
}

# ============================================================================
# CHELICERER / BETTÄNGER (Rustning: 6)
# Kan slås av - förhindrar attack
# ============================================================================

SPIDER_CHELICERER_HUGG = {
    "ytlig": {
        "effekt": "T+1, S+2, B+1",
        "beskrivning": "Repa i chitinpansar på chelicerae"
    },
    "allvarlig": [
        (1, "CHELICERAE AVHUGGEN!", "T*2, S*2, B*2", ["Bettång avskuren", "Gift rinner ut", "Kan ej bita"]),
        (2, "GIFTKÖRTLAR SPRÄNGDA", "T*1, S*2, B*2", ["Gift läcker", "Förgiftar sig själv", "Kräks"]),
        (3, "Djupt hugg i bas", "T*1, S*1, B*2", ["Sprucken", "Svag bettförmåga"]),
        (4, "Led sönderhuggen", "T/2, S*2, B*1", ["Hänger", "Kan ej stänga käken", "Trasig"]),
        (5, "Muskulatur skadad", "T/2, S*1, B*2", ["Svagt bett", "Kraftlös käke"]),
        (6, "Chitin sprucken", "T/10, S*1, B*2", ["Instabil", "Läcker"]),
        (7, "Ytlig skåra", "T/10, S/2, B*1", ["Bucklig"]),
        (8, "Gift sipprar", "T/10, S/10, B*2", ["Läcker lite"]),
        (9, "Repad", "T/10, S/10, B/10", None),
        (10, "Glansande", "T/10, S/10, B/10", None),
    ]
}

SPIDER_CHELICERER_KROSS = {
    "ytlig": {
        "effekt": "T+2, S+3, B+1",
        "beskrivning": "Bucklig chelicerae, kompression"
    },
    "allvarlig": [
        (1, "CHELICERAE KROSSAD!", "T*2, S*2, B/2", ["Bettång sönderkrossad", "Kan ej bita", "Krasande ljud"]),
        (2, "GIFTKÖRTLAR IMPLODERADE", "T*1, S*2, B*1", ["Förgiftar sig själv", "Chock", "Gift inuti kroppen"]),
        (3, "Bas pulveriserad", "T*1, S*2, B/10", ["Hänger ner", "Oanvändbar käke"]),
        (4, "Multipla sprickor", "T/2, S*2, B/10", ["Instabil", "Spricker mer"]),
        (5, "Led sönderslagen", "T/2, S*1, B/10", ["Låst käke", "Kan ej röra"]),
        (6, "Bucklig chitin", "T/10, S*1, B/10", ["Svag käke", "Vanskapt"]),
        (7, "Intern kompression", "T/10, S/2, B/10", ["Smärtsam"]),
        (8, "Ytlig kross", "T/10, S/10, B/10", None),
        (9, "Stöt", "T/10, S/10, B/10", None),
        (10, "Blånad", "T/10, S/10, B/10", None),
    ]
}

SPIDER_CHELICERER_STICK = {
    "ytlig": {
        "effekt": "T+1, S+2, B+2",
        "beskrivning": "Punktering, gift läcker ut"
    },
    "allvarlig": [
        (1, "GENOM GIFTKÖRTELN!", "T*1, S*2, B*2", ["Gift sprutar ut", "Förgiftar sig själv", "Chock"]),
        (2, "Giftkanal genomborrad", "T/2, S*2, B*2", ["Gift läcker", "Kan ej injicera gift"]),
        (3, "Genom bas", "T/2, S*1, B*2", ["Hål", "Läcker hemolypmf"]),
        (4, "Led perforerad", "T/2, S/2, B*1", ["Svag", "Instabil"]),
        (5, "Giftläckage", "T/10, S/10, B*2", ["Drypper gift"]),
        (6, "Djup punktering", "T/10, S/2, B*2", ["Hål"]),
        (7, "Genom chitin", "T/10, S/10, B*2", None),
        (8, "Ytlig punktering", "T/10, S/10, B*1", None),
        (9, "Repad", "T/10, S/10, B/10", None),
        (10, "Knappt igenom", "T/10, S/10, B/10", None),
    ]
}

# ============================================================================
# CARAPACE / HUVUDPANSAR (Rustning: 10)
# Mycket skyddad - högt rustningsvärde
# ============================================================================

SPIDER_CARAPACE_HUGG = {
    "ytlig": {
        "effekt": "T+1, S+1, B+1",
        "beskrivning": "Repa i pansaret, gnistor"
    },
    "allvarlig": [
        (1, "GENOM PANSARET - HJÄRNA!", "T*2, S*2, B/2", ["Hjärnskada", "Kräks", "Krampar"]),
        (2, "Djupt hugg i carapace", "T*1, S*2, B*1", ["Pansar sprucken", "Exponerad hjärna"]),
        (3, "Nervcentrum skadat", "T*1, S*1, B/10", ["Dålig koordination", "Ryckiga rörelser"]),
        (4, "Stor spricka", "T/2, S*1, B/10", ["Pansar svag", "Läcker"]),
        (5, "Pansar skårad", "T/2, S/2, B/10", ["Sårbar"]),
        (6, "Ytlig spricka", "T/10, S*1, B/10", ["Bucklig"]),
        (7, "Gnista och repa", "T/10, S/2, B/10", None),
        (8, "Ytlig skada", "T/10, S/10, B/10", None),
        (9, "Studsade", "T/10, S/10, B/10", None),
        (10, "Inget", "T/10, S/10, B/10", None),
    ]
}

SPIDER_CARAPACE_KROSS = {
    "ytlig": {
        "effekt": "T+2, S+2, B+1",
        "beskrivning": "Kompression av pansar, dov smäll"
    },
    "allvarlig": [
        (1, "PANSAR KROSSAD - HJÄRNA!", "T*2, S*2, B/2", ["Hjärnskada", "Kräks", "Döende"]),
        (2, "Carapace imploderad", "T*2, S*1, B/10", ["Pansar sönderkrossad", "Exponerad hjärna", "Krasande ljud"]),
        (3, "Nervcentrum kompression", "T*1, S*2, B/10", ["Förlamad", "Krampar"]),
        (4, "Multipla sprickor", "T/2, S*2, B/10", ["Instabil pansar", "Läcker vätska"]),
        (5, "Bucklig carapace", "T/2, S*1, B/10", ["Vanskapt pansar", "Sårbar"]),
        (6, "Intern skada", "T/10, S*1, B/10", ["Hjärnskakning"]),
        (7, "Pansar böjd", "T/10, S/2, B/10", None),
        (8, "Stöt", "T/10, S/10, B/10", None),
        (9, "Dov smäll", "T/10, S/10, B/10", None),
        (10, "Studsade", "T/10, S/10, B/10", None),
    ]
}

SPIDER_CARAPACE_STICK = {
    "ytlig": {
        "effekt": "T+1, S+2, B+1",
        "beskrivning": "Punktering av pansar, vass spets"
    },
    "allvarlig": [
        (1, "GENOM PANSAR - HJÄRNA!", "T*2, S*2, B*1", ["Hjärnskada", "Spasmer", "Döende"]),
        (2, "Djupt genom carapace", "T*1, S*2, B*2", ["Nervskada", "Förlamad", "Läcker vätska"]),
        (3, "Genom pansar", "T*1, S*1, B*2", ["Exponerad hjärna", "Hål", "Blöder"]),
        (4, "Nervcentrum punkterat", "T/2, S*2, B*1", ["Dålig koordination", "Krampar"]),
        (5, "Hål i pansar", "T/2, S*1, B*2", ["Sårbar punkt", "Läcker"]),
        (6, "Djup punktering", "T/10, S*1, B*2", ["Hål"]),
        (7, "Genom yttre lager", "T/10, S/2, B*1", None),
        (8, "Ytlig punktering", "T/10, S/10, B*1", None),
        (9, "Repad", "T/10, S/10, B/10", None),
        (10, "Studsade", "T/10, S/10, B/10", None),
    ]
}

# ============================================================================
# BAKKROPP (Rustning: 5)
# Stor, sårbar - mycket inre organ
# ============================================================================

SPIDER_BAKKROPP_HUGG = {
    "ytlig": {
        "effekt": "T+1, S+2, B+2",
        "beskrivning": "Repa i bakkropp, lite hemolypmf"
    },
    "allvarlig": [
        (1, "BAKKROPP KLUVAD!", "T*2, S*2, B*3", ["Inälvor hänger ut", "Döende", "Hemolypmf överallt"]),
        (2, "Djupt hugg - inre organ", "T*2, S*1, B*3", ["Inre blödning", "Chock", "Kollapsar"]),
        (3, "Genom bakkropp", "T*1, S*2, B*2", ["Stort hål", "Organ skadade", "Läcker vätska"]),
        (4, "Djup skåra", "T*1, S*1, B*2", ["Kraftig blödning", "Svag"]),
        (5, "Hemolypmfläckage", "T/2, S*1, B*3", ["Blöder kraftigt", "Rinner nerför"]),
        (6, "Muskulatur skuren", "T/2, S/2, B*2", ["Svag bakkropp", "Hänger"]),
        (7, "Ytlig skåra", "T/10, S*1, B*2", ["Läcker vätska", "Drypper"]),
        (8, "Repad chitin", "T/10, S/2, B*1", None),
        (9, "Ytlig", "T/10, S/10, B*1", None),
        (10, "Nära miss", "T/10, S/10, B/10", None),
    ]
}

SPIDER_BAKKROPP_KROSS = {
    "ytlig": {
        "effekt": "T+2, S+3, B+2",
        "beskrivning": "Kompression av bakkropp, intern skada"
    },
    "allvarlig": [
        (1, "BAKKROPP KROSSAD!", "T*2, S*2, B*2", ["Inre organ pulveriserade", "Döende", "Kräks"]),
        (2, "Intern implosion", "T*2, S*1, B*3", ["Massiv inre blödning", "Chock"]),
        (3, "Organ skadade", "T*1, S*2, B*2", ["Inre skada", "Svag", "Läcker inuti"]),
        (4, "Multipel kompression", "T*1, S*1, B*2", ["Organ trasiga", "Blöder inuti"]),
        (5, "Bucklig bakkropp", "T/2, S*2, B*2", ["Vanskapt", "Smärta", "Läcker vätska"]),
        (6, "Muskelkross", "T/2, S*1, B*2", ["Svag", "Kan ej röra bakkropp"]),
        (7, "Kompression", "T/10, S*1, B*2", ["Blåmärke", "Läcker lite"]),
        (8, "Stöt", "T/10, S/2, B*1", None),
        (9, "Dov smäll", "T/10, S/10, B*1", None),
        (10, "Ytlig", "T/10, S/10, B/10", None),
    ]
}

SPIDER_BAKKROPP_STICK = {
    "ytlig": {
        "effekt": "T+1, S+2, B+2",
        "beskrivning": "Punktering, hemolypmf läcker"
    },
    "allvarlig": [
        (1, "GENOM BAKKROPP!", "T*2, S*2, B*3", ["Organ genomborrade", "Döende", "Läcker massivt"]),
        (2, "Djupt genom inälvor", "T*1, S*2, B*3", ["Inre organ skadade", "Kraftig blödning", "Chock"]),
        (3, "Genom bakkropp", "T*1, S*1, B*3", ["Stort hål", "Organ punkterade", "Läcker vätska"]),
        (4, "Inre perforering", "T/2, S*2, B*2", ["Inre blödning", "Smärta"]),
        (5, "Hemolypmfläckage", "T/2, S*1, B*3", ["Kraftig blödning", "Rinner nerför"]),
        (6, "Djup punktering", "T/10, S*1, B*3", ["Läcker kraftigt"]),
        (7, "Genom chitin", "T/10, S/2, B*2", ["Hål", "Drypper vätska"]),
        (8, "Ytlig punktering", "T/10, S/10, B*2", None),
        (9, "Repad", "T/10, S/10, B*1", None),
        (10, "Knappt igenom", "T/10, S/10, B/10", None),
    ]
}

# ============================================================================
# SPINNVÅRTOR (Rustning: 2)
# Sårbar, förhindrar nätspinning
# ============================================================================

SPIDER_SPINNVARTOR_HUGG = {
    "ytlig": {
        "effekt": "T+1, S+3, B+2",
        "beskrivning": "Repa i spinnvårtor, silk läcker"
    },
    "allvarlig": [
        (1, "SPINNVÅRTOR AVHUGGNA!", "T*1, S*2, B*2", ["Kan ej spinna", "Silk överallt", "Chock"]),
        (2, "Spinnkörtlar skadade", "T/2, S*2, B*2", ["Kan ej spinna nät", "Läcker silke"]),
        (3, "Djupt hugg i vårtor", "T/2, S*1, B*2", ["Svårt att spinna", "Blöder", "Silke läcker"]),
        (4, "Körtel skuren", "T/2, S/2, B*2", ["Läcker silke", "Hemolypmf"]),
        (5, "Vårtorna skadade", "T/10, S*1, B*2", ["Svagt silke", "Trasiga vårtor"]),
        (6, "Silk läcker", "T/10, S/2, B*2", ["Klibbigt"]),
        (7, "Ytlig skåra", "T/10, S/2, B*1", None),
        (8, "Repad", "T/10, S/10, B*1", None),
        (9, "Nära vårtorna", "T/10, S/10, B/10", None),
        (10, "Miss", "T/10, S/10, B/10", None),
    ]
}

SPIDER_SPINNVARTOR_KROSS = {
    "ytlig": {
        "effekt": "T+2, S+3, B+1",
        "beskrivning": "Vårtorna krossade, silk läcker"
    },
    "allvarlig": [
        (1, "SPINNVÅRTOR KROSSADE!", "T*1, S*2, B*1", ["Kan ej spinna", "Pulveriserade vårtor", "Chock"]),
        (2, "Körtel imploderad", "T/2, S*2, B*2", ["Kan ej spinna", "Silke inuti kroppen", "Smärta"]),
        (3, "Multipla krossningar", "T/2, S*2, B*1", ["Trasiga vårtor", "Silke läcker"]),
        (4, "Vårtorna skadade", "T/2, S*1, B*1", ["Svårt att spinna", "Vanskapade vårtor"]),
        (5, "Kompression", "T/10, S*1, B*2", ["Buckliga vårtor", "Läcker silke"]),
        (6, "Buckliga vårtor", "T/10, S/2, B*1", ["Silke flödar dåligt"]),
        (7, "Stöt", "T/10, S/2, B/10", None),
        (8, "Ytlig kross", "T/10, S/10, B/10", None),
        (9, "Dov smäll", "T/10, S/10, B/10", None),
        (10, "Studsade", "T/10, S/10, B/10", None),
    ]
}

SPIDER_SPINNVARTOR_STICK = {
    "ytlig": {
        "effekt": "T+1, S+3, B+2",
        "beskrivning": "Punktering, silk och hemolypmf läcker"
    },
    "allvarlig": [
        (1, "GENOM SPINNKÖRTELN!", "T*1, S*2, B*2", ["Kan ej spinna", "Silke sprutar", "Chock"]),
        (2, "Körtel genomborrad", "T/2, S*2, B*2", ["Kan ej spinna nät", "Silke läcker ut"]),
        (3, "Genom vårtor", "T/2, S*1, B*2", ["Hål i vårtor", "Silke rinner", "Blöder"]),
        (4, "Vårtorna perforerade", "T/2, S/2, B*2", ["Läcker vätska", "Trasiga vårtor"]),
        (5, "Djup punktering", "T/10, S*1, B*2", ["Hål", "Silke läcker"]),
        (6, "Genom en vårta", "T/10, S/2, B*2", ["Läcker silke"]),
        (7, "Ytlig punktering", "T/10, S/2, B*1", None),
        (8, "Repad", "T/10, S/10, B*1", None),
        (9, "Nära", "T/10, S/10, B/10", None),
        (10, "Knappt", "T/10, S/10, B/10", None),
    ]
}

# ============================================================================
# RUSTNINGSVÄRDEN
# ============================================================================

SPIDER_ARMOR_VALUES = {
    "ögon": {"hugg": 3, "kross": 3, "stick": 3},
    "ogon": {"hugg": 3, "kross": 3, "stick": 3},
    "ben": {"hugg": 16, "kross": 15, "stick": 15},
    "led": {"hugg": 11, "kross": 10, "stick": 11},
    "chelicerer": {"hugg": 14, "kross": 13, "stick": 13},
    "chelicerae": {"hugg": 14, "kross": 13, "stick": 13},
    "bettänger": {"hugg": 14, "kross": 13, "stick": 13},
    "bettanger": {"hugg": 14, "kross": 13, "stick": 13},
    "carapace": {"hugg": 18, "kross": 17, "stick": 17},
    "huvudpansar": {"hugg": 18, "kross": 17, "stick": 17},
    "huvud": {"hugg": 18, "kross": 17, "stick": 17},
    "bakkropp": {"hugg": 12, "kross": 13, "stick": 12},
    "abdomen": {"hugg": 12, "kross": 13, "stick": 12},
    "övre bakkropp": {"hugg": 13, "kross": 14, "stick": 13},
    "ovre bakkropp": {"hugg": 13, "kross": 14, "stick": 13},
    "undre bakkropp": {"hugg": 11, "kross": 12, "stick": 11},
    "spinnvårtor": {"hugg": 5, "kross": 6, "stick": 5},
    "spinnvartor": {"hugg": 5, "kross": 6, "stick": 5},
}

# ============================================================================
# MASTER TABLE
# ============================================================================

SPIDER_DAMAGE_TABLES = {
    "ögon": {
        "hugg": SPIDER_OGON_DAMAGE,
        "kross": SPIDER_OGON_DAMAGE,
        "stick": SPIDER_OGON_DAMAGE,
    },
    "ben": {
        "hugg": SPIDER_BEN_HUGG,
        "kross": SPIDER_BEN_KROSS,
        "stick": SPIDER_BEN_STICK,
    },
    "chelicerer": {
        "hugg": SPIDER_CHELICERER_HUGG,
        "kross": SPIDER_CHELICERER_KROSS,
        "stick": SPIDER_CHELICERER_STICK,
    },
    "carapace": {
        "hugg": SPIDER_CARAPACE_HUGG,
        "kross": SPIDER_CARAPACE_KROSS,
        "stick": SPIDER_CARAPACE_STICK,
    },
    "bakkropp": {
        "hugg": SPIDER_BAKKROPP_HUGG,
        "kross": SPIDER_BAKKROPP_KROSS,
        "stick": SPIDER_BAKKROPP_STICK,
    },
    "spinnvårtor": {
        "hugg": SPIDER_SPINNVARTOR_HUGG,
        "kross": SPIDER_SPINNVARTOR_KROSS,
        "stick": SPIDER_SPINNVARTOR_STICK,
    },
}

# ============================================================================
# SLUMPNINGSTABELLER
# ============================================================================

SPIDER_SUBLOCATION_TABLES = {
    "huvud": [
        (1, 3, "ögon"),
        (4, 5, "chelicerer"),
        (6, 10, "carapace"),
    ],
    "ben": [
        (1, 3, "led"),
        (4, 10, "ben"),
    ],
    "bakkropp": [
        (1, 6, "bakkropp"),
        (7, 10, "spinnvårtor"),
    ],
}

# ============================================================================
# PARSE EFFECT CODE - Beräknar T/S/B från effektkoder
# ============================================================================

def parse_effect_code(effect_code: str, base_damage: int) -> Dict[str, int]:
    """
    Tolkar effektkod som 'T/10, S*2, B+3' och beräknar faktiska värden.
    
    Args:
        effect_code: Effektkod från skadetabell (t.ex. "T*2, S/10, B+3")
        base_damage: Grundskada från attacken
    
    Returns:
        Dict med T, S, B värden (t.ex. {"T": 20, "S": 1, "B": 13})
    """
    results = {}
    
    if not effect_code or not effect_code.strip():
        return results
    
    # Dela upp "T/10, S/2, B*2" => ["T/10", "S/2", "B*2"]
    parts = [p.strip() for p in effect_code.split(",")]
    
    for part in parts:
        if not part:
            continue
            
        # Hämta prefix (T, S, B)
        prefix = part[0]
        operation_str = part[1:]
        
        # Parse operation
        if "/" in operation_str:
            divisor = int(operation_str.split("/")[1])
            results[prefix] = base_damage // divisor
        elif "*" in operation_str:
            multiplier = int(operation_str.split("*")[1])
            results[prefix] = base_damage * multiplier
        elif "+" in operation_str:
            addition = int(operation_str.split("+")[1])
            results[prefix] = base_damage + addition
        elif "-" in operation_str:
            subtraction = int(operation_str.split("-")[1])
            results[prefix] = base_damage - subtraction
        else:
            # Fallback: använd base_damage
            results[prefix] = base_damage
    
    return results
