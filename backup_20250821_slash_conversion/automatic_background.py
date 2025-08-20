"""
Automatisk bakgrundsgenerator för EON-rollpersoner
Slår alla nödvändiga tärningar för familj, syskon, födelsedag, mentor etc.
och presenterar resultatet som en sammanhängande berättelse.
"""

import random
import json
import os
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass

@dataclass
class SiblingInfo:
    """Information om ett syskon"""
    gender: str  # "bror" eller "syster"
    age: int
    relationship: str  # "äldre" eller "yngre"
    is_illegitimate: bool = False

@dataclass
class ParentInfo:
    """Information om en förälder"""
    status: str  # "lever", "död", "okänd"
    age: Optional[int] = None
    death_cause: Optional[str] = None

@dataclass
class FamilyBackground:
    """Komplett familjebakgrund"""
    birth_info: str
    siblings: List[SiblingInfo]
    father: ParentInfo
    mother: ParentInfo
    family_special: str
    mentor_info: Optional[str] = None  # För alver

class AutomaticBackgroundGenerator:
    """Genererar automatiskt komplett bakgrund för rollpersoner"""
    
    def __init__(self, data_dir: str = None):
        if data_dir is None:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(script_dir)
            self.data_dir = os.path.join(project_root, 'data', 'character_tables')
        else:
            self.data_dir = data_dir
        
        self.family_tables = self._load_family_tables()
        self.calendar_data = self._load_calendar_data()
    
    def _load_family_tables(self) -> Dict[str, Any]:
        """Laddar familjetabeller från JSON-filer"""
        tables = {}
        family_dir = os.path.join(self.data_dir, 'familj')
        if os.path.exists(family_dir):
            for filename in os.listdir(family_dir):
                if filename.endswith('.json'):
                    filepath = os.path.join(family_dir, filename)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            table_name = filename.replace('.json', '')
                            tables[table_name] = json.load(f)
                    except Exception as e:
                        print(f"Fel vid laddning av {filename}: {e}")
        return tables
    
    def _load_calendar_data(self) -> Dict[str, Any]:
        """Laddar kalenderdata för födelsedag"""
        # Baserat på texten - månader och veckor
        months = {
            1: "januari", 2: "februari", 3: "mars", 4: "april", 
            5: "maj", 6: "juni", 7: "juli", 8: "augusti",
            9: "september", 10: "oktober", 11: "november", 12: "december"
        }
        
        week_phases = {
            1: "fullmåne", 2: "fullmåne", 3: "avtagande", 4: "avtagande",
            5: "nytändning", 6: "nytändning", 7: "växande", 8: "växande"
        }
        
        weekdays = {
            1: "söndag", 2: "måndag", 3: "vigdag", 4: "mittdag",
            5: "åskdag", 6: "fridag", 7: "lördag"
        }
        
        return {
            "months": months,
            "week_phases": week_phases,
            "weekdays": weekdays
        }
    
    def generate_birth_info(self, race: str) -> str:
        """Genererar information om födelsedag/tidpunkt"""
        race_lower = race.lower()
        
        # Alver och vissa tiraker har osäker födelsetidpunkt
        if any(x in race_lower for x in ["sanari", "thism", "kiriya", "henea", "learam", "pyar"]):
            if "frakk" not in race_lower:  # Normala alver
                return self._generate_uncertain_birth()
        
        if "frakk" in race_lower:
            return self._generate_uncertain_birth()
        
        if any(x in race_lower for x in ["ghor", "roghan", "drezin"]):
            return self._generate_dwarven_birth()
        
        # Vanlig kalender för människor, misslor, zolod-dvärgar, marnakh-tiraker
        return self._generate_normal_birth()
    
    def _generate_uncertain_birth(self) -> str:
        """Genererar osäker födelsetidpunkt för alver och frakk-tiraker"""
        uncertain_times = [
            "när snön låg tung", "strax före snösmältningen", "strax efter snösmältningen",
            "vid första snöfallet", "under den fruktansvärda snöstormen", "under en höststorm",
            "under en åskvädersnatt", "när äppelträden blommade", "på försommaren",
            "strax innan midsommar", "när solen smekte de gröna ängarna", "strax efter midsommar",
            "på sensommaren", "vid höstdagjämningen", "vid vårdagjämningen",
            "när alla löven fallit", "när gässen flög söderut"
        ]
        
        roll = random.randint(1, 100)
        if roll <= 95:
            return f"födelsetidpunkt: {random.choice(uncertain_times)}"
        else:
            return "födelsetidpunkt: ingen har ens en liten aning"
    
    def _generate_dwarven_birth(self) -> str:
        """Genererar dvärgisk födelsedag"""
        week = random.randint(1, 42)
        day = random.randint(1, 8)
        
        day_names = ["förstadag", "andradag", "tredjedag", "fjärdedag", 
                    "femtedag", "sjättedag", "sjundedag", "åttåndedag"]
        
        return f"född vecka {week}, {day_names[day-1]}"
    
    def _generate_normal_birth(self) -> str:
        """Genererar normal födelsedag"""
        month_roll = random.randint(1, 100)
        month = ((month_roll - 1) // 8) + 1
        if month > 12:
            month = 12
        
        week_roll = random.randint(1, 10)
        if week_roll >= 9:
            return f"födelsetidpunkt: vet år och månad ({self.calendar_data['months'][month]}) men inte exakt dag"
        
        day_roll = random.randint(1, 7)
        phase = self.calendar_data['week_phases'][week_roll] if week_roll <= 8 else "okänd"
        weekday = self.calendar_data['weekdays'][day_roll]
        
        return f"född i {self.calendar_data['months'][month]}, {phase}vecka, {weekday}"
    
    def generate_siblings(self, race: str, age: int) -> List[SiblingInfo]:
        """Genererar syskon baserat på ras"""
        race_lower = race.lower()
        siblings = []
        
        if any(x in race_lower for x in ["marnakh", "bazirk", "frakk", "gurd", "truhk"]):
            # Tiraker har kullar
            return self._generate_tirak_siblings(age)
        
        # Bestäm antal syskon baserat på ras
        if any(x in race_lower for x in ["ghor", "roghan", "zolod", "drezin"]) or \
           any(x in race_lower for x in ["sanari", "thism", "kiriya", "henea", "learam", "pyar"]):
            # Dvärgar och alver: färre syskon
            older_count = max(0, random.randint(1, 6) - 3)
            younger_count = max(0, random.randint(1, 6) - 3)
        else:
            # Människor och misslor: fler syskon
            older_count = max(0, random.randint(1, 6) - 2)
            younger_count = max(0, random.randint(1, 6) - 2)
        
        # Generera äldre syskon
        for _ in range(older_count):
            gender = "syster" if random.randint(1, 2) == 1 else "bror"
            sibling_age = age + random.randint(1, 6)
            is_illegitimate = False
            
            # Kolla oäkta barn (inte för dvärgar)
            if not any(x in race_lower for x in ["ghor", "roghan", "zolod", "drezin"]):
                if random.randint(1, 10) == 10:
                    is_illegitimate = True
            
            siblings.append(SiblingInfo(gender, sibling_age, "äldre", is_illegitimate))
        
        # Generera yngre syskon
        for _ in range(younger_count):
            gender = "syster" if random.randint(1, 2) == 1 else "bror"
            sibling_age = max(1, age - random.randint(1, 6))
            is_illegitimate = False
            
            if not any(x in race_lower for x in ["ghor", "roghan", "zolod", "drezin"]):
                if random.randint(1, 10) == 10:
                    is_illegitimate = True
            
            if sibling_age > 0:
                siblings.append(SiblingInfo(gender, sibling_age, "yngre", is_illegitimate))
        
        return siblings
    
    def _generate_tirak_siblings(self, age: int) -> List[SiblingInfo]:
        """Genererar tiraksyskon (kullar)"""
        siblings = []
        
        # Äldre kullar
        older_litters = max(0, random.randint(1, 6) - 2)
        for _ in range(older_litters):
            litter_size = max(1, (random.randint(1, 6) // 2) + 1)
            litter_age = age + random.randint(1, 6)
            
            # Bestäm kön för hela kullen (pojkar vanligare)
            gender_roll = random.randint(1, 10)
            if gender_roll <= 8:
                gender = "bror"
            else:
                gender = "syster"
            
            for _ in range(litter_size):
                siblings.append(SiblingInfo(gender, litter_age, "äldre"))
        
        # Jämnåriga (samma kull som rollpersonen)
        same_litter_size = max(0, (random.randint(1, 6) // 2))
        gender_roll = random.randint(1, 10)
        if gender_roll <= 8:
            gender = "bror"
        else:
            gender = "syster"
        
        for _ in range(same_litter_size):
            siblings.append(SiblingInfo(gender, age, "jämnårig"))
        
        # Yngre kullar
        younger_litters = max(0, random.randint(1, 6) - 2)
        for _ in range(younger_litters):
            litter_size = max(1, (random.randint(1, 6) // 2) + 1)
            litter_age = max(1, age - random.randint(1, 6))
            
            gender_roll = random.randint(1, 10)
            if gender_roll <= 8:
                gender = "bror"
            else:
                gender = "syster"
            
            for _ in range(litter_size):
                if litter_age > 0:
                    siblings.append(SiblingInfo(gender, litter_age, "yngre"))
        
        return siblings
    
    def generate_parents_status(self, race: str, oldest_sibling_age: int) -> Tuple[ParentInfo, ParentInfo]:
        """Genererar föräldrars status och ålder"""
        race_lower = race.lower()
        
        # Basålder för äldsta syskon (eller rollpersonen om hen är äldst)
        base_age = oldest_sibling_age
        
        # Modifierat slag baserat på ålder
        roll = random.randint(1, 100) + base_age
        
        # Justera för alver (de slår bara 1d100)
        if any(x in race_lower for x in ["sanari", "thism", "kiriya", "henea", "learam", "pyar"]):
            roll = random.randint(1, 100)
        
        # Bestäm status
        if roll <= 60:
            father_status = "lever"
            mother_status = "lever"
        elif roll <= 80:
            father_status = "okänd"
            mother_status = "lever"
        elif roll <= 95:
            # En förälder död
            if random.randint(1, 2) == 1:
                father_status = "död"
                mother_status = "lever"
            else:
                father_status = "lever"
                mother_status = "död"
        else:
            father_status = "död"
            mother_status = "död"
        
        # Generera åldrar och dödsorsaker
        father = self._create_parent_info(father_status, base_age, "far", race_lower)
        mother = self._create_parent_info(mother_status, base_age, "mor", race_lower)
        
        return father, mother
    
    def _create_parent_info(self, status: str, base_age: int, parent_type: str, race: str) -> ParentInfo:
        """Skapar information om en förälder"""
        parent = ParentInfo(status)
        
        if status == "lever":
            # Beräkna ålder baserat på ras
            if any(x in race for x in ["ghor", "roghan", "zolod", "drezin"]):
                # Dvärgar
                parent.age = base_age + 28 + sum(random.randint(1, 6) for _ in range(4))
            elif any(x in race for x in ["sanari", "thism", "kiriya", "henea", "learam", "pyar"]):
                # Alver
                parent.age = base_age + 10 + sum(random.randint(1, 6) for _ in range(6))
            else:
                # Människor, misslor, tiraker
                parent.age = base_age + 14 + sum(random.randint(1, 6) for _ in range(2))
        
        elif status == "död":
            parent.death_cause = self._generate_death_cause(parent_type)
        
        return parent
    
    def _generate_death_cause(self, parent_type: str) -> str:
        """Genererar dödsorsak för en död förälder"""
        death_causes = {
            "man": [
                "strid", "fångenskap hos fienden", "avrättning", "mord", 
                "olycka", "ålderdom", "sjukdom"
            ],
            "kvinna": [
                "mord", "olycka", "ålderdom", "barnsäng", "sjukdom"
            ]
        }
        
        if parent_type == "far":
            return random.choice(death_causes["man"])
        else:
            return random.choice(death_causes["kvinna"])
    
    def generate_family_special(self, race: str) -> str:
        """Genererar speciella familjeförhållanden"""
        race_lower = race.lower()
        
        # Använd familjetabeller om de finns
        if "missla" in race_lower and "familj_ovr" in self.family_tables:
            # Skulle behöva implementera missletabell separat
            pass
        
        # För nu, använd den generella tabellen
        if "familj_ovr" in self.family_tables:
            return self._roll_on_family_table("familj_ovr")
        
        # Fallback till enkla resultat
        return self._generate_simple_family_trait()
    
    def _roll_on_family_table(self, table_name: str) -> str:
        """Slår på en familjetabell"""
        if table_name not in self.family_tables:
            return "Familjen är inte så speciell"
        
        table = self.family_tables[table_name]
        roll = random.randint(1, 100)
        
        # Hitta rätt resultat baserat på tärningsslag
        for key, value in table.get("familjetabeller", {}).get("övriga", {}).get("ranges", {}).items():
            if self._is_roll_in_range(roll, key):
                return value.get("description", "Okänt resultat")
        
        return "Familjen är inte så speciell"
    
    def _is_roll_in_range(self, roll: int, range_str: str) -> bool:
        """Kontrollerar om ett slag är inom ett visst intervall"""
        try:
            if "-" in range_str:
                start, end = map(int, range_str.split("-"))
                return start <= roll <= end
            else:
                return roll == int(range_str)
        except ValueError:
            return False
    
    def _generate_simple_family_trait(self) -> str:
        """Genererar enkla familjeegenskaper som fallback"""
        traits = [
            "Familjen är inte så speciell",
            "Familjen är mycket fattig",
            "Familjen är ovanligt rik",
            "Familjen har hemliga traditioner",
            "Familjen är välkänd i trakten",
            "Familjen håller sig för sig själv",
            "Familjen har många kontakter",
            "Familjen har dåligt rykte"
        ]
        return random.choice(traits)
    
    def generate_elf_mentor(self, race: str) -> Optional[str]:
        """Genererar mentor-information för alver"""
        race_lower = race.lower()
        
        # Bara alver har mentorer
        if not any(x in race_lower for x in ["sanari", "thism", "kiriya", "henea", "learam", "pyar"]):
            return None
        
        # Enkel mentor-generering (skulle kunna utökas med mentortabeller)
        mentor_types = [
            "en vis och erfaren äldre alv som lärde ut livets grundläggande färdigheter",
            "en respekterad hantverkare som delade sina kunskaper",
            "en före detta äventyrare med många berättelser att dela",
            "en mystisk alv med kunskap om gammal magi",
            "en praktisk alv som lärde ut överlevnadsfärdigheter",
            "en diplomatisk alv som undervisade i etikett och sociala färdigheter"
        ]
        
        return f"Mentor: {random.choice(mentor_types)}"
    
    def generate_complete_background(self, race: str, age: int) -> FamilyBackground:
        """Genererar komplett familjebakgrund för en rollperson"""
        # Generera alla komponenter
        birth_info = self.generate_birth_info(race)
        siblings = self.generate_siblings(race, age)
        
        # Hitta äldsta syskonets ålder för föräldraberäkningar
        oldest_age = age
        for sibling in siblings:
            if sibling.relationship == "äldre" and sibling.age > oldest_age:
                oldest_age = sibling.age
        
        father, mother = self.generate_parents_status(race, oldest_age)
        family_special = self.generate_family_special(race)
        mentor_info = self.generate_elf_mentor(race)
        
        return FamilyBackground(
            birth_info=birth_info,
            siblings=siblings,
            father=father,
            mother=mother,
            family_special=family_special,
            mentor_info=mentor_info
        )
    
    def format_background_summary(self, background: FamilyBackground) -> str:
        """Formaterar bakgrunden som en läsbar sammanfattning"""
        lines = []
        
        # Födelseinfo
        lines.append(f"🎂 **Födelse:** {background.birth_info}")
        
        # Syskon
        if background.siblings:
            sibling_counts = {}
            for sibling in background.siblings:
                key = f"{sibling.relationship}_{sibling.gender}"
                if key not in sibling_counts:
                    sibling_counts[key] = 0
                sibling_counts[key] += 1
            
            sibling_parts = []
            for key, count in sibling_counts.items():
                relation, gender = key.split("_")
                if relation == "jämnårig":
                    relation_text = "jämnårig"
                else:
                    relation_text = relation
                
                if count == 1:
                    sibling_parts.append(f"1 {relation_text} {gender}")
                else:
                    gender_plural = gender + ("ar" if gender == "syster" else "ar")
                    sibling_parts.append(f"{count} {relation_text} {gender_plural}")
            
            lines.append(f"👥 **Syskon:** {', '.join(sibling_parts)}")
        else:
            lines.append("👥 **Syskon:** inga syskon")
        
        # Föräldrar
        father_status = background.father.status
        mother_status = background.mother.status
        
        if father_status == "lever" and mother_status == "lever":
            lines.append(f"👨‍👩‍👧‍👦 **Föräldrar:** båda lever (far {background.father.age} år, mor {background.mother.age} år)")
        elif father_status == "okänd":
            lines.append(f"👨‍👩‍👧‍👦 **Föräldrar:** far okänd, mor lever ({background.mother.age} år)")
        elif father_status == "död" and mother_status == "lever":
            lines.append(f"👨‍👩‍👧‍👦 **Föräldrar:** far död ({background.father.death_cause}), mor lever ({background.mother.age} år)")
        elif father_status == "lever" and mother_status == "död":
            lines.append(f"👨‍👩‍👧‍👦 **Föräldrar:** far lever ({background.father.age} år), mor död ({background.mother.death_cause})")
        else:
            lines.append("👨‍👩‍👧‍👦 **Föräldrar:** båda döda")
        
        # Familjespecialitet
        lines.append(f"🏠 **Familjen:** {background.family_special}")
        
        # Mentor (för alver)
        if background.mentor_info:
            lines.append(f"🧙‍♂️ **{background.mentor_info}**")
        
        return "\n".join(lines)
