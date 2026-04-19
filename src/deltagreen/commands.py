"""
Delta Green slash commands for Discord bot.

Implements d100 percentile system for Delta Green RPG.
"""

import logging
from typing import Optional, Dict, List
import discord
from discord.ext import commands
from discord import app_commands

from .dice_functions import (
    skill_check,
    stat_test,
    luck_roll,
    lethality_roll,
    san_check,
    RollResult
)
from .agent_manager import AgentManager
from .session_manager import SessionManager

# Setup logging
logger = logging.getLogger(__name__)

# Delta Green weapon data
WEAPON_DATA = {
    # Handguns
    "Light pistol": {"damage": "1d8", "lethality": None},
    "Medium pistol": {"damage": "1d10", "lethality": None},
    "Heavy pistol": {"damage": "1d12", "lethality": None},

    # Shotguns
    "Shotgun (shot)": {"damage": "2d8", "lethality": None},
    "Shotgun (slug)": {"damage": "2d8", "lethality": None},
    "Shotgun (nonlethal)": {"damage": "1d6", "lethality": None, "special": "Stun"},

    # Rifles and SMGs
    "Light rifle": {"damage": "1d12", "lethality": 10},
    "SMG": {"damage": "1d10", "lethality": 10},
    "Heavy rifle": {"damage": "1d12+2", "lethality": 10},

    # Melee/Unarmed
    "Unarmed": {"damage": "1d4-1", "lethality": None},
    "Knife": {"damage": "1d4", "lethality": None},
}

# Delta Green armor data
STAT_INDEX_TO_NAME = {1: "STR", 2: "CON", 3: "DEX", 4: "INT", 5: "POW", 6: "CHA"}

BONUS_CHOICES = [
    app_commands.Choice(name="+40%", value=40),
    app_commands.Choice(name="+30%", value=30),
    app_commands.Choice(name="+20%", value=20),
    app_commands.Choice(name="+10%", value=10),
    app_commands.Choice(name="Normal", value=0),
    app_commands.Choice(name="-10%", value=-10),
    app_commands.Choice(name="-20%", value=-20),
    app_commands.Choice(name="-30%", value=-30),
    app_commands.Choice(name="-40%", value=-40),
]

ARMOR_DATA = {
    "None": 0,
    "Riot helmet": 1,
    "Kevlar helmet": 1,
    "Kevlar vest": 3,
    "Reinforced Kevlar vest": 4,
    "Tactical body armor": 5,
    "Bomb suit": 10,
}


class DeltaGreenCommands(commands.Cog):
    """Cog for Delta Green dice rolling and agent management."""

    def __init__(self, bot, embed_factory, agent_manager, session_manager):
        self.bot = bot
        self.embed_factory = embed_factory
        self.agent_manager = agent_manager
        self.session_manager = session_manager
        logger.info("Delta Green commands initialized")

    @app_commands.command(name="dgcheck", description="Delta Green snabbkast med manuellt målvärde (utan agent)")
    @app_commands.describe(
        target="Målvärde att rulla mot (1-99)",
        bonus="Bonus eller penalty (+20, -40, etc.)"
    )
    @app_commands.choices(bonus=BONUS_CHOICES)
    async def dg_check(
        self,
        interaction: discord.Interaction,
        target: app_commands.Range[int, 1, 99],
        bonus: Optional[int] = 0
    ):
        """Quick d100 roll against a manual target value (no agent lookup)."""
        try:
            result = skill_check(target, bonus or 0)

            embed = self.embed_factory.dg_roll_result(
                user_id=interaction.user.id,
                user_name=interaction.user.display_name,
                roll=result.roll,
                tens=result.tens_die,
                ones=result.ones_die,
                target=result.target,
                result_type=result.result.value,
                skill_name=f"Manuellt ({target}%)",
                modifier=bonus or 0
            )

            await interaction.response.send_message(embed=embed)
            logger.info(f"DG check: {interaction.user.display_name} rolled manual {target}% = {result.roll}")

        except Exception as e:
            logger.error(f"Error in dg_check: {e}", exc_info=True)
            error_embed = self.embed_factory.error_message(
                interaction.user.id,
                "Ett fel uppstod vid tärningskastet",
                str(e)
            )
            await interaction.response.send_message(embed=error_embed, ephemeral=True)

    @app_commands.command(name="dgstat", description="Delta Green stat-test (STATx5) – hämtar värde från din agent")
    @app_commands.describe(stat="Vilken stat att testa")
    @app_commands.choices(stat=[
        app_commands.Choice(name="STR (Strength)", value=1),
        app_commands.Choice(name="CON (Constitution)", value=2),
        app_commands.Choice(name="DEX (Dexterity)", value=3),
        app_commands.Choice(name="INT (Intelligence)", value=4),
        app_commands.Choice(name="POW (Power)", value=5),
        app_commands.Choice(name="CHA (Charisma)", value=6),
    ])
    async def dg_stat(
        self,
        interaction: discord.Interaction,
        stat: int
    ):
        """Perform a Delta Green stat test (STATx5) using agent data."""
        try:
            agent = self.agent_manager.get_agent(str(interaction.user.id))
            if not agent:
                await interaction.response.send_message(
                    "Du har ingen agent registrerad. Kontakta GM.",
                    ephemeral=True
                )
                return

            stat_name = STAT_INDEX_TO_NAME[stat]
            stat_value = agent['stats'][stat_name]
            result = stat_test(stat_value)

            display_name = f"{agent['callsign']} ({interaction.user.display_name})"
            embed = self.embed_factory.dg_roll_result(
                user_id=interaction.user.id,
                user_name=display_name,
                roll=result.roll,
                tens=result.tens_die,
                ones=result.ones_die,
                target=result.target,
                result_type=result.result.value,
                skill_name=f"{stat_name} x5 ({stat_value}→{result.target}%)",
                modifier=0
            )

            await interaction.response.send_message(embed=embed)
            logger.info(f"DG stat test: {display_name} rolled {stat_name}x5 ({result.target}%) = {result.roll}")

        except Exception as e:
            logger.error(f"Error in dg_stat: {e}", exc_info=True)
            error_embed = self.embed_factory.error_message(
                interaction.user.id,
                "Ett fel uppstod",
                str(e)
            )
            await interaction.response.send_message(embed=error_embed, ephemeral=True)

    @app_commands.command(name="dgluck", description="Delta Green luck roll (50%)")
    async def dg_luck(
        self,
        interaction: discord.Interaction
    ):
        """Perform a 50% luck roll."""
        try:
            # Perform the luck roll
            result = luck_roll()

            # Create embed
            embed = self.embed_factory.dg_roll_result(
                user_id=interaction.user.id,
                user_name=interaction.user.display_name,
                roll=result.roll,
                tens=result.tens_die,
                ones=result.ones_die,
                target=result.target,
                result_type=result.result.value,
                skill_name="Luck"
            )

            await interaction.response.send_message(embed=embed)
            logger.info(f"DG luck roll: {interaction.user.display_name} rolled {result.roll}")

        except Exception as e:
            logger.error(f"Error in dg_luck: {e}", exc_info=True)
            error_embed = self.embed_factory.error_message(
                interaction.user.id,
                "Ett fel uppstod vid tärningskastet",
                str(e)
            )
            await interaction.response.send_message(embed=error_embed, ephemeral=True)

    @app_commands.command(name="dglethality", description="Delta Green lethality roll")
    @app_commands.describe(
        rating="Lethality percentage (e.g., 10, 15, 20)"
    )
    async def dg_lethality(
        self,
        interaction: discord.Interaction,
        rating: app_commands.Range[int, 1, 99]
    ):
        """Perform a lethality roll."""
        try:
            # Perform the lethality roll
            result = lethality_roll(rating)

            # Create embed
            embed = self.embed_factory.dg_lethality_result(
                user_id=interaction.user.id,
                user_name=interaction.user.display_name,
                roll=result.roll,
                tens=result.tens_die,
                ones=result.ones_die,
                rating=result.rating,
                is_lethal=result.is_lethal,
                damage=result.damage
            )

            await interaction.response.send_message(embed=embed)
            logger.info(f"DG lethality: {interaction.user.display_name} rolled {result.roll} vs {rating}% (lethal={result.is_lethal})")

        except Exception as e:
            logger.error(f"Error in dg_lethality: {e}", exc_info=True)
            error_embed = self.embed_factory.error_message(
                interaction.user.id,
                "Ett fel uppstod vid tärningskastet",
                str(e)
            )
            await interaction.response.send_message(embed=error_embed, ephemeral=True)

    @app_commands.command(name="dgsan", description="Delta Green SAN-check – hämtar SAN automatiskt från din agent")
    @app_commands.describe(
        success_loss="SAN-förlust vid lyckad roll (t.ex. '0', '1', '1d4')",
        failure_loss="SAN-förlust vid misslyckad roll (t.ex. '1', '1d6', '1d10')",
        current_san="Åsidosätt agentens SAN-värde (valfritt)"
    )
    async def dg_san(
        self,
        interaction: discord.Interaction,
        success_loss: str,
        failure_loss: str,
        current_san: Optional[app_commands.Range[int, 0, 99]] = None
    ):
        """Perform a SAN check, auto-reading SAN from agent data and updating it after."""
        try:
            agent = self.agent_manager.get_agent(str(interaction.user.id))

            if current_san is None:
                if not agent:
                    await interaction.response.send_message(
                        "Du har ingen agent registrerad och inget manuellt SAN-värde angavs. Kontakta GM.",
                        ephemeral=True
                    )
                    return
                current_san = agent['derived']['san']['current']

            # Perform the SAN check
            result = san_check(current_san, success_loss, failure_loss)

            display_name = (
                f"{agent['callsign']} ({interaction.user.display_name})"
                if agent else interaction.user.display_name
            )

            # Create embed
            embed = self.embed_factory.dg_san_result(
                user_id=interaction.user.id,
                user_name=display_name,
                roll=result.roll_result.roll,
                tens=result.roll_result.tens_die,
                ones=result.roll_result.ones_die,
                san_before=result.san_before,
                san_loss=result.san_loss,
                san_after=result.san_after,
                result_type=result.roll_result.result.value,
                temporary_insanity=result.triggered_temporary_insanity
            )

            # Persist SAN loss to agent data and check for breaking point
            if agent and result.san_loss > 0:
                san_result = self.agent_manager.modify_san(
                    str(interaction.user.id),
                    -result.san_loss
                )
                if san_result:
                    _, _, hit_breaking_point = san_result
                    if hit_breaking_point:
                        bp = agent['derived']['breaking_point']
                        embed.add_field(
                            name="⚠️ BREAKING POINT",
                            value=f"SAN sjönk under Breaking Point ({bp})!\nAgenten drabbas av en permanent störning.",
                            inline=False
                        )

            await interaction.response.send_message(embed=embed)
            logger.info(
                f"DG SAN check: {display_name} rolled {result.roll_result.roll}, "
                f"lost {result.san_loss} SAN ({current_san} → {result.san_after})"
            )

        except Exception as e:
            logger.error(f"Error in dg_san: {e}", exc_info=True)
            error_embed = self.embed_factory.error_message(
                interaction.user.id,
                "Ett fel uppstod vid SAN-checken",
                str(e)
            )
            await interaction.response.send_message(embed=error_embed, ephemeral=True)

    # Agent Management Commands

    async def skill_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str
    ) -> List[app_commands.Choice[str]]:
        """Autocomplete for agent skills."""
        agent = self.agent_manager.get_agent(str(interaction.user.id))
        if not agent:
            return []

        skills = list(agent.get('skills', {}).keys())

        # Filter based on current input
        if current:
            matching = [s for s in skills if s.lower().startswith(current.lower())]
        else:
            matching = skills[:25]

        return [app_commands.Choice(name=skill, value=skill) for skill in sorted(matching)[:25]]

    @app_commands.command(name="dgagent", description="View your Delta Green agent")
    async def dg_agent_view(
        self,
        interaction: discord.Interaction
    ):
        """View your agent's stats and skills."""
        try:
            agent = self.agent_manager.get_agent(str(interaction.user.id))

            if not agent:
                error_embed = self.embed_factory.error_message(
                    interaction.user.id,
                    "Du har ingen agent",
                    "Kontakta GM för att få din agent skapad."
                )
                await interaction.response.send_message(embed=error_embed, ephemeral=True)
                return

            # Create agent display embed
            embed = self._create_agent_embed(interaction.user.id, agent)
            await interaction.response.send_message(embed=embed)
            logger.info(f"Agent view: {interaction.user.display_name} ({agent['callsign']})")

        except Exception as e:
            logger.error(f"Error in dg_agent_view: {e}", exc_info=True)
            error_embed = self.embed_factory.error_message(
                interaction.user.id,
                "Ett fel uppstod",
                str(e)
            )
            await interaction.response.send_message(embed=error_embed, ephemeral=True)

    @app_commands.command(name="dgallt", description="Visa agentens fulla dossier – alla stats och alla skills > 0")
    async def dg_agent_full(
        self,
        interaction: discord.Interaction
    ):
        """View full agent dossier: all stats, derived attributes, and every skill > 0."""
        try:
            agent = self.agent_manager.get_agent(str(interaction.user.id))

            if not agent:
                error_embed = self.embed_factory.error_message(
                    interaction.user.id,
                    "Du har ingen agent",
                    "Kontakta GM för att få din agent skapad."
                )
                await interaction.response.send_message(embed=error_embed, ephemeral=True)
                return

            embed = self._create_full_agent_embed(interaction.user.id, agent)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            logger.info(f"Full agent view: {interaction.user.display_name} ({agent['callsign']})")

        except Exception as e:
            logger.error(f"Error in dg_agent_full: {e}", exc_info=True)
            error_embed = self.embed_factory.error_message(
                interaction.user.id,
                "Ett fel uppstod",
                str(e)
            )
            await interaction.response.send_message(embed=error_embed, ephemeral=True)

    @app_commands.command(name="dgroll", description="Roll one of your agent's skills")
    @app_commands.describe(
        skill="Skill name (autocomplete available)",
        bonus="Bonus or penalty (+10, -20, +40, etc.)"
    )
    @app_commands.autocomplete(skill=skill_autocomplete)
    @app_commands.choices(bonus=BONUS_CHOICES)
    async def dg_agent_roll(
        self,
        interaction: discord.Interaction,
        skill: str,
        bonus: Optional[int] = 0
    ):
        """Roll one of your agent's skills."""
        try:
            agent = self.agent_manager.get_agent(str(interaction.user.id))

            if not agent:
                error_embed = self.embed_factory.error_message(
                    interaction.user.id,
                    "Du har ingen agent",
                    "Kontakta GM för att få din agent skapad."
                )
                await interaction.response.send_message(embed=error_embed, ephemeral=True)
                return

            # Get skill value with fuzzy matching
            skill_value = self.agent_manager.get_skill_value(str(interaction.user.id), skill)

            if skill_value is None:
                error_embed = self.embed_factory.error_message(
                    interaction.user.id,
                    f"Skill '{skill}' hittades inte",
                    f"Använd `/dgagent` för att se alla dina skills."
                )
                await interaction.response.send_message(embed=error_embed, ephemeral=True)
                return

            # Perform the skill check
            result = skill_check(skill_value, bonus or 0)

            # Track failed check if session active
            if self.session_manager.is_session_active(str(interaction.channel_id)):
                if result.result in (RollResult.FAILURE, RollResult.FUMBLE):
                    self.session_manager.record_failed_check(
                        str(interaction.channel_id),
                        str(interaction.user.id),
                        skill
                    )

            # Create embed with agent info
            embed = self.embed_factory.dg_roll_result(
                user_id=interaction.user.id,
                user_name=f"{agent['callsign']} ({interaction.user.display_name})",
                roll=result.roll,
                tens=result.tens_die,
                ones=result.ones_die,
                target=result.target,
                result_type=result.result.value,
                skill_name=skill,
                modifier=bonus or 0
            )

            await interaction.response.send_message(embed=embed)
            logger.info(f"Agent roll: {agent['callsign']} rolled {skill} ({skill_value}%{bonus:+d if bonus else ''}) = {result.roll}")

        except Exception as e:
            logger.error(f"Error in dg_agent_roll: {e}", exc_info=True)
            error_embed = self.embed_factory.error_message(
                interaction.user.id,
                "Ett fel uppstod",
                str(e)
            )
            await interaction.response.send_message(embed=error_embed, ephemeral=True)

    def _create_agent_embed(self, user_id: int, agent: Dict) -> discord.Embed:
        """Create a formatted agent display embed."""
        # Base info
        title = f"🕵️ DELTA GREEN - Agent Dossier"
        desc_lines = [
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            f"",
            f"**{agent['callsign'].upper()}** - {agent['name']}",
            f"_{agent['occupation']}_",
            f""
        ]

        # Stats
        stats = agent['stats']
        desc_lines.append(f"**STR** {stats['STR']}  **CON** {stats['CON']}  **DEX** {stats['DEX']}")
        desc_lines.append(f"**INT** {stats['INT']}  **POW** {stats['POW']}  **CHA** {stats['CHA']}")
        desc_lines.append("")

        # Derived attributes with bars
        hp_current = agent['derived']['hp']['current']
        hp_max = agent['derived']['hp']['max']
        hp_bar = self._create_bar(hp_current, hp_max, 10)
        desc_lines.append(f"**HP:**  {hp_bar}  {hp_current}/{hp_max}")

        wp_current = agent['derived']['wp']['current']
        wp_max = agent['derived']['wp']['max']
        wp_bar = self._create_bar(wp_current, wp_max, 10)
        desc_lines.append(f"**WP:**  {wp_bar}  {wp_current}/{wp_max}")

        san_current = agent['derived']['san']['current']
        san_max = agent['derived']['san']['max']
        bp = agent['derived']['breaking_point']
        san_bar = self._create_bar(san_current, san_max, 10)
        desc_lines.append(f"**SAN:** {san_bar}  {san_current}/{san_max} (BP: {bp})")
        desc_lines.append("")

        # Top skills
        skills = agent.get('skills', {})
        top_skills = sorted(skills.items(), key=lambda x: x[1], reverse=True)[:5]
        desc_lines.append("**Top Skills:**")
        for skill_name, skill_value in top_skills:
            desc_lines.append(f"• {skill_name}: {skill_value}%")

        embed = discord.Embed(
            title=title,
            description="\n".join(desc_lines),
            color=0x2C3E50  # Dark blue-grey for Delta Green
        )

        return embed

    def _create_full_agent_embed(self, user_id: int, agent: Dict) -> discord.Embed:
        """Create a complete agent display embed with ALL stats and every skill > 0."""
        title = f"🕵️ DELTA GREEN - Full Dossier"

        desc_lines = [
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "",
            f"**{agent['callsign'].upper()}** – {agent['name']}",
            f"_{agent['occupation']}_",
            "",
        ]

        # Stats
        stats = agent['stats']
        desc_lines.append("**STATS**")
        desc_lines.append(
            f"STR {stats['STR']}  •  CON {stats['CON']}  •  DEX {stats['DEX']}"
        )
        desc_lines.append(
            f"INT {stats['INT']}  •  POW {stats['POW']}  •  CHA {stats['CHA']}"
        )
        desc_lines.append("")

        # Derived
        hp = agent['derived']['hp']
        wp = agent['derived']['wp']
        san = agent['derived']['san']
        bp = agent['derived']['breaking_point']
        desc_lines.append("**DERIVED**")
        desc_lines.append(f"HP {hp['current']}/{hp['max']}  •  WP {wp['current']}/{wp['max']}  •  SAN {san['current']}/{san['max']} (BP {bp})")

        embed = discord.Embed(
            title=title,
            description="\n".join(desc_lines),
            color=0x2C3E50
        )

        # Skills > 0, sorted high-to-low
        skills = agent.get('skills', {})
        active_skills = [(name, val) for name, val in skills.items() if val > 0]
        active_skills.sort(key=lambda x: (-x[1], x[0]))

        if not active_skills:
            embed.add_field(
                name="SKILLS",
                value="_Inga skills med värde > 0._",
                inline=False
            )
        else:
            # Split into 3 columns for readability
            lines = [f"`{val:>3}%` {name}" for name, val in active_skills]
            num_cols = 3
            per_col = (len(lines) + num_cols - 1) // num_cols
            cols = [lines[i * per_col:(i + 1) * per_col] for i in range(num_cols)]

            # Discord field value limit is 1024 chars – fall back to single column if overflow
            col_values = ["\n".join(c) if c else "\u200b" for c in cols]
            if any(len(v) > 1024 for v in col_values):
                # Overflow – chunk into multiple safe fields
                chunks = []
                current_chunk = []
                current_len = 0
                for line in lines:
                    if current_len + len(line) + 1 > 1000:
                        chunks.append("\n".join(current_chunk))
                        current_chunk = [line]
                        current_len = len(line)
                    else:
                        current_chunk.append(line)
                        current_len += len(line) + 1
                if current_chunk:
                    chunks.append("\n".join(current_chunk))

                for i, chunk in enumerate(chunks):
                    name = f"SKILLS ({len(active_skills)})" if i == 0 else "\u200b"
                    embed.add_field(name=name, value=chunk, inline=False)
            else:
                embed.add_field(name=f"SKILLS ({len(active_skills)})", value=col_values[0], inline=True)
                embed.add_field(name="\u200b", value=col_values[1], inline=True)
                embed.add_field(name="\u200b", value=col_values[2], inline=True)

        return embed

    def _create_bar(self, current: int, maximum: int, length: int = 10) -> str:
        """Create a visual bar."""
        if maximum == 0:
            ratio = 0
        else:
            ratio = current / maximum

        filled = int(ratio * length)
        empty = length - filled

        return "█" * filled + "░" * empty

    def _find_agent_by_callsign(self, callsign: str) -> Optional[str]:
        """Find user_id by agent callsign (case-insensitive). Returns None if not found."""
        for user_id, cs in self.agent_manager.list_all_agents():
            if cs.lower() == callsign.lower():
                return user_id
        return None

    # GM Commands

    async def agent_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str
    ) -> List[app_commands.Choice[str]]:
        """Autocomplete for all agents (GM only)."""
        all_agents = self.agent_manager.list_all_agents()

        if current:
            matching = [(uid, cs) for uid, cs in all_agents if cs.lower().startswith(current.lower())]
        else:
            matching = all_agents[:25]

        return [app_commands.Choice(name=callsign, value=callsign) for user_id, callsign in matching[:25]]

    @app_commands.command(name="dggmallt", description="[GM] Visa full dossier för valfri agent – alla stats och skills > 0")
    @app_commands.describe(agent="Agent callsign (autocomplete)")
    @app_commands.autocomplete(agent=agent_autocomplete)
    @app_commands.checks.has_permissions(manage_guild=True)
    async def dg_gm_full(
        self,
        interaction: discord.Interaction,
        agent: str
    ):
        """GM view: full dossier for any agent."""
        try:
            target_user_id = self._find_agent_by_callsign(agent)

            if not target_user_id:
                error_embed = self.embed_factory.error_message(
                    interaction.user.id,
                    f"Agent '{agent}' hittades inte",
                    "Använd `/dggmstatus` för att se alla agents."
                )
                await interaction.response.send_message(embed=error_embed, ephemeral=True)
                return

            agent_data = self.agent_manager.get_agent(target_user_id)
            if not agent_data:
                error_embed = self.embed_factory.error_message(
                    interaction.user.id,
                    f"Kunde inte ladda agent '{agent}'",
                    "Kontrollera att agent-filen existerar."
                )
                await interaction.response.send_message(embed=error_embed, ephemeral=True)
                return

            embed = self._create_full_agent_embed(interaction.user.id, agent_data)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            logger.info(f"GM full view: {interaction.user.display_name} viewed {agent_data['callsign']}")

        except Exception as e:
            logger.error(f"Error in dg_gm_full: {e}", exc_info=True)
            error_embed = self.embed_factory.error_message(
                interaction.user.id,
                "Ett fel uppstod",
                str(e)
            )
            await interaction.response.send_message(embed=error_embed, ephemeral=True)

    @app_commands.command(name="dggmroll", description="[GM] Roll for any agent's skill")
    @app_commands.describe(
        agent="Agent callsign (autocomplete)",
        skill="Skill name",
        bonus="Bonus or penalty (+10, -20, +40, etc.)"
    )
    @app_commands.autocomplete(agent=agent_autocomplete)
    @app_commands.choices(bonus=BONUS_CHOICES)
    @app_commands.checks.has_permissions(manage_guild=True)
    async def dg_gm_roll(
        self,
        interaction: discord.Interaction,
        agent: str,
        skill: str,
        bonus: Optional[int] = 0
    ):
        """GM rolls for any agent."""
        try:
            # Find agent by callsign
            target_user_id = self._find_agent_by_callsign(agent)

            if not target_user_id:
                error_embed = self.embed_factory.error_message(
                    interaction.user.id,
                    f"Agent '{agent}' hittades inte",
                    "Använd `/dggmstatus` för att se alla agents."
                )
                await interaction.response.send_message(embed=error_embed, ephemeral=True)
                return

            # Get agent data
            agent_data = self.agent_manager.get_agent(target_user_id)
            if not agent_data:
                error_embed = self.embed_factory.error_message(
                    interaction.user.id,
                    f"Kunde inte ladda agent '{agent}'",
                    "Kontrollera att agent-filen existerar."
                )
                await interaction.response.send_message(embed=error_embed, ephemeral=True)
                return

            # Get skill value with fuzzy matching
            skill_value = self.agent_manager.get_skill_value(target_user_id, skill)

            if skill_value is None:
                error_embed = self.embed_factory.error_message(
                    interaction.user.id,
                    f"Skill '{skill}' hittades inte för {agent}",
                    f"Kontrollera att skill finns för agenten."
                )
                await interaction.response.send_message(embed=error_embed, ephemeral=True)
                return

            # Perform the skill check
            result = skill_check(skill_value, bonus or 0)

            # Track failed check if session active (GM rolls count too!)
            if self.session_manager.is_session_active(str(interaction.channel_id)):
                if result.result in (RollResult.FAILURE, RollResult.FUMBLE):
                    self.session_manager.record_failed_check(
                        str(interaction.channel_id),
                        target_user_id,
                        skill
                    )

            # Create embed with GM note
            embed = self.embed_factory.dg_roll_result(
                user_id=interaction.user.id,
                user_name=f"[GM] {agent_data['callsign']}",
                roll=result.roll,
                tens=result.tens_die,
                ones=result.ones_die,
                target=result.target,
                result_type=result.result.value,
                skill_name=skill,
                modifier=bonus or 0
            )

            await interaction.response.send_message(embed=embed)
            logger.info(f"GM roll: {interaction.user.display_name} rolled for {agent} - {skill} ({skill_value}%) = {result.roll}")

        except Exception as e:
            logger.error(f"Error in dg_gm_roll: {e}", exc_info=True)
            error_embed = self.embed_factory.error_message(
                interaction.user.id,
                "Ett fel uppstod",
                str(e)
            )
            await interaction.response.send_message(embed=error_embed, ephemeral=True)

    @app_commands.command(name="dggmstatus", description="[GM] View all agents")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def dg_gm_status(
        self,
        interaction: discord.Interaction
    ):
        """GM views all agents' status."""
        try:
            all_agents = self.agent_manager.list_all_agents()

            if not all_agents:
                error_embed = self.embed_factory.error_message(
                    interaction.user.id,
                    "Inga agents hittades",
                    "Kontakta utvecklaren för att skapa agents."
                )
                await interaction.response.send_message(embed=error_embed, ephemeral=True)
                return

            # Create status overview
            title = "🕵️ DELTA GREEN - All Agents Status"
            desc_lines = [
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━",
                ""
            ]

            for user_id, callsign in all_agents:
                agent = self.agent_manager.get_agent(user_id)
                if not agent:
                    continue

                # Get current values
                hp = agent['derived']['hp']['current']
                hp_max = agent['derived']['hp']['max']
                san = agent['derived']['san']['current']
                san_max = agent['derived']['san']['max']
                bp = agent['derived']['breaking_point']

                # Warning indicators
                warnings = []
                if san <= bp:
                    warnings.append("⚠️ AT BREAKING POINT")
                elif san <= bp + 5:
                    warnings.append(f"⚠️ {san - bp}pts to BP")
                if hp <= 2:
                    warnings.append("💀 CRITICAL HP")

                warning_str = " ".join(warnings) if warnings else ""

                desc_lines.append(f"**{callsign.upper()}** - {agent['name']}")
                desc_lines.append(f"HP: {hp}/{hp_max}  |  SAN: {san}/{san_max} (BP:{bp})  {warning_str}")
                desc_lines.append("")

            embed = discord.Embed(
                title=title,
                description="\n".join(desc_lines),
                color=0x2C3E50
            )
            embed.set_footer(text=f"Requested by {interaction.user.display_name}")

            await interaction.response.send_message(embed=embed)
            logger.info(f"GM status viewed by {interaction.user.display_name}")

        except Exception as e:
            logger.error(f"Error in dg_gm_status: {e}", exc_info=True)
            error_embed = self.embed_factory.error_message(
                interaction.user.id,
                "Ett fel uppstod",
                str(e)
            )
            await interaction.response.send_message(embed=error_embed, ephemeral=True)

    @app_commands.command(name="dggmset", description="[GM] Modify agent HP/WP/SAN")
    @app_commands.describe(
        agent="Agent callsign",
        attribute="Attribute to modify (hp/wp/san)",
        value="New value"
    )
    @app_commands.autocomplete(agent=agent_autocomplete)
    @app_commands.choices(attribute=[
        app_commands.Choice(name="HP", value="hp"),
        app_commands.Choice(name="WP", value="wp"),
        app_commands.Choice(name="SAN", value="san"),
    ])
    @app_commands.checks.has_permissions(manage_guild=True)
    async def dg_gm_set(
        self,
        interaction: discord.Interaction,
        agent: str,
        attribute: str,
        value: int
    ):
        """GM modifies agent attributes."""
        try:
            # Find agent by callsign
            target_user_id = self._find_agent_by_callsign(agent)

            if not target_user_id:
                error_embed = self.embed_factory.error_message(
                    interaction.user.id,
                    f"Agent '{agent}' hittades inte",
                    "Använd `/dggmstatus` för att se alla agents."
                )
                await interaction.response.send_message(embed=error_embed, ephemeral=True)
                return

            # Get agent
            agent_data = self.agent_manager.get_agent(target_user_id)
            if not agent_data:
                error_embed = self.embed_factory.error_message(
                    interaction.user.id,
                    f"Kunde inte ladda agent '{agent}'",
                    "Kontrollera att agent-filen existerar."
                )
                await interaction.response.send_message(embed=error_embed, ephemeral=True)
                return

            # Get old value and max
            old_value = agent_data['derived'][attribute]['current']
            max_value = agent_data['derived'][attribute]['max']

            # Set new value (clamped to 0-max)
            new_value = max(0, min(max_value, value))
            agent_data['derived'][attribute]['current'] = new_value

            # Save
            self.agent_manager.save_agent(target_user_id, agent_data)

            # Create confirmation embed
            title = f"✅ Agent Modified"
            description = f"**{agent_data['callsign']}** - {attribute.upper()} updated\n\n"
            description += f"{old_value} → **{new_value}** (max: {max_value})"

            embed = discord.Embed(
                title=title,
                description=description,
                color=0x2ECC71
            )
            embed.set_footer(text=f"Modified by {interaction.user.display_name}")

            await interaction.response.send_message(embed=embed)
            logger.info(f"GM set: {interaction.user.display_name} set {agent} {attribute} to {new_value}")

        except Exception as e:
            logger.error(f"Error in dg_gm_set: {e}", exc_info=True)
            error_embed = self.embed_factory.error_message(
                interaction.user.id,
                "Ett fel uppstod",
                str(e)
            )
            await interaction.response.send_message(embed=error_embed, ephemeral=True)

    # Session Management Commands

    @app_commands.command(name="dgstartsession", description="[GM] Start a Delta Green session")
    @app_commands.describe(
        session_name="Name of the session"
    )
    @app_commands.checks.has_permissions(manage_guild=True)
    async def dg_start_session(
        self,
        interaction: discord.Interaction,
        session_name: str
    ):
        """Start a Delta Green session for skill tracking."""
        try:
            channel_id = str(interaction.channel_id)

            if self.session_manager.is_session_active(channel_id):
                error_embed = self.embed_factory.error_message(
                    interaction.user.id,
                    "Session redan aktiv",
                    f"Använd `/dgendsession` för att avsluta den aktiva sessionen först."
                )
                await interaction.response.send_message(embed=error_embed, ephemeral=True)
                return

            # Start session
            success = self.session_manager.start_session(
                channel_id,
                session_name,
                interaction.user.display_name
            )

            if not success:
                error_embed = self.embed_factory.error_message(
                    interaction.user.id,
                    "Kunde inte starta session",
                    "Ett oväntat fel uppstod."
                )
                await interaction.response.send_message(embed=error_embed, ephemeral=True)
                return

            # Create confirmation embed
            title = "✅ Session Started"
            description = f"**{session_name}**\n\n"
            description += "📊 All failed skill checks will be tracked for skill improvement.\n\n"
            description += f"GM: {interaction.user.display_name}\n"
            description += f"Channel: {interaction.channel.name}"

            embed = discord.Embed(
                title=title,
                description=description,
                color=0x2ECC71
            )

            await interaction.response.send_message(embed=embed)
            logger.info(f"Started session '{session_name}' in channel {channel_id}")

        except Exception as e:
            logger.error(f"Error in dg_start_session: {e}", exc_info=True)
            error_embed = self.embed_factory.error_message(
                interaction.user.id,
                "Ett fel uppstod",
                str(e)
            )
            await interaction.response.send_message(embed=error_embed, ephemeral=True)

    @app_commands.command(name="dgendsession", description="[GM] End session and process skill improvements")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def dg_end_session(
        self,
        interaction: discord.Interaction
    ):
        """End session and perform skill improvement."""
        try:
            channel_id = str(interaction.channel_id)

            if not self.session_manager.is_session_active(channel_id):
                error_embed = self.embed_factory.error_message(
                    interaction.user.id,
                    "Ingen aktiv session",
                    f"Använd `/dgstartsession` för att starta en session först."
                )
                await interaction.response.send_message(embed=error_embed, ephemeral=True)
                return

            # Defer response since this might take a while
            await interaction.response.defer()

            # End session and process improvements
            session_data = self.session_manager.end_session(channel_id, self.agent_manager)

            if not session_data:
                error_embed = self.embed_factory.error_message(
                    interaction.user.id,
                    "Kunde inte avsluta session",
                    "Ett oväntat fel uppstod."
                )
                await interaction.followup.send(embed=error_embed, ephemeral=True)
                return

            # Export to Trip19
            export_path = self.session_manager.export_to_trip19(session_data)

            # Create summary embed
            title = "📊 Session Ended - Skill Improvements"
            desc_lines = [
                f"**{session_data['session_name']}**",
                "",
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━",
                ""
            ]

            improvements = session_data.get("improvements", {})
            if not improvements:
                desc_lines.append("No skill improvements this session.")
            else:
                for user_id, data in improvements.items():
                    agent = data["agent"]
                    agent_improvements = data["improvements"]

                    improved_skills = [
                        (skill, imp) for skill, imp in agent_improvements.items()
                        if imp["improvement"] > 0
                    ]

                    if improved_skills:
                        desc_lines.append(f"**{agent['callsign'].upper()}**")
                        for skill, imp in improved_skills:
                            desc_lines.append(
                                f"• {skill}: {imp['old_value']}% → **{imp['new_value']}%** (+{imp['improvement']})"
                            )
                        desc_lines.append("")

            embed = discord.Embed(
                title=title,
                description="\n".join(desc_lines),
                color=0x3498DB
            )

            if export_path:
                embed.add_field(
                    name="📁 Exported",
                    value=f"```{export_path}```",
                    inline=False
                )

            await interaction.followup.send(embed=embed)
            logger.info(f"Ended session '{session_data['session_name']}' - exported to {export_path}")

        except Exception as e:
            logger.error(f"Error in dg_end_session: {e}", exc_info=True)
            error_embed = self.embed_factory.error_message(
                interaction.user.id,
                "Ett fel uppstod",
                str(e)
            )
            await interaction.followup.send(embed=error_embed, ephemeral=True)

    # Helper function to roll weapon damage
    def roll_weapon_damage(self, weapon_name: str) -> Dict:
        """Roll damage for a weapon."""
        import random
        import re

        weapon = WEAPON_DATA.get(weapon_name)
        if not weapon:
            return None

        # Check if weapon has lethality
        if weapon["lethality"]:
            let_result = lethality_roll(weapon["lethality"])

            if let_result.is_lethal:
                return {
                    "weapon": weapon_name,
                    "lethality": weapon["lethality"],
                    "roll": let_result.roll,
                    "is_lethal": True,
                    "damage": 0,
                    "description": "☠️ LETHAL - Instant Kill"
                }
            else:
                return {
                    "weapon": weapon_name,
                    "lethality": weapon["lethality"],
                    "roll": let_result.roll,
                    "is_lethal": False,
                    "damage": let_result.damage,
                    "description": f"Non-lethal: {let_result.damage} HP damage"
                }

        # Standard damage roll (e.g., "1d10", "2d8", "1d4-1", "1d12+2")
        damage_formula = weapon["damage"]

        # Parse formula (e.g., "2d8", "1d4-1", "1d12+2")
        match = re.match(r'(\d+)d(\d+)([-+]\d+)?', damage_formula)
        if not match:
            return None

        num_dice = int(match.group(1))
        dice_sides = int(match.group(2))
        modifier = int(match.group(3)) if match.group(3) else 0

        # Roll dice
        rolls = [random.randint(1, dice_sides) for _ in range(num_dice)]
        total_damage = sum(rolls) + modifier

        # Ensure damage is at least 0
        total_damage = max(0, total_damage)

        result = {
            "weapon": weapon_name,
            "lethality": None,
            "damage_formula": damage_formula,
            "rolls": rolls,
            "modifier": modifier,
            "damage": total_damage,
            "description": f"{damage_formula}: {' + '.join(map(str, rolls))}" + (f" {modifier:+d}" if modifier != 0 else "") + f" = {total_damage} HP"
        }

        # Add special effects
        if weapon.get("special"):
            result["special"] = weapon["special"]

        return result

    # Weapon autocomplete
    async def weapon_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str
    ) -> List[app_commands.Choice[str]]:
        """Autocomplete for weapons."""
        if current:
            matching = [name for name in WEAPON_DATA.keys() if current.lower() in name.lower()]
        else:
            matching = list(WEAPON_DATA.keys())

        return [app_commands.Choice(name=name, value=name) for name in matching[:25]]

    # Armor autocomplete
    async def armor_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str
    ) -> List[app_commands.Choice[str]]:
        """Autocomplete for armor."""
        if current:
            matching = [name for name in ARMOR_DATA.keys() if current.lower() in name.lower()]
        else:
            matching = list(ARMOR_DATA.keys())

        return [app_commands.Choice(name=name, value=name) for name in matching[:25]]

    @app_commands.command(name="dgdmg", description="Roll weapon damage against NPC/enemy")
    @app_commands.describe(weapon="Weapon to use (autocomplete)")
    @app_commands.autocomplete(weapon=weapon_autocomplete)
    async def dg_damage(
        self,
        interaction: discord.Interaction,
        weapon: str
    ):
        """Roll weapon damage (for shooting NPCs)."""
        try:
            if weapon not in WEAPON_DATA:
                error_embed = self.embed_factory.error_message(
                    interaction.user.id,
                    "Okänt vapen",
                    f"Vapnet '{weapon}' finns inte i listan."
                )
                await interaction.response.send_message(embed=error_embed, ephemeral=True)
                return

            # Roll damage
            result = self.roll_weapon_damage(weapon)

            if not result:
                error_embed = self.embed_factory.error_message(
                    interaction.user.id,
                    "Kunde inte rulla skada",
                    "Ett fel uppstod vid skadeberäkningen."
                )
                await interaction.response.send_message(embed=error_embed, ephemeral=True)
                return

            # Create embed
            title = "🔫 Weapon Damage Roll"
            desc_lines = [
                "━━━━━━━━━━━━━━━━━━━━━━━━━",
                "",
                f"**Weapon:** {weapon}",
                ""
            ]

            if result.get("is_lethal"):
                desc_lines.append(f"**Lethality:** {result['lethality']}%")
                desc_lines.append(f"**Roll:** {result['roll']:02d}")
                desc_lines.append("")
                desc_lines.append(f"**Result:** {result['description']}")
                color = 0x8E44AD  # Purple for lethal
            else:
                if result.get("lethality"):
                    desc_lines.append(f"**Lethality:** {result['lethality']}% (failed)")
                    desc_lines.append(f"**Roll:** {result['roll']:02d}")
                    desc_lines.append("")

                desc_lines.append(f"**Damage:** {result['description']}")

                if result.get("special"):
                    desc_lines.append(f"**Special:** {result['special']}")

                color = 0xE74C3C  # Red for damage

            embed = discord.Embed(
                title=title,
                description="\n".join(desc_lines),
                color=color
            )
            embed.set_footer(text=interaction.user.display_name)

            await interaction.response.send_message(embed=embed)
            logger.info(f"Damage roll: {interaction.user.display_name} rolled {weapon} -> {result['damage']} HP")

        except Exception as e:
            logger.error(f"Error in dg_damage: {e}", exc_info=True)
            error_embed = self.embed_factory.error_message(
                interaction.user.id,
                "Ett fel uppstod",
                str(e)
            )
            await interaction.response.send_message(embed=error_embed, ephemeral=True)

    @app_commands.command(name="dggmdmg", description="[GM] Apply weapon damage to an agent")
    @app_commands.describe(
        agent="Agent callsign (autocomplete)",
        weapon="Weapon used (autocomplete)",
        armor="Armor worn (optional, autocomplete)"
    )
    @app_commands.autocomplete(agent=agent_autocomplete, weapon=weapon_autocomplete, armor=armor_autocomplete)
    @app_commands.checks.has_permissions(manage_guild=True)
    async def dg_gm_damage(
        self,
        interaction: discord.Interaction,
        agent: str,
        weapon: str,
        armor: Optional[str] = "None"
    ):
        """GM applies damage to an agent."""
        try:
            # Find agent by callsign
            user_id = self._find_agent_by_callsign(agent)

            if not user_id:
                error_embed = self.embed_factory.error_message(
                    interaction.user.id,
                    "Agent inte hittad",
                    f"Kunde inte hitta agent '{agent}'."
                )
                await interaction.response.send_message(embed=error_embed, ephemeral=True)
                return

            # Get agent data
            agent_data = self.agent_manager.get_agent(user_id)
            if not agent_data:
                error_embed = self.embed_factory.error_message(
                    interaction.user.id,
                    "Agent inte hittad",
                    f"Kunde inte ladda data för '{agent}'."
                )
                await interaction.response.send_message(embed=error_embed, ephemeral=True)
                return

            if weapon not in WEAPON_DATA:
                error_embed = self.embed_factory.error_message(
                    interaction.user.id,
                    "Okänt vapen",
                    f"Vapnet '{weapon}' finns inte i listan."
                )
                await interaction.response.send_message(embed=error_embed, ephemeral=True)
                return

            # Roll damage
            result = self.roll_weapon_damage(weapon)

            if not result:
                error_embed = self.embed_factory.error_message(
                    interaction.user.id,
                    "Kunde inte rulla skada",
                    "Ett fel uppstod vid skadeberäkningen."
                )
                await interaction.response.send_message(embed=error_embed, ephemeral=True)
                return

            # Get armor rating
            armor_rating = ARMOR_DATA.get(armor, 0)

            # Apply damage to agent
            old_hp = agent_data["derived"]["hp"]["current"]
            raw_damage = result["damage"]
            armor_absorbed = 0

            if result.get("is_lethal"):
                # Lethal hit - armor doesn't help against lethality
                new_hp = 0
                self.agent_manager.set_hp(user_id, 0)
            else:
                # Apply armor reduction
                damage = result["damage"]
                if armor_rating > 0:
                    armor_absorbed = min(armor_rating, damage)
                    damage = max(0, damage - armor_rating)

                hp_result = self.agent_manager.modify_hp(user_id, -damage)
                if hp_result:
                    old_hp, new_hp = hp_result
                else:
                    error_embed = self.embed_factory.error_message(
                        interaction.user.id,
                        "Kunde inte applicera skada",
                        "Ett fel uppstod."
                    )
                    await interaction.response.send_message(embed=error_embed, ephemeral=True)
                    return

            # Create embed
            title = f"💥 Damage Applied - {agent_data['callsign']}"
            desc_lines = [
                "━━━━━━━━━━━━━━━━━━━━━━━━━",
                "",
                f"**Weapon:** {weapon}",
                ""
            ]

            if result.get("is_lethal"):
                desc_lines.append(f"**Lethality:** {result['lethality']}%")
                desc_lines.append(f"**Roll:** {result['roll']:02d}")
                desc_lines.append("")
                if armor != "None":
                    desc_lines.append(f"**Armor:** {armor} (AR {armor_rating}) - NO EFFECT against lethality")
                    desc_lines.append("")
                desc_lines.append(f"**Result:** ☠️ LETHAL HIT")
                desc_lines.append(f"**HP:** {old_hp} → **0** (DYING)")
                color = 0x8E44AD  # Purple for lethal
            else:
                if result.get("lethality"):
                    desc_lines.append(f"**Lethality:** {result['lethality']}% (failed)")
                    desc_lines.append(f"**Roll:** {result['roll']:02d}")
                    desc_lines.append("")

                desc_lines.append(f"**Damage:** {result['description']}")

                if armor != "None":
                    desc_lines.append(f"**Armor:** {armor} (AR {armor_rating})")
                    desc_lines.append(f"**Absorbed:** {armor_absorbed} HP")
                    desc_lines.append(f"**Final Damage:** {raw_damage - armor_absorbed} HP")

                if result.get("special"):
                    desc_lines.append(f"**Special:** {result['special']}")

                desc_lines.append("")
                desc_lines.append(f"**HP:** {old_hp} → **{new_hp}**")

                if new_hp <= 0:
                    desc_lines.append("")
                    desc_lines.append("⚠️ **AGENT DOWN**")
                    color = 0x8E44AD  # Purple
                elif new_hp <= agent_data["derived"]["hp"]["max"] // 4:
                    desc_lines.append("")
                    desc_lines.append("⚠️ **CRITICALLY WOUNDED**")
                    color = 0xE74C3C  # Red
                else:
                    color = 0xF39C12  # Orange

            embed = discord.Embed(
                title=title,
                description="\n".join(desc_lines),
                color=color
            )
            embed.set_footer(text=f"GM: {interaction.user.display_name}")

            await interaction.response.send_message(embed=embed)
            logger.info(f"GM damage: {interaction.user.display_name} applied {result['damage']} dmg to {agent} with {weapon}")

        except Exception as e:
            logger.error(f"Error in dg_gm_damage: {e}", exc_info=True)
            error_embed = self.embed_factory.error_message(
                interaction.user.id,
                "Ett fel uppstod",
                str(e)
            )
            await interaction.response.send_message(embed=error_embed, ephemeral=True)

    @app_commands.command(name="dggmreset", description="[GM] Reset agent HP/WP/SAN to original values")
    @app_commands.describe(agent="Agent callsign (autocomplete)")
    @app_commands.autocomplete(agent=agent_autocomplete)
    @app_commands.checks.has_permissions(manage_guild=True)
    async def dg_gm_reset(
        self,
        interaction: discord.Interaction,
        agent: str
    ):
        """GM resets agent to original HP/WP/SAN (current = max)."""
        try:
            # Find agent by callsign
            user_id = self._find_agent_by_callsign(agent)

            if not user_id:
                error_embed = self.embed_factory.error_message(
                    interaction.user.id,
                    "Agent inte hittad",
                    f"Kunde inte hitta agent '{agent}'."
                )
                await interaction.response.send_message(embed=error_embed, ephemeral=True)
                return

            # Get agent data
            agent_data = self.agent_manager.get_agent(user_id)
            if not agent_data:
                error_embed = self.embed_factory.error_message(
                    interaction.user.id,
                    "Agent inte hittad",
                    f"Kunde inte ladda data för '{agent}'."
                )
                await interaction.response.send_message(embed=error_embed, ephemeral=True)
                return

            # Store old values
            old_hp = agent_data["derived"]["hp"]["current"]
            old_wp = agent_data["derived"]["wp"]["current"]
            old_san = agent_data["derived"]["san"]["current"]

            max_hp = agent_data["derived"]["hp"]["max"]
            max_wp = agent_data["derived"]["wp"]["max"]
            max_san = agent_data["derived"]["san"]["max"]

            # Restore to max
            agent_data["derived"]["hp"]["current"] = max_hp
            agent_data["derived"]["wp"]["current"] = max_wp
            agent_data["derived"]["san"]["current"] = max_san

            # Save
            self.agent_manager.save_agent(user_id, agent_data)

            # Create embed
            title = f"🔄 Agent Reset - {agent_data['callsign']}"
            desc_lines = [
                "━━━━━━━━━━━━━━━━━━━━━━━━━",
                "",
                "**Reset to original values (current = max)**",
                ""
            ]

            # Show changes
            if old_hp < max_hp:
                desc_lines.append(f"**HP:** {old_hp} → **{max_hp}** (+{max_hp - old_hp})")
            else:
                desc_lines.append(f"**HP:** {max_hp} (already full)")

            if old_wp < max_wp:
                desc_lines.append(f"**WP:** {old_wp} → **{max_wp}** (+{max_wp - old_wp})")
            else:
                desc_lines.append(f"**WP:** {max_wp} (already full)")

            if old_san < max_san:
                desc_lines.append(f"**SAN:** {old_san} → **{max_san}** (+{max_san - old_san})")
            else:
                desc_lines.append(f"**SAN:** {max_san} (already full)")

            embed = discord.Embed(
                title=title,
                description="\n".join(desc_lines),
                color=0x2ECC71  # Green
            )
            embed.set_footer(text=f"GM: {interaction.user.display_name}")

            await interaction.response.send_message(embed=embed)
            logger.info(f"GM reset: {interaction.user.display_name} reset {agent} to original HP/WP/SAN")

        except Exception as e:
            logger.error(f"Error in dg_gm_reset: {e}", exc_info=True)
            error_embed = self.embed_factory.error_message(
                interaction.user.id,
                "Ett fel uppstod",
                str(e)
            )
            await interaction.response.send_message(embed=error_embed, ephemeral=True)


async def register_slash_dg_commands(bot, embed_factory, agent_manager, session_manager):
    """Register Delta Green slash commands."""
    try:
        dg_cog = DeltaGreenCommands(bot, embed_factory, agent_manager, session_manager)
        await bot.add_cog(dg_cog)
        logger.info("Delta Green commands registered successfully")
    except Exception as e:
        logger.error(f"Failed to register Delta Green commands: {e}", exc_info=True)
        raise
