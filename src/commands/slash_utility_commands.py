"""
Slash commands för utility operations i EON Discord Bot.
Konverterar prefix commands (!help, !stats, !regel, !höj) till moderna slash commands.
"""

import os
import time
import logging
from typing import List, Optional, Tuple, Any
import discord
from discord.ext import commands
from discord import app_commands

# Setup logging
logger = logging.getLogger(__name__)

# Import migration helpers
from migration.helper import MigrationHelper, SlashCommandDecorator

# Import for dice engine functions
from core.dice_engine import unlimited_d6s
from core.constants import MAX_DICE, MAX_SIDES

class UtilitySlashCommands(commands.Cog):
    """Cog för alla utility-relaterade slash commands."""
    
    def __init__(self, bot, roll_tracker, color_handler, embed_factory):
        self.bot = bot
        self.roll_tracker = roll_tracker
        self.color_handler = color_handler
        self.embed_factory = embed_factory
        
        # Migration helper för säker hantering
        self.helper = MigrationHelper(embed_factory)
        self.decorator = SlashCommandDecorator(self.helper)
        
        # Configure paths for rules folder
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(script_dir))
        self.RULES_FOLDER = os.path.join(project_root, "data", "rules")
        
        # Create rules folder if it doesn't exist
        if not os.path.exists(self.RULES_FOLDER):
            os.makedirs(self.RULES_FOLDER)
    
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

    @app_commands.command(name="help", description="Visa detaljerad hjälp för EON Discord Bot kommandon")
    @app_commands.describe(
        category="Kategori av kommandon att visa hjälp för",
        interactive="Använd interaktiv navigation med knappar"
    )
    @app_commands.choices(category=[
        app_commands.Choice(name="Tärningskommandon", value="dice"),
        app_commands.Choice(name="Stridskommandon", value="combat"),
        app_commands.Choice(name="Statistik & Sessioner", value="stats"),
        app_commands.Choice(name="Alla kommandon", value="all")
    ])
    async def help_slash(
        self,
        interaction: discord.Interaction,
        category: Optional[str] = "all",
        interactive: bool = True
    ):
        """Slash command version av !help med förbättrad funktionalitet."""
        start_time = time.time()
        
        try:
            # Skapa huvudhjälp embed
            embed = self.embed_factory.admin_message(
                interaction.user.id,
                "🎲 EON Discord Bot - Hjälp",
                "Komplett guide för alla botkommandon"
            )
            
            if category == "dice" or category == "all":
                embed.add_field(
                    name="🎲 Tärningskommandon",
                    value=(
                        "**Grundläggande:**\n"
                        "`/roll` - Slå tärningar med notation (3d6+2)\n"
                        "`/ex` - Obegränsade tärningar (exploderar på 6:or)\n"
                        "`/count` - Räkna framgångar mot målvärde\n"
                        "`/chance` - Beräkna sannolikhet för framgång\n\n"
                        f"**Begränsningar:** Max {MAX_DICE} tärningar, {MAX_SIDES} sidor"
                    ),
                    inline=False
                )
            
            if category == "combat" or category == "all":
                embed.add_field(
                    name="⚔️ Stridskommandon",
                    value=(
                        "**Attacktyper:**\n"
                        "`/hugg` - Hugganfall med träfftabeller\n"
                        "`/stick` - Stickanfall med precision\n"
                        "`/kross` - Krossanfall för trubbiga vapen\n"
                        "`/fummel` - Slå på fummeltabeller\n\n"
                        "**Modifierare:** Ryttare, fyrbent mål, målpunkter"
                    ),
                    inline=False
                )
            
            if category == "stats" or category == "all":
                embed.add_field(
                    name="📊 Statistik & Verktyg",
                    value=(
                        "**Statistik:**\n"
                        "`/stats` - Sessionstatistik för alla spelare\n"
                        "`/mystats` - Din personliga statistik\n\n"
                        "**Verktyg:**\n"
                        "`/regel` - Visa sparade regler\n"
                        "`/höj` - Förbättringsslag för färdigheter"
                    ),
                    inline=False
                )
            
            # Lägg till navigation info för interactive mode
            if interactive and category == "all":
                embed.add_field(
                    name="🔧 Användarguide",
                    value=(
                        "**Slash Commands fördelar:**\n"
                        "• Autocomplete för parametrar\n"
                        "• Automatisk validering\n"
                        "• Bättre felhantering\n"
                        "• Konsekvent formatering\n\n"
                        "**Kom igång:** Skriv `/` för att se alla kommandon"
                    ),
                    inline=False
                )
            
            # Lägg till footer med versionsinfo
            embed.set_footer(
                text=f"EON Discord Bot • {len(self.bot.tree.get_commands())} slash commands tillgängliga"
            )
            
            execution_time = time.time() - start_time
            await self.helper.log_command_usage(interaction, "help", {
                "category": category,
                "interactive": interactive
            }, execution_time)
            
            # TODO: Implementera interactive buttons för navigation
            await self.helper.send_response(interaction, embed=embed)
            
        except Exception as e:
            embed = await self.helper.create_error_response(
                interaction.user.id,
                f"Ett oväntat fel inträffade: {str(e)}"
            )
            await self.helper.send_response(interaction, embed=embed)

    @app_commands.command(name="stats", description="Visa sessionstatistik för alla spelare")
    @app_commands.describe(
        session_id="Specifik session ID (lämna tom för aktiv session)",
        period="Tidsperiod för statistik",
        detailed="Visa detaljerad statistik"
    )
    @app_commands.choices(period=[
        app_commands.Choice(name="Aktuell session", value="current"),
        app_commands.Choice(name="Senaste dygnet", value="day"),
        app_commands.Choice(name="Senaste veckan", value="week"),
        app_commands.Choice(name="Alla tider", value="all")
    ])
    async def stats_slash(
        self,
        interaction: discord.Interaction,
        session_id: Optional[str] = None,
        period: str = "current",
        detailed: bool = False
    ):
        """Slash command version av !stats med förbättrad funktionalitet."""
        start_time = time.time()
        
        try:
            # Defer för potentiellt långsam databasoperation
            if period in ["week", "all"] or detailed:
                await self.helper.safe_defer(interaction)
            
            # Hämta statistik baserat på period
            if period == "all":
                stats = self.roll_tracker.get_all_time_stats()
                if "error" in stats:
                    embed = await self.helper.create_error_response(
                        interaction.user.id,
                        "Kunde inte hämta all-time statistik",
                        stats["error"]
                    )
                    await self.helper.send_response(interaction, embed=embed)
                    return
                
                # Skapa all-time stats embed
                embed = self.embed_factory.stats_overview(
                    interaction.user.id,
                    "All-Time Statistik",
                    stats['basic_stats'],
                    "alla sessioner"
                )
                
                # Lägg till top players
                if stats['player_stats']:
                    top_players = stats['player_stats'][:5]
                    player_text = "\n".join(
                        f"**{p['name']}**: {p['total_rolls']} slag ({p['success_rate']:.1f}% framgång)"
                        for p in top_players
                    )
                    embed.add_field(
                        name="🏆 Mest Aktiva Spelare",
                        value=player_text,
                        inline=False
                    )
                
                # Lägg till populära tärningar
                if stats['popular_dice']:
                    dice_text = ", ".join(f"{d['type']} ({d['uses']})" for d in stats['popular_dice'][:5])
                    embed.add_field(
                        name="🎲 Populäraste Tärningar",
                        value=dice_text,
                        inline=False
                    )
                
            else:
                # Session-specifik statistik
                stats = self.roll_tracker.get_session_stats(session_id)
                if "error" in stats:
                    embed = await self.helper.create_error_response(
                        interaction.user.id,
                        "Kunde inte hämta sessionstatistik",
                        stats["error"]
                    )
                    await self.helper.send_response(interaction, embed=embed)
                    return
                
                # Skapa session stats embed
                embed = self.embed_factory.stats_overview(
                    interaction.user.id,
                    "Sessionstatistik",
                    stats['session_info'],
                    session_id or self.roll_tracker.current_session
                )
                
                # Lägg till detaljerad spelarstatistik
                if stats['player_stats']:
                    player_text = "\n".join(
                        f"**{p['name']}**: {p['total_rolls']} slag ({p['successes']}/{p['failures']})"
                        for p in stats['player_stats'][:10]
                    )
                    embed.add_field(
                        name="👥 Spelarstatistik",
                        value=player_text,
                        inline=False
                    )
                
                # Lägg till kommandostatistik
                if stats['command_stats']:
                    cmd_text = ", ".join(
                        f"{c['command']} ({c['uses']})" for c in stats['command_stats']
                    )
                    embed.add_field(
                        name="📊 Kommandoanvändning",
                        value=cmd_text,
                        inline=False
                    )
            
            # Lägg till detailed info om begärt
            if detailed and 'ex_special_stats' in stats:
                ex_stats = stats['ex_special_stats']
                embed.add_field(
                    name="✨ Perfekta & Fummel (Ex-kommandon)",
                    value=f"Perfekta slag: {ex_stats.get('total_perfect', 0)} | Fummel: {ex_stats.get('total_fumble', 0)}",
                    inline=False
                )
            
            execution_time = time.time() - start_time
            await self.helper.log_command_usage(interaction, "stats", {
                "session_id": session_id,
                "period": period,
                "detailed": detailed
            }, execution_time)
            
            await self.helper.send_response(interaction, embed=embed)
            
        except Exception as e:
            embed = await self.helper.create_error_response(
                interaction.user.id,
                f"Ett oväntat fel inträffade: {str(e)}"
            )
            await self.helper.send_response(interaction, embed=embed)

    @app_commands.command(name="mystats", description="Visa din personliga tärningsstatistik")
    @app_commands.describe(
        period="Tidsperiod för din statistik",
        detailed="Inkludera detaljerad breakdown"
    )
    @app_commands.choices(period=[
        app_commands.Choice(name="Aktuell session", value="current"),
        app_commands.Choice(name="Alla tider", value="all")
    ])
    async def mystats_slash(
        self,
        interaction: discord.Interaction,
        period: str = "current",
        detailed: bool = False
    ):
        """Slash command version av !mystats."""
        start_time = time.time()
        
        try:
            user_id = str(interaction.user.id)
            
            if period == "all":
                stats = self.roll_tracker.get_player_all_time_stats(user_id)
            else:
                stats = self.roll_tracker.get_player_stats(user_id)
            
            if "error" in stats:
                embed = await self.helper.create_error_response(
                    interaction.user.id,
                    "Kunde inte hämta din statistik",
                    stats["error"]
                )
                await self.helper.send_response(interaction, embed=embed)
                return
            
            # Skapa personlig stats embed
            embed = self.embed_factory.stats_overview(
                interaction.user.id,
                f"{interaction.user.display_name}s Statistik",
                stats.get('basic_stats', {}),
                period
            )
            
            # Lägg till recent rolls för current session
            if period == "current" and "rolls" in stats:
                recent_rolls = stats["rolls"][:5]
                if recent_rolls:
                    roll_text = "\n".join(
                        f"`{r['command']} {r['dice']}`" +
                        (f" (→{r['target']})" if r['target'] else "") +
                        f": {r['values']}" +
                        (f" {'✅' if r['success'] else '❌'}" if r['success'] is not None else "")
                        for r in recent_rolls
                    )
                    embed.add_field(
                        name="🎲 Senaste Slag",
                        value=roll_text,
                        inline=False
                    )
            
            # Lägg till command breakdown för all-time
            if period == "all" and "command_stats" in stats:
                cmd_text = "\n".join(
                    f"**{c['command']}**: {c['uses']} gånger ({c['success_rate']:.1f}% framgång)"
                    for c in stats['command_stats'][:5]
                )
                embed.add_field(
                    name="📊 Kommandoanvändning",
                    value=cmd_text,
                    inline=False
                )
            
            # Lägg till detailed ex stats om tillgängligt
            if detailed and 'ex_special_stats' in stats:
                ex_stats = stats['ex_special_stats']
                embed.add_field(
                    name="✨ Ex-kommando Specialslag",
                    value=(
                        f"Perfekta slag: {ex_stats['perfect_rolls']} ({ex_stats['perfect_rate']:.1f}%)\n"
                        f"Fummel: {ex_stats['fumble_rolls']} ({ex_stats['fumble_rate']:.1f}%)"
                    ),
                    inline=False
                )
            
            # Lägg till lucky/unlucky dice för all-time
            if period == "all":
                if stats.get('lucky_dice', {}).get('type'):
                    embed.add_field(
                        name="🍀 Lyckligaste Tärning",
                        value=f"{stats['lucky_dice']['type']} ({stats['lucky_dice']['success_rate']:.1f}% framgång)",
                        inline=True
                    )
                if stats.get('unlucky_dice', {}).get('type'):
                    embed.add_field(
                        name="💀 Olyckligaste Tärning",
                        value=f"{stats['unlucky_dice']['type']} ({stats['unlucky_dice']['success_rate']:.1f}% framgång)",
                        inline=True
                    )
            
            execution_time = time.time() - start_time
            await self.helper.log_command_usage(interaction, "mystats", {
                "period": period,
                "detailed": detailed
            }, execution_time)
            
            await self.helper.send_response(interaction, embed=embed)
            
        except Exception as e:
            embed = await self.helper.create_error_response(
                interaction.user.id,
                f"Ett oväntat fel inträffade: {str(e)}"
            )
            await self.helper.send_response(interaction, embed=embed)

    @app_commands.command(name="regel", description="Visa sparade regler från regelbiblioteket")
    @app_commands.describe(
        val="Regelnamn eller nummer (t.ex. 'strid' eller '1')"
    )
    @app_commands.autocomplete(val=rule_autocomplete)
    async def rule_slash(
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
                
                embed.set_footer(text="Använd /regel val:1 eller /regel val:regelnamn för att visa specifik regel")
                
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
            await self.helper.log_command_usage(interaction, "regel", {
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

    @app_commands.command(name="höj", description="Gör förbättringsslag för färdigheter enligt EON-regler")
    @app_commands.describe(
        värde="Nuvarande färdighetsvärde (1-30)",
        lättlärd="Färdigheten är lättlärd (Ob4T6 istället för Ob3T6)"
    )
    async def improvement_slash(
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
                "höj",
                num_dice,
                6,
                all_rolls,
                0,  # modifier
                värde,  # target
                success
            )
            
            execution_time = time.time() - start_time
            await self.helper.log_command_usage(interaction, "höj", {
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

    @app_commands.command(name="allstats", description="[GM] Avancerad statistik för alla spelare med export")
    @app_commands.describe(
        period="Tidsperiod för statistik",
        visualisering="Typ av visualisering att generera",
        export="Exportformat för data"
    )
    @app_commands.choices(period=[
        app_commands.Choice(name="Aktuell session", value="current"),
        app_commands.Choice(name="Senaste veckan", value="week"),
        app_commands.Choice(name="Senaste månaden", value="month"),
        app_commands.Choice(name="Alla tider", value="all")
    ])
    @app_commands.choices(visualisering=[
        app_commands.Choice(name="Övergripande", value="overview"),
        app_commands.Choice(name="Tärningsfördelning", value="distribution"),
        app_commands.Choice(name="Aktivitet över tid", value="activity"),
        app_commands.Choice(name="Jämförelse spelare", value="comparison")
    ])
    @app_commands.choices(export=[
        app_commands.Choice(name="Ingen export", value="none"),
        app_commands.Choice(name="CSV-fil", value="csv"),
        app_commands.Choice(name="JSON-data", value="json")
    ])
    @app_commands.default_permissions(manage_guild=True)
    async def allstats_slash(
        self,
        interaction: discord.Interaction,
        period: str = "current",
        visualisering: str = "overview",
        export: str = "none"
    ):
        """[GM ONLY] Avancerad server-statistik med visualisering."""
        # KRITISKT: Defer omedelbart - detta tar tid
        await self.helper.safe_defer(interaction)
        start_time = time.time()
        
        try:
            # Kontrollera GM-behörigheter (förenklad version)
            if not interaction.user.guild_permissions.manage_guild:
                embed = await self.helper.create_error_response(
                    interaction.user.id,
                    "🚫 Endast för administratörer",
                    "Detta kommando kräver server-administratör behörigheter"
                )
                await self.helper.send_response(interaction, embed=embed)
                return
            
            # Hämta omfattande statistik
            if period == "all":
                stats = self.roll_tracker.get_all_time_stats()
            elif period == "month":
                # TODO: Implementera månadsstatistik
                stats = self.roll_tracker.get_all_time_stats()  # Fallback
            elif period == "week":
                # TODO: Implementera veckostatistik  
                stats = self.roll_tracker.get_all_time_stats()  # Fallback
            else:
                stats = self.roll_tracker.get_session_stats()
            
            if "error" in stats:
                embed = await self.helper.create_error_response(
                    interaction.user.id,
                    "Kunde inte hämta statistik",
                    stats["error"]
                )
                await self.helper.send_response(interaction, embed=embed)
                return
            
            # Skapa huvudstatistik embed
            embed = self.embed_factory.stats_overview(
                interaction.user.id,
                f"📊 Avancerad Serverstatistik ({period})",
                stats.get('basic_stats', {}),
                f"Avancerad analys - {period}"
            )
            
            # Per-spelare breakdown
            if stats.get('player_stats'):
                players = stats['player_stats'][:10]  # Top 10
                player_text = ""
                
                for i, player in enumerate(players, 1):
                    success_rate = player.get('success_rate', 0)
                    total_rolls = player.get('total_rolls', 0)
                    
                    # Emoji för ranking
                    rank_emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
                    
                    player_text += f"{rank_emoji} **{player['name']}**: {total_rolls} slag ({success_rate:.1f}%)\n"
                
                embed.add_field(
                    name="👥 Top 10 Mest Aktiva Spelare",
                    value=player_text,
                    inline=False
                )
            
            # Session jämförelser
            if stats.get('session_comparison'):
                comp = stats['session_comparison']
                embed.add_field(
                    name="📈 Trend Analysis",
                    value=f"Aktivitetsökning: {comp.get('activity_trend', 0):+.1f}%\nFramgångsförbättring: {comp.get('success_trend', 0):+.1f}%",
                    inline=True
                )
            
            # Anomaly detection
            if stats.get('anomalies'):
                anomalies = stats['anomalies'][:3]
                anomaly_text = "\n".join([
                    f"⚠️ {anomaly.get('description', 'Okänd anomali')}"
                    for anomaly in anomalies
                ])
                
                if anomaly_text:
                    embed.add_field(
                        name="🚨 Ovanliga Mönster",
                        value=anomaly_text,
                        inline=False
                    )
            
            # Popularaste tärningar med detaljer
            if stats.get('popular_dice'):
                dice_data = stats['popular_dice'][:5]
                dice_text = ""
                
                for dice in dice_data:
                    dice_text += f"**{dice['type']}**: {dice['uses']} användningar ({dice.get('success_rate', 0):.1f}% framgång)\n"
                
                embed.add_field(
                    name="🎲 Populäraste Tärningar",
                    value=dice_text,
                    inline=False
                )
            
            # Export funktionalitet
            export_info = ""
            if export != "none":
                try:
                    export_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'exports')
                    os.makedirs(export_dir, exist_ok=True)
                    
                    timestamp = int(time.time())
                    
                    if export == "csv":
                        import csv
                        export_file = os.path.join(export_dir, f"stats_{period}_{timestamp}.csv")
                        
                        # Förenklad CSV export
                        with open(export_file, 'w', newline='', encoding='utf-8') as f:
                            writer = csv.writer(f)
                            writer.writerow(['Player', 'Total_Rolls', 'Success_Rate', 'Commands_Used'])
                            
                            for player in stats.get('player_stats', []):
                                writer.writerow([
                                    player.get('name', ''),
                                    player.get('total_rolls', 0),
                                    player.get('success_rate', 0),
                                    player.get('total_commands', 0)
                                ])
                        
                        export_info = f"📊 CSV exporterad: {os.path.basename(export_file)}"
                    
                    elif export == "json":
                        import json
                        export_file = os.path.join(export_dir, f"stats_{period}_{timestamp}.json")
                        
                        with open(export_file, 'w', encoding='utf-8') as f:
                            json.dump(stats, f, ensure_ascii=False, indent=2, default=str)
                        
                        export_info = f"📋 JSON exporterad: {os.path.basename(export_file)}"
                        
                except Exception as e:
                    export_info = f"⚠️ Export misslyckades: {str(e)}"
            
            # Cache resultat (5 minuter)
            cache_key = f"allstats_{interaction.guild.id}_{period}_{visualisering}"
            # TODO: Implementera caching om önskat
            
            if export_info:
                embed.add_field(
                    name="💾 Export Status",
                    value=export_info,
                    inline=False
                )
            
            # Performance info
            execution_time = time.time() - start_time
            embed.add_field(
                name="⚡ Performance",
                value=f"Beräkningstid: {execution_time:.2f}s",
                inline=True
            )
            
            await self.helper.log_command_usage(interaction, "allstats", {
                "period": period,
                "visualization": visualisering,
                "export": export,
                "player_count": len(stats.get('player_stats', []))
            }, execution_time)
            
            await self.helper.send_response(interaction, embed=embed)
            
        except Exception as e:
            embed = await self.helper.create_error_response(
                interaction.user.id,
                f"Ett oväntat fel inträffade: {str(e)}"
            )
            await self.helper.send_response(interaction, embed=embed)

    @app_commands.command(name="mystatsall", description="Avancerad personlig statistik med progression och achievements")
    @app_commands.describe(
        period="Tidsperiod för analys",
        jämför="Jämför med din egen historik",
        achievements="Visa achievement progress"
    )
    @app_commands.choices(period=[
        app_commands.Choice(name="Senaste sessionen", value="last_session"),
        app_commands.Choice(name="Senaste veckan", value="week"),  
        app_commands.Choice(name="Senaste månaden", value="month"),
        app_commands.Choice(name="Alla tider", value="all")
    ])
    async def mystatsall_slash(
        self,
        interaction: discord.Interaction,
        period: str = "all",
        jämför: bool = True,
        achievements: bool = True
    ):
        """Avancerad personlig statistik med progression."""
        # Defer för potentiellt komplexa beräkningar
        await self.helper.safe_defer(interaction)
        start_time = time.time()
        
        try:
            user_id = str(interaction.user.id)
            
            # Hämta avancerad spelarstatistik
            if period == "all":
                stats = self.roll_tracker.get_player_all_time_stats(user_id)
            else:
                # Fallback till standard player stats för nu
                stats = self.roll_tracker.get_player_stats(user_id)
                # TODO: Implementera period-specifik statistik
            
            if "error" in stats:
                embed = await self.helper.create_error_response(
                    interaction.user.id,
                    "Kunde inte hämta din statistik",
                    stats["error"]
                )
                await self.helper.send_response(interaction, embed=embed)
                return
            
            # Skapa avancerad personlig embed
            embed = self.embed_factory.stats_overview(
                interaction.user.id,
                f"🎯 {interaction.user.display_name}s Avancerade Statistik",
                stats.get('basic_stats', {}),
                period
            )
            
            # Progression över tid (om jämförelse aktiverad)
            if jämför and stats.get('progression'):
                prog = stats['progression']
                
                progression_text = []
                if prog.get('skill_trend'):
                    trend = prog['skill_trend']
                    trend_emoji = "📈" if trend > 0 else "📉" if trend < 0 else "➡️"
                    progression_text.append(f"{trend_emoji} Färdighet: {trend:+.1f}% förbättring")
                
                if prog.get('activity_trend'):
                    trend = prog['activity_trend']
                    trend_emoji = "🔥" if trend > 0 else "❄️" if trend < 0 else "⚖️"
                    progression_text.append(f"{trend_emoji} Aktivitet: {trend:+.1f}% förändring")
                
                if progression_text:
                    embed.add_field(
                        name="📊 Progression Analys",
                        value="\n".join(progression_text),
                        inline=False
                    )
            
            # Personliga rekord
            if stats.get('personal_records'):
                records = stats['personal_records']
                record_text = []
                
                if records.get('highest_roll'):
                    record_text.append(f"🏆 Högsta slag: {records['highest_roll']}")
                
                if records.get('longest_streak'):
                    record_text.append(f"🔥 Längsta serie: {records['longest_streak']} framgångar")
                
                if records.get('most_rolls_session'):
                    record_text.append(f"🎲 Mest aktiv session: {records['most_rolls_session']} slag")
                
                if record_text:
                    embed.add_field(
                        name="🏅 Personliga Rekord",
                        value="\n".join(record_text),
                        inline=False
                    )
            
            # Achievement tracking
            if achievements and stats.get('achievements'):
                achs = stats['achievements']
                achievement_text = []
                
                # Förenklad achievement system
                total_rolls = stats.get('basic_stats', {}).get('total_rolls', 0)
                
                # Tärnings-achievements
                if total_rolls >= 1000:
                    achievement_text.append("🎖️ Tärnings-Veteran (1000+ slag)")
                elif total_rolls >= 500:
                    achievement_text.append("🏅 Tärnings-Expert (500+ slag)")
                elif total_rolls >= 100:
                    achievement_text.append("🏆 Tärnings-Adept (100+ slag)")
                
                # Success rate achievements
                success_rate = stats.get('basic_stats', {}).get('success_rate', 0)
                if success_rate >= 80:
                    achievement_text.append("⭐ Lyckosam (80%+ framgång)")
                elif success_rate >= 70:
                    achievement_text.append("✨ Skicklig (70%+ framgång)")
                
                # Special achievements (om data finns)
                if stats.get('ex_special_stats', {}).get('perfect_rolls', 0) >= 10:
                    achievement_text.append("💎 Perfektionist (10+ perfekta slag)")
                
                if achievement_text:
                    embed.add_field(
                        name="🏆 Achievements",
                        value="\n".join(achievement_text[:5]),  # Max 5
                        inline=False
                    )
            
            # Jämförelse med egen historik
            if jämför and stats.get('historical_comparison'):
                hist = stats['historical_comparison']
                
                comparison_text = []
                if hist.get('vs_last_month'):
                    diff = hist['vs_last_month']
                    symbol = "📈" if diff > 0 else "📉" if diff < 0 else "➡️"
                    comparison_text.append(f"{symbol} vs förra månaden: {diff:+.1f}%")
                
                if hist.get('vs_best_session'):
                    diff = hist['vs_best_session']
                    comparison_text.append(f"🎯 vs bästa session: {diff:+.1f}%")
                
                if comparison_text:
                    embed.add_field(
                        name="📈 Historisk Jämförelse",
                        value="\n".join(comparison_text),
                        inline=False
                    )
            
            # Predictive analytics (förenklad)
            if stats.get('predictions'):
                pred = stats['predictions']
                
                if pred.get('next_level_estimate'):
                    embed.add_field(
                        name="🔮 Prognos",
                        value=f"Beräknad tid till nästa nivå: {pred['next_level_estimate']}",
                        inline=False
                    )
            
            # Kommando favoriter med trender
            if stats.get('command_trends'):
                trends = stats['command_trends']
                trend_text = "\n".join([
                    f"**{cmd}**: {data['count']} ({data.get('trend', 0):+.0f}%)"
                    for cmd, data in list(trends.items())[:5]
                ])
                
                embed.add_field(
                    name="📊 Kommando Trender",
                    value=trend_text,
                    inline=False
                )
            
            execution_time = time.time() - start_time
            await self.helper.log_command_usage(interaction, "mystatsall", {
                "period": period,
                "compare": jämför,
                "achievements": achievements
            }, execution_time)
            
            await self.helper.send_response(interaction, embed=embed)
            
        except Exception as e:
            embed = await self.helper.create_error_response(
                interaction.user.id,
                f"Ett oväntat fel inträffade: {str(e)}"
            )
            await self.helper.send_response(interaction, embed=embed)


# Registrering function
async def register_slash_utility_commands(bot, roll_tracker, color_handler, embed_factory):
    """
    Registrera slash utility commands med boten.
    """
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
    from config.feature_flags import is_command_enabled
    
    # Kontrollera om slash utility commands är aktiverade
    if not is_command_enabled("help", "utility"):
        print("Slash utility commands är inte aktiverade enligt feature flags")
        return
    
    # Lägg till cog
    utility_cog = UtilitySlashCommands(bot, roll_tracker, color_handler, embed_factory)
    await bot.add_cog(utility_cog)
    print("Slash utility commands har registrerats (/help, /stats, /mystats, /regel, /höj, /allstats, /mystatsall).")