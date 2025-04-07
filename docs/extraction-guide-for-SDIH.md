# Guide för att extrahera "Skjut dom i huvudet"-funktionalitet

Denna guide hjälper dig att extrahera "Skjut dom i huvudet"-funktionaliteten från EON Diceroller-boten och skapa en fristående bot med endast denna funktionalitet.

## 1. Förberedelser

Klona GitHub-repot och navigera till projektkatalogen:

```bash
git clone https://github.com/kullendorff/rpgbot.git
cd rpgbot
```

## 2. Filstruktur

Skapa en ny katalogstruktur för din fristående "Skjut dom i huvudet"-bot:

```bash
mkdir -p sdih-bot/data/sdih_decks
cd sdih-bot
```

## 3. Extrahera koden

Kopiera följande filer från originalkoden:

### 3.1 Skapa bot.py
Skapa huvudfilen `bot.py` med följande:

```python
import discord
from discord.ext import commands
import asyncio
import os
import random
import json
from dotenv import load_dotenv

# Importera våra moduler
from commands import register_commands
from color_handler import ColorHandler
from roll_tracker import RollTracker

# Konfigurera Discord-bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Skapa hjälpklasser
color_handler = ColorHandler()
roll_tracker = RollTracker()

@bot.event
async def on_ready():
    print(f"{bot.user.name} är redo att skjuta zombier i huvudet!")
    print(f"Bot ID: {bot.user.id}")
    print("------")

# Registrera alla kommandon
register_commands(bot, roll_tracker, color_handler)

# Starta boten med token från .env
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

if not TOKEN:
    raise ValueError("DISCORD_TOKEN saknas i .env-filen")

bot.run(TOKEN)
```

### 3.2 Kopiera roll_tracker.py

Skapa en förenklad version av `roll_tracker.py`:

```python
import sqlite3
import os
import datetime
from typing import List, Optional, Dict, Any, Union

class RollTracker:
    """Enkel klass för att logga tärningsslag till SQLite."""
    
    def __init__(self, db_path: str = "data/roll_stats.db"):
        """Initialisera RollTracker med databasanslutning."""
        self.db_path = db_path
        
        # Skapa katalogen om den inte finns
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # Initiera databasen
        self._init_db()
    
    def _init_db(self):
        """Skapa databastabellen om den inte finns."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS roll_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            user_id TEXT,
            user_name TEXT,
            command_type TEXT,
            num_dice INTEGER,
            sides INTEGER,
            roll_values TEXT,
            modifier INTEGER,
            target INTEGER,
            success INTEGER
        )
        ''')
        
        conn.commit()
        conn.close()
    
    def log_roll(self, user_id: str, user_name: str, command_type: str, 
                num_dice: int, sides: int, roll_values: List[int], 
                modifier: int = 0, target: Optional[int] = None,
                success: Optional[bool] = None) -> None:
        """
        Logga ett tärningsslag till databasen.
        
        Args:
            user_id: Discord användar-ID.
            user_name: Användarnamn.
            command_type: Typ av kommando (t.ex. 'rull', 'skada').
            num_dice: Antal tärningar.
            sides: Antal sidor på tärningarna.
            roll_values: Lista med tärningsresultat.
            modifier: Modifierare som läggs till (default 0).
            target: Målvärde att slå mot (kan vara None).
            success: Om slaget var lyckat (kan vara None).
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(
                '''
                INSERT INTO roll_logs (
                    timestamp, user_id, user_name, command_type, num_dice,
                    sides, roll_values, modifier, target, success
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''',
                (
                    datetime.datetime.now().isoformat(),
                    user_id,
                    user_name,
                    command_type,
                    num_dice,
                    sides,
                    str(roll_values),
                    modifier,
                    target,
                    1 if success == True else (0 if success == False else None)
                )
            )
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Error logging roll: {e}")

    def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """
        Hämta statistik för en specifik användare.
        
        Args:
            user_id: Discord användar-ID.
            
        Returns:
            Statistikordlista med användarens tärningsslagsdata.
        """
        stats = {
            "total_rolls": 0,
            "commands": {},
            "naila_count": 0,
            "fumble_count": 0,
            "avg_roll": 0,
            "success_rate": 0
        }
        
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Hämta total antal tärningsslag
            cursor.execute(
                "SELECT COUNT(*) as count FROM roll_logs WHERE user_id = ?",
                (user_id,)
            )
            result = cursor.fetchone()
            stats["total_rolls"] = result["count"] if result else 0
            
            # Räkna användning av olika kommandon
            cursor.execute(
                "SELECT command_type, COUNT(*) as count FROM roll_logs WHERE user_id = ? GROUP BY command_type",
                (user_id,)
            )
            for row in cursor.fetchall():
                stats["commands"][row["command_type"]] = row["count"]
            
            # Räkna Naila och Fucka upp
            cursor.execute(
                "SELECT COUNT(*) as count FROM roll_logs WHERE user_id = ? AND command_type IN ('rull', 'fördel', 'nackdel') AND roll_values LIKE '%20%'",
                (user_id,)
            )
            stats["naila_count"] = cursor.fetchone()["count"]
            
            cursor.execute(
                "SELECT COUNT(*) as count FROM roll_logs WHERE user_id = ? AND command_type IN ('rull', 'fördel', 'nackdel') AND roll_values LIKE '%1%'",
                (user_id,)
            )
            stats["fumble_count"] = cursor.fetchone()["count"]
            
            # Beräkna genomsnittligt tärningsslag för d20-rullningar
            cursor.execute(
                "SELECT roll_values FROM roll_logs WHERE user_id = ? AND sides = 20 AND command_type = 'rull'",
                (user_id,)
            )
            d20_rolls = []
            for row in cursor.fetchall():
                try:
                    values = eval(row["roll_values"])
                    if isinstance(values, list):
                        d20_rolls.extend(values)
                    else:
                        d20_rolls.append(values)
                except:
                    pass
            
            stats["avg_roll"] = sum(d20_rolls) / len(d20_rolls) if d20_rolls else 0
            
            # Beräkna framgångsfrekvens för slag med målvärden
            cursor.execute(
                "SELECT COUNT(*) as total, SUM(success) as successes FROM roll_logs WHERE user_id = ? AND target IS NOT NULL AND success IS NOT NULL",
                (user_id,)
            )
            result = cursor.fetchone()
            if result and result["total"] > 0:
                stats["success_rate"] = (result["successes"] / result["total"]) * 100
            
            conn.close()
            
        except Exception as e:
            print(f"Error getting user stats: {e}")
        
        return stats
```

### 3.3 Skapa color_handler.py

```python
import discord
import random

class ColorHandler:
    """Hanterar färger för användare i Discord embeds."""
    
    def __init__(self):
        """Initialisera ColorHandler med färgkatalog."""
        self.user_colors = {}
        self.default_color = discord.Color.blue()
    
    def get_user_color(self, user_id: int) -> discord.Color:
        """
        Hämta en användares färg, eller generera en ny om ingen finns.
        
        Args:
            user_id: Discord användar-ID.
            
        Returns:
            Discord.Color: Användarens färg för embeds.
        """
        if user_id not in self.user_colors:
            # Generera en slumpmässig färg för nya användare
            r = random.randint(0, 255)
            g = random.randint(0, 255)
            b = random.randint(0, 255)
            self.user_colors[user_id] = discord.Color.from_rgb(r, g, b)
        
        return self.user_colors[user_id]
    
    def set_user_color(self, user_id: int, color: discord.Color) -> None:
        """
        Sätt en användares färg.
        
        Args:
            user_id: Discord användar-ID.
            color: Färgen att sätta.
        """
        self.user_colors[user_id] = color
```

### 3.4 Kopiera dice_functions.py

Kopiera filen `src/skjutdomihuvudet/dice_functions.py` direkt och spara som `dice_functions.py` i din nya bot-katalog.

### 3.5 Kopiera commands.py

Kopiera filen `src/skjutdomihuvudet/commands.py` direkt och spara som `commands.py` i din nya bot-katalog. Ändra följande rad i början av filen:

Från:
```python
from .dice_functions import (
    roll_d20, roll_d20_advantage, roll_d20_disadvantage, 
    roll_damage, roll_hit_zone, 
    parse_initiative_args, roll_initiative,
    InfectionDeck, WEAPON_DAMAGE, 
    get_naila_effect, get_fucka_upp_effect,
    SplatterPointManager
)
```

Till:
```python
from dice_functions import (
    roll_d20, roll_d20_advantage, roll_d20_disadvantage, 
    roll_damage, roll_hit_zone, 
    parse_initiative_args, roll_initiative,
    InfectionDeck, WEAPON_DAMAGE, 
    get_naila_effect, get_fucka_upp_effect,
    SplatterPointManager
)
```

### 3.6 Skapa requirements.txt

```
discord.py>=2.0.0
python-dotenv==1.0.0
```

### 3.7 Skapa .env-fil

```
DISCORD_TOKEN=din_discord_token_här
```

## 4. Anpassa och kör

1. Redigera `.env` och lägg till din Discord bot token.
2. Starta boten med:

```bash
python bot.py
```

## 5. Tillgängliga kommandon

Din bot har nu följande kommandon:

- **Grundläggande tärningsslagning**:
  - `!rull [+modifikation]` - Slå en D20 med modifikation
  - `!fördel [+modifikation]` - Slå med fördel (två D20, ta högsta)
  - `!nackdel [+modifikation]` - Slå med nackdel (två D20, ta lägsta)

- **Skada och träffzoner**:
  - `!skada [vapen/tärningsformel]` - Slå för skada med vapen eller anpassad formel
  - `!träffzon` - Slå för att avgöra vilken kroppsdel som träffas

- **Smittokort**:
  - `!smitta dra [@användare]` - Dra ett smittokort
  - `!smitta reset [@användare]` - Återställ smittokortleken
  - `!smitta status [@användare]` - Visa status för smittokortleken
  - `!amputera [kroppsdel]` - Amputera en smittad kroppsdel

- **Övriga**:
  - `!initiativ [namn] [värde] [namn2] [värde2] ...` - Slå initiativ för deltagare
  - `!splatter reset [antal]` - Återställ splatterpoäng
  - `!splatter use [beskrivning]` - Använd en splatterpoäng
  - `!splatter status` - Visa kvarvarande splatterpoäng
  - `!sdihelp` - Visa hjälp för Skjut dom i huvudet-kommandon

## 6. Anpassning

Du kan enkelt anpassa boten genom att:

1. Ändra vapenskador i `dice_functions.py` i `WEAPON_DAMAGE`-ordboken
2. Lägga till fler Naila/Fucka upp-effekter i funktionerna `get_naila_effect()` och `get_fucka_upp_effect()`
3. Anpassa smittokorten i `InfectionDeck`-klassen
4. Ändra träffzonerna i `HIT_ZONES`-ordboken

## 7. Felsökning

Om du har problem:

1. Kontrollera att din `.env`-fil har korrekt Discord token
2. Verifiera att alla filer är i rätt katalog och struktur
3. Se till att bot-användaren har rätt behörigheter i din Discord-server
4. Kontrollera att du har installerat alla nödvändiga paket
5. Om datafiler saknas, skapa katalogen `data/sdih_decks`

Lycka till med din nya "Skjut dom i huvudet"-bot!
