"""
Character Creation Module for EON Discord Bot

This module provides a comprehensive character creation system for the EON RPG.
It supports multiple races (humans, elves, dwarves, tiraks) with a 32-step
interactive creation process.
"""

from .session import CharacterSession

__all__ = ['CharacterSession']