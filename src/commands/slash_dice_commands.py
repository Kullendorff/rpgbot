"""
Slash commands för tärningsoperationer i EON Discord Bot.
Konverterar prefix commands (!roll, !ex, !count, !chance) till moderna slash commands.
"""

import random
import time
import logging
from typing import List, Optional, Tuple, Any
import discord
from discord.ext import commands
from discord import app_commands

# Setup logging
logger = logging.getLogger(__name__)

# Import migration helpers
from migration.helper import MigrationHelper, SlashCommandDecorator, dice_autocomplete, target_value_autocomplete

# Helper function för hemlig manipulation
def apply_secret_manipulation(user_id: str, rolls: List[int], sides: int, 
                             modifier: int, target: Optional[int]) -> tuple:
    """
    Apply secret manipulation if active for user.
    
    Returns:
        Tuple of (final_rolls, was_manipulated, manipulation_type)
    """
    try:
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        
        # Get main module to access global objects
        import main
        manipulation_manager = main.manipulation_manager
        return manipulation_manager.manipulate_roll_result(
            str(user_id), rolls, sides, modifier, target
        )
    except Exception as e:
        print(f"Error applying manipulation: {e}")
        return rolls, False, None

class DiceSlashCommands(commands.Cog):
    """Cog för alla tärnings-relaterade slash commands."""
    
    def __init__(self, bot, roll_tracker, color_handler, embed_factory, knowledge_base):
        self.bot = bot
        self.roll_tracker = roll_tracker
        self.color_handler = color_handler
        self.embed_factory = embed_factory
        self.knowledge_base = knowledge_base
        
        # Migration helper för säker hantering
        self.helper = MigrationHelper(embed_factory)
        self.decorator = SlashCommandDecorator(self.helper)
        
        # Import dependencies
        from core.constants import MAX_DICE, MAX_SIDES
        from core.dice_parser import parse_dice_string, InvalidDiceFormat, DiceLimitsError
        from core.dice_engine import unlimited_d6s, simulate_unlimited_dice
        from utils.text_utils import clean_unicode
        
        self.MAX_DICE = MAX_DICE
        self.MAX_SIDES = MAX_SIDES
        self.parse_dice_string = parse_dice_string
        self.InvalidDiceFormat = InvalidDiceFormat
        self.DiceLimitsError = DiceLimitsError
        self.unlimited_d6s = unlimited_d6s
        self.simulate_unlimited_dice = simulate_unlimited_dice
        self.clean_unicode = clean_unicode
    
    def add_user_comment(self, embed: discord.Embed, user_id: str, roll_result: dict):
        """Add personalized comment to embed if enabled for user."""
        try:
            # Import global objects from main
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            
            # Get main module to access global objects
            import main
            user_settings = main.user_settings
            comment_generator = main.comment_generator
            
            # Get user settings
            settings = user_settings.get_user_settings(str(user_id))
            
            # Get comment
            comment = comment_generator.get_comment(settings, roll_result)
            
            if comment:
                embed.add_field(name="🎭", value=comment, inline=False)
        except Exception as e:
            print(f"Error adding user comment: {e}")
    

    @app_commands.command(name="roll", description="Rulla tärningar enligt EON-notation (t.ex. 3d6+2)")
    @app_commands.describe(
        tärningar="Tärningsformel (t.ex. 3d6+2, 4d10-1)",
        mål="Målvärde för att bedöma framgång (valfritt)",
        demon="Använd demonisk inspiration för att manipulera resultatet"
    )
    @app_commands.autocomplete(tärningar=dice_autocomplete)
    async def roll_slash(
        self, 
        interaction: discord.Interaction,
        tärningar: str,
        mål: Optional[app_commands.Range[int, 1, 100]] = None,
        demon: bool = False
    ):
        """Slash command version av !roll."""
        start_time = time.time()
        
        try:
            # Hantera demonisk inspiration
            if demon:
                logger.debug(f"Demonisk inspiration aktiverad av {interaction.user.display_name} i /roll {tärningar}")
                try:
                    await interaction.user.send(f"🔥 Demonisk inspiration aktiverad")
                except discord.Forbidden as e:
                    logger.warning(f"Kunde inte skicka DM till {interaction.user.display_name}: DM permissions disabled")
                except Exception as e:
                    logger.error(f"Fel vid skick av DM till {interaction.user.display_name}: {e}")
            
            
            # Parsa dice string
            try:
                dice_spec = self.parse_dice_string(tärningar)
                dice_count, sides, modifier = dice_spec.count, dice_spec.sides, dice_spec.modifier
            except self.InvalidDiceFormat as e:
                embed = await self.helper.create_error_response(
                    interaction.user.id,
                    f"Ogiltig tärningsformel: {tärningar}",
                    "Använd format som '3d6+2' eller '4d10-1'"
                )
                await self.helper.send_response(interaction, embed=embed)
                return
            except self.DiceLimitsError as e:
                embed = await self.helper.create_error_response(
                    interaction.user.id,
                    str(e),
                    f"Max {self.MAX_DICE} tärningar och {self.MAX_SIDES} sidor per tärning"
                )
                await self.helper.send_response(interaction, embed=embed)
                return
            
            # Rulla tärningar ORIGINAL
            original_results = [random.randint(1, sides) for _ in range(dice_count)]
            
            # APPLY SECRET MANIPULATION (innan demon inspiration)
            final_results, was_manipulated, manipulation_type = apply_secret_manipulation(
                interaction.user.id, original_results, sides, modifier, mål
            )
            
            # Beräkna total med (möjligtvis manipulerade) rolls
            total = sum(final_results) + modifier
            
            # Demon inspiration manipulation (endast om inte redan manipulerat)
            if demon and not was_manipulated:
                # Hitta lägsta värdet och ersätt med högsta möjliga
                if final_results:
                    min_index = final_results.index(min(final_results))
                    final_results[min_index] = sides
                    total = sum(final_results) + modifier
            
            # Bedöm framgång — EON är roll-under: lägre total = bättre.
            # Samma bedömning som /ex, /secret_roll, legacy !roll och dice_engine.
            success = None
            if mål is not None:
                success = total <= mål
            
            # Spara i statistik (använd final_results)
            self.roll_tracker.log_roll(
                str(interaction.user.id),
                interaction.user.display_name,
                "roll",
                dice_count,
                sides,
                final_results,
                modifier,
                mål,
                success
            )
            
            # Skapa embed med resultat (använd final_results)
            embed = self.embed_factory.dice_result(
                interaction.user.id,
                interaction.user.display_name,
                "roll",
                tärningar,
                final_results,
                total,
                mål,
                success
            )
            
            # Lägg till modifier info om den finns
            if modifier != 0:
                modifier_text = f"+{modifier}" if modifier > 0 else str(modifier)
                embed.add_field(
                    name="Modifierare", 
                    value=modifier_text, 
                    inline=True
                )
            
            # Lägg till demon inspiration info
            if demon:
                embed.add_field(
                    name="🔥 Demonisk Inspiration", 
                    value="Lägsta tärning ersatt med maxvärde", 
                    inline=False
                )
            
            # Lägg till kommentar för användaren
            roll_result = {
                "success": success,
                "is_critical_success": total == (dice_count * sides) + modifier,  # Max möjligt
                "is_fumble": total == dice_count + modifier,  # Min möjligt
                "total": total,
                "target": mål,
                "was_manipulated": was_manipulated,  # För intern logging
                "manipulation_type": manipulation_type
            }
            self.add_user_comment(embed, interaction.user.id, roll_result)
            
            # Secret logging för GM (endast i console)
            if was_manipulated:
                print(f"[SECRET MANIPULATION] {manipulation_type.upper()} applied to {interaction.user.display_name}: {original_results} -> {final_results}")
            
            execution_time = time.time() - start_time
            await self.helper.log_command_usage(interaction, "roll", {
                "dice": tärningar, "target": mål, "demon": demon
            }, execution_time)
            
            await self.helper.send_response(interaction, embed=embed)
            
        except Exception as e:
            embed = await self.helper.create_error_response(
                interaction.user.id,
                f"Ett oväntat fel inträffade: {str(e)}"
            )
            await self.helper.send_response(interaction, embed=embed)

    @app_commands.command(name="ex", description="Rulla exploderande d6:or (obegränsad explosion på 6:or)")
    @app_commands.describe(
        antal="Antal d6:or att rulla (1-50)",
        modifier="Modifier att lägga till (+/- värde, t.ex. +3 eller -2)",
        mål="Målvärde för att bedöma framgång (valfritt)"
    )
    async def ex_slash(
        self,
        interaction: discord.Interaction,
        antal: app_commands.Range[int, 1, 50],
        modifier: Optional[app_commands.Range[int, -100, 100]] = 0,
        mål: Optional[app_commands.Range[int, 1, 100]] = None
    ):
        """Slash command version av !ex - exploderande d6."""
        start_time = time.time()
        
        try:
            # Använd unlimited_d6s engine
            all_rolls, total_dice, initial_rolls = self.unlimited_d6s(antal)
            results = all_rolls

            # Lägg till modifier till totalen
            total = total_dice + modifier
            
            # Kontrollera perfekta och fummelkriterier baserat på original implementation
            perfect_candidate = False
            if antal == 1:
                if initial_rolls[0] in [1, 2, 3]:
                    perfect_candidate = True
            else:
                not_one_count = sum(1 for r in initial_rolls if r != 1)
                if not_one_count <= 1:
                    perfect_candidate = True

            six_count = sum(1 for r in initial_rolls if r == 6)
            fumble_candidate = (six_count >= 2)
            
            # APPLY SECRET MANIPULATION för EX kommando
            original_total = total
            was_manipulated = False
            manipulation_type = None

            # Check if user has active manipulation
            try:
                import sys
                import os
                sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
                import main
                user_id_str = str(interaction.user.id)
                manipulation = main.manipulation_manager.get_manipulation(user_id_str)

                if manipulation and mål is not None:
                    manipulation_type = manipulation["type"]

                    if manipulation_type in ["lycka", "gudomlig"]:
                        # AUTO-SUCCESS: Ensure roll succeeds (total <= target for ex)
                        if total > mål:  # Currently failing
                            total = mål - 1  # Make it succeed
                            was_manipulated = True

                    elif manipulation_type in ["olycka", "förbannelse"]:
                        # AUTO-FAIL: Ensure roll fails (total > target for ex)
                        if total <= mål:  # Currently succeeding
                            total = mål + 1  # Make it fail
                            was_manipulated = True

                    if was_manipulated:
                        # Update manipulation stats
                        manipulation["rolls_affected"] += 1
                        main.manipulation_manager._save_manipulations()
                        print(f"[SECRET] {manipulation_type.upper()} EX manipulation: {original_total} (dice:{total_dice}+{modifier}) -> {total}")
            except Exception as e:
                print(f"[ERROR] Error applying EX manipulation: {e}")
            
            # Bedöm framgång mot målvärde (använd manipulerad total)
            success = None
            if mål is not None:
                success = total <= mål
            
            # Spara i statistik som ex command
            self.roll_tracker.log_roll(
                str(interaction.user.id),
                interaction.user.display_name,
                "ex",
                antal,
                6,
                results,
                modifier,  # modifier
                mål,  # target
                success,  # success
                perfect_candidate,  # is_perfect
                fumble_candidate  # is_fumble
            )
            
            # Skapa embed
            dice_notation = f"{antal}d6"
            if modifier != 0:
                modifier_text = f"+{modifier}" if modifier > 0 else str(modifier)
                dice_notation += modifier_text
            dice_notation += " (exploderande)"

            embed = self.embed_factory.dice_result(
                interaction.user.id,
                interaction.user.display_name,
                "ex",
                dice_notation,
                initial_rolls,  # Show initial rolls in main display
                total,
                mål,
                success
            )

            # Lägg till modifier info om den finns
            if modifier != 0:
                modifier_text = f"+{modifier}" if modifier > 0 else str(modifier)
                embed.add_field(
                    name="Modifierare",
                    value=modifier_text,
                    inline=True
                )

            # Lägg till explosion info
            explosion_count = len(results) - antal
            if explosion_count > 0:
                embed.add_field(
                    name="💥 Explosioner",
                    value=f"{explosion_count} extra tärningar från 6:or",
                    inline=True
                )
            
            # Visa alla kast (inkl. extra)
            embed.add_field(
                name="Alla kast (inkl. extra)", 
                value=str(all_rolls), 
                inline=False
            )
            
            # Target value and success evaluation
            if mål is not None:
                difference = mål - total
                result_text = None
                if success:
                    result_text = "✨ **Perfekt slag!** (lyckat)" if perfect_candidate else "✅ **Lyckat slag**"
                else:
                    result_text = "💥 **FUMMEL!**" if fumble_candidate else "❌ **Misslyckat**"
                
                embed.add_field(
                    name=f"Motståndsvärde: {mål}",
                    value=f"{result_text}\n(Marginal: {difference:+d})",
                    inline=False
                )
            
            # Special cases
            if perfect_candidate or fumble_candidate:
                special_result = []
                if perfect_candidate:
                    special_result.append("✨ **PERFEKT SLAG!** Tärningsoraklet ler mot dig.")
                if fumble_candidate:
                    special_result.append("💥 **FUMMEL!** Tärningsoraklet skrattar åt din olycka.")
                    
                embed.add_field(
                    name="Särskilt Utfall",
                    value="\n".join(special_result),
                    inline=False
                )
            
            # Visa fördelning om många tärningar
            if len(results) > 10:
                counts = {}
                for r in results:
                    counts[r] = counts.get(r, 0) + 1
                
                distribution = ", ".join(f"{face}×{count}" for face, count in sorted(counts.items()))
                embed.add_field(
                    name="📊 Fördelning", 
                    value=distribution, 
                    inline=False
                )
            
            # Lägg till kommentar för användaren
            roll_result = {
                "success": success,
                "is_critical_success": perfect_candidate,
                "is_fumble": fumble_candidate,
                "is_perfect": perfect_candidate,
                "total": total,
                "target": mål,
                "was_manipulated": was_manipulated,
                "manipulation_type": manipulation_type
            }
            self.add_user_comment(embed, interaction.user.id, roll_result)
            
            # Secret logging för GM (endast i console)
            if was_manipulated:
                print(f"[SECRET MANIPULATION] {manipulation_type.upper()} applied to {interaction.user.display_name} EX command: {original_total} -> {total}")
            
            execution_time = time.time() - start_time
            await self.helper.log_command_usage(interaction, "ex", {
                "antal": antal, "modifier": modifier, "target": mål
            }, execution_time)
            
            await self.helper.send_response(interaction, embed=embed)
            
        except Exception as e:
            embed = await self.helper.create_error_response(
                interaction.user.id,
                f"Ett oväntat fel inträffade: {str(e)}"
            )
            await self.helper.send_response(interaction, embed=embed)

    @app_commands.command(name="count", description="Räkna lyckade tärningsslag mot ett målvärde")
    @app_commands.describe(
        tärningar="Tärningsformel (t.ex. 5d10, 8d6)",
        mål="Målvärde för framgång (obligatorisk)"
    )
    @app_commands.autocomplete(tärningar=dice_autocomplete)
    async def count_slash(
        self,
        interaction: discord.Interaction,
        tärningar: str,
        mål: app_commands.Range[int, 1, 20]
    ):
        """Slash command version av !count."""
        start_time = time.time()
        
        try:
            # Parsa dice string
            try:
                dice_spec = self.parse_dice_string(tärningar)
                dice_count, sides, modifier = dice_spec.count, dice_spec.sides, dice_spec.modifier
            except self.InvalidDiceFormat as e:
                embed = await self.helper.create_error_response(
                    interaction.user.id,
                    f"Ogiltig tärningsformel: {tärningar}",
                    "Använd format som '5d10' eller '8d6'"
                )
                await self.helper.send_response(interaction, embed=embed)
                return
            except self.DiceLimitsError as e:
                embed = await self.helper.create_error_response(
                    interaction.user.id,
                    str(e)
                )
                await self.helper.send_response(interaction, embed=embed)
                return
            
            # Rulla tärningar ORIGINAL
            original_results = [random.randint(1, sides) for _ in range(dice_count)]
            
            # APPLY SECRET MANIPULATION för COUNT kommando
            final_results, was_manipulated, manipulation_type = apply_secret_manipulation(
                interaction.user.id, original_results, sides, modifier, mål
            )
            
            # Räkna framgångar (använd final_results)
            successes = sum(1 for result in final_results if result >= mål)
            total = sum(final_results) + modifier
            
            # Spara i statistik (använd final_results)
            self.roll_tracker.log_roll(
                str(interaction.user.id),
                interaction.user.display_name,
                "count",
                dice_count,
                sides,
                final_results,
                modifier,
                mål,
                successes > 0
            )
            
            # Skapa embed (använd final_results)
            embed = self.embed_factory.dice_result(
                interaction.user.id,
                interaction.user.display_name,
                "count",
                tärningar,
                final_results,
                total,
                mål,
                successes > 0
            )
            
            # Lägg till framgångsinfo
            embed.add_field(
                name="🎯 Framgångar", 
                value=f"{successes} av {dice_count} tärningar", 
                inline=True
            )
            
            # Visuell representation (använd final_results)
            visual = ""
            for result in final_results:
                if result >= mål:
                    visual += "✅"
                else:
                    visual += "❌"
            
            if len(visual) <= 50:  # Begränsa för långa strängar
                embed.add_field(
                    name="📊 Visuellt", 
                    value=visual, 
                    inline=False
                )
            
            # Lägg till kommentar för användaren
            roll_result = {
                "success": successes > 0,
                "is_critical_success": successes == dice_count,  # Alla slag lyckades
                "is_fumble": successes == 0,  # Inga slag lyckades
                "total": successes,
                "target": mål,
                "was_manipulated": was_manipulated,
                "manipulation_type": manipulation_type
            }
            self.add_user_comment(embed, interaction.user.id, roll_result)
            
            # Secret logging för GM (endast i console)
            if was_manipulated:
                print(f"[SECRET MANIPULATION] {manipulation_type.upper()} applied to {interaction.user.display_name} COUNT command: {original_results} -> {final_results}")
            
            execution_time = time.time() - start_time
            await self.helper.log_command_usage(interaction, "count", {
                "dice": tärningar, "target": mål
            }, execution_time)
            
            await self.helper.send_response(interaction, embed=embed)
            
        except Exception as e:
            embed = await self.helper.create_error_response(
                interaction.user.id,
                f"Ett oväntat fel inträffade: {str(e)}"
            )
            await self.helper.send_response(interaction, embed=embed)

    @app_commands.command(name="chance", description="Simulera sannolikhet för exploderande d6:or (EON-system)")
    @app_commands.describe(
        antal="Antal exploderande d6:or (1-20)",
        target="Målvärde för framgång (EON: lägre = bättre)",
        iterations="Antal simuleringar (default 10000)"
    )
    async def chance_slash(
        self,
        interaction: discord.Interaction,
        antal: app_commands.Range[int, 1, 20],
        target: app_commands.Range[int, 1, 100],
        iterations: Optional[app_commands.Range[int, 1000, 100000]] = 10000
    ):
        """Slash command version av !chance - MÅSTE använda defer."""
        # KRITISKT: Denna operation tar alltid >3 sekunder
        await self.helper.safe_defer(interaction)
        
        start_time = time.time()
        
        try:
            # Kör simulering med exploderande d6:or
            success_count = 0
            
            # Progress feedback för långa simuleringar
            if iterations >= 50000:
                progress_embed = self.embed_factory.admin_message(
                    interaction.user.id,
                    "Simulering pågår...",
                    f"Kör {iterations:,} simuleringar av {antal}d6 (exploderande) mot {target}"
                )
                await interaction.followup.send(embed=progress_embed, ephemeral=True)
            
            for i in range(iterations):
                # Använd exploderande d6-logik från unlimited_d6s
                all_rolls, total, initial_rolls = self.unlimited_d6s(antal)
                
                # EON: lägre total = bättre, så success = total <= target
                if total <= target:
                    success_count += 1
            
            # Beräkna statistik
            success_rate = (success_count / iterations) * 100
            failure_rate = 100 - success_rate
            odds_for = f"1:{iterations/success_count:.1f}" if success_count > 0 else "Ingen framgång"
            odds_against = f"{(iterations-success_count)/success_count:.1f}:1" if success_count > 0 else "Omöjligt"
            
            # Skapa resultat embed
            embed = self.embed_factory.dice_result(
                interaction.user.id,
                interaction.user.display_name,
                "chance",
                f"{antal}d6 (exploderande) mot {target}",
                [],  # Inga faktiska resultat att visa
                None,
                target,
                success_rate > 50
            )
            
            # Lägg till sannolikhetsdata
            embed.add_field(
                name="📊 Framgång", 
                value=f"{success_rate:.2f}% ({success_count:,}/{iterations:,})", 
                inline=True
            )
            
            embed.add_field(
                name="📊 Misslyckande", 
                value=f"{failure_rate:.2f}% ({iterations-success_count:,}/{iterations:,})", 
                inline=True
            )
            
            embed.add_field(
                name="🎲 Odds", 
                value=f"För: {odds_for}\\nMot: {odds_against}", 
                inline=False
            )
            
            execution_time = time.time() - start_time
            embed.add_field(
                name="⏱️ Simulering", 
                value=f"Tid: {execution_time:.2f}s", 
                inline=True
            )
            
            await self.helper.log_command_usage(interaction, "chance", {
                "dice": f"{antal}d6", "target": target, "iterations": iterations
            }, execution_time)
            
            await self.helper.send_response(interaction, embed=embed)
            
        except Exception as e:
            embed = await self.helper.create_error_response(
                interaction.user.id,
                f"Ett oväntat fel inträffade: {str(e)}"
            )
            await self.helper.send_response(interaction, embed=embed)


# Registrering function för att ersätta gamla systemet
async def register_slash_dice_commands(bot, roll_tracker, color_handler, embed_factory, knowledge_base):
    """
    Registrera slash dice commands med boten.
    Denna ersätter register_dice_commands för slash commands.
    """
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
    from config.feature_flags import is_command_enabled
    
    # Kontrollera om slash dice commands är aktiverade
    if not is_command_enabled("roll", "dice"):
        print("Slash dice commands är inte aktiverade enligt feature flags")
        return
    
    # Lägg till cog
    dice_cog = DiceSlashCommands(bot, roll_tracker, color_handler, embed_factory, knowledge_base)
    await bot.add_cog(dice_cog)
    print("Slash dice commands har registrerats (/roll, /ex, /count, /chance).")