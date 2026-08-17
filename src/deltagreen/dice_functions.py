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


@dataclass
class ProjectionResult:
    """
    Result of "Projecting Onto a Bond" (Delta Green Agent's Handbook).

    Rule summary: When an Agent loses SAN, the player may roll 1D4 and spend
    that much WP. If the Agent still has at least 1 WP after the cost, the SAN
    loss is reduced by the rolled amount (to a minimum of 0) and the chosen
    Bond's score is reduced by the same amount. If the Agent no longer has
    at least 1 WP, the projection fails: WP drops (the Agent falls unconscious
    at 0 WP), no SAN is reduced, and no Bond damage is dealt.
    """
    d4_roll: int                    # The 1D4 rolled
    wp_before: int
    wp_after: int
    unconscious: bool               # True if WP reached 0 (handled globally elsewhere)
    projection_succeeded: bool      # True if SAN reduction applied
    san_loss_original: int          # SAN loss before projection
    san_loss_reduced: int           # SAN loss after projection (== original if failed)
    bond_before: int
    bond_after: int
    bond_broken: bool               # Bond reduced to 0, permanently broken
    ti_originally_triggered: bool   # Was TI (>=5) triggered by the original loss?
    ti_avoided: bool                # True iff TI was triggered but no longer is


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


def project_onto_bond(
    current_wp: int,
    san_loss: int,
    bond_value: int,
) -> ProjectionResult:
    """
    Perform "Projecting Onto a Bond" (Delta Green Agent's Handbook).

    Mechanics:
      1. Roll 1D4.
      2. Reduce WP by that amount (cap at 0).
      3. If WP >= 1 after the cost: reduce SAN loss by D4 (min 0) and reduce
         the Bond's score by D4 (min 0; Bond is broken at 0).
      4. If WP < 1 after the cost: projection FAILS. No SAN reduction, no
         Bond damage. Agent is unconscious (caller is responsible for setting
         the unconscious flag on the agent — this function only reports it).

    This function is pure: it does not mutate any agent state. The caller
    applies the WP change, SAN adjustment, Bond change and unconscious state.

    Args:
        current_wp: Agent's WP before projection. Must be >= 1 for a meaningful
            attempt (caller should pre-check).
        san_loss: SAN loss just determined by a SAN check.
        bond_value: Current Bond score of the target Bond. Must be >= 1
            (caller should pre-check; broken Bonds cannot be projected onto).

    Returns:
        ProjectionResult with full breakdown.
    """
    d4_roll = random.randint(1, 4)
    wp_after = max(0, current_wp - d4_roll)

    # Per RAW: "If your Agent still has at least 1 WP, reduce the SAN loss..."
    projection_succeeded = wp_after >= 1
    unconscious = wp_after <= 0

    if projection_succeeded:
        san_loss_reduced = max(0, san_loss - d4_roll)
        bond_after = max(0, bond_value - d4_roll)
        bond_broken = bond_after == 0
    else:
        # Projection fails — WP was spent but no mitigation applied.
        san_loss_reduced = san_loss
        bond_after = bond_value
        bond_broken = False

    ti_originally_triggered = san_loss >= 5
    ti_still_triggered = san_loss_reduced >= 5
    ti_avoided = ti_originally_triggered and not ti_still_triggered

    return ProjectionResult(
        d4_roll=d4_roll,
        wp_before=current_wp,
        wp_after=wp_after,
        unconscious=unconscious,
        projection_succeeded=projection_succeeded,
        san_loss_original=san_loss,
        san_loss_reduced=san_loss_reduced,
        bond_before=bond_value,
        bond_after=bond_after,
        bond_broken=bond_broken,
        ti_originally_triggered=ti_originally_triggered,
        ti_avoided=ti_avoided,
    )
