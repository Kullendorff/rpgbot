"""
Slash commands for managing user comment settings - GM ONLY.
"""

import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional

def register_slash_comment_commands(bot: commands.Bot, user_settings, comment_generator, color_handler):
    """Register slash commands for comment settings - GM access only."""
    
    # Comment settings group - GM ONLY
    comment_group = app_commands.Group(name="kommentarer", description="Hantera spelares kommentarer (endast GM)")
    
    @comment_group.command(name="aktivera", description="Aktivera kommentarer för en spelare (endast GM)")
    @app_commands.describe(spelare="Spelare att aktivera kommentarer för")
    @app_commands.default_permissions(manage_guild=True)
    async def enable_comments(interaction: discord.Interaction, spelare: discord.Member):
        """Enable comments for a player - GM only."""
        # KRITISK: GM-kontroll
        if not any(role.name == 'Game Master' for role in interaction.user.roles):
            await interaction.response.send_message(
                "Du behöver Game Master-roll för detta kommando.", 
                ephemeral=True
            )
            return
        
        user_id = str(spelare.id)
        success = user_settings.set_comments_enabled(user_id, True)
        
        if success:
            settings = user_settings.get_user_settings(user_id)
            style = settings["comment_style"]
            frequency = int(settings["comment_frequency"] * 100)
            
            embed = discord.Embed(
                title="✅ Kommentarer Aktiverade",
                description=f"Kommentarer aktiverade för {spelare.display_name}!\n\n"
                           f"**Stil:** {style}\n"
                           f"**Frekvens:** {frequency}% av slag\n\n"
                           f"Använd `/kommentarer stil` för att ändra stil.\n"
                           f"Använd `/kommentarer frekvens` för att ändra frekvens.",
                color=discord.Color.green()
            )
        else:
            embed = discord.Embed(
                title="❌ Fel",
                description=f"Kunde inte aktivera kommentarer för {spelare.display_name}. Försök igen.",
                color=discord.Color.red()
            )
        
        await interaction.response.send_message(embed=embed)
    
    @comment_group.command(name="inaktivera", description="Inaktivera kommentarer för en spelare (endast GM)")
    @app_commands.describe(spelare="Spelare att inaktivera kommentarer för")
    @app_commands.default_permissions(manage_guild=True)
    async def disable_comments(interaction: discord.Interaction, spelare: discord.Member):
        """Disable comments for a player - GM only."""
        # KRITISK: GM-kontroll
        if not any(role.name == 'Game Master' for role in interaction.user.roles):
            await interaction.response.send_message(
                "Du behöver Game Master-roll för detta kommando.", 
                ephemeral=True
            )
            return
        
        user_id = str(spelare.id)
        success = user_settings.set_comments_enabled(user_id, False)
        
        if success:
            embed = discord.Embed(
                title="🔇 Kommentarer Inaktiverade",
                description=f"Kommentarer inaktiverade för {spelare.display_name}.\n\n"
                           "Använd `/kommentarer aktivera` för att aktivera dem igen.",
                color=discord.Color.orange()
            )
        else:
            embed = discord.Embed(
                title="❌ Fel", 
                description=f"Kunde inte inaktivera kommentarer för {spelare.display_name}. Försök igen.",
                color=discord.Color.red()
            )
        
        await interaction.response.send_message(embed=embed)
    
    @comment_group.command(name="stil", description="Ändra kommentarstil för en spelare (endast GM)")
    @app_commands.describe(
        spelare="Spelare att ändra stil för",
        stil="Välj kommentarstil"
    )
    @app_commands.choices(stil=[
        app_commands.Choice(name="Umnatak (syrlig)", value="umnatak"),
        app_commands.Choice(name="Uppmuntrande", value="encouraging"), 
        app_commands.Choice(name="Dramatisk", value="dramatic"),
        app_commands.Choice(name="Neutral", value="neutral")
    ])
    @app_commands.default_permissions(manage_guild=True)
    async def set_comment_style(interaction: discord.Interaction, spelare: discord.Member, stil: str):
        """Set comment style for a player - GM only."""
        # KRITISK: GM-kontroll
        if not any(role.name == 'Game Master' for role in interaction.user.roles):
            await interaction.response.send_message(
                "Du behöver Game Master-roll för detta kommando.", 
                ephemeral=True
            )
            return
        
        user_id = str(spelare.id)
        success = user_settings.set_comment_style(user_id, stil)
        
        if success:
            style_names = {
                "umnatak": "Umnatak (syrlig)",
                "encouraging": "Uppmuntrande", 
                "dramatic": "Dramatisk",
                "neutral": "Neutral"
            }
            
            embed = discord.Embed(
                title="🎭 Kommentarstil Uppdaterad",
                description=f"Kommentarstil för {spelare.display_name} ändrad till: **{style_names[stil]}**\n\n"
                           f"Aktivera kommentarer med `/kommentarer aktivera` om de inte redan är på.",
                color=discord.Color.blue()
            )
        else:
            embed = discord.Embed(
                title="❌ Fel",
                description=f"Kunde inte ändra kommentarstil för {spelare.display_name}. Försök igen.",
                color=discord.Color.red()
            )
        
        await interaction.response.send_message(embed=embed)
    
    @comment_group.command(name="frekvens", description="Ändra kommentarfrekvens för en spelare (endast GM)")
    @app_commands.describe(
        spelare="Spelare att ändra frekvens för",
        procent="Frekvens i procent (10-50)"
    )
    @app_commands.default_permissions(manage_guild=True)
    async def set_comment_frequency(interaction: discord.Interaction, spelare: discord.Member, procent: int):
        """Set comment frequency for a player - GM only."""
        # KRITISK: GM-kontroll
        if not any(role.name == 'Game Master' for role in interaction.user.roles):
            await interaction.response.send_message(
                "Du behöver Game Master-roll för detta kommando.", 
                ephemeral=True
            )
            return
        
        if not (10 <= procent <= 50):
            embed = discord.Embed(
                title="❌ Ogiltig Frekvens",
                description="Frekvensen måste vara mellan 10% och 50%.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        user_id = str(spelare.id)
        frequency = procent / 100.0
        success = user_settings.set_comment_frequency(user_id, frequency)
        
        if success:
            embed = discord.Embed(
                title="📊 Kommentarfrekvens Uppdaterad",
                description=f"Kommentarfrekvens för {spelare.display_name} ändrad till: **{procent}%**\n\n"
                           f"De kommer få kommentarer på cirka {procent}% av sina tärningsslag.",
                color=discord.Color.blue()
            )
        else:
            embed = discord.Embed(
                title="❌ Fel",
                description=f"Kunde inte ändra kommentarfrekvens för {spelare.display_name}. Försök igen.",
                color=discord.Color.red()
            )
        
        await interaction.response.send_message(embed=embed)
    
    @comment_group.command(name="status", description="Visa kommentarinställningar för en spelare (endast GM)")
    @app_commands.describe(spelare="Spelare att visa inställningar för")
    @app_commands.default_permissions(manage_guild=True)
    async def show_comment_status(interaction: discord.Interaction, spelare: discord.Member):
        """Show player's current comment settings - GM only."""
        # KRITISK: GM-kontroll
        if not any(role.name == 'Game Master' for role in interaction.user.roles):
            await interaction.response.send_message(
                "Du behöver Game Master-roll för detta kommando.", 
                ephemeral=True
            )
            return
        
        user_id = str(spelare.id)
        settings = user_settings.get_user_settings(user_id)
        
        style_names = {
            "umnatak": "Umnatak (syrlig)",
            "encouraging": "Uppmuntrande",
            "dramatic": "Dramatisk", 
            "neutral": "Neutral"
        }
        
        enabled = settings["comments_enabled"]
        style = settings["comment_style"]
        frequency = int(settings["comment_frequency"] * 100)
        
        status_emoji = "✅" if enabled else "🔇"
        status_text = "Aktiverade" if enabled else "Inaktiverade"
        
        embed = discord.Embed(
            title=f"{status_emoji} {spelare.display_name}s Kommentarinställningar",
            color=discord.Color.green() if enabled else discord.Color.grey()
        )
        
        embed.add_field(
            name="Status",
            value=status_text,
            inline=True
        )
        
        embed.add_field(
            name="Stil", 
            value=style_names.get(style, style),
            inline=True
        )
        
        embed.add_field(
            name="Frekvens",
            value=f"{frequency}%",
            inline=True
        )
        
        if not enabled:
            embed.add_field(
                name="💡 Tips",
                value=f"Använd `/kommentarer aktivera spelare:{spelare.mention}` för att aktivera kommentarer!",
                inline=False
            )
        
        await interaction.response.send_message(embed=embed)
    
    @comment_group.command(name="lista", description="Visa alla spelares kommentarinställningar (endast GM)")
    @app_commands.default_permissions(manage_guild=True)
    async def list_all_comments(interaction: discord.Interaction):
        """List all players' comment settings - GM only."""
        # KRITISK: GM-kontroll
        if not any(role.name == 'Game Master' for role in interaction.user.roles):
            await interaction.response.send_message(
                "Du behöver Game Master-roll för detta kommando.", 
                ephemeral=True
            )
            return
        
        # Get all users with settings
        all_settings = user_settings.settings_cache
        
        if not all_settings:
            embed = discord.Embed(
                title="📝 Kommentarinställningar",
                description="Inga spelare har kommentarinställningar än.",
                color=discord.Color.grey()
            )
            await interaction.response.send_message(embed=embed)
            return
        
        embed = discord.Embed(
            title="📝 Alla Kommentarinställningar",
            color=discord.Color.blue()
        )
        
        for user_id, settings in all_settings.items():
            try:
                user = bot.get_user(int(user_id))
                display_name = user.display_name if user else f"User {user_id}"
                
                enabled = settings["comments_enabled"]
                style = settings["comment_style"]
                frequency = int(settings["comment_frequency"] * 100)
                
                status = "✅ På" if enabled else "🔇 Av"
                
                embed.add_field(
                    name=display_name,
                    value=f"{status} | {style} | {frequency}%",
                    inline=True
                )
            except Exception as e:
                print(f"Error processing user {user_id}: {e}")
        
        await interaction.response.send_message(embed=embed)
    
    # Global comment controls
    @comment_group.command(name="global_av", description="Stäng av alla kommentarer globalt (endast GM)")
    @app_commands.default_permissions(manage_guild=True)
    async def global_disable(interaction: discord.Interaction):
        """Globally disable all comments - GM only."""
        # KRITISK: GM-kontroll
        if not any(role.name == 'Game Master' for role in interaction.user.roles):
            await interaction.response.send_message(
                "Du behöver Game Master-roll för detta kommando.", 
                ephemeral=True
            )
            return
        
        # Disable for all users
        count = 0
        for user_id in user_settings.settings_cache.keys():
            if user_settings.set_comments_enabled(user_id, False):
                count += 1
        
        embed = discord.Embed(
            title="🔇 Globalt Kommentarstopp",
            description=f"Kommentarer inaktiverade för {count} spelare.\n\n"
                       "Använd `/kommentarer aktivera` för att aktivera individuellt igen.",
            color=discord.Color.orange()
        )
        
        await interaction.response.send_message(embed=embed)
    
    # Register the group
    bot.tree.add_command(comment_group)