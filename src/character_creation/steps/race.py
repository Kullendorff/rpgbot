"""
Race Selection Step for Character Creation

This module handles the race selection step with intelligent filtering based
on the previously selected homeland. Uses homeland_races.json for contextual
race lists and supports percentage-based random generation.
"""

import discord
from discord.ext import commands
from typing import Optional, Tuple, List, Dict, Any
from pathlib import Path

from .base_step import BaseStep
from ..utils.homeland_race_mapper import HomelandRaceMapper
from ..utils.dice_roller import CharacterDiceRoller


class RaceStep(BaseStep):
    """Step 3: Race selection with homeland-based filtering."""
    
    def __init__(self, embed_factory, data_dir: Optional[Path] = None):
        """
        Initialize the race selection step.
        
        Args:
            embed_factory: The embed factory for creating Discord embeds
            data_dir: Optional data directory path
        """
        super().__init__(step_name="folkslag", step_number=3)
        self.embed_factory = embed_factory
        self.data_dir = data_dir or self._get_default_data_dir()
        self.race_mapper = HomelandRaceMapper(self.data_dir)
        self.dice_roller = CharacterDiceRoller()
        
        # Fallback race data for when homeland_races.json is not available
        self.fallback_races = self._load_fallback_races()
    
    def _get_default_data_dir(self) -> Path:
        """Get default data directory."""
        script_dir = Path(__file__).parent
        project_root = script_dir.parent.parent.parent
        return project_root / 'data' / 'character_tables'
    
    def _load_fallback_races(self) -> List[str]:
        """Load fallback race list from existing system."""
        # These are common races that should always be available
        return [
            "Vanare", "Asharier", "Aus", "Tauper", "Darkener",
            "Cirefalier", "Kragg", "Kamor", "Lalaster", "Rauner",
            "Veddo", "Tosher", "Tokon", "Zhaner", "Adasier",
            "Aunurier", "Thalasker", "Pyar", "Kirya", "Thism",
            "Sanari", "Léaram", "Henea", "Ghor", "Zolod",
            "Roghan", "Drezin", "Marnakh", "Frakk", "Bazirk"
        ]
    
    async def execute(self, ctx: commands.Context, session: 'CharacterSession') -> discord.Embed:
        """
        Execute the race selection step with homeland-based filtering.
        
        Args:
            ctx: Discord command context
            session: Current character creation session
            
        Returns:
            Discord embed displaying the race selection
        """
        # Check for Thalamur special case first
        homeland = session.data.get('hemland', '')
        if homeland.lower() == 'thalamur':
            return await self._handle_thalamur_special(ctx, session)
        
        # Get races for the selected homeland
        available_races = self.race_mapper.get_unique_race_names(homeland)
        
        # Fallback if no races found for homeland
        if not available_races:
            return await self._handle_fallback_race_selection(ctx, session, homeland)
        
        # Create embed for homeland-filtered races
        embed = self.embed_factory.admin_message(
            session.user_id,
            f"🏘️ Steg {self.step_number}/{session.max_steps}: Folkslag",
            f"Välj folkslag för **{session.data.get('hemland_title', homeland)}**:"
        )
        
        # Format races for display
        race_list = []
        for i, race in enumerate(available_races, 1):
            race_list.append(f"{i}. {race}")
        
        # Split into chunks if too many races
        chunk_size = 20
        if len(race_list) <= chunk_size:
            embed.add_field(
                name=f"🎭 Vanliga folkslag i {homeland}",
                value="\n".join(race_list),
                inline=False
            )
        else:
            # Split into multiple fields
            for i in range(0, len(race_list), chunk_size):
                chunk = race_list[i:i + chunk_size]
                chunk_title = f"🎭 Folkslag ({i+1}-{min(i+chunk_size, len(race_list))})"
                embed.add_field(
                    name=chunk_title,
                    value="\n".join(chunk),
                    inline=True
                )
        
        # Add context about homeland filtering
        embed.add_field(
            name="🌍 Hemlandsbaserad filtrering",
            value=(
                f"Dessa folkslag är vanliga i **{homeland}**. "
                "Listan är anpassad efter ditt valda hemland för "
                "mer realistisk karaktärsskapning."
            ),
            inline=False
        )
        
        # Add instructions
        embed.add_field(
            name="📝 Instruktioner",
            value=(
                "• **[namn/nummer]** - Välj specifikt folkslag\n"
                "• **slumpa** - Slumpmässigt val (T100-baserat)\n"
                "• **info [nummer]** - Visa information om folkslag\n"
                "• **alla** - Visa alla möjliga folkslag (om du vill byta hemland)"
            ),
            inline=False
        )
        
        embed.set_footer(text="Exempel: !chargen Vanare, !chargen 1, eller !chargen slumpa")
        
        await ctx.send(embed=embed)
        return embed
    
    async def handle_input(self, ctx: commands.Context, session: 'CharacterSession', 
                          input_text: str, *args) -> Tuple[bool, Optional[str]]:
        """
        Handle user input for race selection.
        
        Args:
            ctx: Discord command context
            session: Current character creation session
            input_text: User's input text
            *args: Additional arguments (unused)
            
        Returns:
            Tuple of (success: bool, error_message: Optional[str])
        """
        input_text = input_text.strip().lower()
        homeland = session.data.get('hemland', '')
        
        # Handle special commands
        if input_text == 'slumpa':
            return await self._handle_random_race(ctx, session, homeland)
        elif input_text == 'alla':
            return await self._show_all_races(ctx, session)
        elif input_text.startswith('info'):
            await self._handle_race_info(ctx, input_text, homeland)
            return False, "Info request handled"
        
        # Handle race selection
        selected_race = self._validate_race_choice(input_text, homeland)
        
        if not selected_race:
            available_races = self.race_mapper.get_unique_race_names(homeland)
            if not available_races:
                available_races = self.fallback_races[:10]  # First 10 as examples
            
            error_msg = (
                f"❌ Ogiltigt folkslag: '{input_text}'\n\n"
                f"**Tillgängliga folkslag för {homeland}:**\n" +
                "\n".join(f"• {race}" for race in available_races[:8]) +
                f"\n\n*Använd namn eller nummer, eller skriv `slumpa` för slumpval*"
            )
            await ctx.send(error_msg)
            return False, "Invalid race choice"
        
        # Store selected race
        session.data['folkslag'] = selected_race
        
        # Send confirmation
        confirmation_embed = discord.Embed(
            title="✅ Folkslag bekräftat",
            description=f"**{selected_race}** har valts som folkslag.",
            color=discord.Color.green()
        )
        
        # Add race information if available
        race_info = self._get_race_info(selected_race)
        if race_info:
            confirmation_embed.add_field(
                name="📖 Information",
                value=race_info[:500],  # Discord field limit
                inline=False
            )
        
        await ctx.send(embed=confirmation_embed)
        
        return True, None
    
    async def _handle_thalamur_special(self, ctx: commands.Context, 
                                     session: 'CharacterSession') -> discord.Embed:
        """Handle special Thalamur logic (preserve existing functionality)."""
        embed = self.embed_factory.admin_message(
            session.user_id,
            f"🏛️ Steg {self.step_number}/{session.max_steps}: Thalamur Folkslag",
            "Thalamur har speciella folkslag-regler:"
        )
        
        embed.add_field(
            name="🎭 Specialprocess",
            value=(
                "Thalamur kräver specialhantering för:\n"
                "• Medborgare vs Folket\n"
                "• Ätt-system\n"
                "• Unika kulturella aspekter\n\n"
                "Den befintliga Thalamur-logiken kommer att användas."
            ),
            inline=False
        )
        
        embed.set_footer(text="Thalamur-processen fortsätter enligt befintliga regler...")
        
        await ctx.send(embed=embed)
        
        # Set flag for existing Thalamur handler to take over
        session.data['use_thalamur_special'] = True
        
        return embed
    
    async def _handle_fallback_race_selection(self, ctx: commands.Context, 
                                            session: 'CharacterSession',
                                            homeland: str) -> discord.Embed:
        """Handle fallback race selection when homeland data is not available."""
        embed = self.embed_factory.admin_message(
            session.user_id,
            f"🎭 Steg {self.step_number}/{session.max_steps}: Folkslag",
            f"Folkslag för **{homeland}** (allmän lista):"
        )
        
        embed.add_field(
            name="⚠️ Information",
            value=(
                f"Ingen specifik data hittades för {homeland}. "
                "Visar allmän lista över tillgängliga folkslag."
            ),
            inline=False
        )
        
        # Show fallback races in chunks
        chunk_size = 15
        for i in range(0, len(self.fallback_races), chunk_size):
            chunk = self.fallback_races[i:i + chunk_size]
            race_list = [f"{i+j+1}. {race}" for j, race in enumerate(chunk)]
            
            embed.add_field(
                name=f"Folkslag ({i+1}-{i+len(chunk)})",
                value="\n".join(race_list),
                inline=True
            )
        
        embed.set_footer(text="Använd namn eller nummer för att välja")
        await ctx.send(embed=embed)
        
        return embed
    
    async def _handle_random_race(self, ctx: commands.Context, 
                                session: 'CharacterSession',
                                homeland: str) -> Tuple[bool, Optional[str]]:
        """Handle random race selection using T100 rolls."""
        race_name, variant_name = self.race_mapper.roll_random_race(homeland)
        
        if not race_name:
            # Fallback to simple random selection
            available_races = self.race_mapper.get_unique_race_names(homeland)
            if not available_races:
                available_races = self.fallback_races
            
            if available_races:
                import random
                race_name = random.choice(available_races)
            else:
                await ctx.send("❌ Kunde inte slumpa folkslag - inga alternativ tillgängliga.")
                return False, "No races available for random selection"
        
        # Create full race name with variant if applicable
        full_race_name = race_name
        if variant_name and variant_name != race_name:
            full_race_name = f"{race_name} ({variant_name})"
        
        # Store the race
        session.data['folkslag'] = race_name
        if variant_name:
            session.data['folkslag_variant'] = variant_name
        
        # Create result embed
        random_embed = discord.Embed(
            title="🎲 Slumpmässigt folkslag",
            description=f"**{full_race_name}** har slumpats fram!",
            color=discord.Color.gold()
        )
        
        random_embed.add_field(
            name="🎯 T100-resultat",
            value=f"Slumpat från folkslagstabellen för **{homeland}**",
            inline=False
        )
        
        # Add race info if available
        race_info = self._get_race_info(race_name)
        if race_info:
            random_embed.add_field(
                name="📖 Information",
                value=race_info[:500],
                inline=False
            )
        
        await ctx.send(embed=random_embed)
        
        return True, None
    
    async def _show_all_races(self, ctx: commands.Context, 
                            session: 'CharacterSession') -> Tuple[bool, Optional[str]]:
        """Show all available races (not homeland-filtered)."""
        embed = discord.Embed(
            title="🌍 Alla möjliga folkslag",
            description=(
                "Här är alla folkslag som finns i systemet. "
                "Observera att vissa kan vara ovanliga i ditt valda hemland."
            ),
            color=discord.Color.orange()
        )
        
        # Show in chunks
        chunk_size = 15
        for i in range(0, len(self.fallback_races), chunk_size):
            chunk = self.fallback_races[i:i + chunk_size]
            race_list = [f"{i+j+1}. {race}" for j, race in enumerate(chunk)]
            
            embed.add_field(
                name=f"Folkslag ({i+1}-{i+len(chunk)})",
                value="\n".join(race_list),
                inline=True
            )
        
        embed.add_field(
            name="💡 Tips",
            value=(
                "För mer realistisk karaktär, välj från de folkslag som "
                "visades för ditt hemland tidigare."
            ),
            inline=False
        )
        
        await ctx.send(embed=embed)
        
        # Don't advance - let user choose
        return False, "Showing all races"
    
    async def _handle_race_info(self, ctx: commands.Context, 
                              input_text: str, homeland: str) -> None:
        """Handle info request for a specific race."""
        parts = input_text.split()
        if len(parts) < 2:
            await ctx.send("❌ Ange vilket folkslag du vill ha info om. Exempel: `info 3`")
            return
        
        try:
            race_number = int(parts[1])
            available_races = self.race_mapper.get_unique_race_names(homeland)
            
            if not available_races:
                available_races = self.fallback_races
            
            if 1 <= race_number <= len(available_races):
                race_name = available_races[race_number - 1]
                race_info = self._get_race_info(race_name)
                
                info_embed = discord.Embed(
                    title=f"🎭 {race_name}",
                    description=race_info or "Ingen detaljerad information tillgänglig.",
                    color=discord.Color.blue()
                )
                
                info_embed.set_footer(text=f"Folkslag #{race_number}")
                await ctx.send(embed=info_embed)
            else:
                await ctx.send(f"❌ Ogiltigt nummer. Välj mellan 1 och {len(available_races)}.")
                
        except ValueError:
            await ctx.send("❌ Använd ett giltigt nummer. Exempel: `info 3`")
    
    def _validate_race_choice(self, input_text: str, homeland: str) -> Optional[str]:
        """Validate and normalize a race choice."""
        # Use mapper first
        validated_race = self.race_mapper.validate_race_choice(homeland, input_text)
        
        if validated_race:
            return validated_race
        
        # Fallback validation
        available_races = self.race_mapper.get_unique_race_names(homeland)
        if not available_races:
            available_races = self.fallback_races
        
        # Try as number
        try:
            race_index = int(input_text) - 1
            if 0 <= race_index < len(available_races):
                return available_races[race_index]
        except ValueError:
            pass
        
        # Try name matching
        input_lower = input_text.lower()
        for race in available_races:
            if race.lower() == input_lower or input_lower in race.lower():
                return race
        
        return None
    
    def _get_race_info(self, race_name: str) -> Optional[str]:
        """Get information about a race (placeholder for now)."""
        # This could load from race description files in the future
        race_descriptions = {
            "Vanare": "Vanligt mänskligt folk från Thalamur och omgivningar.",
            "Asharier": "Stolta människor från Asharien med stark krigarkultur.",
            "Pyar": "Den vanligaste alvrassen, kända för sin visdom och långlivadhet.",
            "Ghor": "Dvärgarna från Ghor-klanen, skickliga smeder och krigare.",
            "Marnakh": "Tirakisk stam känd för sin nomadiska livsstil."
        }
        
        return race_descriptions.get(race_name)
    
    def validate_prerequisites(self, session: 'CharacterSession') -> Tuple[bool, Optional[str]]:
        """Validate that prerequisites for this step are met."""
        if 'hemland' not in session.data:
            return False, "Homeland must be selected before race"
        
        return True, None
    
    def get_summary(self, session: 'CharacterSession') -> str:
        """Get a summary of the selected race."""
        folkslag = session.data.get('folkslag', 'Ej valt')
        variant = session.data.get('folkslag_variant')
        
        if variant and variant != folkslag:
            return f"**Folkslag:** {folkslag} ({variant})"
        else:
            return f"**Folkslag:** {folkslag}"
    
    def validate_data(self, session: 'CharacterSession') -> bool:
        """Validate that race data exists and is valid."""
        return 'folkslag' in session.data and bool(session.data['folkslag'])
    
    def can_skip(self, session: 'CharacterSession') -> bool:
        """Race selection cannot be skipped."""
        return False
    
    def get_help_text(self) -> str:
        """Get detailed help text for this step."""
        return (
            f"**Steg {self.step_number}: Folkslag**\n\n"
            "Välj vilket folkslag (ras) din rollperson tillhör. "
            "Listan är filtrerad baserat på ditt valda hemland för "
            "mer realistisk karaktärsskapning.\n\n"
            "**Funktioner:**\n"
            "• **Hemlandsfiltrering** - Endast vanliga folkslag visas\n"
            "• **Slumpgenerering** - T100-baserad med realistiska sannolikheter\n"
            "• **Specialhantering** - Thalamur och andra komplexa fall\n\n"
            "**Kommandon:**\n"
            "• **[namn/nummer]** - Välj specifikt folkslag\n"
            "• **slumpa** - Slumpmässigt val enligt hemlandstabeller\n"
            "• **info [nummer]** - Visa information om folkslag\n"
            "• **alla** - Visa alla möjliga folkslag\n\n"
            "Ditt val av folkslag påverkar attributmodifierare och "
            "tillgängliga kulturer i senare steg."
        )