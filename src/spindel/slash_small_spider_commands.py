# src/spindel/slash_small_spider_commands.py
"""
Slash-kommandon för Små Spindlar.

Del av src/spindel/ — se __init__.py. Modulen är avstängd tills vidare
(config/feature_flags.py: slash_spindel_enabled).
"""

import discord
from discord import app_commands
from typing import Optional

from .small_spider_manager import SmallSpiderManager, SmallSpider

small_spider_managers = {}

def get_small_spider_manager(guild_id: int) -> SmallSpiderManager:
    """Hämtar eller skapar SmallSpiderManager för en server"""
    if guild_id not in small_spider_managers:
        small_spider_managers[guild_id] = SmallSpiderManager(guild_id=guild_id)
    return small_spider_managers[guild_id]

async def register_slash_small_spider_commands(bot, color_handler):
    """Registrerar alla småspindelkommandon"""

    # Autocomplete-funktion för spindlarnas namn
    async def spider_name_autocomplete(
        interaction: discord.Interaction,
        current: str
    ) -> list[app_commands.Choice[str]]:
        """Returnerar levande spindlars namn för autocomplete"""
        manager = get_small_spider_manager(interaction.guild_id)
        alive_spiders = manager.get_alive_spiders()

        # Filtrera namn baserat på vad användaren skrivit
        choices = []
        for spider in alive_spiders:
            if current.lower() in spider.name.lower():
                # Visa status i autocomplete
                trauma_rows = spider.get_filled_rows("T")
                pain_rows = spider.get_filled_rows("S")
                if trauma_rows > 0 or pain_rows > 0:
                    status = "Skadad"
                else:
                    status = "Frisk"
                choices.append(app_commands.Choice(
                    name=f"{spider.name} ({status})",
                    value=spider.name
                ))

        # Discord begränsar till 25 alternativ
        return choices[:25]

    @bot.tree.command(name="spawna_småspindlar", description="Spawna små spindlar (GM)")
    @app_commands.describe(antal="Antal spindlar att spawna")
    async def spawn_small_spiders(
        interaction: discord.Interaction,
        antal: int
    ):
        """Spawnar nya små spindlar"""
        
        if antal < 1:
            await interaction.response.send_message(
                "⚠️ Måste spawna minst 1 spindel!",
                ephemeral=True
            )
            return
        
        if antal > 20:
            await interaction.response.send_message(
                "⚠️ Max 20 spindlar åt gången!",
                ephemeral=True
            )
            return
        
        manager = get_small_spider_manager(interaction.guild_id)
        spawned = manager.spawn(antal)  # Returnerar lista av (ID, namn)

        if len(spawned) == 1:
            spider_id, name = spawned[0]
            msg = f"🕷️ **{name} spawnar!**"
        else:
            names = [name for _, name in spawned]
            if len(names) <= 5:
                name_list = ", ".join(names)
                msg = f"🕷️ **{len(spawned)} små spindlar spawnar!**\n{name_list}"
            else:
                msg = f"🕷️ **{len(spawned)} små spindlar spawnar!**\n{', '.join(names[:3])}, ... och {len(names)-3} till"

        await interaction.response.send_message(msg)
    
    @bot.tree.command(name="attack_småspindel", description="Attackera en liten spindel")
    @app_commands.describe(
        spindel="Vilken spindel (börja skriva för att söka)",
        vapentyp="Typ av vapen (hugg, kross eller stick)",
        område="Vilket område träffas (slumpa, huvud eller kropp)",
        skada="Skadavärde från vapnet"
    )
    @app_commands.autocomplete(spindel=spider_name_autocomplete)
    @app_commands.choices(vapentyp=[
        app_commands.Choice(name="Hugg", value="hugg"),
        app_commands.Choice(name="Kross", value="kross"),
        app_commands.Choice(name="Stick", value="stick")
    ])
    @app_commands.choices(område=[
        app_commands.Choice(name="Slumpa (T10)", value="slumpa"),
        app_commands.Choice(name="Huvud", value="huvud"),
        app_commands.Choice(name="Kropp", value="kropp")
    ])
    async def attack_small_spider(
        interaction: discord.Interaction,
        spindel: str,  # Nu tar vi emot namn istället för ID
        vapentyp: str,
        område: str,
        skada: int
    ):
        """Attackerar en liten spindel"""

        if skada < 0:
            await interaction.response.send_message(
                "⚠️ Skada kan inte vara negativ!",
                ephemeral=True
            )
            return

        manager = get_small_spider_manager(interaction.guild_id)
        spider = manager.get_spider_by_name(spindel)

        if not spider:
            await interaction.response.send_message(
                f"⚠️ Spindeln '{spindel}' finns inte! Använd `/småspindelstatus` för att se aktiva spindlar.",
                ephemeral=True
            )
            return

        if not spider.alive:
            await interaction.response.send_message(
                f"⚠️ {spider.name} är redan DÖD! Välj en annan.",
                ephemeral=True
            )
            return
        
        try:
            result = manager.process_attack(
                spider_id=spider.spider_id,  # Använd ID intern
                weapon_type=vapentyp,
                location=område,
                raw_damage=skada
            )
            
            # PUBLIKT MEDDELANDE (alla ser)
            lines = []
            lines.append(f"🎯 **{interaction.user.display_name} attackerar {spider.name}!**")
            
            if result.location_roll:
                lines.append(f"Slumpar träffzon (T10): **{result.location_roll}** → **{result.hit_location.upper()}**")
            else:
                lines.append(f"Träffar **{result.hit_location.upper()}**!")
            
            lines.append(f"Skada: {result.raw_damage} - {result.armor} rustning = **{result.effective_damage} effektiv skada**")
            lines.append(f"*{result.description}*")
            lines.append(f"**T+{result.trauma}, S+{result.pain}**")
            lines.append("")
            lines.append(f"{spider.name}: T:{spider.total_trauma}/{spider.damage_tolerance*5}, S:{spider.total_pain}/{spider.damage_tolerance*5}")
            
            # Chockslag - bara resultat, inga tärningar
            if result.chock_roll:
                dice, total, success = result.chock_roll
                if not success:
                    lines.append("")
                    lines.append(f"💤 **Chockslag misslyckades - MEDVETSLÖS!**")

            # Dödsslag - bara resultat, inga tärningar
            if result.death_roll:
                dice, total, success = result.death_roll
                if not success:
                    lines.append("")
                    lines.append(f"☠️ **Dödsslag misslyckades - SPINDEL DÖD!**")
            
            # Slutstatus
            lines.append("")
            if result.is_dead:
                lines.append("☠️ **{} DÖD!**".format(spider.name.upper()))
            elif result.is_unconscious:
                lines.append("💤 **{} MEDVETSLÖS!**".format(spider.name))
            else:
                lines.append("⚠️ **{} lever men är skadad!**".format(spider.name))
            
            public_msg = "\n".join(lines)

            user_color = color_handler.get_user_color(interaction.user.id)
            embed = discord.Embed(
                description=public_msg,
                color=user_color
            )
            
            await interaction.response.send_message(embed=embed)

            # GM-RAPPORT (privat DM)
            gm_lines = []
            gm_lines.append("═" * 50)
            gm_lines.append(f"🕷️ {spider.name.upper()} - SKADERAPPORT")
            gm_lines.append("═" * 50)
            gm_lines.append("")
            gm_lines.append("【 SENASTE TRÄFF 】")
            gm_lines.append(f"Attackerare: {interaction.user.display_name}")
            if result.location_roll:
                gm_lines.append(f"Slumpning (T10): {result.location_roll} → {result.hit_location}")
            gm_lines.append(f"Område: {result.hit_location.upper()}")
            gm_lines.append(f"Vapentyp: {result.weapon_type.upper()}")
            gm_lines.append(f"Rå skada: {result.raw_damage}")
            gm_lines.append(f"Rustning: {result.armor}")
            gm_lines.append(f"Effektiv skada: {result.effective_damage}")
            gm_lines.append("")
            gm_lines.append(f"Skadetyp: {result.description}")
            gm_lines.append(f"TS: T+{result.trauma}, S+{result.pain}")
            if result.effects:
                gm_lines.append(f"Effekter: {', '.join(result.effects)}")

            gm_lines.append("")
            gm_lines.append("─" * 50)
            gm_lines.append("【 TOTAL SKADA 】")
            trauma_rows = spider.get_filled_rows("T")
            pain_rows = spider.get_filled_rows("S")

            gm_lines.append(f"Trauma (T): {spider.total_trauma}/{spider.damage_tolerance*5} [{trauma_rows} fyllda rader]")
            gm_lines.append(f"Smärta (S): {spider.total_pain}/{spider.damage_tolerance*5} [{pain_rows} fyllda rader]")
            
            if result.chock_roll or result.death_roll:
                gm_lines.append("")
                gm_lines.append("─" * 50)
                gm_lines.append("【 KRITISKA SLAG 】")
            
            if result.chock_roll:
                dice, total, success = result.chock_roll
                dice_str = ", ".join([str(d) for d in dice])
                gm_lines.append(f"Chockslag: Ob{len(dice)}T6 mot CV {spider.chock_value}")
                gm_lines.append(f"Tärningar: [{dice_str}] = {total}")
                gm_lines.append(f"Resultat: {'✅ KLARAR' if success else '❌ MEDVETSLÖS'} ({total} {'≤' if success else '>'} {spider.chock_value})")
            
            if result.death_roll:
                dice, total, success = result.death_roll
                dice_str = ", ".join([str(d) for d in dice])
                gm_lines.append(f"\nDödsslag: Ob{len(dice)}T6 mot CV {spider.chock_value}")
                gm_lines.append(f"Tärningar: [{dice_str}] = {total}")
                gm_lines.append(f"Resultat: {'✅ ÖVERLEVER' if success else '☠️ DÖD'} ({total} {'≤' if success else '>'} {spider.chock_value})")
            
            gm_lines.append("")
            gm_lines.append("─" * 50)
            if result.is_dead:
                gm_lines.append("Status: ☠️ DÖD")
            elif result.is_unconscious:
                gm_lines.append("Status: 💤 MEDVETSLÖS")
            else:
                gm_lines.append("Status: LEVANDE, SKADAD")
            
            if spider.active_effects:
                gm_lines.append("")
                gm_lines.append("【 AKTIVA EFFEKTER 】")
                for effect in spider.active_effects:
                    gm_lines.append(f"• {effect}")
            
            gm_lines.append("")
            gm_lines.append("═" * 50)
            
            gm_report = "\n".join(gm_lines)
            
            try:
                await interaction.user.send(f"```\n{gm_report}\n```")
            except discord.Forbidden:
                # Om DM inte funkar, skicka ephemeral
                await interaction.followup.send(
                    f"⚠️ Kunde inte skicka GM-rapport via DM.\n```\n{gm_report}\n```",
                    ephemeral=True
                )
        
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Fel vid attack: {str(e)}",
                ephemeral=True
            )
    
    @bot.tree.command(name="småspindelstatus", description="Visa alla små spindlars status")
    async def small_spider_status(interaction: discord.Interaction):
        """Visar status för alla små spindlar"""
        
        manager = get_small_spider_manager(interaction.guild_id)
        
        if not manager.spiders:
            await interaction.response.send_message(
                "⚠️ Inga spindlar har spawnats! Använd `/spawna_småspindlar` först.",
                ephemeral=True
            )
            return
        
        lines = []
        lines.append("═" * 50)
        lines.append("🕷️ SMÅ SPINDLAR - STATUS")
        lines.append("═" * 50)
        lines.append("")
        
        alive_count = 0
        dead_count = 0
        
        for spider in sorted(manager.spiders.values(), key=lambda s: s.name):
            if spider.alive:
                alive_count += 1
                trauma_rows = spider.get_filled_rows("T")
                pain_rows = spider.get_filled_rows("S")

                status = "✅ FRISK"
                if trauma_rows > 0 or pain_rows > 0:
                    status = "⚠️ SKADAD"

                lines.append(f"{spider.name}: {status}")
                lines.append(f"  T:{spider.total_trauma}/{spider.damage_tolerance*5} [{trauma_rows}r], S:{spider.total_pain}/{spider.damage_tolerance*5} [{pain_rows}r]")

                if spider.active_effects:
                    lines.append(f"  Effekter: {', '.join(spider.active_effects)}")

                lines.append("")
            else:
                dead_count += 1
                lines.append(f"{spider.name}: ☠️ DÖD")
                lines.append("")
        
        lines.append("─" * 50)
        lines.append(f"Levande: {alive_count} | Döda: {dead_count} | Totalt: {len(manager.spiders)}")
        lines.append("═" * 50)
        
        status_msg = "\n".join(lines)
        
        await interaction.response.send_message(
            f"```\n{status_msg}\n```",
            ephemeral=True
        )
    
    @bot.tree.command(name="reset_småspindlar", description="Återställ alla små spindlar (GM)")
    async def reset_small_spiders(interaction: discord.Interaction):
        """Återställer alla små spindlar"""
        
        manager = get_small_spider_manager(interaction.guild_id)
        manager.reset()
        
        await interaction.response.send_message(
            "✅ Alla små spindlar har återställts!",
            ephemeral=True
        )
    
    print("Småspindelkommandon registrerade (/spawna_småspindlar, /attack_småspindel, /småspindelstatus, /reset_småspindlar)")
