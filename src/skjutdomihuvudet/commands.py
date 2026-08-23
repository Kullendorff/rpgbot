from typing import List, Tuple, Dict, Optional, Any, Union, Callable
import discord
from discord.ext import commands
import random
import os

# Importera våra funktioner
from .dice_functions import (
    roll_d20, roll_d20_advantage, roll_d20_disadvantage, 
    roll_damage, roll_hit_zone, 
    parse_initiative_args, roll_initiative,
    InfectionDeck, WEAPON_DAMAGE, 
    get_naila_effect, get_fucka_upp_effect,
    SplatterPointManager
)

# Globala instanser
infection_deck_manager = None
splatter_manager = None

def register_commands(bot: commands.Bot, roll_tracker: Any, color_handler: Any) -> None:
    """
    Registrera Skjut-dom-i-huvudet-kommandon för Discord-boten.
    
    Args:
        bot: Discord-botinstansen att registrera kommandona till.
        roll_tracker: RollTracker-instans för att spåra tärningsslag.
        color_handler: ColorHandler-instans för att hantera användarfärger i embeds.
    """
    # Initiera globala instanser
    global infection_deck_manager, splatter_manager
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(os.path.dirname(os.path.dirname(script_dir)), 'data', 'sdih_decks')
    infection_deck_manager = InfectionDeck(data_dir)
    splatter_manager = SplatterPointManager()
    
    @bot.command(name='rull')
    async def rull_command(ctx: commands.Context, modifier_str: str = "+0", testvalue: Optional[int] = None) -> None:
        try:
            modifier = int(modifier_str)

            roll, total, is_naila, is_fumble = roll_d20(modifier)

            embed = discord.Embed(
                title=f"{ctx.author.display_name}s tärningsslag",
                description=f"Slag: d20{'+' if modifier >= 0 else ''}{modifier}",
                color=discord.Color.blue()
            )

            result_text = f"**Resultat:** {roll}{'+' if modifier >= 0 else ''}{modifier} = **{total}**"

            if is_naila:
                result_text += f" 🔥 **NAILA!**\n{get_naila_effect()}"
            elif is_fumble:
                result_text += f" 💀 **FUCKA UPP!**\n{get_fucka_upp_effect()}"

            if testvalue is not None:
                result_text += f"\n\nTest mot **{testvalue}**: {'✅ LYCKAT!' if total >= testvalue else '❌ MISSLYCKAT!'}"

            embed.add_field(name="Utfall", value=result_text)
            await ctx.send(embed=embed)

        except Exception as e:
            await ctx.send(f"Ett fel uppstod: {str(e)}")


    @bot.command(name='fördel')
    async def fordel_command(ctx: commands.Context, modifier_str: str = "+0", testvalue: Optional[int] = None) -> None:
        try:
            modifier = int(modifier_str)

            rolls, best_roll, is_naila, is_fumble = roll_d20_advantage()
            total = best_roll + modifier

            embed = discord.Embed(
                title=f"{ctx.author.display_name}s slag med FÖRDEL",
                description=f"Slag: 2d20, bästa resultat{'+' if modifier >= 0 else ''}{modifier}",
                color=discord.Color.green()
            )

            result_text = f"**Tärningar:** {rolls}\n"
            result_text += f"**Valt resultat:** {best_roll}{'+' if modifier >= 0 else ''}{modifier} = **{total}**"

            if is_naila:
                result_text += f" 🔥 **NAILA!**\n{get_naila_effect()}"
            elif is_fumble:
                result_text += f" 💀 **FUCKA UPP!**\n{get_fucka_upp_effect()}"

            if testvalue is not None:
                result_text += f"\n\nTest mot **{testvalue}**: {'✅ LYCKAT!' if total >= testvalue else '❌ MISSLYCKAT!'}"

            embed.add_field(name="Utfall", value=result_text)
            await ctx.send(embed=embed)

        except Exception as e:
            await ctx.send(f"Ett fel uppstod: {str(e)}")


    @bot.command(name='nackdel')
    async def nackdel_command(ctx: commands.Context, modifier_str: str = "+0", testvalue: Optional[int] = None) -> None:
        try:
            modifier = int(modifier_str)

            rolls, worst_roll, is_naila, is_fumble = roll_d20_disadvantage()
            total = worst_roll + modifier

            embed = discord.Embed(
                title=f"{ctx.author.display_name}s slag med NACKDEL",
                description=f"Slag: 2d20, sämsta resultat{'+' if modifier >= 0 else ''}{modifier}",
                color=discord.Color.red()
            )

            result_text = f"**Tärningar:** {rolls}\n"
            result_text += f"**Valt resultat:** {worst_roll}{'+' if modifier >= 0 else ''}{modifier} = **{total}**"

            if is_naila:
                result_text += f" 🔥 **NAILA!**\n{get_naila_effect()}"
            elif is_fumble:
                result_text += f" 💀 **FUCKA UPP!**\n{get_fucka_upp_effect()}"

            if testvalue is not None:
                result_text += f"\n\nTest mot **{testvalue}**: {'✅ LYCKAT!' if total >= testvalue else '❌ MISSLYCKAT!'}"

            embed.add_field(name="Utfall", value=result_text)
            await ctx.send(embed=embed)

        except Exception as e:
            await ctx.send(f"Ett fel uppstod: {str(e)}")


    @bot.command(name='skada')
    async def skada_command(ctx: commands.Context, *, weapon_or_dice: str) -> None:
        """
        Slår skada för ett vapen.
        
        Användning: 
          !skada [vapennamn]
          !skada [tärningsformel]
        
        Args:
            ctx: Kommandokontexten.
            weapon_or_dice: Vapennamn eller tärningsformel (t.ex. "pistol" eller "2d6+1").
        """
        try:
            weapon_or_dice = weapon_or_dice.lower().strip()
            
            # Försök först tolka som vapennamn
            try:
                rolls, total = roll_damage(weapon_name=weapon_or_dice)
                weapon_name = weapon_or_dice.capitalize()
                damage_formula = WEAPON_DAMAGE[weapon_or_dice]
            except (KeyError, ValueError):
                # Om det inte är ett vapennamn, försök tolka som tärningsformel
                try:
                    rolls, total = roll_damage(damage_string=weapon_or_dice)
                    weapon_name = "Anpassad"
                    damage_formula = weapon_or_dice
                except ValueError:
                    # Lista tillgängliga vapen om inget matchade
                    weapons_list = ", ".join(sorted([w.capitalize() for w in WEAPON_DAMAGE.keys()]))
                    await ctx.send(f"Ogiltigt vapen eller skadeformel. Tillgängliga vapen är:\n{weapons_list}\n\nEller använd tärningsformat t.ex. '2d6+1'")
                    return
            
            # Skapa ett snyggt resultatmeddelande
            color = color_handler.get_user_color(ctx.author.id)
            embed = discord.Embed(
                title=f"{ctx.author.display_name}s skadeslag",
                description=f"Vapen: **{weapon_name}** ({damage_formula})",
                color=color
            )
            
            embed.add_field(name="Tärningar", value=str(rolls), inline=False)
            embed.add_field(name="Total skada", value=f"**{total}**", inline=False)
            
            # Spåra tärningsslag för statistik
            try:
                # Parsea vår formel för att få rätt värden till loggning
                if "d" in damage_formula:
                    if "+" in damage_formula:
                        dice_part, mod_part = damage_formula.split("+")
                        modifier = int(mod_part)
                    elif "-" in damage_formula:
                        dice_part, mod_part = damage_formula.split("-")
                        modifier = -int(mod_part)
                    else:
                        dice_part = damage_formula
                        modifier = 0
                        
                    num_dice, sides = map(int, dice_part.lower().split("d"))
                    
                    roll_tracker.log_roll(
                        user_id=str(ctx.author.id),
                        user_name=ctx.author.display_name,
                        command_type='skada',
                        num_dice=num_dice,
                        sides=sides,
                        roll_values=rolls,
                        modifier=modifier,
                        target=None,
                        success=None
                    )
            except Exception as e:
                print(f"Fel vid loggning av tärningsslag: {e}")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            await ctx.send(f"Ett fel uppstod: {str(e)}\nAnvändning: `!skada [vapennamn]` eller `!skada [tärningsformel]`")

    @bot.command(name='träffzon')
    async def traffzon_command(ctx: commands.Context) -> None:
        """
        Slår för att bestämma vilken kroppsdel som träffas.
        
        Användning: !träffzon
        """
        try:
            roll, zone = roll_hit_zone()
            
            # Skapa ett snyggt resultatmeddelande
            color = color_handler.get_user_color(ctx.author.id)
            embed = discord.Embed(
                title=f"{ctx.author.display_name}s träffzon",
                description="Slår d20 för att bestämma träffzon",
                color=color
            )
            
            embed.add_field(name="Tärning", value=str(roll), inline=True)
            embed.add_field(name="Träffad kroppsdel", value=f"**{zone}**", inline=True)
            
            # Spåra tärningsslag för statistik
            try:
                roll_tracker.log_roll(
                    user_id=str(ctx.author.id),
                    user_name=ctx.author.display_name,
                    command_type='träffzon',
                    num_dice=1,
                    sides=20,
                    roll_values=[roll],
                    modifier=0,
                    target=None,
                    success=None
                )
            except Exception as e:
                print(f"Fel vid loggning av tärningsslag: {e}")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            await ctx.send(f"Ett fel uppstod: {str(e)}")

    @bot.command(name='initiativ')
    async def initiativ_command(ctx: commands.Context, *args) -> None:
        """
        Slår initiativ för flera karaktärer och sorterar dem i turordning.
        
        Användning: !initiativ [namn] [värde] [namn2] [värde2] ...
        Exempel: !initiativ Alice +2 Bob +1 Charlie -1
        
        Args:
            ctx: Kommandokontexten.
            *args: Lista med namn och initiativmodifierare.
        """
        try:
            if len(args) < 2:
                await ctx.send("Användning: `!initiativ [namn] [värde] [namn2] [värde2] ...`\nExempel: `!initiativ Alice +2 Bob +1 Charlie -1`")
                return
            
            # Parsea deltagarna
            participants = parse_initiative_args(list(args))
            
            # Slå initiativ
            initiative_results = roll_initiative(participants)
            
            # Skapa ett snyggt resultatmeddelande
            color = color_handler.get_user_color(ctx.author.id)
            embed = discord.Embed(
                title="Initiativordning",
                description=f"Initiativ för {len(participants)} deltagare",
                color=color
            )
            
            # Lägg till resultaten i fallande ordning
            for i, result in enumerate(initiative_results, 1):
                embed.add_field(
                    name=f"{i}. {result['name']}",
                    value=f"Slag: {result['roll']}{'+' if result['modifier'] > 0 else ''}{result['modifier'] if result['modifier'] != 0 else ''} = **{result['total']}**",
                    inline=False
                )
            
            await ctx.send(embed=embed)
            
        except ValueError as e:
            await ctx.send(f"Fel: {str(e)}")
        except Exception as e:
            await ctx.send(f"Ett fel uppstod: {str(e)}")

    @bot.command(name='smitta')
    async def smitta_command(ctx: commands.Context, action: str, user_mention: str = None) -> None:
        """
        Hanterar infektionskort för en spelare.
        
        Subkommandon:
          !smitta dra [@användare]   - Drar ett kort från användarens smittokortlek
          !smitta reset [@användare] - Återställer användarens smittokortlek
          !smitta status [@användare] - Visar status för smittokortleken
        
        Args:
            ctx: Kommandokontexten.
            action: Subkommando (dra, reset, status).
            user_mention: Discord-mention för användaren (kan vara tom för att referera till kommandoanvändaren).
        """
        try:
            # Bestäm användar-ID baserat på omnämnande eller kommandoanvändaren
            if user_mention and len(ctx.message.mentions) > 0:
                target_user = ctx.message.mentions[0]
            else:
                target_user = ctx.author
            
            user_id = str(target_user.id)
            display_name = target_user.display_name
            
            # Skapa ett embed med användarfärg
            color = color_handler.get_user_color(ctx.author.id)
            embed = discord.Embed(
                title=f"Smittokort för {display_name}",
                color=color
            )
            
            # Hantera subkommandon
            action = action.lower()
            
            if action == "reset":
                # Återställ kortleken
                infection_deck_manager.reset_deck(user_id)
                embed.description = f"Återställde smittokortleken för {display_name}."
                embed.add_field(name="Ny kortlek", value="8 friska kort, 2 smittade kort", inline=False)
                
            elif action == "status":
                # Visa status för kortleken
                status = infection_deck_manager.get_deck_status(user_id)
                
                embed.description = f"Status för {display_name}s smittokortlek"
                embed.add_field(
                    name="Återstående kort", 
                    value=f"{status['remaining']} kort ({status['remaining_healthy']} friska, {status['remaining_infected']} smittade)", 
                    inline=False
                )
                
                embed.add_field(
                    name="Dragna kort", 
                    value=f"{status['drawn']} kort ({status['drawn_healthy']} friska, {status['drawn_infected']} smittade)", 
                    inline=False
                )
                
                embed.add_field(
                    name="Smittorisk", 
                    value=f"{status['infection_chance']:.1f}% chans att bli smittad vid nästa bett", 
                    inline=False
                )
                
            elif action == "dra":
                # Dra ett kort från användarens lek
                card = infection_deck_manager.draw_card(user_id)
                
                if card["type"] == "EmptyDeck":
                    embed.description = f"{display_name}s kortlek är tom! Använd `!smitta reset @{display_name}` för att återställa."
                else:
                    # Sätt färg och ikon baserat på resultatet
                    if card["type"] == "Frisk":
                        result_icon = "✅"
                        embed.color = discord.Color.green()
                    else:  # Smittad
                        result_icon = "☣️"
                        embed.color = discord.Color.red()
                    
                    embed.description = f"{display_name} drog ett kort..."
                    embed.add_field(
                        name="Resultat", 
                        value=f"**{result_icon} {card['type']}**\n{card['message']}", 
                        inline=False
                    )
                    
                    # Visa uppdaterad status
                    status = infection_deck_manager.get_deck_status(user_id)
                    embed.add_field(
                        name="Återstående kort", 
                        value=f"{status['remaining']} kort ({status['remaining_healthy']} friska, {status['remaining_infected']} smittade)", 
                        inline=False
                    )
                    
                    # Visa statistik om användaren blev smittad
                    if card["type"] == "Smittad":
                        embed.add_field(
                            name="Överlevnadstips", 
                            value="Bäst att börja leta efter något att äta hjärnor med...", 
                            inline=False
                        )
            else:
                # Okänt subkommando
                await ctx.send(
                    "Ogiltigt kommando. Använd något av följande:\n"
                    "`!smitta dra [@användare]` - Drar ett kort\n"
                    "`!smitta reset [@användare]` - Återställer kortleken\n"
                    "`!smitta status [@användare]` - Visar status för kortleken"
                )
                return
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            await ctx.send(f"Ett fel uppstod: {str(e)}")

    @bot.command(name='sdihelp')
    async def sdih_help_command(ctx: commands.Context) -> None:
        """
        Visar hjälp för Skjut dom i huvudet-kommandon.
        
        Användning: !sdihelp
        """
        color = color_handler.get_user_color(ctx.author.id)
        embed = discord.Embed(
            title="🧟‍♂️ Skjut dom i huvudet - Kommandon",
            description="Tärningskommandon för zombierollspelet 'Skjut dom i huvudet'",
            color=color
        )
        
        embed.add_field(
            name="Grundläggande tärningsslag",
            value=(
                "`!rull [+modifikation]` - Slår en D20 med modifikation\n"
                "Exempel: `!rull +3`, `!rull -2`, `!rull` 🎲\n"
                "(gamla formatet `!rull d20+3` fungerar fortfarande)"
            ),
            inline=False
        )
        
        embed.add_field(
            name="Fördel/Nackdel",
            value=(
                "`!fördel [+modifikation]` - Slår 2D20 och tar det högsta värdet\n"
                "`!nackdel [+modifikation]` - Slår 2D20 och tar det lägsta värdet\n"
                "Exempel: `!fördel +2`, `!nackdel -1` 🎲"
            ),
            inline=False
        )
        
        embed.add_field(
            name="Skada",
            value=(
                "`!skada [vapen]` - Slår skada för ett fördefinierat vapen\n"
                "`!skada [tärningsformel]` - Slår skada för en anpassad formel\n"
                "Exempel: `!skada pistol`, `!skada 2d6+3` 💥"
            ),
            inline=False
        )
        
        embed.add_field(
            name="Smittokort & Amputation",
            value=(
                "`!smitta dra` - Drar ett kort från din smittokortlek\n"
                "`!smitta status` - Visar status för din smittokortlek\n"
                "`!smitta reset` - Återställer din smittokortlek\n"
                "`!amputera [arm/ben]` - Amputera en kroppsdel för att undvika smitta\n"
                "Exempel: `!smitta dra`, `!amputera höger arm` ☣️\n"
                "*Du kan lägga till @användarnamn efter kommandot för att utföra det på en annan spelare*"
            ),
            inline=False
        )
        
        embed.add_field(
            name="Träffzoner, Initiativ & Splatter",
            value=(
                "`!träffzon` - Slår för att avgöra träffad kroppsdel 🎯\n"
                "`!initiativ [namn] [värde] [namn2] [värde2] ...` - Slår initiativ för flera deltagare\n"
                "`!splatter use [beskrivning]` - Använder en splatterpoäng för Fördel och tredubbel skada\n"
                "`!splatter status` - Visa kvarvarande splatterpoäng\n"
                "Exempel: `!initiativ Alice +2 Bob +1 Charlie -1` ⚡"
            ),
            inline=False
        )
        
        embed.add_field(
            name="Tillgängliga vapen",
            value=", ".join(sorted([v.capitalize() for v in WEAPON_DAMAGE.keys()])),
            inline=False
        )
        
        await ctx.send(embed=embed)

    @bot.command(name='amputera')
    async def amputera_command(ctx: commands.Context, *, body_part: str = None) -> None:
        """
        Amputerar en smittad kroppsdel (arm eller ben) för att undvika zombiesmitta.
        
        Användning: !amputera [kroppsdel]
        
        Args:
            ctx: Kommandokontexten.
            body_part: Vilken kroppsdel som ska amputeras (arm/ben).
        """
        try:
            if not body_part:
                await ctx.send("Användning: `!amputera [arm/ben]`")
                return
                
            # Normalisera indata
            body_part = body_part.lower()
            valid_parts = ["arm", "vänster arm", "höger arm", "ben", "vänster ben", "höger ben"]
            
            # Kontrollera att det är en giltig kroppsdel
            if not any(part in body_part for part in valid_parts):
                await ctx.send("Du kan bara amputera armar och ben. Använd: `!amputera [arm/ben]`")
                return
                
            # Skapa embed
            color = color_handler.get_user_color(ctx.author.id)
            embed = discord.Embed(
                title=f"Amputation av {body_part}",
                description=f"{ctx.author.display_name} försöker amputera sin {body_part}...",
                color=color
            )
            
            # Slå för att se om amputeringen lyckas
            roll, total, is_naila, is_fumble = roll_d20(0)  # Slå d20 utan modifierare
            
            if roll >= 10 or is_naila:  # TV 10 för att lyckas
                # Amputeringen lyckades!
                embed.add_field(
                    name="Resultatet",
                    value=f"**LYCKAD AMPUTATION!** (Slår {roll})\nDu skrek dig hes men lyckades skära av den smittade kroppsdelen innan smittan spred sig. Två nya friska kort har lagts till i din smittokortlek.",
                    inline=False
                )
                
                # Lägg till två friska kort i kortleken
                infection_deck_manager.add_healthy_cards(str(ctx.author.id))
                
                # Beskrivning av konsekvenser
                consequences = ""
                if "arm" in body_part:
                    consequences = "Du har Nackdel på alla slag som kräver två armar."
                elif "ben" in body_part:
                    consequences = "Du har Nackdel på alla slag som kräver två ben och kan inte springa."
                    
                embed.add_field(
                    name="Konsekvenser",
                    value=consequences,
                    inline=False
                )
                
                if is_naila:
                    effect = get_naila_effect()
                    embed.add_field(
                        name="NAILA! 🔥",
                        value=effect,
                        inline=False
                    )
            else:
                # Amputeringen misslyckades
                failure_text = "Du misslyckades med amputeringen. Smittan har troligen redan spridit sig till resten av kroppen."
                
                if is_fumble:
                    effect = get_fucka_upp_effect()
                    failure_text += f"\n\n**FUCKA UPP!** 💀\n{effect}"
                
                embed.add_field(
                    name="Resultatet",
                    value=failure_text,
                    inline=False
                )
                
                # Värmen stiger i kroppen...
                embed.color = discord.Color.red()
            
            # Spåra tärningsslag
            try:
                roll_tracker.log_roll(
                    user_id=str(ctx.author.id),
                    user_name=ctx.author.display_name,
                    command_type='amputera',
                    num_dice=1,
                    sides=20,
                    roll_values=[roll],
                    modifier=0,
                    target=10,  # TV 10 för att lyckas med amputation
                    success=(roll >= 10)
                )
            except Exception as e:
                print(f"Fel vid loggning av tärningsslag: {e}")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            await ctx.send(f"Ett fel uppstod: {str(e)}")

    @bot.command(name='splatter')
    async def splatter_command(ctx: commands.Context, action: str = None, num_players: Optional[str] = None):
        try:
            if action is None:
                await ctx.send(
                    "Användning:\n"
                    "`!splatter reset [antal_spelare]`\n"
                    "`!splatter status`\n"
                    "`!splatter use [din beskrivning]`"
                )
                return

            action = action.lower()

            if action == "reset":
                if num_players is None or not num_players.isdigit():
                    await ctx.send("Du måste ange ett giltigt antal spelare! Exempel: `!splatter reset 4`")
                    return

                num_players_int = int(num_players)
                splatter_manager.reset_points(num_players_int)
                await ctx.send(f"Splatterpoäng återställda till {num_players_int}.")

            elif action == "status":
                status = splatter_manager.get_status()
                await ctx.send(f"Kvarvarande Splatterpoäng: {status['points']}/{status['max_points']}.")

            elif action == "use":
                description = num_players if num_players else "Ingen beskrivning angiven"
                if splatter_manager.use_point():
                    splatter_manager.add_description(description)
                    await ctx.send(
                        f"Splatterpoäng använd med beskrivningen: \"{description}\".\n"
                        "Effekt: Fördel på nästa slag och tredubbel skada!"
                    )
                else:
                    await ctx.send("Inga Splatterpoäng kvar!")
            else:
                await ctx.send("Okänd åtgärd. Använd reset, status eller use.")
        except Exception as e:
            await ctx.send(f"Ett fel uppstod: {str(e)}")
            
    # Returnera en lista av registrerade kommandofunktioner för referens
    return [
        rull_command, fordel_command, nackdel_command, 
        skada_command, traffzon_command, initiativ_command,
        smitta_command, sdih_help_command, amputera_command, 
        splatter_command
    ]
