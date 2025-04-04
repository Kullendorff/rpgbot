import os
import discord
import openai
import faiss
import numpy as np
import tiktoken
import random
from pinecone import Pinecone
from sentence_transformers import SentenceTransformer
import anthropic
from discord.ext import commands
from typing import Tuple, Optional, List, Any
from color_handler import ColorHandler
from roll_tracker import RollTracker
from dotenv import load_dotenv
from combat_manager import CombatManager
from damage_tables import DamageType
from hit_tables import WeaponType  # om du vill ha typ-checking
from fumble_tables import FUMBLE_TABLES, WEAPON_TYPE_ALIASES
from whoosh.index import open_dir
from whoosh.qparser import QueryParser

# Ladda miljövariabler från .env-filen
load_dotenv()

# Hämta Discord-token och kanal-ID:n från miljövariablerna
DISCORD_TOKEN: Optional[str] = os.getenv('DISCORD_TOKEN')
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
CHANNEL_IDS: Optional[str] = os.getenv('CHANNEL_IDS')
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "rpg-knowledge")

print(f"Loaded DISCORD_TOKEN: {'Present' if DISCORD_TOKEN else 'Missing'}")
print(f"Loaded CHANNEL_IDS: {CHANNEL_IDS}")

# Konfigurera Discord-boten med nödvändiga behörigheter
intents: discord.Intents = discord.Intents.default()
intents.message_content = True
bot: commands.Bot = commands.Bot(command_prefix='!', intents=intents)

# client = openai.OpenAI(api_key=OPENAI_API_KEY)

# Initiera hjälputrustning
color_handler: ColorHandler = ColorHandler()
roll_tracker: RollTracker = RollTracker()  # Skapa en instans av RollTracker
combat_manager: CombatManager = CombatManager()

# Konfigurera en undermapp för att lagra regler
RULES_FOLDER: str = "rules"
if not os.path.exists(RULES_FOLDER):
    os.makedirs(RULES_FOLDER)
    
INDEX_FOLDER = "knowledge_index"

pc = None
embedding_model = None
claude_client = None

def initialize_knowledge_base():
    """Initiera kopplingar till kunskapsbasen och AI-tjänsterna."""
    global pc, embedding_model, claude_client
    
    # Kontrollera om API-nycklar finns
    if not PINECONE_API_KEY or not ANTHROPIC_API_KEY:
        print("Varning: PINECONE_API_KEY eller ANTHROPIC_API_KEY saknas. Kunskapsbasfunktionen kommer inte att fungera.")
        return False
    
    try:
        # Initiera Pinecone
        pc = Pinecone(api_key=PINECONE_API_KEY)
        
        # Kontrollera om indexet finns
        if PINECONE_INDEX_NAME not in pc.list_indexes().names():
            print(f"Varning: Pinecone-index '{PINECONE_INDEX_NAME}' hittades inte.")
            return False
        
        # Initiera embedding-modell
        embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
        
        # Initiera Claude API
        claude_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        
        print("Kunskapsbasen har initialiserats framgångsrikt.")
        return True
    except Exception as e:
        print(f"Fel vid initiering av kunskapsbasen: {e}")
        return False

# Funktion för att hämta insikter från kunskapsbasen
def query_knowledge_base(query, top_k=5):
    """
    Hämtar relevanta avsnitt från kunskapsbasen baserat på frågan.
    
    Args:
        query (str): Användarens fråga
        top_k (int): Antal resultat att hämta
        
    Returns:
        tuple: (kontexttext, källreferenser)
    """
    if not pc or not embedding_model or not claude_client:
        return "Kunskapsbasen är inte initialiserad.", []
    
    try:
        # Skapa embedding för frågan
        query_embedding = embedding_model.encode(query).tolist()
        
        # Hämta index
        index = pc.Index(PINECONE_INDEX_NAME)
        
        # Sök efter relevanta avsnitt
        search_results = index.query(
            vector=query_embedding,
            top_k=top_k,
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

# Funktion för att generera svar med Claude
def generate_response(query, context):
    """
    Använder Claude API för att generera ett svar baserat på frågan och kontexten.
    
    Args:
        query (str): Användarens fråga
        context (str): Relevant kontext från kunskapsbasen
        
    Returns:
        str: Claude's svar
    """
    if not claude_client:
        return "Claude API är inte tillgänglig."
    
    try:
        response = claude_client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=1000,
            messages=[
                {
                    "role": "user",
                    "content": f"""
                    Du är en spelledarassistent för rollspel. Din uppgift är att svara på frågor 
                    baserat på rollspelsböckerna.
                    
                    Här är relevant information från rollspelsböckerna:
                    {context}
                    
                    Använd ENDAST den information som tillhandahålls för att svara på denna fråga:
                    {query}
                    
                    Om informationen för att besvara frågan inte finns i det sammanhang som tillhandahålls, 
                    säg bara "Jag har inte den informationen i regelböckerna."
                    
                    Var koncis och korrekt i ditt svar.
                    """
                }
            ]
        )
        
        return response.content[0].text
    except Exception as e:
        print(f"Fel vid användning av Claude API: {e}")
        return f"Ett fel uppstod vid generering av svar: {str(e)}"

# Lägg till detta i on_ready-händelsen för att initiera kunskapsbasen vid start
@bot.event
async def on_ready() -> None:
    """Skriver ut ett meddelande när boten har kopplat upp sig mot Discord."""
    print(f"{bot.user} has connected to Discord!")
    initialize_knowledge_base()  # Initiera kunskapsbasen vid start

# Lägg till detta kommando för att fråga kunskapsbasen
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
        # Hämta relevanta avsnitt från kunskapsbasen
        context, sources = query_knowledge_base(query)
        
        if not context or "Ett fel uppstod" in context:
            await ctx.send(f"Kunde inte söka i kunskapsbasen: {context}")
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


@bot.event
async def on_ready() -> None:
    """Skriver ut ett meddelande när boten har kopplat upp sig mot Discord."""
    print(f"{bot.user} has connected to Discord!")


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
      
def get_embedding(text):
    """Skapar en embedding-vektor för en given text med OpenAIs `text-embedding-ada-002`."""
    response = client.embeddings.create(
        model="text-embedding-ada-002",
        input=text
    )
    return np.array(response.data[0].embedding, dtype=np.float32)

    
def search_knowledge(query):
    """Söker i den indexerade kunskapsbasen och returnerar de bästa resultaten"""
    index = open_dir(INDEX_FOLDER)
    with index.searcher() as searcher:
        parser = QueryParser("content", index.schema)
        query = parser.parse(query)
        results = searcher.search(query, limit=3)  # Begränsa till max 3 träffar

        found_texts = []
        for result in results:
            found_texts.append(f"**{result['title']}**:\n{result['content'][:500]}...")  # Första 500 tecken

        return "\n\n".join(found_texts) if found_texts else None


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
    Avslutar den aktiva spelsessionen.
    
    Args:
        ctx (commands.Context): Kontexten för kommandot.
    """
    roll_tracker.end_session()
    await ctx.send("Game session ended.")


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
        flags (str): Eventuella ytterligare flaggor (exempelvis '--ryttare', '--djur').
    """
    try:
        result: Any = combat_manager.process_attack(
            weapon_type=weapon,
            attack_level=level_or_location if level_or_location.lower() in ["låg", "normal", "hög"] else None,
            damage_value=damage,
            location_override=None if level_or_location.lower() in ["låg", "normal", "hög"] else level_or_location.lower(),
            is_mounted="--ryttare" in flags.lower(),
            is_quadruped="--djur" in flags.lower(),
            direction=None
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
    
    Args:
        ctx (commands.Context): Kontexten för kommandot.
        level_or_location (str): Nivå eller specifikt träffområde.
        damage (int): Angivet skadevärde.
        flags (str, optional): Ytterligare flaggor, t.ex. '--ryttare' eller '--djur'.
    """
    await process_melee_command(ctx, "hugg", level_or_location, damage, flags)


@bot.command(name='stick')
async def stick_command(ctx: commands.Context, level_or_location: str, damage: int, *, flags: str = "") -> None:
    """
    Utför ett stick (smalare attack).
    
    Args:
        ctx (commands.Context): Kontexten för kommandot.
        level_or_location (str): Nivå eller specifikt träffområde.
        damage (int): Angivet skadevärde.
        flags (str, optional): Ytterligare flaggor.
    """
    await process_melee_command(ctx, "stick", level_or_location, damage, flags)


@bot.command(name='kross')
async def kross_command(ctx: commands.Context, level_or_location: str, damage: int, *, flags: str = "") -> None:
    """
    Utför en krossattack.
    
    Args:
        ctx (commands.Context): Kontexten för kommandot.
        level_or_location (str): Nivå eller specifikt träffområde.
        damage (int): Angivet skadevärde.
        flags (str, optional): Ytterligare flaggor.
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
            "\nWhen a die shows its maximum value (e.g., 6 on a d6), you get to roll 2 more dice!"
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
            # OBS: exploding_replace_max måste finnas definierad (antagligen i combat_manager eller en annan modul)
            all_rolls, final_total = exploding_replace_max(num_dice, sides, modifier)

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
        if len(args) == 1:
            dice: str = args[0]
            target: Optional[int] = None
        elif len(args) == 2:
            dice, target_str = args
            target = int(target_str)
        else:
            await ctx.send("Use format: `!roll YdX[+Z]` or `!roll YdX[+Z] TARGET` (e.g. `!roll 2d6+1` or `!roll 4d6-2 24`)")
            return

        num_dice, sides, modifier = parse_dice_string(dice)
        if num_dice > 100 or sides > 1000:
            await ctx.send("Too many dice or sides!")
            return

        color: int = color_handler.get_user_color(ctx.author.id)
        rolls: List[int] = [random.randint(1, sides) for _ in range(num_dice)]
        total: int = sum(rolls) + modifier

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
    
    Args:
        ctx (commands.Context): Kontexten för kommandot.
        *args: Kommandots argument.
    """
    try:
        if len(args) == 1:
            dice: str = args[0]
            target: Optional[int] = None
        elif len(args) == 2:
            dice, target_str = args
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

        await ctx.send(embed=embed)

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

    # Utför expansionskast
    while extra_dice > 0:
        roll: int = random.randint(1, 6)
        all_rolls.append(roll)
        extra_dice -= 1
        if roll == 6:
            extra_dice += 2
        else:
            final_total += roll

    final_total += modifier
    return all_rolls, final_total, initial_rolls


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

def split_message(message, max_length=2000):
    """Dela upp ett långt meddelande i mindre delar."""
    return [message[i:i+max_length] for i in range(0, len(message), max_length)]

import tiktoken  # Används för att beräkna tokens

def count_tokens(text):
    """Räknar antal tokens i en given text med GPT-4:s tokenräknare."""
    encoder = tiktoken.encoding_for_model("gpt-4")
    return len(encoder.encode(text))

import tiktoken
from fuzzywuzzy import process  # För fuzzy matchning

def count_tokens(text):
    """Räknar antal tokens i en given text med GPT-4:s tokenräknare."""
    encoder = tiktoken.encoding_for_model("gpt-4")
    return len(encoder.encode(text))

import faiss
import numpy as np

def get_embedding(text):
    """Skapar en embedding-vektor för en given text (text-embedding-ada-002)."""
    response = openai.Embedding.create(
        model="text-embedding-ada-002",
        input=text
    )
    return np.array(response.data[0].embedding, dtype=np.float32)

def search_faiss(query, top_k=10):
    """Hitta de mest relevanta avsnitten baserat på FAISS-embeddings."""
    index = faiss.read_index("knowledge_index.faiss")
    texts = np.load("knowledge_texts.npy", allow_pickle=True)

    # Skapa en embedding för frågan
    query_embedding = get_embedding(query).reshape(1, -1)

    # Hitta de närmaste matchningarna
    distances, indices = index.search(query_embedding, top_k)

    results = []
    used_indices = set()

    for i in indices[0]:
        if i < len(texts) and i not in used_indices:
            results.append(texts[i])
            used_indices.add(i)

    return results  # Returnerar en lista av chunk-strängar


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


if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
