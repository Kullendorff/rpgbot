"""
Dragonbane (Drakar och Demoner) modul för EON Discord Bot.

Ett fristående spelsystem inbultat i samma bot, på samma sätt som deltagreen/.
Ursprunglig tärninglogik byggd av Jonas (github.com/jonsal/dragonbane),
anpassad till botens arkitektur (Cog + embed_factory) och med rättade
regelavvikelser (initiativ som kortlek, deterministiska tillstånd).
"""

from .dice import (
    CONDITIONS,
    CONDITION_BY_ATTR,
    ATTRIBUTES,
    DiceTermResult,
    FlatTermResult,
    ExpressionResult,
    SkillCheckResult,
    InitiativeEntry,
    roll_expression,
    dragonbane_skill_check,
    roll_initiative,
)

__all__ = [
    "CONDITIONS",
    "CONDITION_BY_ATTR",
    "ATTRIBUTES",
    "DiceTermResult",
    "FlatTermResult",
    "ExpressionResult",
    "SkillCheckResult",
    "InitiativeEntry",
    "roll_expression",
    "dragonbane_skill_check",
    "roll_initiative",
]
