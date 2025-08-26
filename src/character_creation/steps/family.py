"""
Family Steps for Character Creation

This module handles family background generation (Steps 9-11):
- Step 9: Family background generation and confirmation
- Step 10: Family tables (skipped automatically)  
- Step 11: Parents (skipped automatically)

The family system generates complete family backgrounds including:
- Basic family structure (parents, siblings)
- Family profession based on culture
- Special family tables (especially Thalasker Citizens)
- Race-specific family elements (Elf households, Dwarf social class)
"""

import discord
from discord.ext import commands
from typing import Optional, Tuple, List, Dict, Any
from pathlib import Path
import json
import random

from .base_step import BaseStep
from ..utils.dice_roller import CharacterDiceRoller


class FamilyStep(BaseStep):
    """Steps 9-11: Complete family background generation."""
    
    def __init__(self, embed_factory, data_dir: Optional[Path] = None, bg_generator=None, table_processor=None):
        """
        Initialize the family step.
        
        Args:
            embed_factory: The embed factory for creating Discord embeds
            data_dir: Optional data directory path
            bg_generator: Background generator for basic family
            table_processor: Table processor for dice rolls
        """
        super().__init__(step_name="familjebakgrund", step_number=9)
        self.embed_factory = embed_factory
        self.data_dir = data_dir or self._get_default_data_dir()
        self.dice_roller = CharacterDiceRoller()
        self.bg_generator = bg_generator
        self.table_processor = table_processor
        
        # Load data
        self.culture_data = self._load_culture_data()
        self.thalask_family_data = {}  # Loaded on demand
        
    def _get_default_data_dir(self) -> Path:
        """Get default data directory."""
        script_dir = Path(__file__).parent
        project_root = script_dir.parent.parent.parent
        return project_root / 'data' / 'character_tables'
    
    def _load_culture_data(self) -> Dict[str, Any]:
        """Load culture data for family profession generation."""
        try:
            culture_file = self.data_dir / 'familj' / 'huvudnaring.json'
            if culture_file.exists():
                with open(culture_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get('familj_huvudnäring', {})
        except Exception as e:
            print(f"Error loading culture data: {e}")
        return {}
    
    async def execute(self, ctx: commands.Context, session: 'CharacterSession') -> discord.Embed:
        """
        Execute the family background generation step.
        
        Args:
            ctx: Discord command context
            session: Current character creation session
            
        Returns:
            Discord embed displaying the family generation
        """
        embed = self.embed_factory.admin_message(
            session.user_id,
            f"👨‍👩‍👧‍👦 Steg {self.step_number}/{session.max_steps}: Familjebakgrund",
            "Genererar komplett familjebakgrund för din rollperson..."
        )
        
        embed.add_field(
            name="🎲 Vad händer nu?",
            value=(
                "Systemet kommer att generera:\n"
                "• **Grundläggande familj** - Föräldrar och syskon\n"
                "• **Familjens huvudnäring** - Baserat på din kultur\n"
                "• **Specialtabeller** - Rasspecifika familjeegenskaper\n"
                "• **Övriga detaljer** - Hushåll, mentorer, samhällsklass"
            ),
            inline=False
        )
        
        # Get required data
        race = session.data.get('folkslag', '')
        age = session.data.get('ålder', 25)
        culture = session.data.get('kultur', '')
        homeland = session.data.get('hemland', '')
        
        embed.add_field(
            name="📊 Baserat på dina val",
            value=(
                f"**Folkslag:** {race}\n"
                f"**Ålder:** {age} år\n"
                f"**Kultur:** {culture}\n"
                f"**Hemland:** {homeland}"
            ),
            inline=False
        )
        
        embed.set_footer(text="Genererar familj...")
        await ctx.send(embed=embed)
        
        # Generate complete family system
        try:
            complete_family = await self._generate_complete_family_system(
                session, race, age, culture, homeland
            )
            
            # Store in session
            session.data['familj'] = complete_family
            
            # Display the generated family
            await self._display_complete_family(ctx, session, complete_family)
            
            return embed
            
        except Exception as e:
            error_embed = self.embed_factory.error_message(
                session.user_id,
                f"❌ Fel vid generering av familj: {e}"
            )
            await ctx.send(embed=error_embed)
            return error_embed
    
    async def _generate_complete_family_system(self, session: 'CharacterSession', 
                                             race: str, age: int, culture: str, 
                                             homeland: str) -> Dict[str, Any]:
        """Generate complete family system with all components."""
        complete_family = {}
        
        # 1. BASIC FAMILY (using AutomaticBackgroundGenerator)
        if self.bg_generator:
            basic_family = self.bg_generator.generate_complete_background(race, age)
            complete_family['basic'] = self._convert_family_background_to_dict(basic_family)
        else:
            complete_family['basic'] = {'error': 'Background generator not available'}
        
        # 2. FAMILY PROFESSION (based on culture)
        profession_result = self._generate_family_profession(culture)
        complete_family['profession'] = profession_result
        
        # 3. FAMILY SPECIAL TABLES
        family_special = self._generate_family_special_tables(race, culture, session)
        complete_family['special'] = family_special
        
        # 4. RACE-SPECIFIC ADDITIONS
        race_specific = self._generate_race_specific_family(race, age)
        complete_family['race_specific'] = race_specific
        
        return complete_family
    
    def _generate_family_profession(self, culture: str) -> Dict[str, Any]:
        """Generate family profession based on culture from step 5."""
        if not self.culture_data or culture not in self.culture_data:
            return {"error": f"Could not find culture data for: {culture}"}
        
        culture_table = self.culture_data[culture]
        ranges = culture_table.get('ranges', {})
        
        if not ranges:
            return {"error": f"No professions found for culture: {culture}"}
        
        # Roll 1d100 for profession
        roll = random.randint(1, 100)
        
        # Find matching result
        for range_key, range_data in ranges.items():
            if self._is_roll_in_range(roll, range_key):
                profession = range_data.get('profession', 'Unknown')
                skills = range_data.get('skills', [])
                special_rule = range_data.get('special_rule', '')
                skill_bonus = culture_table.get('skill_bonus', '1d6+1')
                
                return {
                    'roll': roll,
                    'profession': profession,
                    'skills': skills,
                    'skill_bonus': skill_bonus,
                    'special_rule': special_rule,
                    'table_title': culture_table.get('titel', culture)
                }
        
        return {"error": f"No result for roll {roll} in {culture}"}
    
    def _generate_family_special_tables(self, race: str, culture: str, session: 'CharacterSession' = None) -> Dict[str, Any]:
        """Generate family special tables."""
        # Check if Thalamur Thalasker Citizen
        if session and session.data.get('thalamur_special') == 'thalasker_medborgare':
            return self._generate_thalask_family_table(session)
        
        # Standard family tables for other races/cultures (placeholder)
        return {
            'economic_status': 'Medelklass ekonomi',
            'family_trait': 'Familjen är känd för sin heder',
            'note': 'Standardfamiljetabeller att implementeras senare'
        }
    
    def _generate_thalask_family_table(self, session: 'CharacterSession') -> Dict[str, Any]:
        """Generate Thalaskic family table for Citizens."""
        # Load Thalaskic family table if not already loaded
        if not self.thalask_family_data:
            try:
                thalask_file = self.data_dir / 'familj' / 'familj_thalask.json'
                with open(thalask_file, 'r', encoding='utf-8') as f:
                    self.thalask_family_data = json.load(f)
            except FileNotFoundError:
                return {"error": "Could not load familj_thalask.json"}
        
        family_table = self.thalask_family_data.get('familjetabeller', {}).get('thalasker_medborgare', {})
        if not family_table:
            return {"error": "Thalasker Citizen table not found"}
        
        # Roll 1d100 on the table
        roll = random.randint(1, 100)
        ranges = family_table.get('ranges', {})
        
        for range_key, range_data in ranges.items():
            if self._is_roll_in_range(roll, range_key):
                result = {
                    'roll': roll,
                    'result_key': range_data.get('result', ''),
                    'description': range_data.get('description', ''),
                    'table_title': family_table.get('titel', 'Thalaskic Family'),
                    'source': 'familj_thalask.json'
                }
                
                # Handle subtables
                if range_data.get('has_subtable') and 'subtable' in range_data:
                    subtable_result = self._roll_on_subtable(range_data['subtable'])
                    result['subtable_result'] = subtable_result
                
                # Handle special rules
                special_rule = range_data.get('special_rule', '')
                if special_rule:
                    result['special_rule'] = special_rule
                    result = self._apply_thalask_special_rule(result, special_rule, session)
                
                # Handle skill bonuses
                skill_bonus = range_data.get('skill_bonus', '')
                if skill_bonus:
                    result['skill_bonus'] = skill_bonus
                    self._apply_skill_bonus_to_session(session, skill_bonus)
                
                return result
        
        return {"error": f"No result for roll {roll} in Thalaskic family table"}
    
    def _apply_thalask_special_rule(self, result: Dict[str, Any], special_rule: str, 
                                  session: 'CharacterSession') -> Dict[str, Any]:
        """Apply special rules from Thalaskic family table."""
        if special_rule == 'roll_on_formogenhet_and_egendom_tables':
            # Very rich family - extra rolls on wealth and property
            result['extra_rolls'] = {
                'formogenhet': 'Free roll on wealth table',
                'egendom': 'Free roll on property table',
                'note': 'Family owns property, character owns wealth'
            }
        elif special_rule == 'roll_on_overnaturliga_egenskaper_r1-37':
            # Adopted with supernatural abilities
            result['supernatural_ability'] = 'Roll on Supernatural Properties (R1-37)'
        elif special_rule == 'giftermal_svarare_ob2t6':
            # Hereditary illness - harder marriage
            result['marriage_penalty'] = 'Marriage two levels harder (+Ob2T6)'
        elif special_rule == 'roll_twice_and_combine':
            # Roll twice and combine results
            second_roll = self._generate_thalask_family_table(session)
            result['second_result'] = second_roll
        
        return result
    
    def _apply_skill_bonus_to_session(self, session: 'CharacterSession', skill_bonus: str):
        """Apply skill bonus from family table to session."""
        # Save skill bonus for later use
        if 'familj_skill_bonuses' not in session.data:
            session.data['familj_skill_bonuses'] = []
        
        session.data['familj_skill_bonuses'].append({
            'source': 'Thalaskic family table',
            'bonus': skill_bonus
        })
    
    def _roll_on_subtable(self, subtable: Dict[str, Any]) -> Dict[str, Any]:
        """Roll on a subtable."""
        roll = random.randint(1, 100)
        ranges = subtable.get('ranges', {})
        
        for range_key, range_data in ranges.items():
            if self._is_roll_in_range(roll, range_key):
                return {
                    'roll': roll,
                    'result_key': range_data.get('result', ''),
                    'description': range_data.get('description', ''),
                    'special_rule': range_data.get('special_rule', '')
                }
        
        return {"error": f"No subtable result for roll {roll}"}
    
    def _generate_race_specific_family(self, race: str, age: int) -> Dict[str, Any]:
        """Generate race-specific family aspects."""
        race_specific = {}
        
        # ELF-SPECIFIC: Household + Mentor
        if race.lower() in ['sanari', 'thism', 'kiriya', 'henea', 'learam', 'pyar']:
            race_specific['household'] = self._generate_elf_household()
            race_specific['mentor'] = self._generate_elf_mentor_details()
        
        # DWARF-SPECIFIC: Social class
        elif race.lower() in ['ghor', 'roghan', 'zolod', 'drezin']:
            race_specific['social_class'] = self._generate_dwarf_social_class()
        
        # TIRAK-SPECIFIC: Clan structure (placeholder)
        elif race.lower() in ['marnakh', 'bazirk', 'frakk']:
            race_specific['clan_info'] = {'note': 'Tirak clan structure to be implemented later'}
        
        return race_specific
    
    def _generate_elf_household(self) -> Dict[str, Any]:
        """Generate elf household with skill bonus."""
        # Simple example - this would be read from tables
        households = [
            {'name': 'Aethel', 'skills': ['etickett', 'bokhållning']},
            {'name': 'Catharion', 'skills': ['etickett', 'bokhållning']},  
            {'name': 'Dorthann', 'skills': ['hantverk', 'värdera']},
            {'name': 'Galindreth', 'skills': ['historia', 'språk']},
        ]
        
        selected = random.choice(households)
        return {
            'name': selected['name'],
            'skills': selected['skills'],
            'bonus': 'ob1T6+1'
        }
    
    def _generate_elf_mentor_details(self) -> Dict[str, Any]:
        """Generate elf mentor with skill bonus."""
        personalities = ['Serious', 'Friendly', 'Stern', 'Wise', 'Eccentric', 'Patient']
        skills = ['besvärjelse', 'ockultism', 'bibliotekskunskap', 'historia']
        
        return {
            'personality': random.choice(personalities),
            'skills': random.sample(skills, 2),  # Choose 2 skills
            'bonus': '1T6+4'
        }
    
    def _generate_dwarf_social_class(self) -> Dict[str, Any]:
        """Generate dwarf social class with attribute effects."""
        social_classes = [
            {'name': 'Miner', 'attributes': {'STY': 1, 'PER': -1}},
            {'name': 'Craftsman', 'attributes': {'BIL': 1, 'STY': 1}},
            {'name': 'Merchant', 'attributes': {'PSY': 1, 'VIL': 1}},
            {'name': 'Warrior nobility', 'attributes': {'STY': 2, 'VIL': 1}},
        ]
        
        selected = random.choice(social_classes)
        return {
            'name': selected['name'],
            'attribute_effects': selected['attributes']
        }
    
    async def _display_complete_family(self, ctx: commands.Context, session: 'CharacterSession', complete_family: Dict[str, Any]):
        """Display the complete family background as unified embeds."""
        
        # Build complete summary
        summary_parts = []
        
        # 1. BASIC FAMILY
        basic = complete_family.get('basic')
        if basic:
            basic_summary = self._format_family_dict_summary(basic)
            summary_parts.append("📅 **GRUNDLÄGGANDE FAMILJ**")
            summary_parts.append(basic_summary)
        
        # 2. FAMILY PROFESSION
        profession = complete_family.get('profession', {})
        if profession and 'profession' in profession:
            summary_parts.append(f"\n💼 **FAMILJENS HUVUDNÄRING**")
            summary_parts.append(f"Familjen arbetar som **{profession['profession']}** (Slag: {profession['roll']})")
            if profession.get('skills'):
                skills_text = ", ".join(profession['skills'])
                summary_parts.append(f"Färdigheter: {skills_text} (Bonus: {profession.get('skill_bonus', '1d6+1')})")
            if profession.get('special_rule'):
                summary_parts.append(f"Specialregel: {profession['special_rule']}")
        
        # 3. FAMILY SPECIAL TABLES
        special = complete_family.get('special', {})
        if special:
            if special.get('source') == 'familj_thalask.json':
                # THALASKIC FAMILY TABLES
                summary_parts.append(f"\n🏛️ **THALASKIC FAMILY**")
                summary_parts.append(f"**{special.get('table_title', 'Thalaskic Family')}** (Roll: {special.get('roll', '?')})")
                
                # Main result
                result_key = special.get('result_key', '').replace('_', ' ').title()
                summary_parts.append(f"**{result_key}**")
                summary_parts.append(special.get('description', ''))
                
                # Subtable result
                if 'subtable_result' in special:
                    subtable = special['subtable_result']
                    subtable_key = subtable.get('result_key', '').replace('_', ' ').title()
                    summary_parts.append(f"└── **{subtable_key}** (Sub-roll: {subtable.get('roll', '?')})")
                    summary_parts.append(f"    {subtable.get('description', '')}")
                
                # Special rules
                if 'extra_rolls' in special:
                    extra = special['extra_rolls']
                    summary_parts.append(f"**Special effect:** {extra.get('note', '')}")
                    summary_parts.append(f"• {extra.get('formogenhet', '')}")
                    summary_parts.append(f"• {extra.get('egendom', '')}")
                
                if 'supernatural_ability' in special:
                    summary_parts.append(f"**Supernatural ability:** {special['supernatural_ability']}")
                
                if 'marriage_penalty' in special:
                    summary_parts.append(f"**Marriage effect:** {special['marriage_penalty']}")
                
                # Second roll (from "roll twice")
                if 'second_result' in special:
                    second = special['second_result']
                    if not second.get('error'):
                        second_key = second.get('result_key', '').replace('_', ' ').title()
                        summary_parts.append(f"\n**Additional result:** {second_key}")
                        summary_parts.append(second.get('description', ''))
            else:
                # STANDARD FAMILY TRAITS (for non-Thalamur races)
                summary_parts.append(f"\n🏠 **FAMILJEEGENSKAPER**")
                if special.get('economic_status'):
                    summary_parts.append(f"**Ekonomisk status:** {special['economic_status']}")
                if special.get('family_trait'):
                    summary_parts.append(f"**Familjens rykte:** {special['family_trait']}")
                if special.get('note'):
                    summary_parts.append(f"*Notering: {special['note']}*")
            
            # Skill bonus
            if 'skill_bonus' in special:
                summary_parts.append(f"**Skill bonus:** {special['skill_bonus']}")
        
        # 4. RACE-SPECIFIC ADDITIONS
        race_specific = complete_family.get('race_specific', {})
        if race_specific:
            summary_parts.append(f"\n🏛️ **RACE-SPECIFIC PROPERTIES**")
            
            # Elf household
            if 'household' in race_specific:
                household = race_specific['household']
                summary_parts.append(f"Household: **{household['name']}**")
                skills_text = ", ".join(household['skills'])
                summary_parts.append(f"Household skills: {skills_text} ({household['bonus']})")
            
            # Elf mentor
            if 'mentor' in race_specific:
                mentor = race_specific['mentor']
                summary_parts.append(f"Mentor: **{mentor['personality']}**")
                skills_text = ", ".join(mentor['skills'])
                summary_parts.append(f"Mentor skills: {skills_text} ({mentor['bonus']})")
            
            # Dwarf social class
            if 'social_class' in race_specific:
                social_class = race_specific['social_class']
                summary_parts.append(f"Social class: **{social_class['name']}**")
                effects = []
                for attr, mod in social_class['attribute_effects'].items():
                    effects.append(f"{attr}{mod:+d}")
                summary_parts.append(f"Attribute effects: {', '.join(effects)}")
        
        # Create and send the family embed
        family_text = "\n".join(summary_parts)
        
        # Split into multiple embeds if too long
        max_length = 1800
        if len(family_text) <= max_length:
            embed = discord.Embed(
                title="👨‍👩‍👧‍👦 Complete Family Background",
                description=family_text,
                color=discord.Color.green()
            )
            embed.add_field(
                name="✅ Bekräftelse",
                value="`!chargen fortsätt` - Fortsätt med denna familjebakgrund\n" +
                      "`!chargen ändra` - Generera ny familjebakgrund",
                inline=False
            )
            embed.set_footer(text="Familjebakgrund genererad")
            await ctx.send(embed=embed)
        else:
            # Split into chunks
            chunks = [family_text[i:i + max_length] 
                     for i in range(0, len(family_text), max_length)]
            
            for i, chunk in enumerate(chunks):
                embed = discord.Embed(
                    title=f"👨‍👩‍👧‍👦 Complete Family Background ({i+1}/{len(chunks)})",
                    description=chunk,
                    color=discord.Color.green()
                )
                
                if i == len(chunks) - 1:  # Last chunk
                    embed.add_field(
                        name="✅ Bekräftelse",
                        value="`!chargen fortsätt` - Fortsätt med denna familjebakgrund\n" +
                              "`!chargen ändra` - Generera ny familjebakgrund",
                        inline=False
                    )
                    embed.set_footer(text="Familjebakgrund genererad")
                
                await ctx.send(embed=embed)
    
    def _format_family_dict_summary(self, family_dict: Dict[str, Any]) -> str:
        """Format family dictionary into readable summary."""
        parts = []
        
        if 'birth_info' in family_dict:
            parts.append(f"Birth: {family_dict['birth_info']}")
        
        if 'father' in family_dict:
            father = family_dict['father']
            age_str = f" (Ålder: {father.get('age', '?')})" if father.get('age') else ""
            parts.append(f"Fader: {father.get('status', 'Okänd')}{age_str}")
        
        if 'mother' in family_dict:
            mother = family_dict['mother']
            age_str = f" (Ålder: {mother.get('age', '?')})" if mother.get('age') else ""
            parts.append(f"Moder: {mother.get('status', 'Okänd')}{age_str}")
        
        if 'siblings' in family_dict:
            siblings = family_dict['siblings']
            if siblings:
                sibling_count = len(siblings)
                parts.append(f"Syskon: {sibling_count}")
        
        return "\n".join(parts) if parts else "Basic family information"
    
    def _convert_family_background_to_dict(self, family_bg) -> Dict[str, Any]:
        """Convert FamilyBackground dataclass to dict for JSON serialization."""
        try:
            # Convert main object to dict
            result = {
                'birth_info': family_bg.birth_info,
                'family_special': family_bg.family_special,
                'mentor_info': family_bg.mentor_info
            }
            
            # Convert siblings list
            result['siblings'] = []
            for sibling in family_bg.siblings:
                result['siblings'].append({
                    'gender': sibling.gender,
                    'age': sibling.age,
                    'relationship': sibling.relationship,
                    'is_illegitimate': sibling.is_illegitimate
                })
            
            # Convert parents
            result['father'] = {
                'status': family_bg.father.status,
                'age': family_bg.father.age,
                'death_cause': family_bg.father.death_cause
            }
            
            result['mother'] = {
                'status': family_bg.mother.status,
                'age': family_bg.mother.age,
                'death_cause': family_bg.mother.death_cause
            }
            
            return result
            
        except Exception as e:
            # Fallback - return basic info
            print(f"Warning: Could not convert FamilyBackground: {e}")
            return {
                'birth_info': 'Family information available',
                'note': 'Details stored in session but conversion failed'
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
    
    async def handle_input(self, ctx: commands.Context, session: 'CharacterSession', 
                          input_text: str, *args) -> Tuple[bool, Optional[str]]:
        """
        Handle user input for family step.
        
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
            if 'familj' not in session.data:
                await ctx.send("❌ Family background must be generated first.")
                return False, "Family background not generated"
            
            return True, None
            
        elif input_lower in ['ändra', 'change', 'reroll', 'ny']:
            # Re-generate family background
            await ctx.send("🔄 Generating new family background...")
            await self.execute(ctx, session)
            return False, "Re-generating family background"
        
        else:
            # Invalid input
            error_msg = (
                "❌ Invalid command. Use:\n\n"
                "• **fortsätt** - Continue with current family background\n"
                "• **ändra** - Generate new family background"
            )
            await ctx.send(error_msg)
            return False, "Invalid input"
    
    def validate_prerequisites(self, session: 'CharacterSession') -> Tuple[bool, Optional[str]]:
        """Validate that prerequisites for this step are met."""
        required_fields = ['kön', 'hemland', 'folkslag', 'ålder', 'kultur', 'attribut']
        
        for field in required_fields:
            if field not in session.data:
                return False, f"{field} must be selected before family background"
        
        return True, None
    
    def get_summary(self, session: 'CharacterSession') -> str:
        """Get a summary of the family background."""
        if 'familj' not in session.data:
            return "**Family:** Not generated"
        
        family = session.data['familj']
        
        # Count family elements
        elements = []
        if family.get('basic'):
            elements.append("basic family")
        if family.get('profession', {}).get('profession'):
            profession = family['profession']['profession']
            elements.append(f"profession: {profession}")
        if family.get('special', {}).get('source'):
            elements.append("special tables")
        if family.get('race_specific'):
            elements.append("race-specific")
        
        return f"**Family:** {', '.join(elements) if elements else 'Generated'}"
    
    def validate_data(self, session: 'CharacterSession') -> bool:
        """Validate that family data exists and is valid."""
        return 'familj' in session.data and isinstance(session.data['familj'], dict)
    
    def can_skip(self, session: 'CharacterSession') -> bool:
        """Family background generation cannot be skipped."""
        return False
    
    def get_help_text(self) -> str:
        """Get detailed help text for this step."""
        return (
            f"**Step {self.step_number}: Family Background**\n\n"
            "Generates complete family background including:\n\n"
            "**Basic Family:**\n"
            "• Parents status and age\n"
            "• Number and details of siblings\n"
            "• Birth circumstances\n\n"
            "**Family Profession:**\n"
            "• Based on chosen culture\n"
            "• Professional skills and bonuses\n"
            "• Special occupational rules\n\n"
            "**Special Tables:**\n"
            "• Thalaskic family tables for Citizens\n"
            "• Economic status and traits\n"
            "• Supernatural elements\n\n"
            "**Race-Specific Elements:**\n"
            "• **Elves:** Household and mentor details\n"
            "• **Dwarves:** Social class and attributes\n"
            "• **Tiraks:** Clan structures (future)\n\n"
            "**Commands:**\n"
            "• **fortsätt** - Continue with generated family\n"
            "• **ändra** - Generate new family background\n\n"
            "This step replaces Steps 9-11 as a unified family system."
        )
    
    def covers_steps(self) -> List[int]:
        """This step covers steps 9, 10, and 11."""
        return [9, 10, 11]
    
    def reload_data(self) -> bool:
        """Reload all data files."""
        try:
            self.culture_data = self._load_culture_data()
            self.thalask_family_data = {}  # Clear cache to force reload
            return True
        except Exception as e:
            print(f"Error reloading family data: {e}")
            return False