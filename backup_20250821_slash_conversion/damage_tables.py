# damage_tables.py

import random
from enum import Enum
from typing import List, Optional, Dict

class DamageType(Enum):
    HUGG = "H"
    KROSS = "K"
    STICK = "S"

class DamageResult:
    """
    Representerar resultatet av en skada, inklusive effektkod, beskrivning och specialeffekter.
    """
    def __init__(self, effect_code: str, effects: Optional[List[str]] = None, description: Optional[str] = None):
        self.effect_code = effect_code
        self.effects = effects or []
        self.description = description  # Lägg till beskrivningen


HUGG_DAMAGE_TABLE = {
    "ansikte": {
        "ytlig": {
            # Exempel: ger lite extra smärta och lite blod
            "effekt": "T+1, S+3, B+1"
        },
        "allvarlig": [
            # Låga slag först = Värst
            (1,  "Hjärna",       "T*2, S*2, B/2",   ["Amp", "Fast", "Men"]), 
            (2,  "Öga",          "T/2, S*2, B*1",   ["Amp", "Men", "Arr"]),
            (3,  "Mun/Käke",     "T/2, S*1, B/10",  ["Amp", "Men", "Arr"]),
            (4,  "Näsa",         "T/10, S/2, B/10", ["Amp", "Arr"]), 
            (5,  "Omtöckning",   "T/10, S*1, B/10", ["Faller", "Tappar"]), 
            (6,  "Blödning",     "T/10, S/10, B*2", ["Arr"]), 
            (7,  "Blödning",     "T/10, S/10, B/2", None),
            (8,  "Öra",          "T/10, S/2,  B/10",["Amp", "Men", "Arr"]), 
            (9,  "Köttsår",      "T/10, S/10, B/10",None),
            (10, "Köttsår",      "T/10, S/10, B/10",None),
        ]
    },

    "skalle": {
        "ytlig": {
            "effekt": "T+2, S+2, B+1"
        },
        "allvarlig": [
            (1,  "Hjärna",       "T*2, S*2, B/2",   ["Amp", "Men"]),
            (2,  "Hjärna",       "T*2, S*1, B/2",   ["Men", "Fast"]),
            (3,  "Skallben",     "T/2, S*2, B*1",   ["Bryt", "Fast"]), 
            (4,  "Skallben",     "T/2, S/2, B/10",  ["Bryt"]),
            (5,  "Omtöckning",   "T/10, S*1, B/10", ["Faller", "Tappar"]), 
            (6,  "Omtöckning",   "T/10, S/2, B/10", ["Tappar"]),
            (7,  "Blödning",     "T/10, S/10, B/2", None),
            (8,  "Blödning",     "T/10, S/2, B/10",["Arr"]),
            (9,  "Köttsår",      "T/10, S/10, B/10",None),
            (10, "Köttsår",      "T/10, S/10, B/10",None),
        ]
    },

    "hals": {
        "ytlig": {
            "effekt": "T+1, S+2, B+1"
        },
        "allvarlig": [
            (1,  "Strupe",    "T*2, S*2, B*1",  ["Amp", "Kväv", "Men"]),
            (2,  "Strupe",    "T*2, S/2, B*1",  ["Amp", "Kväv"]),
            (3,  "Nackkotor", "T/2, S/2, B/10", ["Bryt", "Fast"]),
            (4,  "Pulsåder",  "T/2, S/2, B*2",  ["Men"]),
            (5,  "Artärblödning", "T/10, S/10, B*1", ["Fast"]),
            (6,  "Omtöckning","T/10, S*1, B/10",["Tappar"]),
            (7,  "Blödning",  "T/10, S/10, B/2",["Arr"]),
            (8,  "Blödning",  "T/10, S/10, B/10",None),
            (9,  "Köttsår",   "T/10, S/10, B/10",None),
            (10, "Köttsår",   "T/10, S/10, B/10",None),
        ]
    },

    "bröstkorg": {
        "ytlig": {
            "effekt": "T+1, S+1, B+1"
        },
        "allvarlig": [
            (1,  "Hjärta",     "T*2, S*2, B*3",  ["Amp", "Faller", "Inre skada"]),
            (2,  "Lunga",      "T*1, S*1, B*2",  ["Faller", "Inre skada"]),
            (3,  "Pulsåder",   "T/2, S/2, B*2",  ["Fast"]),
            (4,  "Revben",     "T/2, S/2, B/10", ["Bryt", "Fast"]),
            (5,  "Omtöckning", "T/10, S/2, B/10",["Tappar"]),
            (6,  "Blödning",   "T/10, S/10, B/2",None),
            (7,  "Blödning",   "T/10, S/10, B/10",["Arr"]),
            (8,  "Köttsår",    "T/10, S/10, B/10",None),
            (9,  "Lunga",      "T*1, S*1, B*1",  ["Faller", "Inre skada"]),
            (10, "Köttsår",    "T/10, S/10, B/10",None),
        ]
    },

    "mage": {
        "ytlig": {
            "effekt": "T+1, S+2, B+1"
        },
        "allvarlig": [
            (1,  "Inälvor",    "T*2, S*2, B/2",  ["Amp", "Inre skada"]),
            (2,  "Tarm",       "T/2, S*2, B*1",  ["Amp", "Men"]),
            (3,  "Pulsåder",   "T/2, S/2, B*2",  ["Fast"]),
            (4,  "Omtöckning", "T/10, S/2, B/10",["Tappar"]),
            (5,  "Omtöckning", "T/10, S/2, B/10",["Faller"]),
            (6,  "Blödning",   "T/10, S/10, B/2",["Arr"]),
            (7,  "Blödning",   "T/10, S/10, B/10",None),
            (8,  "Köttsår",    "T/10, S/10, B/10",None),
            (9,  "Ryggrad",    "T/2, S*2, B/10", ["Bryt", "Fast"]),
            (10, "Köttsår",    "T/10, S/10, B/10",None),
        ]
    },

    "underliv": {
        "ytlig": {
            "effekt": "T+1, S+2, B+1"
        },
        "allvarlig": [
            (1,  "Könsorgan",  "T*2, S/2, B/2",  ["Amp", "Men", "Faller"]),
            (2,  "Könsorgan",  "T/2, S/2, B*1",  ["Amp", "Tappar"]),
            (3,  "Omtöckning", "T/10, S*1, B/10",["Faller"]),
            (4,  "Blödning",   "T/10, S/10, B/2",["Arr"]),
            (5,  "Blödning",   "T/10, S/10, B/10",None),
            (6,  "Köttsår",    "T/10, S/10, B/10",None),
            (7,  "Köttsår",    "T/10, S/10, B/10",None),
            (8,  "Köttsår",    "T/10, S/10, B/2",None),
            (9,  "Köttsår",    "T/10, S/10, B/10",None),
            (10, "Köttsår",    "T/10, S/10, B/10",None),
        ]
    },

    "arm": {
        "ytlig": {
            "effekt": "T+1, S+2, B+1"
        },
        "allvarlig": [
            (1,  "Benpipa",     "T/2, S*2, B/10",   ["Amp", "Bryt", "Tappar"]),
            (2,  "Artärblödning","T/2, S/2, B*2",   ["Amp"]),
            (3,  "Muskel/Senor","T/2, S/2, B/10",   ["Men", "Tappar"]),
            (4,  "Omtöckning",  "T/10, S/2, B/10",  ["Faller"]),
            (5,  "Blödning",    "T/10, S/10, B/2",  ["Arr"]),
            (6,  "Blödning",    "T/10, S/10, B/2",  None),
            (7,  "Köttsår",     "T/10, S/10, B/10", None),
            (8,  "Köttsår",     "T/10, S/10, B/10", None),
            (9,  "Benpipa",     "T/2, S*1, B/10",   ["Amp", "Bryt", "Tappar"]),
            (10, "Köttsår",     "T/10, S/10, B/10", None),
        ]
    },

    "ben": {
        "ytlig": {
            "effekt": "T+1, S+1, B+1"
        },
        "allvarlig": [
            (1,  "Lårben",      "T/2, S*2, B/10",   ["Amp", "Bryt", "Faller"]),
            (2,  "Artärblödning","T/2, S/2, B*2",   ["Amp"]),
            (3,  "Muskel/Senor","T/2, S/2, B/10",   ["Faller", "Men"]),
            (4,  "Omtöckning",  "T/10, S*1, B/10",  ["Faller"]),
            (5,  "Blödning",    "T/10, S/10, B/2",  ["Arr"]),
            (6,  "Blödning",    "T/10, S/10, B/10", None),
            (7,  "Köttsår",     "T/10, S/10, B/10", None),
            (8,  "Köttsår",     "T/6, S/5, B/10", None),
            (9,  "Köttsår",     "T/10, S/10, B/10", None),
            (10, "Köttsår",     "T/10, S/10, B/10", None),
        ]
    }
}


KROSS_DAMAGE_TABLE = {
    "ansikte": {
        "ytlig": {
            "effekt": "T+1, S+3, B+1"
        },
        "allvarlig": [
            (1,  "Hjärna",       "T*2, S*2, B/2",   ["Faller", "Men"]),
            (2,  "Käke/Skalle",  "T*1, S*2, B/10",  ["Bryt", "Men"]),
            (3,  "Omtöckning",   "T/2, S*2, B/10",  ["Faller", "Tappar"]),
            (4,  "Näsa",         "T/10, S/2, B/10", ["Bryt"]),
            (5,  "Blödning",     "T/10, S/10, B/2", None),
            (6,  "Blödning",     "T/10, S/10, B/5",["Arr"]),
            (7,  "Öga",          "T/2, S*1, B/10", None),
            (8,  "Öra",          "T/10, S/10, B/10",      None),
            (9,  "Köttkross",    "T/10, S/2",       None),
            (10, "Köttkross",    "T/10, S/10, B/10",None),
        ]
    },

    "skalle": {
        "ytlig": {
            "effekt": "T+2, S+2"
        },
        "allvarlig": [
            (1,  "Hjärna",      "T*2, S*2",        ["Faller", "Men"]),
            (2,  "Hjärna",      "T*2, S*1",        ["Men"]),
            (3,  "Skallben",    "T*1, S*2",        ["Bryt", "Faller"]),
            (4,  "Omtöckning",  "T/2, S/2",        ["Tappar"]),
            (5,  "Omtöckning",  "T/10, S/2",       ["Faller", "Tappar"]),
            (6,  "Blödning",    "T/10, S/10, B/2",      None),
            (7,  "Blödning",    "T/10, S/10, B/5",     None),
            (8,  "Köttkross",   "T/10, S/10",      ["Arr"]),
            (9,  "Skallben",    "T/2,  S/5",      None),
            (10, "Köttkross",   "T/10, S/10",      None),
        ]
    },

    "hals": {
        "ytlig": {
            "effekt": "T+1, S+2"
        },
        "allvarlig": [
            (1,  "Nackkotor",   "T*2, S*2",    ["Bryt", "Faller", "Men"]),
            (2,  "Strupe",      "T*1, S/2",    ["Kväv", "Faller"]),
            (3,  "Strupe",      "T/2, S/2",       ["Inre skada"]),
            (4,  "Omtöckning",  "T/10, S*1",   ["Tappar"]),
            (5,  "Omtöckning",  "T/10, S/2",   ["Tappar"]),
            (6,  "Blödning",    "T/10, S/10",  None),
            (7,  "Nackkotor",   "T*2, S*2",    ["Bryt", "Faller", "Men"]),
            (8,  "Köttkross",   "T/10, S/10",  None),
            (9,  "Nackkotor",   "T*1, S*2",    ["Bryt", "Faller", "Men"]),
            (10, "Köttkross",   "T/10, S/10",  None),
        ]
    },

    "bröstkorg": {
        "ytlig": {
            "effekt": "T+1, S+1"
        },
        "allvarlig": [
            (1,  "Hjärta",      "T*2, S*2",      ["Faller", "Inre skada"]),
            (2,  "Lunga",       "T*1, S*1",      ["Faller", "Inre skada"]),
            (3,  "Ryggrad",     "T/2, S/2",      ["Bryt", "Faller"]),
            (4,  "Revben",      "T/10, S/2",     ["Bryt"]),
            (5,  "Omskakning",  "T/10, S/2",     ["Tappar"]),
            (6,  "Revben",      "T/10, S/5",    None),
            (7,  "Revben",      "T/10, S/10",    None),
            (8,  "Köttkross",   "T/10, S/10",    None),
            (9,  "Ryggrad",     "T/2, S/2",      ["Bryt", "Faller"]),
            (10, "Köttkross",   "T/10, S/10",    None),
        ]
    },

    "mage": {
        "ytlig": {
            "effekt": "T+1, S+2"
        },
        "allvarlig": [
            (1,  "Inälvor",     "T*2, S*2",      ["Inre skada", "Faller"]),
            (2,  "Inälvor",     "T*1, S*2",      ["Inre skada"]),
            (3,  "Ryggrad",     "T/2, S/2",      ["Bryt"]),
            (4,  "Omtöckning",  "T/10, S/2",     ["Tappar"]),
            (5,  "Blödning",    "T/10, S/10",    None),
            (6,  "Blödning",    "T/10, S/10",    None),
            (7,  "Köttkross",   "T/10, S/10",    None),
            (8,  "Köttkross",   "T/10, S/10",    None),
            (9,  "Ryggrad",     "T/2, S/2",      ["Bryt"]),
            (10, "Köttkross",   "T/10, S/10",    None),
        ]
    },

    "underliv": {
        "ytlig": {
            "effekt": "T+1, S+2"
        },
        "allvarlig": [
            (1,  "Könsorgan",   "T*2, S*2",     ["Faller", "Men"]),
            (2,  "Inälvor",     "T*2, S*1",     ["Inre skada"]),
            (3,  "Blödning",    "T/2, S/2",     None),
            (4,  "Omtöckning",  "T/10, S/2",    ["Tappar"]),
            (5,  "Blödning",    "T/10, S/10",   None),
            (6,  "Köttkross",   "T/10, S/10",   None),
            (7,  "Könsorgan",   "T*1, S*2",     ["Faller", "Men"]),
            (8,  "Köttkross",   "T/10, S/10",   None),
            (9,  "Könsorgan",   "T*1, S*2",     ["Faller", "Men"]),
            (10, "Köttkross",   "T/10, S/10",   None),
        ]
    },

    "arm": {
        "ytlig": {
            "effekt": "T+1, S+2"
        },
        "allvarlig": [
            (1,  "Benpipa",    "T*1, S*2",    ["Bryt", "Fast", "Tappar"]),
            (2,  "Benpipa",    "T*1, S*2",    ["Bryt", "Tappar"]),
            (3,  "Muskelkross", "T/2, S/2",    ["Men"]),
            (4,  "Omtöckning",  "T/10, S/2",   ["Tappar"]),
            (5,  "Blödning",    "T/10, S/10",  None),
            (6,  "Köttkross",   "T/10, S/10",  None),
            (7,  "Köttkross",   "T/10, S/10",  None),
            (8,  "Köttkross",   "T/10, S/10",  None),
            (9,  "Benpipa",    "T*1, S*2",    ["Bryt", "Tappar"]),
            (10, "Köttkross",   "T/10, S/10",  None),
        ]
    },

    "ben": {
        "ytlig": {
            "effekt": "T+1, S+2"
        },
        "allvarlig": [
            (1,  "Benbrott",    "T*2, S*2",    ["Bryt", "Faller", "Fast"]),
            (2,  "Benbrott",    "T*1, S*2",    ["Bryt", "Faller"]),
            (3,  "Muskelkross", "T/2, S/2",    ["Faller", "Men"]),
            (4,  "Omtöckning",  "T/10, S/2",   ["Faller"]),
            (5,  "Blödning",    "T/10, S/10",  None),
            (6,  "Köttkross",   "T/10, S/10",  None),
            (7,  "Köttkross",   "T/10, S/10",  None),
            (8,  "Köttkross",   "T/10, S/10",  None),
            (9,  "Benbrott",    "T*1, S*2",    ["Bryt", "Faller"]),
            (10, "Köttkross",   "T/10, S/10",  None),
        ]
    }
}



#
# ========= Skadetabell: STICK =========
#
STICK_DAMAGE_TABLE = {
    "ansikte": {
        "ytlig": {
            "effekt": "T+1, S+3, B+1"
        },
        "allvarlig": [
            (1,  "Hjärna",      "T*2, S*2, B/2",   ["Fast", "Men"]),
            (2,  "Öga",         "T/2, S*2, B/10",  ["Amp", "Arr"]),  
            (3,  "Mun/Käke",    "T/2, S*1, B/10",  ["Men", "Arr"]),
            (4,  "Omtöckning",  "T/10, S*1, B/10", ["Tappar"]),
            (5,  "Blödning",    "T/10, S/10, B*2", ["Fast"]),
            (6,  "Blödning",    "T/10, S/10, B/2", ["Arr"]),
            (7,  "Öra",         "T/2, S*1, B/10",  ["Amp", "Arr"]),
            (8,  "Köttsår",     "T/10, S/10, B/10",None),
            (9,  "Näsa",        "T/10, S/2, B/10", ["Amp", "Arr", "Men"]),
            (10, "Köttsår",     "T/10, S/10, B/10",None),
        ]
    },

    "skalle": {
        "ytlig": {
            "effekt": "T+1, S+2, B+1"
        },
        "allvarlig": [
            (1,  "Hjärna",    "T*2, S*2, B/2", ["Fast", "Men"]),
            (2,  "Hjärna",    "T*2, S*1, B/2", ["Men"]),
            (3,  "Skallben",  "T/2, S/2, B/10",["Bryt", "Fast"]),
            (4,  "Omtöckning","T/2, S/2, B/10",["Tappar"]),
            (5,  "Blödning",  "T/10, S/10, B/2",None),
            (6,  "Blödning",  "T/10, S/10, B/10",["Arr"]),
            (7,  "Köttsår",   "T/10, S/10, B/10",None),
            (8,  "Köttsår",   "T/10, S/10, B/10",None),
            (9,  "Skallben",  "T/2, S/2, B/10",["Bryt", "Fast"]),
            (10, "Köttsår",   "T/10, S/10, B/10",None),
        ]
    },

    "hals": {
        "ytlig": {
            "effekt": "T+1, S+2, B+1"
        },
        "allvarlig": [
            (1,  "Strupe",       "T*2, S*2, B*1", ["Kväv", "Men"]),
            (2,  "Nackkotor",    "T/2, S/2, B/10",["Bryt", "Fast"]),
            (3,  "Pulsåder",     "T/2, S/2, B*2", ["Fast"]),
            (4,  "Artärblödning","T/10, S/10, B*1",["Fast"]),
            (5,  "Omtöckning",   "T/10, S/2, B/10",["Tappar"]),
            (6,  "Blödning",     "T/10, S/10, B/2",["Arr"]),
            (7,  "Blödning",     "T/10, S/10, B/10",None),
            (8,  "Köttsår",      "T/10, S/10, B/10",None),
            (9,  "Köttsår",      "T/10, S/10, B/10",None),
            (10, "Köttsår",      "T/10, S/10, B/10",None),
        ]
    },

    "bröstkorg": {
        "ytlig": {
            "effekt": "T+1, S+1, B+1"
        },
        "allvarlig": [
            (1,  "Hjärta",     "T*2, S*2, B*4", ["Fast", "Fall", "Inre skada"]),
            (2,  "Lunga",      "T*1, S*1, B*1", ["Fast", "Inre skada"]),
            (3,  "Lunga",      "T*1, S*1, B*1", ["Inre skada"]),
            (4,  "Revben",     "T/2, S/2, B/10",["Bryt", "Fast"]),
            (5,  "Omtöckning", "T/10, S/2, B/10",["Tappar"]),
            (6,  "Blödning",   "T/10, S/10, B/2",["Arr"]),
            (7,  "Blödning",   "T/10, S/10, B/10",None),
            (8,  "Hjärta",     "T*2, S/2, B*4", ["Fast", "Fall", "Inre skada"]),
            (9,  "Pulsåder",   "T/5, S/2, B*2", ["Fast"]),
            (10, "Köttsår",    "T/10, S/10, B/10",None),
        ]
    },

    "mage": {
        "ytlig": {
            "effekt": "T+1, S+2, B+1"
        },
        "allvarlig": [
            (1,  "Inälvor",     "T*2, S*2, B*1", ["Inre skada", "Fast", "Fall"]),
            (2,  "Inälvor",     "T/2, S*2, B*1", ["Inre skada"]),
            (3,  "Artärblödning","T/2, S/2, B*2",["Fast"]),
            (4,  "Pulsåder",    "T*1, S/2, B*2",["Fast"]),
            (5,  "Omtöckning",  "T/10, S/2, B/10",["Tappar"]),
            (6,  "Blödning",    "T/10, S/10, B/2",["Arr"]),
            (7,  "Blödning",    "T/10, S/10, B/10",None),
            (8,  "Köttsår",     "T/10, S/10, B/10",None),
            (9,  "Köttsår",     "T/10, S/10, B/10",None),
            (10, "Köttsår",     "T/10, S/10, B/10",None),
        ]
    },

    "underliv": {
        "ytlig": {
            "effekt": "T+1, S+2, B+1"
        },
        "allvarlig": [
            (1,  "Könsorgan",   "T/2, S*2, B/2",   ["Amp", "Men"]),
            (2,  "Könsorgan",   "T/2, S/2, B/2",   ["Men", "Arr"]),
            (3,  "Omtöckning",  "T/10, S*1, B/10", ["Tappar"]),
            (4,  "Blödning",    "T/10, S/10, B/2", ["Fast", "Arr"]),
            (5,  "Blödning",    "T/10, S/10, B/10",None),
            (6,  "Köttsår",     "T/10, S/10, B/10",None),
            (7,  "Köttsår",     "T/10, S/10, B/10",None),
            (8,  "Köttsår",     "T/10, S/10, B/10",None),
            (9,  "Köttsår",     "T/10, S/10, B/10",None),
            (10, "Köttsår",     "T/10, S/10, B/10",None),
        ]
    },

    "arm": {
        "ytlig": {
            "effekt": "T+1, S+2, B+1"
        },
        "allvarlig": [
            (1,  "Benpipa",       "T/10, S*2, B/10", ["Bryt", "Fast", "Tappar"]),
            (2,  "Artärblödning", "T/10, S/10, B*1", ["Fast"]),
            (3,  "Muskel/Senor",  "T/2, S/10, B/10", ["Men", "Tappar"]),
            (4,  "Omtöckning",    "T/10, S*1, B/10", ["Tappar"]),
            (5,  "Blödning",      "T/10, S/10, B/2", ["Arr"]),
            (6,  "Blödning",      "T/10, S/10, B/10",None),
            (7,  "Köttsår",       "T/10, S/10, B/10",None),
            (8,  "Köttsår",       "T/10, S/10, B/10",None),
            (9,  "Köttsår",       "T/10, S/10, B/10",None),
            (10, "Köttsår",       "T/10, S/10, B/10",None),
        ]
    },

    "ben": {
        "ytlig": {
            "effekt": "T+1, S+2, B+1"
        },
        "allvarlig": [
            (1,  "Benpipa",       "T/10, S*2, B/10", ["Bryt", "Fall", "Fast"]),
            (2,  "Artärblödning", "T/10, S/10, B*1", ["Fast"]),
            (3,  "Muskel/Senor",  "T/2, S/10, B/10", ["Fall", "Men"]),
            (4,  "Omtöckning",    "T/10, S*1, B/10", ["Fall"]),
            (5,  "Blödning",      "T/10, S/10, B/2", ["Arr"]),
            (6,  "Blödning",      "T/10, S/10, B/10",None),
            (7,  "Köttsår",       "T/10, S/10, B/10",None),
            (8,  "Muskel/Senor",  "T/2, S/10, B/10", ["Fall", "Men"]),
            (9,  "Köttsår",       "T/10, S/10, B/10",None),
            (10, "Muskel/Senor",  "T/2, S/10, B/10", ["Fall", "Men"]),
        ]
    }
}

 
def parse_effect_code(effect_code: str, base_damage: int) -> dict:
    """
    Tolkar en sträng som 'T/10, S/2, B*2' (kommaseparerad) och beräknar faktiska värden
    baserat på base_damage.
    
    Returnerar en dict, t.ex.:
      {"T": 2, "S": 14, "B": 56}
    beroende på operationssymbolen (/,*,-,+).
    
    Operationer hanterade:
      / => heltalsdivision
      * => multiplikation
      + => addition
      - => subtraktion
    """
    results = {}
    if not effect_code.strip():
        return results  # tom kod

    # Dela upp ex: "T/10, S/2, B*2" => ["T/10", "S/2", "B*2"]
    parts = [p.strip() for p in effect_code.split(",")]

    for part in parts:
        # ex. "T/10", "S/2", "B*2"
        # Splitta på första tecknet som inte är en bokstav 
        # men enklare är att hitta T, S, B i början:
        # T/10 => prefix='T', operation='/10'
        # Men med fler varianter (T+2, S-3) behöver vi en liten parser.
        
        # 1) Få ut prefix: T, S, B ...
        prefix = part[0]  # 'T','S','B' etc.
        rest = part[1:]   # ex. "/10", "*2"
        
        # 2) Kolla vilken operation
        if "/" in rest:
            # ex. '/10'
            op, val = rest.split("/")
            # op blir '' (tom) om rest är "/10", val blir "10"
            # Men om rest var "x/10"? isf behöver vi parse annorlunda.
            # Här förutsätter vi formatet "<prefix><operator><tal>"
            # => prefix='T' operator='/' val='10'
            divisor = int(val)
            results[prefix] = base_damage // divisor

        elif "*" in rest:
            # ex. '*2'
            op, val = rest.split("*")
            multiplier = int(val)
            results[prefix] = base_damage * multiplier

        elif "+" in rest:
            # ex. '+3'
            op, val = rest.split("+")
            addition = int(val)
            results[prefix] = base_damage + addition

        elif "-" in rest:
            # ex. '-2'
            op, val = rest.split("-")
            subtraction = int(val)
            results[prefix] = base_damage - subtraction

        else:
            # Om man har "T" utan / * + - => ex. "T1"? Kan du hantera,
            # men vanligast är T/10, T*2, etc. 
            # Här kan man sätta en fallback, ex. results[prefix] = base_damage
            pass

    return results
#
# ====== DamageCalculator-klass ======
#

class DamageCalculator:
    """
    Tar in:
       - damage_type (HUGG, KROSS, STICK)
       - location (t.ex. 'ansikte', 'skalle', 'arm')
       - damage_value (heltal)

    Returnerar en DamageResult (effect_code, effects).
    """
    def __init__(self):
        self.tables = {
            DamageType.HUGG: HUGG_DAMAGE_TABLE,
            DamageType.KROSS: KROSS_DAMAGE_TABLE,
            DamageType.STICK: STICK_DAMAGE_TABLE
        }

    def get_damage(self, damage_type: DamageType, location: str, damage_value: int, use_malpunkter: bool = False) -> DamageResult:
        """
        Kollar i rätt tabell (HUGG/KROSS/STICK) -> location -> ytlig/allvarlig.
        Om allvarlig (damage_value >= 10) slår 1T10 i tabellen.
        Om Målpunkter används slås 1T6 istället för 1T10 (för bättre placerade träffar).
        Annars returneras "ytlig" damage_result.
        """
        table = self.tables[damage_type]
        if location not in table:
            raise ValueError(f"Ingen skadetabell hittades för '{location}' i {damage_type}")

        # Ytlig skada
        if damage_value < 10:
            effect_code = table[location]["ytlig"]["effekt"]
            return DamageResult(effect_code, description="Ytlig skada")

        # Allvarlig skada
        if use_malpunkter:
            # Använd vanlig T6 istället för T10 vid Målpunkter
            roll_t10 = random.randint(1, 6)
        else:
            roll_t10 = random.randint(1, 10)
            
        for (max_val, sub_desc, effect_code, effects) in table[location]["allvarlig"]:
            if roll_t10 <= max_val:
                return DamageResult(effect_code, effects, description=sub_desc)

        # Om ingen rad matchade (borde ej hända)
        raise ValueError(f"Kunde inte matcha T10-slag={roll_t10} i allvarlig skada för '{location}'.")



#
# KLART!
#
# Du kan nu anropa t.ex.:
#   calc = DamageCalculator()
#   result = calc.get_damage(DamageType.HUGG, "ansikte", 12)
# => Ger en 'DamageResult' med effect_code t.ex. "T*2, S*1, B/2" och effects ["Amp", "Men", "Arr"] (beroende på T10).
#
