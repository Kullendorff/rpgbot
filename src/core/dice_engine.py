import random
from typing import Tuple, List
from .constants import MAX_UNLIMITED_ROLLS, DEFAULT_SIMULATION_TRIALS

def unlimited_d6s(num_dice: int, modifier: int = 0) -> Tuple[List[int], int, List[int]]:
    """
    Slår X stycken 6-sidiga tärningar enligt 'obegränsat'-regeln:
      - Varje 6a räknas inte med i summan men genererar +2 nya tärningar.
      - Upprepa tills inga nya tärningar finns kvar.
    
    Args:
        num_dice (int): Antal tärningar att slå initialt.
        modifier (int): Eventuell modifierare att lägga på slutresultatet.
    
    Returns:
        Tuple[List[int], int, List[int]]:
            - all_rolls: Lista med alla rullade tärningar (inklusive expansionskast).
            - final_total: Slutgiltig summa (exklusive 6:or) plus modifierare.
            - initial_rolls: Lista med resultat från första kastomgången.
    """
    # Första kastomgången
    initial_rolls: List[int] = [random.randint(1, 6) for _ in range(num_dice)]
    all_rolls: List[int] = initial_rolls[:]  # Kopiera för historik
    final_total: int = sum(r for r in initial_rolls if r != 6)

    # Beräkna antal extra tärningar för varje 6a
    extra_dice: int = sum(2 for r in initial_rolls if r == 6)

    # Sätt en gräns för hur många extra tärningar som kan slås
    max_rolls: int = MAX_UNLIMITED_ROLLS
    roll_count: int = 0
    
    # Utför expansionskast
    while extra_dice > 0 and roll_count < max_rolls:
        roll_count += 1
        roll: int = random.randint(1, 6)
        all_rolls.append(roll)
        extra_dice -= 1
        if roll == 6:
            extra_dice += 2
        else:
            final_total += roll
    
    # Logga om vi nådde maxgränsen (detta är extremt osannolikt)
    if roll_count >= max_rolls:
        print(f"Varning: Nådde maxgränsen på {max_rolls} slag för obegränsade T6-slag")

    final_total += modifier
    return all_rolls, final_total, initial_rolls

def simulate_unlimited_dice(num_dice: int, modifier: int, target: int, num_trials: int = DEFAULT_SIMULATION_TRIALS) -> float:
    """
    Simulerar obegränsade T6-slag och beräknar sannolikheten att lyckas.
    
    Args:
        num_dice (int): Antal tärningar.
        modifier (int): Modifierare till slaget.
        target (int): Målvärde att jämföra med.
        num_trials (int): Antal simuleringar att köra.
        
    Returns:
        float: Procentuell chans att lyckas.
    """
    successes = 0
    
    for _ in range(num_trials):
        # Använd den befintliga funktionen för att simulera ett slag
        _, total, _ = unlimited_d6s(num_dice, modifier)
        
        # Kontrollera om det lyckades
        if total <= target:
            successes += 1
            
    # Beräkna och returnera procentuell framgångsfrekvens
    return (successes / num_trials) * 100