import os
from typing import Tuple, List, Optional
from pinecone import Pinecone
from sentence_transformers import SentenceTransformer
import anthropic
from .constants import MAX_TOKENS, DEFAULT_TOP_K

class KnowledgeBase:
    def __init__(self):
        """Initiera KnowledgeBase-klassen."""
        self.pc: Optional[Pinecone] = None
        self.embedding_model: Optional[SentenceTransformer] = None
        self.claude_client: Optional[anthropic.Anthropic] = None
        self.pinecone_api_key: Optional[str] = os.getenv("PINECONE_API_KEY")
        self.anthropic_api_key: Optional[str] = os.getenv("ANTHROPIC_API_KEY")
        self.pinecone_index_name: str = os.getenv("PINECONE_INDEX_NAME", "rpg-knowledge")

    def initialize_knowledge_base(self) -> bool:
        """
        Initiera kopplingar till kunskapsbasen och AI-tjänsterna.
        
        Returns:
            bool: True om initialiseringen lyckades, False annars
        """
        # Kontrollera om API-nycklar finns
        if not self.pinecone_api_key:
            print("Varning: PINECONE_API_KEY saknas. Kunskapsbasfunktionen kommer inte att fungera.")
            return False
            
        if not self.anthropic_api_key:
            print("Varning: ANTHROPIC_API_KEY saknas. Kunskapsbasfunktionen kommer inte att fungera.")
            return False
        
        try:
            # Initiera Pinecone
            print("Initierar Pinecone...")
            self.pc = Pinecone(api_key=self.pinecone_api_key)
            
            # Kontrollera om indexet finns
            print(f"Kontrollerar om index '{self.pinecone_index_name}' finns...")
            available_indexes = self.pc.list_indexes().names()
            print(f"Tillgängliga index: {available_indexes}")
            
            if self.pinecone_index_name not in available_indexes:
                print(f"Varning: Pinecone-index '{self.pinecone_index_name}' hittades inte.")
                return False
            
            # Initiera embedding-modell
            print("Laddar embedding-modell...")
            self.embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
            
            # Initiera Claude API
            print(f"Initierar Claude API med nyckel: {self.anthropic_api_key[:4]}...{self.anthropic_api_key[-4:] if len(self.anthropic_api_key) > 8 else ''}")
            try:
                self.claude_client = anthropic.Anthropic(api_key=self.anthropic_api_key)
                # Testa anslutningen med ett enkelt API-anrop
                print("Testar Claude API-anslutningen...")
                test_response = self.claude_client.messages.create(
                    model="claude-3-5-sonnet-20240620",
                    max_tokens=10,
                    messages=[
                        {"role": "user", "content": "Say hello"}
                    ]
                )
                print("Claude API-anslutning lyckades!")
            except Exception as claude_error:
                print(f"Fel vid initiering av Claude API: {claude_error}")
                self.claude_client = None
                return False
            
            print("Kunskapsbasen har initialiserats framgångsrikt.")
            return True
        except Exception as e:
            print(f"Fel vid initiering av kunskapsbasen: {e}")
            return False

    def query_knowledge_base(self, query: str, top_k: int = DEFAULT_TOP_K) -> Tuple[str, List[str]]:
        """
        Hämtar relevanta avsnitt från kunskapsbasen baserat på frågan.
        
        Args:
            query (str): Användarens fråga
            top_k (int): Antal resultat att hämta
            
        Returns:
            Tuple[str, List[str]]: (kontexttext, källreferenser)
        """
        if not self.pc:
            print("Fel: Pinecone-klient är inte initialiserad")
            return "Kunskapsbasen är inte korrekt initialiserad (Pinecone).", []
        
        if not self.embedding_model:
            print("Fel: Embedding-modell är inte initialiserad")
            return "Kunskapsbasen är inte korrekt initialiserad (Embedding).", []
        
        try:
            # Skapa embedding för frågan
            query_embedding = self.embedding_model.encode(query).tolist()
            
            # Hämta index
            index = self.pc.Index(self.pinecone_index_name)
            
            # Sök efter relevanta avsnitt
            search_results = index.query(
                vector=query_embedding,
                top_k=15,
                include_metadata=True
            )
            
            # Extrahera relevant kontext och källor
            context = ""
            sources = []
            
            for match in search_results["matches"]:
                source = match['metadata'].get('source') or match['metadata'].get('file_name', 'Okänd källa')
                text = match['metadata'].get('text', '')
                
                # Lägg till source i källistan om den inte redan finns
                if source not in sources:
                    sources.append(source)
                    
                # Lägg till text till kontexten
                context += f"[Källa: {source}]\n{text}\n\n"
            
            return context, sources
        except Exception as e:
            print(f"Fel vid sökning i kunskapsbasen: {e}")
            return f"Ett fel uppstod vid sökning i kunskapsbasen: {str(e)}", []

    def generate_response(self, query: str, context: str) -> str:
        """
        Använder Claude API för att generera ett svar baserat på frågan och kontexten.
        
        Args:
            query (str): Användarens fråga
            context (str): Relevant kontext från kunskapsbasen
            
        Returns:
            str: Claude's svar
        """
        if not self.claude_client:
            print("Fel: Claude-klient är inte initialiserad")
            return "Claude API är inte tillgänglig. Kontrollera att ANTHROPIC_API_KEY är korrekt inställd i .env-filen."
        
        try:
            response = self.claude_client.messages.create(
                model="claude-3-5-sonnet-20240620",
                max_tokens=MAX_TOKENS,
                messages=[
                    {
                        "role": "user",
                        "content": f"""
                        Du är en spelledarassistent för rollspelet Eon. Din uppgift är att svara på frågor 
                        baserat på rollspelsböckerna.
                        
                        Här är relevant information från rollspelsböckerna:
                        {context}
                        
                        Använd informationen ovan för att besvara följande fråga så bra du kan:
                        {query}
                        
                        Om informationen i kontexten inte är fullständig men ändå ger ledtrådar,
                        sammanfatta det du kan utläsa och nämn var informationen kommer ifrån.
                        Endast om informationen helt saknas, skriv "Jag har inte den informationen i regelböckerna."
                        
                        Var koncis och korrekt i ditt svar.
                        """
                    }
                ]
            )
            
            return response.content[0].text
        except Exception as e:
            print(f"Fel vid användning av Claude API: {e}")
            return f"Ett fel uppstod vid generering av svar: {str(e)}"