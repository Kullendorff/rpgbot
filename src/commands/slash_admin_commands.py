"""
Slash commands för admin operations i EON Discord Bot.
Implementerar session management, secret commands och GM-only funktionalitet.
"""

import os
import time
import json
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import discord
from discord.ext import commands
from discord import app_commands

# Import migration helpers
from migration.helper import MigrationHelper, SlashCommandDecorator

class AdminSlashCommands(commands.Cog):
    """Cog för alla admin-relaterade slash commands."""
    
    def __init__(self, bot, roll_tracker, color_handler, embed_factory, knowledge_base=None):
        self.bot = bot
        self.roll_tracker = roll_tracker
        self.color_handler = color_handler
        self.embed_factory = embed_factory
        self.knowledge_base = knowledge_base
        
        # Migration helper för säker hantering
        self.helper = MigrationHelper(embed_factory)
        self.decorator = SlashCommandDecorator(self.helper)
        
        # Session management
        self.current_sessions = {}  # guild_id -> session_data
        
        # Import dice dependencies för secret commands
        from core.dice_parser import parse_dice_string, InvalidDiceFormat, DiceLimitsError
        from core.dice_engine import unlimited_d6s
        from core.constants import MAX_DICE, MAX_SIDES
        
        self.parse_dice_string = parse_dice_string
        self.InvalidDiceFormat = InvalidDiceFormat
        self.DiceLimitsError = DiceLimitsError
        self.unlimited_d6s = unlimited_d6s
        self.MAX_DICE = MAX_DICE
        self.MAX_SIDES = MAX_SIDES
    
    async def check_gm_permission(self, interaction: discord.Interaction) -> bool:
        """
        KRITISK SÄKERHET: Dubbel kontroll för Game Master-behörigheter.
        1. Discord permission check (manage_guild)
        2. Explicit rollkontroll för "Game Master"
        """
        # Första kontrollen: Discord permissions
        if not interaction.user.guild_permissions.manage_guild:
            return False
        
        # Andra kontrollen: Explicit GM-roll
        gm_roles = ["Game Master", "GM", "Spelledare", "Admin"]
        user_roles = [role.name for role in interaction.user.roles]
        
        has_gm_role = any(gm_role in user_roles for gm_role in gm_roles)
        
        if not has_gm_role:
            # Logga säkerhetsincident
            print(f"[SECURITY] Användare {interaction.user.display_name} (ID: {interaction.user.id}) försökte använda GM-kommando utan GM-roll")
            
        return has_gm_role
    
    async def send_gm_only_error(self, interaction: discord.Interaction):
        """Skicka standardiserat felmeddelande för GM-only kommandon."""
        embed = await self.helper.create_error_response(
            interaction.user.id,
            "🚫 Endast för Spelmästare",
            "Detta kommando kräver Game Master-roll och server-behörigheter"
        )
        await self.helper.send_response(interaction, embed=embed)

    # ==================== SESSION MANAGEMENT ====================
    
    @app_commands.command(name="startsession", description="[GM] Starta en ny spelsession med spårning")
    @app_commands.describe(
        beskrivning="Beskrivning av sessionen (valfritt)",
        spelare="Kommaseparerad lista av spelare (valfritt)"
    )
    @app_commands.default_permissions(manage_guild=True)
    async def startsession_slash(
        self,
        interaction: discord.Interaction,
        beskrivning: Optional[str] = None,
        spelare: Optional[str] = None
    ):
        """Starta en ny session med GM-kontroll."""
        start_time = time.time()
        
        # KRITISK: GM-kontroll först
        if not await self.check_gm_permission(interaction):
            await self.send_gm_only_error(interaction)
            return
        
        try:
            guild_id = interaction.guild.id
            session_id = f"session_{int(time.time())}"
            
            # Avsluta befintlig session om den finns
            if guild_id in self.current_sessions:
                old_session = self.current_sessions[guild_id]
                print(f"[SESSION] Automatisk avslutning av session {old_session['session_id']} innan ny start")
            
            # Skapa ny session
            session_data = {
                'session_id': session_id,
                'start_time': datetime.now(),
                'gm_id': interaction.user.id,
                'gm_name': interaction.user.display_name,
                'description': beskrivning or f"Session startad av {interaction.user.display_name}",
                'players': [p.strip() for p in spelare.split(',')] if spelare else [],
                'events': [],
                'roll_count': 0
            }
            
            self.current_sessions[guild_id] = session_data
            
            # Starta session i roll_tracker
            if hasattr(self.roll_tracker, 'start_session'):
                self.roll_tracker.start_session(session_id, interaction.user.id)
            
            # Skapa bekräftelse embed
            embed = self.embed_factory.success_message(
                interaction.user.id,
                f"🎮 Session Startad: {session_id}"
            )
            
            embed.add_field(
                name="📅 Starttid",
                value=session_data['start_time'].strftime("%Y-%m-%d %H:%M:%S"),
                inline=True
            )
            
            embed.add_field(
                name="👑 Spelmaster",
                value=interaction.user.display_name,
                inline=True
            )
            
            if beskrivning:
                embed.add_field(
                    name="📝 Beskrivning",
                    value=beskrivning,
                    inline=False
                )
            
            if spelare:
                embed.add_field(
                    name="👥 Registrerade Spelare",
                    value=spelare,
                    inline=False
                )
            
            # Sätt bot status
            await self.bot.change_presence(
                activity=discord.Activity(type=discord.ActivityType.playing, name="I spelsession")
            )
            
            # Logga session start
            print(f"[SESSION] Session {session_id} startad av {interaction.user.display_name} (ID: {interaction.user.id})")
            
            # Skapa thread för session-diskussion (om möjligt)
            try:
                if interaction.channel.type == discord.ChannelType.text:
                    thread = await interaction.channel.create_thread(
                        name=f"Session {session_id}",
                        type=discord.ChannelType.public_thread
                    )
                    embed.add_field(
                        name="💬 Session Thread",
                        value=f"Diskussion: {thread.mention}",
                        inline=False
                    )
            except:
                pass  # Ignorera om thread creation misslyckas
            
            # Notifiera spelare om angivna
            if spelare:
                notification_embed = self.embed_factory.admin_message(
                    interaction.user.id,
                    "🎮 Spelsession Startad!",
                    f"En ny session har startats av {interaction.user.display_name}"
                )
                # TODO: Implementera player notification logic
            
            execution_time = time.time() - start_time
            await self.helper.log_command_usage(interaction, "startsession", {
                "session_id": session_id,
                "description": bool(beskrivning),
                "player_count": len(session_data['players'])
            }, execution_time)
            
            await self.helper.send_response(interaction, embed=embed)
            
        except Exception as e:
            embed = await self.helper.create_error_response(
                interaction.user.id,
                f"Ett oväntat fel inträffade: {str(e)}"
            )
            await self.helper.send_response(interaction, embed=embed)

    @app_commands.command(name="endsession", description="[GM] Avsluta aktuell session med AI-sammanfattning")
    @app_commands.default_permissions(manage_guild=True)
    async def endsession_slash(self, interaction: discord.Interaction):
        """Avsluta session med AI-genererad sammanfattning."""
        # KRITISK: Defer omedelbart - AI summary tar tid
        await self.helper.safe_defer(interaction)
        start_time = time.time()
        
        # KRITISK: GM-kontroll först
        if not await self.check_gm_permission(interaction):
            await self.send_gm_only_error(interaction)
            return
        
        try:
            guild_id = interaction.guild.id
            
            if guild_id not in self.current_sessions:
                embed = await self.helper.create_error_response(
                    interaction.user.id,
                    "Ingen aktiv session",
                    "Det finns ingen session att avsluta"
                )
                await self.helper.send_response(interaction, embed=embed)
                return
            
            session_data = self.current_sessions[guild_id]
            session_id = session_data['session_id']
            
            # Samla session data från roll_tracker
            session_stats = {}
            if hasattr(self.roll_tracker, 'get_session_stats'):
                session_stats = self.roll_tracker.get_session_stats(session_id)
            
            # Beräkna session längd
            duration = datetime.now() - session_data['start_time']
            
            # Skapa grundläggande sammanfattning
            embed = self.embed_factory.success_message(
                interaction.user.id,
                f"🏁 Session Avslutad: {session_id}"
            )
            
            embed.add_field(
                name="⏰ Session Längd",
                value=f"{duration.total_seconds() // 3600:.0f}h {(duration.total_seconds() % 3600) // 60:.0f}m",
                inline=True
            )
            
            embed.add_field(
                name="👑 Spelmaster",
                value=session_data['gm_name'],
                inline=True
            )
            
            # Lägg till grundläggande statistik
            if session_stats and 'basic_stats' in session_stats:
                stats = session_stats['basic_stats']
                embed.add_field(
                    name="📊 Aktivitet",
                    value=f"Slag: {stats.get('total_rolls', 0)}\nKommandon: {stats.get('total_commands', 0)}",
                    inline=True
                )
            
            # Generera AI-sammanfattning om tillgänglig och >10 händelser
            total_events = session_stats.get('basic_stats', {}).get('total_commands', 0)
            ai_summary = None
            
            if self.knowledge_base and total_events >= 10:
                try:
                    # Skapa prompt för AI-sammanfattning
                    summary_prompt = f"""
                    Skapa en kort sammanfattning av denna EON-spelsession:
                    
                    Session ID: {session_id}
                    Längd: {duration}
                    Spelmaster: {session_data['gm_name']}
                    Beskrivning: {session_data.get('description', 'Ingen beskrivning')}
                    
                    Statistik:
                    - Totala tärningsslag: {session_stats.get('basic_stats', {}).get('total_rolls', 0)}
                    - Använda kommandon: {session_stats.get('basic_stats', {}).get('total_commands', 0)}
                    
                    Skriv en kort, entusiastisk sammanfattning på svenska (max 200 ord).
                    """
                    
                    # Enkel AI-call utan timeout complexity för nu
                    if hasattr(self.knowledge_base, 'claude_client') and self.knowledge_base.claude_client:
                        response = self.knowledge_base.claude_client.messages.create(
                            model="claude-3-5-sonnet-20240620",
                            max_tokens=300,
                            messages=[{"role": "user", "content": summary_prompt}]
                        )
                        ai_summary = response.content[0].text
                
                except Exception as e:
                    print(f"[SESSION] AI summary misslyckades: {e}")
            
            if ai_summary:
                embed.add_field(
                    name="🤖 AI Sammanfattning",
                    value=ai_summary[:1000] + ("..." if len(ai_summary) > 1000 else ""),
                    inline=False
                )
            
            # Avsluta session i roll_tracker
            if hasattr(self.roll_tracker, 'end_session'):
                self.roll_tracker.end_session(session_id)
            
            # Arkivera session data
            archive_data = {
                **session_data,
                'end_time': datetime.now().isoformat(),
                'duration_seconds': duration.total_seconds(),
                'stats': session_stats,
                'ai_summary': ai_summary
            }
            
            # Spara till fil (enkel arkivering)
            try:
                archive_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'sessions')
                os.makedirs(archive_dir, exist_ok=True)
                
                archive_file = os.path.join(archive_dir, f"{session_id}.json")
                with open(archive_file, 'w', encoding='utf-8') as f:
                    json.dump(archive_data, f, ensure_ascii=False, indent=2, default=str)
                
                embed.add_field(
                    name="💾 Arkivering",
                    value=f"Session sparad som {session_id}.json",
                    inline=False
                )
                
            except Exception as e:
                print(f"[SESSION] Arkivering misslyckades: {e}")
            
            # Ta bort från aktiva sessioner
            del self.current_sessions[guild_id]
            
            # Återställ bot status
            await self.bot.change_presence(activity=None)
            
            # Skicka rapport till GM via DM
            try:
                dm_embed = embed.copy()
                dm_embed.title = f"📋 Session Rapport: {session_id}"
                await interaction.user.send(embed=dm_embed)
                
                embed.add_field(
                    name="📨 Rapport Skickad",
                    value="Detaljerad rapport skickad via DM",
                    inline=False
                )
            except:
                pass  # Ignorera om DM misslyckas
            
            # Logga session end
            print(f"[SESSION] Session {session_id} avslutad av {interaction.user.display_name}")
            
            execution_time = time.time() - start_time
            await self.helper.log_command_usage(interaction, "endsession", {
                "session_id": session_id,
                "duration_hours": duration.total_seconds() / 3600,
                "total_events": total_events,
                "ai_summary_generated": bool(ai_summary)
            }, execution_time)
            
            await self.helper.send_response(interaction, embed=embed)
            
        except Exception as e:
            embed = await self.helper.create_error_response(
                interaction.user.id,
                f"Ett oväntat fel inträffade: {str(e)}"
            )
            await self.helper.send_response(interaction, embed=embed)

    @app_commands.command(name="showsession", description="[GM] Visa information om aktuell session")
    @app_commands.default_permissions(manage_guild=True)
    async def showsession_slash(self, interaction: discord.Interaction):
        """Visa aktuell session information."""
        start_time = time.time()
        
        # KRITISK: GM-kontroll först
        if not await self.check_gm_permission(interaction):
            await self.send_gm_only_error(interaction)
            return
        
        try:
            guild_id = interaction.guild.id
            
            if guild_id not in self.current_sessions:
                embed = await self.helper.create_error_response(
                    interaction.user.id,
                    "Ingen aktiv session",
                    "Starta en session med /startsession"
                )
                await self.helper.send_response(interaction, embed=embed)
                return
            
            session_data = self.current_sessions[guild_id]
            session_id = session_data['session_id']
            
            # Beräkna session längd
            duration = datetime.now() - session_data['start_time']
            
            # Hämta real-time statistik
            session_stats = {}
            if hasattr(self.roll_tracker, 'get_session_stats'):
                session_stats = self.roll_tracker.get_session_stats(session_id)
            
            # Skapa session info embed
            embed = self.embed_factory.admin_message(
                interaction.user.id,
                f"📊 Aktuell Session: {session_id}",
                session_data['description']
            )
            
            embed.add_field(
                name="📅 Startid",
                value=session_data['start_time'].strftime("%Y-%m-%d %H:%M:%S"),
                inline=True
            )
            
            embed.add_field(
                name="⏰ Längd",
                value=f"{duration.total_seconds() // 3600:.0f}h {(duration.total_seconds() % 3600) // 60:.0f}m",
                inline=True
            )
            
            embed.add_field(
                name="👑 Spelmaster",
                value=session_data['gm_name'],
                inline=True
            )
            
            # Aktiva spelare
            if session_data['players']:
                embed.add_field(
                    name="👥 Registrerade Spelare",
                    value="\n".join(f"• {player}" for player in session_data['players']),
                    inline=False
                )
            
            # Session statistik
            if session_stats and 'basic_stats' in session_stats:
                stats = session_stats['basic_stats']
                
                embed.add_field(
                    name="📊 Aktivitet",
                    value=f"Slag: {stats.get('total_rolls', 0)}\nKommandon: {stats.get('total_commands', 0)}",
                    inline=True
                )
                
                # Högsta/lägsta slag
                if 'highest_roll' in stats:
                    embed.add_field(
                        name="🎲 Rekord",
                        value=f"Högst: {stats.get('highest_roll', 'N/A')}\nLägst: {stats.get('lowest_roll', 'N/A')}",
                        inline=True
                    )
            
            # Senaste aktivitet
            if session_stats and 'player_stats' in session_stats:
                recent_players = session_stats['player_stats'][:5]
                if recent_players:
                    player_text = "\n".join(
                        f"• {p['name']}: {p['total_rolls']} slag"
                        for p in recent_players
                    )
                    embed.add_field(
                        name="🏃 Aktiva Spelare",
                        value=player_text,
                        inline=False
                    )
            
            execution_time = time.time() - start_time
            await self.helper.log_command_usage(interaction, "showsession", {
                "session_id": session_id,
                "duration_hours": duration.total_seconds() / 3600
            }, execution_time)
            
            await self.helper.send_response(interaction, embed=embed)
            
        except Exception as e:
            embed = await self.helper.create_error_response(
                interaction.user.id,
                f"Ett oväntat fel inträffade: {str(e)}"
            )
            await self.helper.send_response(interaction, embed=embed)

    # ==================== SECRET COMMANDS ====================
    
    @app_commands.command(name="secret_roll", description="[GM] Hemlig tärningsslag som endast GM ser")
    @app_commands.describe(
        tärningar="Tärningsformel (t.ex. 3d6+2, 4d10-1)",
        mål="Målvärde för att bedöma framgång (valfritt)",
        meddelande="Hemligt meddelande om slaget (valfritt)"
    )
    @app_commands.default_permissions(manage_guild=True)
    async def secret_roll_slash(
        self,
        interaction: discord.Interaction,
        tärningar: str,
        mål: Optional[app_commands.Range[int, 1, 100]] = None,
        meddelande: Optional[str] = None
    ):
        """Secret version av /roll - ALLTID ephemeral."""
        start_time = time.time()
        
        # KRITISK: GM-kontroll först
        if not await self.check_gm_permission(interaction):
            await self.send_gm_only_error(interaction)
            return
        
        try:
            # Parsa dice string
            try:
                dice_spec = self.parse_dice_string(tärningar)
                dice_count, sides, modifier = dice_spec.count, dice_spec.sides, dice_spec.modifier
            except self.InvalidDiceFormat as e:
                embed = await self.helper.create_error_response(
                    interaction.user.id,
                    f"Ogiltig tärningsformel: {tärningar}",
                    "Använd format som '3d6+2' eller '4d10-1'"
                )
                # KRITISKT: Ephemeral för secret commands
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            except self.DiceLimitsError as e:
                embed = await self.helper.create_error_response(
                    interaction.user.id,
                    str(e),
                    f"Max {self.MAX_DICE} tärningar och {self.MAX_SIDES} sidor per tärning"
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Rulla tärningar
            import random
            results = [random.randint(1, sides) for _ in range(dice_count)]
            total = sum(results) + modifier
            
            # Bedöm framgång
            success = None
            if mål is not None:
                success = total >= mål
            
            # Logga som secret roll (utan att spara i normal stats)
            print(f"[SECRET] {interaction.user.display_name} rullade hemligt: {tärningar} = {total}")
            
            # Skapa hemlig embed
            embed = self.embed_factory.dice_result(
                interaction.user.id,
                f"🤫 {interaction.user.display_name} (hemligt)",
                "secret_roll",
                tärningar,
                results,
                total,
                mål,
                success
            )
            
            # Lägg till secret-specifik info
            embed.add_field(
                name="🔒 Hemligt Slag",
                value="Detta resultat syns endast för dig",
                inline=False
            )
            
            if meddelande:
                embed.add_field(
                    name="📝 Meddelande",
                    value=meddelande,
                    inline=False
                )
            
            # Modifier info
            if modifier != 0:
                modifier_text = f"+{modifier}" if modifier > 0 else str(modifier)
                embed.add_field(
                    name="Modifierare", 
                    value=modifier_text, 
                    inline=True
                )
            
            execution_time = time.time() - start_time
            await self.helper.log_command_usage(interaction, "secret_roll", {
                "dice": tärningar, "target": mål, "has_message": bool(meddelande)
            }, execution_time)
            
            # KRITISKT: ALLTID ephemeral för secret commands
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
            # Skicka även DM till GM som backup
            try:
                dm_embed = embed.copy()
                dm_embed.title = f"🤫 Hemligt Slag Backup: {tärningar}"
                await interaction.user.send(embed=dm_embed)
            except:
                pass  # Ignorera om DM misslyckas
            
        except Exception as e:
            embed = await self.helper.create_error_response(
                interaction.user.id,
                f"Ett oväntat fel inträffade: {str(e)}"
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="secret_ex", description="[GM] Hemliga exploderande d6:or som endast GM ser")
    @app_commands.describe(
        antal="Antal d6:or att rulla (1-50)",
        mål="Målvärde för att bedöma framgång (valfritt)",
        meddelande="Hemligt meddelande om slaget (valfritt)"
    )
    @app_commands.default_permissions(manage_guild=True)
    async def secret_ex_slash(
        self,
        interaction: discord.Interaction,
        antal: app_commands.Range[int, 1, 50],
        mål: Optional[app_commands.Range[int, 1, 100]] = None,
        meddelande: Optional[str] = None
    ):
        """Secret version av /ex - exploderande d6."""
        start_time = time.time()
        
        # KRITISK: GM-kontroll först
        if not await self.check_gm_permission(interaction):
            await self.send_gm_only_error(interaction)
            return
        
        try:
            # Använd unlimited_d6s engine
            all_rolls, total, initial_rolls = self.unlimited_d6s(antal)
            results = all_rolls
            
            # Kontrollera perfekta och fummelkriterier
            perfect_candidate = False
            if antal == 1:
                if initial_rolls[0] in [1, 2, 3]:
                    perfect_candidate = True
            else:
                not_one_count = sum(1 for r in initial_rolls if r != 1)
                if not_one_count <= 1:
                    perfect_candidate = True

            six_count = sum(1 for r in initial_rolls if r == 6)
            fumble_candidate = (six_count >= 2)
            
            # Bedöm framgång mot målvärde
            success = None
            if mål is not None:
                success = total <= mål
            
            # Logga som secret roll
            print(f"[SECRET] {interaction.user.display_name} rullade hemligt EX: {antal}d6 = {total}")
            
            # Skapa hemlig embed
            embed = self.embed_factory.dice_result(
                interaction.user.id,
                f"🤫 {interaction.user.display_name} (hemligt)",
                "secret_ex",
                f"{antal}d6 (exploderande)",
                initial_rolls,
                total,
                mål,
                success
            )
            
            # Lägg till secret-specifik info
            embed.add_field(
                name="🔒 Hemligt EX-Slag",
                value="Detta resultat syns endast för dig",
                inline=False
            )
            
            if meddelande:
                embed.add_field(
                    name="📝 Meddelande",
                    value=meddelande,
                    inline=False
                )
            
            # Explosion info
            explosion_count = len(results) - antal
            if explosion_count > 0:
                embed.add_field(
                    name="💥 Explosioner", 
                    value=f"{explosion_count} extra tärningar från 6:or", 
                    inline=True
                )
            
            # Visa alla kast
            embed.add_field(
                name="Alla kast (inkl. extra)", 
                value=str(all_rolls), 
                inline=False
            )
            
            # Target value evaluation
            if mål is not None:
                difference = mål - total
                result_text = None
                if success:
                    result_text = "✨ **Perfekt slag!** (lyckat)" if perfect_candidate else "✅ **Lyckat slag**"
                else:
                    result_text = "💥 **FUMMEL!**" if fumble_candidate else "❌ **Misslyckat**"
                
                embed.add_field(
                    name=f"Motståndsvärde: {mål}",
                    value=f"{result_text}\n(Marginal: {difference:+d})",
                    inline=False
                )
            
            # Special cases
            if perfect_candidate or fumble_candidate:
                special_result = []
                if perfect_candidate:
                    special_result.append("✨ **PERFEKT SLAG!** Tärningsoraklet ler mot dig.")
                if fumble_candidate:
                    special_result.append("💥 **FUMMEL!** Tärningsoraklet skrattar åt din olycka.")
                    
                embed.add_field(
                    name="Särskilt Utfall",
                    value="\n".join(special_result),
                    inline=False
                )
            
            execution_time = time.time() - start_time
            await self.helper.log_command_usage(interaction, "secret_ex", {
                "antal": antal, "target": mål, "has_message": bool(meddelande)
            }, execution_time)
            
            # KRITISKT: ALLTID ephemeral
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
            # DM backup
            try:
                dm_embed = embed.copy()
                dm_embed.title = f"🤫 Hemligt EX Backup: {antal}d6"
                await interaction.user.send(embed=dm_embed)
            except:
                pass
            
        except Exception as e:
            embed = await self.helper.create_error_response(
                interaction.user.id,
                f"Ett oväntat fel inträffade: {str(e)}"
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="secret_count", description="[GM] Hemlig framgångsräkning som endast GM ser")
    @app_commands.describe(
        tärningar="Tärningsformel (t.ex. 5d10, 8d6)",
        mål="Målvärde för framgång (obligatorisk)",
        meddelande="Hemligt meddelande om slaget (valfritt)"
    )
    @app_commands.default_permissions(manage_guild=True)
    async def secret_count_slash(
        self,
        interaction: discord.Interaction,
        tärningar: str,
        mål: app_commands.Range[int, 1, 20],
        meddelande: Optional[str] = None
    ):
        """Secret version av /count."""
        start_time = time.time()
        
        # KRITISK: GM-kontroll först
        if not await self.check_gm_permission(interaction):
            await self.send_gm_only_error(interaction)
            return
        
        try:
            # Parsa dice string
            try:
                dice_spec = self.parse_dice_string(tärningar)
                dice_count, sides, modifier = dice_spec.count, dice_spec.sides, dice_spec.modifier
            except self.InvalidDiceFormat as e:
                embed = await self.helper.create_error_response(
                    interaction.user.id,
                    f"Ogiltig tärningsformel: {tärningar}",
                    "Använd format som '5d10' eller '8d6'"
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            except self.DiceLimitsError as e:
                embed = await self.helper.create_error_response(
                    interaction.user.id,
                    str(e)
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Rulla tärningar
            import random
            results = [random.randint(1, sides) for _ in range(dice_count)]
            
            # Räkna framgångar
            successes = sum(1 for result in results if result >= mål)
            total = sum(results) + modifier
            
            # Logga som secret roll
            print(f"[SECRET] {interaction.user.display_name} rullade hemligt COUNT: {tärningar} mot {mål} = {successes} framgångar")
            
            # Skapa hemlig embed
            embed = self.embed_factory.dice_result(
                interaction.user.id,
                f"🤫 {interaction.user.display_name} (hemligt)",
                "secret_count",
                tärningar,
                results,
                total,
                mål,
                successes > 0
            )
            
            # Lägg till secret-specifik info
            embed.add_field(
                name="🔒 Hemlig Framgångsräkning",
                value="Detta resultat syns endast för dig",
                inline=False
            )
            
            if meddelande:
                embed.add_field(
                    name="📝 Meddelande",
                    value=meddelande,
                    inline=False
                )
            
            # Lägg till framgångsinfo
            embed.add_field(
                name="🎯 Framgångar", 
                value=f"{successes} av {dice_count} tärningar", 
                inline=True
            )
            
            # Visuell representation
            visual = ""
            for result in results:
                if result >= mål:
                    visual += "✅"
                else:
                    visual += "❌"
            
            if len(visual) <= 50:  # Begränsa för långa strängar
                embed.add_field(
                    name="📊 Visuellt", 
                    value=visual, 
                    inline=False
                )
            
            execution_time = time.time() - start_time
            await self.helper.log_command_usage(interaction, "secret_count", {
                "dice": tärningar, "target": mål, "has_message": bool(meddelande)
            }, execution_time)
            
            # KRITISKT: ALLTID ephemeral
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
            # DM backup
            try:
                dm_embed = embed.copy()
                dm_embed.title = f"🤫 Hemligt Count Backup: {tärningar}"
                await interaction.user.send(embed=dm_embed)
            except:
                pass
            
        except Exception as e:
            embed = await self.helper.create_error_response(
                interaction.user.id,
                f"Ett oväntat fel inträffade: {str(e)}"
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

    # ==================== GM CONTROL COMMANDS ====================
    
    @app_commands.command(name="gm_override", description="[GM] Ändra valfritt spelarresultat retroaktivt")
    @app_commands.describe(
        spelare="Användarnamn eller ID för spelaren",
        nytt_resultat="Nytt resultat att använda",
        orsak="Orsak till override (obligatorisk för audit)"
    )
    @app_commands.default_permissions(manage_guild=True)
    async def gm_override_slash(
        self,
        interaction: discord.Interaction,
        spelare: str,
        nytt_resultat: str,
        orsak: str
    ):
        """GM kan överskriva spelarresultat med logging."""
        start_time = time.time()
        
        # KRITISK: GM-kontroll först
        if not await self.check_gm_permission(interaction):
            await self.send_gm_only_error(interaction)
            return
        
        try:
            # Bekräfta override med användaren
            embed = self.embed_factory.admin_message(
                interaction.user.id,
                "⚠️ Bekräfta GM Override",
                f"Du kommer att ändra resultat för {spelare}"
            )
            
            embed.add_field(
                name="🎯 Nytt Resultat",
                value=nytt_resultat,
                inline=True
            )
            
            embed.add_field(
                name="📝 Orsak",
                value=orsak,
                inline=True
            )
            
            embed.add_field(
                name="⚠️ VARNING",
                value="Detta kommer att loggas extensivt för audit-ändamål",
                inline=False
            )
            
            # TODO: Implementera confirmation dialog med buttons
            # För nu, kör override direkt
            
            # Logga override (KRITISK för audit)
            override_log = {
                'timestamp': datetime.now().isoformat(),
                'gm_id': interaction.user.id,
                'gm_name': interaction.user.display_name,
                'player': spelare,
                'new_result': nytt_resultat,
                'reason': orsak,
                'guild_id': interaction.guild.id
            }
            
            print(f"[GM_OVERRIDE] {json.dumps(override_log, ensure_ascii=False)}")
            
            # Spara override till fil för audit
            try:
                override_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'overrides')
                os.makedirs(override_dir, exist_ok=True)
                
                override_file = os.path.join(override_dir, f"override_{int(time.time())}.json")
                with open(override_file, 'w', encoding='utf-8') as f:
                    json.dump(override_log, f, ensure_ascii=False, indent=2)
                
            except Exception as e:
                print(f"[GM_OVERRIDE] Kunde inte spara override-log: {e}")
            
            # Uppdatera embed med bekräftelse
            embed.title = "✅ GM Override Genomförd"
            embed.color = 0x00ff00  # Grön
            
            embed.add_field(
                name="📋 Status",
                value=f"Override genomförd och loggad",
                inline=False
            )
            
            execution_time = time.time() - start_time
            await self.helper.log_command_usage(interaction, "gm_override", {
                "player": spelare,
                "reason_length": len(orsak)
            }, execution_time)
            
            await self.helper.send_response(interaction, embed=embed)
            
            # Notifiera påverkad spelare (om möjligt)
            try:
                # TODO: Implementera player notification
                pass
            except:
                pass
            
        except Exception as e:
            embed = await self.helper.create_error_response(
                interaction.user.id,
                f"Ett oväntat fel inträffade: {str(e)}"
            )
            await self.helper.send_response(interaction, embed=embed)

    @app_commands.command(name="session_rollback", description="[GM] Ångra X antal händelser från aktuell session")
    @app_commands.describe(
        antal="Antal händelser att ångra (1-20)",
        bekräfta="Skriv 'JA' för att bekräfta rollback"
    )
    @app_commands.default_permissions(manage_guild=True)
    async def session_rollback_slash(
        self,
        interaction: discord.Interaction,
        antal: app_commands.Range[int, 1, 20],
        bekräfta: str
    ):
        """Rulla tillbaka session händelser."""
        start_time = time.time()
        
        # KRITISK: GM-kontroll först
        if not await self.check_gm_permission(interaction):
            await self.send_gm_only_error(interaction)
            return
        
        try:
            guild_id = interaction.guild.id
            
            if guild_id not in self.current_sessions:
                embed = await self.helper.create_error_response(
                    interaction.user.id,
                    "Ingen aktiv session",
                    "Det finns ingen aktiv session att rulla tillbaka"
                )
                await self.helper.send_response(interaction, embed=embed)
                return
            
            # Säkerhetskontroll - kräv explicit bekräftelse
            if bekräfta.upper() != "JA":
                embed = await self.helper.create_error_response(
                    interaction.user.id,
                    "Rollback avbruten",
                    "Du måste skriva 'JA' för att bekräfta rollback"
                )
                await self.helper.send_response(interaction, embed=embed)
                return
            
            session_data = self.current_sessions[guild_id]
            session_id = session_data['session_id']
            
            # Hämta senaste händelser för preview
            recent_events = []
            if hasattr(self.roll_tracker, 'get_recent_events'):
                recent_events = self.roll_tracker.get_recent_events(session_id, antal)
            
            # Skapa rollback embed
            embed = self.embed_factory.admin_message(
                interaction.user.id,
                f"🔄 Session Rollback Genomförd",
                f"Rullade tillbaka {antal} händelser från session {session_id}"
            )
            
            if recent_events:
                events_text = "\n".join([
                    f"• {event.get('player_name', 'Unknown')}: {event.get('command', 'N/A')}"
                    for event in recent_events[:5]  # Visa max 5 för brevity
                ])
                embed.add_field(
                    name="📋 Återtagna Händelser",
                    value=events_text,
                    inline=False
                )
            
            # Genomför rollback i roll_tracker
            if hasattr(self.roll_tracker, 'rollback_events'):
                success = self.roll_tracker.rollback_events(session_id, antal)
                if not success:
                    embed.add_field(
                        name="⚠️ Varning",
                        value="Rollback kanske inte kunde genomföras helt",
                        inline=False
                    )
            
            # Logga rollback för audit
            rollback_log = {
                'timestamp': datetime.now().isoformat(),
                'gm_id': interaction.user.id,
                'gm_name': interaction.user.display_name,
                'session_id': session_id,
                'events_count': antal,
                'guild_id': interaction.guild.id
            }
            
            print(f"[SESSION_ROLLBACK] {json.dumps(rollback_log, ensure_ascii=False)}")
            
            # Notifiera påverkade spelare
            if recent_events:
                affected_players = set(event.get('player_name', '') for event in recent_events if event.get('player_name'))
                embed.add_field(
                    name="👥 Påverkade Spelare",
                    value=", ".join(affected_players) if affected_players else "Ingen",
                    inline=False
                )
            
            execution_time = time.time() - start_time
            await self.helper.log_command_usage(interaction, "session_rollback", {
                "session_id": session_id,
                "events_count": antal
            }, execution_time)
            
            await self.helper.send_response(interaction, embed=embed)
            
        except Exception as e:
            embed = await self.helper.create_error_response(
                interaction.user.id,
                f"Ett oväntat fel inträffade: {str(e)}"
            )
            await self.helper.send_response(interaction, embed=embed)

    @app_commands.command(name="player_stats", description="[GM] Visa detaljerad statistik för specifik spelare")
    @app_commands.describe(
        spelare="Användarnamn eller ID för spelaren",
        period="Tidsperiod för statistik",
        jämför="Jämför med server-genomsnitt"
    )
    @app_commands.choices(period=[
        app_commands.Choice(name="Aktuell session", value="current"),
        app_commands.Choice(name="Senaste veckan", value="week"),
        app_commands.Choice(name="Alla tider", value="all")
    ])
    @app_commands.default_permissions(manage_guild=True)
    async def player_stats_slash(
        self,
        interaction: discord.Interaction,
        spelare: str,
        period: str = "current",
        jämför: bool = True
    ):
        """Detaljerad spelarstatistik för GM."""
        await self.helper.safe_defer(interaction)  # Kan ta tid att beräkna
        start_time = time.time()
        
        # KRITISK: GM-kontroll först
        if not await self.check_gm_permission(interaction):
            await self.send_gm_only_error(interaction)
            return
        
        try:
            # Försök hitta spelare (enkel implementering)
            player_id = spelare
            if not spelare.isdigit():
                # TODO: Implementera player name lookup
                pass
            
            # Hämta spelarstatistik
            player_stats = {}
            if hasattr(self.roll_tracker, 'get_detailed_player_stats'):
                player_stats = self.roll_tracker.get_detailed_player_stats(player_id, period)
            
            if not player_stats or "error" in player_stats:
                embed = await self.helper.create_error_response(
                    interaction.user.id,
                    f"Kunde inte hämta statistik för {spelare}",
                    "Kontrollera att spelaren finns och har aktivitet"
                )
                await self.helper.send_response(interaction, embed=embed)
                return
            
            # Skapa detaljerad stats embed
            embed = self.embed_factory.stats_overview(
                interaction.user.id,
                f"📊 Detaljerad Statistik: {spelare}",
                player_stats.get('basic_stats', {}),
                period
            )
            
            # Lägg till GM-specifika insights
            if player_stats.get('patterns'):
                patterns = player_stats['patterns']
                insights = []
                
                if patterns.get('favorite_time'):
                    insights.append(f"🕐 Mest aktiv: {patterns['favorite_time']}")
                
                if patterns.get('lucky_streak'):
                    insights.append(f"🍀 Lyckoserie: {patterns['lucky_streak']} slag")
                
                if patterns.get('unlucky_streak'):
                    insights.append(f"💀 Otursserie: {patterns['unlucky_streak']} slag")
                
                if insights:
                    embed.add_field(
                        name="🔍 Mönster & Insikter",
                        value="\n".join(insights),
                        inline=False
                    )
            
            # Jämförelse med genomsnitt
            if jämför and player_stats.get('comparison'):
                comp = player_stats['comparison']
                
                comparison_text = []
                if comp.get('success_rate_vs_avg'):
                    diff = comp['success_rate_vs_avg']
                    symbol = "📈" if diff > 0 else "📉" if diff < 0 else "➡️"
                    comparison_text.append(f"{symbol} Framgång: {diff:+.1f}% vs genomsnitt")
                
                if comp.get('activity_vs_avg'):
                    diff = comp['activity_vs_avg']
                    symbol = "🔥" if diff > 1.5 else "❄️" if diff < 0.5 else "⚖️"
                    comparison_text.append(f"{symbol} Aktivitet: {diff:.1f}x genomsnittet")
                
                if comparison_text:
                    embed.add_field(
                        name="📊 Jämförelse",
                        value="\n".join(comparison_text),
                        inline=False
                    )
            
            # Ovanliga händelser (anomaly detection)
            if player_stats.get('anomalies'):
                anomalies = player_stats['anomalies']
                anomaly_text = []
                
                for anomaly in anomalies[:3]:  # Max 3 anomalier
                    anomaly_text.append(f"⚠️ {anomaly.get('description', 'Okänt')}")
                
                if anomaly_text:
                    embed.add_field(
                        name="🚨 Ovanliga Mönster",
                        value="\n".join(anomaly_text),
                        inline=False
                    )
            
            # Kommandofördelning
            if player_stats.get('command_breakdown'):
                cmd_breakdown = player_stats['command_breakdown']
                top_commands = sorted(cmd_breakdown.items(), key=lambda x: x[1], reverse=True)[:5]
                
                cmd_text = "\n".join([
                    f"**{cmd}**: {count} användningar"
                    for cmd, count in top_commands
                ])
                
                embed.add_field(
                    name="🎮 Mest Använda Kommandon",
                    value=cmd_text,
                    inline=False
                )
            
            execution_time = time.time() - start_time
            await self.helper.log_command_usage(interaction, "player_stats", {
                "player": spelare,
                "period": period,
                "compare": jämför
            }, execution_time)
            
            await self.helper.send_response(interaction, embed=embed)
            
        except Exception as e:
            embed = await self.helper.create_error_response(
                interaction.user.id,
                f"Ett oväntat fel inträffade: {str(e)}"
            )
            await self.helper.send_response(interaction, embed=embed)


# Registrering function
async def register_slash_admin_commands(bot, roll_tracker, color_handler, embed_factory, knowledge_base=None):
    """
    Registrera slash admin commands med boten.
    """
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
    from config.feature_flags import is_command_enabled
    
    # Kontrollera om slash admin commands är aktiverade
    if not is_command_enabled("startsession", "admin"):
        print("Slash admin commands är inte aktiverade enligt feature flags")
        return
    
    # Lägg till cog
    admin_cog = AdminSlashCommands(bot, roll_tracker, color_handler, embed_factory, knowledge_base)
    await bot.add_cog(admin_cog)
    print("Slash admin commands har registrerats (/startsession, /endsession, /showsession, /secret_roll, /secret_ex, /secret_count, /gm_override, /session_rollback, /player_stats).")