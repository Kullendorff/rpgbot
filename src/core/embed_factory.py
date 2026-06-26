"""
Centraliserad embed factory för konsekvent visuell profil.
Alla Discord embeds i boten ska skapas genom denna factory.
"""

import discord
from typing import List, Dict, Any, Optional, Union
from datetime import datetime, timezone

class EmbedFactory:
    """Factory-klass för att skapa standardiserade Discord embeds."""
    
    # Standardfärger
    SUCCESS_COLOR = 0x2ECC71    # Grön
    ERROR_COLOR = 0xE74C3C      # Röd  
    WARNING_COLOR = 0xF39C12    # Orange
    INFO_COLOR = 0x3498DB       # Blå
    
    # Standard emojis
    DICE_EMOJI = "🎲"
    SUCCESS_EMOJI = "✅"
    FAILURE_EMOJI = "❌"
    COMBAT_EMOJI = "⚔️"
    STATS_EMOJI = "📊"
    KNOWLEDGE_EMOJI = "📚"
    ADMIN_EMOJI = "🔧"
    
    def __init__(self, color_handler):
        """Initialisera med color_handler för användarfärger."""
        self.color_handler = color_handler
    
    def _get_base_embed(self, user_id: int, title: str, description: str = None) -> discord.Embed:
        """Skapa bas-embed med användarfärg och standardformatering."""
        color = self.color_handler.get_user_color(user_id)
        embed = discord.Embed(title=title, description=description, color=color)
        embed.timestamp = datetime.now(timezone.utc)
        return embed
    
    def dice_result(self, user_id: int, user_name: str, command: str, 
                   dice_expr: str, results: List[int], total: int = None,
                   target: int = None, success: bool = None) -> discord.Embed:
        """Standard mall för tärningsresultat."""
        title = f"{self.DICE_EMOJI} Tärningskast"
        
        # Bygg description
        desc_parts = [f"**{user_name}** rullade `{dice_expr}`"]
        if command != "roll":
            desc_parts.append(f"*(kommando: {command})*")
            
        embed = self._get_base_embed(user_id, title, "\n".join(desc_parts))
        
        # Resultat field
        result_text = f"**Tärningar:** {results}"
        if total is not None:
            result_text += f"\n**Summa:** {total}"
        if target is not None:
            result_text += f"\n**Målvärde:** {target}"
            
        embed.add_field(name="Resultat", value=result_text, inline=False)
        
        # Success/failure indikation
        if success is not None:
            status_emoji = self.SUCCESS_EMOJI if success else self.FAILURE_EMOJI
            status_text = "Lyckat!" if success else "Misslyckat"
            embed.add_field(name="Utfall", value=f"{status_emoji} {status_text}", inline=True)
            
        return embed
    
    def combat_result(self, user_id: int, user_name: str, weapon: str,
                     attack_roll: int = None, damage_rolls: List[int] = None, 
                     hit_zone: str = None, special_effects: List[str] = None,
                     weapon_type: str = None, damage_value: int = None,
                     damage_type: str = None, effect_code: str = None,
                     description: str = None, location_code: str = None,
                     use_malpunkter: bool = False, damage_effects: Dict[str, int] = None) -> discord.Embed:
        """Standard mall för stridsresultat med full EON combat support."""
        title = f"{self.COMBAT_EMOJI} Attackresultat"
        embed_description = f"**{user_name}** attackerar med {weapon}"
        
        embed = self._get_base_embed(user_id, title, embed_description)
        
        # Grundläggande attack info
        if weapon_type:
            embed.add_field(name="Vapentyp", value=weapon_type, inline=True)
        
        if damage_value is not None:
            embed.add_field(name="Skadevärde", value=str(damage_value), inline=True)
            
        # Träffområde med kod - detta är vad spelaren behöver se
        if hit_zone:
            if location_code:
                zone_text = f"Kod {location_code} [{hit_zone}]"
            else:
                zone_text = hit_zone
            embed.add_field(name="Träffområde", value=zone_text, inline=True)
        
        # Ta bort Skadetyp - ger spelarna ingen användbar information
        
        # Effekter och beskrivning
        if description:
            embed.add_field(name="Beskrivning", value=description, inline=False)
            
        # Effektinformation med både kod och beräknade värden i svenska termer
        if effect_code and damage_effects:
            # Konvertera till svenska termer
            swedish_effects = []
            for key, value in damage_effects.items():
                if key == 'T':
                    swedish_effects.append(f"Trauma {value}")
                elif key == 'S':
                    swedish_effects.append(f"Smärta {value}")
                elif key == 'B':
                    swedish_effects.append(f"Blödning {value}")
                else:
                    swedish_effects.append(f"{key} {value}")
            
            effects_display = f"{effect_code} => {', '.join(swedish_effects)}"
            embed.add_field(name="Effekter", value=effects_display, inline=False)
        elif effect_code:
            embed.add_field(name="Effektkod", value=f"`{effect_code}`", inline=True)
            
        # Special effects
        if special_effects:
            effects_text = "\n".join(f"• {effect}" for effect in special_effects)
            embed.add_field(name="Extra effekter", value=effects_text, inline=False)
            
        # Målpunkter
        if use_malpunkter:
            embed.add_field(name="⚡ Special", value="Målpunkter-tekniken användes", inline=False)
            
        return embed
    
    def stats_overview(self, user_id: int, user_name: str, stats_data: Dict[str, Any],
                      session_id: str = None) -> discord.Embed:
        """Standard mall för statistiköversikt."""
        title = f"{self.STATS_EMOJI} Statistik"
        description = f"Översikt för **{user_name}**"
        if session_id:
            description += f"\n*Session: {session_id}*"
            
        embed = self._get_base_embed(user_id, title, description)
        
        # Grundläggande stats
        basic_stats = [
            f"**Totala kast:** {stats_data.get('total_rolls', 0)}",
            f"**Lyckade kast:** {stats_data.get('successes', 0)}",
            f"**Misslyckade kast:** {stats_data.get('failures', 0)}"
        ]
        
        if stats_data.get('success_rate') is not None:
            basic_stats.append(f"**Träffsäkerhet:** {stats_data['success_rate']:.1f}%")
            
        embed.add_field(name="Grundstatistik", value="\n".join(basic_stats), inline=False)
        
        return embed
    
    def knowledge_result(self, user_id: int, user_name: str, question: str,
                        answer: str, sources: List[str] = None) -> discord.Embed:
        """Standard mall för kunskapsresultat."""
        title = f"{self.KNOWLEDGE_EMOJI} Kunskapssökning"
        description = f"**Fråga från {user_name}:**\n*{question}*"
        
        embed = self._get_base_embed(user_id, title, description)
        
        # Svar (med längdbegränsning)
        answer_text = answer[:1000] + "..." if len(answer) > 1000 else answer
        embed.add_field(name="Svar", value=answer_text, inline=False)
        
        # Källor om tillgängliga
        if sources:
            sources_text = "\n".join(f"• {source}" for source in sources[:3])
            if len(sources) > 3:
                sources_text += f"\n*...och {len(sources) - 3} till*"
            embed.add_field(name="Källor", value=sources_text, inline=False)
            
        return embed
    
    def error_message(self, user_id: int, error_msg: str, 
                     suggestion: str = None) -> discord.Embed:
        """Standard mall för felmeddelanden."""
        embed = discord.Embed(
            title="❌ Fel",
            description=error_msg,
            color=self.ERROR_COLOR
        )
        embed.timestamp = datetime.now(timezone.utc)
        
        if suggestion:
            embed.add_field(name="Förslag", value=suggestion, inline=False)
            
        return embed
    
    def success_message(self, user_id: int, message: str) -> discord.Embed:
        """Standard mall för framgångsmeddelanden."""
        embed = discord.Embed(
            title="✅ Klart",
            description=message,
            color=self.SUCCESS_COLOR
        )
        embed.timestamp = datetime.now(timezone.utc)
        return embed
    
    def admin_message(self, user_id: int, title: str, content: str) -> discord.Embed:
        """Standard mall för admin-meddelanden."""
        embed_title = f"{self.ADMIN_EMOJI} {title}"
        embed = self._get_base_embed(user_id, embed_title, content)
        return embed

    # Delta Green Methods
    def dg_roll_result(self, user_id: int, user_name: str, roll: int,
                      tens: int, ones: int, target: int, result_type: str,
                      skill_name: str = None, modifier: int = 0) -> discord.Embed:
        """Standard mall för Delta Green d100-kast."""
        title = "🔟 DELTA GREEN - Skill Check"

        # Format tens/ones display
        tens_display = str(tens) if tens != 0 else "0"
        ones_display = str(ones) if ones != 0 else "0"

        # Build description
        desc_lines = [
            "━━━━━━━━━━━━━━━━━━━━━━━━━",
            f"",
            f"🔟  [{tens_display}] [{ones_display}]  →  **{roll:02d}**",
            f""
        ]

        # Target info
        target_line = f"Target: **{target}%**"
        if modifier != 0:
            sign = "+" if modifier > 0 else ""
            target_line += f" ({sign}{modifier})"
        desc_lines.append(target_line)

        # Result
        if result_type == "critical_success":
            result_emoji = "✨"
            result_text = "CRITICAL SUCCESS"
            result_color = 0xF1C40F  # Gold
        elif result_type == "success":
            result_emoji = "✅"
            result_text = "SUCCESS"
            result_color = 0x2ECC71  # Green
        elif result_type == "failure":
            result_emoji = "❌"
            result_text = "FAILURE"
            result_color = 0xE74C3C  # Red
        else:  # fumble
            result_emoji = "💀"
            result_text = "FUMBLE"
            result_color = 0x8E44AD  # Purple

        desc_lines.append(f"Result: {result_emoji} **{result_text}**")

        # Add special notes for matched digits
        if tens == ones:
            if result_type == "critical_success":
                desc_lines.append("")
                desc_lines.append("_Matched doubles on success!_")
            elif result_type == "fumble":
                desc_lines.append("")
                desc_lines.append("_Matched doubles on failure!_")

        embed = discord.Embed(
            title=title,
            description="\n".join(desc_lines),
            color=result_color
        )
        embed.timestamp = datetime.now(timezone.utc)

        # Add skill name if provided
        if skill_name:
            embed.set_footer(text=f"Skill: {skill_name} | {user_name}")
        else:
            embed.set_footer(text=user_name)

        return embed

    def dg_lethality_result(self, user_id: int, user_name: str,
                           roll: int, tens: int, ones: int, rating: int,
                           is_lethal: bool, damage: Optional[int] = None) -> discord.Embed:
        """Standard mall för Delta Green lethality-kast."""
        title = "💀 DELTA GREEN - Lethality Roll"

        # Format tens/ones display
        tens_display = str(tens) if tens != 0 else "0"
        ones_display = str(ones) if ones != 0 else "0"

        desc_lines = [
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            f"",
            f"🎲  [{tens_display}] [{ones_display}]  →  **{roll:02d}**",
            f"",
            f"Lethality: **{rating}%**"
        ]

        if is_lethal:
            desc_lines.append(f"Result: ☠️ **LETHAL - Instant Kill**")
            desc_lines.append("")
            desc_lines.append("_Target reduced to 0 HP._")
            result_color = 0x8E44AD  # Purple
        else:
            desc_lines.append(f"Result: Non-Lethal")
            desc_lines.append("")
            tens_val = 10 if tens == 0 else tens
            ones_val = 10 if ones == 0 else ones
            desc_lines.append(f"💥 **Damage:** {tens_val} + {ones_val} = **{damage} HP**")
            result_color = 0xE74C3C  # Red

        embed = discord.Embed(
            title=title,
            description="\n".join(desc_lines),
            color=result_color
        )
        embed.timestamp = datetime.now(timezone.utc)
        embed.set_footer(text=user_name)

        return embed

    def dg_san_result(self, user_id: int, user_name: str,
                     roll: int, tens: int, ones: int, san_before: int,
                     san_loss: int, san_after: int, result_type: str,
                     temporary_insanity: bool = False) -> discord.Embed:
        """Standard mall för Delta Green SAN-check."""
        title = "🧠 DELTA GREEN - Sanity Check"

        # Format tens/ones display
        tens_display = str(tens) if tens != 0 else "0"
        ones_display = str(ones) if ones != 0 else "0"

        desc_lines = [
            "━━━━━━━━━━━━━━━━━━━━━━━━━",
            f"",
            f"🎲  [{tens_display}] [{ones_display}]  →  **{roll:02d}**",
            f"",
            f"Current SAN: **{san_before}%**",
            f"Target: **{san_before}%**"
        ]

        # Result
        if result_type in ("critical_success", "success"):
            result_emoji = "✅"
            result_text = "SUCCESS" if result_type == "success" else "CRITICAL SUCCESS"
        else:
            result_emoji = "❌"
            result_text = "FAILURE" if result_type == "failure" else "FUMBLE"

        desc_lines.append(f"Result: {result_emoji} **{result_text}**")
        desc_lines.append("")

        # SAN loss
        if san_loss > 0:
            desc_lines.append(f"**SAN Loss:** {san_loss}")
            desc_lines.append(f"**SAN:** {san_before} → {san_after}")

            if temporary_insanity:
                desc_lines.append("")
                desc_lines.append("⚠️ **TEMPORARY INSANITY TRIGGERED**")
                desc_lines.append("_Lost 5+ SAN in one check!_")
        else:
            desc_lines.append("No SAN loss")

        # Color based on severity
        if temporary_insanity:
            result_color = 0x8E44AD  # Purple
        elif san_loss >= 3:
            result_color = 0xE74C3C  # Red
        elif san_loss > 0:
            result_color = 0xF39C12  # Orange
        else:
            result_color = 0x2ECC71  # Green

        embed = discord.Embed(
            title=title,
            description="\n".join(desc_lines),
            color=result_color
        )
        embed.timestamp = datetime.now(timezone.utc)
        embed.set_footer(text=user_name)

        return embed

    def dg_project_result(
        self,
        user_id: int,
        user_name: str,
        callsign: str,
        bond_name: str,
        d4_roll: int,
        wp_before: int,
        wp_after: int,
        san_loss_original: int,
        san_loss_reduced: int,
        bond_before: int,
        bond_after: int,
        projection_succeeded: bool,
        unconscious: bool,
        bond_broken: bool,
        just_broke: bool,
        ti_originally_triggered: bool,
        ti_avoided: bool,
    ) -> discord.Embed:
        """
        Delta Green "Projecting Onto a Bond" resultat-embed.

        Renderar hela utfallet: D4-kostnad → WP → (vid framgång) reducerad
        SAN-förlust + Bond-skada. Bruten Bond och undviken TI får egna
        markeringar.
        """
        title = "💔 DELTA GREEN - Projecting Onto a Bond"

        lines = [
            "━━━━━━━━━━━━━━━━━━━━━━━━━",
            "",
            f"**Agent:** {callsign}",
            f"**Bond:** {bond_name}",
            "",
            f"🎲  1D4 → **{d4_roll}**  _(WP-kostnad)_",
            f"**WP:** {wp_before} → {wp_after}",
            "",
        ]

        if projection_succeeded:
            lines.append("✅ **Projection lyckades**")
            lines.append("")
            if san_loss_reduced < san_loss_original:
                lines.append(
                    f"**SAN-förlust:** {san_loss_original} → **{san_loss_reduced}** "
                    f"_(reducerad med {san_loss_original - san_loss_reduced})_"
                )
            else:
                lines.append(
                    f"**SAN-förlust:** {san_loss_original} "
                    f"_(ingen reducering — D4 gav noll nytta)_"
                )

            lines.append(f"**Bond:** {bond_before} → {bond_after}")

            if just_broke:
                lines.append("")
                lines.append(f"💔 **Bond bruten:** _{bond_name}_ är permanent förlorad.")
            elif bond_broken:
                lines.append("")
                lines.append(f"_({bond_name} var redan bruten.)_")

            if ti_avoided:
                lines.append("")
                lines.append("🛡️ **Temporary Insanity undveks!**")
                lines.append("_SAN-förlusten drogs ned under 5._")
            elif ti_originally_triggered:
                lines.append("")
                lines.append("⚠️ **Temporary Insanity utlöstes ändå**")
                lines.append(f"_Kvarvarande förlust är {san_loss_reduced} (≥ 5)._")
        else:
            lines.append("❌ **Projection misslyckades**")
            lines.append(
                "_Agenten föll medvetslös vid 0 WP. Ingen SAN-reducering, ingen Bond-skada._"
            )

        if unconscious:
            lines.append("")
            lines.append("😵 **Agenten är nu medvetslös.**")

        # Färgval: bruten bond eller medvetslös = lila, misslyckad = röd,
        # TI undveks = grön, annars orange (mitigerat men kostsamt)
        if just_broke or unconscious:
            color = 0x8E44AD
        elif not projection_succeeded:
            color = 0xE74C3C
        elif ti_avoided:
            color = 0x2ECC71
        else:
            color = 0xF39C12

        embed = discord.Embed(
            title=title,
            description="\n".join(lines),
            color=color,
        )
        embed.timestamp = datetime.now(timezone.utc)
        embed.set_footer(text=user_name)
        return embed

    # ------------------------------------------------------------------
    # Dragonbane (modul av Jonas, github.com/jonsal/dragonbane)
    # ------------------------------------------------------------------
    DRAGONBANE_CREDIT = "Dragonbane-modul av Jonas"

    def _dragonbane_footer(self, embed: discord.Embed, user_name: str) -> None:
        """Sätt en gemensam sidfot som krediterar Jonas på varje Dragonbane-embed."""
        embed.timestamp = datetime.now(timezone.utc)
        embed.set_footer(text=f"{user_name} • {self.DRAGONBANE_CREDIT}")

    def dragonbane_skill_result(
        self, user_id: int, user_name: str, skill: int, modifier: int,
        target: int, mode: str, rolls: list, chosen_roll: int,
        success: bool, critical: str = None, pushed: bool = False,
        condition: str = None, attribute: str = None,
    ) -> discord.Embed:
        """Mall för Dragonbane färdighetsslag (och pressade slag)."""
        prefix = "🐉 Dragonbane: Pressat slag" if pushed else "🐉 Dragonbane: Färdighetsslag"

        if critical == "dragon":
            color = 0xF1C40F        # Guld
            result_emoji, result_text = "✨", "DRAKSLAG: Kritisk framgång!"
        elif critical == "demon":
            color = 0x8E44AD        # Lila
            result_emoji, result_text = "💀", "DEMONSLAG: Kritiskt misslyckande!"
        elif success:
            color = 0x2ECC71        # Grön
            result_emoji, result_text = "✅", "LYCKAT"
        else:
            color = 0xE74C3C        # Röd
            result_emoji, result_text = "❌", "MISSLYCKAT"

        rolls_text = ", ".join(str(r) for r in rolls)
        desc_lines = [
            f"**FV:** {skill}   **Mod:** {modifier:+d}   **Målvärde:** {target}",
            f"**Läge:** {mode}",
            f"**Slag:** {rolls_text}",
            f"**Valt slag:** {chosen_roll}",
            f"**Resultat:** {result_emoji} **{result_text}**",
        ]

        if pushed and condition:
            if attribute:
                desc_lines.append(f"**Tillstånd:** {condition} ({attribute})")
            else:
                desc_lines.append(
                    f"**Tillstånd:** {condition} _(SL bestämmer det slutliga tillståndet)_"
                )

        embed = discord.Embed(title=prefix, description="\n".join(desc_lines), color=color)
        self._dragonbane_footer(embed, user_name)
        return embed

    def dragonbane_expression_result(
        self, user_id: int, user_name: str, expression: str,
        breakdown_lines: list, total: int,
    ) -> discord.Embed:
        """Mall för fritt Dragonbane-tärningsuttryck (dod_slag)."""
        embed = self._get_base_embed(user_id, "🎲 Dragonbane: Tärningsslag",
                                     f"**{user_name}** slår `{expression}`")
        details = "\n".join(breakdown_lines) if breakdown_lines else "Inga termer"
        embed.add_field(name="Uppdelning", value=details, inline=False)
        embed.add_field(name="Totalt", value=f"**{total}**", inline=False)
        self._dragonbane_footer(embed, user_name)
        return embed

    def dragonbane_damage_result(
        self, user_id: int, user_name: str, expression: str,
        breakdown_lines: list, total: int,
    ) -> discord.Embed:
        """Mall för Dragonbane skadeslag (dod_skada)."""
        embed = discord.Embed(
            title="⚔️ Dragonbane: Skadeslag",
            description=f"**{user_name}** slår skada `{expression}`",
            color=0xC0392B,
        )
        details = "\n".join(breakdown_lines) if breakdown_lines else "Inga termer"
        embed.add_field(name="Uppdelning", value=details, inline=False)
        embed.add_field(name="Skada", value=f"**{total}**", inline=False)
        self._dragonbane_footer(embed, user_name)
        return embed

    def dragonbane_initiative_result(
        self, user_id: int, user_name: str, entries: list,
    ) -> discord.Embed:
        """Mall för Dragonbane-initiativ (dod_init). entries: lista med .name och .card."""
        lines = [
            f"{i + 1}. **{entry.name}**: kort {entry.card}"
            for i, entry in enumerate(entries)
        ]
        embed = self._get_base_embed(
            user_id, "⏱️ Dragonbane: Initiativ",
            "Initiativordning (lägst kort agerar först):",
        )
        embed.add_field(name="Ordning", value="\n".join(lines), inline=False)
        self._dragonbane_footer(embed, user_name)
        return embed