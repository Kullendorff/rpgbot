# EON Diceroller Bot - Refactoring Plan

## Mål
Dela upp den monolitiska `main.py` (1300+ rader) i modulära komponenter utan att förlora funktionalitet eller riskera att bryta boten.

## Nuvarande struktur
```
C:\Diceroller\
├── main.py                 # 1300+ rader - ALLT finns här
├── color_handler.py        # Redan modulär ✓
├── roll_tracker.py         # Redan modulär ✓
├── combat_manager.py       # Redan modulär ✓
├── damage_tables.py        # Redan modulär ✓
├── hit_tables.py          # Redan modulär ✓
├── fumble_tables.py       # Redan modulär ✓
├── stats_commands.py      # Redan modulär ✓
└── skjutdomihuvudet/      # Redan modulär ✓
```

## Målstruktur
```
C:\Diceroller\
├── src/
│   ├── bot/
│   │   ├── __init__.py
│   │   ├── main.py              # Bara bot setup och koordination
│   │   └── events.py            # Bot events (@bot.event)
│   ├── commands/
│   │   ├── __init__.py
│   │   ├── dice_commands.py     # !roll, !ex, !count, !chance
│   │   ├── combat_commands.py   # !hugg, !stick, !kross, !fummel
│   │   ├── knowledge_commands.py # !ask, !sök, !allt
│   │   ├── admin_commands.py    # !secret, !startsession, !endsession
│   │   └── utility_commands.py  # !dicehelp, !regel, !hój
│   ├── core/
│   │   ├── __init__.py
│   │   ├── dice_parser.py       # parse_dice_string + validering
│   │   ├── dice_engine.py       # unlimited_d6s + simuleringar
│   │   ├── knowledge_base.py    # Pinecone + Claude integration
│   │   └── constants.py         # Alla konstanter
│   └── utils/
│       ├── __init__.py
│       ├── text_utils.py        # clean_unicode, split_message
│       └── validation.py       # Input validering
├── [befintliga moduler behålls]
└── [backup av original main.py]
```

## Fas 1: Säkerhet och förberedelse

### 1.1 Backup
```bash
cd C:\Diceroller
mkdir backup_original
copy main.py backup_original\main.py.original
```

### 1.2 Skapa katalogstruktur
```bash
mkdir src\bot
mkdir src\commands  
mkdir src\core
mkdir src\utils
```

### 1.3 Skapa __init__.py filer
```python
# Tomma __init__.py filer i alla nya kataloger
```

## Fas 2: Extrahera low-risk moduler (0% risk att bryta något)

### 2.1 Flytta konstanter
```python
# src/core/constants.py
UMNATAK_ID = "680064176227352610"
MAX_DICE = 200
MAX_SIDES = 1000

# Flytta alla UMNATAK_SUCCESS_COMMENTS relaterade funktioner
```

### 2.2 Flytta hjälpfunktioner
```python
# src/utils/text_utils.py
def clean_unicode(text)
def split_message(message: str, max_length: int = 2000)
def count_tokens(text: str) -> int
```

### 2.3 Flytta tärningslogik
```python
# src/core/dice_parser.py
def parse_dice_string(dice_string: str) -> Tuple[int, int, int]

# src/core/dice_engine.py  
def unlimited_d6s(num_dice: int, modifier: int = 0)
def simulate_unlimited_dice(num_dice: int, modifier: int, target: int, num_trials: int = 10000)
```

### 2.4 Uppdatera imports i main.py
```python
from src.core.constants import UMNATAK_ID, MAX_DICE, MAX_SIDES
from src.utils.text_utils import clean_unicode, split_message, count_tokens
from src.core.dice_parser import parse_dice_string
from src.core.dice_engine import unlimited_d6s, simulate_unlimited_dice
```

**TEST**: Kör boten efter varje flytt och verifiera grundfunktionalitet.

## Fas 3: Extrahera kunskapsbas (medium risk)

### 3.1 Skapa knowledge_base.py
```python
# src/core/knowledge_base.py
class KnowledgeBase:
    def __init__(self):
        # Flytta alla globala kunskapsbas-variabler hit
        self.pc = None
        self.embedding_model = None  
        self.claude_client = None
    
    def initialize_knowledge_base(self) -> bool
    def query_knowledge_base(self, query: str, top_k: int = 5)
    def generate_response(self, query: str, context: str) -> str
```

### 3.2 Uppdatera main.py
```python
from src.core.knowledge_base import KnowledgeBase

# Ersätt globala variabler med:
knowledge_base = KnowledgeBase()

# I on_ready():
knowledge_base.initialize_knowledge_base()
```

**TEST**: Verifiera !ask, !sök, !allt kommandon fungerar.

## Fas 4: Extrahera kommandon (high risk men high reward)

### 4.1 Skapa command moduler
```python
# src/commands/dice_commands.py
def register_dice_commands(bot, roll_tracker, color_handler, knowledge_base):
    @bot.command(name='roll')
    async def roll_command(ctx, *args):
        # Flytta exakt nuvarande roll_command hit
        
    @bot.command(name='ex')
    async def ex_command(ctx, *args):
        # Flytta exakt nuvarande ex_command hit
        
    # osv för alla tärningskommandon
```

### 4.2 Registrera kommandon i main.py
```python
from src.commands.dice_commands import register_dice_commands
from src.commands.knowledge_commands import register_knowledge_commands
# osv

# I on_ready() eller efter bot setup:
register_dice_commands(bot, roll_tracker, color_handler, knowledge_base)
register_knowledge_commands(bot, knowledge_base, color_handler)
```

### 4.3 Ny main.py struktur
```python
# src/bot/main.py - drastiskt förminskat
import discord
from discord.ext import commands

# Imports av alla register-funktioner
from src.commands.dice_commands import register_dice_commands
# ... etc

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Globala objekt
color_handler = ColorHandler()
roll_tracker = RollTracker()
combat_manager = CombatManager()
knowledge_base = KnowledgeBase()

@bot.event
async def on_ready():
    print(f"{bot.user} has connected to Discord!")
    
    # Initiera system
    knowledge_base.initialize_knowledge_base()
    load_umnatak_comments()
    
    # Registrera alla kommandon
    register_dice_commands(bot, roll_tracker, color_handler, knowledge_base)
    register_knowledge_commands(bot, knowledge_base, color_handler)
    register_combat_commands(bot, combat_manager, color_handler)
    register_admin_commands(bot, roll_tracker, color_handler, knowledge_base)
    register_utility_commands(bot, color_handler)

if __name__ == "__main__":
    main()
```

## Test-strategi

Efter varje fas:

1. **Kör boten lokalt**
2. **Testa samtliga huvudkommandon**:
   - `!roll 3d6+2`
   - `!ex 4d6 18`
   - `!ask Hur fungerar magi?`
   - `!hugg normal 12`
   - `!stats`
3. **Kontrollera error logs** för import-fel
4. **Testa edge cases** som användare brukar göra

## Roll-back plan

Vid varje fas: om något går fel, återställ från backup och analysera problemet innan nästa försök.

```bash
# Om något går fel:
copy backup_original\main.py.original main.py
```

## Fördelar efter refactoring

- **Maintainability**: Nya features läggs till i rätt modul
- **Testability**: Varje modul kan testas isolerat  
- **Debugging**: Buggar isoleras till specifika moduler
- **Collaboration**: Andra kan jobba på specifika delar
- **Performance**: Lättare att optimera enskilda komponenter

## Viktiga principer

1. **Aldrig ändra logik under refactoring** - bara flytta kod
2. **Testa efter varje steg** - små iterationer
3. **Behåll all funktionalitet** - inget får förloras
4. **Dokumentera ändringar** - så vi vet vad som gjorts
5. **Backward compatibility** - gamla imports ska fungera tillfälligt

## Färdig indikator

Refactoring är klar när:
- [ ] main.py är under 200 rader
- [ ] Alla kommandon fungerar identiskt  
- [ ] Alla tester passerar
- [ ] Kod är uppdelad enligt målstrukturen
- [ ] Alla imports är rena och tydliga