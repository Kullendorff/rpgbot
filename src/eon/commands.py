"""
EON-kommandon (Cog) — /eon_hugg, /eon_stick, /eon_kross, /eon_fummel,
/eon_regel, /eon_hoj.

Del av paketet src/eon/: ren mekanik ligger i hit_tables/damage_tables/
fumble_tables/combat_manager, detta är Discord-lagret.
"""

import os
import random
import time
import logging
from typing import List, Optional, Tuple, Any
import discord
from discord.ext import commands
from discord import app_commands
from discord import ui

# Setup logging
logger = logging.getLogger(__name__)

# Import migration helpers
from migration.helper import MigrationHelper

# Delad infrastruktur (absoluta importer)
from core.dice_engine import unlimited_d6s

# Relativa importer inuti paketet
from .combat_manager import DamageType, WeaponType
from .damage_tables import parse_effect_code
from .fumble_tables import FUMBLE_TABLES, WEAPON_TYPE_ALIASES


class ArmorModal(ui.Modal):
    """Modal för att ange rustningsvärde på träffområde."""

    def __init__(self, combat_cog, weapon: str, bas_skada: int, result: Any, malpunkter: bool):
        # Formatera träffområde för modal title
        hit_zone = f"{result.sub_location.capitalize()} ({result.location_code})"
        super().__init__(title=f"Träff: {hit_zone}")

        self.combat_cog = combat_cog
        self.weapon = weapon
        self.bas_skada = bas_skada
        self.result = result
        self.malpunkter = malpunkter

    rustning = ui.TextInput(
        label="Rustningsvärde",
        placeholder="Ange rustningsvärde (0-50)",
        required=True,
        min_length=1,
        max_length=2,
        default="0"
    )

    async def on_submit(self, interaction: discord.Interaction):
        """Hantera när Modal skickas in."""
        try:
            # Validera rustningsvärde
            try:
                armor_value = int(self.rustning.value)
                if armor_value < 0 or armor_value > 50:
                    raise ValueError("Rustning måste vara mellan 0 och 50")
            except ValueError as e:
                await interaction.response.send_message(
                    f"❌ Ogiltigt rustningsvärde: {self.rustning.value}",
                    ephemeral=True
                )
                return

            # Beräkna slutskada
            final_damage = max(0, self.bas_skada - armor_value)

            # Nu behöver vi omberäkna skaderesultatet med den nya slutskadan
            # eftersom damage_result beror på damage_value >= 10
            damage_type_map = {
                "hugg": DamageType.HUGG,
                "stick": DamageType.STICK,
                "kross": DamageType.KROSS
            }
            damage_type = damage_type_map[self.weapon]

            # Hämta damage location från sub_location via location_mapping (samma som combat_manager gör)
            damage_location = self.combat_cog.combat_manager.location_mapping.get(self.result.sub_location.lower())

            if not damage_location:
                await interaction.response.send_message(
                    f"❌ Kunde inte hitta skademapping för '{self.result.sub_location}'",
                    ephemeral=True
                )
                return

            # Omberäkna skaderesultat med slutskadan
            damage_result = self.combat_cog.combat_manager.damage_calculator.get_damage(
                damage_type=damage_type,
                location=damage_location,
                damage_value=final_damage,
                use_malpunkter=self.malpunkter,
                user_id=str(interaction.user.id)
            )

            # Formatera träffzone
            hit_zone_display = f"{self.result.hit_location.capitalize()} - {self.result.sub_location.capitalize()}"

            # Beräkna effektresultaten
            damage_effects = None
            if damage_result and damage_result.effect_code:
                damage_effects = parse_effect_code(damage_result.effect_code, final_damage)

            # Skapa embed för slutresultat
            embed = self.combat_cog.embed_factory.combat_result(
                interaction.user.id,
                interaction.user.display_name,
                self.weapon.capitalize(),
                weapon_type=self.weapon,
                damage_value=final_damage,
                hit_zone=hit_zone_display,
                effect_code=damage_result.effect_code if damage_result else None,
                description=damage_result.description if damage_result else None,
                location_code=self.result.location_code,
                special_effects=damage_result.effects if damage_result else [],
                use_malpunkter=self.malpunkter,
                damage_effects=damage_effects
            )

            # Lägg till skadeinformation
            embed.add_field(
                name="💥 Skadeberäkning",
                value=f"Basskada: **{self.bas_skada}**\n"
                      f"Rustning: **-{armor_value}**\n"
                      f"Slutskada: **{final_damage}**",
                inline=False
            )

            # Lägg till parametrar
            parameter_info = []
            if self.malpunkter:
                parameter_info.append("🎯 Målpunkter")

            if parameter_info:
                embed.add_field(
                    name="⚔️ Modifierare",
                    value=" • ".join(parameter_info),
                    inline=False
                )

            await interaction.response.send_message(embed=embed)

        except Exception as e:
            await interaction.response.send_message(
                f"❌ Ett fel inträffade: {str(e)}",
                ephemeral=True
            )
            import traceback
            traceback.print_exc()

class EonCommands(commands.Cog):
    """Cog för EON-stridskommandon."""

    def __init__(self, bot, combat_manager, roll_tracker, color_handler, embed_factory):
        self.bot = bot
        self.combat_manager = combat_manager
        self.roll_tracker = roll_tracker
        self.color_handler = color_handler
        self.embed_factory = embed_factory
        
        # Migration helper för säker hantering
        self.helper = MigrationHelper(embed_factory)

        # Configure paths for rules folder
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(script_dir))
        self.RULES_FOLDER = os.path.join(project_root, "data", "rules")

        # Create rules folder if it doesn't exist
        if not os.path.exists(self.RULES_FOLDER):
            os.makedirs(self.RULES_FOLDER)

    async def location_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str,
    ) -> List[app_commands.Choice[str]]:
        """Autocomplete för träffområden."""
        # Breda områden (slår på delområdestabellen) + specifika delområden (direkt träff)
        locations = [
            # Breda områden (slår automatiskt på delområdestabellen)
            "huvud",      # → slår på: ansikte, skalle, hals
            "armar",      # → slår på armens delområden
            "ben",        # → slår på benets delområden
            "buk",        # → slår på: mage, underliv

            # Specifika huvuddelområden (direkt träff)
            "ansikte", "skalle", "hals",

            # Specifika armdelområden (direkt träff)
            "skuldra", "överarm", "armbåge", "underarm", "hand",

            # Bröstkorg (direkt träff)
            "bröstkorg",

            # Specifika bukdelområden (direkt träff)
            "mage", "underliv",

            # Specifika bendelområden (direkt träff)
            "höft", "lår", "knä", "vad", "fot"
        ]

        # Filtrera baserat på current input
        matches = [
            app_commands.Choice(name=location.capitalize(), value=location)
            for location in locations
            if current.lower() in location.lower()
        ]

        return matches[:25]  # Discord limit
    
    async def process_slash_melee_command(
        self,
        interaction: discord.Interaction,
        weapon: str,
        level: Optional[str],
        location: Optional[str],
        damage: int,
        malpunkter: bool
    ) -> None:
        """
        Hanterar gemensam logik för slash melee-kommandon.
        
        Args:
            interaction: Discord interaction
            weapon: Vapentyp (hugg, stick, kross)
            level: Attack level om inget specifikt område anges
            location: Specifikt träffområde
            damage: Skadevärde
            malpunkter: Målpunkter-teknik
        """
        try:
            # Bestäm level_or_location baserat på parametrar
            if location:
                level_or_location = location
                location_override = location.lower()
            else:
                level_or_location = level or "normal"
                location_override = None
            
            # Kontrollera om Målpunkter kan användas
            if malpunkter and not location_override:
                embed = await self.helper.create_error_response(
                    interaction.user.id,
                    "Målpunkter kan endast användas med specifikt träffområde",
                    "Välj ett specifikt område (t.ex. huvud, bröstkorg) för att använda Målpunkter"
                )
                await self.helper.send_response(interaction, embed=embed)
                return
            
            # Skapa flags string för bakåtkompatibilitet
            flags = ""
            if malpunkter:
                flags += " --mp"
            
            # Använd befintlig combat manager logik (ENDAST för träffområde, inte skada än)
            result = self.combat_manager.process_attack(
                weapon_type=weapon,
                attack_level=level_or_location if level_or_location.lower() in ["låg", "normal", "hög"] else None,
                damage_value=damage,  # Basskada, kommer omberäknas efter rustning
                location_override=location_override,
                use_malpunkter=malpunkter,
                user_id=str(interaction.user.id)
            )

            # Visa Modal för rustningsfråga
            modal = ArmorModal(
                combat_cog=self,
                weapon=weapon,
                bas_skada=damage,
                result=result,
                malpunkter=malpunkter
            )

            await interaction.response.send_modal(modal)
            
        except ValueError as e:
            embed = await self.helper.create_error_response(
                interaction.user.id,
                f"Fel i {weapon}-attack",
                str(e)
            )
            await self.helper.send_response(interaction, embed=embed)
        except Exception as e:
            embed = await self.helper.create_error_response(
                interaction.user.id,
                f"Ett oväntat fel inträffade: {str(e)}"
            )
            await self.helper.send_response(interaction, embed=embed)

    @app_commands.command(name="eon_hugg", description="Utför en hugganfall mot valfritt träffområde")
    @app_commands.describe(
        bas_skada="Basskada INNAN rustning dras av (1-100)",
        nivå="Attacknivå om inget specifikt område väljs",
        område="Specifikt träffområde (valfritt)",
        målpunkter="Använd Målpunkter-teknik (kräver specifikt område)"
    )
    @app_commands.choices(nivå=[
        app_commands.Choice(name="Låg nivå", value="låg"),
        app_commands.Choice(name="Normal nivå", value="normal"),
        app_commands.Choice(name="Hög nivå", value="hög")
    ])
    @app_commands.autocomplete(område=location_autocomplete)
    async def eon_hugg(
        self,
        interaction: discord.Interaction,
        bas_skada: app_commands.Range[int, 1, 100],
        nivå: Optional[str] = "normal",
        område: Optional[str] = None,
        målpunkter: bool = False
    ):
        """Slash command version av !hugg."""
        start_time = time.time()

        await self.process_slash_melee_command(
            interaction, "hugg", nivå, område, bas_skada, målpunkter
        )

        execution_time = time.time() - start_time
        await self.helper.log_command_usage(interaction, "eon_hugg", {
            "damage": bas_skada,
            "level": nivå,
            "location": område,
            "malpunkter": målpunkter
        }, execution_time)

    @app_commands.command(name="eon_stick", description="Utför en stickanfall mot valfritt träffområde")
    @app_commands.describe(
        bas_skada="Basskada INNAN rustning dras av (1-100)",
        nivå="Attacknivå om inget specifikt område väljs",
        område="Specifikt träffområde (valfritt)",
        målpunkter="Använd Målpunkter-teknik (kräver specifikt område)"
    )
    @app_commands.choices(nivå=[
        app_commands.Choice(name="Låg nivå", value="låg"),
        app_commands.Choice(name="Normal nivå", value="normal"),
        app_commands.Choice(name="Hög nivå", value="hög")
    ])
    @app_commands.autocomplete(område=location_autocomplete)
    async def eon_stick(
        self,
        interaction: discord.Interaction,
        bas_skada: app_commands.Range[int, 1, 100],
        nivå: Optional[str] = "normal",
        område: Optional[str] = None,
        målpunkter: bool = False
    ):
        """Slash command version av !stick."""
        start_time = time.time()

        await self.process_slash_melee_command(
            interaction, "stick", nivå, område, bas_skada, målpunkter
        )

        execution_time = time.time() - start_time
        await self.helper.log_command_usage(interaction, "eon_stick", {
            "damage": bas_skada,
            "level": nivå,
            "location": område,
            "malpunkter": målpunkter
        }, execution_time)

    @app_commands.command(name="eon_kross", description="Utför en krossanfall mot valfritt träffområde")
    @app_commands.describe(
        bas_skada="Basskada INNAN rustning dras av (1-100)",
        nivå="Attacknivå om inget specifikt område väljs",
        område="Specifikt träffområde (valfritt)",
        målpunkter="Använd Målpunkter-teknik (kräver specifikt område)"
    )
    @app_commands.choices(nivå=[
        app_commands.Choice(name="Låg nivå", value="låg"),
        app_commands.Choice(name="Normal nivå", value="normal"),
        app_commands.Choice(name="Hög nivå", value="hög")
    ])
    @app_commands.autocomplete(område=location_autocomplete)
    async def eon_kross(
        self,
        interaction: discord.Interaction,
        bas_skada: app_commands.Range[int, 1, 100],
        nivå: Optional[str] = "normal",
        område: Optional[str] = None,
        målpunkter: bool = False
    ):
        """Slash command version av !kross."""
        start_time = time.time()

        await self.process_slash_melee_command(
            interaction, "kross", nivå, område, bas_skada, målpunkter
        )

        execution_time = time.time() - start_time
        await self.helper.log_command_usage(interaction, "eon_kross", {
            "damage": bas_skada,
            "level": nivå,
            "location": område,
            "malpunkter": målpunkter
        }, execution_time)

    @app_commands.command(name="eon_fummel", description="Slå på fummeltabellen för specifik vapentyp")
    @app_commands.describe(
        vapen="Typ av vapen som fummel sker med"
    )
    @app_commands.choices(vapen=[
        app_commands.Choice(name="Obevapnat", value="obe"),
        app_commands.Choice(name="Närstridsvapen", value="nar"),
        app_commands.Choice(name="Avståndsvapen", value="avs"),
        app_commands.Choice(name="Sköldar", value="sko")
    ])
    async def eon_fummel(
        self,
        interaction: discord.Interaction,
        vapen: str
    ):
        """Slash command version av !fummel."""
        start_time = time.time()
        
        try:
            # Validera weapon type
            if vapen not in WEAPON_TYPE_ALIASES:
                embed = await self.helper.create_error_response(
                    interaction.user.id,
                    "Ogiltig vapentyp",
                    "Välj en av de tillgängliga vapentyperna"
                )
                await self.helper.send_response(interaction, embed=embed)
                return
            
            # Slå på fummeltabellen
            full_name = WEAPON_TYPE_ALIASES[vapen]
            result = random.randint(1, 20)
            fummel_text = FUMBLE_TABLES[full_name][result]
            
            # Skapa fummel embed
            embed = self.embed_factory.error_message(
                interaction.user.id,
                f"💥 Fummel: {full_name.capitalize()}"
            )
            
            embed.add_field(
                name="🎲 Tärningsslag",
                value=str(result),
                inline=True
            )
            
            embed.add_field(
                name="⚔️ Vapentyp", 
                value=full_name.capitalize(),
                inline=True
            )
            
            embed.add_field(
                name="💥 Fummelresultat",
                value=fummel_text,
                inline=False
            )
            
            execution_time = time.time() - start_time
            await self.helper.log_command_usage(interaction, "eon_fummel", {
                "weapon_type": vapen,
                "result": result
            }, execution_time)
            
            await self.helper.send_response(interaction, embed=embed)
            
        except Exception as e:
            embed = await self.helper.create_error_response(
                interaction.user.id,
                f"Ett oväntat fel inträffade: {str(e)}"
            )
            await self.helper.send_response(interaction, embed=embed)


    async def rule_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str,
    ) -> List[app_commands.Choice[str]]:
        """Autocomplete för regelnamn och nummer."""
        try:
            rules = os.listdir(self.RULES_FOLDER)
            txt_rules = sorted([rule for rule in rules if rule.endswith('.txt')])
            rule_names = [os.path.splitext(rule)[0] for rule in txt_rules]

            matches = []

            # Om input är numerisk, föreslå nummer
            if current.isdigit():
                for i, rule_name in enumerate(rule_names, 1):
                    if str(i).startswith(current):
                        matches.append(
                            app_commands.Choice(name=f"{i}. {rule_name.title()}", value=str(i))
                        )
            else:
                # Föreslå namn och nummer som matchar
                for i, rule_name in enumerate(rule_names, 1):
                    if current.lower() in rule_name.lower():
                        # Lägg till både nummer och namn som alternativ
                        matches.append(
                            app_commands.Choice(name=f"{i}. {rule_name.title()}", value=str(i))
                        )
                        matches.append(
                            app_commands.Choice(name=rule_name.title(), value=rule_name)
                        )

            return matches[:25]  # Discord limit
        except Exception as e:
            logger.error(f"Fel vid regel autocomplete: {e}")
            return []

    @app_commands.command(name="eon_regel", description="Visa sparade regler från regelbiblioteket")
    @app_commands.describe(
        val="Regelnamn eller nummer (t.ex. 'strid' eller '1')"
    )
    @app_commands.autocomplete(val=rule_autocomplete)
    async def eon_regel(
        self,
        interaction: discord.Interaction,
        val: Optional[str] = None
    ):
        """Slash command version av !regel med autocomplete."""
        start_time = time.time()

        try:
            rules = os.listdir(self.RULES_FOLDER)
            txt_rules = sorted([rule for rule in rules if rule.endswith('.txt')])  # Sorterad för konsistent numrering

            if not val:
                # Lista alla regler med nummer
                if not txt_rules:
                    embed = await self.helper.create_error_response(
                        interaction.user.id,
                        "Inga regler tillgängliga",
                        "Regelbiblioteket är tomt"
                    )
                    await self.helper.send_response(interaction, embed=embed)
                    return

                embed = self.embed_factory.admin_message(
                    interaction.user.id,
                    "📚 Tillgängliga Regler",
                    f"Totalt {len(txt_rules)} regler i biblioteket"
                )

                # Skapa numrerad lista
                rule_names = [os.path.splitext(rule)[0] for rule in txt_rules]
                rule_lines = []

                for i, rule_name in enumerate(rule_names, 1):
                    rule_lines.append(f"`{i}.` **{rule_name.title()}**")
                    if i >= 20:  # Begränsa för att inte överskrida Discord-gränser
                        rule_lines.append(f"... och {len(rule_names) - 20} till")
                        break

                rule_text = "\n".join(rule_lines)

                embed.add_field(
                    name="Regelnamn",
                    value=rule_text,
                    inline=False
                )

                embed.set_footer(text="Använd /eon_regel val:1 eller /eon_regel val:regelnamn för att visa specifik regel")

            else:
                # Visa specifik regel - hantera både nummer och namn
                rule_file = None
                rule_name = None

                # Kolla om input är ett nummer
                if val.isdigit():
                    rule_num = int(val)
                    if 1 <= rule_num <= len(txt_rules):
                        rule_file = txt_rules[rule_num - 1]  # Konvertera från 1-indexerad till 0-indexerad
                        rule_name = os.path.splitext(rule_file)[0]
                    else:
                        embed = await self.helper.create_error_response(
                            interaction.user.id,
                            f"Regel nummer {rule_num} finns inte",
                            f"Tillgängliga regler: 1-{len(txt_rules)}. Använd /regel för att se listan."
                        )
                        await self.helper.send_response(interaction, embed=embed)
                        return
                else:
                    # Hantera som namn
                    rule_name = val
                    rule_file = f"{rule_name}.txt"
                    if rule_file not in txt_rules:
                        # Försök hitta match
                        matches = [rule for rule in txt_rules if rule_name.lower() in rule.lower()]
                        if matches:
                            rule_file = matches[0]
                            rule_name = os.path.splitext(rule_file)[0]
                        else:
                            embed = await self.helper.create_error_response(
                                interaction.user.id,
                                f"Regel '{rule_name}' hittades inte",
                                f"Tillgängliga regler: {', '.join([os.path.splitext(r)[0] for r in txt_rules[:5]])}... Använd /regel för fullständig lista."
                            )
                            await self.helper.send_response(interaction, embed=embed)
                            return

                # Läs regelfilen
                with open(os.path.join(self.RULES_FOLDER, rule_file), "r", encoding="utf-8") as f:
                    content = f.read()

                embed = self.embed_factory.admin_message(
                    interaction.user.id,
                    f"📜 Regel: {rule_name.title()}",
                    content[:2000] if len(content) <= 2000 else content[:1997] + "..."
                )

                if len(content) > 2000:
                    embed.set_footer(text="Regel trunkerad - fulltext för lång för Discord")

            execution_time = time.time() - start_time
            await self.helper.log_command_usage(interaction, "eon_regel", {
                "rule_name": val if val else "all_rules",
                "rules_available": len(txt_rules)
            }, execution_time)

            await self.helper.send_response(interaction, embed=embed)

        except Exception as e:
            embed = await self.helper.create_error_response(
                interaction.user.id,
                f"Ett oväntat fel inträffade: {str(e)}"
            )
            await self.helper.send_response(interaction, embed=embed)

    @app_commands.command(name="eon_hoj", description="Gör förbättringsslag för färdigheter enligt EON-regler")
    @app_commands.describe(
        värde="Nuvarande färdighetsvärde (1-30)",
        lättlärd="Färdigheten är lättlärd (Ob4T6 istället för Ob3T6)"
    )
    async def eon_hoj(
        self,
        interaction: discord.Interaction,
        värde: app_commands.Range[int, 1, 30],
        lättlärd: bool = False
    ):
        """Slash command version av !höj."""
        start_time = time.time()

        try:
            # Sätt antal tärningar beroende på om färdigheten är lättlärd
            num_dice = 4 if lättlärd else 3

            # Slå obegränsade T6
            all_rolls, total, initial_rolls = unlimited_d6s(num_dice)

            # Kontrollera om förbättringen lyckas (måste slå lika med eller över)
            success = total >= värde
            new_skill = värde + 1 if success else värde

            # Skapa resultat embed
            embed = self.embed_factory.dice_result(
                interaction.user.id,
                interaction.user.display_name,
                "Förbättringsslag",
                f"{num_dice}d6 (obegränsat)",
                initial_rolls,
                total,
                värde,
                success
            )

            # Lägg till förbättringsspecifik information
            embed.add_field(
                name="🎓 Färdighetsstatus",
                value=f"{'Lättlärd' if lättlärd else 'Normal'} färdighet",
                inline=True
            )

            embed.add_field(
                name="📊 Nuvarande värde",
                value=str(värde),
                inline=True
            )

            embed.add_field(
                name="🎯 Resultat",
                value=f"{'✅ Förbättring!' if success else '❌ Ingen förbättring'}",
                inline=True
            )

            if success:
                embed.add_field(
                    name="⬆️ Nytt färdighetsvärde",
                    value=f"**{new_skill}** (+1)",
                    inline=False
                )
            else:
                embed.add_field(
                    name="ℹ️ Krav för förbättring",
                    value=f"Behöver slå {värde} eller över (slog {total})",
                    inline=False
                )

            # Visa alla kast om explosioner inträffade
            if len(all_rolls) > num_dice:
                embed.add_field(
                    name="💥 Alla kast (inkl. explosioner)",
                    value=str(all_rolls),
                    inline=False
                )

            # Logga i roll tracker (utan target eftersom det är skill improvement)
            self.roll_tracker.log_roll(
                str(interaction.user.id),
                interaction.user.display_name,
                "eon_hoj",
                num_dice,
                6,
                all_rolls,
                0,  # modifier
                värde,  # target
                success
            )

            execution_time = time.time() - start_time
            await self.helper.log_command_usage(interaction, "eon_hoj", {
                "current_skill": värde,
                "easy_learnable": lättlärd,
                "success": success,
                "new_skill": new_skill
            }, execution_time)

            await self.helper.send_response(interaction, embed=embed)

        except Exception as e:
            embed = await self.helper.create_error_response(
                interaction.user.id,
                f"Ett oväntat fel inträffade: {str(e)}"
            )
            await self.helper.send_response(interaction, embed=embed)


# Registrering function
async def register_slash_eon_commands(bot, combat_manager, roll_tracker, color_handler, embed_factory):
    """
    Registrera EON-stridskommandona med boten.
    """
    from config.feature_flags import is_command_enabled

    # Kontrollera om EON-kommandona är aktiverade
    if not is_command_enabled("eon_hugg", "eon"):
        logger.info("EON-stridskommandon är inte aktiverade enligt feature flags")
        return

    # Lägg till cog
    eon_cog = EonCommands(bot, combat_manager, roll_tracker, color_handler, embed_factory)
    await bot.add_cog(eon_cog)
    logger.info("EON-stridskommandon registrerade (/hugg, /stick, /kross, /fummel).")