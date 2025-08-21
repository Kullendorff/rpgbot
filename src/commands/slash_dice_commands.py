"""
Slash commands för tärningsoperationer i EON Discord Bot.
Konverterar prefix commands (!roll, !ex, !count, !chance) till moderna slash commands.
"""

import random
import time
from typing import List, Optional, Tuple, Any
import discord
from discord.ext import commands
from discord import app_commands

# Import migration helpers
from migration.helper import MigrationHelper, SlashCommandDecorator, dice_autocomplete, target_value_autocomplete

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
        from core.constants import UMNATAK_ID, MAX_DICE, MAX_SIDES, UMNATAK_SUCCESS_COMMENTS
        from core.dice_parser import parse_dice_string, InvalidDiceFormat, DiceLimitsError
        from core.dice_engine import unlimited_d6s, simulate_unlimited_dice
        from utils.text_utils import clean_unicode
        
        self.UMNATAK_ID = UMNATAK_ID
        self.MAX_DICE = MAX_DICE
        self.MAX_SIDES = MAX_SIDES
        self.UMNATAK_SUCCESS_COMMENTS = UMNATAK_SUCCESS_COMMENTS
        self.parse_dice_string = parse_dice_string
        self.InvalidDiceFormat = InvalidDiceFormat
        self.DiceLimitsError = DiceLimitsError
        self.unlimited_d6s = unlimited_d6s
        self.simulate_unlimited_dice = simulate_unlimited_dice
        self.clean_unicode = clean_unicode
    
    def get_sarcastic_comment_for_umnatak(self) -> Optional[str]:
        """
        Returnerar en slumpmässig syrlig kommentar om Umnatak, men endast cirka 30% av gångerna.
        """
        random.seed(int(time.time()))
        if random.random() < 0.3:  # 30% chans
            return random.choice(self.UMNATAK_SUCCESS_COMMENTS)
        return None

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
                print(f"[DEBUG] Demonisk inspiration aktiverad av {interaction.user.display_name} i /roll {tärningar}")
                try:
                    await interaction.user.send(f"🔥 Demonisk inspiration aktiverad")
                except:
                    pass  # Ignorera om DM misslyckas
            
            # Kontrollera Umnatak special handling
            is_umnatak = interaction.user.id == self.UMNATAK_ID
            
            # Parsa dice string
            try:
                dice_spec = self.parse_dice_string(tärningar)
                dice_count, sides, modifier = dice_spec.count, dice_spec.sides, dice_spec.modifier
            except self.InvalidDiceFormat as e:
                embed = await self.helper.create_error_response(
                    interaction.user.id,
                    f"Ogiltig tärningsformel: {dice}",
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
            
            # Rulla tärningar
            results = [random.randint(1, sides) for _ in range(dice_count)]
            total = sum(results) + modifier
            
            # Demon inspiration manipulation
            if demon:
                # Hitta lägsta värdet och ersätt med högsta möjliga
                if results:
                    min_index = results.index(min(results))
                    results[min_index] = sides
                    total = sum(results) + modifier
            
            # Bedöm framgång
            success = None
            if mål is not None:
                success = total >= mål
            
            # Spara i statistik
            self.roll_tracker.log_roll(
                str(interaction.user.id),
                interaction.user.display_name,
                "roll",
                dice_count,
                sides,
                results,
                modifier,
                mål,
                success
            )
            
            # Skapa embed med resultat
            embed = self.embed_factory.dice_result(
                interaction.user.id,
                interaction.user.display_name,
                "roll",
                tärningar,
                results,
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
            
            # Umnatak special comments
            if is_umnatak and success:
                comment = self.get_sarcastic_comment_for_umnatak()
                if comment:
                    embed.add_field(
                        name="🎯 Särskild kommentar", 
                        value=comment, 
                        inline=False
                    )
            
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
        mål="Målvärde för att bedöma framgång (valfritt)"
    )
    async def ex_slash(
        self,
        interaction: discord.Interaction,
        antal: app_commands.Range[int, 1, 50],
        mål: Optional[app_commands.Range[int, 1, 100]] = None
    ):
        """Slash command version av !ex - exploderande d6."""
        start_time = time.time()
        
        try:
            # Använd unlimited_d6s engine
            all_rolls, total, initial_rolls = self.unlimited_d6s(antal)
            results = all_rolls
            
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
            
            # Bedöm framgång mot målvärde
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
                0,  # modifier
                mål,  # target
                success,  # success
                perfect_candidate,  # is_perfect
                fumble_candidate  # is_fumble
            )
            
            # Skapa embed
            embed = self.embed_factory.dice_result(
                interaction.user.id,
                interaction.user.display_name,
                "ex",
                f"{antal}d6 (exploderande)",
                initial_rolls,  # Show initial rolls in main display
                total,
                mål,
                success
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
            
            # Umnatak special comments 
            if str(interaction.user.id) == self.UMNATAK_ID and mål is not None and success:
                comment = self.get_sarcastic_comment_for_umnatak()
                if comment:
                    embed.add_field(
                        name="🎯 Särskild kommentar", 
                        value=comment, 
                        inline=False
                    )
            
            execution_time = time.time() - start_time
            await self.helper.log_command_usage(interaction, "ex", {
                "antal": antal, "target": mål
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
                dice_spec = self.parse_dice_string(dice)
                dice_count, sides, modifier = dice_spec.count, dice_spec.sides, dice_spec.modifier
            except self.InvalidDiceFormat as e:
                embed = await self.helper.create_error_response(
                    interaction.user.id,
                    f"Ogiltig tärningsformel: {dice}",
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
            
            # Rulla tärningar
            results = [random.randint(1, sides) for _ in range(dice_count)]
            
            # Räkna framgångar
            successes = sum(1 for result in results if result >= target)
            total = sum(results) + modifier
            
            # Spara i statistik
            self.roll_tracker.log_roll(
                str(interaction.user.id),
                interaction.user.display_name,
                "count",
                dice_count,
                sides,
                results,
                modifier,
                target,
                successes > 0
            )
            
            # Skapa embed
            embed = self.embed_factory.dice_result(
                interaction.user.id,
                interaction.user.display_name,
                "count",
                dice,
                results,
                total,
                target,
                successes > 0
            )
            
            # Lägg till framgångsinfo
            embed.add_field(
                name="🎯 Framgångar", 
                value=f"{successes} av {dice_count} tärningar", 
                inline=True
            )
            
            # Visuell representation
            visual = ""
            for result in results:
                if result >= target:
                    visual += "✅"
                else:
                    visual += "❌"
            
            if len(visual) <= 50:  # Begränsa för långa strängar
                embed.add_field(
                    name="📊 Visuellt", 
                    value=visual, 
                    inline=False
                )
            
            execution_time = time.time() - start_time
            await self.helper.log_command_usage(interaction, "count", {
                "dice": dice, "target": target
            }, execution_time)
            
            await self.helper.send_response(interaction, embed=embed)
            
        except Exception as e:
            embed = await self.helper.create_error_response(
                interaction.user.id,
                f"Ett oväntat fel inträffade: {str(e)}"
            )
            await self.helper.send_response(interaction, embed=embed)

    @app_commands.command(name="chance", description="Simulera sannolikhet för att lyckas med tärningsslag")
    @app_commands.describe(
        dice="Tärningsformel (t.ex. 3d6+2)",
        target="Målvärde för framgång",
        iterations="Antal simuleringar (default 10000)"
    )
    @app_commands.autocomplete(dice=dice_autocomplete)
    async def chance_slash(
        self,
        interaction: discord.Interaction,
        dice: str,
        target: app_commands.Range[int, 1, 100],
        iterations: Optional[app_commands.Range[int, 1000, 100000]] = 10000
    ):
        """Slash command version av !chance - MÅSTE använda defer."""
        # KRITISKT: Denna operation tar alltid >3 sekunder
        await self.helper.safe_defer(interaction)
        
        start_time = time.time()
        
        try:
            # Parsa dice string
            try:
                dice_spec = self.parse_dice_string(dice)
                dice_count, sides, modifier = dice_spec.count, dice_spec.sides, dice_spec.modifier
            except self.InvalidDiceFormat as e:
                embed = await self.helper.create_error_response(
                    interaction.user.id,
                    f"Ogiltig tärningsformel: {dice}",
                    "Använd format som '3d6+2' eller '4d10-1'"
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
            
            # Kör simulering
            success_count = 0
            
            # Progress feedback för långa simuleringar
            if iterations >= 50000:
                progress_embed = self.embed_factory.admin_message(
                    interaction.user.id,
                    "Simulering pågår...",
                    f"Kör {iterations:,} simuleringar av {dice} mot {target}"
                )
                await interaction.followup.send(embed=progress_embed, ephemeral=True)
            
            for i in range(iterations):
                # Rulla och kontrollera framgång
                results = [random.randint(1, sides) for _ in range(dice_count)]
                total = sum(results) + modifier
                if total >= target:
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
                f"{dice} mot {target}",
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
                "dice": dice, "target": target, "iterations": iterations
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