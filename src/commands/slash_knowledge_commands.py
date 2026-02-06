"""
Slash commands för knowledge operations i EON Discord Bot.
Konverterar prefix commands (!ask, !sök, !allt) till moderna slash commands.
"""

import os
import time
from typing import List, Optional, Tuple, Any
import discord
from discord.ext import commands
from discord import app_commands

# Import migration helpers
from migration.helper import MigrationHelper, SlashCommandDecorator
from utils.ai_handler import AIHandler
from core.constants import CLAUDE_MODEL

class KnowledgeSlashCommands(commands.Cog):
    """Cog för alla kunskaps-relaterade slash commands."""
    
    def __init__(self, bot, knowledge_base, color_handler, embed_factory):
        self.bot = bot
        self.knowledge_base = knowledge_base
        self.color_handler = color_handler
        self.embed_factory = embed_factory
        
        # Migration helper för säker hantering
        self.helper = MigrationHelper(embed_factory)
        self.decorator = SlashCommandDecorator(self.helper)
        
        # AI handler för timeout-hantering
        self.ai_handler = AIHandler(embed_factory)
    
    async def query_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str,
    ) -> List[app_commands.Choice[str]]:
        """Autocomplete för vanliga frågor."""
        common_queries = [
            "Hur fungerar magi i Eon?",
            "Vad är reglerna för stridskonst?",
            "Hur beräknas skada?",
            "Vad händer vid fummel?",
            "Hur fungerar färdigheter?",
            "Vad är skillnaden mellan T6 och obegränsat T6?",
            "Hur fungerar träfftabeller?",
            "Vad betyder perfekt slag?",
            "Hur räknas rustningsvärde?",
            "Vad är skillnaden mellan närstrider och avståndstrider?"
        ]
        
        # Filtrera baserat på current input
        matches = [
            app_commands.Choice(name=query, value=query)
            for query in common_queries
            if current.lower() in query.lower()
        ]
        
        return matches[:25]  # Discord limit
    
    @app_commands.command(name="ask", description="Ställ en fråga till AI:n baserat på EON-regelböckerna")
    @app_commands.describe(
        fråga="Din fråga om EON-regler",
        detaljerad="Detaljerat svar (kan ta längre tid)"
    )
    @app_commands.autocomplete(fråga=query_autocomplete)
    async def ask_slash(
        self,
        interaction: discord.Interaction,
        fråga: str,
        detaljerad: Optional[bool] = False
    ):
        """Slash command version av !ask - AI-baserad regelfrågor."""
        # KRITISKT: Defer omedelbart för AI operations
        await self.helper.safe_defer(interaction)
        start_time = time.time()
        
        try:
            # Validera input
            if len(fråga.strip()) < 3:
                embed = await self.helper.create_error_response(
                    interaction.user.id,
                    "Frågan är för kort",
                    "Ställ en mer detaljerad fråga (minst 3 tecken)"
                )
                await self.helper.send_response(interaction, embed=embed)
                return
            
            # Använd AI handler för säker operation
            result = await self.ai_handler.safe_ai_operation(
                interaction,
                self.knowledge_base,
                fråga,
                operation_type="ask"
            )
            
            if result is None:
                # Error redan hanterat av ai_handler
                return
            
            response, sources = result
            
            # Skapa embed för svaret
            embed = self.embed_factory.knowledge_result(
                interaction.user.id,
                interaction.user.display_name,
                fråga,
                response,
                sources
            )
            
            # Lägg till detaljerad information om begärt
            if detaljerad:
                embed.add_field(
                    name="🔍 Detaljerat svar",
                    value="Detta svar inkluderar utökad kontext och källor",
                    inline=False
                )
            
            # Lägg till cache info om applicable
            cache_info = self.ai_handler.get_cache_stats()
            if cache_info['total_entries'] > 0:
                embed.set_footer(
                    text=f"AI Cache: {cache_info['valid_entries']}/{cache_info['total_entries']} entries"
                )
            
            execution_time = time.time() - start_time
            await self.helper.log_command_usage(interaction, "ask", {
                "query": fråga[:100],  # Begränsa för logging
                "detailed": detaljerad,
                "sources_count": len(sources)
            }, execution_time)
            
            await self.helper.send_response(interaction, embed=embed)
            
        except Exception as e:
            embed = await self.helper.create_error_response(
                interaction.user.id,
                f"Ett oväntat fel inträffade: {str(e)}"
            )
            await self.helper.send_response(interaction, embed=embed)

    @app_commands.command(name="sök", description="Sök direkt i EON-regelböckerna efter specifik text")
    @app_commands.describe(
        sökterm="Sökterm att leta efter",
        källa="Filtrera på specifik källa (valfritt)",
        max_resultat="Antal resultat att visa (1-20)"
    )
    async def search_slash(
        self,
        interaction: discord.Interaction,
        sökterm: str,
        källa: Optional[str] = None,
        max_resultat: app_commands.Range[int, 1, 20] = 5
    ):
        """Slash command version av !sök - direktsökning i filer."""
        start_time = time.time()
        
        try:
            # Validera input
            if len(sökterm.strip()) < 2:
                embed = await self.helper.create_error_response(
                    interaction.user.id,
                    "Söktermen är för kort",
                    "Använd minst 2 tecken för sökning"
                )
                await self.helper.send_response(interaction, embed=embed)
                return
            
            # Defer om många resultat kan komma
            if max_results > 10:
                await self.helper.safe_defer(interaction)
            
            # Hämta project root och text folder
            script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            project_root = os.path.dirname(script_dir)
            text_folder = os.path.join(project_root, "data", "extracted_text")
            
            if not os.path.exists(text_folder):
                embed = await self.helper.create_error_response(
                    interaction.user.id,
                    "Textmappen hittades inte",
                    f"Förväntade: {text_folder}"
                )
                await self.helper.send_response(interaction, embed=embed)
                return
            
            # Lista alla textfiler
            all_files = [f for f in os.listdir(text_folder) if f.endswith('.txt')]
            
            # Filtrera filer baserat på source om angiven
            if source:
                files_to_search = [f for f in all_files if source.lower() in f.lower()]
                if not files_to_search:
                    embed = await self.helper.create_error_response(
                        interaction.user.id,
                        f"Inga filer hittades för källa '{source}'",
                        f"Tillgängliga filer: {', '.join(all_files[:5])}{'...' if len(all_files) > 5 else ''}"
                    )
                    await self.helper.send_response(interaction, embed=embed)
                    return
            else:
                files_to_search = all_files
            
            # Sök igenom filer
            results = []
            for file in files_to_search:
                file_path = os.path.join(text_folder, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Hitta alla stycken med sökfrasen
                    paragraphs = content.split('\n\n')
                    for paragraph in paragraphs:
                        if query.lower() in paragraph.lower():
                            # Begränsa styckets längd och rensa
                            clean_para = ' '.join(paragraph.split())
                            excerpt = (clean_para[:300] + '...') if len(clean_para) > 300 else clean_para
                            results.append((file, excerpt))
                            
                            # Begränsa resultat per fil för prestanda
                            if len([r for r in results if r[0] == file]) >= 3:
                                break
                                
                except Exception as e:
                    print(f"Fel vid läsning av {file}: {e}")
                    continue
            
            if not results:
                embed = self.embed_factory.knowledge_result(
                    interaction.user.id,
                    interaction.user.display_name,
                    query,
                    f"Inga träffar hittades för '{query}'",
                    []
                )
                await self.helper.send_response(interaction, embed=embed)
                return
            
            # Begränsa till max_results
            limited_results = results[:max_results]
            
            # Skapa resultat embed
            embed = self.embed_factory.knowledge_result(
                interaction.user.id,
                interaction.user.display_name,
                query,
                f"Hittade {len(results)} träffar",
                list(set([filename for filename, _ in limited_results]))
            )
            
            embed.title = f"📚 Sökresultat för: {query}"
            embed.clear_fields()  # Clear default fields
            
            # Lägg till träffar
            for i, (filename, excerpt) in enumerate(limited_results):
                embed.add_field(
                    name=f"Träff {i+1} - {filename}",
                    value=excerpt,
                    inline=False
                )
            
            # Footer med info om begränsade resultat
            if len(results) > max_results:
                embed.set_footer(
                    text=f"Visar {max_results} av {len(results)} träffar. Använd mer specifika söktermer för bättre resultat."
                )
            
            execution_time = time.time() - start_time
            await self.helper.log_command_usage(interaction, "sök", {
                "query": query,
                "source": source,
                "max_results": max_results,
                "total_results": len(results)
            }, execution_time)
            
            await self.helper.send_response(interaction, embed=embed)
            
        except Exception as e:
            embed = await self.helper.create_error_response(
                interaction.user.id,
                f"Ett oväntat fel inträffade: {str(e)}"
            )
            await self.helper.send_response(interaction, embed=embed)

    @app_commands.command(name="allt", description="Omfattande AI-sökning genom alla EON-dokument")
    @app_commands.describe(
        query="Sökfras för omfattande sökning",
        max_passages="Antal textavsnitt att analysera (5-20)"
    )
    async def allt_slash(
        self,
        interaction: discord.Interaction,
        query: str,
        max_passages: app_commands.Range[int, 5, 20] = 15
    ):
        """Slash command version av !allt - omfattande AI-sökning."""
        # KRITISKT: Defer omedelbart för AI operations
        await self.helper.safe_defer(interaction)
        start_time = time.time()
        
        try:
            # Validera input
            if len(query.strip()) < 3:
                embed = await self.helper.create_error_response(
                    interaction.user.id,
                    "Sökfrasen är för kort",
                    "Använd minst 3 tecken för omfattande sökning"
                )
                await self.helper.send_response(interaction, embed=embed)
                return
            
            # Hämta project root och text folder
            script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            project_root = os.path.dirname(script_dir)
            text_folder = os.path.join(project_root, "data", "extracted_text")
            
            if not os.path.exists(text_folder):
                embed = await self.helper.create_error_response(
                    interaction.user.id,
                    "Textmappen hittades inte",
                    f"Förväntade: {text_folder}"
                )
                await self.helper.send_response(interaction, embed=embed)
                return
            
            # Samla relevanta textavsnitt från alla filer
            all_passages = []
            
            for filename in os.listdir(text_folder):
                if filename.endswith('.txt'):
                    try:
                        with open(os.path.join(text_folder, filename), 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        # Dela upp i stycken och kontrollera varje
                        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
                        for paragraph in paragraphs:
                            if query.lower() in paragraph.lower():
                                all_passages.append({
                                    'source': filename,
                                    'text': paragraph
                                })
                    except Exception as e:
                        print(f"Fel vid läsning av {filename}: {e}")
            
            if not all_passages:
                embed = self.embed_factory.knowledge_result(
                    interaction.user.id,
                    interaction.user.display_name,
                    query,
                    f"Hittade inga textavsnitt för '{query}'",
                    []
                )
                await self.helper.send_response(interaction, embed=embed)
                return
            
            # Begränsa till max_passages för prestanda
            limited_passages = all_passages[:max_passages]
            
            # Skapa prompt för Claude
            prompt = f"""
            Du är en spelledarassistent för rollspelet Eon. Följande textavsnitt hittades när användaren sökte efter "{query}".
            
            Hittade avsnitt:
            """
            
            for i, passage in enumerate(limited_passages):
                prompt += f"\n--- Från {passage['source']} ---\n{passage['text']}\n"
            
            prompt += f"\nBaserat på ovanstående information, svara på frågan: {query}"
            
            # Kontrollera att Claude API är tillgänglig
            if not self.knowledge_base.claude_client:
                embed = await self.helper.create_error_response(
                    interaction.user.id,
                    "Claude API är inte tillgänglig",
                    "Kontrollera ANTHROPIC_API_KEY i .env-filen"
                )
                await self.helper.send_response(interaction, embed=embed)
                return
            
            # Använd AI handler för Claude API call
            success, response = await self.ai_handler.execute_with_timeout(
                interaction,
                self.knowledge_base.claude_client.messages.create,
                (),
                {
                    'model': CLAUDE_MODEL,
                    'max_tokens': 2000,
                    'messages': [{"role": "user", "content": prompt}]
                },
                query=query
            )
            
            if not success:
                embed = await self.helper.create_error_response(
                    interaction.user.id,
                    "AI-analysen misslyckades",
                    response
                )
                await self.helper.send_response(interaction, embed=embed)
                return
            
            # Extrahera text från Claude response
            ai_response = response.content[0].text
            
            # Skapa resultat embed
            sources_list = list(set(p['source'] for p in limited_passages))
            embed = self.embed_factory.knowledge_result(
                interaction.user.id,
                interaction.user.display_name,
                query,
                ai_response,
                sources_list
            )
            
            # Lägg till omfattande sökning info
            embed.add_field(
                name="🔍 Omfattande Sökning",
                value=f"Analyserade {len(limited_passages)} textavsnitt från {len(sources_list)} källor",
                inline=False
            )
            
            if len(all_passages) > max_passages:
                embed.set_footer(
                    text=f"Analyserade {max_passages} av {len(all_passages)} hittade avsnitt för optimal prestanda"
                )
            
            execution_time = time.time() - start_time
            await self.helper.log_command_usage(interaction, "allt", {
                "query": query[:100],
                "max_passages": max_passages,
                "total_passages": len(all_passages),
                "sources_count": len(sources_list)
            }, execution_time)
            
            await self.helper.send_response(interaction, embed=embed)
            
        except Exception as e:
            embed = await self.helper.create_error_response(
                interaction.user.id,
                f"Ett oväntat fel inträffade: {str(e)}"
            )
            await self.helper.send_response(interaction, embed=embed)


# Registrering function
async def register_slash_knowledge_commands(bot, knowledge_base, color_handler, embed_factory):
    """
    Registrera slash knowledge commands med boten.
    """
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
    from config.feature_flags import is_command_enabled
    
    # Kontrollera om slash knowledge commands är aktiverade
    if not is_command_enabled("ask", "knowledge"):
        print("Slash knowledge commands är inte aktiverade enligt feature flags")
        return
    
    # Lägg till cog
    knowledge_cog = KnowledgeSlashCommands(bot, knowledge_base, color_handler, embed_factory)
    await bot.add_cog(knowledge_cog)
    print("Slash knowledge commands har registrerats (/ask, /sök, /allt).")