import os
import random
import re
from typing import Tuple, Optional, List, Any, Dict, Union
import time
import discord
import numpy as np
import tiktoken
from discord.ext import commands
from dotenv import load_dotenv
from pinecone import Pinecone
from sentence_transformers import SentenceTransformer
import anthropic
from whoosh.index import open_dir
from whoosh.qparser import QueryParser

# Importera lokala moduler
from color_handler import ColorHandler
from roll_tracker import RollTracker
from combat_manager import CombatManager
from damage_tables import DamageType
from hit_tables import WeaponType  # om du vill ha typ-checking
from fumble_tables import FUMBLE_TABLES, WEAPON_TYPE_ALIASES

# Import för ytterligare moduler
import stats_commands
# Import för Skjut dom i huvudet
from skjutdomihuvudet import commands as sdih_commands

# Import för rollpersonsskapande
import character_creation

# Ladda miljövariabler från .env-filen
load_dotenv()

# Hämta tokens och API-nycklar från miljövariablerna
DISCORD_TOKEN: Optional[str] = os.getenv('DISCORD_TOKEN')
CHANNEL_IDS: Optional[str] = os.getenv('CHANNEL_IDS')
PINECONE_API_KEY: Optional[str] = os.getenv("PINECONE_API_KEY")
ANTHROPIC_API_KEY: Optional[str] = os.getenv("ANTHROPIC_API_KEY")
PINECONE_INDEX_NAME: str = os.getenv("PINECONE_INDEX_NAME", "rpg-knowledge")

# Konfigurera Discord-boten med nödvändiga behörigheter
intents: discord.Intents = discord.Intents.default()
intents.message_content = True
bot: commands.Bot = commands.Bot(command_prefix='!', intents=intents)

# Initiera hjälputrustning
color_handler: ColorHandler = ColorHandler()
roll_tracker: RollTracker = RollTracker()
combat_manager: CombatManager = CombatManager()

# Konfigurera mappar för regler och kunskapsindex
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
RULES_FOLDER: str = os.path.join(project_root, "data", "rules")
INDEX_FOLDER: str = os.path.join(project_root, "data", "knowledge_index")

# Skapa mappen om den inte finns
if not os.path.exists(RULES_FOLDER):
    os.makedirs(RULES_FOLDER)

# Globala variabler för kunskapsbasen
pc: Optional[Pinecone] = None
embedding_model: Optional[SentenceTransformer] = None
claude_client: Optional[anthropic.Anthropic] = None

# Umnataks Discord ID
UMNATAK_ID = "680064176227352610"

# Kommentarer kommer att laddas in från fil
UMNATAK_SUCCESS_COMMENTS = []

def load_umnatak_comments():
    """
    Laddar in syrliga kommentarer för Umnatak från en textfil.
    Varje rad i filen blir en separat kommentar.
    """
    comments_file = os.path.join(project_root, "data", "config", "umnak_comments.txt")
    try:
        if os.path.exists(comments_file):
            with open(comments_file, 'r', encoding='utf-8') as f:
                # Läs in alla rader och filtrera bort tomma rader
                global UMNATAK_SUCCESS_COMMENTS
                UMNATAK_SUCCESS_COMMENTS = [line.strip() for line in f.readlines() if line.strip()]
            print(f"Laddade {len(UMNATAK_SUCCESS_COMMENTS)} kommentarer för Umnatak")
        else:
            print(f"Varning: Kunde inte hitta kommentarsfilen: {comments_file}")
            # Sätt några standardkommentarer om filen saknas
            UMNATAK_SUCCESS_COMMENTS = [
                "Wow, du lyckades faktiskt!",
                "Statistisk anomali - Umnatak lyckades.",
                "En högst oväntad framgång."
            ]
    except Exception as e:
        print(f"Fel vid inläsning av Umnatak-kommentarer: {e}")
        UMNATAK_SUCCESS_COMMENTS = ["Ovanligt att se dig lyckas, Umnatak!"]

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

def initialize_knowledge_base() -> bool:
    """
    Initiera kopplingar till kunskapsbasen och AI-tjänsterna.
    
    Returns:
        bool: True om initialiseringen lyckades, False annars
    """
    global pc, embedding_model, claude_client
    
    # Kontrollera om API-nycklar finns
    if not PINECONE_API_KEY:
        print("Varning: PINECONE_API_KEY saknas. Kunskapsbasfunktionen kommer inte att fungera.")
        return False
        
    if not ANTHROPIC_API_KEY:
        print("Varning: ANTHROPIC_API_KEY saknas. Kunskapsbasfunktionen kommer inte att fungera.")
        return False
    
    try:
        # Initiera Pinecone
        print("Initierar Pinecone...")
        pc = Pinecone(api_key=PINECONE_API_KEY)
        
        # Kontrollera om indexet finns
        print(f"Kontrollerar om index '{PINECONE_INDEX_NAME}' finns...")
        available_indexes = pc.list_indexes().names()
        print(f"Tillgängliga index: {available_indexes}")
        
        if PINECONE_INDEX_NAME not in available_indexes:
            print(f"Varning: Pinecone-index '{PINECONE_INDEX_NAME}' hittades inte.")
            return False
        
        # Initiera embedding-modell
        print("Laddar embedding-modell...")
        embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
        
        # Initiera Claude API
        print(f"Initierar Claude API med nyckel: {ANTHROPIC_API_KEY[:4]}...{ANTHROPIC_API_KEY[-4:] if len(ANTHROPIC_API_KEY) > 8 else ''}")
        try:
            claude_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
            # Testa anslutningen med ett enkelt API-anrop
            print("Testar Claude API-anslutningen...")
            test_response = claude_client.messages.create(
                model="claude-3-5-sonnet-20240620",
                max_tokens=10,
                messages=[
                    {"role": "user", "content": "Say hello"}
                ]
            )
            print("Claude API-anslutning lyckades!")
        except Exception as claude_error:
            print(f"Fel vid initiering av Claude API: {claude_error}")
            claude_client = None
            return False
        
        print("Kunskapsbasen har initialiserats framgångsrikt.")
        return True
    except Exception as e:
        print(f"Fel vid initiering av kunskapsbasen: {e}")
        return False

def query_knowledge_base(query: str, top_k: int = 5) -> Tuple[str, List[str]]:
    """
    Hämtar relevanta avsnitt från kunskapsbasen baserat på frågan.
    
    Args:
        query (str): Användarens fråga
        top_k (int): Antal resultat att hämta
        
    Returns:
        Tuple[str, List[str]]: (kontexttext, källreferenser)
    """
    if not pc:
        print("Fel: Pinecone-klient är inte initialiserad")
        return "Kunskapsbasen är inte korrekt initialiserad (Pinecone).", []
    
    if not embedding_model:
        print("Fel: Embedding-modell är inte initialiserad")
        return "Kunskapsbasen är inte korrekt initialiserad (Embedding).", []
    
    try:
        # Skapa embedding för frågan
        query_embedding = embedding_model.encode(query).tolist()
        
        # Hämta index
        index = pc.Index(PINECONE_INDEX_NAME)
        
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

def generate_response(query: str, context: str) -> str:
    """
    Använder Claude API för att generera ett svar baserat på frågan och kontexten.
    
    Args:
        query (str): Användarens fråga
        context (str): Relevant kontext från kunskapsbasen
        
    Returns:
        str: Claude's svar
    """
    if not claude_client:
        print("Fel: Claude-klient är inte initialiserad")
        return "Claude API är inte tillgänglig. Kontrollera att ANTHROPIC_API_KEY är korrekt inställd i .env-filen."
    
    try:
        response = claude_client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=1000,
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

def count_tokens(text: str) -> int:
    """Räknar antal tokens i en given text med GPT-4:s tokenräknare."""
    encoder = tiktoken.encoding_for_model("gpt-4")
    return len(encoder.encode(text))
    
def clean_unicode(text):
    """
    Rensar en sträng från eventuella surrogatpar genom att först koda om till bytes 
    och sedan tillbaka till str med felhantering.
    
    Args:
        text (str): Texten som ska rensas
        
    Returns:
        str: Rensad text utan surrogatpar
    """
    if text is None:
        return None
        
    if isinstance(text, str):
        # Omvandla till bytes med 'surrogateescape' och tillbaka med 'replace'
        # Detta ersätter eventuella ogiltiga tecken med U+FFFD (ersättningstecken)
        return text.encode('utf-8', 'surrogateescape').decode('utf-8', 'replace')
    return text

def split_message(message: str, max_length: int = 2000) -> List[str]:
    """Dela upp ett långt meddelande i mindre delar."""
    return [message[i:i+max_length] for i in range(0, len(message), max_length)]

def parse_dice_string(dice_string: str) -> Tuple[int, int, int]:
    """
    Tolkar en tärningssträng med eventuell modifierare.
    
    Exempel:
      "3d6+2" returnerar (3, 6, 2)
      "4d8-1" returnerar (4, 8, -1)
      "2d10"   returnerar (2, 10, 0)
    
    Args:
        dice_string (str): Tärningssträngen att parsa.
    
    Returns:
        Tuple[int, int, int]: En tuple med antal tärningar, antal sidor och modifierare.
    
    Raises:
        ValueError: Om tärningssträngen inte kan parsas korrekt.
    """
    # Leta efter '+' eller '-' för att identifiera modifieraren
    modifier: int = 0
    if '+' in dice_string:
        dice_part, mod_part = dice_string.split('+')
        modifier = int(mod_part)
    elif '-' in dice_string:
        dice_part, mod_part = dice_string.split('-')
        modifier = -int(mod_part)
    else:
        dice_part = dice_string

    # Tolka tärningsdelen i formatet NdX
    num_dice, sides = map(int, dice_part.lower().split('d'))
    return num_dice, sides, modifier

def unlimited_d6s(num_dice: int, modifier: int = 0) -> Tuple[List[int], int, List[int]]:
    """
    Slår X stycken 6-sidiga tärningar enligt 'obegränsat'-regeln:
      - Varje 6a räknas inte med i summan men genererar +2 nya tärningar.
      - Upprepa tills inga nya tärningar finns kvar.
    
    Args:
        num_dice (int): Antal tärningar att slå initialt.
        modifier (int): Eventuell modifierare att lägga på slutresultatet.
    
    Returns:
        Tuple[List[int], int, List[int]]:
            - all_rolls: Lista med alla rullade tärningar (inklusive expansionskast).
            - final_total: Slutgiltig summa (exklusive 6:or) plus modifierare.
            - initial_rolls: Lista med resultat från första kastomgången.
    """
    # Första kastomgången
    initial_rolls: List[int] = [random.randint(1, 6) for _ in range(num_dice)]
    all_rolls: List[int] = initial_rolls[:]  # Kopiera för historik
    final_total: int = sum(r for r in initial_rolls if r != 6)

    # Beräkna antal extra tärningar för varje 6a
    extra_dice: int = sum(2 for r in initial_rolls if r == 6)

    # Sätt en gräns för hur många extra tärningar som kan slås
    max_rolls: int = 1000
    roll_count: int = 0
    
    # Utför expansionskast
    while extra_dice > 0 and roll_count < max_rolls:
        roll_count += 1
        roll: int = random.randint(1, 6)
        all_rolls.append(roll)
        extra_dice -= 1
        if roll == 6:
            extra_dice += 2
        else:
            final_total += roll
    
    # Logga om vi nådde maxgränsen (detta är extremt osannolikt)
    if roll_count >= max_rolls:
        print(f"Varning: Nådde maxgränsen på {max_rolls} slag för obegränsade T6-slag")

    final_total += modifier
    return all_rolls, final_total, initial_rolls

def simulate_unlimited_dice(num_dice: int, modifier: int, target: int, num_trials: int = 10000) -> float:
    """
    Simulerar obegränsade T6-slag och beräknar sannolikheten att lyckas.
    
    Args:
        num_dice (int): Antal tärningar.
        modifier (int): Modifierare till slaget.
        target (int): Målvärde att jämföra med.
        num_trials (int): Antal simuleringar att köra.
        
    Returns:
        float: Procentuell chans att lyckas.
    """
    successes = 0
    
    for _ in range(num_trials):
        # Använd den befintliga funktionen för att simulera ett slag
        _, total, _ = unlimited_d6s(num_dice, modifier)
        
        # Kontrollera om det lyckades
        if total <= target:
            successes += 1
            
    # Beräkna och returnera procentuell framgångsfrekvens
    return (successes / num_trials) * 100

# Bot event handlers and commands

@bot.event
async def on_ready() -> None:
    """Skriver ut ett meddelande när boten har kopplat upp sig mot Discord."""
    print(f"{bot.user} has connected to Discord!")
    print(f"Working directory: {os.getcwd()}")
    print(f"Rules folder: {RULES_FOLDER}")
    print(f"Index folder: {INDEX_FOLDER}")
    
    # Ladda in Umnatak-kommentarer
    load_umnatak_comments()
    
    # Initiera kunskapsbasen vid start
    success = initialize_knowledge_base()
    if success:
        print("Kunskapsbasen initierad och redo att användas.")
    else:
        print("Kunde inte initiera kunskapsbasen. Kommandot !ask kommer inte att fungera korrekt.")
        
    # Registrera statistikkommandona
    stats_commands.register_commands(bot, roll_tracker, color_handler)
    print("Statistikkommandon har registrerats (allstats, mystatsall).")
    
    # Registrera Skjut dom i huvudet-kommandon
    sdih_commands.register_commands(bot, roll_tracker, color_handler)
    print("Skjut dom i huvudet-kommandon har registrerats (rull, fördel, nackdel, etc.).")

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
        # Kontrollera om kunskapsbasen är initialiserad
        if not pc or not embedding_model or not claude_client:
            # Försök att initiera om
            print("Kunskapsbasen är inte initialiserad, försöker initialisera...")
            success = initialize_knowledge_base()
            if not success:
                await ctx.send("⚠️ Kunskapsbasen kunde inte initialiseras. Kontrollera API-nycklar i .env-filen.")
                return
        
        # Hämta relevanta avsnitt från kunskapsbasen
        context, sources = query_knowledge_base(query)
        
        if not context or "Ett fel uppstod" in context:
            await ctx.send(f"⚠️ Kunde inte söka i kunskapsbasen: {context}")
            return
        
        # Generera svar med Claude
        response = generate_response(query, context)
        
        # Skapa embed för svaret
        color = color_handler.get_user_color(ctx.author.id)
        embed = discord.Embed(
            title=f"Svar på: {query[:100]}{'...' if len(query) > 100 else ''}",
            description=response,
            color=color
        )
        
        # Lägg till källor om de finns
        if sources:
            source_text = "\n".join([f"• {source}" for source in sources])
            embed.add_field(name="Källor", value=source_text, inline=False)
        
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
        response = claude_client.messages.create(
            model="claude-3-5-sonnet-20240620", 
            max_tokens=1000,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        # Skicka tillbaka svaret
        color = color_handler.get_user_color(ctx.author.id)
        embed = discord.Embed(
            title=f"Svar på: {query}",
            description=response.content[0].text,
            color=color
        )
        
        sources = ", ".join(set(p['source'] for p in all_passages[:15]))
        embed.add_field(name="Källor", value=sources, inline=False)
        
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
            # Mapp med extraherade textfiler
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
            color = color_handler.get_user_color(ctx.author.id)
            embed = discord.Embed(
                title=f"Sökresultat för: {search_terms}",
                description=f"Hittade {len(results)} träffar",
                color=color
            )
            
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
            if not claude_client:
                # Försök att initiera om
                print("Claude-klienten är inte initialiserad, försöker initiera...")
                success = initialize_knowledge_base()
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
            response = claude_client.messages.create(
                model="claude-3-5-sonnet-20240620",
                max_tokens=1000,
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

@bot.command(name='fummel')
async def fummel_command(ctx: commands.Context, vapentyp: Optional[str] = None) -> None:
    """
    Slår på fummeltabellen för en specifik vapentyp.
    
    Användning: !fummel [vapentyp]
    Vapentyper: obe, nar, avs, sko
    
    Args:
        ctx (commands.Context): Kontexten för kommandot.
        vapentyp (Optional[str]): Den korta benämningen på vapentypen.
    """
    try:
        if vapentyp is None:
            await ctx.send(
                "Användning: `!fummel [vapentyp]`\n"
                "Vapentyper:\n"
                "- `obe` (obevapnat)\n"
                "- `nar` (närstrid)\n"
                "- `avs` (avståndsvapen)\n"
                "- `sko` (sköldar)"
            )
            return

        vapentyp = vapentyp.lower()
        if vapentyp not in WEAPON_TYPE_ALIASES:
            await ctx.send("Ogiltig vapentyp. Använd: obe, nar, avs, sko")
            return

        full_name: str = WEAPON_TYPE_ALIASES[vapentyp]
        result: int = random.randint(1, 20)
        fummel_text: str = FUMBLE_TABLES[full_name][result]
        color: int = color_handler.get_user_color(ctx.author.id)
        embed: discord.Embed = discord.Embed(
            title=f"💥 Fummel: {full_name.capitalize()}",
            description=f"Slag: {result}\n\n{fummel_text}",
            color=color
        )
        await ctx.send(embed=embed)

    except Exception as e:
        await ctx.send(f"Ett fel uppstod: {str(e)}")

async def process_melee_command(ctx: commands.Context, weapon: str, level_or_location: str, damage: int, flags: str) -> None:
    """
    Hanterar gemensam logik för melee-kommandon (t.ex. hugg, stick, kross).
    
    Args:
        ctx (commands.Context): Kontexten för kommandot.
        weapon (str): Vapentyp (t.ex. 'hugg', 'stick', 'kross').
        level_or_location (str): Angiven nivå eller träffområde.
        damage (int): Skadevärde.
        flags (str): Eventuella ytterligare flaggor (exempelvis '--ryttare', '--djur', '--mp').
    """
    try:
        # Kontrollera om Målpunkter (mp) anges i flaggorna
        use_malpunkter = "--mp" in flags.lower()
        
        # Kontrollera om attacken specificerar ett område (inte en nivå)
        location_override = None if level_or_location.lower() in ["låg", "normal", "hög"] else level_or_location.lower()
        
        # Kontrollera om Målpunkter kan användas
        if use_malpunkter and not location_override:
            await ctx.send("⚠️ Målpunkter kan endast användas när du anger ett specifikt träffområde, inte en attacknivå.")
            use_malpunkter = False
        
        result: Any = combat_manager.process_attack(
            weapon_type=weapon,
            attack_level=level_or_location if level_or_location.lower() in ["låg", "normal", "hög"] else None,
            damage_value=damage,
            location_override=location_override,
            is_mounted="--ryttare" in flags.lower(),
            is_quadruped="--djur" in flags.lower(),
            direction=None,
            use_malpunkter=use_malpunkter
        )
        response: str = combat_manager.format_result(result)
        color: int = color_handler.get_user_color(ctx.author.id)
        embed: discord.Embed = discord.Embed(color=color, description=f"```\n{response}\n```")
        await ctx.send(embed=embed)
    except ValueError as e:
        await ctx.send(f"Fel: {str(e)}\nAnvändning: !{weapon} [nivå/område] [skada] [flaggor]")

@bot.command(name='hugg')
async def hugg_command(ctx: commands.Context, level_or_location: str, damage: int, *, flags: str = "") -> None:
    """
    Utför ett hugg (närstridsattack).
    
    Användning: !hugg [nivå/område] [skada] [flaggor]
    
    Nivå kan vara: låg, normal, hög
    Område kan vara specifika kroppsdelar: huvud, ansikte, bröstkorg, etc.
    
    Flaggor:
      --mp        - Använd Målpunkter-tekniken (kräver specifikt träffområde)
      --ryttare   - Attacken utförs från en ryttare
      --djur      - Målet är ett fyrbent djur
    
    Exempel:
      !hugg normal 12
      !hugg ansikte 15 --mp
      !hugg hög 10 --ryttare
    """
    await process_melee_command(ctx, "hugg", level_or_location, damage, flags)

@bot.command(name='stick')
async def stick_command(ctx: commands.Context, level_or_location: str, damage: int, *, flags: str = "") -> None:
    """
    Utför ett stick (smalare attack).
    
    Användning: !stick [nivå/område] [skada] [flaggor]
    
    Nivå kan vara: låg, normal, hög
    Område kan vara specifika kroppsdelar: huvud, ansikte, bröstkorg, etc.
    
    Flaggor:
      --mp        - Använd Målpunkter-tekniken (kräver specifikt träffområde)
      --ryttare   - Attacken utförs från en ryttare
      --djur      - Målet är ett fyrbent djur
    
    Exempel:
      !stick normal 12
      !stick hals 15 --mp
      !stick hög 10 --ryttare
    """
    await process_melee_command(ctx, "stick", level_or_location, damage, flags)

@bot.command(name='kross')
async def kross_command(ctx: commands.Context, level_or_location: str, damage: int, *, flags: str = "") -> None:
    """
    Utför en krossattack.
    
    Användning: !kross [nivå/område] [skada] [flaggor]
    
    Nivå kan vara: låg, normal, hög
    Område kan vara specifika kroppsdelar: huvud, ansikte, bröstkorg, etc.
    
    Flaggor:
      --mp        - Använd Målpunkter-tekniken (kräver specifikt träffområde)
      --ryttare   - Attacken utförs från en ryttare
      --djur      - Målet är ett fyrbent djur
    
    Exempel:
      !kross normal 12
      !kross huvud 15 --mp
      !kross låg 10 --ryttare
    """
    await process_melee_command(ctx, "kross", level_or_location, damage, flags)

@bot.command(name='dicehelp')
async def help_command(ctx: commands.Context) -> None:
    """
    Visar hjälpinformation för alla tärningskommandon.
    
    Args:
        ctx (commands.Context): Kontexten för kommandot.
    """
    color: int = color_handler.get_user_color(ctx.author.id)
    embed: discord.Embed = discord.Embed(
        title="🎲 Kullens Tärningsrullare",
        description="För alla dina tärningsbehov. Nästan",
        color=color
    )
    embed.add_field(
        name="Grundläggande Tärningsslag",
        value=(
            "Slå valfritt antal och typ av tärningar med en valfri modifierare:\n"
            "`!roll NdX[+Z]` - Slå N tärningar med X sidor och modifierare Z\n"
            "Exempel: `!roll 3d6+2` - Slår tre 6-sidiga tärningar och lägger till 2\n"
            "\nBegränsningar: Maximalt 100 tärningar och 1000 sidor per tärning"
        ),
        inline=False
    )
    embed.add_field(
        name="Obegränsade Tärningsslag",
        value=(
            "Slå tärningar som 'exploderar' när de visar maxvärde:\n"
            "`!ex NdX[+Z]` - Slå N obegränsade tärningar med X sidor och modifierare Z\n"
            "Exempel: `!ex 4d6-1` - Slår fyra obegränsade 6-sidiga tärningar och subtraherar 1\n"
            "\nNär en tärning visar sitt maxvärde (t.ex. 6 på en T6), får du slå 2 nya tärningar!"
        ),
        inline=False
    )
    embed.add_field(
        name="Räkna Framgångar",
        value=(
            "Räkna tärningsresultat som når eller överskrider ett målvärde:\n"
            "`!count NdX MÅLVÄRDE` - Slå N X-sidiga tärningar och räkna resultat >= MÅLVÄRDE\n"
            "Exempel: `!count 5d10 7` - Slår fem T10 och räknar hur många som visar 7 eller högre\n"
            "\nLyckade slag visas i **fetstil**"
        ),
        inline=False
    )
    embed.add_field(
        name="Färdighetskontroller",
        value=(
            "Slå mot ett målvärde:\n"
            "`!roll NdX[+Z] MÅLVÄRDE` - Vanlig färdighetskontroll\n"
            "`!ex NdX[+Z] MÅLVÄRDE` - Obegränsad färdighetskontroll\n"
            "Exempel: `!roll 4d6+2 24` - Slår 4T6+2 mot målvärde 24\n"
            "\n✅ Lyckat om totalen ≤ målvärdet\n"
            "❌ Misslyckat om totalen > målvärdet\n"
            "Resultatet visar hur mycket du lyckades eller misslyckades med"
        ),
        inline=False
    )
    embed.add_field(
        name="Sessionshantering",
        value=(
            "Spåra tärningsslag under dina spelsessioner:\n"
            "`!startsession [beskrivning]` - Börja spåra en ny session\n"
            "`!endsession` - Avsluta den nuvarande sessionen\n"
            "`!stats` - Visa statistik för den aktuella sessionen\n"
            "`!mystats` - Visa din personliga statistik\n"
            "\nObservera: Start och avslut av sessioner kräver rollen 'Game Master'"
        ),
        inline=False
    )
    embed.add_field(
        name="Hemliga Slag (Endast Spelledare)",
        value=(
            "Gör hemliga slag som endast visar resultaten för dig:\n"
            "`!secret roll NdX[+Z]` - Hemligt vanligt slag\n"
            "`!secret ex NdX[+Z]` - Hemligt obegränsat slag\n"
            "`!secret count NdX MÅLVÄRDE` - Hemligt räkneslag\n"
            "\nResultaten skickas via DM, och en diskret bekräftelse visas i kanalen.\n"
            "Alla hemliga slag loggas för sessionsstatistik."
        ),
        inline=False
    )
    embed.add_field(
        name="Kunskapsbas",
        value=(
            "Sök i rollspelsböckerna efter regler och information:\n"
            "`!ask [din fråga]` - Ställ en fråga till kunskapsbasen\n"
            "Exempel: `!ask Hur fungerar stridskonster i Eon?`\n"
            "\nKunskapsbasen söker i alla dina regelböcker och ger ett koncist svar."
        ),
        inline=False
    )
    await ctx.send(embed=embed)

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
        target: int = int(target_str)
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

        embed: discord.Embed = discord.Embed(
            title=f"{ctx.author.display_name}'s Count Check",
            description=f"**Rolling {num_dice}d{sides}**, counting results >= {target}",
            color=color
        )
        roll_display: str = ", ".join(formatted_rolls)
        embed.add_field(name="Rolls", value=f"[{roll_display}]", inline=False)

        success_text: str = "Success" if successes == 1 else "Successes"
        success_display: str = f"✨ {successes} {success_text}" if successes > 0 else "❌ No successes"
        embed.add_field(name="Results", value=success_display, inline=False)
        


        await ctx.send(embed=embed)
        
        # Om det är Umnatak och han lyckades, lägg eventuellt till en syrlig kommentar
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
        clean_args = clean_arg_string.split() # <--- Här skapar du clean_args
        
        # Debug-utskrift
        if has_demon_inspiration:
            print(f"[DEBUG] Demonisk inspiration aktiverad av {ctx.author.display_name} i !roll {args}")
            try:
                await ctx.author.send(f"🔥 Demonisk inspiration aktiverad")
            except Exception as e:
                print(f"Kunde inte skicka PM: {e}")

        # Använd den rensade argumentlistan för att tolka tärningskommandot
        # FEL FIXAT: Byt ut 'args_copy' mot 'clean_args'
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

        num_dice, sides, modifier = parse_dice_string(dice)
        if num_dice > 100 or sides > 1000:
            await ctx.send("Too many dice or sides!")
            return

        # Om vi har demonisk influens och ett målvärde, se till att "lyckas" oavsett tärningsslag
        should_force_success = has_demon_inspiration and target is not None
        
        color: int = color_handler.get_user_color(ctx.author.id)
        rolls: List[int] = [random.randint(1, sides) for _ in range(num_dice)]
        total: int = sum(rolls) + modifier
        
        # Manipulera resultatet vid demonisk influens
        if should_force_success:
            # Det verkliga tärningskastet sparas för statistik, men vi visar ett riggat resultat
            # Gör så att slaget precis lyckas med 1-3 enheter under målvärdet
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

        embed: discord.Embed = discord.Embed(
            title=f"{ctx.author.display_name}'s Roll",
            description=f"**Rolling {num_dice}d{sides}{'+' + str(modifier) if modifier > 0 else str(modifier) if modifier < 0 else ''}**",
            color=color
        )
        embed.add_field(name="Rolls", value=str(rolls), inline=False)
        if modifier != 0:
            embed.add_field(name="Modifier", value=str(modifier), inline=True)
        embed.add_field(name="Total", value=str(total), inline=True)

        if target is not None:
            difference: int = target - total
            result: str = f"✅ Success! ({difference:+d})" if total <= target else f"❌ Failure ({difference:+d})"
            embed.add_field(name=f"Skill Check (Target: {target})", value=result, inline=False)
            
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
            target = int(target_str)
        else:
            await ctx.send(
                "Använd: `!ex Xd6[+Z]` eller `!ex Xd6[+Z] [Målvärde]`\n"
                "Ex: `!ex 3d6+2`, `!ex 2d6 12`, `!ex 4d6+1 20`"
            )
            return

        num_dice, sides, modifier = parse_dice_string(dice)
        if sides != 6:
            await ctx.send("Det obegränsade T6-slaget (ex) måste vara d6!")
            return
        if num_dice < 1:
            await ctx.send("Du måste slå minst 1 tärning!")
            return
        if num_dice > 100:
            await ctx.send("För många tärningar!")
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

        color: int = color_handler.get_user_color(ctx.author.id)
        embed: discord.Embed = discord.Embed(
            title=f"{ctx.author.display_name}'s Obegränsade T6-slag",
            description=(
                f"**{num_dice}d6{'+' + str(modifier) if modifier > 0 else str(modifier) if modifier < 0 else ''}**\n"
                "(Varje 6 tas bort från summan men genererar +2 nya tärningar)"
            ),
            color=color
        )
        embed.add_field(name="Första kastomgången", value=str(initial_rolls), inline=False)
        embed.add_field(name="Alla kast (inkl. extra)", value=str(all_rolls), inline=False)
        embed.add_field(name="Slutsumma (utan 6:or) + ev. modifierare", value=str(final_total), inline=True)

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
        # Parsa tärningsspecifikationen
        num_dice, sides, modifier = parse_dice_string(dice_spec)
        
        # Kontrollera att det är T6
        if sides != 6:
            await ctx.send("Endast T6 stöds för sannolikhetsberäkning eftersom Eon använder obegränsade T6-slag.")
            return
        
        # Visa att beräkning pågår
        async with ctx.typing():
            # Beräkna sannolikheten för obegränsat slag
            success_rate = simulate_unlimited_dice(num_dice, modifier, target)
            
            # Skapa ett snyggt svar
            color = color_handler.get_user_color(ctx.author.id)
            embed = discord.Embed(
                title="Sannolikhetsberäkning (Obegränsad T6)",
                description=f"Slag: `{dice_spec}` mot målvärde `{target}`",
                color=color
            )
            
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

@bot.command(name='stats')
async def stats_command(ctx: commands.Context, session_id: Optional[str] = None) -> None:
    """
    Visar statistik för den aktiva sessionen eller en specifik session.
    
    Args:
        ctx (commands.Context): Kontexten för kommandot.
        session_id (Optional[str]): ID för den specifika sessionen (om angivet).
    """
    stats: dict = roll_tracker.get_session_stats(session_id)
    if "error" in stats:
        await ctx.send(stats["error"])
        return

    color: int = color_handler.get_user_color(ctx.author.id)
    embed: discord.Embed = discord.Embed(
        title="Session Statistics",
        description=(
            f"Session: {session_id or roll_tracker.current_session}\n"
            f"Total Players: {stats['session_info']['unique_players']}\n"
            f"Total Rolls: {stats['session_info']['total_rolls']}"
        ),
        color=color
    )
    session_info: dict = stats["session_info"]
    embed.add_field(
        name="Session Info",
        value=(
            f"Started: {session_info['start_time']}\n"
            f"{'Ended: ' + session_info['end_time'] if session_info['end_time'] else 'Still active'}\n"
            f"Description: {session_info['description'] or 'No description'}"
        ),
        inline=False
    )

    players_text: str = ""
    for player in stats["player_stats"]:
        players_text += (
            f"**{player['name']}**\n"
            f"Rolls: {player['total_rolls']}"
        )
        if player['successes'] + player['failures'] > 0:
            players_text += f" (Success rate: {player['success_rate']}%)"
        players_text += "\n"
    if players_text:
        embed.add_field(name="Player Statistics", value=players_text, inline=False)

    if stats["command_stats"]:
        cmd_text: str = "\n".join(
            f"{cmd['command']}: {cmd['uses']} uses" +
            (f" ({cmd['success_rate']}% success)" if cmd['success_rate'] is not None else "")
            for cmd in stats["command_stats"]
        )
        embed.add_field(name="Command Usage", value=cmd_text, inline=False)

    if stats["popular_dice"]:
        dice_text: str = "\n".join(
            f"{dice['type']}: {dice['uses']} times"
            for dice in stats["popular_dice"]
        )
        embed.add_field(name="Most Used Dice", value=dice_text, inline=False)

    await ctx.send(embed=embed)

@bot.command(name='mystats')
async def my_stats_command(ctx: commands.Context, session_id: Optional[str] = None) -> None:
    """
    Visar statistik för den aktiva spelaren.
    
    Args:
        ctx (commands.Context): Kontexten för kommandot.
        session_id (Optional[str]): ID för den specifika sessionen (om angivet).
    """
    stats: dict = roll_tracker.get_player_stats(str(ctx.author.id), session_id)
    if "error" in stats:
        await ctx.send(stats["error"])
        return

    color: int = color_handler.get_user_color(ctx.author.id)
    embed: discord.Embed = discord.Embed(
        title=f"Stats for {ctx.author.display_name}",
        description=f"Session: {session_id or roll_tracker.current_session}",
        color=color
    )

    recent_rolls: List[dict] = stats["rolls"][:5]
    if recent_rolls:
        roll_text: str = "\n".join(
            f"{r['command']} {r['dice']}" +
            (f" (Target: {r['target']})" if r['target'] else "") +
            f": {r['values']}" +
            (f" {'✅' if r['success'] else '❌'}" if r['success'] is not None else "")
            for r in recent_rolls
        )
        embed.add_field(name="Recent Rolls", value=roll_text, inline=False)
    else:
        embed.add_field(name="Recent Rolls", value="No rolls yet", inline=False)

    await ctx.send(embed=embed)

@bot.command(name="regel")
async def regel_command(ctx: commands.Context, *args: str) -> None:
    """
    Hanterar regler:
      1. Kör `!regel` för att lista alla regler.
      2. Kör `!regel [namn eller nummer]` för att visa en specifik regel.
    
    Args:
        ctx (commands.Context): Kontexten för kommandot.
        *args (str): Argument för att välja specifik regel (namn eller nummer).
    """
    if not args:
        rules: List[str] = os.listdir(RULES_FOLDER)
        if not rules:
            await ctx.send("Det finns inga regler ännu.")
            return

        response: str = "**Tillgängliga regler:**\n"
        for i, rule_file in enumerate(rules, start=1):
            rule_name: str = os.path.splitext(rule_file)[0]
            response += f"{i}. {rule_name}\n"
        await ctx.send(response)
    else:
        identifier: str = args[0].lower()
        rules: List[str] = os.listdir(RULES_FOLDER)
        try:
            if identifier.isdigit():
                rule_index: int = int(identifier) - 1
                if rule_index < 0 or rule_index >= len(rules):
                    raise IndexError
                rule_file: str = rules[rule_index]
            else:
                rule_file = f"{identifier}.txt"
                if rule_file not in rules:
                    raise FileNotFoundError

            with open(os.path.join(RULES_FOLDER, rule_file), "r", encoding="utf-8") as f:
                content: str = f.read()

            rule_name: str = os.path.splitext(rule_file)[0]
            if len(content) <= 2000:
                await ctx.send(f"**{rule_name}**:\n{content}")
            else:
                chunks: List[str] = [content[i:i+2000] for i in range(0, len(content), 2000)]
                await ctx.send(f"**{rule_name}**: (uppdelat i flera meddelanden)")
                for chunk in chunks:
                    await ctx.send(chunk)
        except (IndexError, FileNotFoundError):
            await ctx.send("Regeln kunde inte hittas. Kontrollera namnet eller numret.")

character_creation.register_commands(bot, roll_tracker, color_handler)

@bot.command(name='höj')
async def improvement_roll_command(ctx: commands.Context, skill_chance: int, *, flags: str = "") -> None:
    """
    Slår ett förbättringsslag för en färdighet i EON.
    
    Efter ett avslutat speltillfälle får spelaren slå Ob3T6 för varje färdighet som har blivit förkryssad.
    Lyckas slaget ökar färdighetschansen ett steg (+1). För lättlärda färdigheter används Ob4T6.
    
    Användning: !höj [färdighetschans] [flaggor]
    
    Flaggor:
      --ll    - Färdigheten är lättlärd (slår Ob4T6 istället för Ob3T6)
    
    Exempel:
      !höj 16         - Förbättringsslag för normal färdighet med värde 16
      !höj 12 --ll    - Förbättringsslag för lättlärd färdighet med värde 12
    """
    try:
        # Kontrollera om färdigheten är lättlärd
        is_easy_learnable = "--ll" in flags.lower()
        
        # Sätt antal tärningar beroende på om färdigheten är lättlärd
        num_dice = 4 if is_easy_learnable else 3
        
        # Slå tärningarna enligt obegränsad regel
        all_rolls, final_total, initial_rolls = unlimited_d6s(num_dice, 0)
        
        # Kontrollera om slaget är lyckat
        success = final_total >= skill_chance
        
        # Förbered resultattexten
        color = color_handler.get_user_color(ctx.author.id)
        embed = discord.Embed(
            title=f"{ctx.author.display_name}s Förbättringsslag",
            description=(
                f"**Ob{num_dice}T6** för {'lättlärd' if is_easy_learnable else 'normal'} färdighet "
                f"med färdighetschans {skill_chance}"
            ),
            color=color
        )
        
        embed.add_field(name="Första kastomgången", value=str(initial_rolls), inline=False)
        embed.add_field(name="Alla kast (inkl. extra)", value=str(all_rolls), inline=False)
        embed.add_field(name="Slutsumma (utan 6:or)", value=str(final_total), inline=True)
        
        if success:
            result_text = "✅ **Lyckat slag!** Färdighetschansen ökar med +1."
            new_skill_chance = skill_chance + 1
            embed.add_field(
                name="Resultat", 
                value=f"{result_text}\nNy färdighetschans: {new_skill_chance}",
                inline=False
            )
        else:
            result_text = "❌ **Misslyckat slag.** Färdighetschansen förblir oförändrad."
            embed.add_field(
                name="Resultat", 
                value=result_text,
                inline=False
            )
            

        # Logga slaget i statistiken
        roll_tracker.log_roll(
            user_id=str(ctx.author.id),
            user_name=ctx.author.display_name,
            command_type='höj',
            num_dice=num_dice,
            sides=6,
            roll_values=all_rolls,
            modifier=0,
            target=skill_chance,
            success=success
        )
            
        await ctx.send(embed=embed)
        
    except ValueError as e:
        await ctx.send(f"Fel: {str(e)}\nAnvändning: `!höj [färdighetschans] [--ll om lättlärd]`")

def main():
    """
    Huvudfunktion som initierar och startar Discord-boten.
    """
    # Kontrollera att tokens finns
    if not DISCORD_TOKEN:
        print("Fel: DISCORD_TOKEN saknas i .env-filen!")
        return
    
    # Skriv ut startinformation
    print(f"Startar Diceroller Bot")
    print(f"Working directory: {os.getcwd()}")
    print(f"Rules folder: {RULES_FOLDER}")
    print(f"Index folder: {INDEX_FOLDER}")
    
    # Visa tillgängliga kanaler
    if CHANNEL_IDS:
        channels = CHANNEL_IDS.split(',')
        print(f"Bot konfigurerad för {len(channels)} kanaler: {', '.join(channels)}")

    # Starta boten
    print(f"Ansluter till Discord...")
    bot.run(DISCORD_TOKEN)

if __name__ == "__main__":
    main()