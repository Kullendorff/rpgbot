"""
Age Selection Step for Character Creation

This module handles the age selection step where the player chooses
their character's age, with race-specific recommendations and background
roll calculations.
"""

import discord
from discord.ext import commands
from typing import Optional, Tuple, Dict

from .base_step import BaseStep


class AgeStep(BaseStep):
    """Step 4: Age selection for the character."""
    
    def __init__(self, embed_factory):
        """
        Initialize the age selection step.
        
        Args:
            embed_factory: The embed factory for creating Discord embeds
        """
        super().__init__(step_name="ålder", step_number=4)
        self.embed_factory = embed_factory
        
        # Age recommendations by race
        self.age_recommendations = {
            'alv': {
                'range': "200-800 år",
                'description': "Alver lever mycket länge och mognar långsamt"
            },
            'dvärg': {
                'range': "50-200 år", 
                'description': "Dvärgar lever längre än människor"
            },
            'tirak': {
                'range': "25-80 år",
                'description': "Ungefär som människor"
            },
            'thalask': {
                'range': "20-60 år",
                'description': "Kortare livslängd än andra människofolk"
            },
            'vanare': {
                'range': "20-70 år",
                'description': "Standard mänsklig livslängd"
            }
        }
        
        # Default recommendation for humans
        self.default_recommendation = {
            'range': "20-80 år",
            'description': "Standard för människor"
        }
    
    async def execute(self, ctx: commands.Context, session: 'CharacterSession') -> discord.Embed:
        """
        Execute the age selection step.
        
        Args:
            ctx: Discord command context
            session: Current character creation session
            
        Returns:
            Discord embed displaying the age selection
        """
        embed = self.embed_factory.admin_message(
            session.user_id,
            f"⏰ Steg {self.step_number}/{session.max_steps}: Ålder",
            "Välj rollpersonens ålder:"
        )
        
        # Show race-specific recommendations if race is set
        if 'folkslag' in session.data:
            folkslag = session.data['folkslag'].lower()
            recommendation = self.age_recommendations.get(folkslag, self.default_recommendation)
            
            embed.add_field(
                name=f"🎯 Rekommendation för {session.data['folkslag'].capitalize()}",
                value=f"**{recommendation['range']}**\n*{recommendation['description']}*",
                inline=False
            )
        
        # Show background roll effects
        embed.add_field(
            name="📈 Ålderseffekter på bakgrundslag",
            value=(
                "**16-30 år:** Inga extra slag\n"
                "**31-45 år:** +1 bakgrundslag\n"
                "**46-60 år:** +2 bakgrundslag\n"
                "**61-80 år:** +3 bakgrundslag\n"
                "**81-100 år:** +4 bakgrundslag\n"
                "**100+ år:** +5 bakgrundslag"
            ),
            inline=False
        )
        
        embed.add_field(
            name="📝 Instruktioner",
            value="Skriv ålder som ett nummer",
            inline=False
        )
        
        embed.set_footer(text="Exempel: !chargen 25")
        
        await ctx.send(embed=embed)
        return embed
    
    async def handle_input(self, ctx: commands.Context, session: 'CharacterSession', 
                          input_text: str, *args) -> Tuple[bool, Optional[str]]:
        """
        Handle user input for age selection.
        
        Args:
            ctx: Discord command context
            session: Current character creation session
            input_text: User's input text
            *args: Additional arguments (unused)
            
        Returns:
            Tuple of (success: bool, error_message: Optional[str])
        """
        try:
            age = int(input_text.strip())
            
            # Validate age range
            min_age, max_age = self._get_age_limits(session)
            
            if age < min_age or age > max_age:
                error_msg = (
                    f"❌ Åldern måste vara mellan {min_age} och {max_age} år.\n"
                    f"För din ras ({session.data.get('folkslag', 'okänd')}) rekommenderas: "
                    f"{self._get_race_recommendation(session)}"
                )
                await ctx.send(error_msg)
                return False, f"Age {age} outside valid range {min_age}-{max_age}"
            
            # Store age
            session.data['ålder'] = age
            
            # Calculate background rolls bonus
            background_bonus = self._calculate_background_bonus(age)
            session.data['ålder_bakgrundslag_bonus'] = background_bonus
            
            # Send confirmation with bonus info
            confirmation_embed = discord.Embed(
                title="✅ Ålder bekräftad",
                description=f"Ålder satt till: **{age} år**",
                color=discord.Color.green()
            )
            
            if background_bonus > 0:
                confirmation_embed.add_field(
                    name="📈 Bonus bakgrundslag",
                    value=f"+{background_bonus} extra bakgrundslag på grund av ålder",
                    inline=False
                )
            else:
                confirmation_embed.add_field(
                    name="📋 Bakgrundslag",
                    value="Inga extra bakgrundslag (ung ålder)",
                    inline=False
                )
            
            await ctx.send(embed=confirmation_embed)
            
            return True, None
            
        except ValueError:
            error_msg = (
                "❌ Åldern måste vara ett giltigt nummer.\n"
                f"Exempel: `25` för 25 år"
            )
            await ctx.send(error_msg)
            return False, "Invalid age format"
    
    def validate_prerequisites(self, session: 'CharacterSession') -> Tuple[bool, Optional[str]]:
        """
        Validate that prerequisites for this step are met.
        
        Args:
            session: Current character creation session
            
        Returns:
            Tuple of (valid: bool, error_message: Optional[str])
        """
        # Age step typically comes after gender, homeland, and race
        # But we can be flexible about prerequisites
        return True, None
    
    def _get_age_limits(self, session: 'CharacterSession') -> Tuple[int, int]:
        """
        Get minimum and maximum age limits based on race.
        
        Args:
            session: Current character creation session
            
        Returns:
            Tuple of (min_age, max_age)
        """
        folkslag = session.data.get('folkslag', '').lower()
        
        if folkslag == 'alv':
            return 100, 1200  # Elves live very long
        elif folkslag == 'dvärg':
            return 30, 300   # Dwarves live longer than humans
        elif folkslag == 'tirak':
            return 15, 100   # Similar to humans
        elif folkslag == 'thalask':
            return 15, 80    # Shorter lifespan
        else:
            return 16, 120   # Default human range
    
    def _get_race_recommendation(self, session: 'CharacterSession') -> str:
        """
        Get age recommendation text for the character's race.
        
        Args:
            session: Current character creation session
            
        Returns:
            Recommendation string
        """
        folkslag = session.data.get('folkslag', '').lower()
        recommendation = self.age_recommendations.get(folkslag, self.default_recommendation)
        return recommendation['range']
    
    def _calculate_background_bonus(self, age: int) -> int:
        """
        Calculate bonus background rolls based on age.
        
        Args:
            age: Character's age
            
        Returns:
            Number of bonus background rolls
        """
        if age >= 100:
            return 5
        elif age >= 81:
            return 4
        elif age >= 61:
            return 3
        elif age >= 46:
            return 2
        elif age >= 31:
            return 1
        else:
            return 0
    
    def get_summary(self, session: 'CharacterSession') -> str:
        """
        Get a summary of the selected age.
        
        Args:
            session: Current character creation session
            
        Returns:
            Summary string
        """
        age = session.data.get('ålder', 'Ej valt')
        bonus = session.data.get('ålder_bakgrundslag_bonus', 0)
        
        summary = f"**Ålder:** {age} år"
        if bonus > 0:
            summary += f" (+{bonus} bakgrundslag)"
        
        return summary
    
    def validate_data(self, session: 'CharacterSession') -> bool:
        """
        Validate that age data exists and is valid.
        
        Args:
            session: Current character creation session
            
        Returns:
            True if data is valid, False otherwise
        """
        if 'ålder' not in session.data:
            return False
            
        age = session.data['ålder']
        if not isinstance(age, int):
            return False
            
        min_age, max_age = self._get_age_limits(session)
        return min_age <= age <= max_age
    
    def can_skip(self, session: 'CharacterSession') -> bool:
        """
        Check if this step can be skipped.
        
        Age selection cannot be skipped.
        
        Args:
            session: Current character creation session
            
        Returns:
            Always False - age must be selected
        """
        return False
    
    def get_help_text(self) -> str:
        """
        Get detailed help text for this step.
        
        Returns:
            Help text string
        """
        return (
            f"**Steg {self.step_number}: Ålder**\n\n"
            "Välj din rollpersons ålder. Ålder påverkar antalet bakgrundslag du får "
            "senare i karaktärsskapandet - äldre karaktärer har fler livsupplevelser.\n\n"
            "**Ålderseffekter på bakgrundslag:**\n"
            "• 16-30 år: Inga extra slag\n"
            "• 31-45 år: +1 bakgrundslag\n"
            "• 46-60 år: +2 bakgrundslag\n"
            "• 61-80 år: +3 bakgrundslag\n"
            "• 81-100 år: +4 bakgrundslag\n"
            "• 100+ år: +5 bakgrundslag\n\n"
            "**Rasspecifika rekommendationer:**\n"
            "• **Alver:** 200-800 år (lever mycket länge)\n"
            "• **Dvärgar:** 50-200 år (lever längre än människor)\n"
            "• **Tiraker:** 25-80 år (som människor)\n"
            "• **Människor:** 20-80 år (standard)\n\n"
            "Skriv önskad ålder som ett nummer."
        )