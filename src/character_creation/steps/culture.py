"""
Culture Selection Step for Character Creation

This module handles the culture selection step where the player chooses
their character's family culture, which determines family background and
skill bonuses.
"""

import discord
from discord.ext import commands
from typing import Optional, Tuple, List, Dict, Any
from pathlib import Path
import json

from .base_step import BaseStep


class CultureStep(BaseStep):
    """Step 5: Culture selection for the character's family background."""
    
    def __init__(self, embed_factory, data_dir: Optional[Path] = None):
        """
        Initialize the culture selection step.
        
        Args:
            embed_factory: The embed factory for creating Discord embeds
            data_dir: Optional data directory path
        """
        super().__init__(step_name="kultur", step_number=5)
        self.embed_factory = embed_factory
        self.data_dir = data_dir or self._get_default_data_dir()
        self.culture_data: Dict[str, Any] = {}
        self._load_culture_data()
    
    def _get_default_data_dir(self) -> Path:
        """Get default data directory."""
        script_dir = Path(__file__).parent
        project_root = script_dir.parent.parent.parent
        return project_root / 'data' / 'character_tables'
    
    def _load_culture_data(self) -> None:
        """Load culture data from huvudnaring.json."""
        huvudnaring_file = self.data_dir / 'familj' / 'huvudnaring.json'
        
        if not huvudnaring_file.exists():
            print(f"Warning: Could not find {huvudnaring_file}")
            return
        
        try:
            with open(huvudnaring_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Extract culture categories from huvudnäring
            if 'familj_huvudnäring' in data:
                self.culture_data = data['familj_huvudnäring']
                print(f"Loaded {len(self.culture_data)} culture categories")
            else:
                print("Warning: Could not find 'familj_huvudnäring' in huvudnaring.json")
                
        except Exception as e:
            print(f"Error loading culture data: {e}")
    
    async def execute(self, ctx: commands.Context, session: 'CharacterSession') -> discord.Embed:
        """
        Execute the culture selection step.
        
        Args:
            ctx: Discord command context
            session: Current character creation session
            
        Returns:
            Discord embed displaying the culture selection
        """
        if not self.culture_data:
            embed = self.embed_factory.error_message(
                session.user_id,
                "Ingen kulturdata kunde laddas från systemet."
            )
            await ctx.send(embed=embed)
            return embed
        
        embed = self.embed_factory.admin_message(
            session.user_id,
            f"🏛️ Steg {self.step_number}/{session.max_steps}: Kultur",
            "Välj rollpersonens familjekultur som bestämmer familjebakgrunden:"
        )
        
        # Create numbered list of cultures
        culture_options = []
        culture_list = []
        
        counter = 1
        for culture_key, culture_info in self.culture_data.items():
            culture_title = culture_info.get('titel', culture_key)
            culture_description = culture_info.get('beskrivning', '')
            
            culture_list.append(f"{counter}. **{culture_title}**")
            culture_options.append({
                'number': counter,
                'key': culture_key,
                'title': culture_title,
                'description': culture_description,
                'info': culture_info
            })
            counter += 1
        
        # Store options in temp_data for input handling
        session.temp_data['culture_options'] = culture_options
        
        # Display cultures in columns if too many
        if len(culture_list) <= 4:
            embed.add_field(
                name="🎭 Tillgängliga kulturer",
                value="\n".join(culture_list),
                inline=False
            )
        else:
            mid_point = (len(culture_list) + 1) // 2
            embed.add_field(
                name="🎭 Kulturer (1-3)",
                value="\n".join(culture_list[:mid_point]),
                inline=True
            )
            embed.add_field(
                name="🎭 Kulturer (4+)",
                value="\n".join(culture_list[mid_point:]),
                inline=True
            )
        
        # Add context information
        embed.add_field(
            name="📖 Om kulturer",
            value=(
                "Kulturen bestämmer din familjs huvudsakliga näring och "
                "påverkar vilka färdigheter du får bonus på samt din "
                "familjebakgrund i senare steg."
            ),
            inline=False
        )
        
        # Add instructions
        embed.add_field(
            name="📝 Instruktioner",
            value=(
                "• **[nummer]** - Välj kultur med nummer\n"
                "• **info [nummer]** - Visa detaljerad information\n"
                "• **[namn]** - Välj kultur med namn"
            ),
            inline=False
        )
        
        embed.set_footer(text="Exempel: !chargen 2, !chargen info 3, eller !chargen civiliserad")
        
        await ctx.send(embed=embed)
        return embed
    
    async def handle_input(self, ctx: commands.Context, session: 'CharacterSession', 
                          input_text: str, *args) -> Tuple[bool, Optional[str]]:
        """
        Handle user input for culture selection.
        
        Args:
            ctx: Discord command context
            session: Current character creation session
            input_text: User's input text
            *args: Additional arguments (unused)
            
        Returns:
            Tuple of (success: bool, error_message: Optional[str])
        """
        input_text = input_text.strip()
        culture_options = session.temp_data.get('culture_options', [])
        
        if not culture_options:
            await ctx.send("❌ Ingen kulturdata tillgänglig. Försök visa steget igen.")
            return False, "No culture options available"
        
        # Handle info request
        if input_text.lower().startswith('info'):
            await self._handle_info_request(ctx, input_text, culture_options)
            return False, "Info request handled"
        
        # Find selected culture
        selected_culture = self._validate_culture_choice(input_text, culture_options)
        
        if not selected_culture:
            available_cultures = [opt['title'] for opt in culture_options[:5]]  # First 5
            error_msg = (
                f"❌ Ogiltigt kulturval: '{input_text}'\n\n"
                f"**Tillgängliga kulturer:**\n" +
                "\n".join(f"• {culture}" for culture in available_cultures) +
                f"\n\n*Använd nummer, namn eller `info [nummer]` för mer information*"
            )
            await ctx.send(error_msg)
            return False, "Invalid culture choice"
        
        # Calculate skill bonuses
        bonus_list = self._calculate_skill_bonuses(selected_culture['info'])
        
        # Store culture data
        session.data['kultur'] = selected_culture['key']
        session.data['kultur_title'] = selected_culture['title']
        session.data['kultur_bonus'] = bonus_list
        session.data['kultur_info'] = selected_culture['info']
        
        # Send confirmation with bonuses
        confirmation_embed = discord.Embed(
            title="✅ Kultur bekräftad",
            description=f"**{selected_culture['title']}** har valts som familjekultur.",
            color=discord.Color.green()
        )
        
        if bonus_list:
            confirmation_embed.add_field(
                name="🎯 Färdighetsbonus",
                value="\n".join(f"• {bonus}" for bonus in bonus_list),
                inline=False
            )
        
        # Add special rules if any
        special_rules = selected_culture['info'].get('bonus', {}).get('special_regel')
        if special_rules:
            confirmation_embed.add_field(
                name="⚠️ Specialregel",
                value=special_rules,
                inline=False
            )
        
        # Add description if available
        if selected_culture.get('description'):
            confirmation_embed.add_field(
                name="📖 Beskrivning",
                value=selected_culture['description'][:500],  # Discord limit
                inline=False
            )
        
        await ctx.send(embed=confirmation_embed)
        
        return True, None
    
    async def _handle_info_request(self, ctx: commands.Context, 
                                 input_text: str, culture_options: List[Dict]) -> None:
        """Handle info request for a specific culture."""
        parts = input_text.split()
        if len(parts) < 2:
            await ctx.send("❌ Ange vilken kultur du vill ha info om. Exempel: `info 2`")
            return
        
        try:
            info_number = int(parts[1])
            selected_culture = None
            
            for culture in culture_options:
                if culture['number'] == info_number:
                    selected_culture = culture
                    break
            
            if selected_culture:
                await self._show_culture_info(ctx, selected_culture)
            else:
                await ctx.send(f"❌ Ogiltigt nummer. Välj mellan 1 och {len(culture_options)}.")
                
        except ValueError:
            await ctx.send("❌ Använd ett giltigt nummer. Exempel: `info 2`")
    
    async def _show_culture_info(self, ctx: commands.Context, culture: Dict[str, Any]) -> None:
        """Show detailed information about a culture."""
        info_embed = discord.Embed(
            title=f"🏛️ {culture['title']}",
            description=culture.get('description', 'Ingen detaljerad beskrivning tillgänglig.'),
            color=discord.Color.blue()
        )
        
        # Show skill bonuses
        bonus_list = self._calculate_skill_bonuses(culture['info'])
        if bonus_list:
            info_embed.add_field(
                name="🎯 Färdighetsbonus",
                value="\n".join(f"• {bonus}" for bonus in bonus_list),
                inline=False
            )
        
        # Show special rules
        special_rules = culture['info'].get('bonus', {}).get('special_regel')
        if special_rules:
            info_embed.add_field(
                name="⚠️ Specialregler",
                value=special_rules,
                inline=False
            )
        
        # Show available occupations if any
        if 'yrken' in culture['info']:
            occupations = culture['info']['yrken']
            if isinstance(occupations, list) and occupations:
                info_embed.add_field(
                    name="💼 Typiska yrken",
                    value=", ".join(occupations[:10]),  # First 10 occupations
                    inline=False
                )
        
        info_embed.set_footer(text=f"Kultur #{culture['number']}")
        await ctx.send(embed=info_embed)
    
    def _validate_culture_choice(self, input_text: str, 
                               culture_options: List[Dict]) -> Optional[Dict]:
        """Validate and find a culture choice."""
        # Try as number first
        if input_text.isdigit():
            culture_number = int(input_text)
            for culture in culture_options:
                if culture['number'] == culture_number:
                    return culture
        
        # Try name matching (case insensitive)
        input_lower = input_text.lower()
        for culture in culture_options:
            if (culture['title'].lower() == input_lower or 
                culture['key'].lower() == input_lower):
                return culture
        
        # Try partial matching
        matches = []
        for culture in culture_options:
            if (input_lower in culture['title'].lower() or 
                input_lower in culture['key'].lower()):
                matches.append(culture)
        
        # Return exact match if only one found
        if len(matches) == 1:
            return matches[0]
        
        return None
    
    def _calculate_skill_bonuses(self, culture_info: Dict[str, Any]) -> List[str]:
        """Calculate skill bonuses from culture data."""
        bonus_list = []
        bonuses = culture_info.get('bonus', {})
        
        for skill, bonus_value in bonuses.items():
            if skill == 'special_regel':  # Skip special rules
                continue
                
            if isinstance(bonus_value, (int, float)) and bonus_value > 0:
                bonus_list.append(f"+{bonus_value} {skill}")
            elif isinstance(bonus_value, str) and bonus_value.strip():
                bonus_list.append(f"{skill}: {bonus_value}")
        
        return bonus_list
    
    def validate_prerequisites(self, session: 'CharacterSession') -> Tuple[bool, Optional[str]]:
        """Validate that prerequisites for this step are met."""
        # Culture typically comes after race selection
        required_fields = ['kön', 'hemland', 'folkslag']
        
        for field in required_fields:
            if field not in session.data:
                return False, f"{field} must be selected before culture"
        
        return True, None
    
    def get_summary(self, session: 'CharacterSession') -> str:
        """Get a summary of the selected culture."""
        kultur = session.data.get('kultur', 'Ej valt')
        kultur_title = session.data.get('kultur_title', kultur)
        bonus_list = session.data.get('kultur_bonus', [])
        
        summary = f"**Kultur:** {kultur_title}"
        
        if bonus_list:
            summary += f" ({len(bonus_list)} färdighetsbonus)"
        
        return summary
    
    def validate_data(self, session: 'CharacterSession') -> bool:
        """Validate that culture data exists and is valid."""
        if 'kultur' not in session.data:
            return False
        
        kultur = session.data['kultur']
        return kultur in self.culture_data
    
    def can_skip(self, session: 'CharacterSession') -> bool:
        """Culture selection cannot be skipped."""
        return False
    
    def get_help_text(self) -> str:
        """Get detailed help text for this step."""
        return (
            f"**Steg {self.step_number}: Kultur**\n\n"
            "Välj din familjs huvudsakliga kultur/näring. Detta påverkar:\n"
            "• **Färdighetsbonus** - Bonusar på relevanta färdigheter\n"
            "• **Familjebakgrund** - Vad din familj sysslar med\n"
            "• **Ekonomisk situation** - Familjens välstånd\n"
            "• **Sociala kontakter** - Vilka du känner\n\n"
            "**Kulturtyper:**\n"
            "• **Civiliserad** - Stadsbor, hantverkare, köpmän\n"
            "• **Landsbygd** - Bönder, herdar, skogsfolk\n"
            "• **Nomader** - Resande folk, handelsmän\n"
            "• **Primitiv** - Stammfolk, jägare, samlare\n\n"
            "**Kommandon:**\n"
            "• **[nummer/namn]** - Välj kultur\n"
            "• **info [nummer]** - Visa detaljerad information\n\n"
            "Ditt val påverkar senare familjegenerering och bakgrundshändelser."
        )
    
    def get_culture_count(self) -> int:
        """Get total number of available cultures."""
        return len(self.culture_data)
    
    def reload_culture_data(self) -> bool:
        """Reload culture data from file."""
        try:
            self._load_culture_data()
            return len(self.culture_data) > 0
        except Exception as e:
            print(f"Error reloading culture data: {e}")
            return False