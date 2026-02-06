"""
Hemliga manipulation commands - endast GM.
Helt osynliga för alla spelare.
"""

import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional, List

# Trip19 kampanj - fasta spelare
TRIP19_AGENTS = [
    ("368410767189606401", "Mac", "Marcus Riley"),
    ("197809169296916480", "Trench", "Sam Novak"),
    ("223183062882713600", "Scalpel", "Dr. Hanna Engler"),
    ("680064176227352610", "Sparky", "Kai Zhang"),
    ("477800979295633409", "Sullivan", "Father Michael"),
]

def register_slash_manipulation_commands(bot: commands.Bot, manipulation_manager, color_handler):
    """Register secret manipulation commands - GM ONLY."""

    # Autocomplete function for Trip19 agents
    async def agent_autocomplete(
        interaction: discord.Interaction,
        current: str
    ) -> List[app_commands.Choice[str]]:
        """Autocomplete för Trip19-agenter."""
        if current:
            # Filter based on callsign or name
            matching = [
                (user_id, callsign, name)
                for user_id, callsign, name in TRIP19_AGENTS
                if current.lower() in callsign.lower() or current.lower() in name.lower()
            ]
        else:
            matching = TRIP19_AGENTS

        return [
            app_commands.Choice(name=f"{callsign} ({name})", value=user_id)
            for user_id, callsign, name in matching[:25]
        ]

    # Manipulation group - HEMLIGT GM SYSTEM
    manip_group = app_commands.Group(name="manipulation", description="Hemligt tärningsmanipulation (endast GM)")

    @manip_group.command(name="aktivera", description="Aktivera manipulation för spelare (hemligt)")
    @app_commands.describe(
        agent="Trip19 agent (autocomplete)",
        typ="Typ av manipulation"
    )
    @app_commands.autocomplete(agent=agent_autocomplete)
    @app_commands.choices(typ=[
        app_commands.Choice(name="Lycka (automatisk framgång)", value="lycka"),
        app_commands.Choice(name="Olycka (automatisk misslyckande)", value="olycka")
    ])
    @app_commands.default_permissions(manage_guild=True)
    async def activate_player_manipulation(
        interaction: discord.Interaction,
        agent: str,
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

        # agent is now user_id from autocomplete
        user_id = agent

        # Fetch user info for display
        try:
            user = await bot.fetch_user(int(user_id))
            display_name = f"{user.display_name} ({user.name})"
        except:
            # Fallback to finding in TRIP19_AGENTS
            agent_info = next((cs for uid, cs, name in TRIP19_AGENTS if uid == user_id), None)
            display_name = agent_info if agent_info else f"User {user_id}"

        success = manipulation_manager.set_player_manipulation(
            user_id, typ, str(interaction.user.id)
        )

        if success:
            type_names = {
                "lycka": "Lycka (automatisk framgång)",
                "olycka": "Olycka (automatisk misslyckande)"
            }

            embed = discord.Embed(
                title="🎭 Hemlig Manipulation Aktiverad",
                description=f"**Spelare:** {display_name}\n"
                           f"**Typ:** {type_names[typ]}\n\n"
                           f"⚠️ **HEMLIGT** - Spelaren vet inte om detta!\n"
                           f"Alla tärningsslag med målvärde kommer påverkas automatiskt.",
                color=discord.Color.dark_purple()
            )

            embed.add_field(
                name="🔍 Vad händer nu?",
                value=f"• {display_name}s slag manipuleras automatiskt\n"
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
    
    @manip_group.command(name="aktivera_id", description="Aktivera manipulation via User ID (hemligt)")
    @app_commands.describe(
        user_id="Discord User ID (högerklicka på användare > Kopiera Användar-ID)",
        typ="Typ av manipulation"
    )
    @app_commands.choices(typ=[
        app_commands.Choice(name="Lycka (automatisk framgång)", value="lycka"),
        app_commands.Choice(name="Olycka (automatisk misslyckande)", value="olycka")
    ])
    @app_commands.default_permissions(manage_guild=True)
    async def activate_player_manipulation_by_id(
        interaction: discord.Interaction,
        user_id: str,
        typ: str
    ):
        """Aktivera hemlig manipulation för spelare via User ID."""
        # KRITISK: GM-kontroll
        if not any(role.name == 'Game Master' for role in interaction.user.roles):
            await interaction.response.send_message(
                "Du behöver Game Master-roll för detta kommando.", 
                ephemeral=True
            )
            return
        
        # Validera User ID
        try:
            user_id_int = int(user_id)
            user = bot.get_user(user_id_int)
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
        
        success = manipulation_manager.set_player_manipulation(
            user_id, typ, str(interaction.user.id)
        )
        
        if success:
            type_names = {
                "lycka": "Lycka (automatisk framgång)",
                "olycka": "Olycka (automatisk misslyckande)"
            }
            
            embed = discord.Embed(
                title="🎭 Hemlig Manipulation Aktiverad (via ID)",
                description=f"**Spelare:** {user.display_name} ({user.name})\n"
                           f"**User ID:** {user_id}\n"
                           f"**Typ:** {type_names[typ]}\n\n"
                           f"⚠️ **HEMLIGT** - Spelaren vet inte om detta!\n"
                           f"Alla tärningsslag med målvärde kommer påverkas automatiskt.",
                color=discord.Color.dark_purple()
            )
            
            embed.add_field(
                name="🔍 Vad händer nu?",
                value=f"• {user.display_name}s slag manipuleras automatiskt\n"
                      f"• Ingen visuell indikation för spelaren\n"
                      f"• Endast slag med målvärde påverkas\n"
                      f"• Använd `/manipulation status` för att se alla aktiva",
                inline=False
            )
        else:
            embed = discord.Embed(
                title="❌ Manipulation Misslyckades",
                description=f"Kunde inte aktivera manipulation för User ID: {user_id}",
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
    @app_commands.describe(agent="Trip19 agent (autocomplete)")
    @app_commands.autocomplete(agent=agent_autocomplete)
    @app_commands.default_permissions(manage_guild=True)
    async def deactivate_player_manipulation(
        interaction: discord.Interaction,
        agent: str
    ):
        """Inaktivera manipulation för spelare."""
        # KRITISK: GM-kontroll
        if not any(role.name == 'Game Master' for role in interaction.user.roles):
            await interaction.response.send_message(
                "Du behöver Game Master-roll för detta kommando.",
                ephemeral=True
            )
            return

        # agent is now user_id from autocomplete
        user_id = agent

        # Fetch user info for display
        try:
            user = await bot.fetch_user(int(user_id))
            display_name = f"{user.display_name} ({user.name})"
        except:
            agent_info = next((cs for uid, cs, name in TRIP19_AGENTS if uid == user_id), None)
            display_name = agent_info if agent_info else f"User {user_id}"

        success = manipulation_manager.remove_manipulation(user_id)

        if success:
            embed = discord.Embed(
                title="✅ Manipulation Inaktiverad",
                description=f"Manipulation borttagen för {display_name}.\n"
                           f"Deras tärningsslag är nu normala igen.",
                color=discord.Color.green()
            )
        else:
            embed = discord.Embed(
                title="ℹ️ Ingen Manipulation",
                description=f"{display_name} hade ingen aktiv manipulation.",
                color=discord.Color.light_grey()
            )

        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @manip_group.command(name="inaktivera_gm", description="Inaktivera din egen manipulation")
    @app_commands.default_permissions(manage_guild=True)
    async def deactivate_gm_manipulation(interaction: discord.Interaction):
        """Inaktivera GM:s egen manipulation."""
        # KRITISK: GM-kontroll
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
                color=discord.Color.light_grey()
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
                color=discord.Color.light_grey()
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
                # Använd fetch_user() istället för get_user() för att alltid få användaren
                try:
                    user = await bot.fetch_user(int(user_id))
                    display_name = f"{user.display_name} ({user.name})"
                except:
                    # Fallback om vi inte kan hämta användaren
                    display_name = f"User {user_id}"

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