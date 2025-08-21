# Player Comments System - Implementation Instructions

## 🎯 Projektöversikt

Skapa ett konfigurerbart kommentarsystem som ersätter den hårdkodade Umnatak-funktionaliteten med ett flexibelt system för alla spelare.

**Mål:**
- Gör Umnatak-kommentarer konfigurerbara (on/off)
- Utöka till alla spelare med olika kommentarstilar
- Default: Avstängt för alla användare
- Enkel administration via slash commands

---

## 🏗️ Fas 1: Grundläggande User Settings System

### 1.1 Skapa UserSettingsManager

**Skapa `src/core/user_settings.py`:**

```python
"""
User settings manager for the EON Discord bot.
Handles user preferences like comment settings, themes, etc.
"""

import json
import os
from typing import Dict, Optional, Any
from datetime import datetime

class UserSettingsManager:
    def __init__(self, data_dir: str = "data"):
        """
        Initialize user settings manager.
        
        Args:
            data_dir: Directory to store user settings file
        """
        self.data_dir = data_dir
        self.settings_file = os.path.join(data_dir, "user_settings.json")
        self.settings_cache = {}
        self._ensure_data_dir()
        self._load_settings()
    
    def _ensure_data_dir(self):
        """Ensure data directory exists."""
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
    
    def _load_settings(self):
        """Load settings from file into cache."""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    self.settings_cache = json.load(f)
            else:
                self.settings_cache = {}
        except Exception as e:
            print(f"Error loading user settings: {e}")
            self.settings_cache = {}
    
    def _save_settings(self):
        """Save settings cache to file."""
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings_cache, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving user settings: {e}")
    
    def get_user_settings(self, user_id: str) -> Dict[str, Any]:
        """
        Get user settings with defaults.
        
        Args:
            user_id: Discord user ID as string
            
        Returns:
            Dict with user settings
        """
        default_settings = {
            "comments_enabled": False,  # DEFAULT: Avstängt
            "comment_frequency": 0.3,   # 30% chans
            "comment_style": "umnatak", # Default stil
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat()
        }
        
        if user_id not in self.settings_cache:
            self.settings_cache[user_id] = default_settings.copy()
            self._save_settings()
        
        return self.settings_cache[user_id].copy()
    
    def set_comments_enabled(self, user_id: str, enabled: bool) -> bool:
        """
        Enable/disable comments for user.
        
        Args:
            user_id: Discord user ID
            enabled: True to enable, False to disable
            
        Returns:
            True if successful
        """
        try:
            settings = self.get_user_settings(user_id)
            settings["comments_enabled"] = enabled
            settings["last_updated"] = datetime.now().isoformat()
            
            self.settings_cache[user_id] = settings
            self._save_settings()
            return True
        except Exception as e:
            print(f"Error setting comments enabled for {user_id}: {e}")
            return False
    
    def set_comment_style(self, user_id: str, style: str) -> bool:
        """
        Set comment style for user.
        
        Args:
            user_id: Discord user ID
            style: Comment style ('umnatak', 'encouraging', 'dramatic', 'neutral')
            
        Returns:
            True if successful
        """
        valid_styles = ['umnatak', 'encouraging', 'dramatic', 'neutral']
        if style not in valid_styles:
            return False
        
        try:
            settings = self.get_user_settings(user_id)
            settings["comment_style"] = style
            settings["last_updated"] = datetime.now().isoformat()
            
            self.settings_cache[user_id] = settings
            self._save_settings()
            return True
        except Exception as e:
            print(f"Error setting comment style for {user_id}: {e}")
            return False
    
    def set_comment_frequency(self, user_id: str, frequency: float) -> bool:
        """
        Set comment frequency for user.
        
        Args:
            user_id: Discord user ID
            frequency: Float between 0.1 and 0.5 (10-50%)
            
        Returns:
            True if successful
        """
        if not (0.1 <= frequency <= 0.5):
            return False
        
        try:
            settings = self.get_user_settings(user_id)
            settings["comment_frequency"] = frequency
            settings["last_updated"] = datetime.now().isoformat()
            
            self.settings_cache[user_id] = settings
            self._save_settings()
            return True
        except Exception as e:
            print(f"Error setting comment frequency for {user_id}: {e}")
            return False
```

### 1.2 Skapa Comment Styles System

**Skapa `src/core/comment_styles.py`:**

```python
"""
Comment styles and messages for the EON Discord bot.
"""

import random
from typing import Dict, List, Optional

# Kommentarstilar med olika personligheter
COMMENT_STYLES: Dict[str, Dict[str, List[str]]] = {
    "umnatak": {
        "success": [
            "Äntligen lyckades du med något",
            "Ett mirakel inträffade", 
            "Slutade bra trots förväntningarna",
            "Överraskande kompetent denna gång",
            "Gudarna måste ha känt medlidande"
        ],
        "failure": [
            "Som väntat",
            "Klassiskt",
            "Ingen överraskning där",
            "Precis vad jag förväntade mig",
            "Tradition fortsätter"
        ],
        "critical_success": [
            "Nu har världen vänt upp och ner",
            "Jag måste se om igen",
            "Detta trotsade alla odds",
            "Historiska ögonblick"
        ],
        "fumble": [
            "Naturlag i kraft",
            "Åh, där var du igen",
            "Tillbaka till det normala",
            "Balansen återställd"
        ]
    },
    
    "encouraging": {
        "success": [
            "Fantastiskt slag!",
            "Du är på gång nu!",
            "Vilken skicklighet!",
            "Bra jobbat!",
            "Imponerande!"
        ],
        "failure": [
            "Nästa gång blir bättre!",
            "Bara att försöka igen!",
            "Det händer de bästa!",
            "Fortsätt kämpa!",
            "Du kommer tillbaka starkare!"
        ],
        "critical_success": [
            "OTROLIGT! Vilket slag!",
            "Du är på topp idag!",
            "Mästerligt utfört!",
            "Legendariskt!"
        ],
        "fumble": [
            "Alla gör misstag!",
            "Det här händer även proffsen!",
            "Lär av detta och kom tillbaka!",
            "Fummel bygger karaktär!"
        ]
    },
    
    "dramatic": {
        "success": [
            "ÖDET HAR TALAT!",
            "Ett slag för historieböckerna!",
            "Gudarna ler mot dig!",
            "EPISKT UTFÖRT!",
            "Stjärnorna har anpassat sig!"
        ],
        "failure": [
            "Mörkrets krafter motverkar dig!",
            "Ödet testar din beslutsamhet!",
            "Även hjältar faller ibland!",
            "Kampen fortsätter!",
            "Utmaningen växer!"
        ],
        "critical_success": [
            "GUDARNA SJÄLVA APPLÅDERAR!",
            "ETT MIRAKEL UTFÖRT!",
            "LEGENDEN FÖDS!",
            "KOSMOS SJÄLV FÖRUNDRAS!"
        ],
        "fumble": [
            "KAOS REGERAR!",
            "ÖDET HÅNAR DIG!",
            "MÖRKRETS STUND!",
            "TROLLKONSTEN SVIKER!"
        ]
    },
    
    "neutral": {
        "success": [
            "Lyckad handling",
            "Bra resultat",
            "Framgång noterad",
            "Positivt utfall"
        ],
        "failure": [
            "Misslyckad handling",
            "Negativt resultat", 
            "Försök misslyckades",
            "Icke önskat utfall"
        ],
        "critical_success": [
            "Exceptionellt resultat",
            "Kritisk framgång",
            "Maximalt utfall",
            "Optimal prestation"
        ],
        "fumble": [
            "Kritiskt misslyckande",
            "Fummel registrerat",
            "Negativ komplikation",
            "Olycklig utgång"
        ]
    }
}

class CommentGenerator:
    """Generates contextual comments based on roll results and user preferences."""
    
    def __init__(self):
        self.styles = COMMENT_STYLES
    
    def get_comment(self, user_settings: dict, roll_result: dict) -> Optional[str]:
        """
        Get comment based on user settings and roll result.
        
        Args:
            user_settings: User's comment preferences
            roll_result: Dict with roll information
            
        Returns:
            Comment string or None
        """
        # Check if comments are enabled
        if not user_settings.get("comments_enabled", False):
            return None
        
        # Check frequency
        frequency = user_settings.get("comment_frequency", 0.3)
        if random.random() > frequency:
            return None
        
        # Get comment style
        style = user_settings.get("comment_style", "umnatak")
        if style not in self.styles:
            style = "umnatak"
        
        # Determine comment category based on roll result
        category = self._determine_category(roll_result)
        
        # Get comment from style and category
        comments = self.styles[style].get(category, [])
        if not comments:
            return None
        
        return random.choice(comments)
    
    def _determine_category(self, roll_result: dict) -> str:
        """
        Determine comment category based on roll result.
        
        Args:
            roll_result: Dict with roll information
            
        Returns:
            Category string: 'success', 'failure', 'critical_success', 'fumble'
        """
        # Check for critical results first
        if roll_result.get("is_fumble", False):
            return "fumble"
        elif roll_result.get("is_critical_success", False):
            return "critical_success"
        elif roll_result.get("is_perfect", False):
            return "critical_success"
        
        # Check for success/failure
        success = roll_result.get("success")
        if success is True:
            return "success"
        elif success is False:
            return "failure"
        
        # Default to success for positive results
        return "success"
    
    def get_available_styles(self) -> List[str]:
        """Get list of available comment styles."""
        return list(self.styles.keys())
```

---

## 🎮 Fas 2: Integration med Befintligt System

### 2.1 Uppdatera main.py

**Lägg till i `src/main.py` imports:**

```python
# Lägg till dessa imports
from core.user_settings import UserSettingsManager
from core.comment_styles import CommentGenerator

# I global setup (efter andra globala objekt):
user_settings = UserSettingsManager()
comment_generator = CommentGenerator()
```

### 2.2 Uppdatera Dice Commands

**I alla slash dice commands (`src/commands/slash_dice_commands.py`):**

```python
# ERSÄTT den gamla Umnatak-logiken:

# GAMMAL KOD (ta bort):
# if str(interaction.user.id) == UMNATAK_ID:
#     sarcastic_comment = get_sarcastic_comment_for_umnatak()
#     if sarcastic_comment:
#         embed.add_field(name="🎭", value=sarcastic_comment, inline=False)

# NY KOD (lägg till):
def add_user_comment(embed: discord.Embed, user_id: str, roll_result: dict):
    """Add personalized comment to embed if enabled for user."""
    try:
        # Import global objects
        from main import user_settings, comment_generator
        
        # Get user settings
        settings = user_settings.get_user_settings(str(user_id))
        
        # Get comment
        comment = comment_generator.get_comment(settings, roll_result)
        
        if comment:
            embed.add_field(name="🎭", value=comment, inline=False)
    except Exception as e:
        print(f"Error adding user comment: {e}")

# Använd i alla dice commands:
async def slash_roll(interaction, tärningar: str, mål: Optional[int] = None, demon: Optional[bool] = False):
    # ... befintlig logik ...
    
    # Skapa roll_result dict med information om resultatet
    roll_result = {
        "success": (total >= mål) if mål else None,
        "is_critical_success": total == (num_dice * sides) + modifier,  # Max möjligt
        "is_fumble": total == num_dice + modifier,  # Min möjligt
        "total": total,
        "target": mål
    }
    
    # Lägg till embed fields...
    
    # Lägg till kommentar
    add_user_comment(embed, interaction.user.id, roll_result)
    
    await interaction.response.send_message(embed=embed)
```

---

## 🎛️ Fas 3: Slash Commands för Settings

### 3.1 Skapa Comment Settings Commands (GM-ONLY)

**Skapa `src/commands/slash_comment_commands.py`:**

```python
"""
Slash commands for managing user comment settings - GM ONLY.
"""

import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional

def register_slash_comment_commands(bot: commands.Bot, user_settings, comment_generator, color_handler):
    """Register slash commands for comment settings - GM access only."""
    
    # Comment settings group - GM ONLY
    comment_group = app_commands.Group(name="kommentarer", description="Hantera spelares kommentarer (endast GM)")
    
    @comment_group.command(name="aktivera", description="Aktivera kommentarer för en spelare (endast GM)")
    @app_commands.describe(spelare="Spelare att aktivera kommentarer för")
    @app_commands.default_permissions(manage_guild=True)
    async def enable_comments(interaction: discord.Interaction, spelare: discord.Member):
        """Enable comments for a player - GM only."""
        # KRITISK: GM-kontroll
        if not any(role.name == 'Game Master' for role in interaction.user.roles):
            await interaction.response.send_message(
                "Du behöver Game Master-roll för detta kommando.", 
                ephemeral=True
            )
            return
        
        user_id = str(spelare.id)
        success = user_settings.set_comments_enabled(user_id, True)
        
        if success:
            settings = user_settings.get_user_settings(user_id)
            style = settings["comment_style"]
            frequency = int(settings["comment_frequency"] * 100)
            
            embed = discord.Embed(
                title="✅ Kommentarer Aktiverade",
                description=f"Kommentarer aktiverade för {spelare.display_name}!\n\n"
                           f"**Stil:** {style}\n"
                           f"**Frekvens:** {frequency}% av slag\n\n"
                           f"Använd `/kommentarer stil` för att ändra stil.\n"
                           f"Använd `/kommentarer frekvens` för att ändra frekvens.",
                color=discord.Color.green()
            )
        else:
            embed = discord.Embed(
                title="❌ Fel",
                description=f"Kunde inte aktivera kommentarer för {spelare.display_name}. Försök igen.",
                color=discord.Color.red()
            )
        
        await interaction.response.send_message(embed=embed)
    
    @comment_group.command(name="inaktivera", description="Inaktivera kommentarer för en spelare (endast GM)")
    @app_commands.describe(spelare="Spelare att inaktivera kommentarer för")
    @app_commands.default_permissions(manage_guild=True)
    async def disable_comments(interaction: discord.Interaction, spelare: discord.Member):
        """Disable comments for a player - GM only."""
        # KRITISK: GM-kontroll
        if not any(role.name == 'Game Master' for role in interaction.user.roles):
            await interaction.response.send_message(
                "Du behöver Game Master-roll för detta kommando.", 
                ephemeral=True
            )
            return
        
        user_id = str(spelare.id)
        success = user_settings.set_comments_enabled(user_id, False)
        
        if success:
            embed = discord.Embed(
                title="🔇 Kommentarer Inaktiverade",
                description=f"Kommentarer inaktiverade för {spelare.display_name}.\n\n"
                           "Använd `/kommentarer aktivera` för att aktivera dem igen.",
                color=discord.Color.orange()
            )
        else:
            embed = discord.Embed(
                title="❌ Fel", 
                description=f"Kunde inte inaktivera kommentarer för {spelare.display_name}. Försök igen.",
                color=discord.Color.red()
            )
        
        await interaction.response.send_message(embed=embed)
    
    @comment_group.command(name="stil", description="Ändra kommentarstil för en spelare (endast GM)")
    @app_commands.describe(
        spelare="Spelare att ändra stil för",
        stil="Välj kommentarstil"
    )
    @app_commands.choices(stil=[
        app_commands.Choice(name="Umnatak (syrlig)", value="umnatak"),
        app_commands.Choice(name="Uppmuntrande", value="encouraging"), 
        app_commands.Choice(name="Dramatisk", value="dramatic"),
        app_commands.Choice(name="Neutral", value="neutral")
    ])
    @app_commands.default_permissions(manage_guild=True)
    async def set_comment_style(interaction: discord.Interaction, spelare: discord.Member, stil: str):
        """Set comment style for a player - GM only."""
        # KRITISK: GM-kontroll
        if not any(role.name == 'Game Master' for role in interaction.user.roles):
            await interaction.response.send_message(
                "Du behöver Game Master-roll för detta kommando.", 
                ephemeral=True
            )
            return
        
        user_id = str(spelare.id)
        success = user_settings.set_comment_style(user_id, stil)
        
        if success:
            style_names = {
                "umnatak": "Umnatak (syrlig)",
                "encouraging": "Uppmuntrande", 
                "dramatic": "Dramatisk",
                "neutral": "Neutral"
            }
            
            embed = discord.Embed(
                title="🎭 Kommentarstil Uppdaterad",
                description=f"Kommentarstil för {spelare.display_name} ändrad till: **{style_names[stil]}**\n\n"
                           f"Aktivera kommentarer med `/kommentarer aktivera` om de inte redan är på.",
                color=discord.Color.blue()
            )
        else:
            embed = discord.Embed(
                title="❌ Fel",
                description=f"Kunde inte ändra kommentarstil för {spelare.display_name}. Försök igen.",
                color=discord.Color.red()
            )
        
        await interaction.response.send_message(embed=embed)
    
    @comment_group.command(name="frekvens", description="Ändra kommentarfrekvens för en spelare (endast GM)")
    @app_commands.describe(
        spelare="Spelare att ändra frekvens för",
        procent="Frekvens i procent (10-50)"
    )
    @app_commands.default_permissions(manage_guild=True)
    async def set_comment_frequency(interaction: discord.Interaction, spelare: discord.Member, procent: int):
        """Set comment frequency for a player - GM only."""
        # KRITISK: GM-kontroll
        if not any(role.name == 'Game Master' for role in interaction.user.roles):
            await interaction.response.send_message(
                "Du behöver Game Master-roll för detta kommando.", 
                ephemeral=True
            )
            return
        
        if not (10 <= procent <= 50):
            embed = discord.Embed(
                title="❌ Ogiltig Frekvens",
                description="Frekvensen måste vara mellan 10% och 50%.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        user_id = str(spelare.id)
        frequency = procent / 100.0
        success = user_settings.set_comment_frequency(user_id, frequency)
        
        if success:
            embed = discord.Embed(
                title="📊 Kommentarfrekvens Uppdaterad",
                description=f"Kommentarfrekvens för {spelare.display_name} ändrad till: **{procent}%**\n\n"
                           f"De kommer få kommentarer på cirka {procent}% av sina tärningsslag.",
                color=discord.Color.blue()
            )
        else:
            embed = discord.Embed(
                title="❌ Fel",
                description=f"Kunde inte ändra kommentarfrekvens för {spelare.display_name}. Försök igen.",
                color=discord.Color.red()
            )
        
        await interaction.response.send_message(embed=embed)
    
    @comment_group.command(name="status", description="Visa kommentarinställningar för en spelare (endast GM)")
    @app_commands.describe(spelare="Spelare att visa inställningar för")
    @app_commands.default_permissions(manage_guild=True)
    async def show_comment_status(interaction: discord.Interaction, spelare: discord.Member):
        """Show player's current comment settings - GM only."""
        # KRITISK: GM-kontroll
        if not any(role.name == 'Game Master' for role in interaction.user.roles):
            await interaction.response.send_message(
                "Du behöver Game Master-roll för detta kommando.", 
                ephemeral=True
            )
            return
        
        user_id = str(spelare.id)
        settings = user_settings.get_user_settings(user_id)
        
        style_names = {
            "umnatak": "Umnatak (syrlig)",
            "encouraging": "Uppmuntrande",
            "dramatic": "Dramatisk", 
            "neutral": "Neutral"
        }
        
        enabled = settings["comments_enabled"]
        style = settings["comment_style"]
        frequency = int(settings["comment_frequency"] * 100)
        
        status_emoji = "✅" if enabled else "🔇"
        status_text = "Aktiverade" if enabled else "Inaktiverade"
        
        embed = discord.Embed(
            title=f"{status_emoji} {spelare.display_name}s Kommentarinställningar",
            color=discord.Color.green() if enabled else discord.Color.grey()
        )
        
        embed.add_field(
            name="Status",
            value=status_text,
            inline=True
        )
        
        embed.add_field(
            name="Stil", 
            value=style_names.get(style, style),
            inline=True
        )
        
        embed.add_field(
            name="Frekvens",
            value=f"{frequency}%",
            inline=True
        )
        
        if not enabled:
            embed.add_field(
                name="💡 Tips",
                value=f"Använd `/kommentarer aktivera spelare:{spelare.mention}` för att aktivera kommentarer!",
                inline=False
            )
        
        await interaction.response.send_message(embed=embed)
    
    @comment_group.command(name="lista", description="Visa alla spelares kommentarinställningar (endast GM)")
    @app_commands.default_permissions(manage_guild=True)
    async def list_all_comments(interaction: discord.Interaction):
        """List all players' comment settings - GM only."""
        # KRITISK: GM-kontroll
        if not any(role.name == 'Game Master' for role in interaction.user.roles):
            await interaction.response.send_message(
                "Du behöver Game Master-roll för detta kommando.", 
                ephemeral=True
            )
            return
        
        # Get all users with settings
        all_settings = user_settings.settings_cache
        
        if not all_settings:
            embed = discord.Embed(
                title="📝 Kommentarinställningar",
                description="Inga spelare har kommentarinställningar än.",
                color=discord.Color.grey()
            )
            await interaction.response.send_message(embed=embed)
            return
        
        embed = discord.Embed(
            title="📝 Alla Kommentarinställningar",
            color=discord.Color.blue()
        )
        
        for user_id, settings in all_settings.items():
            try:
                user = bot.get_user(int(user_id))
                display_name = user.display_name if user else f"User {user_id}"
                
                enabled = settings["comments_enabled"]
                style = settings["comment_style"]
                frequency = int(settings["comment_frequency"] * 100)
                
                status = "✅ På" if enabled else "🔇 Av"
                
                embed.add_field(
                    name=display_name,
                    value=f"{status} | {style} | {frequency}%",
                    inline=True
                )
            except Exception as e:
                print(f"Error processing user {user_id}: {e}")
        
        await interaction.response.send_message(embed=embed)
    
    # Global comment controls
    @comment_group.command(name="global_av", description="Stäng av alla kommentarer globalt (endast GM)")
    @app_commands.default_permissions(manage_guild=True)
    async def global_disable(interaction: discord.Interaction):
        """Globally disable all comments - GM only."""
        # KRITISK: GM-kontroll
        if not any(role.name == 'Game Master' for role in interaction.user.roles):
            await interaction.response.send_message(
                "Du behöver Game Master-roll för detta kommando.", 
                ephemeral=True
            )
            return
        
        # Disable for all users
        count = 0
        for user_id in user_settings.settings_cache.keys():
            if user_settings.set_comments_enabled(user_id, False):
                count += 1
        
        embed = discord.Embed(
            title="🔇 Globalt Kommentarstopp",
            description=f"Kommentarer inaktiverade för {count} spelare.\n\n"
                       "Använd `/kommentarer aktivera` för att aktivera individuellt igen.",
            color=discord.Color.orange()
        )
        
        await interaction.response.send_message(embed=embed)
    
    # Register the group
    bot.tree.add_command(comment_group)
```
```

### 3.2 Registrera Comment Commands

**Lägg till i `src/main.py` on_ready():**

```python
# Import comment commands
from commands.slash_comment_commands import register_slash_comment_commands

# I on_ready(), efter andra registreringar:
register_slash_comment_commands(bot, user_settings, comment_generator, color_handler)
print("✅ Slash kommentarkommandon registrerade.")
```

---

## 🧪 Fas 4: Testning och Validering

### 4.1 Test Commands (som GM)

```bash
# Testa grundläggande GM-funktionalitet:
/kommentarer status spelare:@Umnatak      # Visa spelarens inställningar
/kommentarer aktivera spelare:@Umnatak    # Aktivera kommentarer för Umnatak
/kommentarer stil spelare:@Umnatak stil:encouraging # Sätt stil
/kommentarer frekvens spelare:@Umnatak procent:30   # Sätt frekvens

# Testa andra spelare:
/kommentarer aktivera spelare:@Player2    # Aktivera för annan spelare
/kommentarer stil spelare:@Player2 stil:dramatic # Sätt dramatisk stil

# Testa admin-funktioner:
/kommentarer lista                        # Visa alla spelares inställningar
/kommentarer global_av                    # Stäng av alla kommentarer

# Testa med tärningsslag (som de aktiva spelarna):
/roll tärningar:3d6+2        # Umnatak bör få uppmuntrande kommentarer
/ex tärningar:4d6            # Player2 bör få dramatiska kommentarer

# Testa permission-kontroll (som icke-GM):
/kommentarer aktivera spelare:@Someone # Bör ge "Du behöver Game Master-roll"
```

### 4.2 Data Validation

**Kontrollera att `data/user_settings.json` skapas:**

```json
{
  "USER_ID_HERE": {
    "comments_enabled": true,
    "comment_frequency": 0.3,
    "comment_style": "encouraging",
    "created_at": "2025-01-21T10:30:00",
    "last_updated": "2025-01-21T10:35:00"
  }
}
```

---

## ✅ Komplett Implementation Checklista

### Kod som ska skapas:
- [ ] `src/core/user_settings.py` - UserSettingsManager class
- [ ] `src/core/comment_styles.py` - CommentGenerator och COMMENT_STYLES
- [ ] `src/commands/slash_comment_commands.py` - Comment management commands

### Kod som ska uppdateras:
- [ ] `src/main.py` - Lägg till user_settings och comment_generator
- [ ] `src/commands/slash_dice_commands.py` - Ersätt Umnatak-logik med nya systemet
- [ ] Ta bort gamla Umnatak-funktioner från `main.py`

### Funktioner som ska fungera:
- [ ] `/kommentarer aktivera/inaktivera` - On/off funktionalitet
- [ ] `/kommentarer stil` - Välja mellan 4 olika stilar
- [ ] `/kommentarer frekvens` - Sätta 10-50% frekvens
- [ ] `/kommentarer status` - Visa nuvarande inställningar
- [ ] Kommentarer dyker upp i dice commands baserat på inställningar
- [ ] Default: Alla användare har kommentarer avstängda

### Datahantering:
- [ ] `data/user_settings.json` skapas automatiskt
- [ ] Settings sparas permanent mellan bot-omstarter
- [ ] Backup-vänligt JSON-format

**🎯 Resultat: Ett flexibelt kommentarsystem som alla spelare kan anpassa efter sin smak!**