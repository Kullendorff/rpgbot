"""
Hemliga manipulation commands - endast GM.
Helt osynliga för alla spelare.
"""

import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional

def register_slash_manipulation_commands(bot: commands.Bot, manipulation_manager, color_handler):
    """Register secret manipulation commands - GM ONLY."""
    
    # Manipulation group - HEMLIGT GM SYSTEM
    manip_group = app_commands.Group(name="manipulation", description="Hemligt tärningsmanipulation (endast GM)")
    
    @manip_group.command(name="aktivera", description="Aktivera manipulation för spelare (hemligt)")
    @app_commands.describe(
        spelare="Spelare att manipulera",
        typ="Typ av manipulation"
    )
    @app_commands.choices(typ=[
        app_commands.Choice(name="Lycka (automatisk framgång)", value="lycka"),
        app_commands.Choice(name="Olycka (automatisk misslyckande)", value="olycka")
    ])
    @app_commands.default_permissions(manage_guild=True)
    async def activate_player_manipulation(
        interaction: discord.Interaction,
        spelare: discord.Member,
        typ: str
    ):
        """Aktivera hemlig manipulation för spelare."""
        # KRITISK: GM-kontroll
        if not any(role.name == 'Game Master' for role in interaction.user.roles):
            await interaction.response.send_message(
                "Du behöver Game Master-roll för detta kommando.", 
                ephemeral=True
            )
            return
        
        success = manipulation_manager.set_player_manipulation(
            str(spelare.id), typ, str(interaction.user.id)
        )
        
        if success:
            type_names = {
                "lycka": "Lycka (automatisk framgång)",
                "olycka": "Olycka (automatisk misslyckande)"
            }
            
            embed = discord.Embed(
                title="🎭 Hemlig Manipulation Aktiverad",
                description=f"**Spelare:** {spelare.display_name}\n"
                           f"**Typ:** {type_names[typ]}\n\n"
                           f"⚠️ **HEMLIGT** - Spelaren vet inte om detta!\n"
                           f"Alla tärningsslag med målvärde kommer påverkas automatiskt.",
                color=discord.Color.dark_purple()
            )
            
            embed.add_field(
                name="🔍 Vad händer nu?",
                value=f"• {spelare.display_name}s slag manipuleras automatiskt\n"
                      f"• Ingen visuell indikation för spelaren\n"
                      f"• Endast slag med målvärde påverkas\n"
                      f"• Använd `/manipulation status` för att se alla aktiva",
                inline=False
            )
        else:
            embed = discord.Embed(
                title="❌ Manipulation Misslyckades",
                description="Kunde inte aktivera manipulation. Kontrollera parametrar.",
                color=discord.Color.red()
            )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @manip_group.command(name="aktivera_gm", description="Aktivera manipulation för dig själv (hemligt)")
    @app_commands.describe(typ="Typ av GM-manipulation")
    @app_commands.choices(typ=[
        app_commands.Choice(name="Gudomlig (du lyckas alltid)", value="gudomlig"),
        app_commands.Choice(name="Förbannelse (du misslyckas alltid)", value="förbannelse")
    ])
    @app_commands.default_permissions(manage_guild=True)
    async def activate_gm_manipulation(
        interaction: discord.Interaction,
        typ: str
    ):
        """Aktivera hemlig manipulation för GM själv."""
        # KRITISK: GM-kontroll
        if not any(role.name == 'Game Master' for role in interaction.user.roles):
            await interaction.response.send_message(
                "Du behöver Game Master-roll för detta kommando.", 
                ephemeral=True
            )
            return
        
        success = manipulation_manager.set_gm_manipulation(
            str(interaction.user.id), typ
        )
        
        if success:
            type_names = {
                "gudomlig": "Gudomlig (automatisk framgång)",
                "förbannelse": "Förbannelse (automatisk misslyckande)"
            }
            
            embed = discord.Embed(
                title="⚡ GM Manipulation Aktiverad",
                description=f"**Typ:** {type_names[typ]}\n\n"
                           f"🎭 Dina egna tärningsslag kommer nu manipuleras automatiskt!\n"
                           f"Endast slag med målvärde påverkas.",
                color=discord.Color.gold()
            )
            
            embed.add_field(
                name="🎲 Vad händer?",
                value=f"• Dina slag manipuleras för att {'lyckas' if typ == 'gudomlig' else 'misslyckas'}\n"
                      f"• Helt hemligt - ingen annan ser manipulation\n"
                      f"• Fungerar på roll, ex, count commands\n"
                      f"• Använd `/manipulation inaktivera_gm` för att stänga av",
                inline=False
            )
        else:
            embed = discord.Embed(
                title="❌ GM Manipulation Misslyckades",
                description="Kunde inte aktivera GM manipulation.",
                color=discord.Color.red()
            )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @manip_group.command(name="inaktivera", description="Inaktivera manipulation för spelare")
    @app_commands.describe(spelare="Spelare att ta bort manipulation för")
    @app_commands.default_permissions(manage_guild=True)
    async def deactivate_player_manipulation(
        interaction: discord.Interaction,
        spelare: discord.Member
    ):
        """Inaktivera manipulation för spelare."""
        # KRITISK: GM-kontroll
        if not any(role.name == 'Game Master' for role in interaction.user.roles):
            await interaction.response.send_message(
                "Du behöver Game Master-roll för detta kommando.", 
                ephemeral=True
            )
            return
        
        success = manipulation_manager.remove_manipulation(str(spelare.id))
        
        if success:
            embed = discord.Embed(
                title="✅ Manipulation Inaktiverad",
                description=f"Manipulation borttagen för {spelare.display_name}.\n"
                           f"Deras tärningsslag är nu normala igen.",
                color=discord.Color.green()
            )
        else:
            embed = discord.Embed(
                title="ℹ️ Ingen Manipulation",
                description=f"{spelare.display_name} hade ingen aktiv manipulation.",
                color=discord.Color.grey()
            )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @manip_group.command(name="inaktivera_gm", description="Inaktivera din egen manipulation")
    @app_commands.default_permissions(manage_guild=True)
    async def deactivate_gm_manipulation(interaction: discord.Interaction):
        """Inaktivera GM:s egen manipulation."""
        # KRITISCH: GM-kontroll
        if not any(role.name == 'Game Master' for role in interaction.user.roles):
            await interaction.response.send_message(
                "Du behöver Game Master-roll för detta kommando.", 
                ephemeral=True
            )
            return
        
        success = manipulation_manager.remove_manipulation(str(interaction.user.id))
        
        if success:
            embed = discord.Embed(
                title="✅ GM Manipulation Inaktiverad",
                description="Din manipulation är nu borttagen.\n"
                           "Dina tärningsslag är normala igen.",
                color=discord.Color.green()
            )
        else:
            embed = discord.Embed(
                title="ℹ️ Ingen GM Manipulation",
                description="Du hade ingen aktiv manipulation.",
                color=discord.Color.grey()
            )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @manip_group.command(name="status", description="Visa alla aktiva manipulationer (hemligt)")
    @app_commands.default_permissions(manage_guild=True)
    async def show_manipulation_status(interaction: discord.Interaction):
        """Visa alla aktiva manipulationer - endast GM."""
        # KRITISK: GM-kontroll
        if not any(role.name == 'Game Master' for role in interaction.user.roles):
            await interaction.response.send_message(
                "Du behöver Game Master-roll för detta kommando.", 
                ephemeral=True
            )
            return
        
        all_manipulations = manipulation_manager.get_all_manipulations()
        
        if not all_manipulations:
            embed = discord.Embed(
                title="🎭 Aktiva Manipulationer",
                description="Inga aktiva manipulationer för tillfället.",
                color=discord.Color.grey()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        embed = discord.Embed(
            title="🎭 Aktiva Hemliga Manipulationer",
            description="Alla manipulationer som påverkar tärningsslag:",
            color=discord.Color.dark_purple()
        )
        
        type_names = {
            "lycka": "🍀 Lycka (framgång)",
            "olycka": "💀 Olycka (misslyckande)", 
            "gudomlig": "⚡ Gudomlig (GM framgång)",
            "förbannelse": "🔥 Förbannelse (GM misslyckande)"
        }
        
        for user_id, data in all_manipulations.items():
            try:
                user = bot.get_user(int(user_id))
                display_name = user.display_name if user else f"User {user_id}"
                
                manipulation_type = data["type"]
                rolls_affected = data["rolls_affected"]
                activated_at = data["activated_at"][:10]  # Just date
                
                type_display = type_names.get(manipulation_type, manipulation_type)
                
                embed.add_field(
                    name=f"{type_display}",
                    value=f"**Spelare:** {display_name}\n"
                          f"**Aktiv sedan:** {activated_at}\n"
                          f"**Slag påverkade:** {rolls_affected}",
                    inline=True
                )
            except Exception as e:
                print(f"Error displaying manipulation for {user_id}: {e}")
        
        embed.add_field(
            name="🔍 Påminnelse",
            value="Dessa manipulationer är helt hemliga!\n"
                  "Spelarna vet inte att deras slag påverkas.",
            inline=False
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @manip_group.command(name="rensa_alla", description="Ta bort alla aktiva manipulationer")
    @app_commands.default_permissions(manage_guild=True)
    async def clear_all_manipulations(interaction: discord.Interaction):
        """Rensa alla aktiva manipulationer - emergency stop."""
        # KRITISK: GM-kontroll
        if not any(role.name == 'Game Master' for role in interaction.user.roles):
            await interaction.response.send_message(
                "Du behöver Game Master-roll för detta kommando.", 
                ephemeral=True
            )
            return
        
        count = manipulation_manager.clear_all_manipulations()
        
        embed = discord.Embed(
            title="🧹 Alla Manipulationer Rensade",
            description=f"Tog bort {count} aktiva manipulationer.\n"
                       "Alla tärningsslag är nu normala igen.",
            color=discord.Color.orange()
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    # Register the group
    bot.tree.add_command(manip_group)