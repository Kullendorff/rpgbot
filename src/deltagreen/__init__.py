"""
Delta Green RPG module for Discord bot.

This module provides dice rolling and character management for the Delta Green RPG,
using the d100 percentile system.
"""

from .dice_functions import (
    RollResult,
    D100Result,
    LethalityResult,
    SanCheckResult,
    roll_d100,
    evaluate_result,
    skill_check,
    stat_test,
    luck_roll,
    lethality_roll,
    san_check,
    parse_san_loss,
)

from .agent_manager import AgentManager
from .session_manager import SessionManager

__all__ = [
    'RollResult',
    'D100Result',
    'LethalityResult',
    'SanCheckResult',
    'roll_d100',
    'evaluate_result',
    'skill_check',
    'stat_test',
    'luck_roll',
    'lethality_roll',
    'san_check',
    'parse_san_loss',
    'AgentManager',
    'SessionManager',
]
