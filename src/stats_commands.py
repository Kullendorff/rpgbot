"""
Statistikkommando-modulen för Eon Diceroller
Innehåller kommandot för att visa permanent statistik
"""

from typing import Dict, List, Optional
import discord
from discord.ext import commands

async def allstats_command(ctx: commands.Context, roll_tracker, color_handler) -> None:
    """
    Visar permanent statistik för alla tärningskast genom tiderna.
    
    Args:
        ctx (commands.Context): Kontexten för kommandot.
    """
    stats: dict = roll_tracker.get_all_time_stats()
    
    color: int = color_handler.get_user_color(ctx.author.id)
    embed: discord.Embed = discord.Embed(
        title="🏆 Permanent Statistik",
        description="Sammanställd statistik över alla sessioner",
        color=color
    )
    
    # Grundläggande statistik
    basic_stats = stats["basic_stats"]
    embed.add_field(
        name="📊 Övergripande statistik",
        value=(
            f"Totalt antal sessioner: {basic_stats['total_sessions']}\n"
            f"Totalt antal spelare: {basic_stats['total_players']}\n"
            f"Totalt antal tärningskast: {basic_stats['total_rolls']}\n"
            f"Genomsnittlig framgångsfrekvens: {basic_stats['avg_success_rate']}%"
        ),
        inline=False
    )
    
    # Top 5 spelare
    top_players = stats["player_stats"][:5]
    if top_players:
        players_text = "\n".join(
            f"{i+1}. **{player['name']}**: {player['total_rolls']} kast ({player['success_rate']}% framgång)"
            for i, player in enumerate(top_players)
        )
        embed.add_field(
            name="🥇 Topp 5 Spelare",
            value=players_text,
            inline=False
        )
    
    # Mest använda kommandona
    top_commands = stats["command_stats"][:5]
    if top_commands:
        commands_text = "\n".join(
            f"{cmd['command']}: {cmd['uses']} gånger" +
            (f" ({cmd['success_rate']}% framgång)" if cmd['success_rate'] is not None else "")
            for cmd in top_commands
        )
        embed.add_field(
            name="🎮 Populära Kommandon",
            value=commands_text,
            inline=False
        )
    
    # Mest använda tärningskombinationerna
    top_dice = stats["popular_dice"][:5]
    if top_dice:
        dice_text = "\n".join(
            f"{dice['type']}: {dice['uses']} gånger"
            for dice in top_dice
        )
        embed.add_field(
            name="🎲 Populära Tärningar",
            value=dice_text,
            inline=False
        )
    
    # Skicka embed
    await ctx.send(embed=embed)

async def mystatsall_command(ctx: commands.Context, roll_tracker, color_handler) -> None:
    """
    Visar permanent statistik för den aktiva spelaren över alla sessioner.
    
    Args:
        ctx (commands.Context): Kontexten för kommandot.
    """
    stats: dict = roll_tracker.get_player_all_time_stats(str(ctx.author.id))
    if "error" in stats:
        await ctx.send(f"Ingen statistik hittades för {ctx.author.display_name}")
        return

    color: int = color_handler.get_user_color(ctx.author.id)
    embed: discord.Embed = discord.Embed(
        title=f"🏆 {stats['user_name']}s Permanenta Statistik",
        description="Sammanställd statistik över alla sessioner",
        color=color
    )
    
    # Grundläggande statistik
    basic_stats = stats["basic_stats"]
    embed.add_field(
        name="📊 Övergripande statistik",
        value=(
            f"Totalt antal tärningskast: {basic_stats['total_rolls']}\n"
            f"Antal sessioner deltagit i: {basic_stats['participated_sessions']}\n"
            f"Framgångsfrekvens: {basic_stats['success_rate']}%\n"
            f"Senaste tärningskast: {basic_stats['last_roll']}"
        ),
        inline=False
    )
    
    # Mest använda kommandona
    top_commands = stats["command_stats"][:5]
    if top_commands:
        commands_text = "\n".join(
            f"{cmd['command']}: {cmd['uses']} gånger" +
            (f" ({cmd['success_rate']}% framgång)" if cmd['success_rate'] is not None else "")
            for cmd in top_commands
        )
        embed.add_field(
            name="🎮 Dina Favoriter",
            value=commands_text,
            inline=False
        )
    
    # Mest använda tärningskombinationerna
    top_dice = stats["popular_dice"]
    if top_dice:
        dice_text = "\n".join(
            f"{dice['type']}: {dice['uses']} gånger"
            for dice in top_dice
        )
        embed.add_field(
            name="🎲 Favoritkombon",
            value=dice_text,
            inline=False
        )
    
    # Lyckostatistik
    lucky_dice = stats["lucky_dice"]
    unlucky_dice = stats["unlucky_dice"]
    
    luck_text = ""
    if lucky_dice["type"]:
        luck_text += f"Lyckligaste tärningen: **{lucky_dice['type']}** ({lucky_dice['success_rate']}% framgång)\n"
    if unlucky_dice["type"]:
        luck_text += f"Olycksaligaste tärningen: **{unlucky_dice['type']}** ({unlucky_dice['success_rate']}% framgång)"
    
    if luck_text:
        embed.add_field(
            name="🍀 Lyckostatistik",
            value=luck_text,
            inline=False
        )
    
    # Skicka embed
    await ctx.send(embed=embed)

def register_commands(bot, roll_tracker, color_handler):
    """Registrerar statistikkommandon till boten"""
    
    @bot.command(name='allstats')
    async def _allstats(ctx: commands.Context):
        """Visar statistik för alla tärningskast genom tiderna."""
        await allstats_command(ctx, roll_tracker, color_handler)
    
    @bot.command(name='mystatsall')
    async def _mystatsall(ctx: commands.Context):
        """Visar personlig statistik över alla sessioner."""
        await mystatsall_command(ctx, roll_tracker, color_handler)
