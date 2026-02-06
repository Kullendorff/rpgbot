# Komplett Implementationsguide - Spindelstridssystem för EON RPG

## 📋 Översikt

Detta projekt implementerar ett komplett stridssystem för Discord-boten rpgbot baserat på EON:s regeluppsättning. Systemet hanterar två typer av spindelmotståndenare:

1. **Gigantspindel** - Boss-fiende med komplex anatomi och persistent lagring
2. **Små spindlar** - Add-fiender som stör ranged-spelare

Båda systemen använder EON:s officiella skadesystem med Trauma/Smärta/Blödning (T/S/B), automatiska chock- och dödsslag, och detaljerade träfftabeller.

---

## 🎯 Syfte och Funktion

### Gigantspindel-systemet

**Syfte:**
- Hantera episk boss-strid mot en massiv spindel
- Ge spelarna känsla av progression när de systematiskt skadar olika kroppsdelar
- Ge GM fullständig kontroll och översikt över fiendens status
- Bevara stridsstatus även om boten kraschar (persistent lagring)

**Funktion:**
- 6 huvudkroppsdelar med underlokationer (ögon, ben, chelicerer, carapace, bakkropp, spinnvårtor)
- Rustning 0-15 beroende på kroppsdel
- Detaljerade skadetabeller (10 resultat per tabell)
- Tracking av ögon (8st) och ben (8st) individuellt
- AI-genererade dramatiska beskrivningar (valfritt)
- Persistent lagring i JSON-filer per guild
- Chockvärde 28, Skadetålighet 10 kolumner

**Spelupplevelse:**
- Spelarna ser publika meddelanden med sina attackresultat
- GM får privata detaljerade rapporter med full statistik
- Strategiska val: Attackera ögon för att blinda? Ben för att sakta ner?
- Dramatiska beskrivningar ökar immersionen

### Små Spindlar-systemet

**Syfte:**
- Ge ranged-spelare (Umnatak/Kazrik) något att hantera i närstrid
- Skapa dynamik där inte alla bara kan stå still och skjuta
- Snabba, enkla strider som inte tar över från huvudfajten

**Funktion:**
- 2 enkla kroppsdelar (huvud rustning 1, kropp rustning 2)
- Förenklade skadetabeller (5 resultat per tabell)
- Dynamisk spawning (GM kan lägga till fler under striden)
- Chockvärde 10, Skadetålighet 4 kolumner
- Dör snabbare än gigantspindeln (2-4 träffar typiskt)
- Samma T/S/B-system och automatiska slag som stora spindeln

**Spelupplevelse:**
- Snabba, actionfyllda strider
- Tvingar ranged-karaktärer att hantera närstridshot
- GM kan justera svårighetsgrad genom att spawna fler/färre

---

## 📁 Filstruktur

```
rpgbot/
├── src/
│   ├── spider_damage_tables.py          [NY - Gigantspindel tabeller]
│   ├── spider_combat_manager.py         [NY - Gigantspindel manager]
│   ├── small_spider_tables.py           [NY - Små spindlar tabeller]
│   ├── small_spider_manager.py          [NY - Små spindlar manager]
│   ├── commands/
│   │   ├── slash_spider_commands.py     [NY - Gigantspindel kommandon]
│   │   └── slash_small_spider_commands.py [NY - Små spindlar kommandon]
│   └── main.py                          [MODIFIERA - Registrera kommandon]
├── data/
│   └── spider_status_{guild_id}.json    [AUTO-SKAPAD - Persistent data]
└── .env                                  [KONTROLLERA - API-nycklar]
```

---

## 🚀 Steg-för-steg Implementation

### STEG 1: Gigantspindel - Skadetabeller

**Fil:** `src/spider_damage_tables.py`

**Vad filen gör:**
- Definierar alla träfftabeller för 6 kroppsdelar × 3 vapentyper (18 tabeller)
- Rustningsvärden för varje kroppsdel
- Slumpningstabeller för underlokationer
- `parse_effect_code()` funktion som tolkar effektkoder (T*2, S/10, etc.)

**Innehåll:**
- `SPIDER_ARMOR_VALUES` - Rustning per kroppsdel och vapentyp
- `SPIDER_OGON_DAMAGE` - Ögontabeller (ytlig + 10 allvarliga resultat)
- `SPIDER_BEN_HUGG/KROSS/STICK` - Bentabeller för alla vapentyper
- `SPIDER_CHELICERER_*` - Bettänger-tabeller
- `SPIDER_CARAPACE_*` - Huvudpansar-tabeller
- `SPIDER_BAKKROPP_*` - Bakkropps-tabeller
- `SPIDER_SPINNVARTOR_*` - Spinnvårtor-tabeller
- `SPIDER_SUBLOCATION_TABLES` - För slumpning av exakt träffplats
- `parse_effect_code()` - KRITISK funktion för T/S/B-beräkning

**Viktigt:**
- Alla svenska tecken (å/ä/ö) måste vara korrekta
- Filen måste vara UTF-8 encoded
- `parse_effect_code()` MÅSTE finnas - används av manager

### STEG 2: Gigantspindel - Combat Manager

**Fil:** `src/spider_combat_manager.py`

**Vad filen gör:**
- Hanterar spindelns hela status (T/S/B, ögon, ben, effekter)
- Processerar attacker och beräknar skador
- Persistent lagring till JSON efter varje attack
- Automatisk laddning av status vid bot-start
- Genererar AI-beskrivningar (om Claude API finns)
- Formaterar rapporter för GM och spelare

**Huvudklasser:**
- `SpiderDamageResult` - Dataclass för attackresultat
- `SpiderCombatManager` - Huvudklass som hanterar allt

**Nyckelfunktioner:**
- `process_attack()` - Processerar en attack och returnerar resultat
- `_save_to_file()` / `_load_from_file()` - Persistent lagring
- `get_filled_rows()` - Beräknar fyllda rader i T/S/B
- `get_chock_difficulty()` / `get_death_difficulty()` - Beräknar Ob för slag
- `should_roll_chock()` / `should_roll_death()` - Avgör om slag krävs
- `format_gm_report()` - Genererar detaljerad GM-rapport
- `format_public_message()` - Genererar publikt meddelande
- `get_eye_status()` / `get_leg_status()` - Visar skadestatus på ögon/ben

**Persistent Lagring:**
- Sparas till `data/spider_status_{guild_id}.json` efter varje attack
- Laddas automatiskt vid `SpiderCombatManager.__init__()`
- Innehåller: T/S/B totaler, skada per kroppsdel, ögon/ben status, aktiva effekter

**AI-beskrivningar (VALFRITT):**
- Kräver `ANTHROPIC_API_KEY` i `.env`
- Använder Claude API för att generera dramatiska beskrivningar
- Fungerar UTAN API-key (fallback till vanliga beskrivningar)
- Kostnader: ~$0.001 per attack (försumbart)

### STEG 3: Gigantspindel - Slash Commands

**Fil:** `src/commands/slash_spider_commands.py`

**Vad filen gör:**
- Registrerar Discord slash-kommandon för gigantspindeln
- Hanterar användarinteraktion
- Skickar publika meddelanden och privata GM-rapporter

**Kommandon:**

**`/spindel vapentyp område skada`**
- Attackerar gigantspindeln
- Område kan vara: huvud/ben/bakkropp (slumpar underlokation) ELLER specifikt (ögon/chelicerer/etc)
- Publikt: Attack + resultat + T/S/B
- Privat DM till attackeraren: Fullständig GM-rapport

**`/spindelstatus`**
- Visar fullständig status (T/S/B, ögon, ben, effekter)
- Endast synlig för den som kör kommandot (ephemeral)

**`/spindelreset`**
- Återställer spindeln helt
- Raderar JSON-filen
- Endast för GM

**`/spindeldump`**
- Exporterar all spindeldata som JSON
- För backup och felsökning
- Kan skickas som fil om för stort

**Viktigt:**
- `get_spider_manager(guild_id)` - Hämtar manager per server
- Använder `color_handler.get_color()` för användarfärger i embeds
- Försöker skicka DM, fallback till ephemeral om DM är avstängt

### STEG 4: Små Spindlar - Skadetabeller

**Fil:** `src/small_spider_tables.py`

**Vad filen gör:**
- Definierar förenklade träfftabeller för små spindlar
- 2 kroppsdelar (huvud/kropp) × 3 vapentyper (6 tabeller)
- Varje tabell har 5 resultat (istället för 10)
- Samma `parse_effect_code()` funktion som stora spindeln

**Innehåll:**
- `SMALL_SPIDER_ARMOR` - Huvud: 1, Kropp: 2
- `SMALL_SPIDER_HUVUD_HUGG/KROSS/STICK` - Huvudtabeller
- `SMALL_SPIDER_KROPP_HUGG/KROSS/STICK` - Kroppstabeller
- `SMALL_SPIDER_LOCATION_TABLE` - Slumpning (T10: 1-3 huvud, 4-10 kropp)
- `parse_effect_code()` - Identisk med stora spindeln

**Design:**
- Enklare än gigantspindeln men samma struktur
- Högre chans att dö direkt (resultat 1-2 ofta dödliga)
- Lägre rustning = lättare att skada

### STEG 5: Små Spindlar - Manager

**Fil:** `src/small_spider_manager.py`

**Vad filen gör:**
- Hanterar spawning och tracking av flera små spindlar
- Samma T/S/B-system som gigantspindeln
- Automatiska chock- och dödsslag
- INGEN persistent lagring (reset vid bot-restart är OK)

**Huvudklasser:**
- `SmallSpiderDamageResult` - Dataclass för attackresultat
- `SmallSpider` - En individuell liten spindel
- `SmallSpiderManager` - Hanterar alla små spindlar för en guild

**SmallSpider-stats:**
- Chockvärde: 10
- Skadetålighet: 4 kolumner
- T/S/B tracking identisk med gigantspindeln
- `alive` / `conscious` flags

**SmallSpiderManager funktioner:**
- `spawn(count)` - Spawnar X nya spindlar, returnerar ID:n
- `get_spider(id)` - Hämtar specifik spindel
- `get_alive_spiders()` - Lista över levande spindlar
- `process_attack()` - Processerar attack (identisk logik som stora spindeln)
- `reset()` - Nollställer alla spindlar

**Viktigt:**
- Inga ID-konflikter: `next_id` inkrementeras alltid
- Spawning utan max-gräns (GM kan spawna hur många som helst)
- Döda spindlar behålls i listan (för statistik)

### STEG 6: Små Spindlar - Slash Commands

**Fil:** `src/commands/slash_small_spider_commands.py`

**Vad filen gör:**
- Registrerar Discord slash-kommandon för små spindlar
- Samma struktur som gigantspindel-kommandon

**Kommandon:**

**`/spawna_småspindlar antal:X`**
- Spawnar X små spindlar (1-20 åt gången)
- Publikt meddelande: "5 små spindlar spawnar! (Spindel #1-5)"
- Endast för GM (men ingen teknisk begränsning)

**`/småspindel spindel:X vapentyp område skada`**
- Attackerar specifik spindel
- Område: slumpa/huvud/kropp
- Publikt: Attack + träffzon + T/S/B + Chock/Dödsslag + Status
- Privat DM till attackeraren: Detaljerad rapport (samma som stora spindeln)

**`/småspindelstatus`**
- Visar alla spindlars status
- Levande: T/S/B och effekter
- Döda: Markeras som "☠️ DÖD"
- Sammanfattning: Levande/Döda/Totalt

**`/reset_småspindlar`**
- Nollställer alla små spindlar
- Tar bort alla från manager
- Endast för GM

**Viktigt:**
- Felhantering: Kollar att spindel finns och lever innan attack
- Använder samma färgschema och embed-format som stora spindeln
- Chock- och dödsslag visas publikt (med tärningar)

### STEG 7: Modifiera main.py

**Fil:** `src/main.py`

**Vad som ska läggas till:**

Hitta där andra slash-kommandon registreras (troligen nära slutet av `setup_hook()` eller liknande), och lägg till EFTER befintliga registreringar men FÖRE `bot.tree.sync()`:

```python
# Registrera gigantspindel-kommandon
from commands.slash_spider_commands import register_slash_spider_commands
await register_slash_spider_commands(bot, color_handler)
print("Gigantspindel-kommandon registrerade (/spindel, /spindelstatus, /spindelreset, /spindeldump).")

# Registrera småspindel-kommandon
from commands.slash_small_spider_commands import register_slash_small_spider_commands
await register_slash_small_spider_commands(bot, color_handler)
print("Småspindel-kommandon registrerade (/spawna_småspindlar, /småspindel, /småspindelstatus, /reset_småspindlar).")
```

**Viktigt:**
- Registrering måste ske EFTER `color_handler` har skapats
- Registrering måste ske INNAN `bot.tree.sync()`
- Om async context krävs, säkerställ att det körs i rätt async-funktion

### STEG 8: Verifiera Environment

**Fil:** `.env`

Kontrollera att följande finns:

```bash
DISCORD_TOKEN=din_discord_token_här
ANTHROPIC_API_KEY=din_claude_api_key_här  # VALFRITT för AI-beskrivningar
```

**Om ANTHROPIC_API_KEY saknas:**
- Systemet fungerar ändå
- Ingen AI-beskrivning genereras
- Bara standard skadetabellbeskrivningar visas

---

## 🧪 Testning

### Test 1: Starta boten

```bash
cd C:\Diceroller
python src/main.py
```

**Förväntat i console:**
```
...
Gigantspindel-kommandon registrerade (/spindel, /spindelstatus, /spindelreset, /spindeldump).
Småspindel-kommandon registrerade (/spawna_småspindlar, /småspindel, /småspindelstatus, /reset_småspindlar).
Synced X slash commands with Discord
```

### Test 2: Gigantspindel

**I Discord:**

```
/spindel vapentyp:hugg område:huvud skada:20
```

**Förväntat:**
1. Publikt meddelande i kanalen med:
   - Träffzon (t.ex. "Slumpar: 5 → ögon")
   - Rustning och effektiv skada
   - Skadebeskrivning
   - T/S/B värden
   - Spindelns totala T/S/B

2. DM till dig med:
   - Detaljerad rapport
   - Chock/Dödsslag (om krävs)
   - Ögon/Ben-status
   - Aktiva effekter
   - AI-beskrivning (om API aktivt)

3. Fil skapas: `data/spider_status_{guild_id}.json`

**Testa krasch-hantering:**
```
/spindel vapentyp:stick område:ögon skada:25
[Stoppa boten med Ctrl+C]
[Starta boten igen]
/spindelstatus
```

**Förväntat:**
- Status visar samma skada som innan krash
- Console visar: "Laddade spindelstatus från fil: ..."

### Test 3: Små Spindlar

**I Discord:**

```
/spawna_småspindlar antal:5
```

**Förväntat:**
- Meddelande: "🕷️ 5 små spindlar spawnar! (Spindel #1-5)"

```
/småspindel spindel:1 vapentyp:hugg område:slumpa skada:12
```

**Förväntat:**
1. Publikt meddelande med:
   - Slumpat område (T10)
   - Skada och rustning
   - T/S/B
   - Chockslag och Dödsslag (med tärningar synliga)
   - Status (lever/medvetslös/död)

2. DM med detaljerad rapport

```
/småspindelstatus
```

**Förväntat:**
- Lista över alla 5 spindlar
- Spindel #1 visar skada från förra attacken
- Spindel #2-5 visar 0 skada
- Sammanfattning: "Levande: 5 | Döda: 0 | Totalt: 5"

### Test 4: Komplext Scenario

**Simulera fullständig strid:**

```
# Setup
/spawna_småspindlar antal:3
/spindelstatus  # Gigantspindel frisk

# Runda 1
/spindel vapentyp:stick område:ögon skada:22
/småspindel spindel:1 vapentyp:hugg område:kropp skada:15

# Runda 2
/spindel vapentyp:hugg område:ben skada:18
/småspindel spindel:1 vapentyp:stick område:huvud skada:20  # Borde döda

# Kontroll
/spindelstatus  # Se gigantspindel status
/småspindelstatus  # Spindel #1 borde vara död

# Runda 3
/småspindel spindel:2 vapentyp:kross område:slumpa skada:10
/spindel vapentyp:kross område:bakkropp skada:25

# Reset
/reset_småspindlar
/spindelreset
```

---

## 📊 EON Skadesystem - Detaljerad Förklaring

### Grundkoncept

**Tre skadetyper:**
- **Trauma (T)** - Vävnadsskada, förstörd kropp
- **Smärta (S)** - Fysiologisk chock, påverkar handlingar
- **Blödning (B)** - Blodförlust, leder till död

**Skadetålighet:**
- Antal rutor per rad innan ny rad fylls
- Gigantspindel: 10 rutor/rad
- Små spindlar: 4 rutor/rad

**Fyllda rader:**
- När en rad fylls ökar svårigheten för Chock/Dödsslag
- Varje fylld rad = +1T6 svårighet

### Chockslag

**När slås det:**
- Vid Trauma-skada
- Vid Smärta-skada
- När en ny Blödnings-rad fylls

**Svårighet:**
```
ObXT6 mot Chockvärde
där X = Trauma-rader + Smärta-rader + Blödnings-rader
```

**Resultat:**
- Klarar: Inget händer
- Misslyckas: Medvetslös

**Exempel:**
```
Gigantspindel (CV 28):
T: 25 (2 rader), S: 15 (1 rad), B: 30 (3 rader)
Chockslag: Ob6T6 mot 28

Slår: [4][5][3][6][2][1] = 21 ≤ 28 → KLARAR
```

### Dödsslag

**När slås det:**
- Vid Trauma-skada
- När en ny Blödnings-rad fylls

**Svårighet:**
```
ObXT6 mot Chockvärde
där X = Trauma-rader + Blödnings-rader (EJ Smärta!)
```

**Resultat:**
- Klarar: Överlever
- Misslyckas: Död

**Exempel:**
```
Små spindel (CV 10):
T: 8 (2 rader), S: 6 (1 rad), B: 7 (1 rad)
Dödsslag: Ob3T6 mot 10 (T-rader + B-rader, ej S)

Slår: [5][6][3] = 14 > 10 → DÖD
```

### Effektkoder

**Format:** `T*2, S/10, B+3`

**Operatorer:**
- `*` = Multiplicera (T*2 = dubbel trauma)
- `/` = Dividera (S/10 = en tiondel smärta)
- `+` = Addera (B+3 = lägg till 3 blödning)
- `-` = Subtrahera (sällan använt)

**Beräkning:**
```python
Effektiv skada = 15
Effektkod = "T*2, S/10, B+3"

Resultat:
T = 15 * 2 = 30
S = 15 / 10 = 1 (heltalsdivision)
B = 15 + 3 = 18
```

**Varför olika operatorer?**
- Kritiska träffar: Hög trauma, låg smärta (T*2, S/10)
- Ytliga skador: Låg trauma, mer smärta (T/10, S+3)
- Blödande sår: Hög blödning (B*2)

---

## 🎮 Spelupplevelse och Design

### Gigantspindel - Strategiska Val

**Ögon (8st, Rustning 0):**
- Lättast att skada
- Progressiva effekter:
  - 0 ögon: Normalt
  - 1-2 ögon: -1T6 avståndsbedömning
  - 3-4 ögon: -2T6 alla synbaserade handlingar
  - 5-6 ögon: -3T6, Halvblind, Panik
  - 7-8 ögon: BLIND - Anfaller vilt åt alla håll

**Strategiskt värde:** 
- Gör spindeln lättare att undvika
- Men kräver precision (träffzon: ögon)
- Trade-off: Låg rustning men liten träffyta

**Ben (8st, Rustning 8):**
- Måttlig rustning
- Kan huggas av för mobility-nerf
- Progressiva effekter:
  - 0-2 ben: Lätt rörelsehinder
  - 3-4 ben: Halv hastighet
  - 5+ ben: Kan knappt röra sig

**Strategiskt värde:**
- Saktar ner spindeln
- Gör den lättare att kita
- Men tar flera träffar att förstöra

**Chelicerer/Bettänger (Rustning 6):**
- Kan slås av/krossas
- Förhindrar bettattacker
- Innehåller giftkörtel (kan explodera och förgifta spindeln själv!)

**Strategiskt värde:**
- Tar bort spindelns mest farliga attack
- Risk för self-poisoning om giftkörtel sprängd

**Carapace/Huvudpansar (Rustning 10):**
- Högsta rustningen
- Direkt väg till hjärnan
- Högst risk om man misslyckas

**Strategiskt värde:**
- High risk, high reward
- Instakill-potential
- Men svårt att penetrera

**Bakkropp (Rustning 5):**
- Stor träffyta
- Mycket inre organ
- Hög blödning-potential

**Strategiskt värde:**
- Lätt att träffa
- Bra för att bygga upp blödning
- Gör spindeln svagare över tid

**Spinnvårtor (Rustning 2):**
- Lätt att skada
- Förhindrar nätspinning
- Tar bort spindelns kontrollförmåga

**Strategiskt värde:**
- Stoppar web-attacks
- Gör miljön säkrare
- Men kräver specifik targeting

### Små Spindlar - Taktisk Utmaning

**Design-filosofi:**
- Tvingar ranged-spelare att hantera närstrid
- Snabba strider som inte tar över från huvudfajten
- Dynamisk spawning ger GM flexibilitet

**Exempel-scenario:**

```
Runda 1:
- Umnatak (bågskytt) står på avstånd och skjuter stora spindeln
- GM: "/spawna_småspindlar antal:3"
- 3 små spindlar springer mot Umnatak

Runda 2:
- Umnatak måste välja: Skjuta stora spindeln eller hantera små spindlar?
- Kazrik (armborstsskytt) hjälper till: "/småspindel spindel:1..."
- Närstridskaraktärer fokuserar på stora spindeln

Runda 3:
- Små spindlar döda/skadade
- Ranged kan återgå till att skjuta stora spindeln
- Men GM kan spawna fler om de vill öka press
```

**Balans:**
- 2-4 små spindlar: Lätt distraction
- 5-8 små spindlar: Seriös threat för ranged
- 10+ små spindlar: Kaos och desperation

---

## 🔧 Felsökning

### Problem: Import-fel

**Symptom:**
```
ModuleNotFoundError: No module named 'spider_damage_tables'
```

**Lösning:**
1. Kontrollera att filen finns: `src/spider_damage_tables.py`
2. Kontrollera filnamn (exakt stavning, inga mellanslag)
3. Kör från rätt directory: `cd C:\Diceroller`
4. Python path: `python src/main.py` (inte bara `main.py`)

### Problem: Parse error

**Symptom:**
```
NameError: name 'parse_effect_code' is not defined
```

**Lösning:**
1. Öppna `spider_damage_tables.py`
2. Scrolla till slutet - `parse_effect_code()` MÅSTE finnas
3. Kontrollera att den inte är indenterad fel (ska vara på toppnivå)

### Problem: Encoding-fel

**Symptom:**
```
UnicodeDecodeError: 'charmap' codec can't decode byte...
Eller: Trasiga å/ä/ö i meddelanden
```

**Lösning:**
1. Öppna alla Python-filer i en editor
2. Spara som UTF-8 (i VS Code: längst ner till höger)
3. Verifiera att alla svenska tecken ser rätt ut

### Problem: Persistent lagring funkar inte

**Symptom:**
```
Spindeln återställs varje gång boten startas om
Eller: Fil skapas men laddas inte
```

**Lösning:**
1. Kontrollera att `data/` mappen existerar
2. Kolla console: Ser du "Laddade spindelstatus från fil: ..."?
3. Öppna JSON-filen manuellt och kolla att den är giltig
4. Testa manuellt:
```python
import json
with open('data/spider_status_123456789.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
    print(data)
```

### Problem: AI-beskrivningar genereras inte

**Symptom:**
- GM-rapport saknar AI-beskrivning
- Inget fel syns

**Lösning:**
1. Kontrollera `.env`: Finns `ANTHROPIC_API_KEY=...`?
2. Testa API-nyckeln:
```python
import anthropic
client = anthropic.Anthropic(api_key="din_key")
print("API funkar!")
```
3. Kolla console: "Fel vid AI-beskrivning: ..."?
4. VIKTIGT: Systemet fungerar UTAN API - ignorera om du inte vill ha AI

### Problem: Chock/Dödsslag slås inte

**Symptom:**
- Attack processerar men inga slag visas

**Lösning:**
1. Kolla skadan: Om T+0, S+0, B+0 → Inga slag krävs
2. Om effektiv skada < 10 → Ytlig skada → Minimal T/S/B
3. Testa med högre skada: `/spindel vapentyp:hugg område:ögon skada:50`

### Problem: Commands syns inte i Discord

**Symptom:**
- `/spindel` finns inte i slash-command lista

**Lösning:**
1. Vänta 5-10 minuter (Discord sync kan ta tid)
2. Kontrollera console: "Synced X slash commands with Discord"
3. Starta om Discord-klienten
4. Testa i privat meddelande till boten först
5. Kontrollera bot permissions: Behöver "applications.commands"

### Problem: DM fungerar inte

**Symptom:**
- "⚠️ Kunde inte skicka GM-rapport via DM"

**Lösning:**
1. Aktivera DMs från servern:
   - Högerklicka server → Privacy Settings
   - "Allow direct messages from server members" → ON
2. Alternativt: Acceptera ephemeral fallback (visas bara för dig)

---

## 📈 Framtida Förbättringar

**Möjliga utökningar:**

1. **Visuella embeds med anatomi**
   - Discord embed med bild av spindel
   - Färgkodade kroppsdelar baserat på skada
   
2. **Automatiska Chock/Dödsslags-rullningar för spelare**
   - Bot slår automatiskt när spelare tar skada
   - Samma system fast åt andra hållet

3. **Fler monster med samma system**
   - Troll, drake, demon, etc.
   - Återanvänd kod-strukturen
   - Bara nya skadetabeller behövs

4. **Replay-funktion för strider**
   - Spara hela stridhistoriken
   - `/spindelreplay` visar alla attacker i ordning
   - Bra för post-session analys

5. **Webhook-logging till extern tjänst**
   - Skicka all striddata till Google Sheets / Airtable
   - Statistik över vilka kroppsdelar som träffas mest
   - Vilka spelare gör mest skada, etc.

6. **Combat rounds tracking**
   - Automatic initiative system
   - Turn order management
   - Round counter

7. **Multi-monster support**
   - Flera gigantspindlar samtidigt
   - ID-system: Spindel A, B, C
   - `/spindel_a`, `/spindel_b` kommandon

---

## ✅ Checklista före Go-Live

**Innan du släpper systemet till spelarna:**

- [ ] Alla 6 filer skapade och på rätt plats
- [ ] `main.py` modifierad och registrerar kommandon
- [ ] Boten startar utan fel
- [ ] Console visar "Spindelkommandon registrerade..."
- [ ] `/spindel` syns i Discord slash-command lista
- [ ] `/småspindel` syns i Discord slash-command lista
- [ ] Testat attack: Publikt meddelande visas korrekt
- [ ] Testat attack: DM med GM-rapport kommer fram
- [ ] Testat krasch: Status återställs efter bot-restart
- [ ] Testat spawning: Små spindlar kan spawnas
- [ ] Testat dödsslag: Spindlar kan dö
- [ ] Svenska tecken (å/ä/ö) visas korrekt
- [ ] `.env` korrekt konfigurerad
- [ ] `data/` mappen existerar och är skrivbar

**Optional (AI-beskrivningar):**
- [ ] `ANTHROPIC_API_KEY` konfigurerad i `.env`
- [ ] Claude API testad och fungerande
- [ ] Kostnad för API accepterad (~$0.001/attack)

---

## 📞 Support och Feedback

**Om något inte fungerar:**

1. Läs felmeddelandet noga
2. Kolla Felsökning-sektionen ovan
3. Verifiera att alla filer är på rätt plats
4. Testa steg-för-steg enligt Testning-sektionen
5. Kontrollera encoding (UTF-8) på alla filer

**Vanliga misstag:**
- Glömmer registrera i `main.py`
- Kör inte från rätt directory
- Encoding-problem (inte UTF-8)
- Saknar `parse_effect_code()` funktion
- Bot permissions fel i Discord

**Debug-tips:**
```python
# I main.py, lägg till:
print(f"Current directory: {os.getcwd()}")
print(f"Files in src/: {os.listdir('src/')}")

# Test import:
try:
    from spider_damage_tables import parse_effect_code
    print("Import successful!")
except Exception as e:
    print(f"Import failed: {e}")
```

---

## 🎉 Slutord

Detta system ger dig ett komplett, production-ready stridssystem för EON-baserade Discord-strider. Systemet är:

- ✅ **Robust** - Persistent lagring, felhantering, fallbacks
- ✅ **Flexibelt** - Dynamisk spawning, anpassningsbart
- ✅ **Immersivt** - Dramatiska beskrivningar, detaljerad feedback
- ✅ **Balanserat** - Följer EON:s regler exakt
- ✅ **Skalbart** - Lätt att lägga till fler monster

**Lycka till med striden mot gigantspindeln!** 🕷️⚔️

---

**Version:** 1.0  
**Skapad:** 2025-01-09  
**Kompatibel med:** rpgbot v2.1+, EON 4th Edition  
**Författare:** Claude (Anthropic) + Johan Kullendorff  
**Licens:** MIT (fri användning och modifiering)
