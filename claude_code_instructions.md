# Claude Code Instruktioner - EON TableProcessor Analys och Implementation

## Bakgrund
Vi utvecklar en TableProcessor för EON Diceroller Bot som ska hantera komplexa rollspelstabeller med hierarkisk struktur, conditional logic och nested subtables. En grundläggande implementation finns redan framtagen, men vi behöver analysera alla befintliga tabeller för att säkerställa att den täcker alla patterns.

## Uppgift 1: Analysera Befintliga Tabellstrukturer

### 1.1 Inventering av Tabeller
Gå igenom katalogen `C:\temp\ai\diceroller\data\character_tables\` och dokumentera:

- Alla JSON-filer som finns
- Mappstruktur (underkategorier som `familj/`, `bord/`, `handelser/` etc.)
- Textfiler för länder/beskrivningar

**Skapa en översikt:**
```markdown
## Befintliga Tabeller

### Bakgrundstabeller
- huvudbakgrund.json
- mental_traits.json
- physical_traits.json
- [etc...]

### Familjetabeller  
- familj/familj_ovr.json
- [etc...]

### Andra strukturer
- [dokumentera alla du hittar]
```

### 1.2 Strukturanalys av Key Patterns
Analysera minst 5-10 olika JSON-filer och identifiera:

**A) Grundstrukturer:**
- Hierarkiska strukturer (`bakgrundstabeller.huvudtabell`)
- Range-definitioner (`"1-25"`, `"26-50"`, `"100"`)
- Dice notation (`"1d100"`, `"2d6+3"`)

**B) Avancerade features:**
- Conditional logic exempel (`conditions`, `not_alv_bazirk_frakktirak`)
- Subtable strukturer (`has_subtable: true`)
- Roll twice mechanics (`"roll_twice"`, `"roll_again"`)
- Skill bonuses (`skill_bonus: "1d6+1"`)

**C) Special cases:**
- Attributmodifierare för folkslag
- Weighted selections
- Cross-references mellan tabeller

### 1.3 Skapa Pattern-dokumentation
För varje unique pattern, dokumentera:

```markdown
### Pattern: [Namn]
**Förekommer i:** [Filnamn]
**Struktur:**
```json
{
  "exempel": "av pattern"
}
```
**Användning:** [Förklaring av vad det gör]
**TableProcessor support:** [Behöver det specialhantering?]
```

## Uppgift 2: Validera TableProcessor Implementation

### 2.1 Granska Befintlig Kod
Vi har en TableProcessor-implementation som hanterar:

- Hierarkisk navigation
- Conditional logic för EON-specifika conditions
- Nested subtables
- Roll twice mechanics
- Robust dice parsing
- Textfil-hantering

### 2.2 Gap-analys
Jämför befintlig implementation mot identifierade patterns:

**Säkerställ att följande fungerar:**
- Alla range-format som används
- Alla dice notations som förekommer
- Alla conditional logic patterns
- Alla subtable strukturer

**Identifiera gaps:**
- Patterns som inte stöds
- Edge cases som behöver special handling
- Performance concerns för stora tabeller

### 2.3 Testa mot Riktiga Data
Skapa test-scripts som:

1. Laddar alla JSON-tabeller
2. Testar basic functionality på varje tabell
3. Verifierar conditional logic
4. Testar edge cases (roll twice, nested subtables)

## Uppgift 3: Utöka och Förbättra TableProcessor

### 3.1 Implementera Saknade Features
Baserat på gap-analysen, lägg till:

- Nya conditional logic patterns
- Support för speciella dice formulas (om de finns)
- Attributmodifier-hantering
- Cross-table references

### 3.2 Optimera Performance
- Caching av laddade tabeller
- Effektiv range-matching
- Memory optimization för stora datasets

### 3.3 Error Handling
- Robust felhantering för korrupta JSON-filer
- Tydliga felmeddelanden för utvecklare
- Graceful degradation vid missing files

## Uppgift 4: Integration och Testing

### 4.1 Skapa Komplett TableProcessor
Baserat på analysen, skapa final version av:

```python
# table_processor.py
class TableProcessor:
    # Komplett implementation med all identifierad funktionalitet
    
# character_context.py  
class CharacterContext:
    # Utökad context för alla identifierade conditional patterns

# table_result.py
class TableResult:
    # Resultat-struktur som hanterar alla result types
```

### 4.2 Integration med Discord Bot
Skapa hjälpfunktioner för Discord-kommandon:

```python
# discord_integration.py
def roll_background_sequence(context, num_rolls=3):
    # Rullar bakgrundssekvens för karaktärsskapande
    
def create_character_context(folkslag, kultur=None, social_class=None):
    # Skapar context från grundläggande karaktärsinfo
    
def format_table_result_for_discord(result):
    # Formaterar TableResult för Discord-meddelanden
```

### 4.3 Comprehensive Testing
Skapa test-suite som:

- Testar alla tabeller individuellt
- Verifierar conditional logic för alla folkslag
- Testar komplett karaktärsskapande-sekvenser
- Performance testing med många samtida användare

## Uppgift 5: Dokumentation och Exempel

### 5.1 Usage Examples
Skapa konkreta exempel för:

```python
# Exempel 1: Basic table roll
processor = TableProcessor()
context = CharacterContext(folkslag="alv", kultur="civiliserad")
result = processor.roll_on_table('mental_traits', context=context)

# Exempel 2: Bakgrundsekvens
background = roll_background_sequence(context, num_rolls=3)

# Exempel 3: Integration med Discord
@bot.command()
async def bakgrund(ctx, folkslag, antal=1):
    # Implementation av Discord-kommando
```

### 5.2 Developer Documentation
Dokumentera:

- API för TableProcessor
- Hur man lägger till nya tabeller
- Conditional logic patterns
- Troubleshooting guide

## Deliverables

När uppgiften är klar ska följande finnas:

1. **Analys-rapport** av alla befintliga tabeller och patterns
2. **Komplett TableProcessor** som hanterar alla identifierade use cases
3. **Integration-kod** för Discord Bot
4. **Test-suite** som verifierar all funktionalitet
5. **Dokumentation** med exempel och troubleshooting

## Prioritet

1. **HÖGST:** Analysera befintliga tabeller (Uppgift 1)
2. **HÖG:** Validera och utöka TableProcessor (Uppgift 2-3)
3. **MEDEL:** Integration och testing (Uppgift 4)
4. **LÅG:** Dokumentation (Uppgift 5)

## Tips för Claude Code

- Använd MCP file operations för att läsa JSON-filer
- Skapa helper scripts för batch-analys av tabeller
- Testa incrementally - verifiera varje pattern innan du går vidare
- Logga alla edge cases du hittar för later analysis
- Performance-testa med stora tabeller från början

## Expected Challenges

- **Encoding issues:** EON använder svenska tecken (ä, ö, å)
- **Complex conditional logic:** Många EON-specifika regler
- **Large table hierarchies:** Huvudbakgrund -> många subtabeller
- **Memory usage:** Många stora JSON-filer laddade samtidigt

## Success Criteria

TableProcessor ska kunna:
- ✅ Ladda alla befintliga EON-tabeller utan fel
- ✅ Hantera alla conditional logic patterns
- ✅ Generera korrekta resultat för alla folkslag/kulturer  
- ✅ Integrera smidigt med befintlig Discord Bot
- ✅ Vara robust och felhanterande i production