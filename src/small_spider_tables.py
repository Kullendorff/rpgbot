# small_spider_tables.py
"""
Skadetabeller för Små Spindlar - EON RPG
Förenklade tabeller med 2 zoner och 5 resultat per tabell
"""

from typing import Dict, List, Tuple, Optional

# ============================================================================
# NAMNLISTA FÖR SMÅSPINDLAR (100 blandade namn)
# ============================================================================

SMALL_SPIDER_NAMES = [
    # Svenska
    "Gunnar", "Astrid", "Bertil", "Ingrid", "Sven", "Birgitta", "Erik", "Margareta",
    "Lars", "Karin", "Bengt", "Ulla", "Gösta", "Maj", "Rune",
    # Engelska
    "Barney", "Eloise", "Theodore", "Prudence", "Chester", "Beatrice", "Winston", "Mildred",
    "Archibald", "Gertrude", "Reginald", "Ethel", "Mortimer", "Agatha", "Percival",
    # Tyska
    "Günther", "Brunhilde", "Wolfgang", "Hildegard", "Klaus", "Gretchen", "Hans", "Ursula",
    "Friedrich", "Helga", "Otto", "Ingeborg", "Heinrich", "Waltraud", "Horst",
    # Franska
    "Pierre", "Giselle", "Jacques", "Colette", "Maurice", "Yvette", "Claude", "Odette",
    "René", "Simone", "Marcel", "Antoinette", "François", "Margot", "Gaston",
    # Spanska
    "Fernando", "Dolores", "Paco", "Carmen", "Diego", "Rosa", "Manuel", "Consuelo",
    # Italienska
    "Giuseppe", "Francesca", "Luigi", "Rosetta", "Antonio", "Lucia", "Marco", "Carmela",
    # Ryska
    "Boris", "Natasha", "Igor", "Svetlana", "Dmitri", "Olga", "Viktor", "Tatiana",
    # Holländska
    "Hendrik", "Grietje", "Piet", "Anke", "Willem", "Cornelia",
    # Irländska
    "Seamus", "Siobhan", "Paddy", "Maeve", "Liam", "Aoife",
    # Skotska
    "Angus", "Morag", "Duncan", "Fiona", "Malcolm", "Eileen",
    # Lite udda
    "Quentin", "Ophelia", "Cornelius", "Esmeralda", "Barnabas", "Zenobia",
    "Ebenezer", "Clotilde", "Ignatius", "Petunia", "Thaddeus", "Brunhilda"
]

# ============================================================================
# RUSTNINGSVÄRDEN
# ============================================================================

SMALL_SPIDER_ARMOR = {
    "huvud": {"hugg": 2, "kross": 2, "stick": 2},
    "kropp": {"hugg": 3, "kross": 3, "stick": 3}
}

# ============================================================================
# HUVUD (Rustning: 2)
# ============================================================================

SMALL_SPIDER_HUVUD_HUGG = {
    "ytlig": {
        "effekt": "T+1, S+1",
        "beskrivning": "Ytlig repa i huvudpansar"
    },
    "allvarlig": [
        (1, "HUVUD KLUVET", "T*2, S*2", ["Död direkt"]),
        (2, "Djupt hugg i hjärna", "T*2, S*1", ["Döende", "Kramper"]),
        (3, "Genom pansar", "T*1, S*1", ["Svår hjärnskada", "Förvirrad"]),
        (4, "Djup skåra", "T/2, S*1", ["Skadad"]),
        (5, "Ytlig skada", "T/10, S/2", None),
    ]
}

SMALL_SPIDER_HUVUD_KROSS = {
    "ytlig": {
        "effekt": "T+2, S+2",
        "beskrivning": "Buckligt pansar, kompression"
    },
    "allvarlig": [
        (1, "HUVUD KROSSAT", "T*2, S*2", ["Död direkt"]),
        (2, "Pansar imploderad", "T*2, S*1", ["Döende", "Hjärnskada"]),
        (3, "Svår kompression", "T*1, S*2", ["Hjärnskakning", "Förvirrad"]),
        (4, "Buckligt pansar", "T/2, S*1", ["Yr", "Svag"]),
        (5, "Ytlig kross", "T/10, S/2", None),
    ]
}

SMALL_SPIDER_HUVUD_STICK = {
    "ytlig": {
        "effekt": "T+1, S+2",
        "beskrivning": "Punktering genom pansar"
    },
    "allvarlig": [
        (1, "GENOM HJÄRNAN", "T*2, S*2", ["Död direkt"]),
        (2, "Djupt genom huvud", "T*2, S*1", ["Döende", "Spasmer"]),
        (3, "Genom pansar", "T*1, S*1", ["Hjärnskada", "Förvirrad"]),
        (4, "Djup punktering", "T/2, S*1", ["Hål", "Läcker"]),
        (5, "Ytlig punktering", "T/10, S/2", None),
    ]
}

# ============================================================================
# KROPP (Rustning: 3)
# ============================================================================

SMALL_SPIDER_KROPP_HUGG = {
    "ytlig": {
        "effekt": "T+1, S+2",
        "beskrivning": "Repa i bakkropp"
    },
    "allvarlig": [
        (1, "KROPP KLUVAD", "T*2, S*2", ["Död direkt", "Inälvor hänger ut"]),
        (2, "Djupt genom kropp", "T*2, S*1", ["Döende", "Inre skada"]),
        (3, "Genom abdomen", "T*1, S*1", ["Organ skadade"]),
        (4, "Djup skåra", "T/2, S*1", ["Läcker vätska", "Svag"]),
        (5, "Ytlig skåra", "T/10, S/2", None),
    ]
}

SMALL_SPIDER_KROPP_KROSS = {
    "ytlig": {
        "effekt": "T+2, S+3",
        "beskrivning": "Kompression av kropp"
    },
    "allvarlig": [
        (1, "KROPP KROSSAD", "T*2, S*2", ["Död direkt", "Organ pulveriserade"]),
        (2, "Intern implosion", "T*2, S*1", ["Döende", "Massiv inre skada"]),
        (3, "Organ skadade", "T*1, S*2", ["Inre skada", "Svag"]),
        (4, "Bucklig kropp", "T/2, S*1", ["Vanskapt", "Smärta"]),
        (5, "Ytlig kross", "T/10, S*1", None),
    ]
}

SMALL_SPIDER_KROPP_STICK = {
    "ytlig": {
        "effekt": "T+1, S+2",
        "beskrivning": "Punktering i kropp"
    },
    "allvarlig": [
        (1, "GENOM KROPPEN", "T*2, S*2", ["Död direkt", "Organ genomborrade"]),
        (2, "Djupt genom inälvor", "T*2, S*1", ["Döende", "Inre skada"]),
        (3, "Genom abdomen", "T*1, S*1", ["Hål", "Organ skadade"]),
        (4, "Djup punktering", "T/2, S*1", ["Läcker kraftigt"]),
        (5, "Ytlig punktering", "T/10, S/2", None),
    ]
}

# ============================================================================
# MASTER TABLE
# ============================================================================

SMALL_SPIDER_DAMAGE_TABLES = {
    "huvud": {
        "hugg": SMALL_SPIDER_HUVUD_HUGG,
        "kross": SMALL_SPIDER_HUVUD_KROSS,
        "stick": SMALL_SPIDER_HUVUD_STICK,
    },
    "kropp": {
        "hugg": SMALL_SPIDER_KROPP_HUGG,
        "kross": SMALL_SPIDER_KROPP_KROSS,
        "stick": SMALL_SPIDER_KROPP_STICK,
    }
}

# ============================================================================
# TRÄFFZON-SLUMPNING (om spelaren väljer "slumpa")
# ============================================================================

SMALL_SPIDER_LOCATION_TABLE = [
    (1, 3, "huvud"),
    (4, 10, "kropp"),
]

# ============================================================================
# PARSE EFFECT CODE - Beräknar T/S/B från effektkoder
# ============================================================================

def parse_effect_code(effect_code: str, base_damage: int) -> Dict[str, int]:
    """
    Tolkar effektkod som 'T/10, S*2' och beräknar faktiska värden.

    Args:
        effect_code: Effektkod från skadetabell (t.ex. "T*2, S/10")
        base_damage: Grundskada från attacken

    Returns:
        Dict med T, S värden (t.ex. {"T": 20, "S": 1})
    """
    results = {}

    if not effect_code or not effect_code.strip():
        return results

    parts = [p.strip() for p in effect_code.split(",")]

    for part in parts:
        if not part:
            continue

        prefix = part[0]
        operation_str = part[1:]

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
            results[prefix] = base_damage

    return results
