# src/spindel/spider_combat_manager.py
"""
Stridshanterare för Gigantspindel
Hanterar träffar, skador och spårning av spindelns status

Del av src/spindel/ — se __init__.py. Modulen är avstängd tills vidare
(config/feature_flags.py: slash_spindel_enabled).
"""

import random
import json
import os
from dataclasses import dataclass
from typing import Optional, Dict, List, Tuple

from .spider_damage_tables import (
    SPIDER_DAMAGE_TABLES,
    SPIDER_ARMOR_VALUES,
    SPIDER_SUBLOCATION_TABLES,
    parse_effect_code
)
import anthropic
from core.constants import CLAUDE_MODEL

@dataclass
class SpiderDamageResult:
    """Resultat från en attack mot spindeln"""
    weapon_type: str
    raw_damage: int
    hit_location: str
    sub_location: str
    armor: int
    effective_damage: int
    trauma: int
    pain: int
    blood: int
    description: str
    effects: List[str]
    location_roll: Optional[int] = None

@dataclass
class RoundEndResult:
    """Resultat från slutfas av runda (blödning)"""
    bleeding_applied: int
    blood_loss_before: int
    blood_loss_after: int
    new_row_filled: bool
    chock_roll: Optional[Tuple[List[int], int, bool]]
    death_roll: Optional[Tuple[List[int], int, bool]]
    is_conscious: bool

class SpiderCombatManager:
    """Hanterar strid mot gigantspindeln"""
    
    def __init__(self, guild_id: int = None):
        """Initierar spindelns status"""
        self.guild_id = guild_id
        self.chock_value = 34
        self.damage_tolerance = 10

        self.total_trauma = 0
        self.total_pain = 0

        # EON Blödningstakt-system
        self.bleeding_rate = 0        # Ökas vid attack med B-skada
        self.total_blood_loss = 0     # Ökas varje runda baserat på bleeding_rate
        self.conscious = True         # Medvetandestatus (påverkar blödningstakt)
        
        self.damage_by_location = {
            "ögon": [],
            "ben": 0,
            "chelicerer": 0,
            "carapace": 0,
            "bakkropp": 0,
            "spinnvårtor": 0
        }
        
        self.eyes_destroyed = 0
        self.eyes_damaged = 0
        self.legs_destroyed = 0
        self.legs_damaged = 0
        
        self.active_effects = []
        self.hit_history = []
        
        # Claude API för AI-beskrivningar
        self.anthropic_client = None
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        if anthropic_key:
            self.anthropic_client = anthropic.Anthropic(api_key=anthropic_key)
        
        # Ladda persistent data
        self._load_from_file()
    
    def _get_save_path(self) -> str:
        """Returnerar sökvägen för persistent lagring"""
        # src/spindel/spider_combat_manager.py -> repo-roten är två steg upp
        # (innan flytten till en egen paketmodul låg filen direkt i src/,
        # då räckte ett steg — se git-historik för spider_combat_manager.py).
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(script_dir))
        data_dir = os.path.join(project_root, "data")
        
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
        
        guild_suffix = f"_{self.guild_id}" if self.guild_id else "_default"
        return os.path.join(data_dir, f"spider_status{guild_suffix}.json")
    
    def _save_to_file(self):
        """Sparar spindelns status till fil"""
        try:
            data = {
                "chock_value": self.chock_value,
                "damage_tolerance": self.damage_tolerance,
                "total_trauma": self.total_trauma,
                "total_pain": self.total_pain,
                "bleeding_rate": self.bleeding_rate,
                "total_blood_loss": self.total_blood_loss,
                "conscious": self.conscious,
                "damage_by_location": self.damage_by_location,
                "eyes_destroyed": self.eyes_destroyed,
                "eyes_damaged": self.eyes_damaged,
                "legs_destroyed": self.legs_destroyed,
                "legs_damaged": self.legs_damaged,
                "active_effects": self.active_effects,
                "hit_count": len(self.hit_history)
            }
            
            with open(self._get_save_path(), 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Fel vid sparande av spindelstatus: {e}")
    
    def _load_from_file(self):
        """Laddar spindelns status från fil med migration"""
        try:
            save_path = self._get_save_path()
            if os.path.exists(save_path):
                with open(save_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                self.total_trauma = data.get("total_trauma", 0)
                self.total_pain = data.get("total_pain", 0)

                # Nya blödningssystemet
                self.bleeding_rate = data.get("bleeding_rate", 0)
                self.total_blood_loss = data.get("total_blood_loss", 0)
                self.conscious = data.get("conscious", True)

                # Backward compatibility - migrera gamla "total_blood" till "total_blood_loss"
                if "total_blood" in data and self.total_blood_loss == 0:
                    self.total_blood_loss = data["total_blood"]
                    print(f"⚠️  Migrerade gammalt blödningsvärde: {data['total_blood']} → total_blood_loss")

                self.damage_by_location = data.get("damage_by_location", self.damage_by_location)
                self.eyes_destroyed = data.get("eyes_destroyed", 0)
                self.eyes_damaged = data.get("eyes_damaged", 0)
                self.legs_destroyed = data.get("legs_destroyed", 0)
                self.legs_damaged = data.get("legs_damaged", 0)
                self.active_effects = data.get("active_effects", [])

                print(f"✅ Laddade spindelstatus från fil: {save_path}")
        except Exception as e:
            print(f"❌ Kunde inte ladda spindelstatus: {e}")
    
    def get_save_data(self) -> Dict:
        """Returnerar all data som dict (för dump)"""
        return {
            "guild_id": self.guild_id,
            "chock_value": self.chock_value,
            "damage_tolerance": self.damage_tolerance,
            "total_trauma": self.total_trauma,
            "total_pain": self.total_pain,
            "bleeding_rate": self.bleeding_rate,
            "total_blood_loss": self.total_blood_loss,
            "conscious": self.conscious,
            "trauma_rows": self.get_filled_rows("T"),
            "pain_rows": self.get_filled_rows("S"),
            "blood_loss_rows": self.get_filled_rows("blood_loss"),
            "chock_difficulty": self.get_chock_difficulty(),
            "death_difficulty": self.get_death_difficulty(),
            "damage_by_location": self.damage_by_location,
            "eyes": {
                "destroyed": self.eyes_destroyed,
                "damaged": self.eyes_damaged,
                "status": self.get_eye_status(),
                "penalty": self.get_eye_penalty()[1]
            },
            "legs": {
                "destroyed": self.legs_destroyed,
                "damaged": self.legs_damaged,
                "status": self.get_leg_status()
            },
            "active_effects": self.active_effects,
            "total_hits": len(self.hit_history),
            "save_file": self._get_save_path()
        }
    
    def _normalize_location(self, location: str) -> str:
        """Normaliserar platsnamn till huvudkategori"""
        location_map = {
            "ogon": "ögon",
            "ögon": "ögon",
            "led": "ben",
            "chelicerae": "chelicerer",
            "bettänger": "chelicerer",
            "bettanger": "chelicerer",
            "huvudpansar": "carapace",
            "huvud": "carapace",
            "abdomen": "bakkropp",
            "övre bakkropp": "bakkropp",
            "ovre bakkropp": "bakkropp",
            "undre bakkropp": "bakkropp",
            "spinnvartor": "spinnvårtor"
        }
        return location_map.get(location.lower(), location.lower())
    
    def _roll_sublocation(self, main_location: str) -> Tuple[str, int]:
        """Slumpar delområde baserat på huvudområde"""
        if main_location.lower() not in SPIDER_SUBLOCATION_TABLES:
            return main_location, None
            
        roll = random.randint(1, 10)
        table = SPIDER_SUBLOCATION_TABLES[main_location.lower()]
        
        for min_val, max_val, subloc in table:
            if min_val <= roll <= max_val:
                return subloc, roll
                
        return main_location, roll
    
    def _get_armor(self, location: str, weapon_type: str) -> int:
        """Hämtar rustningsvärde för plats och vapentyp"""
        location_lower = location.lower()
        
        if location_lower in SPIDER_ARMOR_VALUES:
            armor_dict = SPIDER_ARMOR_VALUES[location_lower]
            return armor_dict.get(weapon_type.lower(), 0)
        
        return 0
    
    def _calculate_damage(self, weapon_type: str, location: str, effective_damage: int) -> Dict:
        """Beräknar skada från tabell"""
        location_lower = location.lower()
        weapon_lower = weapon_type.lower()
        
        table_location = self._normalize_location(location)
        
        if table_location not in SPIDER_DAMAGE_TABLES:
            raise ValueError(f"Ingen skadetabell för '{location}'")
        
        weapon_tables = SPIDER_DAMAGE_TABLES[table_location]
        if weapon_lower not in weapon_tables:
            raise ValueError(f"Ingen tabell för {weapon_type} mot {location}")
        
        damage_table = weapon_tables[weapon_lower]
        
        if effective_damage < 10:
            return {
                "description": damage_table["ytlig"]["beskrivning"],
                "effect_code": damage_table["ytlig"]["effekt"],
                "effects": []
            }
        
        roll = random.randint(1, 10)
        
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
        weapon_type: str,
        location: str,
        raw_damage: int,
        is_specific: bool = False
    ) -> SpiderDamageResult:
        """Processar en attack mot spindeln"""
        
        hit_location = location
        sub_location = location
        location_roll = None
        
        if not is_specific:
            sub_location, location_roll = self._roll_sublocation(location)
        
        armor = self._get_armor(sub_location, weapon_type)
        effective_damage = max(0, raw_damage - armor)
        damage_result = self._calculate_damage(weapon_type, sub_location, effective_damage)
        
        tsb_values = parse_effect_code(damage_result["effect_code"], effective_damage)
        trauma = tsb_values.get("T", 0)
        pain = tsb_values.get("S", 0)
        blood = tsb_values.get("B", 0)

        # Trauma och Smärta appliceras direkt
        self.total_trauma += trauma
        self.total_pain += pain

        # B ökar Blödningstakt (ej direkt skada)
        self.bleeding_rate += blood
        
        normalized_loc = self._normalize_location(sub_location)
        
        if normalized_loc == "ögon":
            # Räkna olika nivåer av ögonförstörelse
            destroyed_effects = ["Öga förstört", "Öga bländat", "Öga skadat"]
            if any(effect in damage_result["effects"] for effect in destroyed_effects):
                self.eyes_destroyed += 1
                effect_name = next((e for e in destroyed_effects if e in damage_result["effects"]), "Öga förstört")
                self.damage_by_location["ögon"].append(f"Öga #{self.eyes_destroyed}: {effect_name}")
            elif trauma > 0:
                self.eyes_damaged += 1
        elif normalized_loc == "ben":
            if "Ben avskuret" in damage_result["effects"]:
                self.legs_destroyed += 1
        else:
            self.damage_by_location[normalized_loc] += trauma
        
        for effect in damage_result["effects"]:
            if effect not in self.active_effects:
                self.active_effects.append(effect)
        
        result = SpiderDamageResult(
            weapon_type=weapon_type,
            raw_damage=raw_damage,
            hit_location=hit_location,
            sub_location=sub_location,
            armor=armor,
            effective_damage=effective_damage,
            trauma=trauma,
            pain=pain,
            blood=blood,
            description=damage_result["description"],
            effects=damage_result["effects"],
            location_roll=location_roll
        )
        
        self.hit_history.append(result)
        self._save_to_file()
        
        return result
    
    def get_filled_rows(self, section: str) -> int:
        """Beräknar antal fyllda rader i en sektion"""
        if section == "T":
            return self.total_trauma // self.damage_tolerance
        elif section == "S":
            # Smärta: Spindeln tål DUBBELT (20 poäng/rad)
            return self.total_pain // (self.damage_tolerance * 2)
        elif section == "B" or section == "blood_loss":
            return self.total_blood_loss // self.damage_tolerance
        return 0
    
    def get_chock_difficulty(self) -> int:
        """Beräknar svårighet för chockslag"""
        trauma_rows = self.get_filled_rows("T")
        pain_rows = self.get_filled_rows("S") // 2
        blood_rows = self.get_filled_rows("blood_loss")
        return trauma_rows + pain_rows + blood_rows
    
    def get_death_difficulty(self) -> int:
        """Beräknar svårighet för dödsslag"""
        trauma_rows = self.get_filled_rows("T")
        blood_rows = self.get_filled_rows("blood_loss")
        return trauma_rows + blood_rows
    
    def should_roll_chock(self, last_result: SpiderDamageResult) -> bool:
        """Avgör om chockslag ska slås FRÅN ATTACK (endast T/S)"""
        # B triggar INTE slag från attack (hanteras i process_round_end)
        return (last_result.trauma > 0 or last_result.pain > 0)
    
    def should_roll_death(self, last_result: SpiderDamageResult) -> bool:
        """Avgör om dödsslag ska slås FRÅN ATTACK (endast T)"""
        # B triggar INTE slag från attack (hanteras i process_round_end)
        return last_result.trauma > 0

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

        # Död hanteras ej automatiskt - GM fattar beslut
        return (dice, total, success)

    def wake_up(self) -> None:
        """Väcker spindeln från medvetslöshet (t.ex. vid healing eller vila)"""
        self.conscious = True
        self._save_to_file()

    def process_round_end(self) -> RoundEndResult:
        """Processerar slutfas av runda - applicerar blödning enligt EON-regler"""
        blood_loss_rows_before = self.get_filled_rows("blood_loss")

        # EON-regel: Om BT >= 11, BF per runda = BT/10 (avrundat nedåt)
        if self.bleeding_rate >= 11:
            bleeding_to_apply = self.bleeding_rate // 10
            if not self.conscious:
                bleeding_to_apply = bleeding_to_apply // 2  # Medvetslös = halv takt
        else:
            bleeding_to_apply = 0  # Blödning under 11 BT ger ingen BF

        self.total_blood_loss += bleeding_to_apply

        blood_loss_rows_after = self.get_filled_rows("blood_loss")
        new_row_filled = blood_loss_rows_after > blood_loss_rows_before

        # Slå endast om NY rad fylls
        chock_roll = None
        death_roll = None

        if new_row_filled:
            chock_roll = self.roll_chock()
            death_roll = self.roll_death()

        self._save_to_file()

        return RoundEndResult(
            bleeding_applied=bleeding_to_apply,
            blood_loss_before=blood_loss_rows_before,
            blood_loss_after=blood_loss_rows_after,
            new_row_filled=new_row_filled,
            chock_roll=chock_roll,
            death_roll=death_roll,
            is_conscious=self.conscious
        )

    def get_eye_status(self) -> str:
        """Returnerar ögonstatus med symboler"""
        destroyed = "☒" * self.eyes_destroyed
        intact = "☐" * (8 - self.eyes_destroyed)
        return destroyed + intact
    
    def get_eye_penalty(self) -> Tuple[int, str]:
        """Returnerar ögonmali"""
        if self.eyes_destroyed == 0:
            return 0, "Inga effekter"
        elif self.eyes_destroyed <= 2:
            return 1, "-1T6 på avståndsbedömning"
        elif self.eyes_destroyed <= 4:
            return 2, "-2T6 på alla synbaserade handlingar"
        elif self.eyes_destroyed <= 6:
            return 3, "-3T6, Halvblind, Panikbeteende"
        else:
            return 5, "BLIND - Anfaller vilt åt alla håll"
    
    def get_leg_status(self) -> str:
        """Returnerar benstatus"""
        if self.legs_destroyed == 0:
            return "Alla ben intakta"
        elif self.legs_destroyed <= 2:
            return f"{self.legs_destroyed} ben förstörda - Lätt rörelsehinder"
        elif self.legs_destroyed <= 4:
            return f"{self.legs_destroyed} ben förstörda - Halv hastighet"
        else:
            return f"{self.legs_destroyed} ben förstörda - Kan knappt röra sig"
    
    async def _generate_ai_description(self, result: SpiderDamageResult) -> Optional[str]:
        """Genererar AI-driven dramatisk beskrivning"""
        if not self.anthropic_client:
            return None
        
        try:
            context = {
                "weapon": result.weapon_type,
                "location": result.sub_location,
                "damage": result.effective_damage,
                "description": result.description,
                "effects": result.effects
            }
            
            prompt = f"""Du är en dramatisk berättare för ett mörkt fantasy-rollspel i EON-universumet.
Beskriv följande attack mot en gigantisk spindel i 2-3 meningar.
Var actionbetonad, visuell och inkludera ljud, rörelser och reaktioner.

MILJÖ: Striden utspelar sig i en snötyngd nordisk skog med höga granar och klippformationer i närheten.
Snön yrrar, träden knakar och klipporna kastar mörka skuggor.

Attack:
- Vapentyp: {context['weapon']}
- Träffområde: {context['location']}
- Effektiv skada: {context['damage']}
- Resultat: {context['description']}
- Effekter: {', '.join(context['effects']) if context['effects'] else 'Inga särskilda effekter'}

Skriv ENDAST beskrivningen på svenska, ingen metakommentar eller annan text."""

            message = self.anthropic_client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=300,
                messages=[{"role": "user", "content": prompt}]
            )
            
            return message.content[0].text.strip()
        
        except Exception as e:
            print(f"Fel vid AI-beskrivning: {e}")
            return None
    
    def format_gm_report(self, last_result: SpiderDamageResult, ai_description: Optional[str] = None) -> str:
        """Formaterar detaljerad rapport för GM"""
        lines = []
        lines.append("═" * 50)
        lines.append("🕷️  GIGANTSPINDEL - SKADERAPPORT")
        lines.append("═" * 50)
        
        lines.append("\n【 SENASTE TRÄFF 】")
        lines.append(f"Område: {last_result.hit_location.upper()}")
        if last_result.location_roll:
            lines.append(f"Slumpning (T10): {last_result.location_roll} → {last_result.sub_location}")
        lines.append(f"Exakt plats: {last_result.sub_location.upper()}")
        lines.append(f"Vapentyp: {last_result.weapon_type.upper()}")
        lines.append(f"Rå skada: {last_result.raw_damage}")
        lines.append(f"Rustning: {last_result.armor}")
        lines.append(f"Effektiv skada: {last_result.effective_damage}")
        lines.append(f"\nSkadetyp: {last_result.description}")
        lines.append(f"TSB: T+{last_result.trauma}, S+{last_result.pain}, B+{last_result.blood}")
        if last_result.effects:
            lines.append(f"Effekter: {', '.join(last_result.effects)}")
        
        if ai_description:
            lines.append("\n【 AI-BESKRIVNING 】")
            lines.append(f'"{ai_description}"')
        
        lines.append("\n" + "─" * 50)
        lines.append("【 TOTAL SKADA 】")
        trauma_rows = self.get_filled_rows("T")
        pain_rows = self.get_filled_rows("S")
        blood_loss_rows = self.get_filled_rows("blood_loss")

        lines.append(f"Trauma (T): {self.total_trauma}/{self.damage_tolerance*10} [{trauma_rows} fyllda rader]")
        lines.append(f"Smärta (S): {self.total_pain}/{self.damage_tolerance*20} [{pain_rows} fyllda rader] (tål DUBBELT)")
        lines.append("")
        lines.append("【 BLÖDNING (EON-SYSTEM) 】")
        if last_result.blood > 0:
            lines.append(f"Ny blödningstakt från träff: +{last_result.blood} BT")
        lines.append(f"Total blödningstakt (BT): {self.bleeding_rate} poäng {'(HALVERAS - medvetslös)' if not self.conscious else ''}")

        # Beräkna BF per runda
        if self.bleeding_rate >= 11:
            bf_per_round = self.bleeding_rate // 10
            if not self.conscious:
                bf_per_round = bf_per_round // 2
            lines.append(f"→ Genererar {bf_per_round} BF per runda (BT/10{' /2' if not self.conscious else ''})")
        else:
            lines.append(f"→ Ingen BF per runda (BT < 11)")

        lines.append(f"Blodförlust (BF): {self.total_blood_loss}/{self.damage_tolerance*10} [{blood_loss_rows} fyllda rader]")
        
        lines.append("\n" + "─" * 50)
        lines.append("【 KRITISKA SLAG 】")
        chock_diff = self.get_chock_difficulty()
        death_diff = self.get_death_difficulty()
        lines.append(f"Chockslag: Ob{chock_diff}T6 mot Chockvärde {self.chock_value}")
        lines.append(f"Dödsslag: Ob{death_diff}T6 mot Chockvärde {self.chock_value}")
        
        if self.should_roll_chock(last_result):
            lines.append("⚠️  CHOCKSLAG KRÄVS!")
        if self.should_roll_death(last_result):
            lines.append("💀 DÖDSSLAG KRÄVS!")
        
        lines.append("\n" + "─" * 50)
        lines.append("【 ÖGON (8 st) 】")
        lines.append(f"Status: {self.get_eye_status()}")
        lines.append(f"Förstörda: {self.eyes_destroyed}/8")
        penalty, desc = self.get_eye_penalty()
        lines.append(f"Effekt: {desc}")
        
        lines.append("\n" + "─" * 50)
        lines.append("【 BEN (8 st) 】")
        lines.append(self.get_leg_status())
        
        lines.append("\n" + "─" * 50)
        lines.append("【 SKADA PER KROPPSDEL 】")
        for location, damage in self.damage_by_location.items():
            if location == "ögon":
                if self.damage_by_location["ögon"]:
                    lines.append(f"Ögon: {', '.join(self.damage_by_location['ögon'])}")
            elif damage > 0:
                lines.append(f"{location.capitalize()}: {damage} Trauma")
        
        if self.active_effects:
            lines.append("\n" + "─" * 50)
            lines.append("【 AKTIVA EFFEKTER 】")
            for effect in self.active_effects:
                lines.append(f"• {effect}")
        
        lines.append("\n" + "═" * 50)
        
        return "\n".join(lines)
    
    def format_public_message(self, result: SpiderDamageResult) -> str:
        """Formaterar publikt meddelande för kanalen"""
        lines = []
        lines.append(f"🎯 **TRÄFF PÅ {result.sub_location.upper()}!**")
        lines.append(f"*{result.description}*")
        lines.append(f"\n**Skada:** {result.raw_damage} - {result.armor} rustning = **{result.effective_damage} effektiv skada**")
        lines.append(f"**T+{result.trauma}, S+{result.pain}**")
        if result.blood > 0:
            lines.append(f"**🩸 Blödningstakt +{result.blood}** (genererar blodförlust per runda)")

        if result.effects:
            lines.append(f"\n**Effekter:** {', '.join(result.effects)}")

        return "\n".join(lines)
    
    def reset(self):
        """Återställer spindeln för ny strid"""
        self.total_trauma = 0
        self.total_pain = 0
        self.bleeding_rate = 0
        self.total_blood_loss = 0
        self.conscious = True
        self.damage_by_location = {k: [] if k == "ögon" else 0 for k in self.damage_by_location.keys()}
        self.eyes_destroyed = 0
        self.eyes_damaged = 0
        self.legs_destroyed = 0
        self.legs_damaged = 0
        self.active_effects = []
        self.hit_history = []
        
        try:
            save_path = self._get_save_path()
            if os.path.exists(save_path):
                os.remove(save_path)
                print(f"Raderade spindelstatus: {save_path}")
        except Exception as e:
            print(f"Kunde inte radera spindelstatus: {e}")
