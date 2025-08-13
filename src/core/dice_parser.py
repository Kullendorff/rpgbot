import re
from dataclasses import dataclass
from typing import Optional
from .constants import MAX_DICE, MAX_SIDES

@dataclass
class DiceSpec:
    """
    Datastruktur som representerar en komplett tärningsspecifikation.
    
    Attributes:
        count: Antal tärningar att slå
        sides: Antal sidor per tärning  
        modifier: +/- modifierare till slutresultatet
        exploding: Om tärningarna ska "explodera" (generera extra kast vid max värde)
        reroll_leq: Slå om tärningar som visar <= detta värde
    """
    count: int
    sides: int  
    modifier: int = 0
    exploding: bool = False
    reroll_leq: Optional[int] = None

    def __str__(self) -> str:
        """Snygg strängrepresentation av dice spec."""
        base = f"{self.count}d{self.sides}"
        if self.modifier > 0:
            base += f"+{self.modifier}"
        elif self.modifier < 0:
            base += str(self.modifier)
        if self.exploding:
            base += "!"
        if self.reroll_leq is not None:
            base += f" r<={self.reroll_leq}"
        return base


class InvalidDiceFormat(ValueError):
    """Kastas när dice notation är felaktig eller kan inte parsas."""
    pass


class DiceLimitsError(ValueError):
    """Kastas när tärningsgränser överskrids (för många tärningar eller sidor)."""
    pass


# Flexibel regex som hanterar olika format och whitespace
DICE_RE = re.compile(
    r'^\s*'                          # Valfri whitespace i början
    r'(?:(\d+)\s*)?'                 # Antal tärningar (valfritt, default 1)
    r'[dD]'                          # 'd' eller 'D' 
    r'(\d+)'                         # Antal sidor (obligatoriskt)
    r'\s*'                           # Valfri whitespace
    r'(?:(\s*[+-]\s*\d+))?'          # Valfri modifierare med whitespace
    r'(\s*!)?'                       # Valfri exploding marker  
    r'(?:\s*r<=\s*(\d+))?'           # Valfri reroll condition  
    r'\s*$',                         # Valfri whitespace i slutet
    re.IGNORECASE
)


def parse_dice_string(dice_string: str) -> DiceSpec:
    """
    Tolkar dice notation och returnerar en DiceSpec.
    
    Stödjer flexibla format:
      "3d6+2"     → DiceSpec(count=3, sides=6, modifier=2)
      "3D6 + 2"   → DiceSpec(count=3, sides=6, modifier=2) 
      " d6 "      → DiceSpec(count=1, sides=6, modifier=0)
      "4D10-1"    → DiceSpec(count=4, sides=10, modifier=-1)
      "2d6!"      → DiceSpec(count=2, sides=6, exploding=True)
      "2d6 r<=2"  → DiceSpec(count=2, sides=6, reroll_leq=2)
      
    Args:
        dice_string: Tärningssträngen att parsa
        
    Returns:
        DiceSpec: Parsad tärningsspecifikation
        
    Raises:
        InvalidDiceFormat: Om formatet är felaktigt
        DiceLimitsError: Om värdena är utanför säkra gränser
    """
    if not isinstance(dice_string, str):
        raise InvalidDiceFormat("Tärningsspecifikation måste vara en sträng")
    
    # Rensa bort extra whitespace
    clean_input = dice_string.strip()
    if not clean_input:
        raise InvalidDiceFormat("Tom tärningsspecifikation")
    
    # Matcha mot regex
    match = DICE_RE.match(clean_input)
    if not match:
        raise InvalidDiceFormat(
            f"Felaktigt tärningsformat: '{dice_string}'\n"
            f"Exempel på korrekt format: '3d6+2', 'd6', '4D10-1'"
        )
    
    count_str, sides_str, modifier_str, exploding_str, reroll_str = match.groups()
    
    try:
        # Parsa antal tärningar (default 1 om inte angivet)
        count = int(count_str) if count_str else 1
        
        # Parsa antal sidor
        sides = int(sides_str)
        
        # Parsa modifierare (ta bort whitespace och konvertera)
        modifier = 0
        if modifier_str:
            modifier_clean = re.sub(r'\s+', '', modifier_str)
            modifier = int(modifier_clean)
        
        # Parsa exploding
        exploding = bool(exploding_str and exploding_str.strip())
        
        # Parsa reroll condition
        reroll_leq = None
        if reroll_str:
            reroll_leq = int(reroll_str)
            
    except ValueError as e:
        raise InvalidDiceFormat(f"Kunde inte tolka numeriska värden: {e}")
    
    # Skapa specifikation
    spec = DiceSpec(
        count=count,
        sides=sides,
        modifier=modifier,
        exploding=exploding,
        reroll_leq=reroll_leq
    )
    
    # Validera säkerhetsgränser
    _validate_dice_spec(spec)
    
    return spec


def _validate_dice_spec(spec: DiceSpec) -> None:
    """
    Validerar att dice spec är inom säkra gränser.
    
    Args:
        spec: DiceSpec att validera
        
    Raises:
        DiceLimitsError: Om värdena är utanför säkra gränser
    """
    if spec.count < 1:
        raise DiceLimitsError("Minst 1 tärning krävs")
    
    if spec.count > MAX_DICE:
        raise DiceLimitsError(
            f"För många tärningar: {spec.count} (max {MAX_DICE})\n"
            f"Detta skyddar mot minnesöverbelastning"
        )
    
    if spec.sides < 2:
        raise DiceLimitsError("Tärningar måste ha minst 2 sidor")
        
    if spec.sides > MAX_SIDES:
        raise DiceLimitsError(
            f"För många sidor per tärning: {spec.sides} (max {MAX_SIDES})\n"
            f"Detta skyddar mot minnesöverbelastning"
        )
    
    # Validera reroll condition
    if spec.reroll_leq is not None:
        if spec.reroll_leq < 1:
            raise DiceLimitsError("Reroll-värde måste vara minst 1")
        if spec.reroll_leq >= spec.sides:
            raise DiceLimitsError(
                f"Reroll-värde ({spec.reroll_leq}) måste vara mindre än antal sidor ({spec.sides})"
            )


