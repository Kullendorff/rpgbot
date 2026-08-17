# src/spindel/slash_spider_commands.py
"""
Slash-kommandon för Gigantspindel-stridssystem.

Del av src/spindel/ — se __init__.py. Modulen är avstängd tills vidare
(config/feature_flags.py: slash_spindel_enabled).
"""

import discord
from discord import app_commands
from typing import Optional
import json

from .spider_combat_manager import SpiderCombatManager

spider_managers = {}

def get_spider_manager(guild_id: int) -> SpiderCombatManager:
    """Hämtar eller skapar SpiderCombatManager för en server"""
    if guild_id not in spider_managers:
        spider_managers[guild_id] = SpiderCombatManager(guild_id=guild_id)
    return spider_managers[guild_id]

async def register_slash_spider_commands(bot, color_handler):
    """Registrerar alla spindelkommandon"""
    
    @bot.tree.command(name="spindel", description="Attackera gigantspindeln")
    @app_commands.describe(
        vapentyp="Typ av vapen (hugg, kross eller stick)",
        område="Vilket område träffas (huvud, ben, bakkropp, eller specifikt)",
        skada="Skadevärde från vapnet"
    )
    @app_commands.choices(vapentyp=[
        app_commands.Choice(name="Hugg", value="hugg"),
        app_commands.Choice(name="Kross", value="kross"),
        app_commands.Choice(name="Stick", value="stick")
    ])
    @app_commands.choices(område=[
        app_commands.Choice(name="Huvud (slumpar delområde)", value="huvud"),
        app_commands.Choice(name="Ben (slumpar delområde)", value="ben"),
        app_commands.Choice(name="Bakkropp (slumpar delområde)", value="bakkropp"),
        app_commands.Choice(name="─────────────────", value="separator1"),
        app_commands.Choice(name="Ögon (specifikt)", value="ögon"),
        app_commands.Choice(name="Bettänger (specifikt)", value="chelicerer"),
        app_commands.Choice(name="Huvudpansar (specifikt)", value="carapace"),
        app_commands.Choice(name="Spinnvårtor (specifikt)", value="spinnvårtor"),
        app_commands.Choice(name="Led på ben (specifikt)", value="led"),
    ])
    async def spindel_command(
        interaction: discord.Interaction,
        vapentyp: str,
        område: str,
        skada: int
    ):
        """Huvudkommando för attack mot spindeln"""
        
        if område == "separator1":
            await interaction.response.send_message(
                "❌ Välj ett giltigt område!",
                ephemeral=True
            )
            return
        
        if skada < 0:
            await interaction.response.send_message(
                "❌ Skada kan inte vara negativ!",
                ephemeral=True
            )
            return
        
        manager = get_spider_manager(interaction.guild_id)
        
        huvudområden = ["huvud", "ben", "bakkropp"]
        is_specific = område.lower() not in huvudområden
        
        try:
            result = manager.process_attack(
                weapon_type=vapentyp,
                location=område,
                raw_damage=skada,
                is_specific=is_specific
            )
            
            public_msg = manager.format_public_message(result)

            user_color = color_handler.get_user_color(interaction.user.id)
            embed = discord.Embed(
                title=f"⚔️ {interaction.user.display_name} attackerar spindeln!",
                description=public_msg,
                color=user_color
            )
            
            if "Döende" in result.effects or "GENOM" in result.description.upper():
                embed.set_footer(text="💀 KRITISK TRÄFF!")
            elif any(effect in result.effects for effect in ["Ben avskuret", "Öga förstört", "Kan ej bita"]):
                embed.set_footer(text="⚠️ ALLVARLIG SKADA!")
            
            await interaction.response.send_message(embed=embed)
            
            ai_description = await manager._generate_ai_description(result)
            gm_report = manager.format_gm_report(result, ai_description)
            
            try:
                await interaction.user.send(f"```\n{gm_report}\n```")
            except discord.Forbidden:
                await interaction.followup.send(
                    f"⚠️ Kunde inte skicka GM-rapport via DM. Aktivera DMs från servern.\n```\n{gm_report}\n```",
                    ephemeral=True
                )
        
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Fel vid attack: {str(e)}",
                ephemeral=True
            )

    @bot.tree.command(name="spindel_runda", description="Slutför runda - applicera blödning")
    async def spindel_runda_command(interaction: discord.Interaction):
        """Processerar slutfas av runda (blödning)"""

        manager = get_spider_manager(interaction.guild_id)

        try:
            result = manager.process_round_end()

            # PUBLIKT MEDDELANDE
            lines = []
            lines.append("🩸 **SLUTFAS AV RUNDA**")
            lines.append("")

            if result.bleeding_applied > 0:
                conscious_text = " (HALVERAT - medvetslös)" if not result.is_conscious else ""
                lines.append(f"Blödning applicerad: **{result.bleeding_applied}** poäng{conscious_text}")
                lines.append(f"Blodförlust: {result.blood_loss_before} → **{result.blood_loss_after}** rader")

                if result.new_row_filled:
                    lines.append("")
                    lines.append("⚠️ **NY RAD FYLLD - SLAG KRÄVS!**")

                    # Chockslag
                    if result.chock_roll:
                        dice, total, success = result.chock_roll
                        dice_str = "".join([f"[{d}]" for d in dice])
                        lines.append("")
                        lines.append(f"🎲 **CHOCKSLAG:** Ob{len(dice)}T6 mot CV {manager.chock_value}")
                        lines.append(f"Slår: {dice_str} = **{total}** → {'✅ KLARAR' if success else '❌ MEDVETSLÖS'}")

                    # Dödsslag
                    if result.death_roll:
                        dice, total, success = result.death_roll
                        dice_str = "".join([f"[{d}]" for d in dice])
                        lines.append("")
                        lines.append(f"💀 **DÖDSSLAG:** Ob{len(dice)}T6 mot CV {manager.chock_value}")
                        lines.append(f"Slår: {dice_str} = **{total}** → {'✅ ÖVERLEVER' if success else '☠️ DÖD'}")
            else:
                lines.append("Ingen blödningstakt aktiv - ingen blödning applicerad.")

            public_msg = "\n".join(lines)

            user_color = color_handler.get_user_color(interaction.user.id)
            embed = discord.Embed(
                title="🕷️ Gigantspindel - Slutfas av runda",
                description=public_msg,
                color=user_color
            )

            if result.new_row_filled and result.chock_roll and not result.chock_roll[2]:
                embed.set_footer(text="💤 SPINDEL MEDVETSLÖS!")

            await interaction.response.send_message(embed=embed)

            # GM-RAPPORT
            gm_lines = []
            gm_lines.append("═" * 50)
            gm_lines.append("🩸 GIGANTSPINDEL - BLÖDNINGSRAPPORT")
            gm_lines.append("═" * 50)
            gm_lines.append("")
            gm_lines.append("【 BLÖDNING 】")
            gm_lines.append(f"Blödningstakt: {manager.bleeding_rate} poäng/runda")
            gm_lines.append(f"Medveten: {'JA' if result.is_conscious else 'NEJ (halverad takt)'}")
            gm_lines.append(f"Applicerad blödning: {result.bleeding_applied} poäng")
            gm_lines.append(f"Blodförlust före: {result.blood_loss_before} rader")
            gm_lines.append(f"Blodförlust efter: {result.blood_loss_after} rader")
            gm_lines.append(f"Total blodförlust: {manager.total_blood_loss}/{manager.damage_tolerance*10}")

            if result.new_row_filled:
                gm_lines.append("")
                gm_lines.append("【 KRITISKA SLAG 】")

                if result.chock_roll:
                    dice, total, success = result.chock_roll
                    dice_str = ", ".join([str(d) for d in dice])
                    gm_lines.append(f"Chockslag: Ob{len(dice)}T6 mot CV {manager.chock_value}")
                    gm_lines.append(f"Tärningar: [{dice_str}] = {total}")
                    gm_lines.append(f"Resultat: {'✅ KLARAR' if success else '❌ MEDVETSLÖS'} ({total} {'≤' if success else '>'} {manager.chock_value})")

                if result.death_roll:
                    dice, total, success = result.death_roll
                    dice_str = ", ".join([str(d) for d in dice])
                    gm_lines.append(f"\nDödsslag: Ob{len(dice)}T6 mot CV {manager.chock_value}")
                    gm_lines.append(f"Tärningar: [{dice_str}] = {total}")
                    gm_lines.append(f"Resultat: {'✅ ÖVERLEVER' if success else '☠️ DÖD'} ({total} {'≤' if success else '>'} {manager.chock_value})")

            gm_lines.append("")
            gm_lines.append("═" * 50)

            gm_report = "\n".join(gm_lines)

            try:
                await interaction.user.send(f"```\n{gm_report}\n```")
            except discord.Forbidden:
                await interaction.followup.send(
                    f"⚠️ Kunde inte skicka GM-rapport via DM.\n```\n{gm_report}\n```",
                    ephemeral=True
                )

        except Exception as e:
            await interaction.response.send_message(
                f"❌ Fel vid rundslut: {str(e)}",
                ephemeral=True
            )

    @bot.tree.command(name="spindelstatus", description="Visa spindelns aktuella status (endast GM)")
    async def spindelstatus_command(interaction: discord.Interaction):
        """Visar fullständig status för spindeln"""
        
        manager = get_spider_manager(interaction.guild_id)
        
        lines = []
        lines.append("═" * 50)
        lines.append("🕷️  GIGANTSPINDEL - AKTUELL STATUS")
        lines.append("═" * 50)
        
        lines.append("\n【 TOTAL SKADA 】")
        trauma_rows = manager.get_filled_rows("T")
        pain_rows = manager.get_filled_rows("S")
        blood_loss_rows = manager.get_filled_rows("blood_loss")

        lines.append(f"Trauma (T): {manager.total_trauma}/{manager.damage_tolerance*10} [{trauma_rows} rader]")
        lines.append(f"Smärta (S): {manager.total_pain}/{manager.damage_tolerance*20} [{pain_rows} rader] (tål DUBBELT)")
        lines.append("")
        lines.append("【 BLÖDNING (EON-SYSTEM) 】")
        lines.append(f"Total blödningstakt: {manager.bleeding_rate} poäng/runda {'(HALVERAS - medvetslös)' if not manager.conscious else ''}")
        lines.append(f"Blodförlust (B): {manager.total_blood_loss}/{manager.damage_tolerance*10} [{blood_loss_rows} rader]")
        
        lines.append("\n【 KRITISKA SLAG 】")
        chock_diff = manager.get_chock_difficulty()
        death_diff = manager.get_death_difficulty()
        lines.append(f"Chockslag: Ob{chock_diff}T6 mot CV {manager.chock_value}")
        lines.append(f"Dödsslag: Ob{death_diff}T6 mot CV {manager.chock_value}")
        
        lines.append("\n【 ÖGON 】")
        lines.append(f"{manager.get_eye_status()} ({manager.eyes_destroyed}/8 förstörda)")
        penalty, desc = manager.get_eye_penalty()
        lines.append(f"Effekt: {desc}")
        
        lines.append("\n【 BEN 】")
        lines.append(manager.get_leg_status())
        
        if manager.active_effects:
            lines.append("\n【 AKTIVA EFFEKTER 】")
            for effect in manager.active_effects:
                lines.append(f"• {effect}")
        
        lines.append("\n" + "═" * 50)
        
        status_msg = "\n".join(lines)
        
        await interaction.response.send_message(
            f"```\n{status_msg}\n```",
            ephemeral=True
        )
    
    @bot.tree.command(name="spindelreset", description="Återställ spindelns status (endast GM)")
    async def spindelreset_command(interaction: discord.Interaction):
        """Återställer spindeln för ny strid"""
        
        manager = get_spider_manager(interaction.guild_id)
        manager.reset()
        
        await interaction.response.send_message(
            "✅ Spindeln har återställts för ny strid! (Status-fil raderad)",
            ephemeral=True
        )
    
    @bot.tree.command(name="spindeldump", description="Visa RAW JSON-data för spindeln (backup)")
    async def spindeldump_command(interaction: discord.Interaction):
        """Dumpar all spindeldata som JSON"""
        
        manager = get_spider_manager(interaction.guild_id)
        data = manager.get_save_data()
        
        json_str = json.dumps(data, indent=2, ensure_ascii=False)
        
        if len(json_str) > 1900:
            import io
            file = discord.File(
                io.BytesIO(json_str.encode('utf-8')),
                filename=f"spider_dump_{interaction.guild_id}.json"
            )
            await interaction.response.send_message(
                "📊 Spindeldata (som fil):",
                file=file,
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                f"📊 Spindeldata:\n```json\n{json_str}\n```",
                ephemeral=True
            )
    
    print("Spindelkommandon registrerade (/spindel, /spindel_runda, /spindelstatus, /spindelreset, /spindeldump)")
