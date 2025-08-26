# EON Discord Bot - Slash Command Konvertering
## Del 2: Knowledge, Combat & Utility Commands

---

## 📋 Förutsättningar

**Innan du börjar Del 2:**
- ✅ Del 1 är komplett och testad
- ✅ Dice commands fungerar som slash
- ✅ Migration helper är etablerad
- ✅ Feature flags är konfigurerade
- ✅ **Embed factory är implementerad och används**
- ✅ Minst 24 timmars test av Del 1

---

## 🧠 Knowledge Commands (AI-integrerade)

### Kritisk Förståelse

**VARNING:** Dessa kommandon använder Claude API som kan ta 5-30 sekunder!

**Discord's timeout-regler:**
- Initial response: 3 sekunder MAX
- Efter defer(): 15 minuter
- Efter första followup: Obegränsat

**Konsekvens:** ALLA knowledge commands MÅSTE använda defer() OMEDELBART

### Implementation Instructions

#### 3.1 Analysera befintliga knowledge commands

**Studera `src/commands/knowledge_commands.py`:**
- Hur fungerar `query_knowledge_base()`?
- Vilka källor används?
- Hur formateras AI-svar?
- Finns det caching?

#### 3.2 Skapa timeout handler

**Ny fil: `src/utils/ai_handler.py`**

Implementera intelligent timeout-hantering som:
1. **Alltid använder defer()** för AI operations
2. **Ger progress feedback** efter 5 sekunder
3. **Hanterar timeout gracefully** med användarvänligt meddelande
4. **Cachar vanliga frågor** för snabbare svar

#### 3.3 Konvertera knowledge commands

**För `/ask` kommandot:**

Parameter ändringar:
- `query: str` - Användarens fråga
- `detailed: Optional[bool]` - Nytt! Låt användare välja detaljnivå

Embed creation:
- **ANVÄND:** `embed_factory.knowledge_result()`
- **ALDRIG:** Skapa `discord.Embed()` direkt
- Hantera långa svar genom att dela upp i flera embeds om nödvändigt

Förbättringar att implementera:
- **Response caching:** Spara svar i 1 timme för identiska frågor
- **Progress indicator:** Visa "bearbetar..." efter 5 sekunder
- **Split long responses:** Discord embeds har 4096 char limit
- **Source attribution:** Visa vilka dokument som användes

Kritiska krav:
- **MÅSTE använda defer() direkt**
- **Timeout efter 45 sekunder** med tydligt felmeddelande
- **Logga alla långsamma queries** (>10 sekunder)
- **Använd embed_factory.error_message()** för fel

**För `/sök` kommandot:**

Parameter ändringar:
- `query: str` - Sökterm
- `source: Optional[str]` - Filtrera på källa
- `max_results: Range[int, 1, 20]` - Begränsa resultat

Detta är snabbare - defer() behövs bara om >100 resultat

**För `/allt` kommandot:**

- Omfattande sökning som kan vara långsam
- Använd defer() för säkerhet
- Överväg att dela upp i flera embeds

#### 3.4 Performance optimering

**Implementera följande:**
1. **Query caching** - Samma fråga inom 1h = instant svar
2. **Preload common queries** - Ladda vanliga frågor vid start
3. **Parallel processing** - Sök flera källor samtidigt
4. **Result pagination** - Dela långa svar i flera meddelanden

---

## ⚔️ Combat Commands

### Kritisk Förståelse

**Huvudutmaning:** Konvertera string flags till boolean parameters

**Nuvarande:** `!hugg normal 12 --ryttare --djur`
**Ny:** `/hugg level:normal damage:12 mounted:true quadruped:true`

### Implementation Instructions

#### 4.1 Analysera combat system

**Studera `src/commands/combat_commands.py`:**
- Vilka träfftabeller används?
- Hur fungerar `process_attack()`?
- Vilka modifierare finns?
- Hur formateras resultat?

#### 4.2 Parameter mapping strategi

**För ALLA combat commands (hugg, stick, kross):**

Gamla parametrar:
- `level_or_location: str` - Kan vara "normal" eller "huvud"
- `damage: int` - Skadetal
- `flags: str` - Parsas för --ryttare, --djur, etc.

Nya parametrar:
- `level: str` - Använd Choices för valid options
- `damage: Range[int, 1, 100]` - Validera automatiskt
- `mounted: Optional[bool] = False` - Ersätter --ryttare
- `quadruped: Optional[bool] = False` - Ersätter --djur

Embed creation:
- **ANVÄND:** `embed_factory.combat_result()`
- **ALDRIG:** Bygg combat embeds manuellt
- Skicka weapon type, rolls, och special effects till factory

**Använd app_commands.choices() för level:**
```
Låg nivå → "låg"
Normal nivå → "normal"  
Hög nivå → "hög"
Huvud → "huvud"
Arm → "arm"
Ben → "ben"
Torso → "torso"
```

#### 4.3 Implementera fummel command

**För `/fummel` kommandot:**

- Använd Choices för weapon_type
- Inkludera ALLA vapenkategorier från fummel-tabellerna
- Visa tydligt resultat med konsekvenser

#### 4.4 State management

**Problem:** Combat kan involvera flera commands i rad

**Lösning att implementera:**
1. Skapa temporary combat sessions (5 min timeout)
2. Spara state mellan commands för samma användare
3. Tillåt "undo" av senaste slaget
4. Visa combat historik på begäran

---

## 🛠️ Utility Commands

### Implementation Instructions

#### 5.1 Help command transformation

**För `/help` kommandot:**

Förbättringar:
- **Kategoriserad hjälp:** Gruppera commands
- **Interactive:** Använd Discord buttons för navigation
- **Context-aware:** Visa endast commands användaren kan köra
- **Examples:** Inkludera exempel för varje command

Implementation:
1. Använd `embed_factory.admin_message()` för huvudsidan
2. Använd konsekvent embed style för alla hjälpsidor
3. Lägg till buttons för varje kategori
4. Visa detaljerad hjälp vid button click

#### 5.2 Stats commands

**För `/stats` och `/mystats`:**

Embed creation:
- **ANVÄND:** `embed_factory.stats_overview()`
- Skicka all statistikdata som dictionary
- Factory hanterar formatering och layout

Förbättringar:
- **Visualisering:** Använd progress bars
- **Jämförelser:** Visa hur du ligger till vs genomsnitt
- **Tidsperioder:** Låt användare välja dag/vecka/månad
- **Export:** Erbjud CSV/JSON export

Parameters:
- `period: Choices["day", "week", "month", "all"]`
- `detailed: Optional[bool]`

#### 5.3 Regel command

**För `/regel` kommandot:**

- Använd autocomplete för regel-namn
- Visa relaterade regler
- Länka till relevanta commands
- Cachea regel-innehåll

#### 5.4 Höj command

**För `/höj` kommandot:**

Parameters:
- `current_skill: Range[int, 1, 30]`
- `advancement_points: Optional[int]`

Visa:
- Kostnad för höjning
- Nya färdighetsvärdet
- Rekommenderade tärningar

---

## 🧪 Testprotokoll Del 2

### Knowledge Commands:
- [ ] `/ask` svarar inom 45 sekunder även för komplexa frågor
- [ ] Caching fungerar för identiska queries
- [ ] Progress indicator visas efter 5 sekunder
- [ ] Långa svar delas upp korrekt
- [ ] Källor visas när tillgängliga

### Combat Commands:
- [ ] Alla attack-typer fungerar med choices
- [ ] Boolean flags ersätter string flags korrekt
- [ ] Fummel-tabeller visas rätt
- [ ] Resultat formateras identiskt med prefix version
- [ ] Damage ranges valideras

### Utility Commands:
- [ ] `/help` är interaktiv med buttons
- [ ] Stats visar korrekt data
- [ ] Regel autocomplete fungerar
- [ ] Alla utilities ger värdefull information

### Performance:
- [ ] Knowledge commands timeout aldrig
- [ ] Combat commands svarar instant
- [ ] Stats kan vara långsam men använder defer()
- [ ] Ingen command tar >45 sekunder totalt

---

## 🔍 Debugging Tips

### För timeout issues:
1. Kontrollera att defer() körs FÖRST i funktionen
2. Använd followup.send() inte response.send_message() efter defer
3. Logga execution time för alla operations
4. Implementera circuit breaker för AI calls

### För parameter issues:
1. Verifiera Range validators är rimliga
2. Testa edge cases (0, negativa, enorma värden)
3. Kontrollera Optional parameters har defaults
4. Validera Choices matchar exakt förväntade värden

### För state issues:
1. Använd interaction.user.id som session key
2. Implementera timeout för gamla sessions
3. Rensa state vid error
4. Logga alla state changes

---

## 📈 Förväntade Resultat

Efter Del 2 implementation:
- **80% färre timeouts** tack vare proper defer() usage
- **2x snabbare knowledge svar** via caching
- **Enklare combat input** med choices och booleans
- **Bättre hjälpsystem** med interaktiv navigation

---

## ⚡ Optimeringstips

1. **Precompile regex patterns** för sökning
2. **Connection pooling** för databas/API
3. **Lazy load** stora datamängder
4. **Background tasks** för maintenance
5. **Rate limiting** för att undvika API throttling

---

## Nästa Steg

När Del 2 är testad och stabil:
1. Kör full regression test av Del 1 + 2
2. Låt fler användare testa i staging
3. Samla metrics på performance
4. Fortsätt till Del 3 (Admin & Finalization)