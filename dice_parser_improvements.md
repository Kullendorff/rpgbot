# EON Diceroller - Förbättring av Dice Parser

## Mål
Förbättra `src/core/dice_parser.py` från en naiv implementation till en robust, vältestad parser som kan hantera varierat användarinput utan att bryta boten.

## Nuvarande problem med dice_parser.py

### Begränsningar i nuvarande kod
```python
def parse_dice_string(dice_string: str) -> Tuple[int, int, int]:
    # Nuvarande implementation är naiv och begränsad:
    # - Kräver exakt format: "3d6+2" 
    # - Fungerar inte med: "3D6 + 2", " d6", "D20"
    # - Ingen validering av input
    # - Inga säkerhetsgränser
    # - Returtyp är oklar tuple istället för struktur
```

### Verkliga användarproblem
- Användare skriver `3D6 + 2` → Bot kraschar
- Användare skriver `d6` → Parsern förstår inte
- Ingen skydd mot `99999d6` → DoS möjligt
- Felmeddelanden är generiska och hjälper inte

## Målarkitektur

### 1. Ny DiceSpec-datastruktur
```python
@dataclass
class DiceSpec:
    count: int              # Antal tärningar
    sides: int              # Antal sidor per tärning  
    modifier: int = 0       # +/- modifierare
    exploding: bool = False # ! för exploderande tärningar
    reroll_leq: Optional[int] = None  # r<=N för omslag vid låga värden
```

### 2. Robusta undantag
```python
class InvalidDiceFormat(ValueError):
    """Kastas när dice notation är felaktig"""
    pass

class DiceLimitsError(ValueError):
    """Kastas när tärningsgränser överskrids"""
    pass
```

### 3. Flexibel regex-parser
```python
# Stödjer: "3d6+2", "3D6 + 2", "d6", "4D10-1", "2d6!", "2d6 r<=2"
DICE_RE = re.compile(
    r'^\s*(?:(\d+)\s*)?[dD](\d+)\s*'     # count (optional) + 'd' + sides
    r'(?:(\s*[+-]\s*\d+))?'              # optional +/- modifier  
    r'(\s*!{1})?'                        # optional exploding '!'
    r'(?:\s*r<=\s*(\d+))?\s*$'           # optional reroll <=N
)
```

## Implementationsplan

### Fas 1: Skapa nya klasser och undantag
**Fil:** `src/core/dice_parser.py`

1. **Lägg till imports och datastrukturer**
   ```python
   import re
   from dataclasses import dataclass
   from typing import Optional
   ```

2. **Definiera DiceSpec och undantag**
   ```python
   @dataclass
   class DiceSpec:
       count: int
       sides: int  
       modifier: int = 0
       exploding: bool = False
       reroll_leq: Optional[int] = None
   
   class InvalidDiceFormat(ValueError):
       pass
       
   class DiceLimitsError(ValueError):
       pass
   ```

3. **Säkerhetskonstanter** (flytta från constants.py om behövs)
   ```python
   MAX_DICE = 100
   MAX_SIDES = 1000
   ```

### Fas 2: Implementera robust parser
**Fil:** `src/core/dice_parser.py`

1. **Definiera regex-pattern**
   ```python
   DICE_RE = re.compile(
       r'^\s*(?:(\d+)\s*)?[dD](\d+)\s*'
       r'(?:(\s*[+-]\s*\d+))?'  
       r'(\s*!{1})?'
       r'(?:\s*r<=\s*(\d+))?\s*$'
   )
   ```

2. **Ny parse_dice_string funktion**
   ```python
   def parse_dice_string(s: str) -> DiceSpec:
       """
       Tolkar dice notation och returnerar DiceSpec.
       
       Exempel:
         "3d6+2" → DiceSpec(count=3, sides=6, modifier=2)
         "d6" → DiceSpec(count=1, sides=6, modifier=0)
         "4D10-1" → DiceSpec(count=4, sides=10, modifier=-1)
         "2d6!" → DiceSpec(count=2, sides=6, exploding=True)
         "2d6 r<=2" → DiceSpec(count=2, sides=6, reroll_leq=2)
       
       Raises:
         InvalidDiceFormat: För felaktig notation
         DiceLimitsError: För värden utanför säkra gränser
       """
   ```

3. **Validering**
   ```python
   def validate_spec(spec: DiceSpec):
       if spec.count < 1:
           raise DiceLimitsError("Minst 1 tärning krävs.")
       if spec.count > MAX_DICE:
           raise DiceLimitsError(f"För många tärningar (max {MAX_DICE}).")
       if spec.sides < 2 or spec.sides > MAX_SIDES:
           raise DiceLimitsError(f"Tärningssidor måste vara mellan 2 och {MAX_SIDES}.")
   ```

### Fas 3: Bakåtkompatibilitet
**Fil:** `src/core/dice_parser.py`

1. **Behåll gamla funktionen temporärt**
   ```python
   def parse_dice_string_legacy(dice_string: str) -> Tuple[int, int, int]:
       """Gammal implementation för bakåtkompatibilitet"""
       spec = parse_dice_string(dice_string)
       return (spec.count, spec.sides, spec.modifier)
   ```

2. **Uppdatera imports gradvis** i andra moduler

### Fas 4: Uppdatera commands
**Moduler att uppdatera:**
- `src/commands/dice_commands.py`
- `src/commands/admin_commands.py` (secret rolls)

1. **Ändra från tuple-unpacking till DiceSpec**
   ```python
   # GAMLA:
   num_dice, sides, modifier = parse_dice_string(dice)
   
   # NYA: 
   spec = parse_dice_string(dice)
   num_dice, sides, modifier = spec.count, spec.sides, spec.modifier
   ```

2. **Förbättrade felmeddelanden**
   ```python
   try:
       spec = parse_dice_string(dice)
   except InvalidDiceFormat as e:
       await ctx.send(f"❌ Felaktigt format: {e}")
       return
   except DiceLimitsError as e:
       await ctx.send(f"⚠️ Gränser överskrids: {e}")
       return
   ```

## Testplan

### Enhetstester
**Skapa:** `tests/test_dice_parser.py`

```python
def test_basic_parsing():
    spec = parse_dice_string("3d6+2")
    assert spec.count == 3
    assert spec.sides == 6
    assert spec.modifier == 2

def test_flexible_input():
    # Bör alla fungera:
    specs = [
        parse_dice_string("3d6+2"),
        parse_dice_string("3D6 + 2"), 
        parse_dice_string(" d6 "),
        parse_dice_string("4D10-1")
    ]

def test_validation():
    with pytest.raises(DiceLimitsError):
        parse_dice_string("10000d6")
```

### Manuella tester
1. **Testa alla nuvarande kommandon** efter varje fas
2. **Testa edge cases** som användare faktiskt skriver
3. **Verifiera felmeddelanden** är hjälpsamma

## Leveransordning

### Vecka 1: Grundstruktur
- [ ] Skapa DiceSpec och undantag
- [ ] Implementera ny parse_dice_string
- [ ] Behåll bakåtkompatibilitet
- [ ] Testa att inget bryts

### Vecka 2: Integration  
- [ ] Uppdatera dice_commands.py
- [ ] Uppdatera admin_commands.py
- [ ] Förbättrade felmeddelanden
- [ ] Ta bort gamla funktionen

### Vecka 3: Polish & tester
- [ ] Enhetstester för all parsing
- [ ] Dokumentation
- [ ] Performance-test med stora värden
- [ ] Validera med riktiga användare

## Säkerhet och begränsningar

### DoS-skydd
```python
MAX_DICE = 100          # Förhindra memory-explosion
MAX_SIDES = 1000        # Rimliga gränser för rollspel
MAX_UNLIMITED_ROLLS = 1000  # För unlimited_d6s safety
```

### Input-sanitering
- Strippa whitespace automatiskt
- Hantera unicode-tecken säkert
- Validera numeriska värden innan konvertering

### Felhantering
- Tydliga felmeddelanden på svenska
- Exempel på korrekt format i fel
- Logging av ofta felaktiga inputs för analys

## Framtida fördelar

Efter denna refactoring:
- **Enklare att lägga till nya dice mechanics** 
- **Bättre användarupplevelse** med flexibelt input
- **Testbar kod** som kan valideras automatiskt
- **Säkrare bot** som inte kan DOS:as av användare
- **Klarare kodstruktur** för framtida utvecklare

---

**VIKTIGT:** Genomför en fas i taget och testa grundligt innan nästa steg. Bakåtkompatibilitet är kritisk - inget befintligt kommando får sluta fungera under övergången.