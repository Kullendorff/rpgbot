import random
import json
import os
from typing import List, Tuple, Dict, Optional, Any, Union
import discord
from discord.ext import commands

# Definiera vapen och deras skador
WEAPON_DAMAGE = {
    "pistol": "2d6",
    "hagelgevär": "3d6",
    "yxa": "2d6",
    "kniv": "1d6+2",
    "basebollträ": "2d6+1",
    "brandyxa": "2d6+3",
    "kofot": "1d6+3",
    "machete": "2d6",
    "motorsåg": "3d6+1",
    "köttyxa": "2d6+1",
    "golfklubba": "1d6+1",
    "hammare": "1d6+2",
    "knytnäve": "1d3",
    "spark": "1d6",
    "revolver": "2d6+1",
    "gevär": "3d6+2",
    "slangbella": "1d4",
    "baseballbat": "2d6",
    "järnrör": "1d6+1",
    "knogjärn": "1d4+1"
}

# Träffzoner baserat på 1d20 (enligt Skjut dom i huvudet regelboken)
HIT_ZONES = {
    1: "Huvud",
    2: "Huvud",
    3: "Huvud",
    4: "Huvud",
    5: "Vänster arm",
    6: "Vänster arm",
    7: "Vänster arm",
    8: "Vänster arm",
    9: "Höger arm",
    10: "Höger arm",
    11: "Höger arm",
    12: "Torso",
    13: "Torso",
    14: "Höger ben",
    15: "Höger ben",
    16: "Vänster ben",
    17: "Vänster ben",
    18: "Vänster ben",
    19: "Bål/rygg",
    20: "Välj träffzon"
}

# Klasser och funktioner här nedanför

class SplatterPointManager:
    def __init__(self):
        self.points = 0
        self.max_points = 0
        self.descriptions_used = []

    def reset_points(self, num_players: int):
        self.points = num_players
        self.max_points = num_players
        self.descriptions_used = []

    def use_point(self) -> bool:
        if self.points > 0:
            self.points -= 1
            return True
        return False

    def add_description(self, description: str):
        self.descriptions_used.append(description)

    def get_status(self) -> Dict[str, Any]:
        return {
            "points": self.points,
            "max_points": self.max_points,
            "points_used": self.max_points - self.points,
            "descriptions": self.descriptions_used
        }

# (Resten av funktionerna och klasserna som tidigare, oförändrade)

# Infoga här resten av din befintliga kod som fanns i dice_functions.py, oförändrad.


class InfectionDeck:
    """Hantera smittokortslekar för spelare enligt Skjut dom i huvudet-regler."""
    
    def __init__(self, data_path: str = None):
        """
        Initialisera smittokortshanterare.
        
        Args:
            data_path: Sökväg till datamappen. Om None skapas sökvägen baserat på skriptets plats.
        """
        if data_path is None:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            self.data_path = os.path.join(os.path.dirname(os.path.dirname(script_dir)), 'data', 'sdih_decks')
        else:
            self.data_path = data_path
            
        # Skapa mappen om den inte existerar
        os.makedirs(self.data_path, exist_ok=True)
        
        # Standardkortlek: 8 friska, 2 smittade
        self.default_deck = [
            {"type": "Frisk", "message": "Du klarade dig! Den här gången..."}, 
            {"type": "Frisk", "message": "Såret rinner av blod, men du känner ingen feber."}, 
            {"type": "Frisk", "message": "Zombiens huggtänder rev upp din hud, men ingen smitta trängde in."}, 
            {"type": "Frisk", "message": "Bettet var ytligt, du kommer att överleva."}, 
            {"type": "Frisk", "message": "En till ärra till samlingen, men inget värre."}, 
            {"type": "Frisk", "message": "Såret är infekterat, men inte av zombievirus."}, 
            {"type": "Frisk", "message": "Ett otäckt bett, men du är immun... för nu."}, 
            {"type": "Frisk", "message": "Du har tur. Den här gången."}, 
            {"type": "Smittad", "message": "Du känner värmen stiga i kroppen. Inom 24 timmar är du en vandöd."}, 
            {"type": "Smittad", "message": "Ditt blod känns som eld i ådrorna. Snart tillhör du de odödas armé."}
        ]
    
    def _get_deck_path(self, user_id: str) -> str:
        """Hämta sökväg till en spelares kortleksfil."""
        return os.path.join(self.data_path, f"{user_id}.json")
    
    def reset_deck(self, user_id: str) -> None:
        """Återställ en spelares kortlek till standardläget."""
        deck_path = self._get_deck_path(user_id)
        with open(deck_path, 'w', encoding='utf-8') as f:
            json.dump({"deck": self.default_deck.copy(), "drawn": []}, f, ensure_ascii=False)
    
    def add_healthy_cards(self, user_id: str, count: int = 2) -> None:
        """Lägg till friska kort till kortleken (för amputation efter bett)."""
        deck_path = self._get_deck_path(user_id)
        
        if not os.path.exists(deck_path):
            self.reset_deck(user_id)
            return
            
        with open(deck_path, 'r', encoding='utf-8') as f:
            deck_data = json.load(f)
            
        # Lägg till friska kort
        for _ in range(count):
            deck_data["deck"].append({"type": "Frisk", "message": "Amputeringen fungerade! Du klarade dig... för nu."})
            
        with open(deck_path, 'w', encoding='utf-8') as f:
            json.dump(deck_data, f, ensure_ascii=False)
    
    def get_deck_status(self, user_id: str) -> Dict[str, Any]:
        """Hämta aktuell status för en spelares kortlek."""
        deck_path = self._get_deck_path(user_id)
        
        # Om kortleken inte finns, skapa den
        if not os.path.exists(deck_path):
            self.reset_deck(user_id)
        
        with open(deck_path, 'r', encoding='utf-8') as f:
            deck_data = json.load(f)
        
        # Räkna typer av kort
        remaining = deck_data["deck"]
        drawn = deck_data["drawn"]
        
        remaining_healthy = sum(1 for card in remaining if card["type"] == "Frisk")
        remaining_infected = sum(1 for card in remaining if card["type"] == "Smittad")
        drawn_healthy = sum(1 for card in drawn if card["type"] == "Frisk")
        drawn_infected = sum(1 for card in drawn if card["type"] == "Smittad")
        
        return {
            "remaining": len(remaining),
            "remaining_healthy": remaining_healthy,
            "remaining_infected": remaining_infected,
            "drawn": len(drawn),
            "drawn_healthy": drawn_healthy,
            "drawn_infected": drawn_infected,
            "infection_chance": (remaining_infected / len(remaining)) * 100 if remaining else 0
        }
    
    def draw_card(self, user_id: str) -> Dict[str, str]:
        """
        Dra ett kort från en spelares smittokortlek.
        
        Returns:
            Dict[str, str]: Draget kort med typ och meddelande
        """
        deck_path = self._get_deck_path(user_id)
        
        # Om kortleken inte finns, skapa den
        if not os.path.exists(deck_path):
            self.reset_deck(user_id)
        
        with open(deck_path, 'r', encoding='utf-8') as f:
            deck_data = json.load(f)
        
        # Kontrollera om det finns kort kvar
        if not deck_data["deck"]:
            return {"type": "EmptyDeck", "message": "Din kortlek är tom!"}
        
        # Dra ett slumpmässigt kort
        card_index = random.randint(0, len(deck_data["deck"]) - 1)
        card = deck_data["deck"].pop(card_index)
        deck_data["drawn"].append(card)
        
        # Spara den uppdaterade kortleken
        with open(deck_path, 'w', encoding='utf-8') as f:
            json.dump(deck_data, f, ensure_ascii=False)
        
        return card

def roll_d20_advantage() -> Tuple[List[int], int, bool, bool]:
    """
    Slå två d20 och välj det högsta resultatet (Fördel enligt Skjut dom i huvudet).
    
    Returns:
        Tuple[List[int], int, bool, bool]: (tärningsresultat, bästa värde, var Naila (20), var Fucka upp (1))
    """
    rolls = [random.randint(1, 20) for _ in range(2)]
    best_roll = max(rolls)
    
    # Enligt reglerna: Om 20 visas på någon av tärningarna = Naila
    is_naila = 20 in rolls
    
    # Om 1 visas på någon av tärningarna = Fucka upp, men vid både 1 och 20 gäller Naila
    is_fumble = 1 in rolls and 20 not in rolls
    
    return rolls, best_roll, is_naila, is_fumble

def roll_d20_disadvantage() -> Tuple[List[int], int, bool, bool]:
    """
    Slå två d20 och välj det lägsta resultatet (Nackdel enligt Skjut dom i huvudet).
    
    Returns:
        Tuple[List[int], int, bool, bool]: (tärningsresultat, sämsta värde, var Naila (20), var Fucka upp (1))
    """
    rolls = [random.randint(1, 20) for _ in range(2)]
    worst_roll = min(rolls)
    
    # Vid nackdel och både 1 och 20 gäller Fucka upp
    is_naila = 20 in rolls and 1 not in rolls
    is_fumble = 1 in rolls
    
    return rolls, worst_roll, is_naila, is_fumble

def roll_d20(modifier: int = 0) -> Tuple[int, int, bool, bool]:
    """
    Slå en vanlig d20 med modifierare.
    
    Args:
        modifier: Värde att lägga till tärningsresultatet.
        
    Returns:
        Tuple[int, int, bool, bool]: (tärningsresultat, totalt, var Naila (20), var Fucka upp (1))
    """
    roll = random.randint(1, 20)
    total = roll + modifier
    
    is_naila = roll == 20
    is_fumble = roll == 1
    
    return roll, total, is_naila, is_fumble

def roll_damage(weapon_name: str = None, damage_string: str = None) -> Tuple[List[int], int]:
    """
    Slå skada för ett vapen.
    
    Args:
        weapon_name: Namn på vapnet (måste finnas i WEAPON_DAMAGE).
        damage_string: Alternativ skadeformel (t.ex. "2d6+1").
        
    Returns:
        Tuple[List[int], int]: (tärningresultat, total skada)
    """
    if weapon_name and weapon_name.lower() in WEAPON_DAMAGE:
        damage_string = WEAPON_DAMAGE[weapon_name.lower()]
    elif not damage_string:
        raise ValueError("Antingen vapennamn eller skadeformel måste anges")
    
    # Parsea skadeformeln
    if "+" in damage_string:
        dice_part, mod_part = damage_string.split("+")
        modifier = int(mod_part)
    elif "-" in damage_string:
        dice_part, mod_part = damage_string.split("-")
        modifier = -int(mod_part)
    else:
        dice_part = damage_string
        modifier = 0
        
    num_dice, sides = map(int, dice_part.lower().split("d"))
    
    # Vanligt slag
    rolls = [random.randint(1, sides) for _ in range(num_dice)]
    total = sum(rolls) + modifier
    
    return rolls, total

# Vi behöver inte funktionen roll_unlimited_d6 eftersom OB-slag inte finns i Skjut dom i huvudet
# Funktionen är borttagen

def roll_hit_zone() -> Tuple[int, str]:
    """
    Slå för att avgöra träffad kroppsdel.
    
    Returns:
        Tuple[int, str]: (tärningsresultat, träffområde)
    """
    roll = random.randint(1, 20)
    zone = HIT_ZONES[roll]
    
    return roll, zone

def parse_initiative_args(args: List[str]) -> List[Tuple[str, int]]:
    """
    Parsea argument för initiativkommando.
    
    Args:
        args: Lista med argument som växlar mellan namn och modifierare.
        
    Returns:
        List[Tuple[str, int]]: Lista med (namn, initiativmodifierare).
    """
    if len(args) % 2 != 0:
        raise ValueError("Ojämnt antal argument. Varje namn måste följas av ett initiativvärde.")
    
    participants = []
    for i in range(0, len(args), 2):
        name = args[i]
        try:
            initiative_mod = int(args[i+1])
            participants.append((name, initiative_mod))
        except ValueError:
            raise ValueError(f"Ogiltigt initiativvärde för {name}. Måste vara ett heltal.")
    
    return participants

def roll_initiative(participants: List[Tuple[str, int]]) -> List[Dict[str, Union[str, int]]]:
    """
    Slå initiativ för deltagarna och sortera i fallande ordning enligt Skjut dom i huvudets regler.
    
    Args:
        participants: Lista med tupler av (namn, initiativmodifierare).
        
    Returns:
        List[Dict[str, Union[str, int]]]: Sorterad lista med initativresultat.
    """
    initiative_results = []
    
    for name, modifier in participants:
        roll = random.randint(1, 20)
        total = roll + modifier
        
        # Kontrollera för Naila och Fucka upp
        is_naila = roll == 20
        is_fumble = roll == 1
        
        initiative_results.append({
            "name": name,
            "roll": roll,
            "modifier": modifier,
            "total": total,
            "is_naila": is_naila,
            "is_fumble": is_fumble
        })
    
    # Sortera efter totalt initiativ (fallande)
    initiative_results.sort(key=lambda x: x["total"], reverse=True)
    
    return initiative_results

def get_naila_effect() -> str:
    """
    Returnerar en slumpmässig positiv effekt för Naila (20 på tärningen).
    
    Returns:
        str: Beskrivning av Naila-effekten
    """
    effects = [
        "Du får en extra handling under denna runda!",
        "Din attack gör dubbel skada!",
        "Du kan frigöra dig från en zombie som håller fast dig.",
        "Du hittar en användbar pryl i närheten.",
        "Du får Fördel på ditt nästa slag.",
        "Du återfår 1T6 i Uthållighet.",
        "Din motståndare tappar sitt vapen.",
        "Du får +2 på all skada du gör denna runda.",
        "Du kan utföra en gratis Manöver omedelbart.",
        "Om du slår till en zombie, faller den omkull."
    ]
    return random.choice(effects)

def get_fucka_upp_effect() -> str:
    """
    Returnerar en slumpmässig negativ effekt för Fucka upp (1 på tärningen).
    
    Returns:
        str: Beskrivning av Fucka upp-effekten
    """
    effects = [
        "Du snubblar och faller omkull.",
        "Du tappar ditt vapen.",
        "Du skadar dig själv, ta 1T3 i skada.",
        "Ditt vapen går sönder.",
        "Du exponerar dig för onödig fara, en zombie får en gratis attack mot dig.",
        "Du slår din allierade istället, slå skada mot hen istället.",
        "Du låser fast dig i en obekväm ställning och får Nackdel på nästa slag.",
        "Du förlorar 1T3 i Stabilitet av rädsla.",
        "Du skrämmer iväg ett djur eller person som annars hade hjälpt dig.",
        "Du gör så mycket ljud att alla zombier inom hörhåll uppmärksammar dig."
    ]
    return random.choice(effects)
