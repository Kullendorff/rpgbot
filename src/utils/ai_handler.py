"""
AI Handler för timeout-hantering och intelligent AI-operation management.
Implementerar intelligent timeout-hantering för knowledge commands.
"""

import asyncio
import time
from typing import Optional, Callable, Dict, Any, Tuple
import discord
from datetime import datetime, timedelta

class AIHandler:
    """Hanterar AI-operationer med intelligent timeout och progress feedback."""
    
    def __init__(self, embed_factory):
        """
        Initiera AI Handler.
        
        Args:
            embed_factory: EmbedFactory instans för konsistent embed-skapande
        """
        self.embed_factory = embed_factory
        self.query_cache = {}  # Simple in-memory cache
        self.cache_timeout = 3600  # 1 hour cache
        self.operation_timeout = 45  # 45 second max timeout
        self.progress_feedback_delay = 5  # Show progress after 5 seconds
        
    def _generate_cache_key(self, query: str, context: str = "") -> str:
        """Generera cache-nyckel från query och context."""
        combined = f"{query}:{context}"
        return str(hash(combined))
    
    def _is_cache_valid(self, cache_entry: Dict) -> bool:
        """Kontrollera om cache entry fortfarande är giltig."""
        if not cache_entry:
            return False
        
        cache_time = cache_entry.get('timestamp', 0)
        return (time.time() - cache_time) < self.cache_timeout
    
    def get_cached_response(self, query: str, context: str = "") -> Optional[str]:
        """
        Hämta cached response om den finns och är giltig.
        
        Args:
            query: Användarens fråga
            context: Kontext för frågan
            
        Returns:
            Cached response eller None
        """
        cache_key = self._generate_cache_key(query, context)
        cache_entry = self.query_cache.get(cache_key)
        
        if self._is_cache_valid(cache_entry):
            print(f"[AI_HANDLER] Cache hit för query: {query[:50]}...")
            return cache_entry['response']
        
        return None
    
    def cache_response(self, query: str, response: str, context: str = "") -> None:
        """
        Cachea ett AI-svar.
        
        Args:
            query: Användarens fråga
            response: AI-svaret
            context: Kontext för frågan
        """
        cache_key = self._generate_cache_key(query, context)
        self.query_cache[cache_key] = {
            'response': response,
            'timestamp': time.time(),
            'query': query
        }
        
        print(f"[AI_HANDLER] Cached response för query: {query[:50]}...")
    
    async def execute_with_timeout(
        self,
        interaction: discord.Interaction,
        operation: Callable,
        operation_args: tuple = (),
        operation_kwargs: dict = None,
        query: str = "",
        show_progress: bool = True
    ) -> Tuple[bool, Any]:
        """
        Exekvera AI-operation med timeout och progress feedback.
        
        Args:
            interaction: Discord interaction
            operation: Function att köra
            operation_args: Args för operation
            operation_kwargs: Kwargs för operation  
            query: Query string för logging
            show_progress: Om progress feedback ska visas
            
        Returns:
            Tuple[bool, Any]: (success, result)
        """
        if operation_kwargs is None:
            operation_kwargs = {}
        
        # Kontrollera cache först
        if hasattr(operation, '__name__') and 'generate_response' in operation.__name__:
            context = operation_kwargs.get('context', '')
            cached = self.get_cached_response(query, context)
            if cached:
                return True, cached
        
        start_time = time.time()
        progress_task = None
        
        try:
            # Starta progress feedback task om operation tar tid
            if show_progress:
                progress_task = asyncio.create_task(
                    self._show_progress_feedback(interaction, query)
                )
            
            # Kör operation med timeout
            result = await asyncio.wait_for(
                asyncio.to_thread(operation, *operation_args, **operation_kwargs),
                timeout=self.operation_timeout
            )
            
            execution_time = time.time() - start_time
            
            # Logga långsamma operationer
            if execution_time > 10:
                print(f"[AI_HANDLER] Långsam operation: {execution_time:.2f}s för '{query[:50]}...'")
            
            # Cachea resultatet om det är ett AI-svar
            if hasattr(operation, '__name__') and 'generate_response' in operation.__name__:
                context = operation_kwargs.get('context', '')
                self.cache_response(query, result, context)
            
            return True, result
            
        except asyncio.TimeoutError:
            print(f"[AI_HANDLER] Timeout efter {self.operation_timeout}s för '{query[:50]}...'")
            return False, "AI-operationen tog för lång tid och avbröts. Försök med en enklare fråga."
            
        except Exception as e:
            print(f"[AI_HANDLER] Fel i AI-operation: {e}")
            return False, f"Ett fel uppstod: {str(e)}"
            
        finally:
            # Avbryt progress feedback
            if progress_task and not progress_task.done():
                progress_task.cancel()
                try:
                    await progress_task
                except asyncio.CancelledError:
                    pass
    
    async def _show_progress_feedback(self, interaction: discord.Interaction, query: str):
        """
        Visa progress feedback efter en kort delay.
        
        Args:
            interaction: Discord interaction
            query: Query som bearbetas
        """
        try:
            await asyncio.sleep(self.progress_feedback_delay)
            
            # Kontrollera om interaction fortfarande är aktiv
            if interaction.response.is_done():
                # Använd followup för progress update
                progress_embed = self.embed_factory.admin_message(
                    interaction.user.id,
                    "🤖 Bearbetar din fråga...",
                    f"Claude AI analyserar: {query[:100]}{'...' if len(query) > 100 else ''}"
                )
                
                await interaction.followup.send(embed=progress_embed, ephemeral=True)
            
        except asyncio.CancelledError:
            # Task avbröts - normalt beteende
            pass
        except Exception as e:
            print(f"[AI_HANDLER] Fel i progress feedback: {e}")
    
    async def safe_ai_operation(
        self,
        interaction: discord.Interaction,
        knowledge_base,
        query: str,
        operation_type: str = "ask",
        **kwargs
    ) -> Optional[str]:
        """
        Säker AI-operation med full felhantering.
        
        Args:
            interaction: Discord interaction
            knowledge_base: KnowledgeBase instans
            query: Användarens fråga
            operation_type: Typ av operation (ask, allt, etc.)
            **kwargs: Extra arguments för operationen
            
        Returns:
            AI-svar eller None vid fel
        """
        # Kontrollera att knowledge base är initialiserad
        if not knowledge_base.pc or not knowledge_base.embedding_model or not knowledge_base.claude_client:
            print("[AI_HANDLER] Knowledge base inte initialiserad, försöker initialisera...")
            success = knowledge_base.initialize_knowledge_base()
            if not success:
                error_embed = await self.create_error_response(
                    interaction.user.id,
                    "Kunskapsbasen kunde inte initialiseras",
                    "Kontrollera API-nycklar i .env-filen"
                )
                await interaction.followup.send(embed=error_embed)
                return None
        
        try:
            if operation_type == "ask":
                # Hämta context först
                success, context_result = await self.execute_with_timeout(
                    interaction,
                    knowledge_base.query_knowledge_base,
                    (query,),
                    show_progress=False
                )
                
                if not success:
                    error_embed = await self.create_error_response(
                        interaction.user.id,
                        "Kunde inte söka i kunskapsbasen",
                        context_result
                    )
                    await interaction.followup.send(embed=error_embed)
                    return None
                
                context, sources = context_result
                
                if not context or "Ett fel uppstod" in context:
                    error_embed = await self.create_error_response(
                        interaction.user.id,
                        "Kunde inte hitta relevant information",
                        context
                    )
                    await interaction.followup.send(embed=error_embed)
                    return None
                
                # Generera svar med Claude
                success, response = await self.execute_with_timeout(
                    interaction,
                    knowledge_base.generate_response,
                    (query, context),
                    query=query
                )
                
                if success:
                    return response, sources
                else:
                    error_embed = await self.create_error_response(
                        interaction.user.id,
                        "AI-svaret kunde inte genereras",
                        response
                    )
                    await interaction.followup.send(embed=error_embed)
                    return None
                    
            elif operation_type == "allt":
                # Implementera allt-operation
                # Detta kräver mer komplex hantering med filsökning
                pass
                
        except Exception as e:
            print(f"[AI_HANDLER] Oväntat fel i safe_ai_operation: {e}")
            error_embed = await self.create_error_response(
                interaction.user.id,
                "Ett oväntat fel inträffade",
                str(e)
            )
            await interaction.followup.send(embed=error_embed)
            return None
    
    async def create_error_response(
        self,
        user_id: int,
        error_title: str,
        error_description: str = ""
    ) -> discord.Embed:
        """
        Skapa error embed med konsistent styling.
        
        Args:
            user_id: Discord user ID
            error_title: Titel på felet
            error_description: Beskrivning av felet
            
        Returns:
            Discord embed med felmeddelande
        """
        return self.embed_factory.admin_message(
            user_id,
            f"⚠️ {error_title}",
            error_description if error_description else "Kontakta en administratör om problemet kvarstår."
        )
    
    def clear_cache(self) -> int:
        """
        Rensa cache.
        
        Returns:
            Antal cachade entries som togs bort
        """
        count = len(self.query_cache)
        self.query_cache.clear()
        print(f"[AI_HANDLER] Rensade {count} cachade entries")
        return count
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Hämta cache-statistik.
        
        Returns:
            Dictionary med cache-statistik
        """
        valid_entries = sum(1 for entry in self.query_cache.values() if self._is_cache_valid(entry))
        
        return {
            'total_entries': len(self.query_cache),
            'valid_entries': valid_entries,
            'invalid_entries': len(self.query_cache) - valid_entries,
            'cache_timeout': self.cache_timeout,
            'operation_timeout': self.operation_timeout
        }