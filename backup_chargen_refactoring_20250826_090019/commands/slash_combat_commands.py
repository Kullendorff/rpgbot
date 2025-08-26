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

# Import migration helpers
from migration.helper import MigrationHelper, SlashCommandDecorator

# Import fumble tables and weapon aliases
from fumble_tables import FUMBLE_TABLES, WEAPON_TYPE_ALIASES

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
        locations = [
            "huvud", "ansikte", "skalle", "hals",
            "vänster arm", "höger arm", "skuldra", "överarm", "armbage", "underarm", "hand",
            "bröstkorg", "buk", "mage", "underliv",
            "vänster ben", "höger ben", "höft", "lår", "knä", "vad", "fot"
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
        mounted: bool,
        quadruped: bool,
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
            mounted: Ryttarflagga
            quadruped: Fyrbeningsflagga
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
            if mounted:
                flags += " --ryttare"
            if quadruped:
                flags += " --djur"
            if malpunkter:
                flags += " --mp"
            
            # Använd befintlig combat manager logik
            result = self.combat_manager.process_attack(
                weapon_type=weapon,
                attack_level=level_or_location if level_or_location.lower() in ["låg", "normal", "hög"] else None,
                damage_value=damage,
                location_override=location_override,
                is_mounted=mounted,
                is_quadruped=quadruped,
                direction=None,
                use_malpunkter=malpunkter
            )
            
            # Formatera träffzone med både huvudområde och specifik kroppsdel
            hit_zone_display = f"{result.hit_location.capitalize()} - {result.sub_location.capitalize()}"
            
            # Beräkna effektresultaten 
            damage_effects = None
            if result.damage_result and result.damage_result.effect_code:
                from damage_tables import parse_effect_code
                damage_effects = parse_effect_code(result.damage_result.effect_code, result.damage_value)
            
            # Skapa embed för resultatet
            embed = self.embed_factory.combat_result(
                interaction.user.id,
                interaction.user.display_name,
                weapon.capitalize(),
                weapon_type=result.weapon_type.value,
                damage_value=result.damage_value,
                hit_zone=hit_zone_display,
                effect_code=result.damage_result.effect_code if result.damage_result else None,
                description=result.damage_result.description if result.damage_result else None,
                location_code=result.location_code,
                special_effects=result.damage_result.effects if result.damage_result else [],
                use_malpunkter=result.use_malpunkter,
                damage_effects=damage_effects
            )
            
            # Lägg till parametrar som användes
            parameter_info = []
            if mounted:
                parameter_info.append("🐎 Ryttare")
            if quadruped:
                parameter_info.append("🦌 Fyrbent mål")
            if malpunkter:
                parameter_info.append("🎯 Målpunkter")
            
            if parameter_info:
                embed.add_field(
                    name="⚔️ Modifierare",
                    value=" • ".join(parameter_info),
                    inline=False
                )
            
            await self.helper.send_response(interaction, embed=embed)
            
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
        skada="Skadevärde för anfallet (1-100)",
        nivå="Attacknivå om inget specifikt område väljs",
        område="Specifikt träffområde (valfritt)",
        ryttare="Anfallet utförs från ryttare",
        fyrfota="Målet är ett fyrbent djur", 
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
        skada: app_commands.Range[int, 1, 100],
        nivå: Optional[str] = "normal",
        område: Optional[str] = None,
        ryttare: bool = False,
        fyrfota: bool = False,
        målpunkter: bool = False
    ):
        """Slash command version av !hugg."""
        start_time = time.time()
        
        await self.process_slash_melee_command(
            interaction, "hugg", nivå, område, skada, ryttare, fyrfota, målpunkter
        )
        
        execution_time = time.time() - start_time
        await self.helper.log_command_usage(interaction, "hugg", {
            "damage": skada,
            "level": nivå,
            "location": område,
            "mounted": ryttare,
            "quadruped": fyrfota,
            "malpunkter": målpunkter
        }, execution_time)

    @app_commands.command(name="stick", description="Utför en stickanfall mot valfritt träffområde")
    @app_commands.describe(
        skada="Skadevärde för anfallet (1-100)",
        nivå="Attacknivå om inget specifikt område väljs",
        område="Specifikt träffområde (valfritt)",
        ryttare="Anfallet utförs från ryttare",
        fyrfota="Målet är ett fyrbent djur",
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
        skada: app_commands.Range[int, 1, 100],
        nivå: Optional[str] = "normal",
        område: Optional[str] = None,
        ryttare: bool = False,
        fyrfota: bool = False,
        målpunkter: bool = False
    ):
        """Slash command version av !stick."""
        start_time = time.time()
        
        await self.process_slash_melee_command(
            interaction, "stick", nivå, område, skada, ryttare, fyrfota, målpunkter
        )
        
        execution_time = time.time() - start_time
        await self.helper.log_command_usage(interaction, "stick", {
            "damage": skada,
            "level": nivå,
            "location": område,
            "mounted": ryttare,
            "quadruped": fyrfota,
            "malpunkter": målpunkter
        }, execution_time)

    @app_commands.command(name="kross", description="Utför en krossanfall mot valfritt träffområde")
    @app_commands.describe(
        skada="Skadevärde för anfallet (1-100)",
        nivå="Attacknivå om inget specifikt område väljs",
        område="Specifikt träffområde (valfritt)",
        ryttare="Anfallet utförs från ryttare",
        fyrfota="Målet är ett fyrbent djur",
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
        skada: app_commands.Range[int, 1, 100],
        nivå: Optional[str] = "normal",
        område: Optional[str] = None,
        ryttare: bool = False,
        fyrfota: bool = False,
        målpunkter: bool = False
    ):
        """Slash command version av !kross."""
        start_time = time.time()
        
        await self.process_slash_melee_command(
            interaction, "kross", nivå, område, skada, ryttare, fyrfota, målpunkter
        )
        
        execution_time = time.time() - start_time
        await self.helper.log_command_usage(interaction, "kross", {
            "damage": skada,
            "level": nivå,
            "location": område,
            "mounted": ryttare,
            "quadruped": fyrfota,
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
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
    from config.feature_flags import is_command_enabled
    
    # Kontrollera om slash combat commands är aktiverade
    if not is_command_enabled("hugg", "combat"):
        print("Slash combat commands är inte aktiverade enligt feature flags")
        return
    
    # Lägg till cog
    combat_cog = CombatSlashCommands(bot, combat_manager, color_handler, embed_factory)
    await bot.add_cog(combat_cog)
    print("Slash combat commands har registrerats (/hugg, /stick, /kross, /fummel).")