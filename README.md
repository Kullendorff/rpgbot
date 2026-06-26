# EON Diceroller Bot 🎲

En avancerad Discord-bot för tärningskast och kunskapshantering för det svenska rollspelet EON, med stöd för "Skjut Dem I Huvudet".

## ✨ Huvudfunktioner

### 🎯 Tärningskast & Statistik
- **Moderna slash commands**: `/roll tärningar:3d6+2`, `/roll tärningar:3D6+2 mål:15` - flexibla format!
- **Obegränsade T6-slag**: `/ex antal:5 mål:12` för EON:s exploderande tärningar
- **Räkna framgångar**: `/count tärningar:5d10 mål:7` räknar resultat ≥ målvärde
- **Sannolikhetsberäkning**: `/chance antal:3 target:15` - EON-korrekt med exploderande d6:or
- **Hemliga slag**: `/secret roll tärningar:2d6` endast synligt för spelledaren
- **Detaljerad statistik**: `/stats`, `/mystats` spårar alla slag

### 🧠 AI-driven Kunskapsbas
- **Intelligent sökning**: `/ask fråga:"Vad är Ferox?"` - AI-assisterad regelfrågor
- **Snabbsökning**: `/sök term:ferox` för direkta sökresultat  
- **Omfattande sökning**: `/allt term:ferox` genomsöker hela regelbiblioteket
- **Regelreferenser**: `/regel namn:strid` för snabba regeluppslag

### ⚔️ Stridsystem
- **Attacksimuleringar**: `/hugg`, `/stick`, `/kross` med realistiska skadeberäkningar
- **Fummeltabeller**: `/fummel` för kritiska misslyckanden
- **Vapenskaderegler**: Automatisk hantering av olika vapentypers skador

### 🎭 Karaktärsskapande & Session
- **Komplett EON karaktärsskapande**: `!chargen` - 32 steg med automatisk tabellhantering
- **Thalamur-specialsystem**: Ätter, medborgarätt och strategisk bakgrundsplacering
- **Sessionshantering**: `/startsession namn:"Äventyr i Trinsmyra"` och `/endsession`
- **AI-sammanfattningar**: Automatiska humoristiska sessionssammanfattningar via Claude AI
- **Personaliserade kommentarer**: `/kommentarer` - SL kan aktivera anpassade kommentarer för spelares tärningsslag

### 🐉 Dragonbane (Drakar och Demoner)
- **Tärningsslag**: `/dod_slag expression:2T6+1T8+3`
- **Färdighetsslag**: `/dod_fv skill:13 modifier:2 mode:fördel` (slag <= FV lyckas, 1 = drakslag, 20 = demonslag)
- **Pressa slag**: `/dod_pressa skill:13 grundegenskap:STY`, eller knappen "Pressa slag" under ett misslyckat slag
- **Skada**: `/dod_skada dice:1T10 bonus:2`
- **Initiativ**: `/dod_init characters:Björn,Saga,Ragna` (kortlek 1-10, lägst agerar först)

> **Dragonbane-modulen är byggd av Jonas** (https://github.com/jonsal/dragonbane). Den ursprungliga koden anpassades till botens arkitektur (Cog + embed_factory) och regelrättades: initiativ dras som kortlek (unika 1-10, lägst först) och tillstånd kan bindas till grundegenskap. Krediten visas även i sidfoten på varje Dragonbane-resultat i Discord. Heder och tack till Jonas.

## 🏗️ Arkitektur (Modulär Design)

```
src/
├── main.py                 # Bot entry point (200 rader, ner från 1300+)
├── commands/               # Kommandomoduler
│   ├── dice_commands.py    # Tärningskommandon (roll, ex, count, chance)
│   ├── admin_commands.py   # Admin/GM kommandon (secret, session)
│   ├── knowledge_commands.py # AI kunskapskommandon (ask, sök, allt)
│   ├── combat_commands.py  # Stridskommandon (hugg, stick, kross)
│   └── utility_commands.py # Hjälpkommandon (stats, regel, dicehelp)
├── core/                   # Kärnfunktionalitet
│   ├── constants.py        # Globala konstanter och konfiguration
│   ├── dice_parser.py      # Avancerad DiceSpec parser med säkerhet
│   ├── dice_engine.py      # Obegränsade T6-slag och sannolikhet
│   └── knowledge_base.py   # AI integration (Claude + Pinecone)
├── utils/                  # Hjälpfunktioner
│   └── text_utils.py       # Textbehandling och Unicode-hantering
└── [Legacy moduler]        # Befintliga moduler (migration pågår)
```

## 🚀 Nya Funktioner (v2.0)

### 🎲 DiceSpec Parser - Professionell Implementation
- **Flexibel syntax**: Stödjer `3d6+2`, `3D6 + 2`, ` d6 `, `4D10-1`
- **Exploding dice**: `2d6!` för exploderande tärningar
- **Reroll syntax**: `2d6 r<=2` för omslag vid låga värden
- **Säkerhetsskydd**: DoS-skydd med MAX_DICE=100, MAX_SIDES=1000
- **Svenska felmeddelanden**: Tydliga fel med exempel på korrekt syntax
- **Robust validering**: Custom exceptions (InvalidDiceFormat, DiceLimitsError)

### 🧪 Kvalitet & Säkerhet
- **Omfattande testning**: 15+ automatiska tester för all parsing
- **100% bakåtkompatibilitet**: Alla gamla kommandon fungerar
- **Säker drift**: Skydd mot minnesöverbelastning och DoS-attacker
- **Unicode-säker**: Hanterar svenska tecken och emojis korrekt

## 📋 Kommandon

### 🎲 Tärningskommandon (Slash Commands)
```
/roll tärningar:XdY[+Z]           # Vanligt tärningskast
/roll tärningar:XdY[+Z] mål:TARGET # Med framgångskontroll  
/ex antal:X mål:TARGET            # Exploderande T6-slag (EON)
/count tärningar:XdY mål:TARGET   # Räkna framgångar ≥ målvärde
/chance antal:X target:TARGET     # Sannolikhet för exploderande d6:or
/secret roll tärningar:XdY        # Hemligt slag för spelledaren
```

### 🧠 Kunskapskommandon (Slash Commands)
```
/ask fråga:"din fråga"     # AI-assisterad regelfråga
/sök term:sökterm          # Snabbsökning i regelböcker
/allt term:sökterm         # Omfattande sökning
/regel namn:kategori       # Regelreferens
```

### ⚔️ Stridskommandon (Slash Commands)
```
/hugg                # Hugtvapen-attack
/stick               # Stickvapenattack  
/kross               # Krossvapenattack
/fummel              # Fummeltabell
```

### 🎭 SL-verktyg (Slash Commands)
```
/kommentarer aktivera spelare:@user    # Aktivera personliga kommentarer
/kommentarer stil spelare:@user stil:encouraging # Ändra kommentarstil
/kommentarer status spelare:@user      # Visa spelarens inställningar
```

### 🎭 Karaktärsskapande
```
!chargen             # Starta ny karaktär (32 EON-steg)
!chargen start       # Starta ny karaktärssession
!chargen status      # Visa nuvarande framsteg
!chargen reset       # Återställ karaktärsskapande
```

### 📊 Session & Admin (Slash Commands)
```
/startsession namn:"sessionnamn"  # Starta spelsession
/endsession                       # Avsluta med AI-sammanfattning
/showsession                      # Visa aktiv session
/stats                           # Serverstatistik
/mystats                         # Personlig statistik
/dicehelp                        # Hjälp för alla kommandon
```

## 🛠️ Installation & Konfiguration

### 🎯 Enkel Installation (Utan AI/Kunskapsbas)

**För de som bara vill spela utan AI-funktioner:**

#### Steg 1: Skapa Discord Bot
1. Gå till [Discord Developer Portal](https://discord.com/developers/applications)
2. Klicka "New Application" och ge den ett namn (t.ex. "EON Diceroller")
3. Gå till "Bot" sektionen i vänster meny
4. Klicka "Add Bot"
5. Under "Token" klicka "Copy" för att kopiera din bot-token
6. Under "Privileged Gateway Intents" aktivera:
   - ✅ **Message Content Intent** (viktigt!)
   - ✅ **Server Members Intent** 
   - ✅ **Presence Intent**

#### Steg 2: Bjud in bot till din server
1. Gå till "OAuth2" → "URL Generator" 
2. Välj scopes: 
   - ✅ **bot**
   - ✅ **applications.commands**
3. Välj Bot Permissions:
   - ✅ **Send Messages**
   - ✅ **Use Slash Commands** 
   - ✅ **Read Message History**
   - ✅ **Add Reactions**
   - ✅ **Embed Links**
4. Kopiera den genererade URL:en och öppna i webbläsare
5. Välj din server och godkänn

#### Steg 3: Installera och konfigurera
```bash
# 1. Klona och installera
git clone https://github.com/kullendorff/RPGBOT.git
cd RPGBOT
pip install -r requirements.txt

# 2. Skapa .env fil med din bot-token
echo "DISCORD_TOKEN=din_kopierade_token_här" > .env

# 3. Starta bot
python src/main.py
```

#### Steg 4: Testa i Discord
Gå till din server och skriv:
- `/roll tärningar:3d6` - Testa grundläggande tärning
- `!chargen` - Starta karaktärsskapande (fortfarande prefix command)
- `/dicehelp` - Se alla kommandon

**Vad fungerar utan AI:**
- ✅ **Alla tärningskommandon**: `/roll`, `/ex`, `/count`, `/chance` 
- ✅ **Stridsystem**: `/hugg`, `/stick`, `/kross`, `/fummel`
- ✅ **Statistik**: `/stats`, `/mystats` 
- ✅ **Karaktärsskapande**: `!chargen` (komplett EON system)
- ✅ **Sessionshantering**: `/startsession`, `/endsession` (utan AI-sammanfattning)
- ✅ **Hjälpkommandon**: `/dicehelp`, grundläggande `/regel`
- ✅ **Kommentarsystem**: `/kommentarer` (personaliserade kommentarer)

**Vad som INTE fungerar utan AI:**
- ❌ `/ask` (AI-assisterade regelfrågor)
- ❌ `/sök` (avancerad kunskapssökning) 
- ❌ `/allt` (omfattande sökning)
- ❌ AI-genererade sessionssammanfattningar

**Detta ger dig 90% av botens funktionalitet utan några externa API:er eller databaser!**

#### 🔧 Vanliga Problem & Lösningar

**Boten svarar inte:**
- ✅ Kontrollera att **Message Content Intent** är aktiverat i Developer Portal
- ✅ Se till att boten har **Send Messages** behörighet i kanalen
- ✅ Kolla att din .env fil innehåller rätt DISCORD_TOKEN

**"Permission denied" fel:**
- ✅ Boten behöver **Embed Links** och **Add Reactions** behörigheter
- ✅ Kontrollera serverinställningar för botroller

**Boten kraschar vid start:**
- ✅ Kör `pip install -r requirements.txt` igen
- ✅ Kontrollera att Python 3.8+ är installerat
- ✅ Se till att .env filen är i rätt mapp (samma som main.py)

### 🧠 Fullständig Installation (Med AI)

**För avancerade funktioner och kunskapsbas:**

```bash
# 1. Klona och installera
git clone https://github.com/kullendorff/RPGBOT.git
cd RPGBOT
pip install -r requirements.txt

# 2. Fullständig konfiguration (.env)
DISCORD_TOKEN=din_discord_token
PINECONE_API_KEY=din_pinecone_nyckel     # För vektorsökning
ANTHROPIC_API_KEY=din_claude_nyckel      # För AI-funktioner
OPENAI_API_KEY=din_openai_nyckel         # Backup AI
PINECONE_INDEX_NAME=rpg-knowledge
CHANNEL_IDS=kanal1,kanal2                # Valfritt: begränsa kanaler

# 3. Bygg kunskapsbas
python utils/extract_all_pdfs.py        # Extrahera text från PDF:er
python utils/index_knowledge.py         # Indexera för sökning

# 4. Starta bot
python src/main.py
```

### Katalogstruktur
```
data/
├── knowledge_index/     # Whoosh sökindex
├── extracted_text/      # Extraherad PDF-text
├── rules/              # Snabbreferenser (.txt)
├── rolls.db            # SQLite statistikdatabas
├── user_colors.json    # Användarfärger
├── config/             # Bot-konfiguration
└── character_tables/   # Karaktärsskapande tabeller
```

## 🔧 Teknisk Information

### Krav
- **Python 3.8+**
- **Discord.py** för Discord API
- **Anthropic Claude** för AI-funktioner
- **Pinecone** för vektorsökning
- **Whoosh** för fulltextsökning
- **SQLite** för statistik

### Prestanda
- **Startid**: ~5-10 sekunder
- **Svarstid**: <500ms för de flesta kommandon
- **Minnesanvändning**: ~50-100MB
- **Säkerhetsgränser**: 100 tärningar, 1000 sidor max

### Säkerhet
- **DoS-skydd**: Begränsar extrema tärningskast
- **Input-validering**: Säker parsing av all användarinput
- **API-nyckelhantering**: Miljövariaber för säker konfiguration
- **Unicode-säker**: Hanterar alla tecken korrekt

## 🎮 Specialfunktioner för EON

### Obegränsade T6-slag (`!ex`)
- **Exploderande logik**: 6:or tas bort men genererar +2 nya tärningar
- **Perfekta slag**: 
  - 1 tärning: Resultat 1-3
  - Flera tärningar: Högst en tärning ≠ 1
- **Fummel**: Två+ 6:or i första kastomgången

### AI Kunskapsbas
- **Omfattande regelböcker**: Stödjer fullständiga EON-regelböcker
- **Kontextuell sökning**: AI förstår synonymer och sammanhang
- **Flerspråkssökning**: Svenska och engelska termer
- **Semantisk sökning**: Hittar relaterat innehåll även utan exakta matchningar

## 📈 Statistik & Spårning

Boten spårar automatiskt:
- **Alla tärningskast** med resultat och framgång/misslyckanden
- **Perfekta slag och fummel** för obegränsade T6-slag
- **Användningsstatistik** per kommando och spelare
- **Sessionsdata** för AI-genererade sammanfattningar
- **Popularitetsdata** för tärningskombinationer

## 🤖 AI Integration

### Claude AI (Anthropic)
- **Regelfrågning**: Intelligent tolkning av komplexa regelfrågor
- **Sessionssammanfattningar**: Humoristiska sammanfattningar av spelstatistik
- **Kontextuell förståelse**: Kan resonera om spelregler och situationer

### Vektorsökning (Pinecone)
- **Semantisk sökning**: Förstår betydelsen, inte bara ord
- **Snabb prestanda**: Subsekund-svar för de flesta sökningar
- **Skalbarhet**: Hanterar stora regeldokument effektivt

## 🧪 Utveckling & Testning

### Kvalitetssäkring
- **Automated Testing**: 15+ enhetstester för kärnfunktioner
- **Integration Tests**: Validerar commands och AI-funktioner
- **Security Testing**: DoS-skydd och input-validering
- **Performance Testing**: Minnesanvändning och svarstider

### Bidrag
1. **Fork** projektet på GitHub
2. **Skapa branch**: `git checkout -b feature/ny-funktion`
3. **Testa**: Kör alla tester innan commit
4. **Pull Request**: Detaljerad beskrivning av ändringar

### Utvecklingsmiljö
```bash
# Utvecklingsverktyg
pip install pytest black flake8 mypy

# Kör tester
python -m pytest tests/

# Kodformattering
black src/

# Statisk analys
mypy src/
```

## 📋 Roadmap

### Kommande funktioner
- [x] **Karaktärsskapande**: ✅ Komplett EON karaktärsgenerator (människor klar)
- [ ] **Karaktärsskapande utbyggnad**: Alver, dvärgar, tiraker
- [ ] **Kampanjhantering**: Spara och hantera långa kampanjer
- [ ] **Mob-strid**: Hantering av stora strider
- [ ] **Grafiska tabeller**: Visuella representationer av statistik
- [ ] **Flerespråksstöd**: Engelska och andra språk

### Tekniska förbättringar
- [ ] **Docker-deployment**: Containeriserad driftsättning  
- [ ] **Web dashboard**: Webbgränssnitt för admin
- [ ] **REST API**: Externa integrationer
- [ ] **Backup-system**: Automatiska säkerhetskopior

## 📄 Licens

Detta projekt är licensierat under **MIT License**. Se `LICENSE` för detaljer.

## 🙏 Erkännanden

- **Jonas** (https://github.com/jonsal/dragonbane) för Dragonbane-modulen: tärninglogik och kommandouppsättning. Anpassad och regelrättad för den här boten.
- **EON Rollspel** för det fantastiska rollspelssystemet
- **Anthropic** för Claude AI
- **Discord.py** för excellent Discord integration
- **Open Source Community** för alla fantastiska bibliotek

---

**Skapat med ❤️ för den svenska rollspelsgemenskapen**

*Bot version: 2.1 | Senast uppdaterad: 2025-01-21*