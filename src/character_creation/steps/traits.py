"""
Character Traits Step for Character Creation

This module handles the optional character traits generation step where
players can choose to roll for personality traits (Lojalitet, Heder, Amor,
Aggression, Tro, Generositet, Rykte) based on their character's race.
"""

import discord
from discord.ext import commands
from typing import Optional, Tuple, List, Dict, Any
from pathlib import Path
import re
import random

from .base_step import BaseStep
from ..utils.dice_roller import CharacterDiceRoller


class TraitsStep(BaseStep):
    """Step 8: Optional character traits generation."""
    
    def __init__(self, embed_factory, data_dir: Optional[Path] = None):
        """
        Initialize the traits step.
        
        Args:
            embed_factory: The embed factory for creating Discord embeds
            data_dir: Optional data directory path
        """
        super().__init__(step_name="karaktärsdrag", step_number=8)
        self.embed_factory = embed_factory
        self.data_dir = data_dir or self._get_default_data_dir()
        self.dice_roller = CharacterDiceRoller()
        
        # Character traits that can be generated (rykte comes from other sources like börd/familj)
        self.trait_names = ['lojalitet', 'heder', 'amor', 'aggression', 'tro', 'generositet']
        
        # Race-specific dice formulas for traits
        self.trait_formulas = self._get_trait_formulas()
    
    def _get_default_data_dir(self) -> Path:
        """Get default data directory."""
        script_dir = Path(__file__).parent
        project_root = script_dir.parent.parent.parent
        return project_root / 'data' / 'character_tables'
    
    def _get_trait_formulas(self) -> Dict[str, Dict[str, str]]:
        """Get race-specific dice formulas for character traits."""
        return {
            'soldarn': {
                'lojalitet': '1d6+12',
                'heder': '3d6', 
                'amor': '3d6',
                'aggression': '3d6',
                'tro': '1d6+12',
                'generositet': '3d6'
            },
            'asharier': {
                'lojalitet': '3d6',
                'heder': '3d6',
                'amor': '3d6', 
                'aggression': '3d6',
                'tro': '3d6',
                'generositet': '1d6+2'
            },
            'auser': {
                'lojalitet': '3d6',
                'heder': '3d6',
                'amor': '3d6',
                'aggression': '3d6', 
                'tro': '1d6+12',
                'generositet': '3d6'
            },
            'thalasker': {
                'lojalitet': '3d6',
                'heder': '3d6',
                'amor': '3d6',
                'aggression': '3d6',
                'tro': '3d6',
                'generositet': '3d6'
            },
            'pyar': {
                'lojalitet': '2d6+6',
                'heder': '3d6',
                'amor': '2d6+1',
                'aggression': '3d6',
                'tro': '2d6+1',
                'generositet': '2d6+6'
            },
            'kiriya': {
                'lojalitet': '2d6+6',
                'heder': '3d6',
                'amor': '2d6+1',
                'aggression': '3d6',
                'tro': '2d6+1',
                'generositet': '2d6+6'
            },
            'thism': {
                'lojalitet': '2d6+6',
                'heder': '2d6+6',
                'amor': '2d6+1',
                'aggression': '2d6+6',
                'tro': '2d6+1',
                'generositet': '2d6+6'
            },
            'sanari': {
                'lojalitet': '2d6+6',
                'heder': '2d6+1',
                'amor': '2d6+1',
                'aggression': '2d6+1',
                'tro': '2d6+1',
                'generositet': '2d6+1'
            },
            'léaram': {
                'lojalitet': '2d6+6',
                'heder': '2d6+6',
                'amor': '2d6+1',
                'aggression': '2d6+6',
                'tro': '3d6',
                'generositet': '2d6+6'
            },
            'henéa': {
                'lojalitet': '2d6+6',
                'heder': '3d6',
                'amor': '2d6+1',
                'aggression': '1d6+12',
                'tro': '2d6+6',
                'generositet': '2d6+1'
            },
            'cirefalier': {
                'lojalitet': '2d6+6',
                'heder': '3d6',
                'amor': '3d6',
                'aggression': '3d6',
                'tro': '2d6+6',
                'generositet': '3d6'
            },
            'vanar': {
                'lojalitet': '3d6',
                'heder': '3d6',
                'amor': '3d6',
                'aggression': '3d6',
                'tro': '3d6',
                'generositet': '3d6'
            }
        }
    
    async def execute(self, ctx: commands.Context, session: 'CharacterSession') -> discord.Embed:
        """
        Execute the traits step.
        
        Args:
            ctx: Discord command context
            session: Current character creation session
            
        Returns:
            Discord embed displaying the traits options
        """
        embed = self.embed_factory.admin_message(
            session.user_id,
            f"🎭 Steg {self.step_number}/{session.max_steps}: Karaktärsdrag",
            "Vill du slå fram karaktärsdrag för din rollperson?"
        )
        
        embed.add_field(
            name="📋 Vad är karaktärsdrag?",
            value=(
                "Karaktärsdrag som **Lojalitet**, **Heder**, **Amor**, **Aggression**, "
                "**Tro** och **Generositet** ger din rollperson personlighet och djup. "
                "Dessa påverkar rollspelet men inte mekaniken direkt."
            ),
            inline=False
        )
        
        embed.add_field(
            name="✅ Dina alternativ",
            value=(
                "• **slå** - Slå fram karaktärsdrag baserat på ditt folkslag\n"
                "• **hoppa** - Hoppa över karaktärsdrag (rekommenderat för nybörjare)"
            ),
            inline=False
        )
        
        # Show current race
        race = session.data.get('folkslag', 'Okänt')
        race_display = self._get_race_display_name(race, session)
        
        embed.add_field(
            name="👤 Ditt folkslag",
            value=f"**{race_display}** - Karaktärsdrag kommer slås enligt folkslagets värden",
            inline=False
        )
        
        # Show what traits will be generated
        trait_formulas = self._get_trait_dice_for_race(race, session)
        if trait_formulas:
            trait_preview = []
            for trait_name in self.trait_names:
                formula = trait_formulas.get(trait_name, '3d6')
                trait_preview.append(f"**{trait_name.capitalize()}:** {formula}")
            
            embed.add_field(
                name="🎲 Tärningsslag som kommer användas",
                value="\n".join(trait_preview),
                inline=False
            )
        
        embed.set_footer(text="Karaktärsdrag är valfria och påverkar främst rollspelet")
        
        await ctx.send(embed=embed)
        return embed
    
    async def handle_input(self, ctx: commands.Context, session: 'CharacterSession', 
                          input_text: str, *args) -> Tuple[bool, Optional[str]]:
        """
        Handle user input for traits step.
        
        Args:
            ctx: Discord command context
            session: Current character creation session
            input_text: User's input text
            *args: Additional arguments (unused)
            
        Returns:
            Tuple of (success: bool, error_message: Optional[str])
        """
        input_lower = input_text.strip().lower()
        
        if input_lower in ['slå', 'roll', 'framslå', 'sla']:
            # Roll character traits
            await self._roll_character_traits(ctx, session)
            return False, "Traits generated, awaiting confirmation"
            
        elif input_lower in ['hoppa', 'skip', 'hoppaöver', 'hoppa över']:
            # Skip character traits
            session.data['karaktärsdrag'] = {}
            
            embed = discord.Embed(
                title="⏭️ Hoppar över karaktärsdrag",
                description="Karaktärsdrag har hoppats över.",
                color=discord.Color.orange()
            )
            embed.add_field(
                name="ℹ️ Information",
                value="Du kan alltid lägga till karaktärsdrag manuellt senare.",
                inline=False
            )
            
            await ctx.send(embed=embed)
            return True, None
            
        elif input_lower in ['fortsätt', 'behåll', 'continue'] and 'karaktärsdrag' in session.temp_data:
            # Confirm rolled traits
            session.data['karaktärsdrag'] = session.temp_data.get('karaktärsdrag', {})
            session.temp_data.clear()
            
            embed = discord.Embed(
                title="✅ Karaktärsdrag sparade",
                description="Dina karaktärsdrag har sparats!",
                color=discord.Color.green()
            )
            
            await ctx.send(embed=embed)
            return True, None
            
        elif input_lower in ['slåom', 'ändra', 'reroll'] and 'karaktärsdrag' in session.temp_data:
            # Re-roll traits
            await ctx.send("🔄 Slår om karaktärsdrag...")
            await self._roll_character_traits(ctx, session)
            return False, "Traits re-rolled, awaiting confirmation"
        
        else:
            # Invalid input - show appropriate help based on current state
            if 'karaktärsdrag' in session.temp_data:
                error_msg = (
                    "❌ Ogiltigt kommando. Använd:\\n\\n"
                    "• **fortsätt** - Behåll nuvarande karaktärsdrag\\n"
                    "• **slåom** - Slå om karaktärsdragen"
                )
            else:
                error_msg = (
                    "❌ Ogiltigt kommando. Använd:\\n\\n"
                    "• **slå** - Slå fram karaktärsdrag\\n"
                    "• **hoppa** - Hoppa över karaktärsdrag"
                )
            
            await ctx.send(error_msg)
            return False, "Invalid input"
    
    async def _roll_character_traits(self, ctx: commands.Context, session: 'CharacterSession'):
        """Roll character traits based on race."""
        race = session.data.get('folkslag', '')
        trait_formulas = self._get_trait_dice_for_race(race, session)
        
        if not trait_formulas:
            await ctx.send(f"❌ Karaktärsdrag inte implementerat för folkslag: {race}")
            return
        
        # Roll all traits
        results = {}
        for trait_name in self.trait_names:
            dice_formula = trait_formulas.get(trait_name, '3d6')
            roll_result = self._roll_dice_formula(dice_formula)
            results[trait_name] = {
                'value': roll_result,
                'dice': dice_formula
            }
        
        # Display results
        race_display = self._get_race_display_name(race, session)
        
        embed = discord.Embed(
            title="🎭 Dina Karaktärsdrag",
            description=f"Karaktärsdrag för **{race_display}**:",
            color=discord.Color.blue()
        )
        
        # Add traits in a nice format
        for trait_name in self.trait_names:
            data = results[trait_name]
            embed.add_field(
                name=f"✨ {trait_name.capitalize()}",
                value=f"**{data['value']}** ({data['dice']})",
                inline=True
            )
        
        # Add explanation
        embed.add_field(
            name="📖 Förklaring",
            value=(
                "Värdena representerar din karaktärs grundläggande personlighetsdrag. "
                "Högre värden betyder starkare uttryck av det draget."
            ),
            inline=False
        )
        
        # Save in temp_data for confirmation
        session.temp_data['karaktärsdrag'] = results
        
        embed.set_footer(text="!chargen fortsätt för att behålla, !chargen slåom för att slå om")
        await ctx.send(embed=embed)
    
    def _get_trait_dice_for_race(self, race: str, session: 'CharacterSession' = None) -> Dict[str, str]:
        """Get trait dice formulas for a specific race."""
        if not race:
            return {}
        
        race_lower = race.lower()
        
        # Special handling for Thalamur Citizens - use Thalasker traits
        if (session and session.data.get('thalamur_special') == 'thalasker_medborgare' and 
            session.data.get('thalamur_samhällsklass') == 'Medborgare'):
            race_lower = 'thalasker'
        
        # Try to find exact match for race/nationality
        for race_key, traits in self.trait_formulas.items():
            if race_key in race_lower or race_lower in race_key:
                return traits
        
        # If race not found in mapping - use 3d6 for all traits (default)
        return {
            'lojalitet': '3d6',
            'heder': '3d6',
            'amor': '3d6',
            'aggression': '3d6',
            'tro': '3d6',
            'generositet': '3d6'
        }
    
    def _get_race_display_name(self, race: str, session: 'CharacterSession' = None) -> str:
        """Get the display name for a race (handles special cases)."""
        if not race:
            return 'Okänt'
        
        # Special display for Thalamur Citizens
        if (session and session.data.get('thalamur_special') == 'thalasker_medborgare' and 
            session.data.get('thalamur_samhällsklass') == 'Medborgare'):
            return 'Thalasker'
        
        return race.capitalize()
    
    def _roll_dice_formula(self, formula: str) -> int:
        """Roll dice according to formula like '3d6', '2d6+6', '1d6+12'."""
        # Parse formula like "XdY+Z" or "XdY"
        match = re.match(r'(\d+)d(\d+)(?:\+(\d+))?', formula.lower())
        if not match:
            return 0
        
        num_dice = int(match.group(1))
        dice_sides = int(match.group(2))
        modifier = int(match.group(3)) if match.group(3) else 0
        
        # Roll the dice
        rolls = self.dice_roller.roll_multiple_d6(num_dice) if dice_sides == 6 else [random.randint(1, dice_sides) for _ in range(num_dice)]
        total = sum(rolls) + modifier
        return total
    
    def validate_prerequisites(self, session: 'CharacterSession') -> Tuple[bool, Optional[str]]:
        """Validate that prerequisites for this step are met."""
        required_fields = ['kön', 'hemland', 'folkslag', 'ålder', 'kultur', 'attribut']
        
        for field in required_fields:
            if field not in session.data:
                return False, f"{field} must be selected before traits"
        
        return True, None
    
    def get_summary(self, session: 'CharacterSession') -> str:
        """Get a summary of the character traits."""
        traits = session.data.get('karaktärsdrag', {})
        
        if not traits:
            return "**Karaktärsdrag:** Inga genererade"
        
        # Count non-empty traits
        trait_count = len([t for t in traits.values() if t.get('value', 0) > 0])
        return f"**Karaktärsdrag:** {trait_count} drag genererade"
    
    def validate_data(self, session: 'CharacterSession') -> bool:
        """Validate that traits data exists and is valid."""
        # Traits are optional, so missing data is valid
        if 'karaktärsdrag' not in session.data:
            return True
        
        traits = session.data.get('karaktärsdrag', {})
        
        # Empty traits dictionary is valid (player skipped)
        if not traits:
            return True
        
        # If traits exist, validate structure
        for trait_name, trait_data in traits.items():
            if not isinstance(trait_data, dict):
                return False
            if 'value' not in trait_data:
                return False
        
        return True
    
    def can_skip(self, session: 'CharacterSession') -> bool:
        """Traits step can always be skipped."""
        return True
    
    def get_help_text(self) -> str:
        """Get detailed help text for this step."""
        return (
            f"**Steg {self.step_number}: Karaktärsdrag**\\n\\n"
            "Generera valfria karaktärsdrag för djupare rollspel:\\n\\n"
            "**Karaktärsdrag:**\\n"
            "• **Lojalitet** - Trohet mot familj, vänner, organisationer\\n"
            "• **Heder** - Respekt för ära och moral\\n"
            "• **Amor** - Kärlek, passion, romantik\\n"
            "• **Aggression** - Våldsamhet, konfliktbenägenhet\\n"
            "• **Tro** - Religiös eller filosofisk övertygelse\\n"
            "• **Generositet** - Givmildhet, hjälpsamhet\\n"
            "• **Rykte** - Hur andra ser dig\\n\\n"
            "**Funktionalitet:**\\n"
            "• Olika folkslag har olika tärningsslag\\n"
            "• Högre värden = starkare uttryck av draget\\n"
            "• Påverkar rollspel, inte mekanik\\n"
            "• Helt valfritt att använda\\n\\n"
            "**Kommandon:**\\n"
            "• **slå** - Generera karaktärsdrag\\n"
            "• **hoppa** - Hoppa över steget\\n"
            "• **fortsätt** - Behåll genererade drag\\n"
            "• **slåom** - Generera nya drag"
        )
    
    def get_trait_names(self) -> List[str]:
        """Get list of all trait names."""
        return self.trait_names.copy()
    
    def get_race_formulas(self, race: str) -> Dict[str, str]:
        """Get trait formulas for a specific race."""
        return self._get_trait_dice_for_race(race)
    
    def has_custom_formulas(self, race: str) -> bool:
        """Check if a race has custom trait formulas."""
        race_lower = race.lower()
        
        for race_key in self.trait_formulas.keys():
            if race_key in race_lower or race_lower in race_key:
                return True
        
        return False