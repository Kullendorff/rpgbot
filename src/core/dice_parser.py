from typing import Tuple

def parse_dice_string(dice_string: str) -> Tuple[int, int, int]:
    """
    Tolkar en tärningssträng med eventuell modifierare.
    
    Exempel:
      "3d6+2" returnerar (3, 6, 2)
      "4d8-1" returnerar (4, 8, -1)
      "2d10"   returnerar (2, 10, 0)
    
    Args:
        dice_string (str): Tärningssträngen att parsa.
    
    Returns:
        Tuple[int, int, int]: En tuple med antal tärningar, antal sidor och modifierare.
    
    Raises:
        ValueError: Om tärningssträngen inte kan parsas korrekt.
    """
    # Leta efter '+' eller '-' för att identifiera modifieraren
    modifier: int = 0
    if '+' in dice_string:
        dice_part, mod_part = dice_string.split('+')
        modifier = int(mod_part)
    elif '-' in dice_string:
        dice_part, mod_part = dice_string.split('-')
        modifier = -int(mod_part)
    else:
        dice_part = dice_string

    # Tolka tärningsdelen i formatet NdX
    num_dice, sides = map(int, dice_part.lower().split('d'))
    return num_dice, sides, modifier