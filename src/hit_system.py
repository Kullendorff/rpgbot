from dataclasses import dataclass
from typing import Optional, List, Dict, Tuple, Any
import random
import logging

logging.basicConfig(level=logging.INFO)

@dataclass
class HitResult:
    """
    Representerar resultatet av en träff.
    
    Attributes:
        location (str): Huvudträffområdet.
        sub_location (str): Det specifika delområdet inom huvudträffområdet.
        code (str): Kod för referens till skadatabeller.
        is_critical (bool): Anger om träffen var kritisk.
        damage_effects (List[str]): Lista med skadeffekter som tillkommit.
    """
    location: str
    sub_location: str
    code: str  # för referens till skadatabeller
    is_critical: bool
    damage_effects: List[str]

class HitSystem:
    def __init__(self) -> None:
        """
        Initierar HitSystem och laddar in nödvändiga tabeller.
        """
        self.tables: Dict[str, Any] = {}  # Exempel på en plats att lagra laddade tabeller
        self.load_tables()
    
    def load_tables(self) -> None:
        """
        Laddar in tabeller från hit_tables.py eller annan källa.
        
        Denna metod bör implementeras med logik för att ladda in nödvändiga
        tabeller som används i beräkningen av träffområden och skada.
        
        Raises:
            NotImplementedError: Om metoden inte är implementerad.
        """
        # TODO: Implementera logik för att ladda tabeller
        raise NotImplementedError("load_tables() måste implementeras")
        
    def get_hit_location(self, weapon_type: str, attack_level: str, roll: int) -> HitResult:
        """
        Bestämmer träffområdet baserat på vapentyp, attacknivå och ett slumpmässigt värde.
        
        Args:
            weapon_type (str): Vapentypen som sträng.
            attack_level (str): Attacknivån som sträng.
            roll (int): Det rullade värdet (exempelvis mellan 1 och 100).
        
        Returns:
            HitResult: Ett objekt som beskriver träffområdet och eventuella sub-områden.
        
        Raises:
            NotImplementedError: Om metoden inte är implementerad.
        """
        # TODO: Implementera huvudlogiken för att bestämma träffområdet
        raise NotImplementedError("get_hit_location() måste implementeras")
    
    def calculate_damage(self, hit_result: HitResult, damage_value: int) -> Tuple[str, List[str]]:
        """
        Beräknar skada och tillhörande effekter baserat på ett träffresultat och angivet skadevärde.
        
        Args:
            hit_result (HitResult): Resultatet från get_hit_location.
            damage_value (int): Det grundläggande skadevärdet.
        
        Returns:
            Tuple[str, List[str]]: En tuple bestående av en skadebeskrivning (str) 
            samt en lista med skadeffekter (List[str]).
        
        Raises:
            NotImplementedError: Om metoden inte är implementerad.
        """
        # TODO: Implementera beräkningen av skada
        raise NotImplementedError("calculate_damage() måste implementeras")
        
    def process_attack(
        self,
        weapon_type: str,
        attack_level: Optional[str],
        damage_value: int,
        location_override: Optional[str] = None,
        is_mounted: bool = False,
        is_quadruped: bool = False,
        direction: Optional[str] = None
    ) -> HitResult:
        """
        Bearbetar en attack genom att bestämma träffområdet, beräkna skada och returnera ett HitResult.
        
        Args:
            weapon_type (str): Vapentypen.
            attack_level (Optional[str]): Attacknivån (används om inget override ges).
            damage_value (int): Det grundläggande skadevärdet.
            location_override (Optional[str]): Angivet träffområde att använda direkt.
            is_mounted (bool): Om attacken sker med rytter.
            is_quadruped (bool): Om motståndaren är ett fyrbent djur.
            direction (Optional[str]): Eventuell riktning.
        
        Returns:
            HitResult: Resultatet av attacken.
        
        Raises:
            Exception: Om någon del av attackprocessen misslyckas.
        """
        # Slumpa ett värde för att bestämma träffområdet
        dice_roll: int = random.randint(1, 100)
        logging.info(f"Processerar attack med roll: {dice_roll}")
        
        # Hämta träffområdet
        hit: HitResult = self.get_hit_location(weapon_type, attack_level, dice_roll)
        
        # Beräkna skada och effekter
        damage_description, effects = self.calculate_damage(hit, damage_value)
        
        # Uppdatera damage_effects med de beräknade effekterna
        hit.damage_effects = effects
        
        # (Valfritt: damage_description kan läggas till i HitResult om så önskas)
        return hit
