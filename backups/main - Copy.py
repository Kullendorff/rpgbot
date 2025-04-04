import os
import random
import discord
from discord.ext import commands
from color_handler import ColorHandler
from roll_tracker import RollTracker
from dotenv import load_dotenv
from combat_manager import CombatManager
from damage_tables import DamageType
from hit_tables import WeaponType  # om du vill ha typ-checking
from fumble_tables import FUMBLE_TABLES, WEAPON_TYPE_ALIASES

# Ladda miljövariabler från .env filen
load_dotenv()

# Hämta Discord token från miljövariablerna
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
CHANNEL_IDS = os.getenv('CHANNEL_IDS')

print(f"Loaded DISCORD_TOKEN: {'Present' if DISCORD_TOKEN else 'Missing'}")
print(f"Loaded CHANNEL_IDS: {CHANNEL_IDS}")


# Konfigurera Discord-boten med nödvändiga behörigheter
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)
color_handler = ColorHandler()
roll_tracker = RollTracker()  # Skapa en instans av RollTracker
combat_manager = CombatManager()

# Konfigurera en undermapp för att lagra regler
RULES_FOLDER = "rules"
if not os.path.exists(RULES_FOLDER):
    os.makedirs(RULES_FOLDER)

@bot.event
async def on_ready():
    print(f"{bot.user} has connected to Discord!")

def parse_dice_string(dice_string: str):
    """
    Tolkar en tärningssträng med eventuell modifierare.
    Exempel: "3d6+2" returnerar (3, 6, 2)
             "4d8-1" returnerar (4, 8, -1)
             "2d10" returnerar (2, 10, 0)
    """
    # Leta efter + eller - i strängen
    modifier = 0
    if '+' in dice_string:
        dice_part, mod_part = dice_string.split('+')
        modifier = int(mod_part)
    elif '-' in dice_string:
        dice_part, mod_part = dice_string.split('-')
        modifier = -int(mod_part)
    else:
        dice_part = dice_string

    # Tolka tärningsdelen (NdX)
    num_dice, sides = map(int, dice_part.lower().split('d'))
    return num_dice, sides, modifier

@bot.command(name='startsession')
@commands.has_role('Game Master')
async def start_session(ctx, *, description: str = None):
    """Startar en ny spelsession och börjar spåra tärningskast."""
    session_id = roll_tracker.start_session(description)
    await ctx.send(f"Started new game session (ID: {session_id})")
    if description:
        await ctx.send(f"Session description: {description}")

@bot.command(name='endsession')
@commands.has_role('Game Master')
async def end_session(ctx):
    """Avslutar den aktiva spelsessionen."""
    roll_tracker.end_session()
    await ctx.send("Game session ended.")

@bot.command(name='showsession')
@commands.has_role('Game Master')
async def show_session(ctx):
    """Visar information om den aktiva sessionen."""
    if roll_tracker.current_session:
        await ctx.send(f"Active session ID: {roll_tracker.current_session}")
    else:
        await ctx.send("No active session.")
        
@bot.command(name='fummel')
async def fummel_command(ctx, vapentyp: str = None):
    """
    Slår på fummeltabellen för en specifik vapentyp.
    Användning: !fummel [vapentyp]
    Vapentyper: obe/nar/avs/sko
    """
    try:
        # Om ingen vapentyp angetts, visa hjälp
        if vapentyp is None:
            await ctx.send("Användning: `!fummel [vapentyp]`\n"
                         "Vapentyper:\n"
                         "- `obe` (obevapnat)\n"
                         "- `nar` (närstrid)\n"
                         "- `avs` (avståndsvapen)\n"
                         "- `sko` (sköldar)")
            return

        # Normalisera input
        vapentyp = vapentyp.lower()
        
        # Konvertera kort namn till långt namn
        if vapentyp not in WEAPON_TYPE_ALIASES:
            await ctx.send("Ogiltig vapentyp. Använd: obe, nar, avs, sko")
            return
            
        full_name = WEAPON_TYPE_ALIASES[vapentyp]

        # Slå T20 för att bestämma fummelresultat
        result = random.randint(1, 20)
        fummel_text = FUMBLE_TABLES[full_name][result]

        # Skapa en snygg embed för resultatet
        color = color_handler.get_user_color(ctx.author.id)
        embed = discord.Embed(
            title=f"💥 Fummel: {full_name.capitalize()}",
            description=f"Slag: {result}\n\n{fummel_text}",
            color=color
        )
        
        await ctx.send(embed=embed)

    except Exception as e:
        await ctx.send(f"Ett fel uppstod: {str(e)}")   
        
        
@bot.command(name='hugg')
async def hugg_command(ctx, level_or_location: str, damage: int, *, flags=""):
    """
    Hanterar kommandot !hugg.
    Användning: !hugg [nivå/område] [skada] [flaggor]
    """
    try:
        # Försök göra själva attack‐beräkningen
        result = combat_manager.process_attack(
            weapon_type="hugg",
            attack_level=level_or_location if level_or_location.lower() in ["låg", "normal", "hög"] else None,
            damage_value=damage,
            location_override=None if level_or_location.lower() in ["låg", "normal", "hög"] else level_or_location.lower(),
            is_mounted="--ryttare" in flags.lower(),
            is_quadruped="--djur" in flags.lower(),
            direction=None
        )

        # Formatera resultatet som text
        response = combat_manager.format_result(result)

        # Skapa en Embed i try-blocket
        color = color_handler.get_user_color(ctx.author.id)
        embed = discord.Embed(color=color)

        # Sätt hela texten som description (ingen ```backtick``!)
        embed.description = response

        # Skicka embed
        await ctx.send(embed=embed)

    except ValueError as e:
        # Om det blir fel i process_attack visar vi feltext i vanlig text
        await ctx.send(f"Fel: {str(e)}\nAnvändning: !hugg [nivå/område] [skada] [flaggor]")


@bot.command(name='stick')
async def stick_command(ctx, level_or_location: str, damage: int, *, flags=""):
    """
    Hanterar kommandot !stick.
    """
    try:
        result = combat_manager.process_attack(
            weapon_type="stick",
            attack_level=level_or_location if level_or_location.lower() in ["låg", "normal", "hög"] else None,
            damage_value=damage,
            location_override=None if level_or_location.lower() in ["låg", "normal", "hög"] else level_or_location.lower(),
            is_mounted="--ryttare" in flags.lower(),
            is_quadruped="--djur" in flags.lower(),
            direction=None
        )

        response = combat_manager.format_result(result)
        
        # Använd standard kodblock för konsekvent font
        formatted_response = f"```\n{response}\n```"
        
        color = color_handler.get_user_color(ctx.author.id)
        embed = discord.Embed(color=color)
        embed.description = formatted_response
        
        await ctx.send(embed=embed)

    except ValueError as e:
        await ctx.send(f"Fel: {str(e)}\nAnvändning: !stick [nivå/område] [skada] [flaggor]")

@bot.command(name='kross')
async def kross_command(ctx, level_or_location: str, damage: int, *, flags=""):
    """
    Hanterar kommandot !kross.
    """
    try:
        result = combat_manager.process_attack(
            weapon_type="kross",
            attack_level=level_or_location if level_or_location.lower() in ["låg", "normal", "hög"] else None,
            damage_value=damage,
            location_override=None if level_or_location.lower() in ["låg", "normal", "hög"] else level_or_location.lower(),
            is_mounted="--ryttare" in flags.lower(),
            is_quadruped="--djur" in flags.lower(),
            direction=None
        )

        response = combat_manager.format_result(result)
        
        # Använd standard kodblock för konsekvent font
        formatted_response = f"```\n{response}\n```"
        
        color = color_handler.get_user_color(ctx.author.id)
        embed = discord.Embed(color=color)
        embed.description = formatted_response
        
        await ctx.send(embed=embed)

    except ValueError as e:
        await ctx.send(f"Fel: {str(e)}\nAnvändning: !kross [nivå/område] [skada] [flaggor]")


@bot.command(name='dicehelp')
async def help_command(ctx):
    """Visar hjälpinformation för alla tillgängliga tärningskommandon."""
    color = color_handler.get_user_color(ctx.author.id)
    
    embed = discord.Embed(
        title="🎲 Kullens Terningsrullare",
        description="För alla dina tärningsbehov. Nästan",
        color=color
    )
    
    embed.add_field(
        name="Basic Dice Rolling",
        value=(
            "Roll any number and type of dice with optional modifier:\n"
            "`!roll NdX[+Z]` - Roll N dice with X sides and modifier Z\n"
            "Example: `!roll 3d6+2` - Rolls three 6-sided dice and adds 2\n"
            "\nLimits: Maximum 100 dice and 1000 sides per die"
        ),
        inline=False
    )
    
    embed.add_field(
        name="Exploding Dice",
        value=(
            "Roll dice that 'explode' when maximum value is rolled:\n"
            "`!ex NdX[+Z]` - Roll N exploding dice with X sides and modifier Z\n"
            "Example: `!ex 4d6-1` - Rolls four 6-sided exploding dice and subtracts 1\n"
            "\nWhen a die shows its maximum value (e.g., 6 on a d6), "
            "you get to roll 2 more dice!"
        ),
        inline=False
    )
    
    embed.add_field(
        name="Count Successes",
        value=(
            "Count dice results that meet or exceed a target number:\n"
            "`!count NdX TARGET` - Roll N X-sided dice and count results >= TARGET\n"
            "Example: `!count 5d10 7` - Rolls five d10s and counts how many show 7 or higher\n"
            "\nSuccessful rolls are shown in **bold**"
        ),
        inline=False
    )
    
    embed.add_field(
        name="Skill Checks",
        value=(
            "Roll against a target number:\n"
            "`!roll NdX[+Z] TARGET` - Regular skill check\n"
            "`!ex NdX[+Z] TARGET` - Exploding skill check\n"
            "Example: `!roll 4d6+2 24` - Rolls 4d6+2 against target number 24\n"
            "\n✅ Success if total ≤ target number\n"
            "❌ Failure if total > target number\n"
            "The result shows how much you succeeded or failed by"
        ),
        inline=False
    )
    
    embed.add_field(
        name="Session Tracking",
        value=(
            "Track dice rolls during your game sessions:\n"
            "`!startsession [description]` - Start tracking a new session\n"
            "`!endsession` - End the current session\n"
            "`!stats` - Show statistics for the current session\n"
            "`!mystats` - Show your personal statistics\n"
            "\nNote: Starting and ending sessions requires the 'Game Master' role"
        ),
        inline=False
    )
    
    embed.add_field(
        name="Secret Rolls (Game Master Only)",
        value=(
            "Make secret rolls that only show results to you:\n"
            "`!secret roll NdX[+Z]` - Secret normal roll\n"
            "`!secret ex NdX[+Z]` - Secret exploding roll\n"
            "`!secret count NdX TARGET` - Secret counting roll\n"
            "\nResults are sent via DM, and a discreet confirmation appears in the channel.\n"
            "All secret rolls are logged for session statistics."
        ),
        inline=False
    )
    
    await ctx.send(embed=embed)

@bot.command(name='secret')
@commands.has_role('Game Master')
async def secret_roll(ctx, *args):
    """
    Gör ett hemligt tärningskast som endast visas för spelledaren.
    Stödjer alla typer av tärningskast: roll, ex, och count.
    """
    try:
        # Försök ta bort originalmeddelandet för sekretess
        try:
            await ctx.message.delete()
        except:
            pass

        # Validera indata
        if len(args) < 1:
            await ctx.author.send("Använd formatet:\n"
                                "`!secret roll 2d6` - Vanligt slag\n"
                                "`!secret ex 3d6` - Exploderande slag\n"
                                "`!secret count 4d6 4` - Räkna resultat")
            return

        command_type = args[0].lower()
        dice_args = args[1:]

        # Skapa basembed för resultatet
        color = color_handler.get_user_color(ctx.author.id)
        result_embed = discord.Embed(
            title="🎲 Secret Roll",
            description=f"Command: !{command_type} {' '.join(dice_args)}",
            color=color
        )

        # Hantera olika typer av tärningskast
        if command_type == "roll":
            if len(dice_args) < 1 or len(dice_args) > 2:
                await ctx.author.send("Felaktigt format för roll-kommando")
                return

            dice = dice_args[0]
            target = int(dice_args[1]) if len(dice_args) == 2 else None
            
            num_dice, sides, modifier = parse_dice_string(dice)
            rolls = [random.randint(1, sides) for _ in range(num_dice)]
            total = sum(rolls) + modifier

            result_embed.add_field(name="Rolls", value=str(rolls), inline=False)
            if modifier != 0:
                result_embed.add_field(name="Modifier", value=str(modifier), inline=True)
            result_embed.add_field(name="Total", value=str(total), inline=True)

            if target is not None:
                difference = target - total
                success = total <= target
                result = f"✅ Success! ({difference:+d})" if success else f"❌ Failure ({difference:+d})"
                result_embed.add_field(name=f"Skill Check (Target: {target})", value=result, inline=False)

        elif command_type == "ex":
            if len(dice_args) < 1 or len(dice_args) > 2:
                await ctx.author.send("Felaktigt format för ex-kommando")
                return

            dice = dice_args[0]
            target = int(dice_args[1]) if len(dice_args) == 2 else None
            
            num_dice, sides, modifier = parse_dice_string(dice)
            all_rolls, final_total = exploding_replace_max(num_dice, sides, modifier)

            result_embed.add_field(name="All Rolls", value=str(all_rolls), inline=False)
            if modifier != 0:
                result_embed.add_field(name="Modifier", value=str(modifier), inline=True)
            result_embed.add_field(name=f"Final Total (excl. {sides}s)", value=str(final_total), inline=True)

            if target is not None:
                difference = target - final_total
                success = final_total <= target
                result = f"✅ Success! ({difference:+d})" if success else f"❌ Failure ({difference:+d})"
                result_embed.add_field(name=f"Skill Check (Target: {target})", value=result, inline=False)

        elif command_type == "count":
            if len(dice_args) != 2:
                await ctx.author.send("Felaktigt format för count-kommando")
                return

            dice, target = dice_args
            target = int(target)
            
            num_dice, sides, modifier = parse_dice_string(dice)
            if modifier != 0:
                await ctx.author.send("Modifierare stöds inte för count-kommandon")
                return

            rolls = [random.randint(1, sides) for _ in range(num_dice)]
            successes = sum(1 for roll in rolls if roll >= target)
            formatted_rolls = [f"**{roll}**" if roll >= target else str(roll) for roll in rolls]
            
            roll_display = ", ".join(formatted_rolls)
            result_embed.add_field(name="Rolls", value=f"[{roll_display}]", inline=False)
            
            success_text = "Success" if successes == 1 else "Successes"
            success_display = f"✨ {successes} {success_text}"
            if successes == 0:
                success_display = "❌ No successes"
            
            result_embed.add_field(name="Results", value=success_display, inline=False)

        else:
            await ctx.author.send("Ogiltigt kommando. Använd 'roll', 'ex', eller 'count'.")
            return

        # Logga det hemliga slaget
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

        # Skicka det detaljerade resultatet till spelledaren
        await ctx.author.send(embed=result_embed)

        # Skicka en diskret bekräftelse i kanalen
        confirm_embed = discord.Embed(
            title="🎲 Secret Roll",
            description=f"{ctx.author.display_name} made a secret {command_type}",
            color=color
        )
        await ctx.send(embed=confirm_embed)

    except Exception as e:
        await ctx.author.send(f"Ett fel uppstod: {str(e)}")

@bot.command(name='count')
async def count_command(ctx, *args):
    try:
        # Kontrollera att vi har rätt antal argument
        if len(args) != 2:
            await ctx.send("Use format: `!count YdX Z` (e.g. `!count 5d10 7` to count results >= 7)")
            return

        # Tolka tärningskastet och målvärdet
        dice, target = args
        target = int(target)
        
        # Använd vår befintliga parse_dice_string funktion
        num_dice, sides, modifier = parse_dice_string(dice)
        if modifier != 0:
            await ctx.send("Modifiers are not supported for counting successes!")
            return
            
        if num_dice > 100 or sides > 1000:
            await ctx.send("Too many dice or sides!")
            return
            
        if target > sides:
            await ctx.send(f"Target number ({target}) cannot be higher than die sides ({sides})!")
            return

        # Slå tärningarna och räkna lyckade resultat
        color = color_handler.get_user_color(ctx.author.id)
        rolls = [random.randint(1, sides) for _ in range(num_dice)]
        
        # Räkna lyckade slag och skapa en lista med formaterade resultat
        successes = sum(1 for roll in rolls if roll >= target)
        formatted_rolls = [f"**{roll}**" if roll >= target else str(roll) for roll in rolls]
        
        # Logga tärningsslaget
        roll_tracker.log_roll(
            user_id=str(ctx.author.id),
            user_name=ctx.author.display_name,
            command_type='count',
            num_dice=num_dice,
            sides=sides,
            roll_values=rolls,
            target=target,
            success=None  # För count behandlar vi framgång annorlunda
        )
        
        # Skapa embed med resultaten
        embed = discord.Embed(
            title=f"{ctx.author.display_name}'s Count Check",
            description=f"**Rolling {num_dice}d{sides}**, counting results >= {target}",
            color=color
        )
        
        # Visa resultaten med fetstil för lyckade slag
        roll_display = ", ".join(formatted_rolls)
        embed.add_field(
            name="Rolls", 
            value=f"[{roll_display}]", 
            inline=False
        )
        
        # Visa antal lyckade slag
        success_text = "Success" if successes == 1 else "Successes"
        success_display = f"✨ {successes} {success_text}"
        if successes == 0:
            success_display = "❌ No successes"
            
        embed.add_field(
            name="Results", 
            value=success_display, 
            inline=False
        )

        await ctx.send(embed=embed)
        
    except ValueError:
        await ctx.send("Use format: `!count YdX Z` (e.g. `!count 5d10 7` to count results >= 7)")

@bot.command(name='roll')
async def roll_command(ctx, *args):
    try:
        # Kontrollera om vi har ett eller två argument
        if len(args) == 1:
            dice = args[0]
            target = None
        elif len(args) == 2:
            dice, target = args
            target = int(target)
        else:
            await ctx.send("Use format: `!roll YdX[+Z]` or `!roll YdX[+Z] TARGET` (e.g. `!roll 2d6+1` or `!roll 4d6-2 24`)")
            return

        # Tolka tärningskastet med eventuell modifierare
        num_dice, sides, modifier = parse_dice_string(dice)
        if num_dice > 100 or sides > 1000:
            await ctx.send("Too many dice or sides!")
            return

        # Slå tärningarna och beräkna summan
        color = color_handler.get_user_color(ctx.author.id)
        rolls = [random.randint(1, sides) for _ in range(num_dice)]
        total = sum(rolls) + modifier

        # Lägg till loggning av kastet
        success = None
        if target is not None:
            success = total <= target
        
        roll_tracker.log_roll(
            user_id=str(ctx.author.id),
            user_name=ctx.author.display_name,
            command_type='roll',
            num_dice=num_dice,
            sides=sides,
            roll_values=rolls,
            modifier=modifier,
            target=target,
            success=success
        )

        # Skapa embed med grundläggande information
        embed = discord.Embed(
            title=f"{ctx.author.display_name}'s Roll",
            description=f"**Rolling {num_dice}d{sides}{'+' + str(modifier) if modifier > 0 else str(modifier) if modifier < 0 else ''}**",
            color=color
        )
        embed.add_field(name="Rolls", value=str(rolls), inline=False)
        if modifier != 0:
            embed.add_field(name="Modifier", value=str(modifier), inline=True)
        embed.add_field(name="Total", value=str(total), inline=True)

        # Om vi har ett målvärde, lägg till resultatet av färdighetskontrollen
        if target is not None:
            difference = target - total
            if total <= target:
                result = f"✅ Success! ({difference:+d})"
            else:
                result = f"❌ Failure ({difference:+d})"
            embed.add_field(name=f"Skill Check (Target: {target})", value=result, inline=False)

        await ctx.send(embed=embed)
    except ValueError:
        await ctx.send("Use format: `!roll YdX[+Z]` or `!roll YdX[+Z] TARGET` (e.g. `!roll 2d6+1` or `!roll 4d6-2 24`)")
        
@bot.command(name='ex')
async def ex_command(ctx, *args):
    """
    Gör ett obegränsat T6-slag (Ob-slag) och kollar perfekt/fummel.
    Exempel:
      !ex 3d6
      !ex 2d6+1
      !ex 3d6 15
      !ex 2d6+2 10
    """
    try:
        # 1) Hantera argument - antingen [dice] eller [dice, target]
        if len(args) == 1:
            dice = args[0]
            target = None
        elif len(args) == 2:
            dice, target = args
            target = int(target)
        else:
            await ctx.send(
                "Använd: `!ex Xd6[+Z]` eller `!ex Xd6[+Z] [Målvärde]`\n"
                "Ex: `!ex 3d6+2`, `!ex 2d6 12`, `!ex 4d6+1 20`"
            )
            return

        # 2) Parsar tärningssträngen (t.ex. '3d6+1')
        num_dice, sides, modifier = parse_dice_string(dice)

        # 3) Kontrollera att det verkligen är d6 (ob-slag)
        if sides != 6:
            await ctx.send("Det obegränsade T6-slaget (ex) måste vara d6!")
            return

        # 4) Säkerhetskoll
        if num_dice < 1:
            await ctx.send("Du måste slå minst 1 tärning!")
            return
        if num_dice > 100:
            await ctx.send("För många tärningar!")
            return

        # 5) Slå de obegränsade tärningarna (inkl expansionslogik)
        #    Vi vill också kunna se vilka resultat som kom i 'första kastet'
        #    vs. expansionskasten. Om din unlimited_d6s redan returnerar
        #    initial_rolls och all_rolls kan du använda den direkt.
        all_rolls, final_total, initial_rolls = unlimited_d6s(num_dice, modifier)

        # 6) Kolla Perfekt/Fummel förutsättningar innan expansions:
        #    a) Perfekt villkor (1): "Alla tärningar utfaller med '1', med undantag för högst en"
        #       eller specialfallet Ob1T6 => (1), (2) eller (3).
        perfect_candidate = False
        if num_dice == 1:
            # Om första kastet är bara 1 tärning => den måste vara 1, 2 eller 3
            if initial_rolls[0] in [1, 2, 3]:
                perfect_candidate = True
        else:
            # Om fler än 1 tärning => räkna hur många som INTE är 1
            not_one_count = sum(1 for r in initial_rolls if r != 1)
            # Om "alla är 1 förutom max en tärning"
            if not_one_count <= 1:
                perfect_candidate = True

        # b) Fummel villkor (1): "Två eller fler '6' vid första kastet"
        six_count = sum(1 for r in initial_rolls if r == 6)
        fumble_candidate = (six_count >= 2)

        # 7) Kolla hur det gick mot target
        #    (Nu har vi expansionsresultat => final_total)
        #    Perfekt/fummel är bara relevant om man har en target
        #    men om du vill kan du tillåta dem även utan target.
        #    Här utgår vi ifrån att "perfect" och "fumble" bara
        #    är meningsfulla när man slår mot ett målvärde/färdighet.
        success = None
        result_text = None
        if target is not None:
            if final_total <= target:
                # LYCKAT
                success = True
                # Om vi också uppfyllde perfect_condition_1 => Perfekt
                if perfect_candidate:
                    result_text = "✨ **Perfekt slag!** (lyckat)"
                else:
                    result_text = "✅ **Lyckat slag**"
            else:
                # MISSLYCKAT
                success = False
                # Om vi också uppfyllde fummel_condition_1 => Fummel
                if fumble_candidate:
                    result_text = "💥 **FUMMEL!**"
                else:
                    result_text = "❌ **Misslyckat**"
        else:
            # Ingen target => bara visa totalen
            result_text = "Resultat: " + str(final_total)

        # 8) Bygg Embed för snygg presentation
        color = color_handler.get_user_color(ctx.author.id)
        embed = discord.Embed(
            title=f"{ctx.author.display_name}'s Obegränsade T6-slag",
            description=(
                f"**{num_dice}d6"
                f"{'+' + str(modifier) if modifier > 0 else str(modifier) if modifier < 0 else ''}**\n"
                "(Varje 6 tas bort från summan men genererar +2 nya tärningar)"
            ),
            color=color
        )
        embed.add_field(
            name="Första kastomgången",
            value=str(initial_rolls),
            inline=False
        )
        embed.add_field(
            name="Alla kast (inkl. extra)",
            value=str(all_rolls),
            inline=False
        )
        embed.add_field(
            name="Slutsumma (utan 6:or) + ev. modifierare",
            value=str(final_total),
            inline=True
        )

        # Om det finns en target, visa skill-check-resultat
        if target is not None:
            difference = target - final_total
            embed.add_field(
                name=f"Motståndsvärde: {target}",
                value=f"{result_text}\n(Marginal: {difference:+d})",
                inline=False
            )
        else:
            # Ingen target => "Vanligt" slag
            embed.add_field(
                name="Resultat",
                value=result_text,
                inline=False
            )

        await ctx.send(embed=embed)

        # 9) Logga i RollTracker
        #    Sätt success=True/False om vi hade en target, annars None
        roll_tracker.log_roll(
            user_id=str(ctx.author.id),
            user_name=ctx.author.display_name,
            command_type='ex',
            num_dice=num_dice,
            sides=6,
            roll_values=all_rolls,
            modifier=modifier,
            target=target,
            success=success
        )

    except ValueError:
        await ctx.send(
            "Felaktigt format. Exempel:\n"
            "`!ex 3d6`, `!ex 3d6+1`, `!ex 4d6 18`, `!ex 2d6+2 15`"
        )


def unlimited_d6s(num_dice: int, modifier: int = 0):
    """
    Slår X st 6-sidiga tärningar enligt 'obegränsat'-regeln:
    - Varje 6a räknas inte i summan men genererar +2 nya tärningar.
    - Upprepa tills inga nya tärningar finns kvar.
    Returnerar:
      all_rolls: lista med samtliga rullade tärningar (första + expansions)
      final_total: slutgiltig summa (exkl. 6:or) + modifier
      initial_rolls: endast första kastomgången
    """
    import random

    # Första omgången
    initial_rolls = [random.randint(1, 6) for _ in range(num_dice)]
    all_rolls = initial_rolls[:]  # Kopiera för historik
    final_total = sum(r for r in initial_rolls if r != 6)

    # Extra tärningar att slå för varje 6
    extra_dice = 0
    for r in initial_rolls:
        if r == 6:
            extra_dice += 2

    # Slå expansions-tärningar
    while extra_dice > 0:
        roll = random.randint(1, 6)
        all_rolls.append(roll)
        extra_dice -= 1
        if roll == 6:
            # En 6a genererar ytterligare 2 tärningar
            extra_dice += 2
        else:
            # Om inte 6, lägg till i summan
            final_total += roll

    # Lägg på ev. modifier
    final_total += modifier

    return all_rolls, final_total, initial_rolls

    
@bot.command(name='stats')
async def stats_command(ctx, session_id: str = None):
    """Visar statistik för den aktiva sessionen eller en specifik session."""
    stats = roll_tracker.get_session_stats(session_id)
    
    if "error" in stats:
        await ctx.send(stats["error"])
        return

    color = color_handler.get_user_color(ctx.author.id)
    embed = discord.Embed(
        title="Session Statistics",
        description=(
            f"Session: {session_id or roll_tracker.current_session}\n"
            f"Total Players: {stats['session_info']['unique_players']}\n"
            f"Total Rolls: {stats['session_info']['total_rolls']}"
        ),
        color=color
    )

    # Session Information
    session_info = stats["session_info"]
    embed.add_field(
        name="Session Info",
        value=(
            f"Started: {session_info['start_time']}\n"
            f"{'Ended: ' + session_info['end_time'] if session_info['end_time'] else 'Still active'}\n"
            f"Description: {session_info['description'] or 'No description'}"
        ),
        inline=False
    )

    # Player Statistics
    players_text = ""
    for player in stats["player_stats"]:
        players_text += (
            f"**{player['name']}**\n"
            f"Rolls: {player['total_rolls']}"
        )
        if player['successes'] + player['failures'] > 0:
            players_text += f" (Success rate: {player['success_rate']}%)"
        players_text += "\n"

    if players_text:
        embed.add_field(
            name="Player Statistics",
            value=players_text,
            inline=False
        )

    # Command Usage
    if stats["command_stats"]:
        cmd_text = "\n".join(
            f"{cmd['command']}: {cmd['uses']} uses" +
            (f" ({cmd['success_rate']}% success)" if cmd['success_rate'] is not None else "")
            for cmd in stats["command_stats"]
        )
        embed.add_field(
            name="Command Usage",
            value=cmd_text,
            inline=False
        )

    # Popular Dice Types
    if stats["popular_dice"]:
        dice_text = "\n".join(
            f"{dice['type']}: {dice['uses']} times"
            for dice in stats["popular_dice"]
        )
        embed.add_field(
            name="Most Used Dice",
            value=dice_text,
            inline=False
        )

    await ctx.send(embed=embed)

@bot.command(name='mystats')
async def my_stats_command(ctx, session_id: str = None):
    """Visar statistik för den aktiva spelaren."""
    stats = roll_tracker.get_player_stats(str(ctx.author.id), session_id)
    
    if "error" in stats:
        await ctx.send(stats["error"])
        return

    color = color_handler.get_user_color(ctx.author.id)
    embed = discord.Embed(
        title=f"Stats for {ctx.author.display_name}",
        description=f"Session: {session_id or roll_tracker.current_session}",
        color=color
    )

    # Visa de senaste tärningskasten
    recent_rolls = stats["rolls"][:5]  # Visa bara de 5 senaste
    if recent_rolls:
        roll_text = "\n".join(
            f"{r['command']} {r['dice']}" +
            (f" (Target: {r['target']})" if r['target'] else "") +
            f": {r['values']}" +
            (f" {'✅' if r['success'] else '❌'}" if r['success'] is not None else "")
            for r in recent_rolls
        )
        embed.add_field(
            name="Recent Rolls",
            value=roll_text,
            inline=False
        )
    else:
        embed.add_field(
            name="Recent Rolls",
            value="No rolls yet",
            inline=False
        )

    await ctx.send(embed=embed)
    
@bot.command(name="regel")
async def regel_command(ctx, *args):
    """
    Hantera regler:
    1. Kör `!regel` för att lista alla regler.
    2. Kör `!regel [namn eller nummer]` för att visa en specifik regel.
    """
    if not args:
        # Lista alla regler
        rules = os.listdir(RULES_FOLDER)
        if not rules:
            await ctx.send("Det finns inga regler ännu.")
            return

        response = "**Tillgängliga regler:**\n"
        for i, rule_file in enumerate(rules, start=1):
            rule_name = os.path.splitext(rule_file)[0]  # Ta bort filändelsen
            response += f"{i}. {rule_name}\n"
        await ctx.send(response)

    else:
        # Visa en specifik regel baserat på namn eller nummer
        identifier = args[0].lower()
        rules = os.listdir(RULES_FOLDER)

        try:
            if identifier.isdigit():
                # Hämta regel med nummer
                rule_index = int(identifier) - 1
                if rule_index < 0 or rule_index >= len(rules):
                    raise IndexError
                rule_file = rules[rule_index]
            else:
                # Hämta regel med namn
                rule_file = f"{identifier}.txt"
                if rule_file not in rules:
                    raise FileNotFoundError

            # Läs och dela upp långt innehåll
            with open(os.path.join(RULES_FOLDER, rule_file), "r", encoding="utf-8") as f:
                content = f.read()

            rule_name = os.path.splitext(rule_file)[0]
            if len(content) <= 2000:
                await ctx.send(f"**{rule_name}**:\n{content}")
            else:
                # Dela upp innehållet i block på max 2000 tecken
                chunks = [content[i:i+2000] for i in range(0, len(content), 2000)]
                await ctx.send(f"**{rule_name}**: (uppdelat i flera meddelanden)")
                for chunk in chunks:
                    await ctx.send(chunk)

        except (IndexError, FileNotFoundError):
            await ctx.send("Regeln kunde inte hittas. Kontrollera namnet eller numret.")

    

# Starta Discord-boten
if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)