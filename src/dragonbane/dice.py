"""
Ren tärninglogik för Dragonbane. Fristående och testbar (injicerbar Random).

Ursprung: Jonas (github.com/jonsal/dragonbane). Anpassad och regelrättad:
  * Initiativ dras som kortlek (unika 1-10, lägst agerar först) i stället
    för T10 med återläggning sorterat högst först.
  * Tillstånd kan bindas till grundegenskap i stället för att alltid slumpas.
"""

from __future__ import annotations

from dataclasses import dataclass
from random import Random
import re


_VALID_EXPR_RE = re.compile(r"^[0-9dDtT+\-\s]+$")

# Grundegenskaper i Dragonbane och tillståndet de styr.
ATTRIBUTES: tuple[str, ...] = ("STY", "FYS", "SMI", "INT", "PSY", "KAR")

CONDITION_BY_ATTR: dict[str, str] = {
    "STY": "Utmattad",
    "FYS": "Krasslig",
    "SMI": "Omtöcknad",
    "INT": "Arg",
    "PSY": "Rädd",
    "KAR": "Uppgiven",
}

# (tillstånd, grundegenskap) för slumpval när grundegenskap inte angetts.
CONDITIONS: tuple[tuple[str, str], ...] = tuple(
    (condition, attr) for attr, condition in CONDITION_BY_ATTR.items()
)


@dataclass
class DiceTermResult:
    sign: int
    count: int
    sides: int
    rolls: list[int]

    @property
    def subtotal(self) -> int:
        return self.sign * sum(self.rolls)

    @property
    def label(self) -> str:
        base = f"{self.count}d{self.sides}"
        return f"-{base}" if self.sign < 0 else base


@dataclass
class FlatTermResult:
    value: int


@dataclass
class ExpressionResult:
    expression: str
    dice_terms: list[DiceTermResult]
    flat_terms: list[FlatTermResult]
    total: int


@dataclass
class SkillCheckResult:
    skill: int
    modifier: int
    target: int
    mode: str
    rolls: list[int]
    chosen_roll: int
    success: bool
    critical: str | None


@dataclass
class InitiativeEntry:
    name: str
    card: int


def _parse_term(raw_term: str) -> tuple[str, int]:
    sign = 1
    term = raw_term
    if term.startswith("+"):
        term = term[1:]
    elif term.startswith("-"):
        sign = -1
        term = term[1:]
    return term, sign


def roll_expression(expression: str, rng: Random | None = None) -> ExpressionResult:
    """Slå ett tärningsuttryck, t.ex. '2T6+1T8+3'. Accepterar både T och d."""
    rng = rng or Random()
    expr = expression.strip()
    if not expr:
        raise ValueError("Uttrycket är tomt")
    if not _VALID_EXPR_RE.match(expr):
        raise ValueError("Uttrycket innehåller ogiltiga tecken")

    # Normalisera svenskt T till d internt.
    compact = expr.replace(" ", "").replace("T", "d").replace("D", "d")
    if compact[0] == "d":
        compact = f"1{compact}"

    terms = re.findall(r"[+-]?[^+-]+", compact)
    if not terms:
        raise ValueError("Kunde inte tolka uttrycket")

    dice_terms: list[DiceTermResult] = []
    flat_terms: list[FlatTermResult] = []
    total = 0

    for raw_term in terms:
        term, sign = _parse_term(raw_term)
        if not term:
            raise ValueError("Ogiltig tom term i uttrycket")

        if "d" in term:
            parts = term.split("d")
            if len(parts) != 2:
                raise ValueError(f"Ogiltig tärningsterm: {raw_term}")

            count_str, sides_str = parts
            if not sides_str:
                raise ValueError(f"Ogiltig tärningsterm: {raw_term}")
            count = int(count_str) if count_str else 1
            sides = int(sides_str)

            if count <= 0 or count > 100:
                raise ValueError("Antal tärningar måste vara mellan 1 och 100")
            if sides <= 1 or sides > 1000:
                raise ValueError("Tärningssidor måste vara mellan 2 och 1000")

            rolls = [rng.randint(1, sides) for _ in range(count)]
            term_result = DiceTermResult(sign=sign, count=count, sides=sides, rolls=rolls)
            dice_terms.append(term_result)
            total += term_result.subtotal
        else:
            value = int(term) * sign
            flat_terms.append(FlatTermResult(value=value))
            total += value

    return ExpressionResult(
        expression=expression,
        dice_terms=dice_terms,
        flat_terms=flat_terms,
        total=total,
    )


def dragonbane_skill_check(
    skill: int,
    modifier: int = 0,
    mode: str = "normal",
    rng: Random | None = None,
) -> SkillCheckResult:
    """Färdighetsslag på T20. Slag <= målvärde lyckas. 1 = drake, 20 = demon."""
    rng = rng or Random()

    if skill < 1 or skill > 30:
        raise ValueError("Färdighetsvärde måste vara mellan 1 och 30")
    if modifier < -10 or modifier > 10:
        raise ValueError("Modifikation måste vara mellan -10 och +10")

    normalized_mode = mode.lower().strip()
    if normalized_mode not in {"normal", "fördel", "nackdel"}:
        raise ValueError("Läge måste vara normal, fördel eller nackdel")

    target = max(1, min(30, skill + modifier))
    if normalized_mode == "normal":
        rolls = [rng.randint(1, 20)]
        chosen_roll = rolls[0]
    else:
        rolls = [rng.randint(1, 20), rng.randint(1, 20)]
        chosen_roll = min(rolls) if normalized_mode == "fördel" else max(rolls)

    critical: str | None = None
    if chosen_roll == 1:
        critical = "dragon"
        success = True
    elif chosen_roll == 20:
        critical = "demon"
        success = False
    else:
        success = chosen_roll <= target

    return SkillCheckResult(
        skill=skill,
        modifier=modifier,
        target=target,
        mode=normalized_mode,
        rolls=rolls,
        chosen_roll=chosen_roll,
        success=success,
        critical=critical,
    )


def roll_initiative(
    names: list[str],
    rng: Random | None = None,
) -> list[InitiativeEntry]:
    """
    Dra initiativ enligt Dragonbane: kortlek 1-10, unika kort, lägst agerar
    först. Vid fler än 10 stridande används flera lekar (då kan kortvärden
    upprepas, ties bryts av dragordning).
    """
    rng = rng or Random()
    if not names:
        return []

    deck: list[int] = []
    while len(deck) < len(names):
        chunk = list(range(1, 11))
        rng.shuffle(chunk)
        deck.extend(chunk)

    cards = deck[: len(names)]
    entries = [InitiativeEntry(name=name, card=card) for name, card in zip(names, cards)]
    # Stabil sortering: lägst kort först, ties i ursprunglig ordning.
    entries.sort(key=lambda e: e.card)
    return entries
