"""
Special Rules Step for Character Creation

This module handles race-specific special rules, primarily focusing on
Cirefalier field disturbances (field störningar) but designed to be
extensible for other racial special rules.
"""

import discord
from discord.ext import commands
from typing import Optional, Tuple, List, Dict, Any
from pathlib import Path
import json
import random

from .base_step import BaseStep
from ..utils.dice_roller import CharacterDiceRoller


class SpecialRulesStep(BaseStep):
    """Step 7: Special racial rules processing."""
    
    def __init__(self, embed_factory, data_dir: Optional[Path] = None):
        """
        Initialize the special rules step.
        
        Args:
            embed_factory: The embed factory for creating Discord embeds
            data_dir: Optional data directory path
        """
        super().__init__(step_name="specialregler", step_number=7)
        self.embed_factory = embed_factory
        self.data_dir = data_dir or self._get_default_data_dir()
        self.dice_roller = CharacterDiceRoller()
        
        # Load field disturbance data for Cirefalier
        self.field_disturbance_data = self._load_field_disturbance_data()
    
    def _get_default_data_dir(self) -> Path:
        """Get default data directory."""
        script_dir = Path(__file__).parent
        project_root = script_dir.parent.parent.parent
        return project_root / 'data' / 'character_tables'
    
    def _load_field_disturbance_data(self) -> Dict[str, Any]:
        """Load Cirefalier field disturbance table from JSON file."""
        disturbance_file = self.data_dir / 'field_storning.json'
        
        if not disturbance_file.exists():
            print(f"Warning: Could not find {disturbance_file}")
            return {}
        
        try:
            with open(disturbance_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading field disturbance data: {e}")
            return {}
    
    async def execute(self, ctx: commands.Context, session: 'CharacterSession') -> discord.Embed:
        """
        Execute the special rules step.
        
        Args:
            ctx: Discord command context
            session: Current character creation session
            
        Returns:
            Discord embed displaying the special rules processing
        """
        race = session.data.get('folkslag', '').lower()
        
        # Check if character is Cirefalier
        if 'cirefalier' in race:
            return await self._handle_cirefalier_field_disturbances(ctx, session)
        else:
            # Skip for all other races
            embed = self.embed_factory.admin_message(
                session.user_id,
                f"⏭️ Steg {self.step_number}/{session.max_steps}: Specialregler",
                f"**{session.data.get('folkslag', 'Ditt folkslag')}** har inga specialregler att hantera."
            )
            
            embed.add_field(
                name="✅ Redo att fortsätta",
                value="Inga särskilda rasegenskaper behöver hanteras för detta folkslag.",
                inline=False
            )
            
            embed.set_footer(text="Steg hoppades över automatiskt")
            
            await ctx.send(embed=embed)
            return embed
    
    async def _handle_cirefalier_field_disturbances(self, ctx: commands.Context, 
                                                   session: 'CharacterSession') -> discord.Embed:
        """Handle Cirefalier field disturbances."""
        if not self.field_disturbance_data:
            embed = self.embed_factory.error_message(
                session.user_id,
                "Fel: Kan inte ladda field-störningsdata för Cirefalier."
            )
            await ctx.send(embed=embed)
            return embed
        
        embed = self.embed_factory.admin_message(
            session.user_id,
            f"🧬 Steg {self.step_number}/{session.max_steps}: Cirefaliers fältstörningar",
            "Som **Cirefalier** kan du ha bio/psykotropiska fältstörningar."
        )
        
        embed.add_field(
            name="🎲 Vad händer nu?",
            value=(
                "Systemet kommer att slå för att avgöra hur många fältstörningar "
                "din karaktär har, och sedan generera de specifika störningarna."
            ),
            inline=False
        )
        
        embed.add_field(
            name="📖 Om fältstörningar",
            value=(
                "Fältstörningar är biologiska/psykiska avvikelser som påverkar "
                "Cirefaliers relation till fältet. De kan vara både fördelar "
                "och nackdelar för din karaktär."
            ),
            inline=False
        )
        
        embed.set_footer(text="Slår för fältstörningar...")
        
        await ctx.send(embed=embed)
        
        # Automatically roll for field disturbances
        await self._roll_field_disturbances(ctx, session)
        
        return embed
    
    async def _roll_field_disturbances(self, ctx: commands.Context, session: 'CharacterSession'):
        """Roll for Cirefalier field disturbances."""
        try:
            # Get the disturbance tables
            disturbance_tables = self.field_disturbance_data.get('störningar_cirefalier', {})
            number_table = disturbance_tables.get('antal_störningar', {})
            
            if not number_table:
                await ctx.send("❌ Fel: Kan inte hitta antal-störnings tabellen.")
                return
            
            # Roll for number of disturbances
            number_roll = self.dice_roller.roll_d100()
            number_result = self._find_table_result(number_table, number_roll)
            
            embed = discord.Embed(
                title="🎲 Antal Fältstörningar",
                description=f"**Slag:** {number_roll}",
                color=discord.Color.blue()
            )
            
            embed.add_field(
                name="📋 Resultat",
                value=number_result.get('description', 'Okänt resultat'),
                inline=False
            )
            
            result_key = number_result.get('result', 'error')
            
            # Handle different results
            if result_key == 'ingen_störning':
                # No disturbances
                session.data['field_storningar'] = []
                embed.add_field(
                    name="✅ Inga störningar",
                    value="Din Cirefalier har inga fältstörningar! 🎉",
                    inline=False
                )
                embed.set_footer(text="Inga fältstörningar. Skriv !chargen fortsätt för nästa steg.")
                
                await ctx.send(embed=embed)
                
            elif result_key == 'roll_twice':
                # Special case: roll twice more
                embed.add_field(
                    name="⚠️ Specialfall",
                    value="Slår två gånger till och adderar resultaten...",
                    inline=False
                )
                await ctx.send(embed=embed)
                
                # TODO: Implement multiple roll logic
                await ctx.send("⚠️ Multi-roll logik inte implementerad än. Tilldelas en störning tillfälligt.")
                await self._roll_actual_disturbances(ctx, session, 1)
                
            else:
                # Determine number of rolls based on result
                num_rolls = self._get_rolls_from_result(result_key)
                
                if num_rolls > 0:
                    embed.add_field(
                        name="🎯 Nästa steg",
                        value=f"Slår nu **{num_rolls}** gång(er) på störningstabellen...",
                        inline=False
                    )
                    await ctx.send(embed=embed)
                    
                    # Roll for actual disturbances
                    await self._roll_actual_disturbances(ctx, session, num_rolls)
                else:
                    # Fallback
                    embed.add_field(
                        name="❓ Okänt resultat",
                        value="Okänt antal störningar, hoppar över...",
                        inline=False
                    )
                    await ctx.send(embed=embed)
                    session.data['field_storningar'] = []
                    
        except Exception as e:
            await ctx.send(f"❌ Fel vid hantering av fältstörningar: {e}")
            # Set empty disturbances and continue
            session.data['field_storningar'] = []
    
    async def _roll_actual_disturbances(self, ctx: commands.Context, 
                                       session: 'CharacterSession', num_rolls: int):
        """Roll for the actual field disturbances."""
        try:
            # Get the disturbance table
            disturbance_tables = self.field_disturbance_data.get('störningar_cirefalier', {})
            disturbance_table = disturbance_tables.get('störning', {})
            
            if not disturbance_table:
                await ctx.send("❌ Fel: Kan inte hitta störningstabellen.")
                session.data['field_storningar'] = []
                return
            
            results = []
            
            # Roll for each disturbance
            for i in range(num_rolls):
                roll = self.dice_roller.roll_d100()
                result = self._find_table_result(disturbance_table, roll)
                
                results.append({
                    'roll': roll,
                    'result_key': result.get('result', 'unknown'),
                    'description': result.get('description', 'Okänd störning'),
                    'name': result.get('name', f'Störning {i+1}')
                })
            
            # Display all disturbances
            embed = discord.Embed(
                title="🧬 Dina Fältstörningar",
                description=f"**Resultat från {num_rolls} slag:**",
                color=discord.Color.purple()
            )
            
            for i, result in enumerate(results, 1):
                embed.add_field(
                    name=f"💫 Störning {i} (Slag: {result['roll']})",
                    value=result['description'],
                    inline=False
                )
            
            # Save results
            session.data['field_storningar'] = results
            
            embed.set_footer(text="Fältstörningar genererade. Skriv !chargen fortsätt för nästa steg.")
            await ctx.send(embed=embed)
            
        except Exception as e:
            await ctx.send(f"❌ Fel vid slående av fältstörningar: {e}")
            session.data['field_storningar'] = []
    
    def _find_table_result(self, table: Dict[str, Any], roll: int) -> Dict[str, Any]:
        """Find result from a table based on dice roll."""
        ranges = table.get('ranges', {})
        
        for range_key, result_data in ranges.items():
            if self._is_roll_in_range(roll, range_key):
                return result_data
        
        return {
            "result": "error",
            "description": f"Inget resultat hittades för slag {roll}",
            "name": "Fel"
        }
    
    def _is_roll_in_range(self, roll: int, range_str: str) -> bool:
        """Check if a dice roll is within a range string."""
        try:
            range_str = str(range_str).strip()
            if "-" in range_str:
                start, end = map(int, range_str.split("-"))
                return start <= roll <= end
            else:
                return roll == int(range_str)
        except (ValueError, AttributeError):
            return False
    
    def _get_rolls_from_result(self, result_key: str) -> int:
        """Get number of rolls from result key."""
        result_mapping = {
            'en_störning': 1,
            'två_störningar': 2,
            'tre_störningar': 3,
            'en_storning': 1,  # Alternative spelling
            'tva_storningar': 2,  # Alternative spelling
            'tre_storningar': 3   # Alternative spelling
        }
        return result_mapping.get(result_key, 0)
    
    async def handle_input(self, ctx: commands.Context, session: 'CharacterSession', 
                          input_text: str, *args) -> Tuple[bool, Optional[str]]:
        """
        Handle user input for special rules step.
        
        Args:
            ctx: Discord command context
            session: Current character creation session
            input_text: User's input text
            *args: Additional arguments (unused)
            
        Returns:
            Tuple of (success: bool, error_message: Optional[str])
        """
        input_lower = input_text.strip().lower()
        
        if input_lower in ['fortsätt', 'continue', 'next', 'behåll']:
            # Continue to next step
            race = session.data.get('folkslag', '').lower()
            
            if 'cirefalier' in race and 'field_storningar' not in session.data:
                # Cirefalier but no field disturbances processed yet
                await ctx.send("❌ Fältstörningar måste hanteras först.")
                return False, "Field disturbances not processed"
            
            return True, None
            
        elif input_lower in ['slåom', 'reroll', 'ändra']:
            # Re-roll field disturbances (only for Cirefalier)
            race = session.data.get('folkslag', '').lower()
            
            if 'cirefalier' in race:
                await ctx.send("🔄 Slår om fältstörningar...")
                await self._roll_field_disturbances(ctx, session)
                return False, "Re-rolling disturbances"
            else:
                await ctx.send("❌ Inga specialregler att slå om för detta folkslag.")
                return False, "No special rules to reroll"
        
        else:
            # Invalid input
            race = session.data.get('folkslag', '').lower()
            
            if 'cirefalier' in race:
                error_msg = (
                    "❌ Ogiltigt kommando. Använd:\\n\\n"
                    "• **fortsätt** - Fortsätt med nuvarande störningar\\n"
                    "• **slåom** - Slå om fältstörningar"
                )
            else:
                error_msg = (
                    "❌ Ogiltigt kommando. Använd:\\n\\n"
                    "• **fortsätt** - Gå till nästa steg"
                )
            
            await ctx.send(error_msg)
            return False, "Invalid input"
    
    def validate_prerequisites(self, session: 'CharacterSession') -> Tuple[bool, Optional[str]]:
        """Validate that prerequisites for this step are met."""
        required_fields = ['kön', 'hemland', 'folkslag', 'ålder', 'kultur', 'attribut']
        
        for field in required_fields:
            if field not in session.data:
                return False, f"{field} must be selected before special rules"
        
        return True, None
    
    def get_summary(self, session: 'CharacterSession') -> str:
        """Get a summary of the special rules processing."""
        race = session.data.get('folkslag', 'Okänt')
        
        if 'cirefalier' in race.lower():
            disturbances = session.data.get('field_storningar', [])
            if not disturbances:
                return "**Specialregler:** Inga fältstörningar"
            else:
                return f"**Specialregler:** {len(disturbances)} field-störning(ar)"
        else:
            return "**Specialregler:** Inga tillämpliga"
    
    def validate_data(self, session: 'CharacterSession') -> bool:
        """Validate that special rules data exists and is valid."""
        race = session.data.get('folkslag', '').lower()
        
        if 'cirefalier' in race:
            # Cirefalier must have field_storningar (even if empty list)
            return 'field_storningar' in session.data
        else:
            # Other races don't need special data
            return True
    
    def can_skip(self, session: 'CharacterSession') -> bool:
        """Most races can skip special rules, but Cirefalier cannot."""
        race = session.data.get('folkslag', '').lower()
        return 'cirefalier' not in race
    
    def get_help_text(self) -> str:
        """Get detailed help text for this step."""
        return (
            f"**Steg {self.step_number}: Specialregler**\\n\\n"
            "Hanterar rasspecifika specialregler och egenskaper:\\n\\n"
            "**Cirefalier:**\\n"
            "• **Fältstörningar** - Bio/psykotropiska avvikelser\\n"
            "• Påverkar relation till fältet\\n"
            "• Kan vara fördelar eller nackdelar\\n\\n"
            "**Andra folkslag:**\\n"
            "• Inga specialregler att hantera för tillfället\\n"
            "• Steg hoppas över automatiskt\\n\\n"
            "**Kommandon:**\\n"
            "• **fortsätt** - Gå vidare till nästa steg\\n"
            "• **slåom** - Slå om fältstörningar (endast Cirefalier)"
        )
    
    def get_race_special_rules(self, race: str) -> List[str]:
        """Get list of special rules for a race."""
        race_lower = race.lower()
        
        if 'cirefalier' in race_lower:
            return ["Fältstörningar"]
        else:
            return []
    
    def has_special_rules(self, race: str) -> bool:
        """Check if a race has special rules."""
        return len(self.get_race_special_rules(race)) > 0
    
    def reload_field_disturbance_data(self) -> bool:
        """Reload field disturbance data from file."""
        try:
            self.field_disturbance_data = self._load_field_disturbance_data()
            return len(self.field_disturbance_data) > 0
        except Exception as e:
            print(f"Error reloading field disturbance data: {e}")
            return False