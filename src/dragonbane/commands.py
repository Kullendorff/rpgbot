"""
Dragonbane slash-kommandon för Discord-boten.

Speglar deltagreen/commands.py: Cog med @app_commands.command, embeds via
embed_factory, registrering via register_slash_dragonbane_commands().

Ursprunglig logik och kommandouppsättning av Jonas
(github.com/jonsal/dragonbane). Anpassad till botens arkitektur och regelrättad.
"""

from __future__ import annotations

import logging
from random import Random
from typing import Literal, Optional

import discord
from discord import app_commands
from discord.ext import commands

from .dice import (
    CONDITION_BY_ATTR,
    CONDITIONS,
    dragonbane_skill_check,
    dragonbane_skill_advancement,
    roll_expression,
    roll_fear_table,
    roll_mummy_attack,
    roll_initiative,
)

logger = logging.getLogger(__name__)

ModeLiteral = Literal["normal", "fördel", "nackdel"]
AttrLiteral = Literal["STY", "FYS", "SMI", "INT", "PSY", "KAR"]


def _expression_breakdown(result) -> list[str]:
    """Bygg läsbara rader för ett tärningsuttryck (dod_slag)."""
    parts: list[str] = []
    for i, dt in enumerate(result.dice_terms):
        sign = "+" if dt.sign > 0 else "-"
        label = f"{dt.count}T{dt.sides}: {dt.rolls}"
        if i == 0 and dt.sign > 0:
            parts.append(label)
        else:
            parts.append(f"{sign} {label}")
    for ft in result.flat_terms:
        sign = "+" if ft.value >= 0 else "-"
        parts.append(f"{sign} {abs(ft.value)}")
    return parts


def _damage_breakdown(result) -> list[str]:
    """Bygg läsbara rader för ett skadeslag (dod_skada)."""
    lines = [f"{t.count}T{t.sides}: {t.rolls}" for t in result.dice_terms]
    for ft in result.flat_terms:
        lines.append(f"Modifikation: {ft.value:+d}")
    return lines


def _resolve_condition(attribute: Optional[str], rng: Random) -> tuple[str, Optional[str]]:
    """
    Bestäm tillstånd vid pressning. Om grundegenskap angetts blir det
    deterministiskt (regelrätt), annars slumpas det och SL får sista ordet.
    """
    if attribute:
        attr = attribute.upper()
        return CONDITION_BY_ATTR.get(attr, "Utmattad"), attr
    condition, attr = rng.choice(CONDITIONS)
    return condition, None


class PushView(discord.ui.View):
    """Knapp för att pressa ett misslyckat slag direkt under resultatet."""

    def __init__(
        self,
        embed_factory,
        skill: int,
        modifier: int,
        mode: str,
        antal: int = 1,
        attribute: Optional[str] = None,
    ) -> None:
        super().__init__(timeout=60)
        self.embed_factory = embed_factory
        self.skill = skill
        self.modifier = modifier
        self.mode = mode
        self.antal = antal
        self.attribute = attribute
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

    @discord.ui.button(label="Pressa slag", style=discord.ButtonStyle.danger)
    async def push_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        self.stop()
        button.disabled = True
        try:
            await interaction.message.edit(view=self)  # type: ignore[union-attr]
        except discord.NotFound:
            pass

        try:
            result = dragonbane_skill_check(
                skill=self.skill, modifier=self.modifier, mode=self.mode, antal=self.antal
            )
        except ValueError as err:
            error = self.embed_factory.error_message(
                interaction.user.id, "Pressat slag misslyckades", str(err)
            )
            await interaction.response.send_message(embed=error, ephemeral=True)
            return

        condition, attr = _resolve_condition(self.attribute, Random())
        embed = self.embed_factory.dragonbane_skill_result(
            user_id=interaction.user.id,
            user_name=interaction.user.display_name,
            skill=result.skill,
            modifier=result.modifier,
            target=result.target,
            mode=result.mode,
            antal=result.antal,
            rolls=result.rolls,
            chosen_roll=result.chosen_roll,
            success=result.success,
            critical=result.critical,
            pushed=True,
            condition=condition,
            attribute=attr,
        )
        await interaction.response.send_message(embed=embed)


class DragonbaneCommands(commands.Cog):
    """Cog för Dragonbane: tärningar, färdighetsslag, skada, initiativ."""

    def __init__(self, bot, embed_factory) -> None:
        self.bot = bot
        self.embed_factory = embed_factory
        logger.info("Dragonbane commands initialized")

    @app_commands.command(name="dod_slag", description="Slå ett tärningsuttryck, t.ex. 2T6+1T8+3")
    @app_commands.describe(expression="Tärningsuttryck som 1T20+5 eller 2T6+1")
    async def dod_slag(self, interaction: discord.Interaction, expression: str) -> None:
        try:
            result = roll_expression(expression)
        except ValueError as err:
            error = self.embed_factory.error_message(
                interaction.user.id, "Ogiltigt slag", str(err)
            )
            await interaction.response.send_message(embed=error, ephemeral=True)
            return

        embed = self.embed_factory.dragonbane_expression_result(
            user_id=interaction.user.id,
            user_name=interaction.user.display_name,
            expression=result.expression,
            breakdown_lines=_expression_breakdown(result),
            total=result.total,
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="dod_fv", description="Färdighetsslag på T20 (slag <= FV lyckas)")
    @app_commands.describe(
        skill="Färdighetsvärde (1-30)",
        modifier="Situationsmodifikation (-10 till +10)",
        mode="normal, fördel eller nackdel",
        antal="Stapling av fördel/nackdel utöver grundslaget, t.ex. 2 = trippel (house rule)",
    )
    async def dod_fv(
        self,
        interaction: discord.Interaction,
        skill: app_commands.Range[int, 1, 30],
        modifier: app_commands.Range[int, -10, 10] = 0,
        mode: ModeLiteral = "normal",
        antal: app_commands.Range[int, 1, 99] = 1,
    ) -> None:
        try:
            result = dragonbane_skill_check(skill=skill, modifier=modifier, mode=mode, antal=antal)
        except ValueError as err:
            error = self.embed_factory.error_message(
                interaction.user.id, "Ogiltigt färdighetsslag", str(err)
            )
            await interaction.response.send_message(embed=error, ephemeral=True)
            return

        embed = self.embed_factory.dragonbane_skill_result(
            user_id=interaction.user.id,
            user_name=interaction.user.display_name,
            skill=result.skill,
            modifier=result.modifier,
            target=result.target,
            mode=result.mode,
            antal=result.antal,
            rolls=result.rolls,
            chosen_roll=result.chosen_roll,
            success=result.success,
            critical=result.critical,
        )

        can_push = not result.success and result.critical != "demon"
        if can_push:
            view = PushView(
                self.embed_factory, skill=skill, modifier=modifier, mode=result.mode, antal=antal
            )
            await interaction.response.send_message(embed=embed, view=view)
            view.message = await interaction.original_response()
        else:
            await interaction.response.send_message(embed=embed)

    @app_commands.command(name="dod_skada", description="Slå skadeslag")
    @app_commands.describe(dice="Skadeslag, t.ex. 1T8 eller 2T6", bonus="Modifikation")
    async def dod_skada(
        self, interaction: discord.Interaction, dice: str, bonus: int = 0
    ) -> None:
        if bonus < -20 or bonus > 20:
            error = self.embed_factory.error_message(
                interaction.user.id,
                "Ogiltig modifikation",
                "Modifikationen måste vara mellan -20 och +20.",
            )
            await interaction.response.send_message(embed=error, ephemeral=True)
            return

        expression = f"{dice}{bonus:+d}" if bonus else dice
        try:
            result = roll_expression(expression)
        except ValueError as err:
            error = self.embed_factory.error_message(
                interaction.user.id, "Ogiltigt skadeslag", str(err)
            )
            await interaction.response.send_message(embed=error, ephemeral=True)
            return

        embed = self.embed_factory.dragonbane_damage_result(
            user_id=interaction.user.id,
            user_name=interaction.user.display_name,
            expression=expression,
            breakdown_lines=_damage_breakdown(result),
            total=result.total,
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(
        name="dod_pressa",
        description="Pressa ett misslyckat färdighetsslag: slå om men dra ett tillstånd",
    )
    @app_commands.describe(
        skill="Färdighetsvärde (1-30)",
        modifier="Situationsmodifikation (-10 till +10)",
        mode="normal, fördel eller nackdel",
        grundegenskap="Färdighetens grundegenskap (ger rätt tillstånd). Lämna tom för slump.",
        antal="Stapling av fördel/nackdel utöver grundslaget, t.ex. 2 = trippel (house rule)",
    )
    async def dod_pressa(
        self,
        interaction: discord.Interaction,
        skill: app_commands.Range[int, 1, 30],
        modifier: app_commands.Range[int, -10, 10] = 0,
        mode: ModeLiteral = "normal",
        grundegenskap: Optional[AttrLiteral] = None,
        antal: app_commands.Range[int, 1, 99] = 1,
    ) -> None:
        try:
            result = dragonbane_skill_check(skill=skill, modifier=modifier, mode=mode, antal=antal)
        except ValueError as err:
            error = self.embed_factory.error_message(
                interaction.user.id, "Ogiltigt färdighetsslag", str(err)
            )
            await interaction.response.send_message(embed=error, ephemeral=True)
            return

        condition, attr = _resolve_condition(grundegenskap, Random())
        embed = self.embed_factory.dragonbane_skill_result(
            user_id=interaction.user.id,
            user_name=interaction.user.display_name,
            skill=result.skill,
            modifier=result.modifier,
            target=result.target,
            mode=result.mode,
            antal=result.antal,
            rolls=result.rolls,
            chosen_roll=result.chosen_roll,
            success=result.success,
            critical=result.critical,
            pushed=True,
            condition=condition,
            attribute=attr,
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(
        name="dod_hoj",
        description="Färdighetsförbättring: slå 1T20, högre än FV ger +1",
    )
    @app_commands.describe(skill="Nuvarande färdighetsvärde (1-30)")
    async def dod_hoj(
        self,
        interaction: discord.Interaction,
        skill: app_commands.Range[int, 1, 30],
    ) -> None:
        try:
            result = dragonbane_skill_advancement(skill=skill)
        except ValueError as err:
            error = self.embed_factory.error_message(
                interaction.user.id, "Ogiltigt förbättringsslag", str(err)
            )
            await interaction.response.send_message(embed=error, ephemeral=True)
            return

        embed = self.embed_factory.dragonbane_advancement_result(
            user_id=interaction.user.id,
            user_name=interaction.user.display_name,
            skill=result.skill,
            roll=result.roll,
            success=result.success,
            new_skill=result.new_skill,
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(
        name="dod_skrack",
        description="Slå på skräcktabellen (1T8) efter misslyckat PSY-slag mot en skräckattack",
    )
    async def dod_skrack(self, interaction: discord.Interaction) -> None:
        result = roll_fear_table()

        embed = self.embed_factory.dragonbane_fear_result(
            user_id=interaction.user.id,
            user_name=interaction.user.display_name,
            roll=result.roll,
            condition=result.condition,
            description=result.description,
            vp_loss=result.vp_loss,
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(
        name="dod_mumie",
        description="Slå på mumiens anfallstabell (1T6)",
    )
    async def dod_mumie(self, interaction: discord.Interaction) -> None:
        result = roll_mummy_attack()

        embed = self.embed_factory.dragonbane_mummy_attack_result(
            user_id=interaction.user.id,
            user_name=interaction.user.display_name,
            roll=result.roll,
            name=result.name,
            description=result.description,
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="dod_init", description="Slå initiativ för alla karaktärer (kortlek 1-10)")
    @app_commands.describe(characters="Kommaseparerade namn, t.ex. Björn,Saga,Ragna")
    async def dod_init(self, interaction: discord.Interaction, characters: str) -> None:
        names = [n.strip() for n in characters.split(",") if n.strip()]
        if not names:
            error = self.embed_factory.error_message(
                interaction.user.id, "Inga karaktärer", "Ange minst ett karaktärsnamn."
            )
            await interaction.response.send_message(embed=error, ephemeral=True)
            return
        if len(names) > 20:
            error = self.embed_factory.error_message(
                interaction.user.id, "För många karaktärer", "Max 20 karaktärer."
            )
            await interaction.response.send_message(embed=error, ephemeral=True)
            return

        entries = roll_initiative(names)
        embed = self.embed_factory.dragonbane_initiative_result(
            user_id=interaction.user.id,
            user_name=interaction.user.display_name,
            entries=entries,
        )
        await interaction.response.send_message(embed=embed)


async def register_slash_dragonbane_commands(bot, embed_factory):
    """Registrera Dragonbane slash-kommandon (modul av Jonas)."""
    try:
        cog = DragonbaneCommands(bot, embed_factory)
        await bot.add_cog(cog)
        logger.info("Dragonbane commands registered successfully")
    except Exception as e:
        logger.error(f"Failed to register Dragonbane commands: {e}", exc_info=True)
        raise
