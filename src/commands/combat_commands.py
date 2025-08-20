"""
Combat commands for the EON Discord bot.

This module contains all combat-related commands including weapon attacks and fumble tables.
"""

import random
from typing import Optional, Any
import discord
from discord.ext import commands

# Import fumble tables and weapon aliases
from fumble_tables import FUMBLE_TABLES, WEAPON_TYPE_ALIASES


def register_combat_commands(bot: commands.Bot, combat_manager, color_handler, embed_factory) -> None:
    """
    Register all combat commands with the bot.
    
    Args:
        bot (commands.Bot): The Discord bot instance
        combat_manager: The CombatManager instance for processing attacks
        color_handler: The ColorHandler instance for user colors
    """
    
    @bot.command(name='fummel')
    async def fummel_command(ctx: commands.Context, vapentyp: Optional[str] = None) -> None:
        """
        Slår på fummeltabellen för en specifik vapentyp.
        
        Användning: !fummel [vapentyp]
        Vapentyper: obe, nar, avs, sko
        
        Args:
            ctx (commands.Context): Kontexten för kommandot.
            vapentyp (Optional[str]): Den korta benämningen på vapentypen.
        """
        try:
            if vapentyp is None:
                await ctx.send(
                    "Användning: `!fummel [vapentyp]`\n"
                    "Vapentyper:\n"
                    "- `obe` (obevapnat)\n"
                    "- `nar` (närstrid)\n"
                    "- `avs` (avståndsvapen)\n"
                    "- `sko` (sköldar)"
                )
                return

            vapentyp = vapentyp.lower()
            if vapentyp not in WEAPON_TYPE_ALIASES:
                await ctx.send("Ogiltig vapentyp. Använd: obe, nar, avs, sko")
                return

            full_name: str = WEAPON_TYPE_ALIASES[vapentyp]
            result: int = random.randint(1, 20)
            fummel_text: str = FUMBLE_TABLES[full_name][result]
            color: int = color_handler.get_user_color(ctx.author.id)
            embed = embed_factory.error_message(
                ctx.author.id,
                f"💥 Fummel: {full_name.capitalize()}\n\nSlag: {result}\n\n{fummel_text}"
            )
            await ctx.send(embed=embed)

        except Exception as e:
            await ctx.send(f"Ett fel uppstod: {str(e)}")

    async def process_melee_command(ctx: commands.Context, weapon: str, level_or_location: str, damage: int, flags: str) -> None:
        """
        Hanterar gemensam logik för melee-kommandon (t.ex. hugg, stick, kross).
        
        Args:
            ctx (commands.Context): Kontexten för kommandot.
            weapon (str): Vapentyp (t.ex. 'hugg', 'stick', 'kross').
            level_or_location (str): Angiven nivå eller träffområde.
            damage (int): Skadevärde.
            flags (str): Eventuella ytterligare flaggor (exempelvis '--ryttare', '--djur', '--mp').
        """
        try:
            # Kontrollera om Målpunkter (mp) anges i flaggorna
            use_malpunkter = "--mp" in flags.lower()
            
            # Kontrollera om attacken specificerar ett område (inte en nivå)
            location_override = None if level_or_location.lower() in ["låg", "normal", "hög"] else level_or_location.lower()
            
            # Kontrollera om Målpunkter kan användas
            if use_malpunkter and not location_override:
                await ctx.send("⚠️ Målpunkter kan endast användas när du anger ett specifikt träffområde, inte en attacknivå.")
                use_malpunkter = False
            
            result: Any = combat_manager.process_attack(
                weapon_type=weapon,
                attack_level=level_or_location if level_or_location.lower() in ["låg", "normal", "hög"] else None,
                damage_value=damage,
                location_override=location_override,
                is_mounted="--ryttare" in flags.lower(),
                is_quadruped="--djur" in flags.lower(),
                direction=None,
                use_malpunkter=use_malpunkter
            )
            # Formatera träffzone med både huvudområde och specifik kroppsdel
            hit_zone_display = f"{result.hit_location.capitalize()} - {result.sub_location.capitalize()}"
            
            # Beräkna effektresultaten 
            damage_effects = None
            if result.damage_result and result.damage_result.effect_code:
                from damage_tables import parse_effect_code
                damage_effects = parse_effect_code(result.damage_result.effect_code, result.damage_value)
            
            embed = embed_factory.combat_result(
                ctx.author.id,
                ctx.author.display_name,
                weapon.capitalize(),
                # INTE attack_roll - spelaren behöver inte se träffslaget
                weapon_type=result.weapon_type.value,
                damage_value=result.damage_value,
                hit_zone=hit_zone_display,
                # Ta bort damage_type - ger ingen användbar information
                effect_code=result.damage_result.effect_code if result.damage_result else None,
                description=result.damage_result.description if result.damage_result else None,
                location_code=result.location_code,
                special_effects=result.damage_result.effects if result.damage_result else [],
                use_malpunkter=result.use_malpunkter,
                damage_effects=damage_effects
            )
            await ctx.send(embed=embed)
        except ValueError as e:
            await ctx.send(f"Fel: {str(e)}\nAnvändning: !{weapon} [nivå/område] [skada] [flaggor]")

    @bot.command(name='hugg')
    async def hugg_command(ctx: commands.Context, level_or_location: str, damage: int, *, flags: str = "") -> None:
        """
        Utför ett hugg (närstridsattack).
        
        Användning: !hugg [nivå/område] [skada] [flaggor]
        
        Nivå kan vara: låg, normal, hög
        Område kan vara specifika kroppsdelar: huvud, ansikte, bröstkorg, etc.
        
        Flaggor:
          --mp        - Använd Målpunkter-tekniken (kräver specifikt träffområde)
          --ryttare   - Attacken utförs från en ryttare
          --djur      - Målet är ett fyrbent djur
        
        Exempel:
          !hugg normal 12
          !hugg ansikte 15 --mp
          !hugg hög 10 --ryttare
        """
        await process_melee_command(ctx, "hugg", level_or_location, damage, flags)

    @bot.command(name='stick')
    async def stick_command(ctx: commands.Context, level_or_location: str, damage: int, *, flags: str = "") -> None:
        """
        Utför ett stick (smalare attack).
        
        Användning: !stick [nivå/område] [skada] [flaggor]
        
        Nivå kan vara: låg, normal, hög
        Område kan vara specifika kroppsdelar: huvud, ansikte, bröstkorg, etc.
        
        Flaggor:
          --mp        - Använd Målpunkter-tekniken (kräver specifikt träffområde)
          --ryttare   - Attacken utförs från en ryttare
          --djur      - Målet är ett fyrbent djur
        
        Exempel:
          !stick normal 12
          !stick hals 15 --mp
          !stick hög 10 --ryttare
        """
        await process_melee_command(ctx, "stick", level_or_location, damage, flags)

    @bot.command(name='kross')
    async def kross_command(ctx: commands.Context, level_or_location: str, damage: int, *, flags: str = "") -> None:
        """
        Utför en krossattack.
        
        Användning: !kross [nivå/område] [skada] [flaggor]
        
        Nivå kan vara: låg, normal, hög
        Område kan vara specifika kroppsdelar: huvud, ansikte, bröstkorg, etc.
        
        Flaggor:
          --mp        - Använd Målpunkter-tekniken (kräver specifikt träffområde)
          --ryttare   - Attacken utförs från en ryttare
          --djur      - Målet är ett fyrbent djur
        
        Exempel:
          !kross normal 12
          !kross huvud 15 --mp
          !kross låg 10 --ryttare
        """
        await process_melee_command(ctx, "kross", level_or_location, damage, flags)