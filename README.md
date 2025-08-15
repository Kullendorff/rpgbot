# EON Diceroller Bot 🎲

En avancerad Discord-bot för tärningskast och kunskapshantering för det svenska rollspelet EON, med stöd för "Skjut Dem I Huvudet".

## ✨ Huvudfunktioner

### 🎯 Tärningskast & Statistik
- **Flexibla tärningskast**: `!roll 3d6+2`, `!roll 3D6 + 2`, `!roll d6` - alla format fungerar!
- **Obegränsade T6-slag**: `!ex 3d6 15` för EON:s exploderande tärningar
- **Räkna framgångar**: `!count 5d10 7` räknar resultat ≥ målvärde
- **Sannolikhetsberäkning**: `!chance 3d6+2 15` visar lyckosannolikhet
- **Hemliga slag**: `!secret roll 2d6` endast synligt för spelledaren
- **Detaljerad statistik**: `!stats`, `!mystats` spårar alla slag

### 🧠 AI-driven Kunskapsbas
- **Intelligent sökning**: `!ask "Vad är Ferox?"` - AI-assisterad regelfrågor
- **Snabbsökning**: `!sök ferox` för direkta sökresultat  
- **Omfattande sökning**: `!allt ferox` genomsöker hela regelbiblioteket
- **Regelreferenser**: `!regel strid` för snabba regeluppslag

### ⚔️ Stridsystem
- **Attacksimuleringar**: `!hugg`, `!stick`, `!kross` med realistiska skadeberäkningar
- **Fummeltabeller**: `!fummel` för kritiska misslyckanden
- **Vapenskaderegler**: Automatisk hantering av olika vapentypers skador

### 🎭 Sessionshantering & AI
- **Sessionshantering**: `!startsession "Äventyr i Trinsmyra"` och `!endsession`
- **AI-sammanfattningar**: Automatiska humoristiska sessionssammanfattningar via Claude AI
- **Spelledarverktyg**: Hemliga kommandon och demonisk inspiration

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

### 🎲 Tärningskommandon
```
!roll XdY[+Z]        # Vanligt tärningskast
!roll XdY[+Z] TARGET # Med framgångskontroll
!ex XdY[+Z] TARGET   # Obegränsat T6-slag (EON)
!count XdY TARGET    # Räkna framgångar ≥ målvärde
!chance XdY TARGET   # Beräkna sannolikhet att lyckas
!secret COMMAND      # Hemligt slag för spelledaren
```

### 🧠 Kunskapskommandon
```
!ask "fråga"         # AI-assisterad regelfråga
!sök sökterm         # Snabbsökning i regelböcker
!allt sökterm        # Omfattande sökning
!regel kategori      # Regelreferens
```

### ⚔️ Stridskommandon
```
!hugg               # Hugtvapen-attack
!stick              # Stickvapenattack  
!kross              # Krossvapenattack
!fummel             # Fummeltabell
```

### 📊 Session & Admin
```
!startsession "namn"  # Starta spelsession
!endsession          # Avsluta med AI-sammanfattning
!showsession         # Visa aktiv session
!stats               # Serverstatistik
!mystats             # Personlig statistik
!dicehelp            # Hjälp för alla kommandon
```

## 🛠️ Installation & Konfiguration

### Snabbstart
```bash
# 1. Klona och installera
git clone https://github.com/kullendorff/RPGBOT.git
cd RPGBOT
pip install -r requirements.txt

# 2. Konfigurera miljövariabler (.env)
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
- [ ] **Karaktärsskapande**: Fullständig EON karaktärsgenerator
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

- **EON Rollspel** för det fantastiska rollspelssystemet
- **Anthropic** för Claude AI
- **Discord.py** för excellent Discord integration
- **Open Source Community** för alla fantastiska bibliotek

---

**Skapat med ❤️ för den svenska rollspelsgemenskapen**

*Bot version: 2.0 | Senast uppdaterad: 2025-01-13*