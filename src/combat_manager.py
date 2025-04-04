import random
from dataclasses import dataclass
from typing import Optional, Tuple, Any

from hit_tables import (
    WeaponType,
    AttackLevel,
    BASE_HIT_TABLE,
    get_hit_location,
    get_mounted_hit_modification,
    get_mount_hit_location,
    get_quadruped_hit_location
)
from damage_tables import (
    DamageType,
    DamageResult,
    DamageCalculator,
    parse_effect_code
)

@dataclass
class CombatResult:
    """
    Representerar resultatet av en attack.
    
    Attributes:
        weapon_type (WeaponType): Vapentypen som användes.
        damage_value (int): Angivet skadevärde.
        location_roll (Optional[int]): Rullat värde för träffområdet (None om override används).
        hit_location (str): Huvudträffområdet.
        sub_location (str): Delområde (t.ex. specifikt ansikte om huvudet träffas).
        location_code (str): Kod för träffområdet (används för referens).
        damage_type (DamageType): Skadetyp baserat på vapentypen.
        damage_result (DamageResult): Resultatet från skadedetekalculeringen.
        is_mounted (bool): Om attacken sker när ryttare är involverad.
        is_quadruped (bool): Om attacken sker mot ett fyrbent djur.
        direction (Optional[str]): Eventuell riktning för attacken.
    use_malpunkter (bool): Om Målpunkter-tekniken används.
    """
    weapon_type: WeaponType
    damage_value: int
    location_roll: Optional[int]
    hit_location: str
    sub_location: str
    location_code: str
    damage_type: DamageType
    damage_result: DamageResult
    is_mounted: bool = False
    is_quadruped: bool = False
    direction: Optional[str] = None
    use_malpunkter: bool = False

class CombatManager:
    def __init__(self) -> None:
        self.damage_calculator: DamageCalculator = DamageCalculator()
        
        # Tabeller för T10-slag för delområden
        self.DELOMRADE_TABLE: dict[str, dict[Tuple[int, int], str]] = {
            "huvud": {
                (1, 4): "ansikte",
                (5, 8): "skalle",
                (9, 10): "hals"
            },
            "arm": {
                (1, 2): "skuldra",
                (3, 4): "överarm",
                (5, 5): "armbage",
                (6, 8): "underarm",
                (9, 10): "hand"
            },
            "bröstkorg": {
                (1, 10): "bröstkorg"
            },
            "buk": {
                (1, 8): "mage",
                (9, 10): "underliv"
            },
            "ben": {
                (1, 2): "höft",
                (3, 4): "lår",
                (5, 6): "knä",
                (7, 9): "vad",
                (10, 10): "fot"
            }
        }

        # Mappning för att mappa sub-location till skadetabellen
        self.location_mapping: dict[str, str] = {
            # Huvudets delområden
            "huvud": "huvud",
            "ansikte": "ansikte",
            "skalle": "skalle", 
            "hals": "hals",
            # Armens delområden
            "vänster arm": "arm",
            "höger arm": "arm",
            "arm": "arm",
            "skuldra": "arm",
            "överarm": "arm",
            "armbage": "arm",
            "underarm": "arm",
            "hand": "arm",
            # Bröstkorg
            "bröstkorg": "bröstkorg",
            # Bukens delområden
            "buk": "mage",
            "mage": "mage",
            "underliv": "mage",
            # Benets delområden
            "vänster ben": "ben",
            "höger ben": "ben",
            "ben": "ben",
            "höft": "ben",
            "lår": "ben", 
            "knä": "ben",
            "vad": "ben",
            "fot": "ben"
        }

    def _get_hit_location(self, attack_level: str, location_roll: int, dtype: DamageType) -> Tuple[str, Optional[int], str]:
        """
        Bestämmer träffområdet baserat på attacknivå, rullat värde och skadetyp.
        
        Args:
            attack_level (str): Attacknivån.
            location_roll (int): Det rullade värdet (1-100).
            dtype (DamageType): Den aktuella skadetypen.
        
        Returns:
            Tuple[str, Optional[int], str]: En tuple med (hit_location, sub_roll, sub_location).
        
        Raises:
            ValueError: Om attack_level saknas i tabellen eller om slaget är ogiltigt.
        """
        table_key: str = "hugg_kross" if dtype in [DamageType.HUGG, DamageType.KROSS] else "stick_avstand"
        if attack_level not in BASE_HIT_TABLE[table_key]:
            raise ValueError(f"Nivån {attack_level} finns inte för {dtype}")
        for (lower, upper), (location, subloc, code) in BASE_HIT_TABLE[table_key][attack_level]:
            if lower <= location_roll <= upper:
                if location == "huvud":
                    sub_roll: int = random.randint(1, 10)
                    for (sub_lower, sub_upper), sub_location in self.DELOMRADE_TABLE["huvud"].items():
                        if sub_lower <= sub_roll <= sub_upper:
                            return location, sub_roll, sub_location
                return location, None, location
        raise ValueError(f"Ogiltigt slag {location_roll} för {dtype.name} / {attack_level}")

    def _get_sub_location(self, main_location: str) -> Tuple[str, Optional[int]]:
        """
        Slår för delområde för de kroppsdelar som har sådana.
        
        Args:
            main_location (str): Huvudområdet (ex. 'huvud' eller 'buk').
        
        Returns:
            Tuple[str, Optional[int]]: (sub_location, sub_roll) där sub_roll kan vara None.
        """
        main_lower: str = main_location.lower()
        if main_lower in ["huvud", "buk"]:
            sub_roll: int = random.randint(1, 10)
            for (sub_lower, sub_upper), sub_loc in self.DELOMRADE_TABLE[main_lower].items():
                if sub_lower <= sub_roll <= sub_upper:
                    return sub_loc, sub_roll
        return main_location, None

    def _determine_location(
        self,
        attack_level: Optional[str],
        location_override: Optional[str],
        damage_type: DamageType
    ) -> Tuple[str, Optional[int], str, str]:
        """
        Bestämmer träffområdet baserat på antingen override eller genom att slå slumpmässigt.
        
        Args:
            attack_level (Optional[str]): Attacknivå (om override inte ges).
            location_override (Optional[str]): Angivet område att använda direkt.
            damage_type (DamageType): Den aktuella skadetypen.
        
        Returns:
            Tuple[str, Optional[int], str, str]:
                - damage_location: Området som används i skadetabellen.
                - location_roll: Det rullade värdet (None om override används).
                - hit_location: Huvudträffområdet.
                - sub_location: Det bestämda delområdet.
        
        Raises:
            ValueError: Om varken attack_level eller override anges, eller om mappning misslyckas.
        """
        if location_override:
            hit_location: str = location_override
            sub_location, _ = self._get_sub_location(hit_location)
            location_roll: Optional[int] = None
            damage_location: Optional[str] = self.location_mapping.get(sub_location.lower())
            return damage_location, location_roll, hit_location, sub_location
        else:
            if not attack_level:
                raise ValueError("Antingen attack_level eller location_override måste anges")
            location_roll = random.randint(1, 100)
            hit_location, _, _ = self._get_hit_location(attack_level, location_roll, damage_type)
            sub_location, _ = self._get_sub_location(hit_location)
            damage_location: Optional[str] = self.location_mapping.get(sub_location.lower())
            return damage_location, location_roll, hit_location, sub_location

    def process_attack(
        self,
        weapon_type: str,
        attack_level: Optional[str],
        damage_value: int,
        location_override: Optional[str],
        is_mounted: bool,
        is_quadruped: bool,
        direction: Optional[str] = None,
        use_malpunkter: bool = False
    ) -> CombatResult:
        """
        Bearbetar en attack och returnerar ett CombatResult med all information.
        
        Args:
            weapon_type (str): Vapentypen som sträng.
            attack_level (Optional[str]): Attacknivån (om override inte ges).
            damage_value (int): Skadevärdet.
            location_override (Optional[str]): Om ett specifikt träffområde ska användas.
            is_mounted (bool): Om attacken sker från en rytter.
            is_quadruped (bool): Om motståndaren är ett fyrbent djur.
            direction (Optional[str]): Eventuell riktning.
        
        Returns:
            CombatResult: Ett objekt med all information om attacken.
        
        Raises:
            ValueError: Om vapentypen är ogiltig, attack_level saknas, eller mappningen misslyckas.
        """
        try:
            w_type: WeaponType = WeaponType(weapon_type)
        except ValueError:
            raise ValueError(f"Ogiltig vapentyp: {weapon_type}")

        # Bestäm damage_type baserat på vapentypen
        damage_type: DamageType = {
            WeaponType.HUGG: DamageType.HUGG,
            WeaponType.KROSS: DamageType.KROSS,
            WeaponType.STICK: DamageType.STICK,
            WeaponType.AVSTAND: DamageType.STICK
        }[w_type]

        # Bestäm träffområde
        damage_location, location_roll, hit_location, sub_location = self._determine_location(attack_level, location_override, damage_type)
        if not damage_location:
            raise ValueError(f"Kunde inte mappa träffområde: {hit_location} -> {sub_location}")

        # Beräkna skada
        damage_result: DamageResult = self.damage_calculator.get_damage(
            damage_type=damage_type,
            location=damage_location,
            damage_value=damage_value,
            use_malpunkter=use_malpunkter
        )

        location_code: str = str(location_roll) if location_roll is not None else "override"

        return CombatResult(
            weapon_type=w_type,
            damage_value=damage_value,
            location_roll=location_roll,
            hit_location=hit_location,
            sub_location=sub_location,
            location_code=location_code,
            damage_type=damage_type,
            damage_result=damage_result,
            is_mounted=is_mounted,
            is_quadruped=is_quadruped,
            direction=direction,
            use_malpunkter=use_malpunkter
        )
        
    def format_result(self, result: CombatResult) -> str:
        """
        Formaterar ett CombatResult till en sträng för utskrift.
        
        Args:
            result (CombatResult): Resultatet att formatera.
        
        Returns:
            str: En formaterad sträng med information om attacken.
        """
        lines: list[str] = []

        # Grundinformation
        lines.append(f"Vapentyp: {result.weapon_type.value}")
        lines.append(f"Skadevärde: {result.damage_value}")
        if result.location_roll is not None:
            lines.append(f"Träffslag: {result.location_roll}")
        
        # Träffområde
        location_text: str = f"Träffområde: {result.hit_location.capitalize()}"
        if result.sub_location and result.sub_location != result.hit_location:
            location_text += f" ({result.sub_location.capitalize()})"
        location_text += f" [kod: {result.location_code}]"
        lines.append(location_text)

        # Skadetyp
        lines.append(f"Skadetyp: {result.damage_type.value}")
        
        # Effektkod och effekter
        damage_result = result.damage_result
        effect_code: str = damage_result.effect_code
        effects: list[str] = damage_result.effects
        description: str = damage_result.description if damage_result.description else "Ingen detaljerad beskrivning"

        lines.append(f"Beskrivning: {description}")

        # Numeriska effekter
        numeric_results: dict[str, Any] = parse_effect_code(effect_code, result.damage_value)
        numeric_str: str = ", ".join(f"{k}={v}" for k, v in numeric_results.items())
        eff_text: str = f"Effekter: {effect_code}"
        if numeric_str:
            eff_text += f" => {numeric_str}"
        lines.append(eff_text)
        
        # Extra effekter
        if effects:
            lines.append(f"Extra effekter: {', '.join(effects)}")
            
        # Om Målpunkter användes
        if result.use_malpunkter:
            lines.append("Målpunkter-tekniken användes")

        return "\n".join(lines)
