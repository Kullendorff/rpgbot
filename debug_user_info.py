"""
Debug kommando för att visa användarinfo och roller.
"""

import discord
from discord import app_commands
from discord.ext import commands

@app_commands.command(name="debug_user", description="Visa all användarinfo för debugging")
@app_commands.describe(användare="Användare att visa info för (lämna tom för dig själv)")
async def debug_user_info(interaction: discord.Interaction, användare: discord.Member = None):
    """Debug användarinfo och permissions."""
    
    # Använd angiven användare eller den som kör kommandot
    user = användare if användare else interaction.user
    guild = interaction.guild
    
    # Basic user info
    target_name = user.display_name if user != interaction.user else "Din"
    embed = discord.Embed(
        title=f"🔍 {target_name} Användarinfo",
        color=discord.Color.blue()
    )
    
    embed.add_field(
        name="👤 Grundinfo",
        value=f"**Användare:** {user.mention}\n"
              f"**ID:** {user.id}\n"
              f"**Namn:** {user.name}#{user.discriminator}\n"
              f"**Display Name:** {user.display_name}",
        inline=False
    )
    
    # Discord permissions
    permissions = user.guild_permissions
    embed.add_field(
        name="🔧 Discord Permissions",
        value=f"**Manage Guild:** {permissions.manage_guild}\n"
              f"**Administrator:** {permissions.administrator}\n"
              f"**Manage Channels:** {permissions.manage_channels}\n"
              f"**Manage Messages:** {permissions.manage_messages}",
        inline=False
    )
    
    # All roles
    roles = [role.name for role in user.roles if role.name != "@everyone"]
    embed.add_field(
        name="🎭 Alla Roller",
        value=", ".join(roles) if roles else "Inga roller",
        inline=False
    )
    
    # Specific role checks
    has_gm_role = any(role.name == 'Game Master' for role in user.roles)
    has_admin_role = any(role.name == 'Admin' for role in user.roles)
    has_moderator_role = any(role.name == 'Moderator' for role in user.roles)
    
    embed.add_field(
        name="🎮 Specifika Rollkontroller",
        value=f"**Game Master:** {has_gm_role}\n"
              f"**Admin:** {has_admin_role}\n"
              f"**Moderator:** {has_moderator_role}",
        inline=False
    )
    
    # Guild info
    embed.add_field(
        name="🏰 Guild Info",
        value=f"**Guild:** {guild.name}\n"
              f"**Guild ID:** {guild.id}\n"
              f"**Owner:** {guild.owner.display_name if guild.owner else 'Okänd'}",
        inline=False
    )
    
    # Command permissions test
    can_use_gm_commands = permissions.manage_guild and has_gm_role
    embed.add_field(
        name="✅ Kommando Access Test",
        value=f"**Kan använda GM commands:** {can_use_gm_commands}\n"
              f"**Logik:** manage_guild ({permissions.manage_guild}) AND Game Master roll ({has_gm_role})",
        inline=False
    )
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

@app_commands.command(name="debug_user_id", description="Debug användarinfo via User ID")
@app_commands.describe(user_id="Discord User ID att undersöka")
async def debug_user_info_by_id(interaction: discord.Interaction, user_id: str):
    """Debug användarinfo via User ID."""
    
    # Validera User ID
    try:
        user_id_int = int(user_id)
        user = interaction.client.get_user(user_id_int)
        if not user:
            await interaction.response.send_message(
                f"❌ Kunde inte hitta användare med ID: {user_id}",
                ephemeral=True
            )
            return
    except ValueError:
        await interaction.response.send_message(
            "❌ Ogiltigt User ID. Måste vara ett nummer.",
            ephemeral=True
        )
        return
    
    guild = interaction.guild
    member = guild.get_member(user_id_int) if guild else None
    
    # Basic user info
    embed = discord.Embed(
        title=f"🔍 {user.display_name} Användarinfo (via ID)",
        color=discord.Color.blue()
    )
    
    embed.add_field(
        name="👤 Grundinfo",
        value=f"**Användare:** {user.mention}\n"
              f"**ID:** {user.id}\n"
              f"**Namn:** {user.name}#{user.discriminator}\n"
              f"**Display Name:** {user.display_name}",
        inline=False
    )
    
    if member:
        # Discord permissions (om användaren är medlem)
        permissions = member.guild_permissions
        embed.add_field(
            name="🔧 Discord Permissions",
            value=f"**Manage Guild:** {permissions.manage_guild}\n"
                  f"**Administrator:** {permissions.administrator}\n"
                  f"**Manage Channels:** {permissions.manage_channels}\n"
                  f"**Manage Messages:** {permissions.manage_messages}",
            inline=False
        )
        
        # All roles
        roles = [role.name for role in member.roles if role.name != "@everyone"]
        embed.add_field(
            name="🎭 Alla Roller",
            value=", ".join(roles) if roles else "Inga roller",
            inline=False
        )
        
        # Specific role checks
        has_gm_role = any(role.name == 'Game Master' for role in member.roles)
        has_admin_role = any(role.name == 'Admin' for role in member.roles)
        has_moderator_role = any(role.name == 'Moderator' for role in member.roles)
        
        embed.add_field(
            name="🎮 Specifika Rollkontroller",
            value=f"**Game Master:** {has_gm_role}\n"
                  f"**Admin:** {has_admin_role}\n"
                  f"**Moderator:** {has_moderator_role}",
            inline=False
        )
        
        # Command permissions test
        can_use_gm_commands = permissions.manage_guild and has_gm_role
        embed.add_field(
            name="✅ Kommando Access Test",
            value=f"**Kan använda GM commands:** {can_use_gm_commands}\n"
                  f"**Logik:** manage_guild ({permissions.manage_guild}) AND Game Master roll ({has_gm_role})",
            inline=False
        )
    else:
        embed.add_field(
            name="⚠️ Medlemsstatus",
            value="Användaren är inte medlem av denna server, eller så kan botten inte se dem.",
            inline=False
        )
    
    # Guild info
    if guild:
        embed.add_field(
            name="🏰 Guild Info",
            value=f"**Guild:** {guild.name}\n"
                  f"**Guild ID:** {guild.id}\n"
                  f"**Owner:** {guild.owner.display_name if guild.owner else 'Okänd'}",
            inline=False
        )
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

def register_debug_command(bot):
    """Registrera debug kommandona."""
    bot.tree.add_command(debug_user_info)
    bot.tree.add_command(debug_user_info_by_id)
    print("Debug kommandon '/debug_user' och '/debug_user_id' registrerade.")