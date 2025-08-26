"""
Attributes Step for Character Creation

This module handles the attributes generation step where the player chooses
a dice rolling method (3d6, 4d6, or 2d6+9) and generates their character's
base attributes, then applies racial modifiers.
"""

import discord
from discord.ext import commands
from typing import Optional, Tuple, List, Dict, Any
from pathlib import Path
import json

from .base_step import BaseStep
from ..utils.dice_roller import CharacterDiceRoller


class AttributesStep(BaseStep):
    """Step 6: Attributes generation with racial modifiers."""
    
    def __init__(self, embed_factory, data_dir: Optional[Path] = None):
        """
        Initialize the attributes step.
        
        Args:
            embed_factory: The embed factory for creating Discord embeds
            data_dir: Optional data directory path
        """
        super().__init__(step_name="attribut", step_number=6)
        self.embed_factory = embed_factory
        self.data_dir = data_dir or self._get_default_data_dir()
        self.dice_roller = CharacterDiceRoller()
        
        # Attribute names in order
        self.attribute_names = ["STY", "TÅL", "RÖR", "PER", "PSY", "VIL", "BIL", "SYN", "HÖR"]
        
        # Available generation methods
        self.generation_methods = {
            '1': '3d6',
            '2': '4d6', 
            '3': '2d6+9',
            '3d6': '3d6',
            '4d6': '4d6',
            '2d6+9': '2d6+9'
        }
        
        # Load racial modifiers
        self.racial_modifiers = self._load_racial_modifiers()
    
    def _get_default_data_dir(self) -> Path:
        """Get default data directory."""
        script_dir = Path(__file__).parent
        project_root = script_dir.parent.parent.parent
        return project_root / 'data' / 'character_tables'
    
    def _load_racial_modifiers(self) -> Dict[str, Any]:
        """Load racial attribute modifiers from JSON file."""
        modifiers_file = self.data_dir / 'folkslag' / 'attribute_modifiers.json'
        
        if not modifiers_file.exists():
            print(f"Warning: Could not find {modifiers_file}")
            return {}
        
        try:
            with open(modifiers_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading attribute modifiers: {e}")
            return {}
    
    async def execute(self, ctx: commands.Context, session: 'CharacterSession') -> discord.Embed:
        """
        Execute the attributes generation step.
        
        Args:
            ctx: Discord command context
            session: Current character creation session
            
        Returns:
            Discord embed displaying the attribute generation options
        """
        embed = self.embed_factory.admin_message(
            session.user_id,
            f"🎲 Steg {self.step_number}/{session.max_steps}: Grundattribut",
            "Välj metod för att generera rollpersonens grundattribut:"
        )
        
        embed.add_field(
            name="🎯 Tillgängliga metoder",
            value=(
                "**1. 3d6** - Standard (Genomsnitt ~10-11 per attribut)\n"
                "**2. 4d6** - Höga värden (Bästa 3 av 4 tärningar)\n"
                "**3. 2d6+9** - Heroisk (Genomsnitt ~16 per attribut)"
            ),
            inline=False
        )
        
        embed.add_field(
            name="📊 Attribut som genereras",
            value="**STY** (Styrka), **TÅL** (Tålighet), **RÖR** (Rörlighet)\n"
                  "**PER** (Perception), **PSY** (Psyke), **VIL** (Vilja)\n"
                  "**BIL** (Bildning), **SYN** (Syn), **HÖR** (Hörsel)",
            inline=False
        )
        
        embed.add_field(
            name="📝 Kommandon",
            value=(
                "• **1** eller **3d6** - Standard metod\n"
                "• **2** eller **4d6** - Höga värden\n"
                "• **3** eller **2d6+9** - Heroisk metod"
            ),
            inline=False
        )
        
        # Show current race for context
        race = session.data.get('folkslag', 'Ej valt')
        if race != 'Ej valt':
            embed.add_field(
                name="⚡ Rasmodifierare",
                value=f"Attribut kommer automatiskt modifieras av **{race}** rasegenskaper",
                inline=False
            )
        
        embed.set_footer(text="Exempel: !chargen 1, !chargen 4d6")
        
        await ctx.send(embed=embed)
        return embed
    
    async def handle_input(self, ctx: commands.Context, session: 'CharacterSession', 
                          input_text: str, *args) -> Tuple[bool, Optional[str]]:
        """
        Handle user input for attribute generation method selection.
        
        Args:
            ctx: Discord command context
            session: Current character creation session
            input_text: User's input text
            *args: Additional arguments (unused)
            
        Returns:
            Tuple of (success: bool, error_message: Optional[str])
        """
        input_text = input_text.strip().lower()
        
        # Validate method choice
        if input_text not in self.generation_methods:
            error_msg = (
                "❌ Ogiltigt val. Använd:\n\n"
                "• **1** eller **3d6** - Standard\n"
                "• **2** eller **4d6** - Höga värden\n"
                "• **3** eller **2d6+9** - Heroisk"
            )
            await ctx.send(error_msg)
            return False, "Invalid method choice"
        
        # Get the method
        method = self.generation_methods[input_text]
        
        try:
            # Generate base attributes
            base_attributes = self._generate_attributes(method)
            
            # Get race for modifiers
            race = session.data.get('folkslag')
            if not race:
                await ctx.send("❌ Fel: Folkslag måste vara satt först.")
                return False, "Race not set"
            
            # Apply racial modifiers
            final_attributes = self._apply_racial_modifiers(base_attributes, race, session)
            
            # Calculate statistics
            attribute_sum = sum(final_attributes.values())
            chock = (final_attributes["STY"] + final_attributes["TÅL"] + final_attributes["VIL"]) // 3
            
            # Create result embed
            embed = discord.Embed(
                title="🎲 Genererade Attribut",
                description=f"Grundattribut med **{method.upper()}** metod och **{race}** rasmodifierare:",
                color=discord.Color.green()
            )
            
            # Show attributes with changes
            attr_display = []
            for attr in self.attribute_names:
                base_value = base_attributes[attr]
                final_value = final_attributes[attr]
                
                if final_value != base_value:
                    # Show change from racial modifier
                    change = final_value - base_value
                    change_str = f" ({base_value}{change:+d})"
                    attr_display.append(f"**{attr}:** {final_value}{change_str}")
                else:
                    attr_display.append(f"**{attr}:** {final_value}")
            
            embed.add_field(
                name="📊 Attributvärden",
                value="\n".join(attr_display),
                inline=True
            )
            
            embed.add_field(
                name="📈 Summering",
                value=f"**Totalsumma:** {attribute_sum}\n**Chockvärde:** {chock}",
                inline=True
            )
            
            # Store the results
            session.data['grundattribut'] = base_attributes
            session.data['attribut'] = final_attributes
            session.data['attribut_metod'] = method.upper()
            session.data['attribut_summa'] = attribute_sum
            session.data['chockvärde'] = chock
            
            embed.set_footer(text="Attribut sparade. Skriv !chargen fortsätt för nästa steg.")
            await ctx.send(embed=embed)
            
            return True, None
            
        except Exception as e:
            await ctx.send(f"❌ Fel vid generering av attribut: {e}")
            return False, f"Generation error: {e}"
    
    def _generate_attributes(self, method: str) -> Dict[str, int]:
        """
        Generate base attributes using the specified method.
        
        Args:
            method: Generation method ('3d6', '4d6', or '2d6+9')
            
        Returns:
            Dictionary of attribute name to value
        """
        attributes = {}
        
        for attr in self.attribute_names:
            if method == "3d6":
                attributes[attr] = sum(self.dice_roller.roll_multiple_d6(3))
            elif method == "4d6":
                # Roll 4d6, keep best 3
                rolls = sorted(self.dice_roller.roll_multiple_d6(4), reverse=True)
                attributes[attr] = sum(rolls[:3])
            elif method == "2d6+9":
                attributes[attr] = sum(self.dice_roller.roll_multiple_d6(2)) + 9
            else:
                raise ValueError(f"Unknown method: {method}")
        
        return attributes
    
    def _apply_racial_modifiers(self, attributes: Dict[str, int], race: str, 
                              session: 'CharacterSession') -> Dict[str, int]:
        """
        Apply racial modifiers to base attributes.
        
        Args:
            attributes: Base attributes dictionary
            race: Character's race
            session: Character session (for special cases)
            
        Returns:
            Modified attributes dictionary
        """
        if not self.racial_modifiers:
            print(f"No racial modifiers loaded, returning base attributes")
            return attributes.copy()
        
        # Normalize race name
        race_lower = race.lower()
        
        # Special handling for Thalamur Citizens - they use Thalasker modifiers
        if (session.data.get('thalamur_special') == 'thalasker_medborgare' and 
            session.data.get('thalamur_samhällsklass') == 'Medborgare'):
            race_lower = 'thalasker'
        
        # Find racial modifiers
        race_mods = None
        for category, races in self.racial_modifiers.items():
            if race_lower in races:
                race_mods = races[race_lower]
                break
        
        if not race_mods:
            print(f"No modifiers found for race: {race}")
            return attributes.copy()
        
        # Apply modifiers
        modified_attributes = attributes.copy()
        for attr, modifier in race_mods.items():
            if attr in modified_attributes:
                modified_attributes[attr] += modifier
                modified_attributes[attr] = max(1, modified_attributes[attr])  # Minimum 1
        
        return modified_attributes
    
    def validate_prerequisites(self, session: 'CharacterSession') -> Tuple[bool, Optional[str]]:
        """Validate that prerequisites for this step are met."""
        required_fields = ['kön', 'hemland', 'folkslag', 'ålder', 'kultur']
        
        for field in required_fields:
            if field not in session.data:
                return False, f"{field} must be selected before attributes"
        
        return True, None
    
    def get_summary(self, session: 'CharacterSession') -> str:
        """Get a summary of the generated attributes."""
        if 'attribut' not in session.data:
            return "**Attribut:** Ej genererade"
        
        attributes = session.data['attribut']
        method = session.data.get('attribut_metod', 'Okänd')
        total = session.data.get('attribut_summa', 0)
        
        return f"**Attribut:** {method} metod (Summa: {total})"
    
    def validate_data(self, session: 'CharacterSession') -> bool:
        """Validate that attribute data exists and is valid."""
        required_keys = ['attribut', 'grundattribut', 'attribut_metod']
        
        for key in required_keys:
            if key not in session.data:
                return False
        
        # Validate all attributes exist
        attributes = session.data.get('attribut', {})
        return all(attr in attributes for attr in self.attribute_names)
    
    def can_skip(self, session: 'CharacterSession') -> bool:
        """Attributes generation cannot be skipped."""
        return False
    
    def get_help_text(self) -> str:
        """Get detailed help text for this step."""
        return (
            f"**Steg {self.step_number}: Grundattribut**\\n\\n"
            "Generera rollpersonens nio grundattribut med vald metod:\\n\\n"
            "**Metoder:**\\n"
            "• **3d6** - Standard EON-metod, ger genomsnitt ~10-11\\n"
            "• **4d6** - Höga värden, slå 4 tärningar och ta bästa 3\\n"
            "• **2d6+9** - Heroisk, ger genomsnitt ~16 per attribut\\n\\n"
            "**Attribut:**\\n"
            "• **STY** (Styrka) - Fysisk kraft\\n"
            "• **TÅL** (Tålighet) - Uthållighet och hälsa\\n"
            "• **RÖR** (Rörlighet) - Snabbhet och smidighet\\n"
            "• **PER** (Perception) - Uppmärksamhet\\n"
            "• **PSY** (Psyke) - Mental stabilitet\\n"
            "• **VIL** (Vilja) - Viljestyrka\\n"
            "• **BIL** (Bildning) - Kunskap och lärdom\\n"
            "• **SYN** (Syn) - Synförmåga\\n"
            "• **HÖR** (Hörsel) - Hörselförmåga\\n\\n"
            "Attribut modifieras automatiskt av ditt valda folkslag."
        )
    
    def get_method_description(self, method: str) -> str:
        """Get description of a generation method."""
        descriptions = {
            '3d6': 'Standard EON-metod (3-18, genomsnitt ~10-11)',
            '4d6': 'Höga värden (3-18, högre genomsnitt)',
            '2d6+9': 'Heroisk metod (11-21, genomsnitt ~16)'
        }
        return descriptions.get(method, f'Okänd metod: {method}')
    
    def get_racial_modifiers_for_race(self, race: str) -> Dict[str, int]:
        """Get racial modifiers for a specific race."""
        if not self.racial_modifiers:
            return {}
        
        race_lower = race.lower()
        for category, races in self.racial_modifiers.items():
            if race_lower in races:
                return races[race_lower].copy()
        
        return {}
    
    def reload_racial_modifiers(self) -> bool:
        """Reload racial modifiers from file."""
        try:
            self.racial_modifiers = self._load_racial_modifiers()
            return len(self.racial_modifiers) > 0
        except Exception as e:
            print(f"Error reloading racial modifiers: {e}")
            return False