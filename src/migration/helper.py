"""
Migration helper för säker konvertering från prefix till slash commands.
Innehåller utilities för logging, defer handling, och parameter conversion.
"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional, Union
import discord
from discord.ext import commands
from discord import app_commands

class MigrationHelper:
    """Hjälper med säker migration från prefix till slash commands."""
    
    def __init__(self, embed_factory):
        """Initialisera med embed factory för konsekvent UI."""
        self.embed_factory = embed_factory
        self.logger = logging.getLogger('migration')
        
    async def safe_defer(self, interaction: discord.Interaction, ephemeral: bool = False):
        """
        Säkert defer för slash commands som kan ta tid.
        Använd detta för alla operationer som kan ta >3 sekunder.
        """
        try:
            if not interaction.response.is_done():
                await interaction.response.defer(ephemeral=ephemeral)
                self.logger.info(f"Deferred interaction for user {interaction.user.id}")
        except Exception as e:
            self.logger.error(f"Failed to defer interaction: {e}")
    
    async def send_response(self, interaction: discord.Interaction, embed: discord.Embed = None, content: str = None):
        """
        Skicka svar på ett säkert sätt, oavsett om interaction redan är deferred.
        """
        try:
            if interaction.response.is_done():
                # Interaction redan svarad (deferred), använd followup
                await interaction.followup.send(embed=embed, content=content)
            else:
                # Kan svara direkt
                await interaction.response.send_message(embed=embed, content=content)
        except Exception as e:
            self.logger.error(f"Failed to send response: {e}")
            # Fallback attempt
            try:
                await interaction.followup.send(embed=embed, content=content)
            except:
                pass
    
    def parse_dice_flags(self, flags_str: str) -> Dict[str, bool]:
        """
        Konvertera gamla flaggor från prefix commands till boolean parametrar.
        
        Args:
            flags_str: String med flaggor som "--de --ryttare"
            
        Returns:
            Dict med parsed flaggor: {"demon": True, "ryttare": True}
        """
        if not flags_str:
            return {}
            
        flags = {}
        flags_str = flags_str.lower()
        
        # Mappa gamla flaggor till nya parametrar
        flag_mapping = {
            "--de": "demon",
            "--ryttare": "mounted", 
            "--djur": "quadruped",
            "--mp": "malpunkter"
        }
        
        for old_flag, new_param in flag_mapping.items():
            flags[new_param] = old_flag in flags_str
            
        return flags
    
    async def log_command_usage(self, interaction: discord.Interaction, command_name: str, 
                              params: Dict[str, Any], execution_time: float = None):
        """
        Logga slash command användning för monitoring och debugging.
        """
        log_data = {
            "user_id": interaction.user.id,
            "user_name": interaction.user.display_name,
            "command": command_name,
            "parameters": params,
            "guild_id": interaction.guild_id if interaction.guild else None,
            "execution_time": execution_time
        }
        
        self.logger.info(f"Slash command executed: {log_data}")
    
    def validate_dice_notation(self, dice_str: str) -> bool:
        """
        Validera dice notation för autocomplete och input validation.
        """
        import re
        # Regex för giltiga EON dice patterns
        pattern = r'^(\d{1,3})d(\d{1,3})([+-]\d{1,3})?$'
        return bool(re.match(pattern, dice_str.lower().replace(' ', '')))
    
    async def create_error_response(self, user_id: int, error_msg: str, suggestion: str = None) -> discord.Embed:
        """Skapa standardiserat felmeddelande."""
        return self.embed_factory.error_message(user_id, error_msg, suggestion)


class SlashCommandDecorator:
    """Decorator för att automatisera vanliga slash command patterns."""
    
    def __init__(self, helper: MigrationHelper):
        self.helper = helper
    
    def auto_defer(self, timeout_seconds: float = 3.0):
        """
        Decorator som automatiskt defer:ar commands som kan ta tid.
        
        Args:
            timeout_seconds: Tid innan auto-defer aktiveras
        """
        def decorator(func):
            async def wrapper(interaction: discord.Interaction, *args, **kwargs):
                start_time = time.time()
                
                # Starta en timer för auto-defer
                defer_task = asyncio.create_task(
                    self._auto_defer_after_timeout(interaction, timeout_seconds)
                )
                
                try:
                    # Kör den faktiska kommandot
                    result = await func(interaction, *args, **kwargs)
                    execution_time = time.time() - start_time
                    
                    # Logga användning
                    await self.helper.log_command_usage(
                        interaction, func.__name__, kwargs, execution_time
                    )
                    
                    return result
                finally:
                    # Avbryt defer-timer
                    defer_task.cancel()
                    try:
                        await defer_task
                    except asyncio.CancelledError:
                        pass
                        
            return wrapper
        return decorator
    
    async def _auto_defer_after_timeout(self, interaction: discord.Interaction, timeout: float):
        """Automatisk defer efter timeout."""
        await asyncio.sleep(timeout)
        await self.helper.safe_defer(interaction)


# Globala utility funktioner för autocomplete
async def dice_autocomplete(interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
    """
    Autocomplete för dice notation med vanliga EON-kombinationer.
    """
    # Vanliga EON dice kombinationer
    common_dice = [
        "1d6", "2d6", "3d6", "4d6", "5d6", "6d6",
        "1d10", "2d10", "3d10", "4d10", "5d10",
        "1d20", "2d20", "3d20",
        "1d100", "2d100",
        "3d6+1", "3d6+2", "3d6+3", "3d6-1", "3d6-2",
        "4d6+1", "4d6+2", "4d6-1", "4d6-2"
    ]
    
    # Filtrera baserat på användarens input
    if current:
        matching = [dice for dice in common_dice if dice.startswith(current.lower())]
    else:
        matching = common_dice[:10]  # Visa första 10 som default
    
    # Begränsa till Discord's max 25 choices
    return [
        app_commands.Choice(name=dice, value=dice) 
        for dice in matching[:25]
    ]

async def target_value_autocomplete(interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
    """
    Autocomplete för vanliga målvärden i EON.
    """
    common_targets = ["6", "7", "8", "9", "10", "11", "12", "13", "14", "15", "16", "17", "18", "19", "20"]
    
    if current:
        matching = [target for target in common_targets if target.startswith(current)]
    else:
        matching = common_targets[:10]
    
    return [
        app_commands.Choice(name=f"Målvärde {target}", value=target)
        for target in matching[:25]
    ]