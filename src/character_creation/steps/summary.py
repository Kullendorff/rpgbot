"""
Summary Step for Character Creation

This module handles the final character summary (Step 15):
- Displays complete character information across multiple embeds
- Shows basic information, family background, background events
- Collects and displays skill bonuses from all sources
- Provides final completion confirmation
- Cleans up the character creation session
"""

import discord
from discord.ext import commands
from typing import Optional, Tuple, List, Dict, Any
from pathlib import Path

from .base_step import BaseStep


class SummaryStep(BaseStep):
    """Step 15: Final character summary and session completion."""
    
    def __init__(self, embed_factory, data_dir: Optional[Path] = None):
        """
        Initialize the summary step.
        
        Args:
            embed_factory: The embed factory for creating Discord embeds
            data_dir: Optional data directory path (not used but kept for consistency)
        """
        super().__init__(step_name="sammanfattning", step_number=15)
        self.embed_factory = embed_factory
        
    async def execute(self, ctx: commands.Context, session: 'CharacterSession') -> discord.Embed:
        """
        Execute the character summary step.
        
        Args:
            ctx: Discord command context
            session: Current character creation session
            
        Returns:
            Discord embed (last embed sent)
        """
        await ctx.send("📊 Generating complete character summary...")
        
        # Create multiple embeds to show all information
        embeds = []
        
        # Embed 1: Basic Information
        basic_embed = await self._create_basic_info_embed(session)
        embeds.append(basic_embed)
        
        # Embed 2: Family Background
        family_embed = await self._create_family_background_embed(session)
        embeds.append(family_embed)
        
        # Embed 3: Background Events
        background_embed = await self._create_background_events_embed(session)
        embeds.append(background_embed)
        
        # Embed 4: Skill Bonuses
        skills_embed = await self._create_skill_bonuses_embed(session)
        embeds.append(skills_embed)
        
        # Embed 5: Final Completion
        final_embed = await self._create_completion_embed(session)
        embeds.append(final_embed)
        
        # Send all embeds
        for embed in embeds:
            await ctx.send(embed=embed)
        
        return final_embed
    
    async def _create_basic_info_embed(self, session: 'CharacterSession') -> discord.Embed:
        """Create the basic information embed."""
        embed = self.embed_factory.admin_message(
            session.user_id, 
            "🎭 Character Summary - Part 1: Basic Information", 
            "Complete overview of your generated EON character:"
        )
        
        # Basic info
        folkslag_text = session.data.get('folkslag', 'Unknown').capitalize()
        
        # Add Thalamur-specific information
        thalamur_special = session.data.get('thalamur_special')
        if thalamur_special:
            samhällsklass = session.data.get('thalamur_samhällsklass', '')
            if samhällsklass:
                folkslag_text += f" ({samhällsklass})"
                
                # Add family information for Citizens
                if samhällsklass == 'Citizen':
                    thalamur_att = session.data.get('thalamur_ätt')
                    thalamur_att_data = session.data.get('thalamur_ätt_data', {})
                    if thalamur_att and thalamur_att_data:
                        folkslag_text += f", Family {thalamur_att_data.get('titel', thalamur_att.title())}"
        
        embed.add_field(
            name="👤 Basic Information",
            value=f"**Gender:** {session.data.get('kön', 'Unknown').capitalize()}\n" +
                  f"**Age:** {session.data.get('ålder', 'Unknown')} years\n" +
                  f"**Homeland:** {session.data.get('hemland', 'Unknown')}\n" +
                  f"**Race:** {folkslag_text}\n" +
                  f"**Culture:** {session.data.get('kultur_namn', session.data.get('kultur', 'Unknown'))}",
            inline=False
        )
        
        # Thalamur family information
        thalamur_att_data = session.data.get('thalamur_ätt_data')
        if thalamur_att_data:
            bonusar = thalamur_att_data.get('bonusar', {})
            att_info = []
            
            # Description
            att_info.append(f"**Description:** {thalamur_att_data.get('beskrivning', 'No description')}")
            
            # Placement bonuses
            if 'placera_slag' in bonusar:
                att_info.append(f"**Place background rolls on:** {', '.join(bonusar['placera_slag'])}")
            
            # Easy skills
            if 'lattlarda_fardigheter' in bonusar:
                att_info.append(f"**Easy skills:** {', '.join(bonusar['lattlarda_fardigheter'])}")
            
            # Extra contacts
            if 'extra_kontakter' in bonusar:
                att_info.append(f"**Extra contacts:** +{bonusar['extra_kontakter']}")
            
            # Special rule
            if 'special_regel' in bonusar:
                att_info.append(f"**Special rule:** {bonusar['special_regel']}")
            
            embed.add_field(
                name=f"🏛️ Thalamur Family: {thalamur_att_data.get('titel', 'Unknown')}",
                value="\n".join(att_info),
                inline=False
            )
        
        # Field disturbances for Cirefalier
        field_storningar = session.data.get('field_storningar', [])
        if field_storningar:
            storning_text = []
            for i, storning in enumerate(field_storningar, 1):
                storning_text.append(f"{i}. **{storning['result_key'].replace('_', ' ').title()}**")
            
            embed.add_field(
                name="🧬 Field Disturbances (Cirefalier)",
                value="\n".join(storning_text) if storning_text else "No disturbances",
                inline=False
            )
        elif 'cirefalier' in session.data.get('folkslag', '').lower():
            embed.add_field(
                name="🧬 Field Disturbances (Cirefalier)",
                value="No disturbances 🎉",
                inline=False
            )
        
        # Character traits
        karaktersdrag = session.data.get('karaktärsdrag', {})
        if karaktersdrag:
            trait_text = []
            for trait, data in karaktersdrag.items():
                if isinstance(data, dict) and 'value' in data:
                    trait_text.append(f"**{trait.capitalize()}:** {data['value']}")
                else:
                    trait_text.append(f"**{trait.capitalize()}:** {data}")
            
            embed.add_field(
                name="🎭 Character Traits",
                value="\n".join(trait_text) if trait_text else "No character traits",
                inline=False
            )
        
        # Attributes
        attributes = session.data.get('attribut', {})
        if attributes:
            attr_text = []
            total = sum(attributes.values())
            for attr, value in attributes.items():
                attr_text.append(f"**{attr}:** {value}")
            
            embed.add_field(
                name="⚔️ Attributes",
                value="\n".join(attr_text) + f"\n\n**Total sum:** {total}",
                inline=True
            )
        
        return embed
    
    async def _create_family_background_embed(self, session: 'CharacterSession') -> discord.Embed:
        """Create the family background embed."""
        embed = self.embed_factory.admin_message(
            session.user_id, 
            "👨‍👩‍👧‍👦 Character Summary - Part 2: Family Background", 
            ""
        )
        
        # Show family background summary from complete family data
        family_data = session.data.get('familj', session.data.get('komplett_familjebakgrund'))
        if family_data:
            family_text = []
            
            # Basic family
            basic = family_data.get('basic', {})
            if basic:
                basic_summary = self._format_family_dict_summary(basic)
                family_text.append("📅 **BASIC FAMILY**")
                family_text.append(basic_summary)
            
            # Profession from culture
            profession = family_data.get('profession', {})
            if profession and 'profession' in profession:
                family_text.append(f"\n💼 **FAMILY PROFESSION**")
                family_text.append(f"Family works as **{profession['profession']}** (Roll: {profession['roll']})")
                if profession.get('skills'):
                    skills_text = ", ".join(profession['skills'])
                    family_text.append(f"Skills: {skills_text} (Bonus: {profession.get('skill_bonus', '1d6+1')})")
            
            # Race-specific properties
            race_specific = family_data.get('race_specific', {})
            if race_specific:
                family_text.append(f"\n🏛️ **RACE-SPECIFIC PROPERTIES**")
                
                if 'household' in race_specific:
                    household = race_specific['household']
                    family_text.append(f"🏠 **Household:** {household.get('name', 'Unknown')}")
                    if 'skills' in household:
                        skills = ", ".join(household['skills'])
                        family_text.append(f"Bonus: {skills} ({household.get('bonus', '1d6+1')})")
                
                if 'mentor' in race_specific:
                    mentor = race_specific['mentor']
                    family_text.append(f"🧙‍♂️ **Mentor:** {mentor.get('personality', 'Unknown personality')}")
                    if 'skills' in mentor:
                        skills = ", ".join(mentor['skills'])
                        family_text.append(f"Mentor skills: {skills} ({mentor.get('bonus', '1d6+4')})")
                
                if 'social_class' in race_specific:
                    social = race_specific['social_class']
                    family_text.append(f"🏛️ **Social class:** {social.get('name', 'Unknown')}")
                    if 'attribute_effects' in social:
                        effects = social['attribute_effects']
                        effect_text = ", ".join([f"{attr}: {'+' if val >= 0 else ''}{val}" for attr, val in effects.items()])
                        family_text.append(f"Attribute effects: {effect_text}")
            
            if family_text:
                # Limit length for Discord embed
                family_summary = "\n".join(family_text)
                if len(family_summary) > 1800:
                    family_summary = family_summary[:1800] + "..."
                
                embed.add_field(
                    name="🏠 Family Background",
                    value=family_summary,
                    inline=False
                )
        
        return embed
    
    async def _create_background_events_embed(self, session: 'CharacterSession') -> discord.Embed:
        """Create the background events embed."""
        embed = self.embed_factory.admin_message(
            session.user_id, 
            "📚 Character Summary - Part 3: Background Events", 
            ""
        )
        
        # Number of background rolls
        background_rolls = session.data.get('antal_bakgrundslag', 0)
        embed.add_field(
            name="🎲 Background Rolls",
            value=f"Total number of rolls: **{background_rolls}**",
            inline=False
        )
        
        # Processed background results
        processed_results = session.data.get('processed_background_results', [])
        if processed_results:
            results_text = []
            for i, result in enumerate(processed_results, 1):
                category = result.get('category', 'Unknown')
                result_desc = result.get('result', 'No result')
                # Limit length to fit
                short_desc = result_desc[:50] + "..." if len(result_desc) > 50 else result_desc
                results_text.append(f"**{i}.** {category}: {short_desc}")
            
            embed.add_field(
                name="📋 Mottagna bakgrundshändelser:",
                value="\n".join(results_text[:10]),  # Max 10 results
                inline=False
            )
            
            if len(processed_results) > 10:
                embed.add_field(
                    name="📖 Ytterligare händelser:",
                    value=f"... och {len(processed_results) - 10} ytterligare bakgrundshändelser",
                    inline=False
                )
        else:
            embed.add_field(
                name="📋 Background events:",
                value="No specific background events processed yet.",
                inline=False
            )
        
        return embed
    
    async def _create_skill_bonuses_embed(self, session: 'CharacterSession') -> discord.Embed:
        """Create the skill bonuses embed."""
        embed = self.embed_factory.admin_message(
            session.user_id, 
            "🎯 Character Summary - Part 4: Skill Bonuses", 
            ""
        )
        
        # Collect skill bonuses from all sources
        skill_bonuses = self._collect_all_skill_bonuses(session)
        
        if skill_bonuses:
            skills_text = []
            for skill, sources in skill_bonuses.items():
                source_list = []
                for source in sources:
                    if source['bonus']:
                        source_list.append(f"{source['source']}: {source['bonus']}")
                    else:
                        source_list.append(source['source'])
                skills_text.append(f"**{skill.capitalize()}:** {', '.join(source_list)}")
            
            embed.add_field(
                name="📚 Mottagna färdighetsbonusar:",
                value="\n".join(skills_text),
                inline=False
            )
        else:
            embed.add_field(
                name="📚 Skill bonuses:",
                value="No specific skill bonuses documented (but may exist from background events)",
                inline=False
            )
        
        return embed
    
    async def _create_completion_embed(self, session: 'CharacterSession') -> discord.Embed:
        """Create the final completion embed."""
        embed = self.embed_factory.admin_message(
            session.user_id, 
            "🏆 Character Creation Complete!", 
            "Your EON character is now ready for adventure!"
        )
        
        embed.add_field(
            name="✅ Completed steps:",
            value="• Basic information (gender, age, homeland, race)\n" +
                  "• Culture and family background\n" +
                  "• Attribute generation with racial modifiers\n" +
                  "• Complete automatic family generation\n" +
                  "• Detailed background events",
            inline=False
        )
        
        embed.add_field(
            name="🎮 Session ended:",
            value=f"Character creation session is now complete.\n" +
                  f"Use `!chargen start` to create a new character.",
            inline=False
        )
        
        return embed
    
    def _format_family_dict_summary(self, family_dict: Dict[str, Any]) -> str:
        """Format family dictionary into readable summary."""
        parts = []
        
        if 'birth_info' in family_dict:
            parts.append(f"Birth: {family_dict['birth_info']}")
        
        if 'father' in family_dict:
            father = family_dict['father']
            parts.append(f"Father: {father.get('status', 'Unknown')} (Age: {father.get('age', '?')})")
        
        if 'mother' in family_dict:
            mother = family_dict['mother']
            parts.append(f"Mother: {mother.get('status', 'Unknown')} (Age: {mother.get('age', '?')})")
        
        if 'siblings' in family_dict:
            siblings = family_dict['siblings']
            if siblings:
                sibling_count = len(siblings)
                parts.append(f"Siblings: {sibling_count}")
        
        return "\n".join(parts) if parts else "Basic family information"
    
    def _collect_all_skill_bonuses(self, session: 'CharacterSession') -> Dict[str, List[Dict[str, str]]]:
        """Collect all skill bonuses from various sources."""
        skill_bonuses = {}
        
        # 1. From family profession
        family_data = session.data.get('familj', session.data.get('komplett_familjebakgrund', {}))
        profession = family_data.get('profession', {})
        if profession and 'skills' in profession:
            skill_bonus = profession.get('skill_bonus', '1d6+1')
            for skill in profession['skills']:
                if skill not in skill_bonuses:
                    skill_bonuses[skill] = []
                skill_bonuses[skill].append({
                    'source': 'Family profession',
                    'bonus': skill_bonus
                })
        
        # 2. From race-specific properties
        race_specific = family_data.get('race_specific', {})
        
        # Elf household
        if 'household' in race_specific:
            household = race_specific['household']
            if 'skills' in household:
                bonus = household.get('bonus', '1d6+1')
                for skill in household['skills']:
                    if skill not in skill_bonuses:
                        skill_bonuses[skill] = []
                    skill_bonuses[skill].append({
                        'source': f"Elf household ({household.get('name', 'Unknown')})",
                        'bonus': bonus
                    })
        
        # Elf mentor
        if 'mentor' in race_specific:
            mentor = race_specific['mentor']
            if 'skills' in mentor:
                bonus = mentor.get('bonus', '1d6+4')
                for skill in mentor['skills']:
                    if skill not in skill_bonuses:
                        skill_bonuses[skill] = []
                    skill_bonuses[skill].append({
                        'source': 'Elf mentor',
                        'bonus': bonus
                    })
        
        # 3. From Thalaskic family tables
        family_skill_bonuses = session.data.get('familj_skill_bonuses', [])
        for bonus_data in family_skill_bonuses:
            # This would need more specific implementation based on the bonus structure
            source = bonus_data.get('source', 'Unknown source')
            bonus = bonus_data.get('bonus', '')
            
            # Add to general skill bonuses (since we don't know specific skills)
            skill_name = 'Various skills'
            if skill_name not in skill_bonuses:
                skill_bonuses[skill_name] = []
            skill_bonuses[skill_name].append({
                'source': source,
                'bonus': bonus
            })
        
        # 4. From Thalamur family bonuses
        thalamur_att_data = session.data.get('thalamur_ätt_data', {})
        if thalamur_att_data:
            bonusar = thalamur_att_data.get('bonusar', {})
            if 'lattlarda_fardigheter' in bonusar:
                for skill in bonusar['lattlarda_fardigheter']:
                    if skill not in skill_bonuses:
                        skill_bonuses[skill] = []
                    skill_bonuses[skill].append({
                        'source': f"Thalamur family ({thalamur_att_data.get('titel', 'Unknown')})",
                        'bonus': 'Easy to learn'
                    })
        
        return skill_bonuses
    
    async def handle_input(self, ctx: commands.Context, session: 'CharacterSession', 
                          input_text: str, *args) -> Tuple[bool, Optional[str]]:
        """
        Handle user input for summary step.
        
        The summary step doesn't require input - it's the final step that completes the session.
        Any input will end the session.
        
        Args:
            ctx: Discord command context
            session: Current character creation session
            input_text: User's input text
            *args: Additional arguments (unused)
            
        Returns:
            Tuple of (success: bool, error_message: Optional[str])
        """
        # Summary step always completes the session
        return True, None
    
    def validate_prerequisites(self, session: 'CharacterSession') -> Tuple[bool, Optional[str]]:
        """Validate that prerequisites for this step are met."""
        # Summary step requires all previous steps to be completed
        required_fields = [
            'kön', 'hemland', 'folkslag', 'ålder', 'kultur', 'attribut', 
            'familj', 'antal_bakgrundslag'
        ]
        
        for field in required_fields:
            if field not in session.data:
                return False, f"{field} must be completed before character summary"
        
        return True, None
    
    def get_summary(self, session: 'CharacterSession') -> str:
        """Get a summary of the character creation completion."""
        return "**Summary:** Character creation completed!"
    
    def validate_data(self, session: 'CharacterSession') -> bool:
        """Validate that all required data exists for the summary."""
        # Check that we have the minimum required data for a summary
        return (session.data.get('kön') is not None and 
                session.data.get('folkslag') is not None and
                session.data.get('attribut') is not None)
    
    def can_skip(self, session: 'CharacterSession') -> bool:
        """Summary step cannot be skipped - it's the final step."""
        return False
    
    def get_help_text(self) -> str:
        """Get detailed help text for this step."""
        return (
            f"**Step {self.step_number}: Character Summary**\n\n"
            "Final character creation step that displays:\n\n"
            "**Basic Information:**\n"
            "• Gender, age, homeland, race, culture\n"
            "• Thalamur family information (if applicable)\n"
            "• Field disturbances for Cirefalier\n"
            "• Character traits and attributes\n\n"
            "**Family Background:**\n"
            "• Complete family structure\n"
            "• Family profession and skills\n"
            "• Race-specific family properties\n\n"
            "**Background Events:**\n"
            "• Number of background rolls\n"
            "• All processed background events\n\n"
            "**Skill Bonuses:**\n"
            "• Bonuses from family profession\n"
            "• Race-specific skill bonuses\n"
            "• Thalamur family bonuses\n\n"
            "This step automatically completes the character creation session.\n"
            "Use `!chargen start` to create a new character afterwards."
        )
    
    def covers_steps(self) -> List[int]:
        """This step covers only step 15."""
        return [15]