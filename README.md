# EON Diceroller Bot 🎲

En Discord-bot för tärningskast, regeluppslag och spelledarverktyg. Ursprungligen byggd för det svenska rollspelet EON, med stöd även för Dragonbane (Drakar och Demoner), Star Wars D6, Delta Green och Skjut Dem I Huvudet.

## ✨ Huvudfunktioner

### 🎯 Tärningskast & Statistik
- **Moderna slash commands**: `/roll tärningar:3d6+2`, `/roll tärningar:3D6+2 mål:15` - flexibla format!
- **Obegränsade T6-slag**: `/ex antal:5 mål:12` för EON:s exploderande tärningar
- **Räkna framgångar**: `/count tärningar:5d10 mål:7` räknar resultat ≥ målvärde
- **Sannolikhetsberäkning**: `/chance antal:3 target:15` - EON-korrekt med exploderande d6:or
- **Hemliga slag**: `/secret_roll`, `/secret_ex` och `/secret_count` - endast synliga för spelledaren
- **Detaljerad statistik**: `/stats`, `/mystats`, `/allstats`, `/mystatsall` spårar slagen

### 📚 Regeluppslag
- **Regelreferenser**: `/eon_regel namn:strid` för snabba regeluppslag från `data/rules/`
- **Förbättringsslag**: `/eon_hoj` enligt EON-reglerna

### ⚔️ Stridsystem
- **Attacksimuleringar**: `/eon_hugg`, `/eon_stick`, `/eon_kross` med realistiska skadeberäkningar
- **Fummeltabeller**: `/eon_fummel` för kritiska misslyckanden
- **Vapenskaderegler**: Automatisk hantering av olika vapentypers skador

### 🎭 Session & kommentarer
- **Sessionshantering**: `/startsession beskrivning:"Äventyr i Trinsmyra"`, `/endsession` och `/showsession`
- **Personaliserade kommentarer**: `/kommentarer` - SL kan aktivera anpassade kommentarer för spelares tärningsslag

### 🐉 Dragonbane (Drakar och Demoner)
- **Tärningsslag**: `/dod_slag expression:2T6+1T8+3`
- **Färdighetsslag**: `/dod_fv skill:13 modifier:2 mode:fördel` (slag <= FV lyckas, 1 = drakslag, 20 = demonslag). Parameter `antal` staplar fördel/nackdel (house rule)
- **Pressa slag**: `/dod_pressa skill:13 grundegenskap:STY`, eller knappen "Pressa slag" under ett misslyckat slag
- **Skada**: `/dod_skada dice:1T10 bonus:2`
- **Förbättring**: `/dod_hoj skill:13` (1T20, högre än FV ger +1)
- **Skräck och mumie**: `/dod_skrack`, `/dod_mumie`
- **Initiativ**: `/dod_init characters:Björn,Saga,Ragna` (kortlek 1-10, lägst agerar först)

> **Dragonbane-modulen är byggd av Jonas.** Den ursprungliga koden anpassades till botens arkitektur (Cog + embed_factory) och regelrättades: initiativ dras som kortlek (unika 1-10, lägst först) och tillstånd kan bindas till grundegenskap. Krediten visas även i sidfoten på varje Dragonbane-resultat i Discord. Heder och tack till Jonas.

### ⚔️ Star Wars D6 (WEG40120, 2nd Ed. Revised & Expanded)
- **Färdighets-/attributslag**: `/sw_slag kod:4D+2 svarighet:15` — Wild Die exploderar på 6:or, en etta på det första slaget ger SL tre alternativ (räkna in / dra bort ettan och högsta andra tärningen / komplikation), alla uträknade direkt i embeden
- **Character Point**: knappen "+1D Character Point" under resultatet lägger till en ny tärning som också exploderar på 6:or (kan tryckas flera gånger)
- **Force Point**: `/sw_slag kod:4D+2 force_point:True` — dubblar hela tärningspoolen (kan inte kombineras med Character Point samma runda)
- **Multipla handlingar**: `/sw_slag kod:4D+2 handlingar:3` — automatiskt -1D per extra handling
- **Motstått slag**: `/sw_motstand aktion:4D+2 forsvar:3D+1` — högst total vinner, oavgjort går till initiativtagaren
- **Referens**: `/sw_svarighet` — svårighetsnivåer och modifikatorsteg
- **Initiativ**: `/sw_init karaktarer:"Han 3D+2, Chewie 2D+1"`

Regler verifierade mot källboken (WEG40120), inte bara OCR-texten — se `src/starwars/dice.py` för sidhänvisningar.

### 🕵️ Delta Green
- **Snabbkast och tester**: `/dgcheck`, `/dgstat`, `/dgluck`, `/dglethality`, `/dgsan`
- **Agent**: `/dgagent`, `/dgallt`, `/dgroll`, `/dgdmg`, `/dgproject`
- **SL-verktyg**: `/dggmallt`, `/dggmroll`, `/dggmstatus`, `/dggmset`, `/dggmdmg`, `/dggmreset`
- **Session**: `/dgstartsession`, `/dgendsession`

### ☢️ Skjut Dem I Huvudet
SDIH använder fortfarande prefixkommandon (`!`), inte slash. Hjälp via `!sdihelp`. Exempel: `!rull`, `!fördel`, `!nackdel`, `!skada`, `!träffzon`, `!initiativ`, `!smitta`, `!amputera`, `!splatter`.

## 🏗️ Arkitektur (Modulär Design)

```
src/
├── main.py                 # Bot entry point
├── commands/               # Gemensamma slash-kommandon
│   ├── slash_dice_commands.py    # /roll, /ex, /count, /chance
│   ├── slash_admin_commands.py   # /secret_roll, /secret_ex, /secret_count, session
│   ├── slash_utility_commands.py # /help, /stats, /mystats, /allstats, /mystatsall
│   ├── slash_comment_commands.py # /kommentarer
│   └── slash_manipulation_commands.py
├── eon/                    # EON: mekanik + EonCommands (/eon_hugg, /eon_regel, /eon_hoj, ...)
├── dragonbane/             # Dragonbane / Drakar och Demoner
├── starwars/               # Star Wars D6 (WEG40120)
├── deltagreen/             # Delta Green
├── skjutdomihuvudet/       # Skjut Dem I Huvudet (prefixkommandon)
├── core/                   # Kärnfunktionalitet
│   ├── constants.py        # Globala konstanter och konfiguration
│   ├── dice_parser.py      # DiceSpec-parser med säkerhetsgränser
│   └── dice_engine.py      # Obegränsade T6-slag och sannolikhet
└── utils/                  # Hjälpfunktioner
    └── text_utils.py       # Textbehandling och Unicode-hantering
```

## 🚀 DiceSpec Parser

- **Flexibel syntax**: Stödjer `3d6+2`, `3D6 + 2`, ` d6 `, `4D10-1`
- **Exploding dice**: `2d6!` för exploderande tärningar
- **Reroll syntax**: `2d6 r<=2` för omslag vid låga värden
- **Säkerhetsskydd**: DoS-skydd med MAX_DICE=100, MAX_SIDES=1000
- **Svenska felmeddelanden**: Tydliga fel med exempel på korrekt syntax
- **Robust validering**: Egna undantag (InvalidDiceFormat, DiceLimitsError)

### 🧪 Kvalitet & Säkerhet
- **Automatiska tester**: enhetstester för tärningsmotorer och mekanik (Star Wars, Delta Green, Dragonbane, EON)
- **Säker drift**: Skydd mot minnesöverbelastning och DoS-attacker
- **Unicode-säker**: Hanterar svenska tecken och emojis korrekt

## 📋 Kommandon

### 🎲 Tärningskommandon (Slash Commands)
```
/roll tärningar:XdY[+Z]            # Vanligt tärningskast
/roll tärningar:XdY[+Z] mål:TARGET # Med framgångskontroll
/ex antal:X mål:TARGET             # Exploderande T6-slag (EON)
/count tärningar:XdY mål:TARGET    # Räkna framgångar ≥ målvärde
/chance antal:X target:TARGET      # Sannolikhet för exploderande d6:or
/secret_roll tärningar:XdY         # Hemligt slag för spelledaren
/secret_ex antal:X                 # Hemliga exploderande T6-slag
/secret_count tärningar:XdY mål:Y  # Hemlig framgångsräkning
```

### 📚 Regler (Slash Commands)
```
/eon_regel namn:kategori   # Regelreferens från data/rules/
/eon_hoj                   # Förbättringsslag för färdigheter
```

### ⚔️ Stridskommandon (Slash Commands)
```
/eon_hugg            # Hugtvapen-attack
/eon_stick           # Stickvapenattack
/eon_kross           # Krossvapenattack
/eon_fummel          # Fummeltabell
```

### 🎭 SL-verktyg (Slash Commands)
```
/kommentarer aktivera spelare:@user     # Aktivera personliga kommentarer
/kommentarer stil spelare:@user stil:encouraging
/kommentarer frekvens / status / lista / inaktivera / global_av
```

### 📊 Session, statistik & hjälp (Slash Commands)
```
/startsession beskrivning:"sessionnamn"  # Starta spelsession
/endsession                              # Avsluta spelsession
/showsession                             # Visa aktiv session
/stats                                   # Serverstatistik
/mystats                                 # Personlig statistik
/allstats                                # [GM] Avancerad statistik
/mystatsall                              # Utökad personlig statistik
/help                                    # Hjälp för kommandona
```

Dragonbane-, Star Wars- och Delta Green-kommandona listas under huvudfunktionerna ovan. SDIH använder prefixkommandon, se `!sdihelp`.

## 🛠️ Installation & Konfiguration

### 🎯 Installation

**Krav:** Python 3.10 eller nyare (numpy 2.2 i `requirements.txt` kräver minst 3.10). Fungerar på Windows, macOS och Linux.

#### Steg 1: Skapa Discord Bot
1. Gå till [Discord Developer Portal](https://discord.com/developers/applications)
2. Klicka "New Application" och ge den ett namn (t.ex. "EON Diceroller")
3. Gå till "Bot" sektionen i vänster meny
4. Klicka "Add Bot"
5. Under "Token" klicka "Copy" för att kopiera din bot-token
6. Under "Privileged Gateway Intents" aktivera:
   - ✅ **Message Content Intent** (behövs för SDIH:s prefixkommandon)
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

Klona repot och skapa en virtuell miljö:

```bash
git clone https://github.com/Kullendorff/rpgbot.git
cd rpgbot
```

Windows:

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

macOS / Linux:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Skapa en `.env`-fil i **repots rotkatalog** (samma mapp som `requirements.txt`, inte i `src/`) med minst:

```
DISCORD_TOKEN=din_kopierade_token_här
```

Valfritt men rekommenderat vid utveckling: `GUILD_ID=din_server_id` ger omedelbar synkning av slash-kommandon till den servern. Utan `GUILD_ID` kan en global synk ta upp till en timme.

Starta boten från repots rotkatalog:

```bash
python src/main.py
```

#### Steg 4: Testa i Discord
Gå till din server och skriv:
- `/roll tärningar:3d6` - Testa grundläggande tärning
- `/help` - Se kommandona

**Allt fungerar utan externa API:er.** Boten behöver bara `DISCORD_TOKEN`.

#### 🔧 Vanliga Problem & Lösningar

**Boten svarar inte:**
- ✅ Kontrollera att **Message Content Intent** är aktiverat i Developer Portal (behövs för SDIH)
- ✅ Se till att boten har **Send Messages** behörighet i kanalen
- ✅ Kolla att `.env` ligger i repots rot och innehåller rätt `DISCORD_TOKEN`
- ✅ Slash-kommandon som saknas efter start: sätt `GUILD_ID` eller vänta på global synk

**"Permission denied" fel:**
- ✅ Boten behöver **Embed Links** och **Add Reactions** behörigheter
- ✅ Kontrollera serverinställningar för botroller

**Boten kraschar vid start:**
- ✅ Kontrollera att Python 3.10+ används (`python --version`)
- ✅ Kör `pip install -r requirements.txt` i den aktiverade virtuella miljön
- ✅ Se till att `.env` finns i repots rotkatalog och att du startar från den mappen

### Katalogstruktur
```
data/
├── rules/              # Snabbreferenser (.txt)
├── rolls.db            # SQLite statistikdatabas
├── user_colors.json    # Användarfärger
├── config/             # Bot-konfiguration
├── deltagreen/         # Delta Green-data
└── sdih_decks/         # Kortlekar för Skjut Dem I Huvudet
```

## 🔧 Teknisk Information

### Krav
- **Python 3.10+** (krävs av numpy 2.2)
- **Discord.py** för Discord API
- **SQLite** för statistik

### Prestanda
- **Startid**: ~5-10 sekunder
- **Svarstid**: <500ms för de flesta kommandon
- **Minnesanvändning**: ~50-100MB
- **Säkerhetsgränser**: 100 tärningar, 1000 sidor max

### Säkerhet
- **DoS-skydd**: Begränsar extrema tärningskast
- **Input-validering**: Säker parsing av all användarinput
- **API-nyckelhantering**: Miljövariabler för säker konfiguration
- **Unicode-säker**: Hanterar alla tecken korrekt

## 🎮 Specialfunktioner för EON

### Obegränsade T6-slag (`/ex`)
- **Exploderande logik**: 6:or tas bort men genererar +2 nya tärningar
- **Perfekta slag**:
  - 1 tärning: Resultat 1-3
  - Flera tärningar: Högst en tärning ≠ 1
- **Fummel**: Två+ 6:or i första kastomgången

## 📈 Statistik & Spårning

Boten spårar automatiskt:
- **Alla tärningskast** med resultat och framgång/misslyckanden
- **Perfekta slag och fummel** för obegränsade T6-slag
- **Användningsstatistik** per kommando och spelare
- **Sessionsdata**
- **Popularitetsdata** för tärningskombinationer

## 🧪 Utveckling & Testning

Tester använder `unittest` och ska köras som skript, inte via `pytest` eller `python -m unittest`:

```bash
python tests/test_starwars_dice.py
python tests/test_dragonbane_dice.py
python tests/test_eon_mechanics.py
python tests/test_eon_commands_registration.py
python tests/test_deltagreen_agent_manager.py
python tests/test_deltagreen_project_flow.py
python tests/test_deltagreen_projection.py
python tests/test_deltagreen_san_cache.py
```

### Bidrag
1. **Fork** projektet på GitHub
2. **Skapa branch**: `git checkout -b feature/ny-funktion`
3. **Testa**: Kör testerna ovan innan commit
4. **Pull Request**: Detaljerad beskrivning av ändringar

## 📋 Roadmap

### Kommande funktioner
- [ ] **Kampanjhantering**: Spara och hantera långa kampanjer
- [ ] **Mob-strid**: Hantering av stora strider
- [ ] **Grafiska tabeller**: Visuella representationer av statistik
- [ ] **Flerespråksstöd**: Engelska och andra språk
- [ ] **SDIH som slash commands**: Prefixkommandona i Skjut Dem I Huvudet flyttas till `/`

### Tekniska förbättringar
- [ ] **Docker-deployment**: Containeriserad driftsättning
- [ ] **Web dashboard**: Webbgränssnitt för admin
- [ ] **REST API**: Externa integrationer
- [ ] **Backup-system**: Automatiska säkerhetskopior

## 📄 Licens

Detta projekt är licensierat under **MIT License**. Se `LICENSE` för detaljer.

## 🙏 Erkännanden

- **Jonas** för Dragonbane-modulen: tärninglogik och kommandouppsättning. Anpassad och regelrättad för den här boten.
- **EON Rollspel** för det fantastiska rollspelssystemet
- **Discord.py** för excellent Discord integration
- **Open Source Community** för alla fantastiska bibliotek

---

**Skapat med ❤️ för den svenska rollspelsgemenskapen**

*Senast uppdaterad: 2026-11-25*
