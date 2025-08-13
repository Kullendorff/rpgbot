"""
Admin commands for the EON Discord bot.

This module contains administrative commands that require Game Master role:
- startsession: Start a new game session for tracking dice rolls
- endsession: End the current session with AI-generated summary
- showsession: Display information about the active session
- secret: Perform secret dice rolls visible only to the GM
"""

import random
from typing import Optional, List
import discord
from discord.ext import commands

# Import core modules
from core.constants import MAX_TOKENS
from core.dice_parser import parse_dice_string
from core.dice_engine import unlimited_d6s


def register_admin_commands(bot, roll_tracker, color_handler, knowledge_base):
    """
    Register all admin commands with the bot.
    
    Args:
        bot: The Discord bot instance
        roll_tracker: Roll tracking instance for logging statistics
        color_handler: Color handler for user-specific embed colors
        knowledge_base: Knowledge base instance for AI features
    """
    
    @bot.command(name='startsession')
    @commands.has_role('Game Master')
    async def start_session(ctx: commands.Context, *, description: Optional[str] = None) -> None:
        """
        Startar en ny spelsession och börjar spåra tärningskast.
        
        Args:
            ctx (commands.Context): Kontexten för kommandot.
            description (Optional[str]): En valfri beskrivning för sessionen.
        """
        session_id: str = roll_tracker.start_session(description)
        await ctx.send(f"Started new game session (ID: {session_id})")
        if description:
            await ctx.send(f"Session description: {description}")

    @bot.command(name='endsession')
    @commands.has_role('Game Master')
    async def end_session(ctx: commands.Context) -> None:
        """
        Avslutar den aktiva spelsessionen och skickar en humoristisk sammanfattning.
        
        Args:
            ctx (commands.Context): Kontexten för kommandot.
        """
        session_id = roll_tracker.current_session
        if not session_id:
            await ctx.send("Ingen aktiv session att avsluta.")
            return
            
        # Avsluta sessionen
        roll_tracker.end_session()
        await ctx.send("Session avslutad.")
        
        # Hämta statistik för avslutad session
        stats: dict = roll_tracker.get_session_stats(session_id)
        if "error" in stats:
            await ctx.send(f"Kunde inte skapa en sammanfattning: {stats['error']}")
            return
            
        await ctx.send("Skapar en sammanfattning av sessionen...")
        
        # Visa att boten bearbetar
        async with ctx.typing():
            try:
                # Kontrollera om Claude API är tillgängligt
                if not knowledge_base.claude_client:
                    # Försök att initiera om
                    print("Claude-klienten är inte initialiserad, försöker initiera...")
                    success = knowledge_base.initialize_knowledge_base()
                    if not success:
                        await ctx.send("⚠️ Kunde inte skapa en sammanfattning - Claude API är inte tillgängligt.")
                        return
                        
                # Skapa ett sammandrag av statistiken i text
                session_info = stats["session_info"]
                player_stats = stats["player_stats"]
                command_stats = stats["command_stats"]
                popular_dice = stats["popular_dice"]
                
                # Skapa en statistiktext för Claude
                stats_text = f"""Session: {session_id}
                Startad: {session_info['start_time']}
                Avslutad: {session_info['end_time']}
                Beskrivning: {session_info['description'] or 'Ingen beskrivning'}
                Antal spelare: {session_info['unique_players']}
                Totalt antal tärningskast: {session_info['total_rolls']}
                
                Spelarstatistik:
                """
                
                for player in player_stats:
                    success_rate = player['success_rate'] if player['successes'] + player['failures'] > 0 else 0
                    stats_text += f"{player['name']}: {player['total_rolls']} kast, {success_rate}% framgång\n"
                    
                stats_text += "\nPopulära kommandon:\n"
                for cmd in command_stats:
                    stats_text += f"{cmd['command']}: {cmd['uses']} gånger"                
                    if cmd['success_rate'] is not None:
                        stats_text += f", {cmd['success_rate']}% framgång"
                    stats_text += "\n"
                    
                stats_text += "\nPopulära tärningskombinationer:\n"
                for dice in popular_dice:
                    stats_text += f"{dice['type']}: {dice['uses']} gånger\n"
                    
                print("Skickar statistik till Claude API:", stats_text)
                    
                # Skicka till Claude
                response = knowledge_base.claude_client.messages.create(
                    model="claude-3-5-sonnet-20240620",
                    max_tokens=MAX_TOKENS,
                    messages=[
                        {
                            "role": "user",
                            "content": f"""
                            Här är statistik från senaste EON-sessionen:
                            
                            {stats_text}
                            
                            Kan du ge en kort, humoristisk sammanfattning av denna session baserat på statistiken? 
                            Gör det gärna lite skämtsamt och rolligt - kanske kommentera på framgångsfrekvens, 
                            särskilda tärningskombinationer, eller något annat intressant du ser.
                            Försök hålla det på ca 3-5 meningar.
                            """
                        }
                    ]
                )
                
                summary = response.content[0].text.strip()
                
                # Skapa en snygg embed med sammanfattningen
                color = color_handler.get_user_color(ctx.author.id)
                embed = discord.Embed(
                    title="🎭 Humoristisk sessionssammanfattning",
                    description=summary,
                    color=color
                )
                
                # Lägg till grundläggande statistik
                embed.add_field(
                    name="📊 Basstatistik",
                    value=f"Tärningskast: {session_info['total_rolls']}\nSpelare: {session_info['unique_players']}",
                    inline=False
                )
                
                # Skicka embed till kanalen
                await ctx.send(embed=embed)
                
            except Exception as e:
                print(f"Fel vid skapande av sessionssammanfattning: {e}")
                await ctx.send(f"⚠️ Ett fel uppstod vid skapande av sessionssammanfattning: {str(e)}")
                # Skicka ändå ett besked om att sessionen är avslutad
                await ctx.send("Sessionen har ändå avslutats korrekt och all statistik har sparats.")

    @bot.command(name='showsession')
    @commands.has_role('Game Master')
    async def show_session(ctx: commands.Context) -> None:
        """
        Visar information om den aktiva sessionen.
        
        Args:
            ctx (commands.Context): Kontexten för kommandot.
        """
        if roll_tracker.current_session:
            await ctx.send(f"Active session ID: {roll_tracker.current_session}")
        else:
            await ctx.send("No active session.")

    @bot.command(name='secret')
    @commands.has_role('Game Master')
    async def secret_roll(ctx: commands.Context, *args) -> None:
        """
        Gör ett hemligt tärningskast som endast visas för spelledaren.
        Stödjer typerna: roll, ex, och count.
        
        Användningsexempel:
          !secret roll 2d6
          !secret ex 3d6
          !secret count 4d6 4
        
        Args:
            ctx (commands.Context): Kontexten för kommandot.
            *args: Kommandots argument.
        """
        try:
            try:
                await ctx.message.delete()
            except Exception:
                pass

            if len(args) < 1:
                await ctx.author.send(
                    "Använd formatet:\n"
                    "`!secret roll 2d6` - Vanligt slag\n"
                    "`!secret ex 3d6` - Exploderande slag\n"
                    "`!secret count 4d6 4` - Räkna resultat"
                )
                return

            command_type: str = args[0].lower()
            dice_args: List[str] = list(args[1:])

            color: int = color_handler.get_user_color(ctx.author.id)
            result_embed: discord.Embed = discord.Embed(
                title="🎲 Secret Roll",
                description=f"Command: !{command_type} {' '.join(dice_args)}",
                color=color
            )

            if command_type == "roll":
                if len(dice_args) < 1 or len(dice_args) > 2:
                    await ctx.author.send("Felaktigt format för roll-kommando")
                    return

                dice: str = dice_args[0]
                target: Optional[int] = int(dice_args[1]) if len(dice_args) == 2 else None

                num_dice, sides, modifier = parse_dice_string(dice)
                rolls: List[int] = [random.randint(1, sides) for _ in range(num_dice)]
                total: int = sum(rolls) + modifier

                result_embed.add_field(name="Rolls", value=str(rolls), inline=False)
                if modifier != 0:
                    result_embed.add_field(name="Modifier", value=str(modifier), inline=True)
                result_embed.add_field(name="Total", value=str(total), inline=True)

                if target is not None:
                    difference: int = target - total
                    success: bool = total <= target
                    result: str = f"✅ Success! ({difference:+d})" if success else f"❌ Failure ({difference:+d})"
                    result_embed.add_field(name=f"Skill Check (Target: {target})", value=result, inline=False)

            elif command_type == "ex":
                if len(dice_args) < 1 or len(dice_args) > 2:
                    await ctx.author.send("Felaktigt format för ex-kommando")
                    return

                dice: str = dice_args[0]
                target: Optional[int] = int(dice_args[1]) if len(dice_args) == 2 else None

                num_dice, sides, modifier = parse_dice_string(dice)
                # Använd unlimited_d6s-funktionen för exploderande tärningar
                all_rolls, final_total, initial_rolls = unlimited_d6s(num_dice, modifier)

                result_embed.add_field(name="All Rolls", value=str(all_rolls), inline=False)
                if modifier != 0:
                    result_embed.add_field(name="Modifier", value=str(modifier), inline=True)
                result_embed.add_field(name=f"Final Total (excl. {sides}s)", value=str(final_total), inline=True)

                if target is not None:
                    difference: int = target - final_total
                    success: bool = final_total <= target
                    result: str = f"✅ Success! ({difference:+d})" if success else f"❌ Failure ({difference:+d})"
                    result_embed.add_field(name=f"Skill Check (Target: {target})", value=result, inline=False)

            elif command_type == "count":
                if len(dice_args) != 2:
                    await ctx.author.send("Felaktigt format för count-kommando")
                    return

                dice, target_str = dice_args
                target: int = int(target_str)
                num_dice, sides, modifier = parse_dice_string(dice)
                if modifier != 0:
                    await ctx.author.send("Modifierare stöds inte för count-kommandon")
                    return

                rolls: List[int] = [random.randint(1, sides) for _ in range(num_dice)]
                successes: int = sum(1 for roll in rolls if roll >= target)
                formatted_rolls: List[str] = [f"**{roll}**" if roll >= target else str(roll) for roll in rolls]
                roll_display: str = ", ".join(formatted_rolls)
                result_embed.add_field(name="Rolls", value=f"[{roll_display}]", inline=False)
                success_text: str = "Success" if successes == 1 else "Successes"
                success_display: str = f"✨ {successes} {success_text}" if successes > 0 else "❌ No successes"
                result_embed.add_field(name="Results", value=success_display, inline=False)

            else:
                await ctx.author.send("Ogiltigt kommando. Använd 'roll', 'ex', eller 'count'.")
                return

            # Identifiera perfekta slag och fummel för hemliga obegränsade T6-slag
            is_perfect = False
            is_fumble = False
            
            if command_type == "ex":
                # Använd den befintliga logiken från ex-kommandot för perfekta och fummel
                if num_dice == 1:
                    if initial_rolls[0] in [1, 2, 3]:
                        is_perfect = True
                else:
                    not_one_count: int = sum(1 for r in initial_rolls if r != 1)
                    if not_one_count <= 1:
                        is_perfect = True

                six_count: int = sum(1 for r in initial_rolls if r == 6)
                is_fumble = (six_count >= 2)
                
                # Logga det hemliga slaget med perfekt/fummel-information för !ex
                roll_tracker.log_roll(
                    user_id=str(ctx.author.id),
                    user_name=ctx.author.display_name,
                    command_type=f'secret_ex',
                    num_dice=num_dice,
                    sides=sides,
                    roll_values=all_rolls,
                    modifier=modifier,
                    target=target,
                    success=success if 'success' in locals() else None,
                    is_perfect=is_perfect,
                    is_fumble=is_fumble
                )
            else:
                # Logga vanliga hemliga slag utan perfekt/fummel-information
                roll_tracker.log_roll(
                    user_id=str(ctx.author.id),
                    user_name=ctx.author.display_name,
                    command_type=f'secret_{command_type}',
                    num_dice=num_dice,
                    sides=sides,
                    roll_values=rolls if command_type != "ex" else all_rolls,
                    modifier=modifier,
                    target=target,
                    success=success if 'success' in locals() else None
                )

            await ctx.author.send(embed=result_embed)

            confirm_embed: discord.Embed = discord.Embed(
                title="🎲 Secret Roll",
                description=f"{ctx.author.display_name} made a secret {command_type}",
                color=color
            )
            await ctx.send(embed=confirm_embed)

        except Exception as e:
            await ctx.author.send(f"Ett fel uppstod: {str(e)}")