# EON Diceroller Bot 🎲

En avancerad Discord-bot för tärningskast och regeluppslag för det svenska rollspelet EON, med stöd för "Skjut Dem I Huvudet".

## ✨ Huvudfunktioner

### 🎯 Tärningskast & Statistik
- **Moderna slash commands**: `/roll tärningar:3d6+2`, `/roll tärningar:3D6+2 mål:15` - flexibla format!
- **Obegränsade T6-slag**: `/ex antal:5 mål:12` för EON:s exploderande tärningar
- **Räkna framgångar**: `/count tärningar:5d10 mål:7` räknar resultat ≥ målvärde
- **Sannolikhetsberäkning**: `/chance antal:3 target:15` - EON-korrekt med exploderande d6:or
- **Hemliga slag**: `/secret roll tärningar:2d6` endast synligt för spelledaren
- **Detaljerad statistik**: `/stats`, `/mystats` spårar alla slag

### 📚 Regeluppslag
- **Regelreferenser**: `/eon_regel namn:strid` för snabba regeluppslag från `data/rules/`

### ⚔️ Stridsystem
- **Attacksimuleringar**: `/eon_hugg`, `/eon_stick`, `/eon_kross` med realistiska skadeberäkningar
- **Fummeltabeller**: `/eon_fummel` för kritiska misslyckanden
- **Vapenskaderegler**: Automatisk hantering av olika vapentypers skador

### 🎭 Karaktärsskapande & Session
- **Sessionshantering**: `/startsession namn:"Äventyr i Trinsmyra"` och `/endsession`
- **Personaliserade kommentarer**: `/kommentarer` - SL kan aktivera anpassade kommentarer för spelares tärningsslag

### 🐉 Dragonbane (Drakar och Demoner)
- **Tärningsslag**: `/dod_slag expression:2T6+1T8+3`
- **Färdighetsslag**: `/dod_fv skill:13 modifier:2 mode:fördel` (slag <= FV lyckas, 1 = drakslag, 20 = demonslag)
- **Pressa slag**: `/dod_pressa skill:13 grundegenskap:STY`, eller knappen "Pressa slag" under ett misslyckat slag
- **Skada**: `/dod_skada dice:1T10 bonus:2`
- **Initiativ**: `/dod_init characters:Björn,Saga,Ragna` (kortlek 1-10, lägst agerar först)

> **Dragonbane-modulen är byggd av Jonas** (https://github.com/jonsal/dragonbane). Den ursprungliga koden anpassades till botens arkitektur (Cog + embed_factory) och regelrättades: initiativ dras som kortlek (unika 1-10, lägst först) och tillstånd kan bindas till grundegenskap. Krediten visas även i sidfoten på varje Dragonbane-resultat i Discord. Heder och tack till Jonas.

### ⚔️ Star Wars D6 (WEG40120, 2nd Ed. Revised & Expanded)
- **Färdighets-/attributslag**: `/sw_slag kod:4D+2 svarighet:15` — Wild Die exploderar på 6:or, en etta på det första slaget ger SL tre alternativ (räkna in / dra bort ettan och högsta andra tärningen / komplikation), alla uträknade direkt i embeden
- **Character Point**: knappen "+1D Character Point" under resultatet lägger till en ny tärning som också exploderar på 6:or (kan tryckas flera gånger)
- **Force Point**: `/sw_slag kod:4D+2 force_point:true` — dubblar hela tärningspoolen (kan inte kombineras med Character Point samma runda)
- **Multipla handlingar**: `/sw_slag kod:4D+2 handlingar:3` — automatiskt -1D per extra handling
- **Motstått slag**: `/sw_motstand aktion:4D+2 forsvar:3D+1` — högst total vinner, oavgjort går till initiativtagaren
- **Referens**: `/sw_svarighet` — svårighetsnivåer och modifikatorsteg
- **Initiativ**: `/sw_init karaktarer:"Han 3D+2, Chewie 2D+1"`

Regler verifierade mot källboken (WEG40120), inte bara OCR-texten — se `src/starwars/dice.py` för sidhänvisningar.

## 🏗️ Arkitektur (Modulär Design)

```
src/
├── main.py                 # Bot entry point
├── commands/               # Slash-kommandomoduler
│   ├── slash_dice_commands.py    # Tärningskommandon (/roll, /ex, /count, /chance)
│   ├── slash_admin_commands.py   # Admin/GM kommandon (/secret_roll, session)
│   └── slash_utility_commands.py # Hjälpkommandon (/stats, /dicehelp)
├── eon/                    # EON som eget paket: mekanik + EonCommands (/eon_hugg, /eon_regel ...)
├── core/                   # Kärnfunktionalitet
│   ├── constants.py        # Globala konstanter och konfiguration
│   ├── dice_parser.py      # Avancerad DiceSpec parser med säkerhet
│   └── dice_engine.py      # Obegränsade T6-slag och sannolikhet
└── utils/                  # Hjälpfunktioner
    └── text_utils.py       # Textbehandling och Unicode-hantering
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

### 📚 Regler (Slash Commands)
```
/eon_regel namn:kategori   # Regelreferens från data/rules/
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
/kommentarer aktivera spelare:@user    # Aktivera personliga kommentarer
/kommentarer stil spelare:@user stil:encouraging # Ändra kommentarstil
/kommentarer status spelare:@user      # Visa spelarens inställningar
```

### 📊 Session & Admin (Slash Commands)
```
/startsession namn:"sessionnamn"  # Starta spelsession
/endsession                       # Avsluta spelsession
/showsession                      # Visa aktiv session
/stats                           # Serverstatistik
/mystats                         # Personlig statistik
/dicehelp                        # Hjälp för alla kommandon
```

## 🛠️ Installation & Konfiguration

### 🎯 Installation

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
- `/dicehelp` - Se alla kommandon

**Allt fungerar utan externa API:er:**
- ✅ **Alla tärningskommandon**: `/roll`, `/ex`, `/count`, `/chance` 
- ✅ **Stridsystem**: `/eon_hugg`, `/eon_stick`, `/eon_kross`, `/eon_fummel`
- ✅ **Statistik**: `/stats`, `/mystats` 
- ✅ **Sessionshantering**: `/startsession`, `/endsession`
- ✅ **Hjälpkommandon**: `/dicehelp`, grundläggande `/eon_regel`
- ✅ **Kommentarsystem**: `/kommentarer` (personaliserade kommentarer)

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

### Katalogstruktur
```
data/
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

## 📈 Statistik & Spårning

Boten spårar automatiskt:
- **Alla tärningskast** med resultat och framgång/misslyckanden
- **Perfekta slag och fummel** för obegränsade T6-slag
- **Användningsstatistik** per kommando och spelare
- **Sessionsdata**
- **Popularitetsdata** för tärningskombinationer

## 🧪 Utveckling & Testning

### Kvalitetssäkring
- **Automated Testing**: 15+ enhetstester för kärnfunktioner
- **Integration Tests**: Validerar kommandon och moduler
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
- **Discord.py** för excellent Discord integration
- **Open Source Community** för alla fantastiska bibliotek

---

**Skapat med ❤️ för den svenska rollspelsgemenskapen**

*Bot version: 2.1 | Senast uppdaterad: 2025-01-21*