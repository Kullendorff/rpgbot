"""
Finaliserings script för EON Discord Bot slash command migration.
Hanterar gradvis nedstängning av prefix system och övergång till enbart slash commands.
"""

import os
import sys
import json
import time
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

class MigrationFinalizer:
    """Hanterar slutlig övergång från prefix till slash commands."""
    
    def __init__(self, bot):
        self.bot = bot
        self.migration_phases = {
            1: "soft_deprecation",      # Varningar och logging
            2: "gradual_shutdown",      # Inaktivera mindre använda commands  
            3: "critical_only",         # Endast kritiska commands kvar
            4: "full_migration"         # Alla prefix commands borttagna
        }
        self.current_phase = self._get_current_phase()
        
        # Konfigurera paths
        self.base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.migration_data_path = os.path.join(self.base_path, "data", "migration")
        self.backup_path = os.path.join(self.base_path, "data", "backups")
        
        # Säkerställ att mapparna finns
        os.makedirs(self.migration_data_path, exist_ok=True)
        os.makedirs(self.backup_path, exist_ok=True)
    
    def _get_current_phase(self) -> int:
        """Hämta nuvarande migrationsfas från konfiguration."""
        try:
            config_path = os.path.join(self.migration_data_path, "migration_phase.json")
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    return config.get('current_phase', 1)
        except FileNotFoundError as e:
            logger.debug(f"Migration phase config inte funnen, använder default fas 1: {e}")
        except json.JSONDecodeError as e:
            logger.warning(f"Kunde inte parsa migration phase config, använder default fas 1: {e}")
        except Exception as e:
            logger.error(f"Oväntat fel vid läsning av migration phase, använder default fas 1: {e}")
        return 1  # Default till fas 1
    
    def _set_current_phase(self, phase: int):
        """Sätt nuvarande migrationsfas."""
        try:
            config_path = os.path.join(self.migration_data_path, "migration_phase.json")
            config = {
                'current_phase': phase,
                'phase_name': self.migration_phases[phase],
                'updated_at': datetime.now().isoformat(),
                'previous_phase': self.current_phase
            }
            
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            
            self.current_phase = phase
            print(f"[MIGRATION] Migrationsfas uppdaterad till {phase}: {self.migration_phases[phase]}")
            
        except Exception as e:
            print(f"[MIGRATION] Kunde inte uppdatera migrationsfas: {e}")
    
    async def log_prefix_usage(self, user_id: str, command: str, args: List[str]):
        """Logga användning av prefix commands för analys."""
        try:
            usage_log = {
                'timestamp': datetime.now().isoformat(),
                'user_id': user_id,
                'command': command,
                'args_count': len(args),
                'phase': self.current_phase
            }
            
            log_file = os.path.join(self.migration_data_path, f"prefix_usage_{datetime.now().strftime('%Y%m%d')}.json")
            
            # Läs befintlig log
            logs = []
            if os.path.exists(log_file):
                with open(log_file, 'r', encoding='utf-8') as f:
                    logs = json.load(f)
            
            # Lägg till ny log
            logs.append(usage_log)
            
            # Spara tillbaka (begränsa till senaste 1000 entries)
            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump(logs[-1000:], f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            print(f"[MIGRATION] Kunde inte logga prefix användning: {e}")
    
    async def send_deprecation_warning(self, ctx, command: str) -> bool:
        """
        Skicka deprecation warning baserat på aktuell fas.
        
        Returns:
            bool: True om kommandot ska fortsätta köras, False om det ska blockeras
        """
        try:
            user = ctx.author
            
            if self.current_phase == 1:  # Soft deprecation
                warning_message = (
                    f"⚠️ **Kommandot `!{command}` är föråldrat!**\n"
                    f"Använd `/{command}` istället för bättre funktionalitet.\n"
                    f"Prefix commands kommer att tas bort inom kort."
                )
                
                await ctx.send(warning_message, delete_after=10)
                
                # Skicka DM första gången
                if not await self._has_received_dm(user.id, command):
                    try:
                        dm_message = (
                            f"Hej {user.display_name}! 👋\n\n"
                            f"Vi har bytt till moderna slash commands för bättre funktionalitet.\n"
                            f"Istället för `!{command}`, använd `/{command}`.\n\n"
                            f"**Fördelar med slash commands:**\n"
                            f"• Autocomplete för parametrar\n"
                            f"• Bättre felhantering\n"
                            f"• Konsekvent formatering\n"
                            f"• Snabbare respons\n\n"
                            f"Skriv `/help` för att se alla nya kommandon!"
                        )
                        await user.send(dm_message)
                        await self._mark_dm_sent(user.id, command)
                    except Exception as e:
                        logger.warning(f"Kunde inte skicka migration DM till {user.display_name} för kommando {command}: {e}")
                
                return True  # Låt kommandot köras
                
            elif self.current_phase == 2:  # Gradual shutdown
                if command in self._get_non_critical_commands():
                    error_message = (
                        f"❌ **Kommandot `!{command}` är inaktiverat!**\n"
                        f"Använd `/{command}` istället.\n"
                        f"Vissa prefix commands är nu permanent inaktiverade."
                    )
                    await ctx.send(error_message)
                    return False  # Blockera kommandot
                else:
                    warning_message = (
                        f"🚨 **SISTA VARNING för `!{command}`!**\n"
                        f"Detta kommando kommer snart att tas bort helt.\n"
                        f"Växla till `/{command}` NU!"
                    )
                    await ctx.send(warning_message, delete_after=5)
                    return True
                    
            elif self.current_phase == 3:  # Critical only
                if command not in self._get_critical_commands():
                    error_message = (
                        f"🚫 **`!{command}` är borttaget!**\n"
                        f"Använd `/{command}` istället.\n"
                        f"Endast kritiska prefix commands fungerar nu."
                    )
                    await ctx.send(error_message)
                    return False
                else:
                    warning_message = (
                        f"⚡ **KRITISK VARNING för `!{command}`!**\n"
                        f"Detta är ett av de sista prefix commands som fungerar.\n"
                        f"Växla till `/{command}` omedelbart!"
                    )
                    await ctx.send(warning_message, delete_after=5)
                    return True
                    
            elif self.current_phase >= 4:  # Full migration
                final_message = (
                    f"🏁 **Prefix commands är helt borttagna!**\n"
                    f"Alla kommandon använder nu slash commands.\n"
                    f"Använd `/{command}` eller skriv `/help` för hjälp."
                )
                await ctx.send(final_message)
                return False
            
            return True  # Default: låt kommandot köras
            
        except Exception as e:
            print(f"[MIGRATION] Fel vid deprecation warning: {e}")
            return True  # Vid fel, låt kommandot köras
    
    def _get_non_critical_commands(self) -> List[str]:
        """Kommandon som stängs av först (fas 2)."""
        return [
            "chance",  # Simulering är inte kritisk
            "regel",   # Regelvisning finns i slash
            "help"     # Hjälp finns i slash
        ]
    
    def _get_critical_commands(self) -> List[str]:
        """Kritiska kommandon som behålls längst (fas 3)."""
        return [
            "roll",    # Grundläggande tärningsslag
            "ex",      # Exploderande tärningar
            "stats",   # Viktiga statistik
            "ask"      # AI-funktionalitet
        ]
    
    async def _has_received_dm(self, user_id: int, command: str) -> bool:
        """Kontrollera om användare redan fått DM för detta kommando."""
        try:
            dm_log_file = os.path.join(self.migration_data_path, "dm_sent_log.json")

            if os.path.exists(dm_log_file):
                with open(dm_log_file, 'r', encoding='utf-8') as f:
                    dm_log = json.load(f)
                    return f"{user_id}_{command}" in dm_log

        except FileNotFoundError as e:
            logger.debug(f"DM log file inte funnen, returnerar False: {e}")
        except json.JSONDecodeError as e:
            logger.warning(f"Kunde inte parsa DM log file, returnerar False: {e}")
        except Exception as e:
            logger.error(f"Oväntat fel vid kontroll av DM log, returnerar False: {e}")
        return False
    
    async def _mark_dm_sent(self, user_id: int, command: str):
        """Markera att DM har skickats för att undvika spam."""
        try:
            dm_log_file = os.path.join(self.migration_data_path, "dm_sent_log.json")
            
            dm_log = {}
            if os.path.exists(dm_log_file):
                with open(dm_log_file, 'r', encoding='utf-8') as f:
                    dm_log = json.load(f)
            
            dm_log[f"{user_id}_{command}"] = datetime.now().isoformat()
            
            with open(dm_log_file, 'w', encoding='utf-8') as f:
                json.dump(dm_log, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            print(f"[MIGRATION] Kunde inte markera DM som skickad: {e}")
    
    async def analyze_prefix_usage(self) -> Dict[str, Any]:
        """Analysera prefix command användning för att avgöra när nästa fas ska börja."""
        try:
            today = datetime.now().strftime('%Y%m%d')
            log_file = os.path.join(self.migration_data_path, f"prefix_usage_{today}.json")
            
            if not os.path.exists(log_file):
                return {
                    'total_usage': 0,
                    'unique_users': 0,
                    'command_breakdown': {},
                    'ready_for_next_phase': True
                }
            
            with open(log_file, 'r', encoding='utf-8') as f:
                logs = json.load(f)
            
            # Analysera senaste 24 timmarna
            cutoff_time = datetime.now() - timedelta(hours=24)
            recent_logs = [
                log for log in logs 
                if datetime.fromisoformat(log['timestamp']) > cutoff_time
            ]
            
            total_usage = len(recent_logs)
            unique_users = len(set(log['user_id'] for log in recent_logs))
            
            command_breakdown = {}
            for log in recent_logs:
                cmd = log['command']
                command_breakdown[cmd] = command_breakdown.get(cmd, 0) + 1
            
            # Bestäm om redo för nästa fas
            ready_for_next_phase = False
            
            if self.current_phase == 1:
                # Växla till fas 2 om <50 prefix användningar per dag
                ready_for_next_phase = total_usage < 50
                
            elif self.current_phase == 2:
                # Växla till fas 3 om <20 prefix användningar per dag
                ready_for_next_phase = total_usage < 20
                
            elif self.current_phase == 3:
                # Växla till fas 4 om <5 prefix användningar per dag
                ready_for_next_phase = total_usage < 5
            
            return {
                'total_usage': total_usage,
                'unique_users': unique_users,
                'command_breakdown': command_breakdown,
                'ready_for_next_phase': ready_for_next_phase,
                'current_phase': self.current_phase,
                'analysis_time': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"[MIGRATION] Fel vid analys av prefix användning: {e}")
            return {'error': str(e)}
    
    async def advance_migration_phase(self) -> bool:
        """Avancera till nästa migrationsfas om kriterierna är uppfyllda."""
        try:
            analysis = await self.analyze_prefix_usage()
            
            if analysis.get('ready_for_next_phase', False) and self.current_phase < 4:
                # Skapa backup innan fasförändring
                await self.create_migration_backup()
                
                next_phase = self.current_phase + 1
                self._set_current_phase(next_phase)
                
                # Logga fasförändringen
                phase_log = {
                    'from_phase': self.current_phase - 1,
                    'to_phase': next_phase,
                    'timestamp': datetime.now().isoformat(),
                    'trigger_analysis': analysis
                }
                
                phase_log_file = os.path.join(self.migration_data_path, "phase_changes.json")
                
                phase_logs = []
                if os.path.exists(phase_log_file):
                    with open(phase_log_file, 'r', encoding='utf-8') as f:
                        phase_logs = json.load(f)
                
                phase_logs.append(phase_log)
                
                with open(phase_log_file, 'w', encoding='utf-8') as f:
                    json.dump(phase_logs, f, ensure_ascii=False, indent=2)
                
                print(f"[MIGRATION] Avancerade till fas {next_phase}: {self.migration_phases[next_phase]}")
                
                # Skicka notification till administratörer
                await self._notify_admins_phase_change(next_phase, analysis)
                
                return True
                
            return False
            
        except Exception as e:
            print(f"[MIGRATION] Fel vid fas-avancering: {e}")
            return False
    
    async def _notify_admins_phase_change(self, new_phase: int, analysis: Dict[str, Any]):
        """Notifiera administratörer om fasförändring."""
        try:
            # TODO: Implementera admin notification
            # Detta skulle kunna skicka DM till server admins eller posta i admin channel
            pass
        except Exception as e:
            print(f"[MIGRATION] Kunde inte notifiera admins om fasförändring: {e}")
    
    async def create_migration_backup(self) -> str:
        """Skapa backup innan kritiska förändringar."""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_dir = os.path.join(self.backup_path, f"pre_phase_{self.current_phase + 1}_{timestamp}")
            os.makedirs(backup_dir, exist_ok=True)
            
            # Kopiera viktiga filer
            import shutil
            
            # Kopiera kommando-filer
            src_commands = os.path.join(self.base_path, "src", "commands")
            dst_commands = os.path.join(backup_dir, "commands")
            if os.path.exists(src_commands):
                shutil.copytree(src_commands, dst_commands)
            
            # Kopiera migration data
            dst_migration = os.path.join(backup_dir, "migration_data")
            shutil.copytree(self.migration_data_path, dst_migration)
            
            # Skapa backup metadata
            backup_info = {
                'backup_type': f'pre_phase_{self.current_phase + 1}',
                'created_at': datetime.now().isoformat(),
                'phase_from': self.current_phase,
                'phase_to': self.current_phase + 1,
                'backup_path': backup_dir
            }
            
            with open(os.path.join(backup_dir, 'backup_info.json'), 'w', encoding='utf-8') as f:
                json.dump(backup_info, f, ensure_ascii=False, indent=2)
            
            print(f"[MIGRATION] Backup skapad: {backup_dir}")
            return backup_dir
            
        except Exception as e:
            print(f"[MIGRATION] Kunde inte skapa backup: {e}")
            return ""
    
    async def emergency_rollback(self, target_phase: int = 1) -> bool:
        """Akut rollback till tidigare fas."""
        try:
            print(f"[MIGRATION] 🚨 EMERGENCY ROLLBACK till fas {target_phase}")
            
            # Skapa emergency backup först
            emergency_backup = os.path.join(self.backup_path, f"emergency_rollback_{int(time.time())}")
            os.makedirs(emergency_backup, exist_ok=True)
            
            # Logga rollback
            rollback_log = {
                'type': 'emergency_rollback',
                'from_phase': self.current_phase,
                'to_phase': target_phase,
                'timestamp': datetime.now().isoformat(),
                'reason': 'Emergency rollback initiated'
            }
            
            with open(os.path.join(emergency_backup, 'rollback_log.json'), 'w', encoding='utf-8') as f:
                json.dump(rollback_log, f, ensure_ascii=False, indent=2)
            
            # Sätt tillbaka fasen
            self._set_current_phase(target_phase)
            
            print(f"[MIGRATION] ✅ Emergency rollback genomförd till fas {target_phase}")
            return True
            
        except Exception as e:
            print(f"[MIGRATION] ❌ Emergency rollback misslyckades: {e}")
            return False
    
    def get_migration_status(self) -> Dict[str, Any]:
        """Hämta fullständig migrationsstatus."""
        try:
            analysis = asyncio.run(self.analyze_prefix_usage())
            
            return {
                'current_phase': self.current_phase,
                'phase_name': self.migration_phases[self.current_phase],
                'usage_analysis': analysis,
                'next_phase_ready': analysis.get('ready_for_next_phase', False),
                'total_phases': len(self.migration_phases),
                'migration_complete': self.current_phase >= 4,
                'status_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'error': f'Kunde inte hämta migrationsstatus: {e}',
                'current_phase': self.current_phase,
                'status_timestamp': datetime.now().isoformat()
            }


# Convenience functions för användning i bot
async def should_run_prefix_command(bot, ctx, command: str) -> bool:
    """Kontrollera om ett prefix command ska köras baserat på migrationsfas."""
    if not hasattr(bot, 'migration_finalizer'):
        bot.migration_finalizer = MigrationFinalizer(bot)
    
    finalizer = bot.migration_finalizer
    
    # Logga användningen
    await finalizer.log_prefix_usage(str(ctx.author.id), command, [])
    
    # Kontrollera om kommandot ska köras
    return await finalizer.send_deprecation_warning(ctx, command)

async def check_migration_advancement(bot):
    """Kontrollera om det är dags att avancera migrationsfas."""
    if not hasattr(bot, 'migration_finalizer'):
        bot.migration_finalizer = MigrationFinalizer(bot)
    
    await bot.migration_finalizer.advance_migration_phase()

# CLI script för manuell migration management
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Användning: python finalization_script.py [status|advance|rollback|backup]")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    # Skapa mock bot för standalone användning
    class MockBot:
        pass
    
    finalizer = MigrationFinalizer(MockBot())
    
    if command == "status":
        status = finalizer.get_migration_status()
        print(json.dumps(status, ensure_ascii=False, indent=2))
        
    elif command == "advance":
        result = asyncio.run(finalizer.advance_migration_phase())
        print(f"Fas-avancering: {'Genomförd' if result else 'Inte redo eller fel'}")
        
    elif command == "rollback":
        target_phase = int(sys.argv[2]) if len(sys.argv) > 2 else 1
        result = asyncio.run(finalizer.emergency_rollback(target_phase))
        print(f"Rollback till fas {target_phase}: {'Genomförd' if result else 'Misslyckades'}")
        
    elif command == "backup":
        backup_path = asyncio.run(finalizer.create_migration_backup())
        print(f"Backup skapad: {backup_path}")
        
    else:
        print(f"Okänt kommando: {command}")
        sys.exit(1)