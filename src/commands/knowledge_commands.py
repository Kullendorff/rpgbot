import os
import discord
from discord.ext import commands
from typing import Optional
import anthropic
from core.constants import MAX_TOKENS, CLAUDE_MODEL


def register_knowledge_commands(bot, knowledge_base, color_handler, embed_factory):
    """
    Registrerar alla kunskapsrelaterade kommandon för boten.
    
    Args:
        bot: Discord bot-instansen
        knowledge_base: KnowledgeBase-instans för AI-frågor
        color_handler: ColorHandler-instans för användarfärger
    """
    
    @bot.command(name='ask')
    async def ask_command(ctx: commands.Context, *, query: str = None) -> None:
        """
        Ställer en fråga till kunskapsbasen och får ett svar baserat på rollspelsböckerna.
        
        Användning: !ask Vad är reglerna för stridskonst?
        
        Args:
            ctx (commands.Context): Kontexten för kommandot.
            query (str): Frågan att ställa till kunskapsbasen.
        """
        if not query:
            await ctx.send("Användning: `!ask [din fråga]`\nExempel: `!ask Hur fungerar magi i Eon?`")
            return
        
        # Visa att boten bearbetar frågan
        async with ctx.typing():
            # Kontrollera om kunskapsbasen är initialiserad. ensure_ready()
            # kör laddningen i en bakgrundstråd och delar lås med
            # bakgrundsjobbet i main.py, så vi väntar bara in en redan
            # pågående laddning istället för att starta en andra.
            if not knowledge_base.is_ready:
                print("Kunskapsbasen är inte initialiserad, väntar in laddningen...")
                success = await knowledge_base.ensure_ready()
                if not success:
                    await ctx.send("⚠️ Kunskapsbasen kunde inte initialiseras. Kontrollera API-nycklar i .env-filen.")
                    return
            
            # Hämta relevanta avsnitt från kunskapsbasen
            context, sources = knowledge_base.query_knowledge_base(query)
            
            if not context or "Ett fel uppstod" in context:
                await ctx.send(f"⚠️ Kunde inte söka i kunskapsbasen: {context}")
                return
            
            # Generera svar med Claude
            response = knowledge_base.generate_response(query, context)
            
            # Skapa embed för svaret
            embed = embed_factory.knowledge_result(
                ctx.author.id,
                ctx.author.display_name,
                query,
                response,
                sources
            )
            
            # Skicka svaret
            await ctx.send(embed=embed)
            
    @bot.command(name='allt')
    async def allt_command(ctx: commands.Context, *, query: str = None) -> None:
        """
        Söker igenom alla textfiler och returnerar hela stycken som matchar.
        """
        if not query:
            await ctx.send("Användning: `!allt [sökfras]`")
            return
        
        async with ctx.typing():
            # Hämta project root från main.py's logik
            script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            project_root = os.path.dirname(script_dir)
            text_folder = os.path.join(project_root, "data", "extracted_text")
            
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
                await ctx.send(f"Hittade inga träffar för '{query}'")
                return
                
            # Skapa en prompt till Claude med alla hittade avsnitt
            prompt = f"""
            Du är en spelledarassistent för rollspelet Eon. Följande textavsnitt hittades när användaren sökte efter "{query}".
            
            Hittade avsnitt:
            """
            
            for i, passage in enumerate(all_passages[:15]):  # Begränsa till 15 för att inte överbelasta
                prompt += f"\n--- Från {passage['source']} ---\n{passage['text']}\n"
                
            prompt += f"\nBaserat på ovanstående information, svara på frågan: {query}"
                
            # Anropa Claude med alla hittade avsnitt
            if not knowledge_base.claude_client:
                await ctx.send("⚠️ Claude API är inte tillgänglig.")
                return
                
            response = knowledge_base.claude_client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=MAX_TOKENS,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            # Skicka tillbaka svaret  
            sources_list = list(set(p['source'] for p in all_passages[:15]))
            embed = embed_factory.knowledge_result(
                ctx.author.id,
                ctx.author.display_name,
                query,
                response.content[0].text,
                sources_list
            )
            
            await ctx.send(embed=embed)        
            
    @bot.command(name='sök')
    async def sok_command(ctx: commands.Context, *args) -> None:
        """
        Söker efter information i filer vars namn innehåller söktermen.
        
        Användning: 
          !sök [sökfras]           - söker i alla filer
          !sök -f fildelnamn [sökfras] - söker i filer som innehåller fildelnamn
        """
        if not args:
            await ctx.send("Användning: `!sök [sökfras]` eller `!sök -f fildelnamn [sökfras]`")
            return
        
        # Kolla om användaren vill söka i specifik fil
        if args[0] == "-f" and len(args) >= 3:
            file_pattern = args[1].lower()
            search_terms = " ".join(args[2:])
            search_in_specific_files = True
        else:
            search_terms = " ".join(args)
            search_in_specific_files = False
        
        async with ctx.typing():
            try:
                # Hämta project root från main.py's logik
                script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                project_root = os.path.dirname(script_dir)
                text_folder = os.path.join(project_root, "data", "extracted_text")
                
                # Lista alla textfiler
                all_files = [f for f in os.listdir(text_folder) if f.endswith('.txt')]
                
                if search_in_specific_files:
                    # Filtrera filer som innehåller det angivna mönstret
                    files_to_search = [f for f in all_files if file_pattern.lower() in f.lower()]
                    
                    if not files_to_search:
                        await ctx.send(f"⚠️ Inga filer hittades som innehåller '{file_pattern}'.")
                        return
                        
                    # Visa vilka filer som söks igenom
                    file_list = "\n".join([f"• {f}" for f in files_to_search[:5]])
                    if len(files_to_search) > 5:
                        file_list += f"\n... och {len(files_to_search) - 5} till"
                    
                    await ctx.send(f"Söker i följande filer:\n{file_list}")
                else:
                    # Sök i alla filer
                    files_to_search = all_files
                    
                results = []
                for file in files_to_search:
                    file_path = os.path.join(text_folder, file)
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Hitta alla stycken med sökfrasen
                    paragraphs = content.split('\n\n')
                    for paragraph in paragraphs:
                        if search_terms.lower() in paragraph.lower():
                            # Begränsa styckets längd och rensa från överflödiga radbrytningar
                            clean_para = ' '.join(paragraph.split())
                            excerpt = (clean_para[:300] + '...') if len(clean_para) > 300 else clean_para
                            results.append((file, excerpt))
                    
                if not results:
                    await ctx.send(f"Inga träffar för '{search_terms}'.")
                    return
                
                # Skapa ett snyggt svar
                embed = embed_factory.knowledge_result(
                    ctx.author.id,
                    ctx.author.display_name,
                    search_terms,
                    f"Hittade {len(results)} träffar",
                    [filename for filename, _ in results[:5]]
                )
                embed.title = f"📚 Sökresultat för: {search_terms}"
                embed.clear_fields()  # Clear default fields from knowledge_result
                
                # Lägg till max 5 träffar i svaret
                for i, (filename, excerpt) in enumerate(results[:5]):
                    embed.add_field(
                        name=f"Träff {i+1} - {filename}",
                        value=excerpt,
                        inline=False
                    )
                    
                if len(results) > 5:
                    embed.set_footer(text=f"Visar 5 av {len(results)} träffar. Använd mer specifika söktermer för bättre resultat.")
                    
                await ctx.send(embed=embed)
                    
            except Exception as e:
                await ctx.send(f"Ett fel uppstod: {str(e)}")