"""
Star Wars: The Roleplaying Game, 2nd Edition, Revised & Expanded (WEG40120)
modul för EON Discord Bot.

Ett fristående spelsystem inbultat i samma bot, på samma sätt som
deltagreen/ och dragonbane/. Regler verifierade mot källboken (inte bara
OCR-texten), se docstring i dice.py för sidhänvisningar.
"""

from .dice import (
    DIFFICULTY_LEVELS, MAX_DICE, MAX_PIPS, MAX_EXPLOSIONS,
    DiceCode, WildDieResult, SWRollResult, OpposedResult,
    parse_dice_code, apply_multiple_actions, roll, add_character_point_die,
    difficulty_band, opposed,
)

__all__ = [
    'DIFFICULTY_LEVELS',
    'MAX_DICE',
    'MAX_PIPS',
    'MAX_EXPLOSIONS',
    'DiceCode',
    'WildDieResult',
    'SWRollResult',
    'OpposedResult',
    'parse_dice_code',
    'apply_multiple_actions',
    'roll',
    'add_character_point_die',
    'difficulty_band',
    'opposed',
]
