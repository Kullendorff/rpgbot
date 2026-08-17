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
    FEAR_TABLE,
    MUMMY_ATTACK_TABLE,
    DiceTermResult,
    FlatTermResult,
    ExpressionResult,
    SkillCheckResult,
    InitiativeEntry,
    AdvancementResult,
    FearResult,
    MummyAttackResult,
    roll_expression,
    dragonbane_skill_check,
    dragonbane_skill_advancement,
    roll_fear_table,
    roll_mummy_attack,
    roll_initiative,
)

__all__ = [
    "CONDITIONS",
    "CONDITION_BY_ATTR",
    "ATTRIBUTES",
    "FEAR_TABLE",
    "MUMMY_ATTACK_TABLE",
    "DiceTermResult",
    "FlatTermResult",
    "ExpressionResult",
    "SkillCheckResult",
    "InitiativeEntry",
    "AdvancementResult",
    "FearResult",
    "MummyAttackResult",
    "roll_expression",
    "dragonbane_skill_check",
    "dragonbane_skill_advancement",
    "roll_fear_table",
    "roll_mummy_attack",
    "roll_initiative",
]
