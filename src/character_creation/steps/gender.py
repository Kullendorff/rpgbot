"""
Gender Selection Step for Character Creation

This module handles the first step of character creation where the player
selects their character's gender.
"""

import discord
from discord.ext import commands
from typing import Optional, Tuple

from .base_step import BaseStep


class GenderStep(BaseStep):
    """Step 1: Gender selection for the character."""
    
    def __init__(self, embed_factory):
        """
        Initialize the gender selection step.
        
        Args:
            embed_factory: The embed factory for creating Discord embeds
        """
        super().__init__(step_name="kön", step_number=1)
        self.embed_factory = embed_factory
        
        # Gender mapping for input validation
        self.gender_map = {
            '1': 'kvinna', 
            'kvinna': 'kvinna', 
            'female': 'kvinna',
            'f': 'kvinna',
            '2': 'man', 
            'man': 'man', 
            'male': 'man',
            'm': 'man',
            '3': 'annat', 
            'annat': 'annat', 
            'icke-binärt': 'annat',
            'icke-binär': 'annat',
            'ickebinär': 'annat',
            'ickebinärt': 'annat', 
            'other': 'annat',
            'o': 'annat',
            'nb': 'annat',
            'non-binary': 'annat',
            'nonbinary': 'annat'
        }
    
    async def execute(self, ctx: commands.Context, session: 'CharacterSession') -> discord.Embed:
        """
        Execute the gender selection step.
        
        Args:
            ctx: Discord command context
            session: Current character creation session
            
        Returns:
            Discord embed displaying the gender selection options
        """
        embed = self.embed_factory.admin_message(
            session.user_id,
            f"Steg {self.step_number}/{session.max_steps}: Kön",
            "Välj rollpersonens kön:"
        )
        
        embed.add_field(
            name="Val",
            value="1. Kvinna\n2. Man\n3. Annat/icke-binärt",
            inline=False
        )
        
        embed.add_field(
            name="📝 Instruktioner",
            value="Skriv ditt val (nummer eller text)",
            inline=False
        )
        
        embed.set_footer(text="Exempel: !chargen kvinna, !chargen 1, eller !chargen annat")
        
        await ctx.send(embed=embed)
        return embed
    
    async def handle_input(self, ctx: commands.Context, session: 'CharacterSession', 
                          input_text: str, *args) -> Tuple[bool, Optional[str]]:
        """
        Handle user input for gender selection.
        
        Args:
            ctx: Discord command context
            session: Current character creation session
            input_text: User's input text
            *args: Additional arguments (unused)
            
        Returns:
            Tuple of (success: bool, error_message: Optional[str])
        """
        input_lower = input_text.lower().strip()
        
        # Check if input is valid
        if input_lower not in self.gender_map:
            error_msg = (
                "❌ Ogiltigt val. Giltiga alternativ:\n"
                "• **Kvinna** (eller 1, f, female)\n"
                "• **Man** (eller 2, m, male)\n"
                "• **Annat** (eller 3, nb, icke-binärt, non-binary)"
            )
            await ctx.send(error_msg)
            return False, "Invalid gender selection"
        
        # Store the selected gender
        selected_gender = self.gender_map[input_lower]
        session.data['kön'] = selected_gender
        
        # Update context
        session.update_context()
        
        # Send confirmation
        confirmation_embed = discord.Embed(
            title="✅ Val bekräftat",
            description=f"Kön satt till: **{selected_gender.capitalize()}**",
            color=discord.Color.green()
        )
        await ctx.send(embed=confirmation_embed)
        
        return True, None
    
    def validate_prerequisites(self, session: 'CharacterSession') -> Tuple[bool, Optional[str]]:
        """
        Validate that prerequisites for this step are met.
        
        Since this is the first step, there are no prerequisites.
        
        Args:
            session: Current character creation session
            
        Returns:
            Tuple of (valid: bool, error_message: Optional[str])
        """
        # First step has no prerequisites
        return True, None
    
    def get_summary(self, session: 'CharacterSession') -> str:
        """
        Get a summary of the selected gender.
        
        Args:
            session: Current character creation session
            
        Returns:
            Summary string
        """
        gender = session.data.get('kön', 'Ej valt')
        return f"**Kön:** {gender.capitalize()}"
    
    def validate_data(self, session: 'CharacterSession') -> bool:
        """
        Validate that gender data exists and is valid.
        
        Args:
            session: Current character creation session
            
        Returns:
            True if data is valid, False otherwise
        """
        return 'kön' in session.data and session.data['kön'] in ['kvinna', 'man', 'annat']
    
    def can_skip(self, session: 'CharacterSession') -> bool:
        """
        Check if this step can be skipped.
        
        Gender selection cannot be skipped.
        
        Args:
            session: Current character creation session
            
        Returns:
            Always False - gender must be selected
        """
        return False
    
    def get_help_text(self) -> str:
        """
        Get detailed help text for this step.
        
        Returns:
            Help text string
        """
        return (
            f"**Steg {self.step_number}: Kön**\n\n"
            "Detta är det första steget i karaktärsskapandet. Du måste välja ett kön "
            "för din rollperson. Detta val påverkar inte spelmekaniken direkt men kan "
            "ha betydelse för rollspel och vissa kulturella aspekter.\n\n"
            "**Alternativ:**\n"
            "• **Kvinna** - Kvinnlig rollperson\n"
            "• **Man** - Manlig rollperson\n"
            "• **Annat** - Icke-binär eller annat könsuttryck\n\n"
            "Skriv ditt val som text eller nummer."
        )