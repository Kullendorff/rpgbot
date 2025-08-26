"""
Debug script för att testa permissions och roller.
"""

import discord
from discord import app_commands
from discord.ext import commands

# Skapa en temporär debug-command
@app_commands.command(name="debug_permissions", description="Debug permissions och roller")
@app_commands.default_permissions(manage_guild=True)
async def debug_permissions(interaction: discord.Interaction):
    """Debug permissions."""
    
    # Kolla permissions
    has_manage_guild = interaction.user.guild_permissions.manage_guild
    
    # Lista alla roller
    user_roles = [role.name for role in interaction.user.roles]
    
    # Kolla specifik Game Master roll
    has_gm_role = any(role.name == 'Game Master' for role in interaction.user.roles)
    
    embed = discord.Embed(
        title="🔍 Permission Debug",
        color=discord.Color.blue()
    )
    
    embed.add_field(
        name="Discord Permissions",
        value=f"Manage Guild: {has_manage_guild}",
        inline=False
    )
    
    embed.add_field(
        name="Alla dina roller",
        value=", ".join(user_roles) if user_roles else "Inga roller",
        inline=False
    )
    
    embed.add_field(
        name="Game Master roll check",
        value=f"Har 'Game Master' roll: {has_gm_role}",
        inline=False
    )
    
    # Kolla om kommandot ens syns
    embed.add_field(
        name="Status",
        value="Om du ser detta meddelande så fungerar Discord permissions!",
        inline=False
    )
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

print("Debug command skapad. Lägg till den i main.py temporärt.")