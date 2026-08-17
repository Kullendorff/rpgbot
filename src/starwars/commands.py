"""
Star Wars D6 (WEG40120, 2nd Ed. Revised & Expanded) slash-kommandon för
Discord-boten.

Speglar dragonbane/commands.py: Cog med @app_commands.command, embeds via
embed_factory, registrering via register_slash_starwars_commands(). All
regellogik (Wild Die-explosion, 1:e-specialregel, Force/Character Points,
svårighetsband) ligger i dice.py — den här filen är bara Discord-lagret.
"""

from __future__ import annotations

import logging
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands

from .dice import (
    DiceCode,
    SWRollResult,
    parse_dice_code,
    apply_multiple_actions,
    roll,
    add_character_point_die,
    difficulty_band,
    opposed,
)

logger = logging.getLogger(__name__)


def _difficulty_success(total: int, difficulty: Optional[int]) -> Optional[bool]:
    """None om inget svårighetstal angetts — då renderas slaget utan pass/fail."""
    if difficulty is None:
        return None
    return total >= difficulty


def _roll_breakdown(result: SWRollResult) -> str:
    """
    Läsbar '+'-sammanfattning av exakt vilka tärningar (och ev. pips/mod)
    som slogs, t.ex. '3+3+⭐6+4+2'. Wild Die och Character Points markeras
    med ⭐/🔹 på sin första tärning; resten av en exploderande kedja listas
    utan markör. Summan av de visade termerna är alltid lika med totalen.
    """
    terms: list[str] = [str(r) for r in result.regular_rolls]

    wild_rolls = result.wild.rolls
    terms.append(f"⭐{wild_rolls[0]}")
    terms.extend(str(r) for r in wild_rolls[1:])

    for cp in result.cp_dice:
        cp_rolls = cp.rolls
        terms.append(f"🔹{cp_rolls[0]}")
        terms.extend(str(r) for r in cp_rolls[1:])

    if result.pips:
        terms.append(str(result.pips))
    if result.modifier:
        terms.append(str(result.modifier) if result.modifier < 0 else f"+{result.modifier}")

    parts = [terms[0]]
    for term in terms[1:]:
        parts.append(term if term[0] in "+-" else f"+{term}")
    return "".join(parts)


def _render_roll_embed(
    embed_factory,
    user_id: int,
    user_name: str,
    result: SWRollResult,
    base_code_label: Optional[str] = None,
    difficulty: Optional[int] = None,
    description: Optional[str] = None,
) -> discord.Embed:
    """Bygg embeden för ett SWRollResult. Delad av /sw_slag och Character Point-knappen."""
    total_if_removed = result.total_if_removed if result.wild.is_one else None

    return embed_factory.starwars_roll_result(
        user_id=user_id,
        user_name=user_name,
        code_label=str(result.code),
        regular_rolls=result.regular_rolls,
        wild_rolls=result.wild.rolls,
        cp_rolls=[cp.rolls for cp in result.cp_dice],
        pips=result.pips,
        modifier=result.modifier,
        total=result.total,
        actions=result.actions,
        force_point=result.force_point,
        base_code_label=base_code_label,
        difficulty=difficulty,
        success=_difficulty_success(result.total, difficulty),
        difficulty_band=difficulty_band(result.total),
        total_if_removed=total_if_removed,
        description=description,
    )


class CharacterPointView(discord.ui.View):
    """
    Knapp för att spendera en Character Point efter slaget (regelrätt:
    "may be spent during the game", innan SL säger utfall). Varje tryck
    lägger till en ny tärning som exploderar på 6 precis som Wild Die
    (s. 81), men saknar 1:e-specialregeln. Kan tryckas flera gånger.
    """

    def __init__(
        self,
        embed_factory,
        result: SWRollResult,
        owner_id: int,
        user_name: str,
        base_code_label: Optional[str] = None,
        difficulty: Optional[int] = None,
        description: Optional[str] = None,
    ) -> None:
        super().__init__(timeout=120)
        self.embed_factory = embed_factory
        self.result = result
        self.owner_id = owner_id
        self.user_name = user_name
        self.base_code_label = base_code_label
        self.difficulty = difficulty
        self.description = description
        self.message: Optional[discord.Message] = None

    async def on_timeout(self) -> None:
        for item in self.children:
            if hasattr(item, "disabled"):
                item.disabled = True  # type: ignore[union-attr]
        if self.message:
            try:
                await self.message.edit(view=self)
            except discord.NotFound:
                pass

    @discord.ui.button(label="+1D Character Point", style=discord.ButtonStyle.success)
    async def cp_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        if interaction.user.id != self.owner_id:
            error = self.embed_factory.error_message(
                interaction.user.id,
                "Inte ditt slag",
                "Bara den som slog kan spendera en Character Point på det här resultatet.",
            )
            await interaction.response.send_message(embed=error, ephemeral=True)
            return

        self.result = add_character_point_die(self.result)
        embed = _render_roll_embed(
            self.embed_factory,
            self.owner_id,
            self.user_name,
            self.result,
            base_code_label=self.base_code_label,
            difficulty=self.difficulty,
            description=self.description,
        )
        await interaction.response.edit_message(embed=embed, view=self)


class StarWarsCommands(commands.Cog):
    """Cog för Star Wars D6: färdighets-/attributslag, motstådda slag, referenser."""

    def __init__(self, bot, embed_factory) -> None:
        self.bot = bot
        self.embed_factory = embed_factory
        logger.info("Star Wars D6 commands initialized")

    @app_commands.command(
        name="sw_slag",
        description="Färdighets-/attributslag i Star Wars D6, t.ex. 4D+2",
    )
    @app_commands.describe(
        kod="Tärningskod, t.ex. 4D+2, 4D eller 4",
        svarighet="Svårighetstal att slå mot (valfritt)",
        mod="Situationsmodifikation, utan +-tecken (t.ex. -5 eller 10)",
        handlingar="Antal samtidiga handlingar denna runda (2+ ger -1D per extra handling)",
        force_point="Spendera en Force Point: dubblar hela poolen (kan inte kombineras med CP samma runda)",
        beskrivning="Valfri flavor text, t.ex. 'Blaster mot stormtrooper'",
    )
    async def sw_slag(
        self,
        interaction: discord.Interaction,
        kod: str,
        svarighet: Optional[int] = None,
        mod: app_commands.Range[int, -30, 30] = 0,
        handlingar: app_commands.Range[int, 1, 6] = 1,
        force_point: bool = False,
        beskrivning: Optional[str] = None,
    ) -> None:
        if svarighet is not None and svarighet < 1:
            error = self.embed_factory.error_message(
                interaction.user.id, "Ogiltigt svårighetstal", "Svårighetstal måste vara minst 1."
            )
            await interaction.response.send_message(embed=error, ephemeral=True)
            return

        try:
            base_code = parse_dice_code(kod)
            effective_code = apply_multiple_actions(base_code, handlingar)
            if force_point:
                effective_code = effective_code.doubled()
        except ValueError as err:
            error = self.embed_factory.error_message(
                interaction.user.id, "Ogiltig tärningskod", str(err)
            )
            await interaction.response.send_message(embed=error, ephemeral=True)
            return

        result = roll(effective_code, modifier=mod, actions=handlingar, force_point=force_point)

        base_label = str(base_code) if str(base_code) != str(effective_code) else None
        embed = _render_roll_embed(
            self.embed_factory,
            interaction.user.id,
            interaction.user.display_name,
            result,
            base_code_label=base_label,
            difficulty=svarighet,
            description=beskrivning,
        )

        # CP och FP kan inte kombineras samma runda — knappen erbjuds bara
        # när Force Point inte redan spenderats.
        if force_point:
            await interaction.response.send_message(embed=embed)
        else:
            view = CharacterPointView(
                self.embed_factory,
                result,
                interaction.user.id,
                interaction.user.display_name,
                base_code_label=base_label,
                difficulty=svarighet,
                description=beskrivning,
            )
            await interaction.response.send_message(embed=embed, view=view)
            view.message = await interaction.original_response()

    @app_commands.command(
        name="sw_motstand",
        description="Motstått slag: högst total vinner, oavgjort går till initiativtagaren",
    )
    @app_commands.describe(
        aktion="Initiativtagarens tärningskod, t.ex. 4D+2",
        forsvar="Försvararens tärningskod, t.ex. 3D+1",
        initiativtagare="Namn på initiativtagaren (valfritt, default ditt eget)",
        forsvarare="Namn på försvararen (valfritt)",
        mod_aktion="Modifikation för initiativtagaren, utan +-tecken (t.ex. -5 eller 10)",
        mod_forsvar="Modifikation för försvararen, utan +-tecken (t.ex. -5 eller 10)",
    )
    async def sw_motstand(
        self,
        interaction: discord.Interaction,
        aktion: str,
        forsvar: str,
        initiativtagare: Optional[str] = None,
        forsvarare: Optional[str] = None,
        mod_aktion: app_commands.Range[int, -30, 30] = 0,
        mod_forsvar: app_commands.Range[int, -30, 30] = 0,
    ) -> None:
        try:
            aktion_code = parse_dice_code(aktion)
            forsvar_code = parse_dice_code(forsvar)
        except ValueError as err:
            error = self.embed_factory.error_message(
                interaction.user.id, "Ogiltig tärningskod", str(err)
            )
            await interaction.response.send_message(embed=error, ephemeral=True)
            return

        result = opposed(
            aktion_code,
            forsvar_code,
            initiator_modifier=mod_aktion,
            defender_modifier=mod_forsvar,
        )

        embed = self.embed_factory.starwars_opposed_result(
            initiator_name=initiativtagare or interaction.user.display_name,
            defender_name=forsvarare or "Försvarare",
            initiator_code_label=str(aktion_code),
            defender_code_label=str(forsvar_code),
            initiator_total=result.initiator.total,
            defender_total=result.defender.total,
            winner=result.winner,
            tie=result.tie,
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(
        name="sw_svarighet",
        description="Referenstabell: svårighetsnivåer och modifikatorsteg",
    )
    async def sw_svarighet(self, interaction: discord.Interaction) -> None:
        embed = self.embed_factory.starwars_difficulty_table(
            interaction.user.id, interaction.user.display_name
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(
        name="sw_init",
        description="Slå initiativ (Perception) för flera karaktärer",
    )
    @app_commands.describe(
        karaktarer="Namn och tärningskod per karaktär, kommaseparerat, t.ex. 'Han 3D+2, Chewie 2D+1'",
    )
    async def sw_init(self, interaction: discord.Interaction, karaktarer: str) -> None:
        entries_raw = [c.strip() for c in karaktarer.split(",") if c.strip()]
        if not entries_raw:
            error = self.embed_factory.error_message(
                interaction.user.id, "Inga karaktärer", "Ange minst en karaktär."
            )
            await interaction.response.send_message(embed=error, ephemeral=True)
            return
        if len(entries_raw) > 20:
            error = self.embed_factory.error_message(
                interaction.user.id, "För många karaktärer", "Max 20 karaktärer."
            )
            await interaction.response.send_message(embed=error, ephemeral=True)
            return

        parsed: list[tuple[str, DiceCode]] = []
        for entry in entries_raw:
            parts = entry.rsplit(" ", 1)
            if len(parts) != 2:
                error = self.embed_factory.error_message(
                    interaction.user.id,
                    "Ogiltigt format",
                    f"'{entry}' saknar tärningskod. Använd t.ex. 'Han 3D+2'.",
                )
                await interaction.response.send_message(embed=error, ephemeral=True)
                return

            name, code_text = parts
            try:
                code = parse_dice_code(code_text)
            except ValueError as err:
                error = self.embed_factory.error_message(
                    interaction.user.id, f"Ogiltig tärningskod för {name}", str(err)
                )
                await interaction.response.send_message(embed=error, ephemeral=True)
                return
            parsed.append((name, code))

        rolled = [(name, roll(code)) for name, code in parsed]
        rolled.sort(key=lambda item: item[1].total, reverse=True)
        entries = [
            {"name": name, "total": result.total, "breakdown": _roll_breakdown(result)}
            for name, result in rolled
        ]

        embed = self.embed_factory.starwars_initiative_result(
            interaction.user.id, interaction.user.display_name, entries
        )
        await interaction.response.send_message(embed=embed)


async def register_slash_starwars_commands(bot, embed_factory):
    """Registrera Star Wars D6 slash-kommandon."""
    try:
        cog = StarWarsCommands(bot, embed_factory)
        await bot.add_cog(cog)
        logger.info("Star Wars D6 commands registered successfully")
    except Exception as e:
        logger.error(f"Failed to register Star Wars D6 commands: {e}", exc_info=True)
        raise
