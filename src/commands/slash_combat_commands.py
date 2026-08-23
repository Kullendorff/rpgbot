"""
Slash commands för combat operations i EON Discord Bot.
Konverterar prefix commands (!hugg, !stick, !kross, !fummel) till moderna slash commands.
"""

import random
import time
from typing import List, Optional, Tuple, Any
import discord
from discord.ext import commands
from discord import app_commands
from discord import ui

# Import migration helpers
from migration.helper import MigrationHelper, SlashCommandDecorator

# Import fumble tables and weapon aliases
from fumble_tables import FUMBLE_TABLES, WEAPON_TYPE_ALIASES


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
            from combat_manager import DamageType, WeaponType

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
                from damage_tables import parse_effect_code
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

class CombatSlashCommands(commands.Cog):
    """Cog för alla combat-relaterade slash commands."""
    
    def __init__(self, bot, combat_manager, color_handler, embed_factory):
        self.bot = bot
        self.combat_manager = combat_manager
        self.color_handler = color_handler
        self.embed_factory = embed_factory
        
        # Migration helper för säker hantering
        self.helper = MigrationHelper(embed_factory)
        self.decorator = SlashCommandDecorator(self.helper)
    
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

    @app_commands.command(name="hugg", description="Utför en hugganfall mot valfritt träffområde")
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
    async def hugg_slash(
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
        await self.helper.log_command_usage(interaction, "hugg", {
            "damage": bas_skada,
            "level": nivå,
            "location": område,
            "malpunkter": målpunkter
        }, execution_time)

    @app_commands.command(name="stick", description="Utför en stickanfall mot valfritt träffområde")
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
    async def stick_slash(
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
        await self.helper.log_command_usage(interaction, "stick", {
            "damage": bas_skada,
            "level": nivå,
            "location": område,
            "malpunkter": målpunkter
        }, execution_time)

    @app_commands.command(name="kross", description="Utför en krossanfall mot valfritt träffområde")
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
    async def kross_slash(
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
        await self.helper.log_command_usage(interaction, "kross", {
            "damage": bas_skada,
            "level": nivå,
            "location": område,
            "malpunkter": målpunkter
        }, execution_time)

    @app_commands.command(name="fummel", description="Slå på fummeltabellen för specifik vapentyp")
    @app_commands.describe(
        vapen="Typ av vapen som fummel sker med"
    )
    @app_commands.choices(vapen=[
        app_commands.Choice(name="Obevapnat", value="obe"),
        app_commands.Choice(name="Närstridsvapen", value="nar"),
        app_commands.Choice(name="Avståndsvapen", value="avs"),
        app_commands.Choice(name="Sköldar", value="sko")
    ])
    async def fummel_slash(
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
            await self.helper.log_command_usage(interaction, "fummel", {
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


# Registrering function
async def register_slash_combat_commands(bot, combat_manager, color_handler, embed_factory):
    """
    Registrera slash combat commands med boten.
    """
    # TODO: Ta bort sys.path manipulation - använd proper package structure
    # import sys
    # import os
    # sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
    from config.feature_flags import is_command_enabled
    
    # Kontrollera om slash combat commands är aktiverade
    if not is_command_enabled("hugg", "combat"):
        print("Slash combat commands är inte aktiverade enligt feature flags")
        return
    
    # Lägg till cog
    combat_cog = CombatSlashCommands(bot, combat_manager, color_handler, embed_factory)
    await bot.add_cog(combat_cog)
    print("Slash combat commands har registrerats (/hugg, /stick, /kross, /fummel).")