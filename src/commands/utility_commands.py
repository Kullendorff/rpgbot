"""
Utility commands module for the EON Discord bot.

This module contains utility commands like help, statistics, rules lookup, and improvement rolls.
"""

import os
from typing import Optional, List
import discord
from discord.ext import commands

# Import for dice engine functions
from core.dice_engine import unlimited_d6s
from core.constants import MAX_DICE, MAX_SIDES


def register_utility_commands(bot: commands.Bot, roll_tracker, color_handler, embed_factory) -> None:
    """
    Register all utility commands with the bot.
    
    Args:
        bot (commands.Bot): The Discord bot instance.
        roll_tracker: The roll tracking system.
        color_handler: The color handling system.
    """
    
    # Configure paths for rules folder
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(script_dir))
    RULES_FOLDER = os.path.join(project_root, "data", "rules")
    
    # Create rules folder if it doesn't exist
    if not os.path.exists(RULES_FOLDER):
        os.makedirs(RULES_FOLDER)

    @bot.command(name='dicehelp')
    async def help_command(ctx: commands.Context) -> None:
        """
        Visar hjälpinformation för alla tärningskommandon.
        
        Args:
            ctx (commands.Context): Kontexten för kommandot.
        """
        color: int = color_handler.get_user_color(ctx.author.id)
        embed = embed_factory.admin_message(
            ctx.author.id,
            "Kullens Tärningsrullare",
            "För alla dina tärningsbehov. Nästan"
        )
        embed.add_field(
            name="Grundläggande Tärningsslag",
            value=(
                "Slå valfritt antal och typ av tärningar med en valfri modifierare:\n"
                "`!roll NdX[+Z]` - Slå N tärningar med X sidor och modifierare Z\n"
                "Exempel: `!roll 3d6+2` - Slår tre 6-sidiga tärningar och lägger till 2\n"
                f"\nBegränsningar: Maximalt {MAX_DICE} tärningar och {MAX_SIDES} sidor per tärning"
            ),
            inline=False
        )
        embed.add_field(
            name="Obegränsade Tärningsslag",
            value=(
                "Slå tärningar som 'exploderar' när de visar maxvärde:\n"
                "`!ex NdX[+Z]` - Slå N obegränsade tärningar med X sidor och modifierare Z\n"
                "Exempel: `!ex 4d6-1` - Slår fyra obegränsade 6-sidiga tärningar och subtraherar 1\n"
                "\nNär en tärning visar sitt maxvärde (t.ex. 6 på en T6), får du slå 2 nya tärningar!"
            ),
            inline=False
        )
        embed.add_field(
            name="Räkna Framgångar",
            value=(
                "Räkna tärningsresultat som når eller överskrider ett målvärde:\n"
                "`!count NdX MÅLVÄRDE` - Slå N X-sidiga tärningar och räkna resultat >= MÅLVÄRDE\n"
                "Exempel: `!count 5d10 7` - Slår fem T10 och räknar hur många som visar 7 eller högre\n"
                "\nLyckade slag visas i **fetstil**"
            ),
            inline=False
        )
        embed.add_field(
            name="Färdighetskontroller",
            value=(
                "Slå mot ett målvärde:\n"
                "`!roll NdX[+Z] MÅLVÄRDE` - Vanlig färdighetskontroll\n"
                "`!ex NdX[+Z] MÅLVÄRDE` - Obegränsad färdighetskontroll\n"
                "Exempel: `!roll 4d6+2 24` - Slår 4T6+2 mot målvärde 24\n"
                "\n✅ Lyckat om totalen ≤ målvärdet\n"
                "❌ Misslyckat om totalen > målvärdet\n"
                "Resultatet visar hur mycket du lyckades eller misslyckades med"
            ),
            inline=False
        )
        embed.add_field(
            name="Sessionshantering",
            value=(
                "Spåra tärningsslag under dina spelsessioner:\n"
                "`!startsession [beskrivning]` - Börja spåra en ny session\n"
                "`!endsession` - Avsluta den nuvarande sessionen\n"
                "`!stats` - Visa statistik för den aktuella sessionen\n"
                "`!mystats` - Visa din personliga statistik\n"
                "\nObservera: Start och avslut av sessioner kräver rollen 'Game Master'"
            ),
            inline=False
        )
        embed.add_field(
            name="Hemliga Slag (Endast Spelledare)",
            value=(
                "Gör hemliga slag som endast visar resultaten för dig:\n"
                "`!secret roll NdX[+Z]` - Hemligt vanligt slag\n"
                "`!secret ex NdX[+Z]` - Hemligt obegränsat slag\n"
                "`!secret count NdX MÅLVÄRDE` - Hemligt räkneslag\n"
                "\nResultaten skickas via DM, och en diskret bekräftelse visas i kanalen.\n"
                "Alla hemliga slag loggas för sessionsstatistik."
            ),
            inline=False
        )
        embed.add_field(
            name="Kunskapsbas",
            value=(
                "Sök i rollspelsböckerna efter regler och information:\n"
                "`!ask [din fråga]` - Ställ en fråga till kunskapsbasen\n"
                "Exempel: `!ask Hur fungerar stridskonster i Eon?`\n"
                "\nKunskapsbasen söker i alla dina regelböcker och ger ett koncist svar."
            ),
            inline=False
        )
        await ctx.send(embed=embed)

    @bot.command(name='stats')
    async def stats_command(ctx: commands.Context, session_id: Optional[str] = None) -> None:
        """
        Visar statistik för den aktiva sessionen eller en specifik session.
        
        Args:
            ctx (commands.Context): Kontexten för kommandot.
            session_id (Optional[str]): ID för den specifika sessionen (om angivet).
        """
        stats: dict = roll_tracker.get_session_stats(session_id)
        if "error" in stats:
            await ctx.send(stats["error"])
            return

        color: int = color_handler.get_user_color(ctx.author.id)
        embed = embed_factory.stats_overview(
            ctx.author.id,
            "Session",
            stats['session_info'],
            session_id or roll_tracker.current_session
        )
        session_info: dict = stats["session_info"]
        embed.add_field(
            name="Session Info",
            value=(
                f"Started: {session_info['start_time']}\n"
                f"{'Ended: ' + session_info['end_time'] if session_info['end_time'] else 'Still active'}\n"
                f"Description: {session_info['description'] or 'No description'}"
            ),
            inline=False
        )

        players_text: str = ""
        for player in stats["player_stats"]:
            players_text += (
                f"**{player['name']}**\n"
                f"Rolls: {player['total_rolls']}"
            )
            if player['successes'] + player['failures'] > 0:
                players_text += f" (Success rate: {player['success_rate']}%)"
            players_text += "\n"
        if players_text:
            embed.add_field(name="Player Statistics", value=players_text, inline=False)

        if stats["command_stats"]:
            cmd_text: str = "\n".join(
                f"{cmd['command']}: {cmd['uses']} uses" +
                (f" ({cmd['success_rate']}% success)" if cmd['success_rate'] is not None else "")
                for cmd in stats["command_stats"]
            )
            embed.add_field(name="Command Usage", value=cmd_text, inline=False)

        if stats["popular_dice"]:
            dice_text: str = "\n".join(
                f"{dice['type']}: {dice['uses']} times"
                for dice in stats["popular_dice"]
            )
            embed.add_field(name="Most Used Dice", value=dice_text, inline=False)

        await ctx.send(embed=embed)

    @bot.command(name='mystats')
    async def my_stats_command(ctx: commands.Context, session_id: Optional[str] = None) -> None:
        """
        Visar statistik för den aktiva spelaren.
        
        Args:
            ctx (commands.Context): Kontexten för kommandot.
            session_id (Optional[str]): ID för den specifika sessionen (om angivet).
        """
        stats: dict = roll_tracker.get_player_stats(str(ctx.author.id), session_id)
        if "error" in stats:
            await ctx.send(stats["error"])
            return

        color: int = color_handler.get_user_color(ctx.author.id)
        embed = embed_factory.stats_overview(
            ctx.author.id,
            ctx.author.display_name,
            stats,
            session_id or roll_tracker.current_session
        )

        recent_rolls: List[dict] = stats["rolls"][:5]
        if recent_rolls:
            roll_text: str = "\n".join(
                f"{r['command']} {r['dice']}" +
                (f" (Target: {r['target']})" if r['target'] else "") +
                f": {r['values']}" +
                (f" {'✅' if r['success'] else '❌'}" if r['success'] is not None else "")
                for r in recent_rolls
            )
            embed.add_field(name="Recent Rolls", value=roll_text, inline=False)
        else:
            embed.add_field(name="Recent Rolls", value="No rolls yet", inline=False)

        await ctx.send(embed=embed)

    @bot.command(name="regel")
    async def regel_command(ctx: commands.Context, *args: str) -> None:
        """
        Hanterar regler:
          1. Kör `!regel` för att lista alla regler.
          2. Kör `!regel [namn eller nummer]` för att visa en specifik regel.
        
        Args:
            ctx (commands.Context): Kontexten för kommandot.
            *args (str): Argument för att välja specifik regel (namn eller nummer).
        """
        if not args:
            rules: List[str] = os.listdir(RULES_FOLDER)
            if not rules:
                await ctx.send("Det finns inga regler ännu.")
                return

            response: str = "**Tillgängliga regler:**\n"
            for i, rule_file in enumerate(rules, start=1):
                rule_name: str = os.path.splitext(rule_file)[0]
                response += f"{i}. {rule_name}\n"
            await ctx.send(response)
        else:
            identifier: str = args[0].lower()
            rules: List[str] = os.listdir(RULES_FOLDER)
            try:
                if identifier.isdigit():
                    rule_index: int = int(identifier) - 1
                    if rule_index < 0 or rule_index >= len(rules):
                        raise IndexError
                    rule_file: str = rules[rule_index]
                else:
                    rule_file = f"{identifier}.txt"
                    if rule_file not in rules:
                        raise FileNotFoundError

                with open(os.path.join(RULES_FOLDER, rule_file), "r", encoding="utf-8") as f:
                    content: str = f.read()

                rule_name: str = os.path.splitext(rule_file)[0]
                if len(content) <= 2000:
                    await ctx.send(f"**{rule_name}**:\n{content}")
                else:
                    chunks: List[str] = [content[i:i+2000] for i in range(0, len(content), 2000)]
                    await ctx.send(f"**{rule_name}**: (uppdelat i flera meddelanden)")
                    for chunk in chunks:
                        await ctx.send(chunk)
            except (IndexError, FileNotFoundError):
                await ctx.send("Regeln kunde inte hittas. Kontrollera namnet eller numret.")

    @bot.command(name='höj')
    async def improvement_roll_command(ctx: commands.Context, skill_chance: int, *, flags: str = "") -> None:
        """
        Slår ett förbättringsslag för en färdighet i EON.
        
        Efter ett avslutat speltillfälle får spelaren slå Ob3T6 för varje färdighet som har blivit förkryssad.
        Lyckas slaget ökar färdighetschansen ett steg (+1). För lättlärda färdigheter används Ob4T6.
        
        Användning: !höj [färdighetschans] [flaggor]
        
        Flaggor:
          --ll    - Färdigheten är lättlärd (slår Ob4T6 istället för Ob3T6)
        
        Exempel:
          !höj 16         - Förbättringsslag för normal färdighet med värde 16
          !höj 12 --ll    - Förbättringsslag för lättlärd färdighet med värde 12
        """
        try:
            # Kontrollera om färdigheten är lättlärd
            is_easy_learnable = "--ll" in flags.lower()
            
            # Sätt antal tärningar beroende på om färdigheten är lättlärd
            num_dice = 4 if is_easy_learnable else 3
            
            # Slå tärningarna enligt obegränsad regel
            all_rolls, final_total, initial_rolls = unlimited_d6s(num_dice, 0)
            
            # Kontrollera om slaget är lyckat
            success = final_total >= skill_chance
            
            # Förbered resultattexten
            color = color_handler.get_user_color(ctx.author.id)
            embed = embed_factory.dice_result(
                ctx.author.id,
                ctx.author.display_name,
                "höj",
                f"Ob{num_dice}T6",
                initial_rolls,
                final_total,
                skill_chance,
                success
            )
            
            embed.add_field(name="Första kastomgången", value=str(initial_rolls), inline=False)
            embed.add_field(name="Alla kast (inkl. extra)", value=str(all_rolls), inline=False)
            embed.add_field(name="Slutsumma (utan 6:or)", value=str(final_total), inline=True)
            
            if success:
                result_text = "✅ **Lyckat slag!** Färdighetschansen ökar med +1."
                new_skill_chance = skill_chance + 1
                embed.add_field(
                    name="Resultat", 
                    value=f"{result_text}\nNy färdighetschans: {new_skill_chance}",
                    inline=False
                )
            else:
                result_text = "❌ **Misslyckat slag.** Färdighetschansen förblir oförändrad."
                embed.add_field(
                    name="Resultat", 
                    value=result_text,
                    inline=False
                )
                

            # Logga slaget i statistiken
            roll_tracker.log_roll(
                user_id=str(ctx.author.id),
                user_name=ctx.author.display_name,
                command_type='höj',
                num_dice=num_dice,
                sides=6,
                roll_values=all_rolls,
                modifier=0,
                target=skill_chance,
                success=success
            )
                
            await ctx.send(embed=embed)
            
        except ValueError as e:
            await ctx.send(f"Fel: {str(e)}\nAnvändning: `!höj [färdighetschans] [--ll om lättlärd]`")