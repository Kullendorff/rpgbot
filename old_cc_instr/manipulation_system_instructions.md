# Hemligt Tärnings-Manipulation System - Implementation

## 🎯 Projektöversikt

Skapa ett hemligt system där GM kan manipulera tärningsresultat för spelare (och sig själv) utan att de vet om det. Systemet ska vara helt osynligt för alla utom GM.

**Mål:**
- GM kan aktivera automatisk framgång/misslyckande för spelare
- GM kan aktivera automatisk framgång/misslyckande för sig själv
- Manipulationen är helt hemlig - inga meddelanden till påverkade spelare
- Endast GM kan se status och kontrollera systemet

---

## 🏗️ Fas 1: Manipulation Manager System

### 1.1 Skapa ManipulationManager

**Skapa `src/core/manipulation_manager.py`:**

```python
"""
Hemlig tärnings-manipulation system för GM.
Hanterar automatisk framgång/misslyckande utan att spelare vet om det.
"""

import json
import os
from typing import Dict, Optional, Any, List
from datetime import datetime
import random

class ManipulationManager:
    def __init__(self, data_dir: str = "data"):
        """
        Initialize manipulation manager.
        
        Args:
            data_dir: Directory to store manipulation data
        """
        self.data_dir = data_dir
        self.manipulation_file = os.path.join(data_dir, "secret_manipulations.json")
        self.active_manipulations = {}
        self._ensure_data_dir()
        self._load_manipulations()
    
    def _ensure_data_dir(self):
        """Ensure data directory exists."""
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
    
    def _load_manipulations(self):
        """Load active manipulations from file."""
        try:
            if os.path.exists(self.manipulation_file):
                with open(self.manipulation_file, 'r', encoding='utf-8') as f:
                    self.active_manipulations = json.load(f)
            else:
                self.active_manipulations = {}
        except Exception as e:
            print(f"Error loading manipulations: {e}")
            self.active_manipulations = {}
    
    def _save_manipulations(self):
        """Save active manipulations to file."""
        try:
            with open(self.manipulation_file, 'w', encoding='utf-8') as f:
                json.dump(self.active_manipulations, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving manipulations: {e}")
    
    def set_player_manipulation(self, user_id: str, manipulation_type: str, gm_id: str) -> bool:
        """
        Set manipulation for a player.
        
        Args:
            user_id: Target player's Discord user ID
            manipulation_type: 'lycka' (auto-success) or 'olycka' (auto-fail)
            gm_id: GM who activated this manipulation
            
        Returns:
            True if successful
        """
        valid_types = ['lycka', 'olycka']
        if manipulation_type not in valid_types:
            return False
        
        try:
            manipulation_data = {
                "type": manipulation_type,
                "target": "player",
                "activated_by": gm_id,
                "activated_at": datetime.now().isoformat(),
                "rolls_affected": 0
            }
            
            self.active_manipulations[user_id] = manipulation_data
            self._save_manipulations()
            
            print(f"[SECRET] Manipulation '{manipulation_type}' activated for user {user_id} by GM {gm_id}")
            return True
        except Exception as e:
            print(f"Error setting player manipulation: {e}")
            return False
    
    def set_gm_manipulation(self, gm_id: str, manipulation_type: str) -> bool:
        """
        Set manipulation for GM themselves.
        
        Args:
            gm_id: GM's Discord user ID
            manipulation_type: 'gudomlig' (auto-success) or 'förbannelse' (auto-fail)
            
        Returns:
            True if successful
        """
        valid_types = ['gudomlig', 'förbannelse']
        if manipulation_type not in valid_types:
            return False
        
        try:
            manipulation_data = {
                "type": manipulation_type,
                "target": "gm",
                "activated_by": gm_id,
                "activated_at": datetime.now().isoformat(),
                "rolls_affected": 0
            }
            
            self.active_manipulations[gm_id] = manipulation_data
            self._save_manipulations()
            
            print(f"[SECRET] GM manipulation '{manipulation_type}' activated for GM {gm_id}")
            return True
        except Exception as e:
            print(f"Error setting GM manipulation: {e}")
            return False
    
    def remove_manipulation(self, user_id: str) -> bool:
        """
        Remove manipulation for a user.
        
        Args:
            user_id: User's Discord user ID
            
        Returns:
            True if manipulation was removed
        """
        try:
            if user_id in self.active_manipulations:
                del self.active_manipulations[user_id]
                self._save_manipulations()
                print(f"[SECRET] Manipulation removed for user {user_id}")
                return True
            return False
        except Exception as e:
            print(f"Error removing manipulation: {e}")
            return False
    
    def get_manipulation(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get active manipulation for a user.
        
        Args:
            user_id: User's Discord user ID
            
        Returns:
            Manipulation data or None
        """
        return self.active_manipulations.get(user_id)
    
    def get_all_manipulations(self) -> Dict[str, Dict[str, Any]]:
        """Get all active manipulations."""
        return self.active_manipulations.copy()
    
    def manipulate_roll_result(self, user_id: str, original_rolls: List[int], 
                              sides: int, modifier: int, target: Optional[int]) -> tuple:
        """
        Manipulate roll result if user has active manipulation.
        
        Args:
            user_id: User's Discord user ID
            original_rolls: Original dice roll values
            sides: Number of sides on dice
            modifier: Roll modifier
            target: Target value (if any)
            
        Returns:
            Tuple of (manipulated_rolls, was_manipulated, manipulation_type)
        """
        manipulation = self.get_manipulation(str(user_id))
        if not manipulation:
            return original_rolls, False, None
        
        manipulation_type = manipulation["type"]
        
        try:
            # Update roll count
            manipulation["rolls_affected"] += 1
            self._save_manipulations()
            
            # Only manipulate if there's a target to succeed/fail against
            if target is None:
                return original_rolls, False, manipulation_type
            
            current_total = sum(original_rolls) + modifier
            
            if manipulation_type in ["lycka", "gudomlig"]:
                # AUTO-SUCCESS: Ensure roll succeeds
                if current_total >= target:
                    # Already succeeding, no need to manipulate
                    return original_rolls, False, manipulation_type
                else:
                    # Need to manipulate to succeed
                    needed_total = target
                    needed_dice_sum = needed_total - modifier
                    
                    # Create believable manipulated rolls that sum to needed value
                    manipulated_rolls = self._create_believable_rolls(
                        original_rolls, needed_dice_sum, sides, "success"
                    )
                    
                    print(f"[SECRET] {manipulation_type.upper()} manipulation: {original_rolls} -> {manipulated_rolls}")
                    return manipulated_rolls, True, manipulation_type
            
            elif manipulation_type in ["olycka", "förbannelse"]:
                # AUTO-FAIL: Ensure roll fails
                if current_total < target:
                    # Already failing, no need to manipulate
                    return original_rolls, False, manipulation_type
                else:
                    # Need to manipulate to fail
                    needed_total = target - 1
                    needed_dice_sum = needed_total - modifier
                    
                    # Ensure we don't go below minimum possible
                    min_possible = len(original_rolls)
                    if needed_dice_sum < min_possible:
                        needed_dice_sum = min_possible
                    
                    # Create believable manipulated rolls that sum to needed value
                    manipulated_rolls = self._create_believable_rolls(
                        original_rolls, needed_dice_sum, sides, "failure"
                    )
                    
                    print(f"[SECRET] {manipulation_type.upper()} manipulation: {original_rolls} -> {manipulated_rolls}")
                    return manipulated_rolls, True, manipulation_type
            
        except Exception as e:
            print(f"Error manipulating roll: {e}")
            return original_rolls, False, manipulation_type
        
        return original_rolls, False, manipulation_type
    
    def _create_believable_rolls(self, original_rolls: List[int], target_sum: int, 
                                sides: int, intent: str) -> List[int]:
        """
        Create believable manipulated rolls that sum to target.
        
        Args:
            original_rolls: Original roll values
            target_sum: Target sum for manipulated rolls
            sides: Number of sides on dice
            intent: "success" or "failure"
            
        Returns:
            List of manipulated roll values
        """
        num_dice = len(original_rolls)
        min_sum = num_dice  # Minimum possible (all 1s)
        max_sum = num_dice * sides  # Maximum possible
        
        # Ensure target is within possible range
        target_sum = max(min_sum, min(target_sum, max_sum))
        
        # Start with original rolls and adjust gradually
        manipulated = original_rolls.copy()
        current_sum = sum(manipulated)
        
        # If we need to increase the sum
        while current_sum < target_sum:
            # Find a die that can be increased
            for i in range(num_dice):
                if manipulated[i] < sides and current_sum < target_sum:
                    increase = min(sides - manipulated[i], target_sum - current_sum)
                    manipulated[i] += increase
                    current_sum += increase
                    if current_sum >= target_sum:
                        break
        
        # If we need to decrease the sum
        while current_sum > target_sum:
            # Find a die that can be decreased
            for i in range(num_dice):
                if manipulated[i] > 1 and current_sum > target_sum:
                    decrease = min(manipulated[i] - 1, current_sum - target_sum)
                    manipulated[i] -= decrease
                    current_sum -= decrease
                    if current_sum <= target_sum:
                        break
        
        # Add some randomness to make it look natural
        # Occasionally swap values between dice while maintaining sum
        if random.random() < 0.3:  # 30% chance
            for _ in range(random.randint(1, 3)):
                i, j = random.sample(range(num_dice), 2)
                if manipulated[i] > 1 and manipulated[j] < sides:
                    if random.random() < 0.5:
                        manipulated[i] -= 1
                        manipulated[j] += 1
        
        return manipulated
    
    def clear_all_manipulations(self) -> int:
        """
        Clear all active manipulations.
        
        Returns:
            Number of manipulations cleared
        """
        count = len(self.active_manipulations)
        self.active_manipulations = {}
        self._save_manipulations()
        print(f"[SECRET] Cleared {count} active manipulations")
        return count
```

---

## 🎮 Fas 2: Integration med Dice Commands

### 2.1 Uppdatera main.py

**Lägg till i `src/main.py` imports och setup:**

```python
# Lägg till import
from core.manipulation_manager import ManipulationManager

# I global setup (efter andra globala objekt):
manipulation_manager = ManipulationManager()
```

### 2.2 Uppdatera Dice Commands

**I `src/commands/slash_dice_commands.py`, uppdatera alla dice commands:**

```python
# Lägg till denna funktion i början av filen:
def apply_secret_manipulation(user_id: str, rolls: List[int], sides: int, 
                             modifier: int, target: Optional[int]) -> tuple:
    """
    Apply secret manipulation if active for user.
    
    Returns:
        Tuple of (final_rolls, was_manipulated, manipulation_type)
    """
    try:
        from main import manipulation_manager
        return manipulation_manager.manipulate_roll_result(
            str(user_id), rolls, sides, modifier, target
        )
    except Exception as e:
        print(f"Error applying manipulation: {e}")
        return rolls, False, None

# Uppdatera roll_command:
async def slash_roll(interaction, tärningar: str, mål: Optional[int] = None, demon: Optional[bool] = False):
    try:
        # ... befintlig parsing kod ...
        
        # ORIGINAL ROLLS
        original_rolls = [random.randint(1, sides) for _ in range(num_dice)]
        
        # APPLY SECRET MANIPULATION (innan demon inspiration)
        final_rolls, was_manipulated, manipulation_type = apply_secret_manipulation(
            interaction.user.id, original_rolls, sides, modifier, mål
        )
        
        # Beräkna total med (möjligtvis manipulerade) rolls
        total = sum(final_rolls) + modifier
        
        # DEMON INSPIRATION (endast om inte redan manipulerat)
        if demon and mål and not was_manipulated:
            # ... befintlig demon logic ...
            # Använd final_rolls för demon inspiration också
        
        # VISA ENDAST FINAL ROLLS (ingen indikation på manipulation)
        roll_result = {
            "success": (total >= mål) if mål else None,
            "is_critical_success": total == (num_dice * sides) + modifier,
            "is_fumble": total == num_dice + modifier,
            "total": total,
            "target": mål,
            "was_manipulated": was_manipulated,  # För intern logging
            "manipulation_type": manipulation_type
        }
        
        # NORMAL EMBED CREATION (använd final_rolls)
        embed = discord.Embed(color=color)
        embed.add_field(name="Tärningar", value=str(final_rolls), inline=False)
        # ... resten av embed creation ...
        
        # Secret logging för GM (endast i console)
        if was_manipulated:
            print(f"[SECRET MANIPULATION] {manipulation_type.upper()} applied to {interaction.user.display_name}: {original_rolls} -> {final_rolls}")
        
        await interaction.response.send_message(embed=embed)
        
    except Exception as e:
        await interaction.response.send_message(f"Ett fel uppstod: {str(e)}", ephemeral=True)

# SAMMA LOGIK ska appliceras på:
# - slash_ex (obegränsade tärningar)
# - slash_count (success counting)
# - secret_roll, secret_ex, secret_count (admin commands)
```

---

## 🎛️ Fas 3: GM Manipulation Commands

### 3.1 Skapa Manipulation Commands

**Skapa `src/commands/slash_manipulation_commands.py`:**

```python
"""
Hemliga manipulation commands - endast GM.
Helt osynliga för alla spelare.
"""

import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional

def register_slash_manipulation_commands(bot: commands.Bot, manipulation_manager, color_handler):
    """Register secret manipulation commands - GM ONLY."""
    
    # Manipulation group - HEMLIGT GM SYSTEM
    manip_group = app_commands.Group(name="manipulation", description="Hemligt tärningsmanipulation (endast GM)")
    
    @manip_group.command(name="aktivera", description="Aktivera manipulation för spelare (hemligt)")
    @app_commands.describe(
        spelare="Spelare att manipulera",
        typ="Typ av manipulation"
    )
    @app_commands.choices(typ=[
        app_commands.Choice(name="Lycka (automatisk framgång)", value="lycka"),
        app_commands.Choice(name="Olycka (automatisk misslyckande)", value="olycka")
    ])
    @app_commands.default_permissions(manage_guild=True)
    async def activate_player_manipulation(
        interaction: discord.Interaction,
        spelare: discord.Member,
        typ: str
    ):
        """Aktivera hemlig manipulation för spelare."""
        # KRITISK: GM-kontroll
        if not any(role.name == 'Game Master' for role in interaction.user.roles):
            await interaction.response.send_message(
                "Du behöver Game Master-roll för detta kommando.", 
                ephemeral=True
            )
            return
        
        success = manipulation_manager.set_player_manipulation(
            str(spelare.id), typ, str(interaction.user.id)
        )
        
        if success:
            type_names = {
                "lycka": "Lycka (automatisk framgång)",
                "olycka": "Olycka (automatisk misslyckande)"
            }
            
            embed = discord.Embed(
                title="🎭 Hemlig Manipulation Aktiverad",
                description=f"**Spelare:** {spelare.display_name}\n"
                           f"**Typ:** {type_names[typ]}\n\n"
                           f"⚠️ **HEMLIGT** - Spelaren vet inte om detta!\n"
                           f"Alla tärningsslag med målvärde kommer påverkas automatiskt.",
                color=discord.Color.dark_purple()
            )
            
            embed.add_field(
                name="🔍 Vad händer nu?",
                value=f"• {spelare.display_name}s slag manipuleras automatiskt\n"
                      f"• Ingen visuell indikation för spelaren\n"
                      f"• Endast slag med målvärde påverkas\n"
                      f"• Använd `/manipulation status` för att se alla aktiva",
                inline=False
            )
        else:
            embed = discord.Embed(
                title="❌ Manipulation Misslyckades",
                description="Kunde inte aktivera manipulation. Kontrollera parametrar.",
                color=discord.Color.red()
            )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @manip_group.command(name="aktivera_gm", description="Aktivera manipulation för dig själv (hemligt)")
    @app_commands.describe(typ="Typ av GM-manipulation")
    @app_commands.choices(typ=[
        app_commands.Choice(name="Gudomlig (du lyckas alltid)", value="gudomlig"),
        app_commands.Choice(name="Förbannelse (du misslyckas alltid)", value="förbannelse")
    ])
    @app_commands.default_permissions(manage_guild=True)
    async def activate_gm_manipulation(
        interaction: discord.Interaction,
        typ: str
    ):
        """Aktivera hemlig manipulation för GM själv."""
        # KRITISK: GM-kontroll
        if not any(role.name == 'Game Master' for role in interaction.user.roles):
            await interaction.response.send_message(
                "Du behöver Game Master-roll för detta kommando.", 
                ephemeral=True
            )
            return
        
        success = manipulation_manager.set_gm_manipulation(
            str(interaction.user.id), typ
        )
        
        if success:
            type_names = {
                "gudomlig": "Gudomlig (automatisk framgång)",
                "förbannelse": "Förbannelse (automatisk misslyckande)"
            }
            
            embed = discord.Embed(
                title="⚡ GM Manipulation Aktiverad",
                description=f"**Typ:** {type_names[typ]}\n\n"
                           f"🎭 Dina egna tärningsslag kommer nu manipuleras automatiskt!\n"
                           f"Endast slag med målvärde påverkas.",
                color=discord.Color.gold()
            )
            
            embed.add_field(
                name="🎲 Vad händer?",
                value=f"• Dina slag manipuleras för att {'lyckas' if typ == 'gudomlig' else 'misslyckas'}\n"
                      f"• Helt hemligt - ingen annan ser manipulation\n"
                      f"• Fungerar på roll, ex, count commands\n"
                      f"• Använd `/manipulation inaktivera_gm` för att stänga av",
                inline=False
            )
        else:
            embed = discord.Embed(
                title="❌ GM Manipulation Misslyckades",
                description="Kunde inte aktivera GM manipulation.",
                color=discord.Color.red()
            )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @manip_group.command(name="inaktivera", description="Inaktivera manipulation för spelare")
    @app_commands.describe(spelare="Spelare att ta bort manipulation för")
    @app_commands.default_permissions(manage_guild=True)
    async def deactivate_player_manipulation(
        interaction: discord.Interaction,
        spelare: discord.Member
    ):
        """Inaktivera manipulation för spelare."""
        # KRITISK: GM-kontroll
        if not any(role.name == 'Game Master' for role in interaction.user.roles):
            await interaction.response.send_message(
                "Du behöver Game Master-roll för detta kommando.", 
                ephemeral=True
            )
            return
        
        success = manipulation_manager.remove_manipulation(str(spelare.id))
        
        if success:
            embed = discord.Embed(
                title="✅ Manipulation Inaktiverad",
                description=f"Manipulation borttagen för {spelare.display_name}.\n"
                           f"Deras tärningsslag är nu normala igen.",
                color=discord.Color.green()
            )
        else:
            embed = discord.Embed(
                title="ℹ️ Ingen Manipulation",
                description=f"{spelare.display_name} hade ingen aktiv manipulation.",
                color=discord.Color.grey()
            )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @manip_group.command(name="inaktivera_gm", description="Inaktivera din egen manipulation")
    @app_commands.default_permissions(manage_guild=True)
    async def deactivate_gm_manipulation(interaction: discord.Interaction):
        """Inaktivera GM:s egen manipulation."""
        # KRITISK: GM-kontroll
        if not any(role.name == 'Game Master' for role in interaction.user.roles):
            await interaction.response.send_message(
                "Du behöver Game Master-roll för detta kommando.", 
                ephemeral=True
            )
            return
        
        success = manipulation_manager.remove_manipulation(str(interaction.user.id))
        
        if success:
            embed = discord.Embed(
                title="✅ GM Manipulation Inaktiverad",
                description="Din manipulation är nu borttagen.\n"
                           "Dina tärningsslag är normala igen.",
                color=discord.Color.green()
            )
        else:
            embed = discord.Embed(
                title="ℹ️ Ingen GM Manipulation",
                description="Du hade ingen aktiv manipulation.",
                color=discord.Color.grey()
            )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @manip_group.command(name="status", description="Visa alla aktiva manipulationer (hemligt)")
    @app_commands.default_permissions(manage_guild=True)
    async def show_manipulation_status(interaction: discord.Interaction):
        """Visa alla aktiva manipulationer - endast GM."""
        # KRITISK: GM-kontroll
        if not any(role.name == 'Game Master' for role in interaction.user.roles):
            await interaction.response.send_message(
                "Du behöver Game Master-roll för detta kommando.", 
                ephemeral=True
            )
            return
        
        all_manipulations = manipulation_manager.get_all_manipulations()
        
        if not all_manipulations:
            embed = discord.Embed(
                title="🎭 Aktiva Manipulationer",
                description="Inga aktiva manipulationer för tillfället.",
                color=discord.Color.grey()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        embed = discord.Embed(
            title="🎭 Aktiva Hemliga Manipulationer",
            description="Alla manipulationer som påverkar tärningsslag:",
            color=discord.Color.dark_purple()
        )
        
        type_names = {
            "lycka": "🍀 Lycka (framgång)",
            "olycka": "💀 Olycka (misslyckande)", 
            "gudomlig": "⚡ Gudomlig (GM framgång)",
            "förbannelse": "🔥 Förbannelse (GM misslyckande)"
        }
        
        for user_id, data in all_manipulations.items():
            try:
                user = bot.get_user(int(user_id))
                display_name = user.display_name if user else f"User {user_id}"
                
                manipulation_type = data["type"]
                rolls_affected = data["rolls_affected"]
                activated_at = data["activated_at"][:10]  # Just date
                
                type_display = type_names.get(manipulation_type, manipulation_type)
                
                embed.add_field(
                    name=f"{type_display}",
                    value=f"**Spelare:** {display_name}\n"
                          f"**Aktiv sedan:** {activated_at}\n"
                          f"**Slag påverkade:** {rolls_affected}",
                    inline=True
                )
            except Exception as e:
                print(f"Error displaying manipulation for {user_id}: {e}")
        
        embed.add_field(
            name="🔍 Påminnelse",
            value="Dessa manipulationer är helt hemliga!\n"
                  "Spelarna vet inte att deras slag påverkas.",
            inline=False
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @manip_group.command(name="rensa_alla", description="Ta bort alla aktiva manipulationer")
    @app_commands.default_permissions(manage_guild=True)
    async def clear_all_manipulations(interaction: discord.Interaction):
        """Rensa alla aktiva manipulationer - emergency stop."""
        # KRITISK: GM-kontroll
        if not any(role.name == 'Game Master' for role in interaction.user.roles):
            await interaction.response.send_message(
                "Du behöver Game Master-roll för detta kommando.", 
                ephemeral=True
            )
            return
        
        count = manipulation_manager.clear_all_manipulations()
        
        embed = discord.Embed(
            title="🧹 Alla Manipulationer Rensade",
            description=f"Tog bort {count} aktiva manipulationer.\n"
                       "Alla tärningsslag är nu normala igen.",
            color=discord.Color.orange()
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    # Register the group
    bot.tree.add_command(manip_group)
```

### 3.2 Registrera Manipulation Commands

**Lägg till i `src/main.py` on_ready():**

```python
# Import manipulation commands
from commands.slash_manipulation_commands import register_slash_manipulation_commands

# I on_ready(), efter andra registreringar:
register_slash_manipulation_commands(bot, manipulation_manager, color_handler)
print("✅ Slash manipulationskommandon registrerade (hemliga).")
```

---

## 🧪 Fas 4: Testning och Validering

### 4.1 Test Commands (som GM)

```bash
# Aktivera manipulationer:
/manipulation aktivera spelare:@Player1 typ:lycka       # Player1 lyckas alltid
/manipulation aktivera spelare:@Player2 typ:olycka     # Player2 misslyckas alltid
/manipulation aktivera_gm typ:gudomlig                 # GM lyckas alltid

# Testa manipulerade slag (som påverkade spelare):
/roll tärningar:3d6+2 mål:15    # Player1 bör lyckas även med dåliga rolls
/roll tärningar:3d6+2 mål:8     # Player2 bör misslyckas även med bra rolls

# GM status och kontroll:
/manipulation status            # Visa alla aktiva manipulationer
/manipulation inaktivera spelare:@Player1  # Ta bort manipulation
/manipulation rensa_alla        # Emergency stop - ta bort alla

# Test utan målvärde (ska INTE manipuleras):
/roll tärningar:3d6+2           # Ska vara normalt även med aktiv manipulation
```

### 4.2 Hemlig Data Validation

**Kontrollera att `data/secret_manipulations.json` skapas:**

```json
{
  "USER_ID_1": {
    "type": "lycka",
    "target": "player", 
    "activated_by": "GM_USER_ID",
    "activated_at": "2025-01-21T10:30:00",
    "rolls_affected": 5
  },
  "USER_ID_2": {
    "type": "förbannelse",
    "target": "gm",
    "activated_by": "GM_USER_ID", 
    "activated_at": "2025-01-21T10:35:00",
    "rolls_affected": 2
  }
}
```

---

## ✅ Implementation Checklista

### Kod som ska skapas:
- [ ] `src/core/manipulation_manager.py` - ManipulationManager class
- [ ] `src/commands/slash_manipulation_commands.py` - GM manipulation commands

### Kod som ska uppdateras:
- [ ] `src/main.py` - Lägg till manipulation_manager global
- [ ] `src/commands/slash_dice_commands.py` - Integrera manipulation i alla dice commands
- [ ] `src/commands/slash_admin_commands.py` - Uppdatera secret commands med manipulation

### Funktioner som ska fungera:
- [ ] `/manipulation aktivera spelare:@User typ:lycka` - Hemlig auto-framgång
- [ ] `/manipulation aktivera spelare:@User typ:olycka` - Hemlig auto-misslyckande  
- [ ] `/manipulation aktivera_gm typ:gudomlig` - GM auto-framgång
- [ ] `/manipulation aktivera_gm typ:förbannelse` - GM auto-misslyckande
- [ ] `/manipulation status` - Visa alla aktiva (endast GM)
- [ ] `/manipulation inaktivera` - Ta bort specifik manipulation
- [ ] `/manipulation rensa_alla` - Emergency stop alla manipulationer

### Hemliga egenskaper:
- [ ] Ingen visuell indikation för påverkade spelare
- [ ] Manipulerade rolls ser naturliga ut
- [ ] Endast GM kan se aktiva manipulationer
- [ ] Endast slag med målvärde påverkas
- [ ] Console logging för GM debugging

### Datahantering:
- [ ] `data/secret_manipulations.json` för persistent storage
- [ ] Räknar antal påverkade slag per manipulation
- [ ] Timestamp för när manipulation aktiverades
- [ ] Spårar vem som aktiverade varje manipulation

---

## 🎭 Användningsexempel

### Scenario 1: Hjälp svag spelare
```bash
# GM ser att Player1 har otur
/manipulation aktivera spelare:@Player1 typ:lycka

# Player1 rullar normalt:
/roll tärningar:3d6+2 mål:15
# Resultat: [2, 3, 4] + 2 = 11 -> Manipuleras till [4, 5, 6] + 2 = 17 ✅

# Ingen vet att manipulation skedde!
```

### Scenario 2: GM vill misslyckas för dramats skull
```bash
# GM aktiverar självförbannelse
/manipulation aktivera_gm typ:förbannelse

# GM rullar för NPC:
/roll tärningar:4d6 mål:18  
# Resultat: [6, 6, 5, 4] = 21 -> Manipuleras till [3, 4, 5, 6] = 18 -> 17 ❌

# Skapar dramatisk spänning!
```

### Scenario 3: Hemlig straff för övermodig spelare
```bash
# Player2 är övermodig, GM vill läxa upp
/manipulation aktivera spelare:@Player2 typ:olycka

# Player2 rullar självsäkert:
/roll tärningar:5d6+3 mål:12
# Resultat: [4, 5, 5, 3, 2] + 3 = 22 -> Manipuleras till [1, 2, 3, 3, 2] + 3 = 14 -> 11 ❌

# Player2 förstår inte varför de har så otur plötsligt...
```

---

## 🔒 Säkerhetsaspekter

### GM-Only Access:
- **Discord permissions** (`manage_guild=True`)
- **Role checking** (`Game Master` roll krävs)
- **Ephemeral responses** (endast GM ser command resultat)

### Data Security:
- **Hemlig fil** (`secret_manipulations.json`) separerad från andra settings
- **Console logging** för debugging (ej synligt för spelare)
- **No telltale signs** i Discord meddelanden

### Missbruksskydd:
- **Endast målvärdes-slag** påverkas (ej rena tärningsslag)
- **Believable results** - manipulerade slag ser naturliga ut
- **Emergency stop** med `/manipulation rensa_alla`

---

## 🎨 Advanced Features (Framtida)

### Smart Manipulation:
```python
# Framtida förbättringar som kan läggas till:

# Gradual manipulation (inte 100% framgång):
/manipulation aktivera spelare:@User typ:lycka styrka:70  # 70% chans för framgång

# Tidsbaserad manipulation:
/manipulation aktivera spelare:@User typ:lycka duration:30  # 30 minuter

# Conditional manipulation:
/manipulation aktivera spelare:@User typ:lycka condition:"only_combat"  # Endast stridslag

# Manipulation med meddelanden:
/manipulation aktivera spelare:@User typ:lycka message:"Gudarna gynnar dig"
```

### Analytics:
```python
# Manipulation statistik:
/manipulation stats  # Visa användningsstatistik
/manipulation history spelare:@User  # Visa spelarens manipulationshistorik
```

---

## 🎯 Slutresultat

### Vad GM kan göra:
1. **Hemligt hjälpa** spelare som har otur
2. **Hemligt straffa** spelare som är övermodiga  
3. **Kontrollera sin egen lycka** för dramatiska effekter
4. **Skapa berättelsemoment** genom kontrollerade utfall

### Vad spelarna upplever:
- **Normala tärningsslag** - ingen aning om manipulation
- **Naturliga resultat** - manipulerade slag ser trovärdiga ut
- **Obeveklig dramatik** - lycka och olycka kommer "av sig själv"

### Systemfördelar:
- **Helt hemligt** - ingen spårarbarhet för spelare
- **Flexibelt** - GM kan kontrollera precis vad som behövs
- **Säkert** - endast GM har access
- **Persistent** - överlever bot-omstarter

**🎭 Det ultimata verktyget för diskret berättarkontroll! 🎲✨**

---

## 🆕 EXTRA: Ny Spelare Färgfix

**Lägg till i `color_handler.py` eller motsvarande:**

```python
# Lägg till ny spelare med Discord ID: 223183062882713600
# Föreslå en unik färg som inte krockar med befintliga

FIXED_USER_COLORS = {
    "680064176227352610": 0xFF6B6B,  # Umnatak - Röd
    "223183062882713600": 0x4ECDC4,  # Ny spelare - Turkos/Teal
    # Lägg till fler efter behov...
}

# Alternativa färger för ny spelare:
# 0x45B7D1  # Ljusblå
# 0x96CEB4  # Mint grön  
# 0xFFE66D  # Ljusgul
# 0xDDA0DD  # Plum/lila
# 0xFF9F43  # Orange
```

**Välj en färg som passar spelarens karaktär eller preferenser! 🎨**