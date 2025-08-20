# EON TableProcessor - Analys av Befintliga Tabellstrukturer

## Befintliga Tabeller - Inventering

### 📋 Bakgrundstabeller (Karaktärsskapande)
- `huvudbakgrund.json` - Huvudtabell för bakgrundssekvens
- `mental_traits.json` - Mentala egenskaper 
- `physical_traits.json` - Fysiska egenskaper
- `social_traits.json` - Sociala egenskaper
- `disadvantages.json` - Nackdelar
- `supernatural_trait.json` - Övernaturliga förmågor
- `background_tables.json` - Allmänna bakgrundstabeller

### 🏠 Familjetabeller (`familj/`)
- `familj_ovr.json` - Familjeöversikt
- `huvudnaring.json` - Huvudnäring generell
- `huvudnäring_civ_adlig.json` - Adlig huvudnäring
- `huvudnäring_civ_hamnstad.json` - Hamnstad huvudnäring

### 🍽️ Bordstabeller (`bord/`)
- `bord_asharier.json` - Asharisk bordstradition
- `bord_cirefalier.json` - Cirefalisk bordstradition
- `bord_ovr_civ.json` - Civiliserad övrig bordstradition
- `bord_primitiva.json` - Primitiv bordstradition
- `bord_thalask.json` - Thalaskisk bordstradition

### 🌍 Folkslag & Kulturer (`folkslag/`)
- `attribute_modifiers.json` - Attributmodifierare per folkslag
- `humans/` - Textfiler för alla humantyper:
  - adasier.txt, aunurier.txt, auser.txt, cirefalier.txt, darkener.txt
  - kamor.txt, kragg.txt, lalaster.txt, rauner.txt, tauper.txt
  - tokon.txt, tosher.txt, vanarer.txt, veddo.txt, zhaner.txt

### 📍 Länder & Hemort (`landerhemort/`)
**Textfiler för alla länder/regioner:**
- Alarinn.txt, Asharien.txt, Colonan.txt, Consaber.txt, Damarien.txt
- Det_cirefaliska_samväldet.txt, Dhurkoor.txt, Drunok.txt
- Ebhron.txt, Eumo.txt, Eyrenskogarna.txt, Forion.txt
- Jargiska_Kejsardömet.txt, Kamor.txt, Kinanne_an_Oro.txt
- [+25 fler länder/regioner]

### 📜 Händelsetabeller (`handelser/`)
- `alver_hand.json` - Alv-specifika händelser
- `ovriga_handelser.json` - Allmänna händelser
- `thalask_atte.json` - Thalaskisk ätt
- `thalask_hand.json` - Thalaskisk händelser

### 💰 Övriga Tabeller
- `agodelar.json` - Ägodelar
- `egenheter.json` - Personliga egenheter
- `field_storning.json` - Fältstörning (magisk)
- `formogenhet.json` - Förmögenhet
- `random_hemort_folkslag.json` - Slumpmässig hemort baserat på folkslag

## 📊 Analysresultat - Identifierade Patterns

### A) Grundstrukturer ✅ ANALYSERAD

#### Pattern 1: Hierarkisk Struktur
**Förekommer i:** huvudbakgrund.json, mental_traits.json, alla bakgrundstabeller
**Struktur:**
```json
{
  "bakgrundstabeller": {
    "huvudtabell": {
      "titel": "Huvudbakgrundstabellen",
      "beskrivning": "...",
      "dice": "1d100",
      "ranges": {
        "1-2": {"result": "börd", "description": "..."},
        "3-15": {"result": "föremål_ägodelar", "description": "..."}
      }
    }
  }
}
```
**Användning:** Standard tabellformat för alla bakgrundstabeller
**TableProcessor support:** ✅ Behöver grundläggande range-matching

#### Pattern 2: Range Definitions
**Förekommer i:** Alla JSON-tabeller
**Format:** `"1-2"`, `"3-15"`, `"26-45"`, `"100"`
**Användning:** Definierar tärningsresultat-intervall
**TableProcessor support:** ✅ Standard range parsing

#### Pattern 3: Dice Notation
**Förekommer i:** Alla tabeller, skill bonuses
**Format:** `"1d100"`, `"1d6+1"`, `"2T6"`, `"ob2T6"`
**Användning:** Definierar vilket tärningsslag som ska göras
**TableProcessor support:** ✅ Behöver robust dice parser (redan har!)

### B) Avancerade Features ✅ ANALYSERAD

#### Pattern 4: Roll Twice Mechanics
**Förekommer i:** mental_traits.json (99-100), familj_ovr.json (100)
**Struktur:**
```json
"99-100": {
  "result": "fler_egenskaper",
  "description": "Slå två gånger till på denna tabell och använd båda resultaten."
}
```
**Användning:** Genererar flera resultat från samma tabell
**TableProcessor support:** ⚠️ Behöver specialhantering för "roll twice" logic

#### Pattern 5: Conditional Logic
**Förekommer i:** alver_hand.json (rad 135-144)
**Struktur:**
```json
"90-92": {
  "result": "tvilling_conditional",
  "description": "När du föddes...",
  "conditions": {
    "henea": {
      "result": "tvilling_henea", 
      "description": "Din döda tvillings själ..."
    },
    "not_henea": {
      "result": "tvilling_not_henea",
      "description": "Din dödfödda tvilling..."
    }
  }
}
```
**Användning:** Olika resultat baserat på karaktärens folkslag/egenskaper
**TableProcessor support:** ⚠️ Behöver context-aware conditional evaluation

#### Pattern 6: Subtable Strukturer  
**Förekommer i:** familj_ovr.json (rad 14-35)
**Struktur:**
```json
"26-29": {
  "result": "adopted",
  "description": "Rollpersonen är adopterad.",
  "has_subtable": true,
  "subtable": {
    "dice": "1d100",
    "ranges": {
      "1-20": {"result": "...", "description": "..."}
    }
  }
}
```
**Användning:** Nested tabeller för detaljerade resultat
**TableProcessor support:** ✅ Recursive table resolution

#### Pattern 7: Skill Bonuses
**Förekommer i:** mental_traits.json (genomgående)
**Struktur:** Inbäddat i descriptions
- `"Du får 1T6+4 enheter att spendera på färdigheten etikett"`
- `"ALLA kunskapsfärdigheter blir lättlärda"`
- `"Öka RPs bildning med +2"`
**Användning:** Ger färdighetspoäng och attributförändringar
**TableProcessor support:** ⚠️ Behöver text parsing för benefits extraction

### C) Special Cases ✅ ANALYSERAD

#### Pattern 8: Attributmodifierare per Folkslag
**Förekommer i:** attribute_modifiers.json
**Struktur:**
```json
{
  "människor": {
    "adasier": {"STY": -2, "TÅL": 3, "RÖR": 2, "PER": -1},
    "cirefalier": {"PER": 1, "BIL": 1, "HÖR": -2}
  },
  "alver": {
    "henea": {"STY": -2, "TÅL": -1, "RÖR": 3}
  }
}
```
**Användning:** Attributmodifiering baserat på folkslag och subtyp
**TableProcessor support:** ✅ Direct lookup by folkslag key

#### Pattern 9: Textfiler för Beskrivningar
**Förekommer i:** folkslag/humans/, landerhemort/
**Format:** Plain text files (.txt)
**Användning:** Detaljerade beskrivningar av kulturer och länder
**TableProcessor support:** ✅ Text file reading

#### Pattern 10: Cross-References
**Förekommer i:** huvudbakgrund.json → andra tabeller
**Usage:** `"result": "mentala_egenskaper"` pekar på mental_traits.json
**TableProcessor support:** ⚠️ Behöver table lookup och navigation

## 🔍 Gap-Analys - Vad TableProcessor Behöver

### ✅ Redan Stöds
1. Hierarkisk struktur navigation
2. Range-based dice resolution  
3. Dice notation parsing (har robust parser)
4. Subtable recursion
5. Attributmodifier lookup
6. Text file reading

### ⚠️ Behöver Implementation/Förbättring
1. **Roll Twice Mechanics**: Automatisk multiple rolls
2. **Conditional Logic**: Context-aware evaluation (henea vs not_henea)
3. **Skill Bonus Parsing**: Extrahera färdighetspoäng från descriptions
4. **Cross-Table References**: Automatisk navigation mellan tabeller
5. **Swedish Dice Notation**: `ob2T6`, `2T6` support
6. **Benefit Extraction**: Parsa descriptions för bonuses

### 🚨 Kritiska Saknade Features
1. **CharacterContext Integration**: Folkslag/kultur-awareness för conditionals
2. **Benefit System**: Strukturerad hantering av skill/attribute bonuses  
3. **Table Cache**: Performance för stora hierarchier
4. **Error Recovery**: Robust felhantering för missing references

## 🎯 Nästa Steg - Prioriterat

1. ✅ Komplett strukturanalys klar
2. 🔄 **PÅGÅR:** Validera befintlig TableProcessor implementation
3. ⏳ Implementera saknade features (conditionals, roll twice, benefits)
4. ⏳ Skapa comprehensive testing suite

## 📝 Validering av Befintlig TableProcessor

### ✅ Stöds Redan (Bra Implementation!)

1. **✅ Hierarkisk Navigation** - `roll_on_table()` med `subtable_name` parameter
2. **✅ Range Matching** - `_value_in_range()` hanterar "1-25" och "100" format
3. **✅ Dice Rolling** - `_roll_dice()` med regex parsing för "1d100", "2d6+3"
4. **✅ Subtable Recursion** - `has_subtable` och `subtable` hantering
5. **✅ Conditional Logic** - `_resolve_conditionals()` och `_check_condition()`
6. **✅ Context Awareness** - `CharacterContext` för folkslag/kultur
7. **✅ Data Loading** - Automatisk laddning av JSON och textfiler
8. **✅ Error Handling** - Robust felhantering med exceptions

### ⚠️ Partiellt Stöd (Behöver Förbättring)

1. **⚠️ Roll Twice Mechanics** - Grundläggande stöd men inte pattern-specifik
   - **Nuvarande:** Hårdkodat för `result == 'roll_twice'`
   - **Behöver:** Pattern matching för "slå två gånger till på denna tabell"

2. **⚠️ Swedish Dice Notation** - Stöder "1d100" men inte "ob2T6", "2T6"
   - **Saknas:** EON-specifika format som `ob2T6`, `1T6+4` enheter

3. **⚠️ Cross-Table References** - Partiellt i `roll_background_sequence()`
   - **Behöver:** Automatisk lookup av `"result": "mentala_egenskaper"` → `mental_traits.json`

### ❌ Saknas Helt (Kritiska Gaps)

1. **❌ Skill Bonus Parsing** - Ingen text parsing för benefits
   - **Exempel:** `"Du får 1T6+4 enheter att spendera på färdigheten etikett"`
   - **Behöver:** Regex parsing för att extrahera færdighetspoäng

2. **❌ Benefit Extraction System** - Ingen strukturerad hantering
   - **Exempel:** `"Öka RPs bildning med +2"`, `"ALLA kunskapsfärdigheter blir lättlärda"`
   - **Behöver:** Strukturerad `BenefitParser` klass

3. **❌ Advanced Conditional Patterns** - Endast enkla folkslag-checks
   - **Saknas:** `"henea"` vs `"not_henea"` från `alver_hand.json`
   - **Behöver:** Utökade condition checks för alvlinjer

4. **❌ Table Caching** - Laddar om data varje gång
   - **Performance:** Ineffektivt för många simultanea användare
   - **Behöver:** Singleton pattern eller cache system

5. **❌ Multiple Roll Results** - Hanterar bara "roll twice"
   - **Saknas:** `"Fler egenskaper. Slå två gånger till på denna tabell och använd båda resultaten."`
   - **Behöver:** Flexibel "roll N times" mechanics

### 📊 Compatibility Score: 7/10

**Starkt fundament** med bra arkitektur, men behöver utökas för full EON-kompatibilitet.

## 🚨 Kritiska Implementationsgaps

### 1. **Conditional Logic Utökning**
Nuvarande conditions täcker inte alv-linjer som `henea`, `not_henea`:
```python
# SAKNAS i _check_condition():
elif condition_key == "henea":
    return context.stam == "henea"  # Behöver alv-linje support
elif condition_key == "not_henea":
    return context.stam != "henea"
```

### 2. **Skill Parsing System**
```python
# BEHÖVS: BenefitParser klass
class BenefitParser:
    def extract_benefits(self, description: str) -> List[Benefit]:
        # Parse "Du får 1T6+4 enheter att spendera på färdigheten etikett"
        # Parse "Öka RPs bildning med +2" 
        # Parse "ALLA kunskapsfärdigheter blir lättlärda"
```

### 3. **Swedish Dice Support** 
```python
# BEHÖVS i _roll_dice():
# Support för "ob2T6", "2T6" notation
if 'ob' in dice_str or 't6' in dice_str.lower():
    return self._roll_eon_dice(dice_str)
```

### 4. **Dynamic Table Resolution**
```python
# BEHÖVS: Auto-resolve cross-references
def resolve_table_reference(self, result_key: str, context: CharacterContext):
    table_mapping = {
        'mentala_egenskaper': 'mental_traits',
        'händelser': self._get_events_table_for_race(context.folkslag)
    }
```