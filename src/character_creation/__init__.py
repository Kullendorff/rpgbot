"""
Character Creation Module for EON Discord Bot

This module provides a comprehensive character creation system for the EON RPG.
It supports multiple races (humans, elves, dwarves, tiraks) with a 32-step
interactive creation process.
"""

from .session import CharacterSession

# Import register_commands from the legacy character creation file to maintain compatibility
try:
    from character_creation_legacy import register_commands
except ImportError:
    print("Warning: Could not import register_commands from character_creation_legacy.py")
    register_commands = None

__all__ = ['CharacterSession', 'register_commands']