"""
Delta Green dice mechanics.

Implements the d100 percentile system with Delta Green-specific rules:
- Roll under or equal to skill = success
- Critical success: 01, or matching digits on success (11, 22, 33, 44)
- Fumble: 00 (100), or matching digits on failure (55, 66, 77, 88, 99)
- Lethality: instant kill on success, sum of dice as damage on failure
"""

import random
import re
from dataclasses import dataclass
from typing import Optional, Tuple
from enum import Enum


class RollResult(Enum):
    """Result of a d100 roll."""
    CRITICAL_SUCCESS = "critical_success"
    SUCCESS = "success"
    FAILURE = "failure"
    FUMBLE = "fumble"


@dataclass
class D100Result:
    """Result of a d100 roll."""
    roll: int                    # The actual d100 result (1-100)
    tens_die: int               # Tens digit (0-9, where 0 = 10)
    ones_die: int               # Ones digit (0-9, where 0 = 10)
    target: int                 # Target number to roll under
    result: RollResult          # Critical/Success/Failure/Fumble
    is_matched: bool            # True if tens == ones (11, 22, etc.)
    margin: int                 # Difference from target (negative = success)


@dataclass
class LethalityResult:
    """Result of a lethality roll."""
    roll: int
    tens_die: int
    ones_die: int
    rating: int                 # Lethality percentage
    is_lethal: bool            # True if instant kill
    damage: Optional[int]       # Sum of dice if not lethal


@dataclass
class SanCheckResult:
    """Result of a SAN check."""
    roll_result: D100Result     # The underlying d100 roll
    san_before: int
    san_loss: int               # Actual loss based on success/failure
    san_after: int
    triggered_temporary_insanity: bool  # 5+ SAN in one check


def roll_d100() -> Tuple[int, int, int]:
    """
    Roll d100 and return (total, tens_die, ones_die).

    Returns:
        Tuple of (roll 1-100, tens digit 0-9, ones digit 0-9)
        Note: 00 on both dice = 100, 0 on single die represents 10
    """
    tens = random.randint(0, 9)
    ones = random.randint(0, 9)

    # Calculate total: both 00 = 100, otherwise (tens * 10) + ones
    if tens == 0 and ones == 0:
        total = 100
    else:
        total = (tens * 10) + ones

    return total, tens, ones


def evaluate_result(roll: int, target: int, tens: int, ones: int) -> RollResult:
    """
    Evaluate a d100 roll against a target value.

    Delta Green critical/fumble rules:
    - Critical Success: 01, OR matching digits (11,22,33,44) on success
    - Fumble: 100 (00), OR matching digits (55,66,77,88,99) on failure

    Args:
        roll: d100 result (1-100)
        target: Target to roll under or equal to
        tens: Tens die (0-9)
        ones: Ones die (0-9)

    Returns:
        RollResult enum value
    """
    is_success = roll <= target
    is_matched = tens == ones

    # Check for critical success
    if roll == 1:
        return RollResult.CRITICAL_SUCCESS

    # Check for fumble
    if roll == 100:
        return RollResult.FUMBLE

    # Matched digits
    if is_matched:
        if is_success:
            return RollResult.CRITICAL_SUCCESS
        else:
            return RollResult.FUMBLE

    # Regular success or failure
    return RollResult.SUCCESS if is_success else RollResult.FAILURE


def skill_check(skill_value: int, modifier: int = 0) -> D100Result:
    """
    Perform a Delta Green skill check.

    Args:
        skill_value: Base skill percentage (0-99)
        modifier: Bonus/penalty to skill (+20, -40, etc.)

    Returns:
        D100Result with all roll details
    """
    target = max(0, min(99, skill_value + modifier))
    roll, tens, ones = roll_d100()
    result = evaluate_result(roll, target, tens, ones)

    return D100Result(
        roll=roll,
        tens_die=tens,
        ones_die=ones,
        target=target,
        result=result,
        is_matched=(tens == ones),
        margin=roll - target
    )


def stat_test(stat_value: int) -> D100Result:
    """
    Perform a STAT x 5 test (STR, DEX, CON, INT, POW, CHA).

    Args:
        stat_value: Raw stat value (3-18 typically)

    Returns:
        D100Result against STAT * 5 target
    """
    target = stat_value * 5
    roll, tens, ones = roll_d100()
    result = evaluate_result(roll, target, tens, ones)

    return D100Result(
        roll=roll,
        tens_die=tens,
        ones_die=ones,
        target=target,
        result=result,
        is_matched=(tens == ones),
        margin=roll - target
    )


def luck_roll() -> D100Result:
    """
    50% luck roll - used when no skill applies.

    Returns:
        D100Result with 50% target
    """
    return skill_check(50, 0)


def lethality_roll(rating: int) -> LethalityResult:
    """
    Perform a lethality roll.

    If roll <= rating: instant kill
    If roll > rating: damage = sum of dice (treating 0 as 10)

    Args:
        rating: Lethality percentage (e.g., 10, 15, 20)

    Returns:
        LethalityResult with kill status or damage if non-lethal
    """
    roll, tens, ones = roll_d100()
    is_lethal = roll <= rating

    # Calculate damage if not lethal
    damage = None
    if not is_lethal:
        tens_value = 10 if tens == 0 else tens
        ones_value = 10 if ones == 0 else ones
        damage = tens_value + ones_value

    return LethalityResult(
        roll=roll,
        tens_die=tens,
        ones_die=ones,
        rating=rating,
        is_lethal=is_lethal,
        damage=damage
    )


def parse_san_loss(loss_str: str) -> int:
    """
    Parse and roll a SAN loss string.

    Args:
        loss_str: "0", "1", "1d4", "1d6", "1d10", etc.

    Returns:
        Actual loss amount (rolled if dice expression)
    """
    loss_str = loss_str.strip()

    # Simple number
    if loss_str.isdigit():
        return int(loss_str)

    # Dice expression: XdY or XdY+Z
    match = re.match(r'(\d+)d(\d+)(?:\+(\d+))?', loss_str.lower())
    if match:
        num_dice = int(match.group(1))
        die_size = int(match.group(2))
        modifier = int(match.group(3)) if match.group(3) else 0

        total = sum(random.randint(1, die_size) for _ in range(num_dice))
        return total + modifier

    # Default to 0 if can't parse
    return 0


def san_check(
    current_san: int,
    success_loss: str,
    failure_loss: str,
) -> SanCheckResult:
    """
    Perform a SAN check.

    Args:
        current_san: Agent's current SAN score
        success_loss: SAN loss on success (e.g., "0", "1", "1d4")
        failure_loss: SAN loss on failure (e.g., "1", "1d6", "1d10")

    Returns:
        SanCheckResult with full breakdown
    """
    # Roll against current SAN
    roll_result = skill_check(current_san, 0)

    # Determine loss based on success/failure
    if roll_result.result in (RollResult.SUCCESS, RollResult.CRITICAL_SUCCESS):
        san_loss = parse_san_loss(success_loss)
    else:
        san_loss = parse_san_loss(failure_loss)

    san_after = max(0, current_san - san_loss)
    triggered_temporary_insanity = san_loss >= 5

    return SanCheckResult(
        roll_result=roll_result,
        san_before=current_san,
        san_loss=san_loss,
        san_after=san_after,
        triggered_temporary_insanity=triggered_temporary_insanity
    )
