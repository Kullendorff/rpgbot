import random
import time
from typing import List, Optional, Tuple, Any
import discord
from discord.ext import commands

def register_dice_commands(bot, roll_tracker, color_handler, embed_factory, knowledge_base):
    """Registrera alla tärnings-relaterade kommandon."""
    
    # Import här för att undvika cirkulära imports
    from core.constants import UMNATAK_ID, MAX_DICE, MAX_SIDES, UMNATAK_SUCCESS_COMMENTS
    from core.dice_parser import parse_dice_string, InvalidDiceFormat, DiceLimitsError
    from core.dice_engine import unlimited_d6s, simulate_unlimited_dice
    from utils.text_utils import clean_unicode
    
    def get_sarcastic_comment_for_umnatak() -> Optional[str]:
        """
        Returnerar en slumpmässig syrlig kommentar om Umnatak, men endast cirka 30% av gångerna.
        Övriga gånger returneras None för att inte överanvända skämten.
        """
        # Använd tidsbaserat seed för att variera sannolikheten
        random.seed(int(time.time()))
        
        # Endast cirka 30% av gångerna returnera en kommentar
        if random.random() < 0.3:  # 30% chans
            return random.choice(UMNATAK_SUCCESS_COMMENTS)
        return None

    @bot.command(name='count')
    async def count_command(ctx: commands.Context, *args) -> None:
        """
        Räkna antalet lyckade tärningsslag.
        
        Använd format: !count YdX TARGET
        Exempel: !count 5d10 7
        
        Args:
            ctx (commands.Context): Kontexten för kommandot.
            *args: Kommandots argument.
        """
        try:
            if len(args) != 2:
                await ctx.send("Use format: `!count YdX Z` (e.g. `!count 5d10 7` to count results >= 7)")
                return

            dice, target_str = args
            try:
                target: int = int(target_str)
            except ValueError:
                await ctx.send(f"❌ Felaktigt målvärde: '{target_str}' är inte ett giltigt tal")
                return
            
            # Parsa tärningsspecifikationen med nya parser
            try:
                spec = parse_dice_string(dice)
                num_dice, sides, modifier = spec.count, spec.sides, spec.modifier
            except InvalidDiceFormat as e:
                await ctx.send(f"❌ Felaktigt format: {e}")
                return
            except DiceLimitsError as e:
                await ctx.send(f"⚠️ Gränser överskrids: {e}")
                return
                
            if modifier != 0:
                await ctx.send("Modifiers are not supported for counting successes!")
                return
            if target > sides:
                await ctx.send(f"Target number ({target}) cannot be higher than die sides ({sides})!")
                return

            color: int = color_handler.get_user_color(ctx.author.id)
            rolls: List[int] = [random.randint(1, sides) for _ in range(num_dice)]
            successes: int = sum(1 for roll in rolls if roll >= target)
            formatted_rolls: List[str] = [f"**{roll}**" if roll >= target else str(roll) for roll in rolls]

            roll_tracker.log_roll(
                user_id=str(ctx.author.id),
                user_name=ctx.author.display_name,
                command_type='count',
                num_dice=num_dice,
                sides=sides,
                roll_values=rolls,
                target=target,
                success=None
            )

            embed = embed_factory.dice_result(
                ctx.author.id,
                ctx.author.display_name,
                "count",
                f"{num_dice}d{sides}",
                rolls,
                None,  # No total for count
                target,
                successes > 0
            )
            
            # Add custom field for count results
            success_text: str = "Success" if successes == 1 else "Successes"
            success_display: str = f"✨ {successes} {success_text}" if successes > 0 else "❌ No successes"
            embed.add_field(name="Träffar", value=success_display, inline=False)

            await ctx.send(embed=embed)
            
            # Om det är Umnatak och han lyckades, lägg eventuellt till en syrlig kommentar
            success = successes > 0
            if str(ctx.author.id) == UMNATAK_ID and target is not None and success:  
                comment = get_sarcastic_comment_for_umnatak()
                if comment:
                    await ctx.send(f"*{comment}*")
                    
        except ValueError:
            await ctx.send("Use format: `!count YdX Z` (e.g. `!count 5d10 7` to count results >= 7)")

    @bot.command(name='roll')
    async def roll_command(ctx: commands.Context, *args) -> None:
        """
        Rulla tärningar enligt formeln YdX[+Z] [TARGET].
        
        Använd format:
          !roll YdX[+Z]
          !roll YdX[+Z] TARGET
        
        Exempel:
          !roll 2d6+1
          !roll 4d6-2 24
        
        Args:
            ctx (commands.Context): Kontexten för kommandot.
            *args: Kommandots argument.
        """
        try:
            arg_string = ' '.join(args).lower()
            has_demon_inspiration = "--de" in arg_string
            
            # Ta bort --de flaggan från argumenten om den finns
            clean_arg_string = arg_string.replace("--de", "").strip()
            clean_args = clean_arg_string.split()
            
            # Debug-utskrift
            if has_demon_inspiration:
                print(f"[DEBUG] Demonisk inspiration aktiverad av {ctx.author.display_name} i !roll {args}")
                try:
                    await ctx.author.send(f"🔥 Demonisk inspiration aktiverad")
                except Exception as e:
                    print(f"Kunde inte skicka PM: {e}")

            # Använd den rensade argumentlistan för att tolka tärningskommandot
            if len(clean_args) == 1:
                dice: str = clean_args[0]
                target: Optional[int] = None
            elif len(clean_args) == 2:
                dice, target_str = clean_args
                try:
                    target = int(target_str)
                except ValueError:
                    dice = clean_args[0]
                    target = None
            else:
                await ctx.send("Use format: `!roll YdX[+Z]` or `!roll YdX[+Z] TARGET` (e.g. `!roll 2d6+1` or `!roll 4d6-2 24`)")
                return

            # Parsa tärningsspecifikationen med nya parser
            try:
                spec = parse_dice_string(dice)
                num_dice, sides, modifier = spec.count, spec.sides, spec.modifier
            except InvalidDiceFormat as e:
                await ctx.send(f"❌ Felaktigt format: {e}")
                return
            except DiceLimitsError as e:
                await ctx.send(f"⚠️ Gränser överskrids: {e}")
                return

            # Om vi har demonisk influens och ett målvärde, se till att "lyckas" oavsett tärningsslag
            should_force_success = has_demon_inspiration and target is not None
            
            color: int = color_handler.get_user_color(ctx.author.id)
            rolls: List[int] = [random.randint(1, sides) for _ in range(num_dice)]
            total: int = sum(rolls) + modifier

            # Spara det ÄKTA kastet för statistiken: vid demonisk inspiration
            # riggas de visade tärningarna/totalen, men rolls.db ska logga
            # vad som faktiskt slogs — inte förfalskningen.
            genuine_rolls: List[int] = list(rolls)
            genuine_total: int = total

            # Manipulera resultatet vid demonisk influens
            if should_force_success:
                # Visat resultat riggas till en knapp framgång (1-3 under mål);
                # det äkta kastet ovan är redan säkrat för statistik.
                success_margin = random.randint(1, 3)
                original_total = total  # Spara det faktiska resultatet för intern spårning
                total = target - success_margin  # Ändra totalen så att den precis klarar målvärdet

                # Beräkna vilket villånger nu gör att denna summa uppnås
                rolls_sum = total - modifier
                
                # Förfalska tärningarna - om detta används av spelledaren kan spelarna inte se
                # att vi har manipulerat resultatet
                if rolls_sum > 0:  # Se till att vi inte försöker göra ommöjliga tärningsslag
                    # Resetta tärningarna och förfalska dem
                    rolls = []  # Töm listan med tärningsslag
                    remaining = rolls_sum
                    
                    # Fördela värden till tärningarna
                    for i in range(num_dice - 1):
                        # Gör så de flesta tärningar visar rimliga värden
                        max_val = min(sides, remaining - (num_dice - i - 1))  # Lämna minst 1 för varje återstående tärning
                        if max_val < 1:
                            max_val = 1
                        val = random.randint(1, max_val)
                        rolls.append(val)
                        remaining -= val
                    
                    # Sista tärningen får ta resten av värdet
                    if remaining > sides:  # Om vi fortfarande har för mycket kvar
                        # Gör mer jämn fördelning för att vara mer trovdig
                        while remaining > sides and len(rolls) > 0:
                            idx = random.randint(0, len(rolls) - 1)
                            extra = min(sides - rolls[idx], remaining - sides)
                            if extra > 0:
                                rolls[idx] += extra
                                remaining -= extra
                        
                        # Om vi fortfarande har för mycket kan vi bara låtsas att modifieraren är högre
                        if remaining > sides:
                            rolls.append(sides)  # Sista tärningen visar max
                        else:
                            rolls.append(remaining)  # Sista tärningen tar resten
                    else:
                        rolls.append(remaining)  # Normal fördelning fungerar bra
                    
                    # Blanda tärningarna för att dölja mönstret
                    random.shuffle(rolls)

            success: Optional[bool] = None
            if target is not None:
                success = total <= target
            genuine_success: Optional[bool] = target is not None and genuine_total <= target

            roll_tracker.log_roll(
                user_id=str(ctx.author.id),
                user_name=ctx.author.display_name,
                command_type='roll',
                num_dice=num_dice,
                sides=sides,
                roll_values=genuine_rolls,
                modifier=modifier,
                target=target,
                success=genuine_success
            )

            # Bygg dice expression för display
            dice_expr = f"{num_dice}d{sides}"
            if modifier > 0:
                dice_expr += f"+{modifier}"
            elif modifier < 0:
                dice_expr += str(modifier)
                
            embed = embed_factory.dice_result(
                ctx.author.id,
                ctx.author.display_name,
                "roll",
                dice_expr,
                rolls,
                total,
                target,
                success
            )
            
            # Add modifier field if present
            if modifier != 0:
                embed.add_field(name="Modifierare", value=str(modifier), inline=True)
                
            await ctx.send(embed=embed)
            
            # Om det är Umnatak och han lyckades, lägg eventuellt till en syrlig kommentar
            if str(ctx.author.id) == UMNATAK_ID and target is not None and success:  
                comment = get_sarcastic_comment_for_umnatak()
                if comment:
                    await ctx.send(f"*{comment}*")
                    
        except ValueError:
            await ctx.send("Use format: `!roll YdX[+Z]` or `!roll YdX[+Z] TARGET` (e.g. `!roll 2d6+1` or `!roll 4d6-2 24`)")

    @bot.command(name='ex')
    async def ex_command(ctx: commands.Context, *args) -> None:
        """
        Gör ett obegränsat T6-slag (Ob-slag) och kollar perfekt/fummel.
        
        Exempel:
          !ex 3d6
          !ex 2d6+1
          !ex 3d6 15
          !ex 2d6+2 10
          !ex 3d6 18 --de  (aktiverar demonisk hjälp)
        
        Args:
            ctx (commands.Context): Kontexten för kommandot.
            *args: Kommandots argument.
        """
        try:
            # Förenklad hantering av argumenten
            arg_string = ' '.join(args).lower()
            
            # Kontrollera om demonisk hjälp är aktiverad
            has_demon_inspiration = "--de" in arg_string
            
            # Ta bort --de flaggan från strängen
            clean_arg_string = arg_string.replace("--de", "").strip()
            clean_args = clean_arg_string.split()
            
            # Skicka diskret bekräftelse till spelledaren om demonisk hjälp aktiveras
            if has_demon_inspiration:
                print(f"[DEBUG] Demonisk inspiration aktiverad av {ctx.author.display_name} i !ex {args}")
                try:
                    await ctx.author.send(f"🔥 Demonisk inspiration aktiverad")
                except Exception as e:
                    print(f"Kunde inte skicka PM: {e}")
            
            # Tolka argument
            if len(clean_args) == 1:
                dice: str = clean_args[0]
                target: Optional[int] = None
            elif len(clean_args) == 2:
                dice, target_str = clean_args
                try:
                    target = int(target_str)
                except ValueError:
                    await ctx.send(f"❌ Felaktigt målvärde: '{target_str}' är inte ett giltigt tal")
                    return
            else:
                await ctx.send(
                    "Använd: `!ex Xd6[+Z]` eller `!ex Xd6[+Z] [Målvärde]`\n"
                    "Ex: `!ex 3d6+2`, `!ex 2d6 12`, `!ex 4d6+1 20`"
                )
                return

            # Parsa tärningsspecifikationen med nya parser
            try:
                spec = parse_dice_string(dice)
                num_dice, sides, modifier = spec.count, spec.sides, spec.modifier
            except InvalidDiceFormat as e:
                await ctx.send(f"❌ Felaktigt format: {e}")
                return
            except DiceLimitsError as e:
                await ctx.send(f"⚠️ Gränser överskrids: {e}")
                return
                
            if sides != 6:
                await ctx.send("Det obegränsade T6-slaget (ex) måste vara d6!")
                return

            # Slå tärningarna enligt obegränsad regel
            all_rolls, final_total, initial_rolls = unlimited_d6s(num_dice, modifier)

            # Om vi har demonisk hjälp och ett målvärde, manipulera resultatet vid behov
            if has_demon_inspiration and target is not None:
                # Ändra resultatet bara om det skulle misslyckas, annars behåll ursprungligt resultat
                if final_total > target:
                    # Spara ursprungligt resultat för loggning
                    original_final_total = final_total
                    
                    # Manipulera resultatet så det precis klarar målvärdet med 1-3 enheter
                    success_margin = random.randint(1, 3)
                    final_total = target - success_margin
                    
                    # Logga inte synligt men skriv ut debug-information
                    print(f"[DEBUG] Manipulerade resultat från {original_final_total} till {final_total}")

            # Kontrollera perfekta och fummelkriterier
            perfect_candidate: bool = False
            if num_dice == 1:
                if initial_rolls[0] in [1, 2, 3]:
                    perfect_candidate = True
            else:
                not_one_count: int = sum(1 for r in initial_rolls if r != 1)
                if not_one_count <= 1:
                    perfect_candidate = True

            six_count: int = sum(1 for r in initial_rolls if r == 6)
            fumble_candidate: bool = (six_count >= 2)

            success: Optional[bool] = None
            result_text: Optional[str] = None
            if target is not None:
                # När demonisk hjälp är aktiverad, se till att slaget alltid lyckas
                if has_demon_inspiration:
                    success = True
                    result_text = "✨ **Perfekt slag!** (lyckat)" if perfect_candidate else "✅ **Lyckat slag**"
                else:
                    # Normalt beteende utan demonisk hjälp
                    if final_total <= target:
                        success = True
                        result_text = "✨ **Perfekt slag!** (lyckat)" if perfect_candidate else "✅ **Lyckat slag**"
                    else:
                        success = False
                        result_text = "💥 **FUMMEL!**" if fumble_candidate else "❌ **Misslyckat**"
            else:
                result_text = "Resultat: " + str(final_total)

            # Bygg dice expression för display  
            dice_expr = f"{num_dice}d6"
            if modifier > 0:
                dice_expr += f"+{modifier}"
            elif modifier < 0:
                dice_expr += str(modifier)
                
            embed = embed_factory.dice_result(
                ctx.author.id,
                ctx.author.display_name,
                "ex",
                dice_expr,
                initial_rolls,
                final_total,
                target,
                success
            )
            embed.add_field(name="Alla kast (inkl. extra)", value=str(all_rolls), inline=False)

            if target is not None:
                difference: int = target - final_total
                embed.add_field(
                    name=f"Motståndsvärde: {target}",
                    value=f"{result_text}\n(Marginal: {difference:+d})",
                    inline=False
                )
            else:
                embed.add_field(name="Resultat", value=result_text, inline=False)
                
            # Lägg till information om perfekt slag eller fummel
            if perfect_candidate or fumble_candidate:
                special_result = []
                if perfect_candidate:
                    special_result.append("\u2728 **PERFEKT SLAG!** Tärningsoraklet ler mot dig.")
                if fumble_candidate:
                    special_result.append("\ud83d\udca5 **FUMMEL!** Tärningsoraklet skrattar åt din olycka.")
                    
                embed.add_field(
                    name="Särskilt Utfall",
                    value="\n".join(special_result),
                    inline=False
                )
            # Rensa alla fält i embed från eventuella surrogatpar
            embed.title = clean_unicode(embed.title)
            embed.description = clean_unicode(embed.description)

            # Rensa varje fält i embed
            for i, field in enumerate(embed.fields):
                embed.fields[i].name = clean_unicode(field.name)
                embed.fields[i].value = clean_unicode(field.value)
            await ctx.send(embed=embed)
            
            # Om det är Umnatak och han lyckades, lägg eventuellt till en syrlig kommentar
            if str(ctx.author.id) == UMNATAK_ID and target is not None and success:  
                comment = get_sarcastic_comment_for_umnatak()
                if comment:
                    await ctx.send(f"*{comment}*")

            roll_tracker.log_roll(
                user_id=str(ctx.author.id),
                user_name=ctx.author.display_name,
                command_type='ex',
                num_dice=num_dice,
                sides=6,
                roll_values=all_rolls,
                modifier=modifier,
                target=target,
                success=success,
                is_perfect=perfect_candidate,
                is_fumble=fumble_candidate
            )

        except ValueError:
            await ctx.send(
                "Felaktigt format. Exempel:\n"
                "`!ex 3d6`, `!ex 3d6+1`, `!ex 4d6 18`, `!ex 2d6+2 15`"
            )

    @bot.command(name='chance')
    async def chance_command(ctx: commands.Context, dice_spec: str, target: int) -> None:
        """
        Beräknar sannolikheten att lyckas med ett obegränsat T6-slag mot ett målvärde.
        
        Användning:
          !chance 3d6+2 15 - Beräkna chansen att lyckas med obegränsat slag
        
        Args:
            ctx (commands.Context): Kontexten för kommandot.
            dice_spec (str): Tärningsspecifikation (t.ex. 3d6+2).
            target (int): Målvärde att jämföra med.
        """
        try:
            # Parsa tärningsspecifikationen med nya parser
            try:
                spec = parse_dice_string(dice_spec)
                num_dice, sides, modifier = spec.count, spec.sides, spec.modifier
            except InvalidDiceFormat as e:
                await ctx.send(f"❌ Felaktigt format: {e}")
                return
            except DiceLimitsError as e:
                await ctx.send(f"⚠️ Gränser överskrids: {e}")
                return
            
            # Kontrollera att det är T6
            if sides != 6:
                await ctx.send("Endast T6 stöds för sannolikhetsberäkning eftersom Eon använder obegränsade T6-slag.")
                return
            
            # Visa att beräkning pågår
            async with ctx.typing():
                # Beräkna sannolikheten för obegränsat slag
                success_rate = simulate_unlimited_dice(num_dice, modifier, target)
                
                # Skapa ett snyggt svar
                embed = embed_factory.dice_result(
                    ctx.author.id,
                    ctx.author.display_name,
                    "chance",
                    dice_spec,
                    [],  # No actual rolls for probability
                    None,  # No total
                    target,
                    None  # No actual success/fail
                )
                
                # Override with probability specific content
                embed.clear_fields()
                embed.add_field(
                    name="Chans att lyckas",
                    value=f"**{success_rate:.1f}%**",
                    inline=False
                )
                
                # Lägg till lite extra användbar information
                if success_rate > 95:
                    kommentar = "Varför ens slå?"
                elif success_rate > 75:
                    kommentar = "Walk in the da park"
                elif success_rate > 50:
                    kommentar = "Mer troligt att lyckas än att misslyckas"
                elif success_rate > 25:
                    kommentar = "Ingen minns en fegis!"
                else:
                    kommentar = "Ser tight ut"
                
                embed.add_field(
                    name="Kommentar",
                    value=kommentar,
                    inline=False
                )
                
                await ctx.send(embed=embed)
                
        except Exception as e:
            await ctx.send(f"Ett fel uppstod vid beräkning: {str(e)}")