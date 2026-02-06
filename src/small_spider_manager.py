# small_spider_manager.py
"""
Stridshanterare för Små Spindlar
Hanterar spawning, träffar, skador och automatiska chock/dödsslag
"""

import random
import os
import sys
from dataclasses import dataclass
from typing import Optional, Dict, List, Tuple
import anthropic
from core.constants import CLAUDE_MODEL

# TODO: Ta bort sys.path manipulation - använd proper package structure
# sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from small_spider_tables import (
    SMALL_SPIDER_DAMAGE_TABLES,
    SMALL_SPIDER_ARMOR,
    SMALL_SPIDER_LOCATION_TABLE,
    SMALL_SPIDER_NAMES,
    parse_effect_code
)

@dataclass
class SmallSpiderDamageResult:
    """Resultat från en attack mot liten spindel"""
    spider_id: int
    weapon_type: str
    raw_damage: int
    hit_location: str
    armor: int
    effective_damage: int
    trauma: int
    pain: int
    description: str
    effects: List[str]
    location_roll: Optional[int] = None

    # Slag
    chock_roll: Optional[Tuple[List[int], int, bool]] = None  # (tärningar, summa, klarar)
    death_roll: Optional[Tuple[List[int], int, bool]] = None  # (tärningar, summa, klarar)

    # Status
    is_dead: bool = False
    is_unconscious: bool = False

class SmallSpider:
    """En liten spindel med EON skadesystem"""

    def __init__(self, spider_id: int, name: str):
        self.spider_id = spider_id
        self.name = name  # Spindelns namn (t.ex. "Barney", "Eloise")
        self.chock_value = 12
        self.damage_tolerance = 5  # 5 rutor per rad

        self.total_trauma = 0
        self.total_pain = 0

        self.alive = True
        self.conscious = True

        self.active_effects = []
        self.hit_count = 0
    
    def get_filled_rows(self, section: str) -> int:
        """Beräknar antal fyllda rader i en sektion"""
        if section == "T":
            return self.total_trauma // self.damage_tolerance
        elif section == "S":
            return self.total_pain // self.damage_tolerance
        return 0
    
    def get_chock_difficulty(self) -> int:
        """Beräknar svårighet för chockslag (T + S rader)"""
        return (self.get_filled_rows("T") +
                self.get_filled_rows("S"))
    
    def get_death_difficulty(self) -> int:
        """Beräknar svårighet för dödsslag (endast T rader, EJ smärta)"""
        return self.get_filled_rows("T")
    
    def should_roll_chock(self, trauma_added: int, pain_added: int) -> bool:
        """Avgör om chockslag ska slås"""
        return (trauma_added > 0 or pain_added > 0)
    
    def should_roll_death(self, trauma_added: int) -> bool:
        """Avgör om dödsslag ska slås"""
        return trauma_added > 0
    
    def roll_chock(self) -> Tuple[List[int], int, bool]:
        """Slår chockslag och returnerar (tärningar, summa, klarar)"""
        difficulty = self.get_chock_difficulty()
        
        if difficulty == 0:
            return ([], 0, True)
        
        dice = [random.randint(1, 6) for _ in range(difficulty)]
        total = sum(dice)
        success = total <= self.chock_value
        
        if not success:
            self.conscious = False
        
        return (dice, total, success)
    
    def roll_death(self) -> Tuple[List[int], int, bool]:
        """Slår dödsslag och returnerar (tärningar, summa, klarar)"""
        difficulty = self.get_death_difficulty()
        
        if difficulty == 0:
            return ([], 0, True)
        
        dice = [random.randint(1, 6) for _ in range(difficulty)]
        total = sum(dice)
        success = total <= self.chock_value
        
        if not success:
            self.alive = False
        
        return (dice, total, success)

class SmallSpiderManager:
    """Hanterar alla små spindlar för en guild"""

    def __init__(self, guild_id: int = None):
        self.guild_id = guild_id
        self.spiders: Dict[int, SmallSpider] = {}  # ID → Spider
        self.spider_names: Dict[str, int] = {}  # Namn → ID (för snabb lookup)
        self.used_names: set = set()  # Namn som används av levande spindlar
        self.next_id = 1

        # Claude API för AI-beskrivningar
        self.anthropic_client = None
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        if anthropic_key:
            self.anthropic_client = anthropic.Anthropic(api_key=anthropic_key)
    
    def _get_available_name(self) -> Optional[str]:
        """Hämtar ett ledigt namn från listan"""
        available = [name for name in SMALL_SPIDER_NAMES if name not in self.used_names]
        if not available:
            return None
        return random.choice(available)

    def spawn(self, count: int) -> List[Tuple[int, str]]:
        """Spawnar nya spindlar och returnerar lista med (ID, namn)"""
        spawned = []
        for _ in range(count):
            name = self._get_available_name()
            if name is None:
                # Om alla namn är upptagna, återanvänd ett från en död spindel
                dead_spiders = [s for s in self.spiders.values() if not s.alive]
                if dead_spiders:
                    name = random.choice(dead_spiders).name
                else:
                    # Fallback: använd generiskt namn
                    name = f"Spindel #{self.next_id}"

            spider_id = self.next_id
            spider = SmallSpider(spider_id, name)
            self.spiders[spider_id] = spider
            self.spider_names[name] = spider_id
            self.used_names.add(name)
            spawned.append((spider_id, name))
            self.next_id += 1

        return spawned
    
    def get_spider(self, spider_id: int) -> Optional[SmallSpider]:
        """Hämtar en specifik spindel via ID"""
        return self.spiders.get(spider_id)

    def get_spider_by_name(self, name: str) -> Optional[SmallSpider]:
        """Hämtar en specifik spindel via namn"""
        spider_id = self.spider_names.get(name)
        if spider_id is not None:
            return self.spiders.get(spider_id)
        return None
    
    def get_alive_spiders(self) -> List[SmallSpider]:
        """Returnerar alla levande spindlar"""
        return [s for s in self.spiders.values() if s.alive]
    
    def _roll_location(self) -> Tuple[str, int]:
        """Slumpar träffzon"""
        roll = random.randint(1, 10)
        for min_val, max_val, location in SMALL_SPIDER_LOCATION_TABLE:
            if min_val <= roll <= max_val:
                return location, roll
        return "kropp", roll
    
    def _get_armor(self, location: str, weapon_type: str) -> int:
        """Hämtar rustningsvärde"""
        if location in SMALL_SPIDER_ARMOR:
            return SMALL_SPIDER_ARMOR[location].get(weapon_type.lower(), 0)
        return 0
    
    def _calculate_damage(self, weapon_type: str, location: str, effective_damage: int) -> Dict:
        """Beräknar skada från tabell"""
        if location not in SMALL_SPIDER_DAMAGE_TABLES:
            raise ValueError(f"Ingen skadetabell för '{location}'")
        
        weapon_tables = SMALL_SPIDER_DAMAGE_TABLES[location]
        if weapon_type.lower() not in weapon_tables:
            raise ValueError(f"Ingen tabell för {weapon_type} mot {location}")
        
        damage_table = weapon_tables[weapon_type.lower()]
        
        if effective_damage < 10:
            return {
                "description": damage_table["ytlig"]["beskrivning"],
                "effect_code": damage_table["ytlig"]["effekt"],
                "effects": []
            }
        
        roll = random.randint(1, 5)
        
        for max_val, description, effect_code, effects in damage_table["allvarlig"]:
            if roll <= max_val:
                return {
                    "description": description,
                    "effect_code": effect_code,
                    "effects": effects or []
                }
        
        return {
            "description": "Okänd skada",
            "effect_code": "T/10, S/10, B/10",
            "effects": []
        }
    
    def process_attack(
        self,
        spider_id: int,
        weapon_type: str,
        location: str,
        raw_damage: int
    ) -> SmallSpiderDamageResult:
        """Processerar en attack mot en liten spindel"""
        
        spider = self.get_spider(spider_id)
        if not spider:
            raise ValueError(f"Spindel #{spider_id} finns inte!")
        
        if not spider.alive:
            raise ValueError(f"Spindel #{spider_id} är redan död!")
        
        # Slumpa plats om "slumpa"
        location_roll = None
        if location.lower() == "slumpa":
            location, location_roll = self._roll_location()
        
        # Beräkna skada
        armor = self._get_armor(location, weapon_type)
        effective_damage = max(0, raw_damage - armor)
        damage_result = self._calculate_damage(weapon_type, location, effective_damage)
        
        # Beräkna T/S
        ts_values = parse_effect_code(damage_result["effect_code"], effective_damage)
        trauma = ts_values.get("T", 0)
        pain = ts_values.get("S", 0)

        # Applicera skada
        spider.total_trauma += trauma
        spider.total_pain += pain
        spider.hit_count += 1

        # Lägg till effekter
        for effect in damage_result["effects"]:
            if effect not in spider.active_effects:
                spider.active_effects.append(effect)

        # Kolla om slag behövs
        chock_roll = None
        death_roll = None

        if spider.should_roll_chock(trauma, pain):
            chock_roll = spider.roll_chock()

        if spider.should_roll_death(trauma):
            death_roll = spider.roll_death()
        
        # Bygg resultat
        result = SmallSpiderDamageResult(
            spider_id=spider_id,
            weapon_type=weapon_type,
            raw_damage=raw_damage,
            hit_location=location,
            armor=armor,
            effective_damage=effective_damage,
            trauma=trauma,
            pain=pain,
            description=damage_result["description"],
            effects=damage_result["effects"],
            location_roll=location_roll,
            chock_roll=chock_roll,
            death_roll=death_roll,
            is_dead=not spider.alive,
            is_unconscious=not spider.conscious
        )
        
        return result

    async def generate_ai_description(self, spider: SmallSpider, result: SmallSpiderDamageResult) -> Optional[str]:
        """Genererar AI-driven dramatisk beskrivning för småspindel"""
        if not self.anthropic_client:
            return None

        try:
            context = {
                "spider_name": spider.name,
                "weapon": result.weapon_type,
                "location": result.hit_location,
                "damage": result.effective_damage,
                "description": result.description,
                "effects": result.effects,
                "is_dead": result.is_dead,
                "is_unconscious": result.is_unconscious
            }

            status = ""
            if result.is_dead:
                status = f"{spider.name} dog av träffen."
            elif result.is_unconscious:
                status = f"{spider.name} föll medvetslös."

            prompt = f"""Du är en dramatisk berättare för ett mörkt fantasy-rollspel i EON-universumet.
Beskriv följande attack mot en liten spindel vid namn {context['spider_name']} i 2-3 korta meningar.
Var actionbetonad, visuell och inkludera ljud, rörelser och reaktioner.

MILJÖ: Striden utspelar sig i en snötyngd nordisk skog med höga granar och klippformationer i närheten.
Snön yrrar, träden knakar och klipporna kastar mörka skuggor.

Attack mot {context['spider_name']}:
- Vapentyp: {context['weapon']}
- Träffområde: {context['location']}
- Effektiv skada: {context['damage']}
- Resultat: {context['description']}
- Effekter: {', '.join(context['effects']) if context['effects'] else 'Inga särskilda effekter'}
{f'- SLUTSTATUS: {status}' if status else ''}

Skriv ENDAST beskrivningen på svenska, ingen metakommentar eller annan text."""

            message = self.anthropic_client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=200,
                messages=[{"role": "user", "content": prompt}]
            )

            return message.content[0].text.strip()

        except Exception as e:
            print(f"Fel vid AI-beskrivning för småspindel: {e}")
            return None

    def reset(self):
        """Återställer alla spindlar"""
        self.spiders = {}
        self.spider_names = {}
        self.used_names = set()
        self.next_id = 1
