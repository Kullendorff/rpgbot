"""
Background Steps for Character Creation

This module handles background generation (Steps 12-14):
- Step 12: Background roll count calculation
- Step 13: Main background table rolls
- Step 14: Specific background events processing

The background system:
- Calculates rolls based on race, age, and attributes
- Performs rolls on main background table
- Processes specific background events one by one
- Supports Thalamur family placement bonuses
- Handles reroll and confirmation options
"""

import discord
from discord.ext import commands
from typing import Optional, Tuple, List, Dict, Any
from pathlib import Path
import json
import random

from .base_step import BaseStep
from ..utils.dice_roller import CharacterDiceRoller


class BackgroundStep(BaseStep):
    """Steps 12-14: Complete background generation system."""
    
    def __init__(self, embed_factory, data_dir: Optional[Path] = None, table_processor=None):
        """
        Initialize the background step.
        
        Args:
            embed_factory: The embed factory for creating Discord embeds
            data_dir: Optional data directory path
            table_processor: Table processor for complex dice rolls
        """
        super().__init__(step_name="bakgrundslag_antal", step_number=12)
        self.embed_factory = embed_factory
        self.data_dir = data_dir or self._get_default_data_dir()
        self.dice_roller = CharacterDiceRoller()
        self.table_processor = table_processor
        
        # Current step in the background process
        self.current_background_step = 12  # Will be updated based on session state
        
        # Load background tables
        self.background_tables = self._load_background_tables()
        
    def _get_default_data_dir(self) -> Path:
        """Get default data directory."""
        script_dir = Path(__file__).parent
        project_root = script_dir.parent.parent.parent
        return project_root / 'data' / 'character_tables'
    
    def _load_background_tables(self) -> Dict[str, Any]:
        """Load background table data."""
        try:
            bg_file = self.data_dir / 'huvudbakgrund.json'
            if bg_file.exists():
                with open(bg_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading background tables: {e}")
        return {}
    
    async def execute(self, ctx: commands.Context, session: 'CharacterSession') -> discord.Embed:
        """
        Execute the appropriate background step based on session state.
        
        Args:
            ctx: Discord command context
            session: Current character creation session
            
        Returns:
            Discord embed displaying the step
        """
        # Determine which background step we're on
        if 'antal_bakgrundslag' not in session.data:
            return await self._execute_step_12_count(ctx, session)
        elif 'huvudbakgrund_results' not in session.data:
            return await self._execute_step_13_main_table(ctx, session)
        else:
            return await self._execute_step_14_events(ctx, session)
    
    async def _execute_step_12_count(self, ctx: commands.Context, session: 'CharacterSession') -> discord.Embed:
        """Step 12: Calculate number of background rolls."""
        self.current_background_step = 12
        self.step_name = "bakgrundslag_antal"
        self.step_number = 12
        
        # Get required data
        race = session.data.get('folkslag')
        age = session.data.get('ålder')
        attributes = session.data.get('attribut', {})
        
        if not race or not age or not attributes:
            embed = self.embed_factory.error_message(
                session.user_id,
                "❌ Error: Race, age and attributes must be set first."
            )
            await ctx.send(embed=embed)
            return embed
        
        # Calculate attribute sum
        attribute_sum = sum(attributes.values())
        
        # Calculate background rolls
        background_rolls = self._calculate_background_rolls(race, age, attribute_sum)
        
        # Create result embed
        embed = self.embed_factory.admin_message(
            session.user_id, 
            f"🎲 Steg {self.step_number}/{session.max_steps}: Antal Bakgrundsslag", 
            "Beräknar hur många bakgrundsslag du får:"
        )
        
        # Show calculation components
        base_rolls = self._get_base_rolls_for_race(race)
        embed.add_field(
            name="Grundslag (Ras)",
            value=f"**{race.capitalize()}:** {base_rolls} slag",
            inline=True
        )
        
        # Attribute sum bonus
        attr_bonus = 0
        if attribute_sum < 70: 
            attr_bonus = 2
        elif 71 <= attribute_sum <= 85: 
            attr_bonus = 1
        
        embed.add_field(
            name="Attributbonus",
            value=f"Summa {attribute_sum}: +{attr_bonus} slag",
            inline=True
        )
        
        # Age bonus  
        age_bonus = 0
        if 31 <= age <= 45: age_bonus = 1
        elif 46 <= age <= 60: age_bonus = 2
        elif 61 <= age <= 80: age_bonus = 3
        elif 81 <= age <= 100: age_bonus = 4
        elif age > 100: age_bonus = 5
        
        embed.add_field(
            name="Åldersbonus",
            value=f"{age} år: +{age_bonus} slag",
            inline=True
        )
        
        embed.add_field(
            name="**Totalt Antal Bakgrundsslag**",
            value=f"🎲 **{background_rolls} slag** på huvudbakgrundstabellen",
            inline=False
        )
        
        embed.set_footer(text="Skriv: !chargen fortsätt för att fortsätta")
        await ctx.send(embed=embed)
        
        # Save the roll count
        session.data['antal_bakgrundslag'] = background_rolls
        
        return embed
    
    async def _execute_step_13_main_table(self, ctx: commands.Context, session: 'CharacterSession') -> discord.Embed:
        """Step 13: Roll on main background table."""
        self.current_background_step = 13
        self.step_name = "huvudbakgrund"
        self.step_number = 13
        
        antal_slag = session.data.get('antal_bakgrundslag')
        
        if not antal_slag:
            embed = self.embed_factory.error_message(
                session.user_id,
                "❌ Error: Background roll count must be calculated first."
            )
            await ctx.send(embed=embed)
            return embed
        
        # Check if player has family placement bonuses
        if self._has_placeable_background_rolls(session):
            return await self._handle_family_based_placement(ctx, session, antal_slag)
        else:
            # Standard random rolls
            return await self._perform_random_background_rolls(ctx, session, antal_slag)
    
    async def _execute_step_14_events(self, ctx: commands.Context, session: 'CharacterSession') -> discord.Embed:
        """Step 14: Process specific background events."""
        self.current_background_step = 14
        self.step_name = "bakgrundshändelser"
        self.step_number = 14
        
        results = session.data.get('huvudbakgrund_results')
        
        if not results:
            embed = self.embed_factory.error_message(
                session.user_id,
                "❌ Error: No background results to process."
            )
            await ctx.send(embed=embed)
            return embed
        
        # Check if we've started processing rolls
        if 'current_background_index' not in session.data:
            session.data['current_background_index'] = 0
            session.data['processed_background_results'] = []
        
        current_index = session.data['current_background_index']
        
        # Check if we're done with all rolls
        if current_index >= len(results):
            return await self._show_final_background_summary(ctx, session)
        
        # Get current roll to process
        current_result = results[current_index]
        result_type = current_result['result_key']
        
        await ctx.send(f"🎲 Processing roll {current_index + 1}/{len(results)}: **{current_result['description']}**")
        
        # Roll on specific table based on result
        detailed_result = await self._roll_specific_background_table(ctx, session, result_type, current_result)
        
        if detailed_result:
            # Show result with keep/reroll options
            return await self._show_background_result_with_options(ctx, session, detailed_result, current_result)
        else:
            # If no specific table found, continue
            await ctx.send(f"⚠️ No specific table for {result_type}, skipping...")
            await self._advance_to_next_background_roll(ctx, session)
            return await self.execute(ctx, session)  # Recursive call to continue
    
    def _calculate_background_rolls(self, race: str, age: int, attribute_sum: int) -> int:
        """Calculate number of background rolls (same logic as character_creation.py)."""
        base_rolls = self._get_base_rolls_for_race(race)
        total_rolls = base_rolls
        
        # Attribute sum bonus
        if attribute_sum < 70: 
            total_rolls += 2
        elif 71 <= attribute_sum <= 85: 
            total_rolls += 1
        
        # Age bonus
        if 31 <= age <= 45: total_rolls += 1
        elif 46 <= age <= 60: total_rolls += 2
        elif 61 <= age <= 80: total_rolls += 3
        elif 81 <= age <= 100: total_rolls += 4
        elif age > 100: total_rolls += 5
        
        return total_rolls
    
    def _get_base_rolls_for_race(self, race: str) -> int:
        """Return base number of background rolls for different races."""
        base_rolls = {
            "vanarer": 7, "cirefalier": 6, "adasier": 7, "darkener": 7, "lalaster": 7,
            "misslor": 4,
            "ghor": 5, "roghan": 5, "zolod": 5, "drezin": 5,  # dwarves
            "marnakh": 5, "bazirk": 5, "frakk": 5,  # tiraks  
            "sanari": 5, "thism": 5, "kiriya": 5, "henea": 5, "learam": 5, "pyar": 5  # elves
        }
        
        race_lower = race.lower()
        return base_rolls.get(race_lower, 7)  # Default for humans
    
    def _has_placeable_background_rolls(self, session: 'CharacterSession') -> bool:
        """Check if player has family-based placement opportunities."""
        thalamur_att_data = session.data.get('thalamur_ätt_data')
        if not thalamur_att_data:
            return False
        
        bonusar = thalamur_att_data.get('bonusar', {})
        placera_slag = bonusar.get('placera_slag', [])
        return len(placera_slag) > 0
    
    async def _handle_family_based_placement(self, ctx: commands.Context, session: 'CharacterSession', antal_slag: int) -> discord.Embed:
        """Handle family-based placement of background rolls."""
        thalamur_att_data = session.data.get('thalamur_ätt_data', {})
        bonusar = thalamur_att_data.get('bonusar', {})
        placera_slag = bonusar.get('placera_slag', [])
        att_namn = thalamur_att_data.get('titel', 'Unknown family')
        
        embed = self.embed_factory.admin_message(
            session.user_id, 
            f"🎯 Step {self.step_number}/{session.max_steps}: Family-based Background Placement", 
            f"As member of **{att_namn}** you can place some of your {antal_slag} background rolls:"
        )
        
        # Show available placements
        placement_text = []
        for i, kategori in enumerate(placera_slag, 1):
            kategori_display = kategori.replace('_', ' ').title()
            placement_text.append(f"{i}. **{kategori_display}**")
        
        embed.add_field(
            name="🏛️ Available placements:",
            value="\\n".join(placement_text),
            inline=False
        )
        
        embed.add_field(
            name="📝 Commands",
            value=(
                "• **auto** - Automatic random rolls\\n"
                "• **1** - Place in first category\\n"
                "• **2** - Place in second category\\n"
                "• etc."
            ),
            inline=False
        )
        
        embed.set_footer(text="Choose placement or use 'auto' for random rolls")
        await ctx.send(embed=embed)
        
        return embed
    
    async def _perform_random_background_rolls(self, ctx: commands.Context, session: 'CharacterSession', antal_slag: int) -> discord.Embed:
        """Perform random background rolls on main table."""
        if not self.background_tables:
            embed = self.embed_factory.error_message(
                session.user_id,
                "❌ Error: Could not load background tables."
            )
            await ctx.send(embed=embed)
            return embed
        
        embed = self.embed_factory.admin_message(
            session.user_id,
            f"🎲 Steg {self.step_number}/{session.max_steps}: Huvudbakgrundstabell",
            f"Slår {antal_slag} gånger på huvudbakgrundstabellen..."
        )
        await ctx.send(embed=embed)
        
        results = []
        bakgrund_data = self.background_tables.get('bakgrundstabeller', {})
        main_table = bakgrund_data.get('huvudtabell', {})
        ranges = main_table.get('ranges', {})
        
        if not ranges:
            embed = self.embed_factory.error_message(
                session.user_id,
                "❌ Error: No background table ranges found."
            )
            await ctx.send(embed=embed)
            return embed
        
        # Perform rolls
        for i in range(antal_slag):
            roll = random.randint(1, 100)
            result = self._find_table_result(ranges, roll)
            
            if result:
                results.append({
                    'roll': roll,
                    'result_key': result.get('result', 'unknown'),
                    'description': result.get('description', 'Unknown result'),
                    'table_type': result.get('table_type', ''),
                    'special_rule': result.get('special_rule', '')
                })
            else:
                results.append({
                    'roll': roll,
                    'result_key': 'error',
                    'description': f'No result found for roll {roll}',
                    'table_type': '',
                    'special_rule': ''
                })
        
        # Save results
        session.data['huvudbakgrund_results'] = results
        
        # Display results
        return await self._display_background_results(ctx, session, results)
    
    async def _display_background_results(self, ctx: commands.Context, session: 'CharacterSession', results: List[Dict[str, Any]]) -> discord.Embed:
        """Display the background roll results."""
        embed = discord.Embed(
            title="🎲 Huvudbakgrundstabell Resultat",
            description=f"Resultat från {len(results)} bakgrundsslag:",
            color=discord.Color.blue()
        )
        
        for i, result in enumerate(results, 1):
            embed.add_field(
                name=f"Roll {i}: {result['roll']}",
                value=result['description'],
                inline=False
            )
        
        embed.add_field(
            name="📋 Nästa Steg",
            value="Dessa resultat kommer nu att processas individuellt för detaljerade händelser.",
            inline=False
        )
        
        embed.set_footer(text="Skriv: !chargen fortsätt för att börja processa händelser")
        await ctx.send(embed=embed)
        
        return embed
    
    def _find_table_result(self, ranges: Dict[str, Any], roll: int) -> Dict[str, Any]:
        """Find result from a table based on dice roll."""
        for range_key, result_data in ranges.items():
            if self._is_roll_in_range(roll, range_key):
                return result_data
        
        return {
            "result": "error",
            "description": f"No result found for roll {roll}",
            "table_type": ""
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
    
    async def _roll_specific_background_table(self, ctx: commands.Context, session: 'CharacterSession', 
                                           result_type: str, original_result: Dict) -> Dict[str, Any]:
        """Roll on specific background table based on main table result."""
        table_mapping = {
            'fysiska_egenskaper': 'physical_traits.json',
            'mentala_egenskaper': 'mental_traits.json', 
            'övernaturliga_egenskaper': 'supernatural_trait.json',
            'nackdelar': 'disadvantages.json',
            'föremål_ägodelar': 'agodelar.json',
            'förmögenhet': 'formogenhet.json',
            'händelser': self._get_events_table_for_race(session),
            'börd': self._get_birth_table_for_race(session),
            'extra_slag_familj': 'familj/familj_ovr.json',
            'egendom': 'egendom.json'
        }
        
        table_file = table_mapping.get(result_type)
        if not table_file:
            return None
        
        try:
            # Load the table
            table_data = self._load_background_subtable(table_file)
            if not table_data:
                return None
            
            # Special handling for egendom tables
            if result_type == 'egendom':
                return await self._roll_egendom_table(session, table_data, original_result)
            
            # Roll on the table
            roll = random.randint(1, 100)
            result_data = self._find_subtable_result_with_conditions(table_data, roll, session)
            
            return {
                'table_type': result_type,
                'table_file': table_file,
                'roll': roll,
                'result': result_data.get('result', 'Unknown'),
                'description': result_data.get('description', 'No description available'),
                'result_key': result_data.get('result', 'unknown'),
                'original_main_roll': original_result
            }
            
        except Exception as e:
            print(f"Error rolling on table {result_type}: {e}")
            return None
    
    async def _show_background_result_with_options(self, ctx: commands.Context, session: 'CharacterSession',
                                                 detailed_result: Dict, original_result: Dict) -> discord.Embed:
        """Show background result with keep/reroll options."""
        table_display_name = self._get_table_display_name(detailed_result['table_type'])
        
        embed = discord.Embed(
            title=f"🎯 {table_display_name}",
            description=f"**Roll:** {detailed_result['roll']}",
            color=discord.Color.green()
        )
        
        embed.add_field(
            name="📋 Resultat",
            value=detailed_result['result'],
            inline=False
        )
        
        embed.add_field(
            name="📖 Beskrivning",
            value=detailed_result['description'],
            inline=False
        )
        
        embed.add_field(
            name="✅ Alternativ",
            value=(
                "`!chargen fortsätt` - Behåll detta resultat\\n"
                "`!chargen slåom` - Slå om på samma tabell\\n"
                "`!chargen hoppa` - Hoppa över detta resultat"
            ),
            inline=False
        )
        
        # Store current result for input handling
        session.temp_data['current_detailed_result'] = detailed_result
        
        embed.set_footer(text=f"Processing result {session.data.get('current_background_index', 0) + 1}")
        await ctx.send(embed=embed)
        
        return embed
    
    def _get_table_display_name(self, table_type: str) -> str:
        """Return readable name for table types."""
        display_names = {
            'fysiska_egenskaper': 'Fysiska Egenskaper',
            'mentala_egenskaper': 'Mentala Egenskaper',
            'övernaturliga_egenskaper': 'Övernaturliga Egenskaper',
            'nackdelar': 'Nackdelar',
            'föremål_ägodelar': 'Föremål & Ägodelar',
            'förmögenhet': 'Förmögenhet',
            'händelser': 'Händelser',
            'börd': 'Börd',
            'egendom': 'Egendom'
        }
        return display_names.get(table_type, table_type.replace('_', ' ').title())
    
    async def _advance_to_next_background_roll(self, ctx: commands.Context, session: 'CharacterSession'):
        """Advance to the next background roll."""
        session.data['current_background_index'] = session.data.get('current_background_index', 0) + 1
        
        # Clear temp data
        if 'current_detailed_result' in session.temp_data:
            del session.temp_data['current_detailed_result']
    
    async def _show_final_background_summary(self, ctx: commands.Context, session: 'CharacterSession') -> discord.Embed:
        """Show final summary of all background events."""
        processed_results = session.data.get('processed_background_results', [])
        
        embed = discord.Embed(
            title="📜 Background Events Summary",
            description="Complete summary of your character's background:",
            color=discord.Color.gold()
        )
        
        if processed_results:
            for i, result in enumerate(processed_results, 1):
                embed.add_field(
                    name=f"{i}. {result['category']} (Roll: {result['roll']})",
                    value=result['result'],
                    inline=False
                )
        else:
            embed.add_field(
                name="No Events",
                value="No background events were processed.",
                inline=False
            )
        
        embed.add_field(
            name="✅ Complete",
            value="Background generation completed! Your character's history is now established.",
            inline=False
        )
        
        embed.set_footer(text="Write: !chargen fortsätt to continue to character summary")
        await ctx.send(embed=embed)
        
        return embed
    
    async def handle_input(self, ctx: commands.Context, session: 'CharacterSession', 
                          input_text: str, *args) -> Tuple[bool, Optional[str]]:
        """
        Handle user input for background steps.
        
        Args:
            ctx: Discord command context
            session: Current character creation session
            input_text: User's input text
            *args: Additional arguments
            
        Returns:
            Tuple of (success: bool, error_message: Optional[str])
        """
        input_lower = input_text.strip().lower()
        
        # Determine current background step
        current_step = self._get_current_background_step(session)
        
        if current_step == 12:  # Background count
            return await self._handle_step_12_input(ctx, session, input_lower)
        elif current_step == 13:  # Main background table
            return await self._handle_step_13_input(ctx, session, input_lower)
        elif current_step == 14:  # Background events
            return await self._handle_step_14_input(ctx, session, input_lower)
        else:
            await ctx.send("❌ Unknown background step state.")
            return False, "Unknown step state"
    
    def _get_current_background_step(self, session: 'CharacterSession') -> int:
        """Determine which background step we're currently on."""
        if 'antal_bakgrundslag' not in session.data:
            return 12
        elif 'huvudbakgrund_results' not in session.data:
            return 13
        elif 'current_background_index' not in session.data:
            # We have results but haven't started processing them yet - still on step 13
            return 13
        elif session.data.get('current_background_index', 0) < len(session.data.get('huvudbakgrund_results', [])):
            return 14
        else:
            return 15  # Done with background
    
    async def _handle_step_12_input(self, ctx: commands.Context, session: 'CharacterSession', input_lower: str) -> Tuple[bool, Optional[str]]:
        """Handle input for step 12 (background count)."""
        if input_lower in ['fortsätt', 'continue', 'next']:
            return True, None
        else:
            await ctx.send("❌ Write `!chargen fortsätt` to continue to background rolls.")
            return False, "Invalid input for step 12"
    
    async def _handle_step_13_input(self, ctx: commands.Context, session: 'CharacterSession', input_lower: str) -> Tuple[bool, Optional[str]]:
        """Handle input for step 13 (main background table)."""
        if input_lower in ['fortsätt', 'continue', 'next', 'auto']:
            return True, None
        elif input_lower.isdigit():
            # Handle family placement selection
            choice = int(input_lower)
            thalamur_att_data = session.data.get('thalamur_ätt_data', {})
            placera_slag = thalamur_att_data.get('bonusar', {}).get('placera_slag', [])
            
            if 1 <= choice <= len(placera_slag):
                await ctx.send(f"✅ Placing background roll in category {choice}")
                # This would implement the actual placement logic
                return True, None
            else:
                await ctx.send(f"❌ Invalid choice. Choose 1-{len(placera_slag)} or 'auto'.")
                return False, "Invalid placement choice"
        else:
            await ctx.send("❌ Write `!chargen fortsätt` or choose a placement number.")
            return False, "Invalid input for step 13"
    
    async def _handle_step_14_input(self, ctx: commands.Context, session: 'CharacterSession', input_lower: str) -> Tuple[bool, Optional[str]]:
        """Handle input for step 14 (background events)."""
        # Check if we're processing individual background rolls
        current_index = session.data.get('current_background_index', -1)
        total_results = len(session.data.get('huvudbakgrund_results', []))
        
        if current_index < total_results:
            if input_lower in ['fortsätt', 'behåll', 'keep']:
                # Keep current result and advance
                current_result = session.temp_data.get('current_detailed_result')
                if current_result:
                    # Add to processed results
                    processed_results = session.data.get('processed_background_results', [])
                    processed_results.append({
                        'category': self._get_table_display_name(current_result['table_type']),
                        'roll': current_result['roll'],
                        'result': current_result['result'],
                        'table_file': current_result['table_file']
                    })
                    session.data['processed_background_results'] = processed_results
                    
                    await ctx.send(f"✅ Keeping result: **{current_result['result']}**")
                    await self._advance_to_next_background_roll(ctx, session)
                    
                    # Continue processing or finish
                    if session.data['current_background_index'] >= len(session.data['huvudbakgrund_results']):
                        return True, None  # Done with all background events
                    else:
                        # Continue with next event
                        await self.execute(ctx, session)
                        return False, "Processing next background event"
                else:
                    await ctx.send("❌ Inget resultat att behålla.")
                    return False, "No current result"
                    
            elif input_lower in ['slåom', 'slå om', 'reroll']:
                # Reroll on same table
                current_result = session.temp_data.get('current_detailed_result')
                if current_result:
                    await ctx.send("🔄 Rerolling...")
                    # Get current original result
                    results = session.data.get('huvudbakgrund_results', [])
                    current_index = session.data['current_background_index']
                    original_result = results[current_index]
                    
                    # Roll again on same table
                    detailed_result = await self._roll_specific_background_table(ctx, session, current_result['table_type'], original_result)
                    if detailed_result:
                        await self._show_background_result_with_options(ctx, session, detailed_result, original_result)
                        return False, "Rerolled, waiting for new choice"
                    else:
                        await ctx.send("❌ Could not reroll, skipping...")
                        await self._advance_to_next_background_roll(ctx, session)
                        return False, "Reroll failed, advancing"
                else:
                    await ctx.send("❌ No result to reroll.")
                    return False, "No current result"
                    
            elif input_lower in ['hoppa', 'skip']:
                # Skip this result
                await ctx.send("⏭️ Skipping this result...")
                await self._advance_to_next_background_roll(ctx, session)
                
                # Continue processing or finish
                if session.data['current_background_index'] >= len(session.data['huvudbakgrund_results']):
                    return True, None  # Done with all background events
                else:
                    # Continue with next event
                    await self.execute(ctx, session)
                    return False, "Skipped, processing next background event"
            else:
                await ctx.send(
                    "❌ Invalid command. Use:\n"
                    "• **fortsätt** - Keep current result\n"
                    "• **slåom** - Reroll on same table\n"
                    "• **hoppa** - Skip this result"
                )
                return False, "Invalid input for step 14"
        else:
            # All background events processed, ready to continue
            if input_lower in ['fortsätt', 'continue', 'next']:
                return True, None
            else:
                await ctx.send("❌ Write `!chargen fortsätt` to continue to character summary.")
                return False, "Invalid input for step 14 completion"
    
    def validate_prerequisites(self, session: 'CharacterSession') -> Tuple[bool, Optional[str]]:
        """Validate that prerequisites for this step are met."""
        required_fields = ['kön', 'hemland', 'folkslag', 'ålder', 'kultur', 'attribut', 'familj']
        
        for field in required_fields:
            if field not in session.data:
                return False, f"{field} must be selected before background generation"
        
        return True, None
    
    def get_summary(self, session: 'CharacterSession') -> str:
        """Get a summary of the background generation."""
        current_step = self._get_current_background_step(session)
        
        if current_step == 12:
            return "**Background:** Roll count not calculated"
        elif current_step == 13:
            rolls = session.data.get('antal_bakgrundslag', 0)
            return f"**Background:** {rolls} rolls calculated"
        elif current_step == 14:
            results = session.data.get('huvudbakgrund_results', [])
            processed = session.data.get('processed_background_results', [])
            return f"**Background:** {len(processed)}/{len(results)} events processed"
        else:
            processed = session.data.get('processed_background_results', [])
            return f"**Background:** {len(processed)} events completed"
    
    def validate_data(self, session: 'CharacterSession') -> bool:
        """Validate that background data exists and is valid."""
        current_step = self._get_current_background_step(session)
        
        if current_step <= 12:
            return True  # No data required yet
        elif current_step <= 13:
            return 'antal_bakgrundslag' in session.data
        else:
            return ('antal_bakgrundslag' in session.data and 
                   'huvudbakgrund_results' in session.data)
    
    def can_skip(self, session: 'CharacterSession') -> bool:
        """Background generation cannot be skipped."""
        return False
    
    def _load_background_subtable(self, filename: str) -> Dict[str, Any]:
        """Load a background subtable from file."""
        try:
            filepath = self.data_dir / filename
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading {filename}: {e}")
            return None
    
    def _find_subtable_result_with_conditions(self, table_data: Dict[str, Any], roll: int, session: 'CharacterSession') -> Dict[str, str]:
        """Find result from subtable and handle conditional logic."""
        # First try to find the result in the table
        result_entry = self._find_table_entry(table_data, roll)
        
        if not result_entry:
            return {
                'result': 'error',
                'description': f'No result for roll {roll}'
            }
        
        # Check if it's a conditional result
        if 'conditions' in result_entry:
            return self._resolve_conditional_result(result_entry, session)
        
        # Regular result
        return {
            'result': result_entry.get('result', 'unknown'),
            'description': result_entry.get('description', f'Result for roll {roll}')
        }
    
    def _find_table_entry(self, table_data: Dict[str, Any], roll: int) -> Dict[str, Any]:
        """Find table entry for a given roll."""
        # Handle EON table structure with bakgrundstabeller
        if 'bakgrundstabeller' in table_data:
            for section_name, section_data in table_data['bakgrundstabeller'].items():
                if 'ranges' in section_data:
                    ranges = section_data['ranges']
                    for range_key, range_data in ranges.items():
                        if self._is_roll_in_range(roll, range_key):
                            return range_data
        
        # Direct ranges structure  
        if 'ranges' in table_data:
            ranges = table_data['ranges']
            for range_key, range_data in ranges.items():
                if self._is_roll_in_range(roll, range_key):
                    return range_data
        
        return None
    
    def _resolve_conditional_result(self, result_entry: Dict, session: 'CharacterSession') -> Dict[str, str]:
        """Resolve conditional result based on character data."""
        conditions = result_entry.get('conditions', {})
        folkslag = session.data.get('folkslag', '').lower()
        
        # Check dwarf conditions
        if 'is_dvärg' in conditions and any(dvarg in folkslag for dvarg in ['ghor', 'drezin', 'roghan', 'dvärg']):
            condition_result = conditions['is_dvärg']
            return {
                'result': condition_result.get('result', 'dvärg_result'),
                'description': condition_result.get('description', 'Dvärg-specifikt resultat')
            }
        
        if 'not_dvärg' in conditions and not any(dvarg in folkslag for dvarg in ['ghor', 'drezin', 'roghan', 'dvärg']):
            condition_result = conditions['not_dvärg']
            return {
                'result': condition_result.get('result', 'icke_dvärg_result'),
                'description': condition_result.get('description', 'Icke-dvärg resultat')
            }
        
        # Check noble/knight conditions  
        kultur = session.data.get('kultur', '').lower()
        if 'not_riddare' in conditions and 'adlig' not in kultur:
            condition_result = conditions['not_riddare']
            return {
                'result': condition_result.get('result', 'icke_riddare_result'),
                'description': condition_result.get('description', 'Icke-riddare resultat')
            }
        
        if 'is_riddare' in conditions and 'adlig' in kultur:
            condition_result = conditions['is_riddare']
            return {
                'result': condition_result.get('result', 'riddare_result'),
                'description': condition_result.get('description', 'Riddare resultat')
            }
        
        # Check Cirefalier conditions
        if 'is_cirefalier' in conditions and 'cirefalier' in folkslag:
            condition_result = conditions['is_cirefalier']
            return {
                'result': condition_result.get('result', 'cirefalier_result'),
                'description': condition_result.get('description', 'Cirefalier-specifikt resultat')
            }
            
        if 'not_cirefalier' in conditions and 'cirefalier' not in folkslag:
            condition_result = conditions['not_cirefalier']
            return {
                'result': condition_result.get('result', 'icke_cirefalier_result'),
                'description': condition_result.get('description', 'Icke-cirefalier resultat')
            }
        
        # If no conditions match, return default
        return {
            'result': result_entry.get('result', 'conditional_unresolved'),
            'description': result_entry.get('description', 'Villkor ej uppfyllda - kontakta SL')
        }
    
    def _get_events_table_for_race(self, session: 'CharacterSession') -> str:
        """Choose events table based on race."""
        race = session.data.get('folkslag', '').lower()
        
        # Specific event tables for different races  
        if any(elf in race for elf in ['sanari', 'thism', 'kiriya', 'henea', 'learam', 'pyar']):
            return 'handelser/alver_hand.json'
        elif session.data.get('thalamur_special') == 'thalasker_medborgare':
            return 'handelser/thalask_hand.json'  
        else:
            # Use general events table for all other races (including Cirefalier)
            return 'handelser/ovriga_handelser.json'
    
    def _get_birth_table_for_race(self, session: 'CharacterSession') -> str:
        """Choose birth table based on race."""
        race = session.data.get('folkslag', '').lower()
        
        # Use race-specific birth tables based on available files
        if 'asharier' in race:
            return 'bord/bord_asharier.json'
        elif 'cirefalier' in race:
            return 'bord/bord_cirefalier.json'
        elif session.data.get('thalamur_special') == 'thalasker_medborgare':
            return 'bord/bord_thalask.json'
        elif any(primitive in race for primitive in ['kragg', 'vanarer']):
            return 'bord/bord_primitiva.json'
        else:
            # Use general civilized birth table
            return 'bord/bord_ovr_civ.json'
    
    async def _roll_egendom_table(self, session: 'CharacterSession', table_data: dict, original_result: dict) -> dict:
        """Special handling for egendom (property) tables."""
        # Placeholder - implement specific egendom logic if needed
        roll = random.randint(1, 100)
        result_data = self._find_subtable_result_with_conditions(table_data, roll, session)
        
        return {
            'table_type': 'egendom',
            'table_file': 'egendom.json',
            'roll': roll,
            'result': result_data['description'],
            'result_key': result_data['result'],
            'original_main_roll': original_result
        }
    
    def get_help_text(self) -> str:
        """Get detailed help text for this step."""
        return (
            f"**Steps {self.step_number}-14: Background Generation**\n\n"
            "Complete background generation system:\n\n"
            "**Step 12: Roll Count**\n"
            "• Calculate background rolls based on race, age, attributes\n"
            "• Bonus rolls for low attributes and advanced age\n\n"
            "**Step 13: Main Background Table**\n"
            "• Roll on main background table\n"
            "• Family placement bonuses for Thalamur Citizens\n"
            "• Determine event categories\n\n"
            "**Step 14: Specific Events**\n"
            "• Process each background result individually\n"
            "• Roll on specific tables (traits, items, events)\n"
            "• Keep, reroll, or skip each result\n\n"
            "**Commands:**\n"
            "• **fortsätt** - Continue/keep result\n"
            "• **slåom** - Reroll current result\n"
            "• **hoppa** - Skip current result\n"
            "• **auto** - Automatic placement (step 13)\n\n"
            "Background generation establishes your character's history and special traits."
        )
    
    def covers_steps(self) -> List[int]:
        """This step covers steps 12, 13, and 14."""
        return [12, 13, 14]
    
    def reload_data(self) -> bool:
        """Reload all data files."""
        try:
            self.background_tables = self._load_background_tables()
            return True
        except Exception as e:
            print(f"Error reloading background data: {e}")
            return False