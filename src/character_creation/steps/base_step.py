"""
Base Step Class for Character Creation

This module defines the abstract base class for all character creation steps.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import discord
from discord.ext import commands


class BaseStep(ABC):
    """Abstract base class for character creation steps."""
    
    def __init__(self, step_name: str, step_number: int):
        """
        Initialize a character creation step.
        
        Args:
            step_name: The name of this step
            step_number: The step number in the creation process
        """
        self.step_name = step_name
        self.step_number = step_number
        self.next_step = None
        self.previous_step = None
    
    @abstractmethod
    async def execute(self, ctx: commands.Context, session: 'CharacterSession') -> discord.Embed:
        """
        Execute this step of character creation.
        
        Args:
            ctx: Discord command context
            session: Current character creation session
            
        Returns:
            Discord embed displaying the step
        """
        pass
    
    @abstractmethod
    async def handle_input(self, ctx: commands.Context, session: 'CharacterSession', 
                          input_text: str, *args) -> tuple[bool, Optional[str]]:
        """
        Handle user input for this step.
        
        Args:
            ctx: Discord command context
            session: Current character creation session
            input_text: User's input text
            *args: Additional arguments
            
        Returns:
            Tuple of (success: bool, error_message: Optional[str])
        """
        pass
    
    @abstractmethod
    def validate_prerequisites(self, session: 'CharacterSession') -> tuple[bool, Optional[str]]:
        """
        Validate that prerequisites for this step are met.
        
        Args:
            session: Current character creation session
            
        Returns:
            Tuple of (valid: bool, error_message: Optional[str])
        """
        pass
    
    def get_step_data(self, session: 'CharacterSession') -> Dict[str, Any]:
        """
        Get data relevant to this step from the session.
        
        Args:
            session: Current character creation session
            
        Returns:
            Dictionary of step-specific data
        """
        return session.character_data.get(self.step_name, {})
    
    def save_step_data(self, session: 'CharacterSession', data: Dict[str, Any]) -> None:
        """
        Save step data to the session.
        
        Args:
            session: Current character creation session
            data: Data to save
        """
        if self.step_name not in session.character_data:
            session.character_data[self.step_name] = {}
        session.character_data[self.step_name].update(data)
    
    def can_skip(self, session: 'CharacterSession') -> bool:
        """
        Check if this step can be skipped.
        
        Args:
            session: Current character creation session
            
        Returns:
            True if step can be skipped, False otherwise
        """
        return False
    
    def get_help_text(self) -> str:
        """
        Get help text for this step.
        
        Returns:
            Help text string
        """
        return f"Steg {self.step_number}: {self.step_name}"
    
    def __repr__(self) -> str:
        return f"<Step {self.step_number}: {self.step_name}>"