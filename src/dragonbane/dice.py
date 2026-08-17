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

# Skräcktabellen (T8): slås vid misslyckat PSY-slag mot en skräckattack.
FEAR_TABLE: dict[int, tuple[str, str]] = {
    1: (
        "Kraftlös",
        "Fasan tömmer dig på kraft och beslutsamhet. Du förlorar 2T6 VP "
        "(lägst 0) och får tillståndet Uppgiven.",
    ),
    2: (
        "Skakis",
        "Du drabbas av plötslig darrning och får tillståndet Rädd.",
    ),
    3: (
        "Flämtar",
        "Fasan gör dig så skräckslagen att du börjar andas kraftigt och "
        "får tillståndet Utmattad.",
    ),
    4: (
        "Blek",
        "Du blir vit som ett lakan i ansiktet. Du och alla andra "
        "rollpersoner inom 10 meter som ser dig får tillståndet Rädd.",
    ),
    5: (
        "Skrik",
        "Du utstöter ett högt skrik av fasa. Alla andra rollpersoner som "
        "hör dig utsätts omedelbart för en skräckattack (max ett PSY-slag "
        "per skräckkälla).",
    ),
    6: (
        "Vredesmod",
        "Din skräck förvandlas till vrede. Du måste angripa källan till "
        "skräcken på din nästa tur (i närstrid om möjligt) och får "
        "tillståndet Arg.",
    ),
    7: (
        "Paralyserad",
        "Du stelnar av skräck och kan varken agera eller förflytta dig på "
        "din nästa tur. Inför varje påföljande tur krävs ett nytt PSY-slag "
        "(ej handling) för att bryta förlamningen.",
    ),
    8: (
        "Vild panik",
        "Du drabbas av total panik och flyr i högsta fart. På din nästa "
        "tur måste du sprinta bort från skräckkällan, och lyckas med ett "
        "nytt PSY-slag (ej handling) inför varje påföljande tur för att "
        "återfå kontrollen.",
    ),
}

# Mumiens anfallstabell (T6): monsterspecifik attack för mumie-motståndare.
MUMMY_ATTACK_TABLE: dict[int, tuple[str, str]] = {
    1: (
        "Förbannelse!",
        "Kastar en förbannelse över en motståndare inom 10 meter. Offret "
        "utsätts för en skräckattack med nackdel på PSY-slaget.",
    ),
    2: (
        "Dubbelslag!",
        "Mumien slår med nävarna mot upp till två motståndare inom 2 "
        "meter från varandra. De tar 2T6 krosskada och slås till marken.",
    ),
    3: (
        "Insektssvärm!",
        "Mumien spyr ut insekter över alla motståndare inom 4 meter. "
        "Dessa tar T8 i skada (rustning skyddar inte) och måste lyckas "
        "med ett PSY-slag för att inte förlora sin tur.",
    ),
    4: (
        "Dödligt nappatag!",
        "Mumien greppar och slungar iväg en motståndare 2T6 meter. "
        "Offret landar liggande och tar lika mycket skada som avståndet.",
    ),
    5: (
        "Strypning!",
        "Mumien tar ett strypgrepp på en motståndare. Offret tar 2T6 "
        "krosskada direkt (ingen rustning) och ytterligare T6 vid varje "
        "ny tur för mumien. Kräv ett slag mot STY med nackdel för att "
        "komma loss.",
    ),
    6: (
        "Hjärtkross!",
        "Mumiens ögon lyser blått och den försöker krossa offrets hjärta "
        "på avstånd (upp till 10 meter). Offret tar T10 i skada (ingen "
        "rustning), utsätts för en skräckattack och förlorar sin tur.",
    ),
}


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


@dataclass
class AdvancementResult:
    skill: int
    roll: int
    success: bool
    new_skill: int


@dataclass
class FearResult:
    roll: int
    condition: str
    description: str
    vp_loss: int | None = None


@dataclass
class MummyAttackResult:
    roll: int
    name: str
    description: str


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


def dragonbane_skill_advancement(
    skill: int,
    rng: Random | None = None,
) -> AdvancementResult:
    """
    Färdighetsförbättring: slå 1T20. Slår du högre än nuvarande FV ökar
    färdigheten med 1 (regelrätt Dragonbane-mekanik). Eftersom T20 aldrig
    kan ge mer än 20 är FV 20 eller högre praktiskt taget omöjligt att
    förbättra vidare.
    """
    rng = rng or Random()

    if skill < 1 or skill > 30:
        raise ValueError("Färdighetsvärde måste vara mellan 1 och 30")

    roll = rng.randint(1, 20)
    success = roll > skill
    new_skill = skill + 1 if success else skill

    return AdvancementResult(skill=skill, roll=roll, success=success, new_skill=new_skill)


def roll_fear_table(rng: Random | None = None) -> FearResult:
    """
    Skräcktabellen: slå 1T8 och läs av resultatet. Används vid misslyckat
    PSY-slag mot en skräckattack. Vid resultat 1 (Kraftlös) slås även
    2T6 VP-förlust (i praktiken lägst 0, hanteras av den som bokför VP).
    """
    rng = rng or Random()

    roll = rng.randint(1, 8)
    condition, description = FEAR_TABLE[roll]

    vp_loss = None
    if roll == 1:
        vp_loss = rng.randint(1, 6) + rng.randint(1, 6)

    return FearResult(roll=roll, condition=condition, description=description, vp_loss=vp_loss)


def roll_mummy_attack(rng: Random | None = None) -> MummyAttackResult:
    """Mumiens anfallstabell: slå 1T6 och läs av vilken attack mumien gör."""
    rng = rng or Random()

    roll = rng.randint(1, 6)
    name, description = MUMMY_ATTACK_TABLE[roll]

    return MummyAttackResult(roll=roll, name=name, description=description)


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
