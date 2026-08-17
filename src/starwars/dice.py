"""
Ren tärninglogik för Star Wars: The Roleplaying Game, 2nd Edition, Revised
& Expanded (WEG40120). Fristående och testbar (injicerbar Random), inga
discord-beroenden.

Regelkällor, verifierade mot boken (inte OCR-texten):
  * Grundmekanik och svårighetstal: kapitlet "Rolling Actions".
  * Wild Die, explosion på 6 (s. 20): räknas in och slås om, obegränsat.
  * Wild Die, etta (s. 72-73): "for the first roll only" — endast det
    FÖRSTA slaget på Wild Die utlöser SL:s val mellan tre utfall. En etta
    som dyker upp längre in i en explosionskedja (t.ex. 6 -> 1) är bara en
    vanlig etta.
  * Character Points (s. 81, "Character Elements"): en spenderad CP ger en
    ny tärning som ALSO exploderar på 6 (samma mekanik som Wild Die), men
    saknar 1:e-specialregeln — en etta på en CP-tärning läggs bara till
    normalt, inget SL-val.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from random import Random
import re


# Antal tärningar respektive pips är praktiskt begränsade, inte regelmässigt
# begränsade — skydd mot orimlig input snarare än en regelgräns.
MAX_DICE = 100
MAX_PIPS = 99

# Skydd mot en trasig/stubbad rng som alltid ger 6 (regeln själv saknar tak
# på hur många gånger en Wild Die eller CP-tärning kan explodera).
MAX_EXPLOSIONS = 100

_DICE_CODE_RE = re.compile(r"^\s*(\d+)\s*[Dd]?\s*(\+\s*\d+)?\s*$")

# (namn, lägsta, högsta) — Heroic saknar egentligt tak i källan; 10 000 är
# gott om marginal (en 100D-pool med maximal explodering hamnar långt under).
DIFFICULTY_LEVELS: tuple[tuple[str, int, int], ...] = (
    ("Very Easy", 1, 5),
    ("Easy", 6, 10),
    ("Moderate", 11, 15),
    ("Difficult", 16, 20),
    ("Very Difficult", 21, 30),
    ("Heroic", 31, 10_000),
)


@dataclass
class DiceCode:
    """En tärningskod, t.ex. '4D+2' = fyra sexsidiga tärningar plus 2."""

    dice: int
    pips: int = 0

    def __post_init__(self) -> None:
        if self.dice < 1:
            raise ValueError("Tärningskoden måste ha minst 1D")
        if self.dice > MAX_DICE:
            raise ValueError(f"Tärningskoden får ha högst {MAX_DICE}D")
        if self.pips < 0:
            raise ValueError("Pips kan inte vara negativa")
        if self.pips > MAX_PIPS:
            raise ValueError(f"Pips får vara högst {MAX_PIPS}")

    def __str__(self) -> str:
        return f"{self.dice}D+{self.pips}" if self.pips else f"{self.dice}D"

    @property
    def pips_warning(self) -> bool:
        """Ovanligt (men inte ogiltigt) med mer än +2 pips i en tärningskod."""
        return self.pips > 2

    def with_dice_delta(self, delta: int) -> "DiceCode":
        """Ny kod med `delta` färre/fler tärningar (multipla handlingar)."""
        return DiceCode(dice=self.dice + delta, pips=self.pips)

    def doubled(self) -> "DiceCode":
        """Force Point: dubblar hela tärningspoolen (tärningar OCH pips)."""
        return DiceCode(dice=self.dice * 2, pips=self.pips * 2)


@dataclass
class WildDieResult:
    """
    En exploderande tärningskedja: `rolls[0]` är det första slaget, följt
    av eventuella omslag när en 6:a kom upp. Används både för den vanliga
    Wild Die och för Character Point-tärningar — mekaniken (explosion på 6)
    är identisk för båda. `is_one` är bara meningsfull för den riktiga Wild
    Die; CP-tärningar saknar 1:e-specialregeln helt.
    """

    rolls: list[int]

    @property
    def total(self) -> int:
        return sum(self.rolls)

    @property
    def exploded(self) -> bool:
        return self.rolls[0] == 6

    @property
    def is_one(self) -> bool:
        """
        Endast det FÖRSTA slaget räknas (källa s. 72-73: "for the first
        roll only"). En etta som dyker upp efter en explosion, t.ex. i
        kedjan 6 -> 1, är bara en vanlig etta och utlöser inget SL-val.
        """
        return self.rolls[0] == 1

    @property
    def chain_label(self) -> str:
        """Läsbar sträng för embeds, t.ex. '⭐6→6→3' eller '⭐2'."""
        return "⭐" + "→".join(str(r) for r in self.rolls)


@dataclass
class SWRollResult:
    """
    Rådata för ett D6-slag — inga färdigsummerade totaler sparas, allt
    beräknas som properties. Det gör att Character Point-knappen kan lägga
    till en ny post i `cp_dice` och räkna om resultatet utan att slå om
    övriga tärningar.
    """

    code: DiceCode
    regular_rolls: list[int]
    wild: WildDieResult
    modifier: int = 0
    actions: int = 1
    force_point: bool = False
    cp_dice: list[WildDieResult] = field(default_factory=list)

    @property
    def pips(self) -> int:
        return self.code.pips

    @property
    def action_penalty(self) -> int:
        """Antal tärningar avdragna på grund av multipla handlingar."""
        return self.actions - 1

    @property
    def total(self) -> int:
        """Alt A vid Wild Die-etta: räkna in allt normalt (standardutfallet)."""
        return (
            sum(self.regular_rolls)
            + self.wild.total
            + sum(cp.total for cp in self.cp_dice)
            + self.pips
            + self.modifier
        )

    @property
    def total_if_removed(self) -> int:
        """
        Alt B vid Wild Die-etta: dra bort ettan och den högsta andra
        tärningen i poolen (en vanlig tärning eller en hel CP-kedja,
        räknad som en enhet — precis som Wild Die själv räknas som en
        enhet trots att den kan ha exploderat till flera slag).
        """
        others = self.regular_rolls + [cp.total for cp in self.cp_dice]
        highest = max(others) if others else 0
        return self.total - 1 - highest


@dataclass
class OpposedResult:
    """Resultatet av ett motstått slag (opposed roll)."""

    initiator: SWRollResult
    defender: SWRollResult
    winner: str  # "initiator" eller "defender"
    tie: bool


def _roll_exploding_die(rng: Random) -> WildDieResult:
    """
    Slå en tärning som exploderar på 6 (Wild Die-mekaniken, s. 20 och s. 81
    för CP-tärningar): 6:an räknas in OCH tärningen slås om, hur många
    gånger som helst så länge det kommer 6:or.
    """
    rolls = [rng.randint(1, 6)]
    while rolls[-1] == 6 and len(rolls) < MAX_EXPLOSIONS:
        rolls.append(rng.randint(1, 6))
    return WildDieResult(rolls=rolls)


def parse_dice_code(text: str) -> DiceCode:
    """
    Tolka en tärningskod, t.ex. '4D+2', '4d', '4D' eller bara '4'. D är
    valfritt: ett ensamt tal tolkas som antal tärningar utan pips.
    """
    if text is None or not text.strip():
        raise ValueError("Tärningskoden är tom")

    stripped = text.strip()
    match = _DICE_CODE_RE.match(stripped)
    if not match:
        raise ValueError(
            f"Kunde inte tolka tärningskoden '{text}'. Använd formatet "
            f"4D+2, 4D eller 4."
        )

    dice_str, pips_part = match.groups()
    dice = int(dice_str)
    pips = int(pips_part.replace("+", "").strip()) if pips_part else 0

    return DiceCode(dice=dice, pips=pips)


def apply_multiple_actions(code: DiceCode, actions: int) -> DiceCode:
    """
    Multipla handlingar: 1 handling = full tärningskod. 2 handlingar = -1D
    på alla slag den rundan, 3 = -2D, osv.
    """
    if actions < 1:
        raise ValueError("Antal handlingar måste vara minst 1")

    penalty_dice = actions - 1
    if penalty_dice >= code.dice:
        raise ValueError(
            f"För många handlingar ({actions}) för tärningskoden {code} — "
            f"poolen skulle hamna under 1D."
        )

    return code.with_dice_delta(-penalty_dice)


def roll(
    code: DiceCode,
    *,
    modifier: int = 0,
    actions: int = 1,
    force_point: bool = False,
    rng: Random | None = None,
) -> SWRollResult:
    """
    Slå en tärningskod. En av tärningarna är alltid Wild Die.

    `code` förväntas redan vara den slutgiltiga, justerade koden (efter ev.
    `apply_multiple_actions` och `DiceCode.doubled()` för Force Point) —
    `actions` och `force_point` sparas här enbart för presentation i
    embeden, de tillämpas inte på nytt.
    """
    rng = rng or Random()

    regular_rolls = [rng.randint(1, 6) for _ in range(code.dice - 1)]
    wild = _roll_exploding_die(rng)

    return SWRollResult(
        code=code,
        regular_rolls=regular_rolls,
        wild=wild,
        modifier=modifier,
        actions=actions,
        force_point=force_point,
    )


def add_character_point_die(
    result: SWRollResult,
    rng: Random | None = None,
) -> SWRollResult:
    """
    Spendera en Character Point: lägg till en ny tärning som exploderar på
    6 precis som Wild Die (s. 81), men utan 1:e-specialregeln — en etta på
    en CP-tärning läggs bara till normalt. Kan anropas flera gånger; varje
    CP ger en ny, oberoende exploderande kedja.
    """
    rng = rng or Random()
    new_cp_die = _roll_exploding_die(rng)
    return replace(result, cp_dice=result.cp_dice + [new_cp_die])


def difficulty_band(total: int) -> str:
    """Vilken svårighetsnivå (Very Easy ... Heroic) en total motsvarar."""
    for name, low, high in DIFFICULTY_LEVELS:
        if low <= total <= high:
            return name
    return DIFFICULTY_LEVELS[-1][0]


def opposed(
    initiator_code: DiceCode,
    defender_code: DiceCode,
    *,
    initiator_modifier: int = 0,
    defender_modifier: int = 0,
    rng: Random | None = None,
) -> OpposedResult:
    """
    Motstått slag: båda sidor slår sin tärningskod, högst total vinner.
    Vid oavgjort vinner den som initierade handlingen.
    """
    rng = rng or Random()

    initiator_result = roll(initiator_code, modifier=initiator_modifier, rng=rng)
    defender_result = roll(defender_code, modifier=defender_modifier, rng=rng)

    tie = initiator_result.total == defender_result.total
    winner = "initiator" if initiator_result.total >= defender_result.total else "defender"

    return OpposedResult(
        initiator=initiator_result,
        defender=defender_result,
        winner=winner,
        tie=tie,
    )
