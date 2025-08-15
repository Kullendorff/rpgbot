# Claude Code Instruktioner - EON Diceroller Interaktivt Karaktärsskapande

## Projektöversikt
Implementera ett komplett steg-för-steg interaktivt karaktärsskapande-system för EON Diceroller Bot som vägleder användare genom alla 33 steg av EON:s rollpersonsskapande-process.

## Aktuell Status
- ✅ **Grundläggande kommandon:** `!attribut`, `!folkslag`, `!egenskap`, `!bakgrund`, `!npc`
- ✅ **Automatisk familjebakgrund:** `!familjebakgrund` - komplett implementation klar
- ✅ **EON TableProcessor:** Avancerad tabellhantering med conditional logic (eon_table_processor.py)
- ❌ **Session management:** Saknas helt
- ❌ **Steg-för-steg process:** Behöver implementeras

## Mål: Implementera Session-Baserat Karaktärsskapande

### 1. Integrera EON TableProcessor

**Befintlig fil:** `src/eon_table_processor.py` (redan skriven)

Den här klassen hanterar alla komplexa tabellslag med:
- **Conditional logic:** Olika resultat baserat på folkslag/kultur/social_class
- **Hierarkiska tabeller:** huvudbakgrund → specifika tabeller automatiskt
- **Subtables:** Nested tabeller med egna ranges
- **Benefits parsing:** Extraherar färdigheter, attributbonusar, pengar automatiskt
- **Auto-resolution:** Följer cross-references mellan tabeller

**Integration i session-systemet:**

```python
# I InteractiveCharacterCreator.__init__()
from eon_table_processor import TableProcessor, CharacterContext, create_character_context

class InteractiveCharacterCreator:
    def __init__(self):
        self.active_sessions = {}
        self.steps = self._define_steps()
        self.table_processor = TableProcessor()  # <-- Lägg till detta
        self.bg_generator = AutomaticBackgroundGenerator()
```

### 2. Skapa Session Management System

**Fil:** `src/interactive_chargen.py`

```python
from eon_table_processor import TableProcessor, CharacterContext, create_character_context

class CharacterSession:
    """Hanterar en pågående karaktärsskapande-session för en användare"""
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.current_step = 1
        self.max_steps = 33
        self.data = {}
        self.context = CharacterContext()  # <-- För tabellhantering
        self.created_at = datetime.now()
    
    def update_context(self):
        """Uppdaterar context baserat på nuvarande data"""
        if 'folkslag' in self.data:
            self.context = create_character_context(
                folkslag=self.data['folkslag'],
                kultur=self.data.get('kultur'),
                social_class=self.data.get('social_class')
            )
    
    def save_to_file(self):
        """Sparar session till JSON-fil"""
        # Implementation för persistens
    
    @classmethod
    def load_from_file(cls, user_id: str):
        """Laddar sparad session från fil"""
        # Implementation för att ladda session

class InteractiveCharacterCreator:
    """Huvudklass för interaktivt karaktärsskapande"""
    def __init__(self):
        self.active_sessions = {}  # user_id -> CharacterSession
        self.table_processor = TableProcessor()  # <-- Tabellhantering
        self.bg_generator = AutomaticBackgroundGenerator()  # <-- Familjebakgrund
        self.steps = self._define_steps()
    
    def _define_steps(self):
        """Definierar alla 33 steg i ordning"""
        return [
            {"id": 1, "name": "kön", "handler": self.step_gender},
            {"id": 2, "name": "hemland", "handler": self.step_homeland}, 
            {"id": 3, "name": "folkslag", "handler": self.step_race},
            {"id": 4, "name": "ålder", "handler": self.step_age},
            {"id": 5, "name": "religion", "handler": self.step_religion},
            {"id": 6, "name": "kultur", "handler": self.step_culture},
            {"id": 7, "name": "attribut", "handler": self.step_attributes},
            {"id": 8, "name": "specialregler", "handler": self.step_special_rules},
            {"id": 9, "name": "karaktärsdrag", "handler": self.step_character_traits},
            # FAMILJ KOMMER FÖRE BAKGRUND I EON
            {"id": 10, "name": "familjebakgrund", "handler": self.step_family_background},
            {"id": 11, "name": "familjetabeller", "handler": self.step_family_tables}, 
            {"id": 12, "name": "föräldrar", "handler": self.step_parents},
            # BAKGRUNDSLAG EFTER FAMILJ
            {"id": 13, "name": "bakgrundslag_antal", "handler": self.step_background_count},
            {"id": 14, "name": "huvudbakgrund", "handler": self.step_main_background},
            {"id": 15, "name": "bakgrundshändelser", "handler": self.step_background_events},
            # ... resterande steg 16-33
        ]
```

### 2. Implementera Grundläggande Session-Kommandon

**Registrera i:** `src/character_creation.py`

```python
@bot.command(name='chargen')
async def chargen_command(ctx: commands.Context, action: str = None, *args):
    """Huvudkommando för interaktivt karaktärsskapande"""
    
    if action == "start":
        # Starta ny session
        session = chargen.start_session(ctx.author.id)
        await chargen.show_current_step(ctx, session)
    
    elif action == "status":
        # Visa nuvarande progress
        session = chargen.get_session(ctx.author.id)
        if session:
            await chargen.show_status(ctx, session)
        else:
            await ctx.send("Du har ingen aktiv karaktärsskapande-session. Använd `!chargen start`")
    
    elif action == "step":
        # Gå till nästa steg
        session = chargen.get_session(ctx.author.id)
        if session:
            await chargen.next_step(ctx, session)
        else:
            await ctx.send("Ingen aktiv session.")
    
    elif action == "back":
        # Gå tillbaka ett steg
        session = chargen.get_session(ctx.author.id)
        if session:
            await chargen.previous_step(ctx, session)
        else:
            await ctx.send("Ingen aktiv session.")
    
    elif action == "abort":
        # Avbryt session
        chargen.end_session(ctx.author.id)
        await ctx.send("Karaktärsskapande avbrutet.")
    
    else:
        # Tolka som input för nuvarande steg
        session = chargen.get_session(ctx.author.id)
        if session:
            await chargen.handle_step_input(ctx, session, action, *args)
        else:
            await ctx.send("Använd `!chargen start` för att börja skapa en rollperson.")
```

### 3. Implementera Steg-Hanterare

### 5. Grundläggande Steg-Hanterare

**Exempel för steg 1-4:**

```python
async def step_gender(self, ctx, session):
    """Steg 1: Välj kön"""
    embed = discord.Embed(
        title="🎭 Steg 1/33: Kön",
        description="Välj rollpersonens kön:",
        color=0x00ff00
    )
    embed.add_field(name="Val", value="1. Kvinna\n2. Man", inline=False)
    embed.set_footer(text="Skriv: !chargen 1 eller !chargen kvinna")
    await ctx.send(embed=embed)

async def step_homeland(self, ctx, session):
    """Steg 2: Välj hemland"""
    # Ladda från befintliga hemlands-filer
    embed = discord.Embed(
        title="🏰 Steg 2/33: Hemland", 
        description="Välj rollpersonens hemland (1-37 eller namn):",
        color=0x00ff00
    )
    # Lista första 10 länder, visa att det finns fler
    embed.add_field(name="Exempel", value="1. Adasien\n2. Alarinn\n3. Alkarlen\n...", inline=False)
    embed.set_footer(text="Skriv: !chargen lista för alla länder, eller !chargen [nummer/namn]")
    await ctx.send(embed=embed)

async def step_race(self, ctx, session):
    """Steg 3: Välj folkslag"""
    # Använd befintlig folkslag-logik från character_creation.py
    # Men integrera i session-systemet

async def step_family_background(self, ctx, session):
    """Steg 10: Familjebakgrund - Använd befintlig implementation FÖRE bakgrundslag"""
    race = session.data.get('folkslag')
    age = session.data.get('ålder')
    
    if not race or not age:
        await ctx.send("❌ Fel: Folkslag och ålder måste vara satta först.")
        return
    
    # Använd den befintliga AutomaticBackgroundGenerator
    background = self.bg_generator.generate_complete_background(race, age)
    summary = self.bg_generator.format_background_summary(background)
    
    embed = discord.Embed(
        title=f"👨‍👩‍👧‍👦 Steg 10/33: Familjebakgrund (Före bakgrundslag)",
        description=summary,
        color=0x00ff00
    )
    embed.set_footer(text="Skriv: !chargen behåll eller !chargen nytt")
    await ctx.send(embed=embed)
    
    # Spara temporärt tills användaren bekräftar
    session.temp_data = {'familjebakgrund': background}

async def step_main_background(self, ctx, session):
    """Steg 14: Huvudbakgrundstabellen - EFTER familj är klar"""
    
    # Beräkna antal bakgrundslag baserat på ålder och attributsumma
    num_rolls = self._calculate_background_rolls(session)
    
    embed = discord.Embed(
        title=f"🎲 Steg 14/33: Huvudbakgrundstabellen ({num_rolls} slag)",
        description=f"Nu slår vi bakgrundshändelser (familjen är redan klar)...",
        color=0x00ff00
    )
    
    # Information om familjen som redan är satt
    if 'familjebakgrund' in session.data:
        embed.add_field(
            name="✅ Familj (redan fastställd)",
            value="Familjebakgrund fastställd i steg 10-12",
            inline=False
        )
    
    await ctx.send(embed=embed)
    
    # Fortsätt med bakgrundshändelser...
```

### 6. TableProcessor Integration Benefits

**Fördelar med att använda TableProcessor:**

1. **Intelligent Cross-References:**
   ```python
   # Istället för manuell mappning:
   if result == "mentala_egenskaper":
       roll_on_mental_traits_table()
   
   # TableProcessor gör detta automatiskt:
   result = table_processor.roll_with_auto_resolution(
       'huvudbakgrund', context=session.context, auto_resolve_depth=2
   )
   ```

2. **Conditional Logic:**
   ```python
   # Automatisk hantering av folkslag-specifika regler:
   # - Alver får andra händelser än människor
   # - Riddare får andra börd-resultat än bönder
   # - Primitiva kulturer vs civiliserade kulturer
   ```

3. **Benefit Extraction:**
   ```python
   # Automatisk parsning av färdighetsbonus från beskrivningar:
   # "Du får 1T6+4 enheter att spendera på färdigheten etikett"
   # → Benefit(type='skill', target='etikett', value='1T6+4')
   ```

4. **Error Handling:**
   ```python
   # Robust hantering av:
   # - Felaktiga tabellreferenser
   # - Saknade conditional branches  
   # - Tärningsnotation (både d6 och T6 format)
   ```

### 4. Integrera med Befintlig Familjebakgrund

**Modifiera:** `src/automatic_background.py`

Lägg till metod för integration:

```python
def integrate_with_session(self, session_data: Dict[str, Any]) -> FamilyBackground:
    """Integrerar med session-data för konsekvent karaktärsskapande"""
    race = session_data.get('folkslag', 'vanarer')
    age = session_data.get('ålder', 25)
    
    # Eventuell framtida integration med andra session-data
    # t.ex. religion, kultur, etc.
    
    return self.generate_complete_background(race, age)
```

### 7. Session Persistens och TableProcessor

**Skapa:** `data/character_tables/sessions/` mapp

```python
def save_session(self, session: CharacterSession):
    """Sparar session till JSON-fil"""
    session_dir = os.path.join(self.data_dir, 'sessions')
    os.makedirs(session_dir, exist_ok=True)
    
    filepath = os.path.join(session_dir, f"{session.user_id}.json")
    session_data = {
        'user_id': session.user_id,
        'current_step': session.current_step,
        'data': session.data,
        'created_at': session.created_at.isoformat()
    }
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(session_data, f, ensure_ascii=False, indent=2)

def load_session(self, user_id: str) -> Optional[CharacterSession]:
    """Laddar sparad session"""
    filepath = os.path.join(self.data_dir, 'sessions', f"{user_id}.json")
    
    if not os.path.exists(filepath):
        return None
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        session = CharacterSession(user_id)
        session.current_step = data['current_step']
        session.data = data['data']
        session.created_at = datetime.fromisoformat(data['created_at'])
        
        return session
    except Exception as e:
        print(f"Fel vid laddning av session för {user_id}: {e}")
        return None
```

## Implementationsordning

### Fas 1: Grundläggande Session System + TableProcessor (Prioritet 1)
1. **Verifiera `eon_table_processor.py`** fungerar korrekt
2. **Skapa `interactive_chargen.py`** med session-klasser + TableProcessor integration
3. **Implementera `!chargen start/status/abort`** kommandon
4. **Implementera steg 1-4** (kön, hemland, folkslag, ålder) + context-uppdatering
5. **Session persistens** (spara/ladda från JSON)

### Fas 2: Avancerad Tabellhantering (Prioritet 2)
1. **Implementera steg 10-11** (bakgrundshändelser med auto-resolution)
2. **Integrera familjebakgrund** som steg 12 
3. **Lägg till benefit processing** (automatisk färdighets/attributhantering)
4. **Testa TableProcessor** med riktiga EON-tabeller

### Fas 3: Komplett System (Prioritet 3)
1. **Lägg till steg 5-9** (religion, attribut, specialregler)
2. **Lägg till steg 13-33** (yrke, färdigheter, utrustning)
3. **Export till färdig karaktär** med alla benefits summerade
4. **Optimering och buggfixar**

## Testning

### Manuell testning med TableProcessor:
```
!chargen start
!chargen kvinna
!chargen soldarn  
!chargen vanarer
!chargen 25
# ... (hoppa till steg 10-11)
!chargen step (flera gånger tills steg 10)
# Bakgrundshändelser genereras automatiskt med auto-resolution
# "mentala_egenskaper" → rullar automatiskt på mental_traits tabellen
# "händelser" → rullar automatiskt på rätt händelsetabell för folkslag
!chargen behåll
!chargen step  # Steg 12: Familjebakgrund genereras
!chargen status  # Visa all data inklusive benefits
```

### Automated tests med TableProcessor:
```python
def test_table_processor_integration():
    creator = InteractiveCharacterCreator()
    session = creator.start_session("test_user")
    session.data = {'folkslag': 'alv', 'ålder': 150, 'kultur': 'civiliserad'}
    session.update_context()
    
    # Test att TableProcessor använder rätt händelsetabell för alver
    result = creator.table_processor.roll_with_auto_resolution(
        'huvudbakgrund', context=session.context
    )
    assert result.source_table == 'huvudbakgrund'
    # Test auto-resolution fungerar

def test_benefit_extraction():
    processor = TableProcessor()
    result = processor.roll_on_table('mental_traits')
    # Test att benefits extraheras korrekt från beskrivningar
```

## Förväntade Utmaningar

### 1. State Management med TableProcessor
- **Problem:** Sessions kan gå förlorade vid bot-restart
- **Lösning:** Automatisk sparning efter varje steg + loading vid bot-start
- **TableProcessor integration:** Context sparas som del av session

### 2. Komplex Tabellhantering
- **Problem:** EON har komplexa conditional rules och cross-references
- **Lösning:** ✅ TableProcessor hanterar detta automatiskt med auto-resolution
- **Fördel:** Mindre kod, färre buggar, följer EON-regler exakt

### 3. Benefit Tracking  
- **Problem:** Bakgrundshändelser ger färdigheter/attributbonusar som måste spåras
- **Lösning:** ✅ TableProcessor extraherar benefits automatiskt från beskrivningar
- **Resultat:** Session håller automatiskt koll på alla bonusar

## Slutresultat

När implementationen är klar ska användare kunna:

```
!chargen start           # Starta ny rollperson
# Guidat genom alla 33 steg med intelligent tabellhantering
!chargen status         # Se progress + alla benefits (Steg 15/33: Yrke)
!chargen back           # Ångra senaste val
!chargen export         # Få färdig karaktär som JSON/text med alla bonusar summerade
```

**TableProcessor** ger systemet kraftfull tabellhantering som:
- Automatiskt följer EON:s komplexa regler och cross-references
- Extraherar färdigheter och attributbonusar från bakgrundshändelser  
- Hanterar folkslag-specifika tabeller (alver vs människor vs tiraker)
- Gör conditional logic transparent och robust

**Familjebakgrunden** integreras smidig som steg 12 och ger samma rika, automatiskt genererade berättelser som den nuvarande `!familjebakgrund` kommandot, men inom ramen för en strukturerad karaktärsskapande-process.

---

**Start med Fas 1** för att få grundläggande session-hantering + TableProcessor integration på plats, sedan bygg ut steg för steg med befintlig funktionalitet som bas. TableProcessor:n ger dig en kraftfull grund för att hantera alla EON:s komplexa tabellregler automatiskt.