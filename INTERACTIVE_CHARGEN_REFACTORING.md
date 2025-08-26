# Interactive Character Generator - Refaktoreringsplan

## Problem
`interactive_chargen.py` har vuxit till **4111 rader** med **124 metoder** i en enda fil. Detta gör koden:
- Svår att navigera och förstå
- Omöjlig att testa isolerat
- Svår att underhålla och debugga
- Problematisk för parallell utveckling
- Svår att utöka för nya raser

## Mål
Dela upp den monolitiska filen i en modulär arkitektur som är:
- Lätt att förstå och navigera
- Enkel att testa och underhålla
- Flexibel för nya raser och funktioner
- Följer Single Responsibility Principle
- Behåller full backwards compatibility

## Föreslagen Arkitektur

```
src/character_creation/
├── __init__.py                    # Package initialization
├── session.py                     # CharacterSession class (~60 rader)
├── creator.py                     # InteractiveCharacterCreator (orchestrator, ~200 rader)
│
├── steps/                         # Varje steg som egen modul
│   ├── __init__.py
│   ├── base_step.py              # Abstrakt basklass för alla steg
│   ├── gender.py                 # Steg 1: Kön (~100 rader)
│   ├── homeland.py               # Steg 2: Hemland (~200 rader)
│   ├── race.py                   # Steg 3: Folkslag (~400 rader)
│   ├── age.py                    # Steg 4: Ålder (~100 rader)
│   ├── culture.py                # Steg 5: Kultur (~150 rader)
│   ├── attributes.py             # Steg 6: Attribut (~200 rader)
│   ├── special_rules.py          # Steg 7: Specialregler (~250 rader)
│   ├── traits.py                 # Steg 8: Karaktärsdrag (~300 rader)
│   ├── family.py                 # Steg 9-11: Familj (~800 rader)
│   ├── background.py             # Steg 12-14: Bakgrund (~700 rader)
│   └── summary.py                # Steg 15: Sammanfattning (~200 rader)
│
├── generators/                    # Genereringsfunktioner
│   ├── __init__.py
│   ├── family_generator.py       # Familjegenereringssystem
│   ├── trait_generator.py        # Karaktärsdragsgenerering
│   ├── background_generator.py   # Bakgrundshändelser
│   └── attribute_generator.py    # Attributslagning
│
├── handlers/                      # Input-hantering och specialfall
│   ├── __init__.py
│   ├── input_validator.py        # Validering av användarinput
│   ├── dice_handler.py           # Tärningsslag-hantering
│   ├── thalamur_handler.py       # Thalamur speciallogik
│   ├── cirefalier_handler.py     # Cirefalier field störningar
│   └── race_specific_handler.py  # Övrig rasspecifik logik
│
├── formatters/                    # Formattering och presentation
│   ├── __init__.py
│   ├── embed_builder.py          # Discord embed-skapande
│   ├── text_formatter.py         # Textformattering
│   ├── table_formatter.py        # Tabellformattering
│   └── summary_builder.py        # Sammanfattningar
│
├── data/                          # Data-access layer
│   ├── __init__.py
│   ├── table_loader.py           # Ladda JSON-tabeller
│   ├── file_loader.py            # Ladda textfiler
│   ├── cache_manager.py          # Cache för ofta använd data
│   └── constants.py              # Konstanter och konfiguration
│
└── utils/                         # Hjälpfunktioner
    ├── __init__.py
    ├── dice_roller.py             # Tärningsslag
    ├── name_generator.py          # Namngenererering
    └── age_calculator.py          # Åldersberäkningar

```

## Detaljerad Modullbeskrivning

### Core Modules

#### `session.py`
- `CharacterSession` klass
- Session state management
- Data persistence
- Session validation

#### `creator.py`
- `InteractiveCharacterCreator` huvudklass
- Step orchestration
- Session lifecycle management
- Command registration med Discord

### Steps Modules

#### `base_step.py`
```python
from abc import ABC, abstractmethod

class BaseStep(ABC):
    """Abstrakt basklass för alla karaktärsskapandesteg"""
    
    @abstractmethod
    async def execute(self, ctx, session):
        """Kör steget"""
        pass
    
    @abstractmethod
    async def handle_input(self, ctx, session, input_text):
        """Hantera användarinput för steget"""
        pass
    
    @abstractmethod
    def validate(self, session):
        """Validera att steget kan köras"""
        pass
```

#### Steg-specifika moduler
Varje steg-modul innehåller:
- Steg-specifik logik
- Input-hantering
- Validering
- Embed-generering
- Integration med relevanta generators/handlers

### Generators Modules

#### `family_generator.py`
- `generate_complete_family_system()`
- Rasspecifik familjegenerering
- Föräldragenerering
- Syskon och släktingar
- Familjeegenskaper

#### `background_generator.py`
- Bakgrundshändelser
- Tabellslag
- Undertabellhantering
- Villkorad händelsehantering

### Handlers Modules

#### `thalamur_handler.py`
Specialhantering för Thalamur:
- Citizenship val
- Ätt-system
- Medborgare vs Folket
- Attributmodifierare

#### `race_specific_handler.py`
Generell rashantering:
- Alver: Hushåll, mentorer, ålder
- Dvärgar: Klaner, dvärgfäst, samhällsklass
- Tiraker: Kullar, stammar, klanstrukturer

### Data Access Layer

#### `table_loader.py`
- Centraliserad JSON-laddning
- Lazy loading
- Error handling för saknade tabeller
- Tabellvalidering

#### `cache_manager.py`
- Cache ofta använd data
- Minska fil-I/O
- Session-specifik cache
- TTL-hantering

## Implementation Plan

### Fas 1: Förberedelser (Dag 1)
1. **Skapa mappstruktur**
   - Skapa alla mappar enligt arkitekturen
   - Skapa tomma `__init__.py` filer
   - Skapa README i varje mapp

2. **Skapa base classes**
   - Implementera `BaseStep` abstrakt klass
   - Skapa grundläggande test framework
   - Sätt upp logging

3. **Extrahera CharacterSession**
   - Flytta `CharacterSession` till `session.py`
   - Uppdatera imports
   - Verifiera att inget går sönder

### Fas 2: Migration av enkla steg (Dag 2-3)
Börja med de enklaste stegen för att etablera mönstret:

1. **Migrera gender.py**
   - ~100 rader kod
   - Enkel logik
   - Bra test case

2. **Migrera age.py**
   - ~100 rader kod
   - Tydlig avgränsning
   - Validering av mönstret

3. **Migrera culture.py**
   - ~150 rader kod
   - Testar table loading

### Fas 3: Migration av komplexa steg (Dag 4-7)
1. **Migrera race.py**
   - Mest komplex logik
   - Thalamur specialfall
   - ~400 rader

2. **Migrera family.py**
   - Stor modul (~800 rader)
   - Kan behöva delas ytterligare
   - Mycket generering

3. **Migrera background.py**
   - Komplex tabellhantering
   - ~700 rader
   - Många undertabeller

### Fas 4: Extrahera gemensam funktionalitet (Dag 8-9)
1. **Skapa generators**
   - Extrahera genereringsfunktioner
   - Skapa enhetliga interfaces
   - Dokumentera

2. **Skapa handlers**
   - Centralisera specialfallshantering
   - Skapa återanvändbar kod
   - Testa isolerat

3. **Skapa formatters**
   - Standardisera embed-skapande
   - Enhetlig textformattering
   - Konsekvent presentation

### Fas 5: Integration och testning (Dag 10-11)
1. **Integration testing**
   - End-to-end test av hela flödet
   - Verifiera alla steg fungerar
   - Performance testing

2. **Backwards compatibility**
   - Säkerställ gamla kommandon fungerar
   - Migration av aktiva sessioner
   - Fallback-hantering

### Fas 6: Optimering och cleanup (Dag 12)
1. **Kod-cleanup**
   - Ta bort gamla filen
   - Uppdatera imports överallt
   - Rensa unused code

2. **Dokumentation**
   - Uppdatera README
   - Skapa developer guide
   - API dokumentation

## Testning

### Unit Tests
Varje modul ska ha egen test-fil:
```
tests/character_creation/
├── test_session.py
├── test_creator.py
├── steps/
│   ├── test_gender.py
│   ├── test_homeland.py
│   └── ...
├── generators/
│   ├── test_family_generator.py
│   └── ...
└── handlers/
    ├── test_thalamur_handler.py
    └── ...
```

### Integration Tests
- Full karaktärsskapande-flöde
- Rasspecifika test cases
- Error handling scenarios
- Performance benchmarks

## Fördelar

### Utveckling
- **Modularitet**: Varje del kan utvecklas isolerat
- **Testbarhet**: Enklare att skriva och köra tester
- **Läsbarhet**: Mindre filer är lättare att förstå
- **Parallell utveckling**: Flera utvecklare kan jobba samtidigt

### Underhåll
- **Debuggning**: Lättare att hitta och fixa buggar
- **Refaktorering**: Mindre risk att påverka andra delar
- **Dokumentation**: Varje modul kan dokumenteras separat
- **Versionshantering**: Tydligare commits och historik

### Prestanda
- **Lazy loading**: Ladda bara nödvändiga moduler
- **Caching**: Centraliserad cache-hantering
- **Optimering**: Lättare att optimera specifika delar

### Utbyggbarhet
- **Nya raser**: Lägg till i relevanta moduler
- **Nya steg**: Skapa ny step-modul
- **Nya features**: Tydligt var kod ska läggas

## Risker och Mitigering

### Risk 1: Breaking Changes
**Mitigering**: 
- Omfattande testning innan varje fas
- Behåll gamla filen som backup
- Gradvis migration med feature flags

### Risk 2: Performance Degradation
**Mitigering**:
- Benchmark före och efter
- Profile kritiska delar
- Optimera efter behov

### Risk 3: Lost Functionality
**Mitigering**:
- Detaljerad genomgång av all kod
- Checklist för alla funktioner
- User acceptance testing

## Success Criteria

Refaktoreringen är lyckad när:
1. ✅ All funktionalitet bevarad
2. ✅ Ingen performance degradation
3. ✅ 80%+ test coverage
4. ✅ Alla raser fungerar
5. ✅ Kod är modulär och DRY
6. ✅ Dokumentation uppdaterad
7. ✅ Inga kända buggar
8. ✅ Utvecklare kan enkelt hitta och förstå kod

## Nästa Steg för Ras-implementation

Med denna struktur blir ras-implementation mycket enklare:

### Alver
1. Uppdatera `steps/race.py` med alv-logik
2. Lägg till i `generators/family_generator.py`:
   - Hushåll-system
   - Mentor-generering
3. Skapa `handlers/elf_handler.py`:
   - Åldershantering (200-800 år)
   - Osäker födelsetidpunkt

### Dvärgar
1. Uppdatera `steps/race.py` med dvärg-logik
2. Lägg till i `generators/family_generator.py`:
   - Klan-system
   - Dvärgfäst-boende
3. Skapa `handlers/dwarf_handler.py`:
   - Samhällsklass
   - Klan-specifik logik

### Tiraker
1. Uppdatera `steps/race.py` med tirak-logik
2. Lägg till i `generators/family_generator.py`:
   - Kull-system
   - Stam-strukturer
3. Skapa `handlers/tirak_handler.py`:
   - Klan-hantering
   - Kulturspecifik logik

## Tidsuppskattning

- **Total tid**: 12-15 arbetsdagar
- **Fas 1-2**: 3 dagar (grundstruktur)
- **Fas 3-4**: 6 dagar (migration)
- **Fas 5-6**: 3 dagar (integration och cleanup)
- **Buffer**: 3 dagar för oförutsedda problem

## Konklusion

Denna refaktorering kommer att transformera en ohanterlig 4000+ raders fil till en välorganiserad, modulär arkitektur som är lätt att underhålla, testa och utöka. Det är ett nödvändigt steg innan vi kan effektivt implementera stöd för icke-mänskliga raser.