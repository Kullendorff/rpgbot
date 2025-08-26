# Step Migration Pattern - Refaktorering av interactive_chargen.py

## Migrationsmönster

Detta dokument beskriver det etablerade mönstret för att migrera steg från den monolitiska `interactive_chargen.py` till separata moduler.

## Exempel: Gender Step Migration

### 1. Skapa ny step-modul

**Fil:** `src/character_creation/steps/[step_name].py`

```python
from .base_step import BaseStep

class [StepName]Step(BaseStep):
    def __init__(self, embed_factory):
        super().__init__(step_name="[step_key]", step_number=[N])
        self.embed_factory = embed_factory
        # Step-specifik initialisering
    
    async def execute(self, ctx, session):
        # Visa step UI
        embed = self.embed_factory.admin_message(...)
        await ctx.send(embed=embed)
        return embed
    
    async def handle_input(self, ctx, session, input_text, *args):
        # Hantera användarinput
        # Returnera (success: bool, error_msg: Optional[str])
        return True, None
    
    def validate_prerequisites(self, session):
        # Validera förutsättningar
        return True, None
```

### 2. Uppdatera interactive_chargen.py

#### 2.1 Lägg till import
```python
from character_creation.steps.[step_name] import [StepName]Step
```

#### 2.2 Initiera i __init__
```python
def __init__(self, embed_factory, data_dir=None):
    # ...
    self.[step_name]_step = [StepName]Step(self.embed_factory)
    # ...
```

#### 2.3 Uppdatera step-metoder
```python
async def step_[name](self, ctx, session):
    """Steg N: [Beskrivning] - använder ny modul"""
    await self.[step_name]_step.execute(ctx, session)

async def handle_[key]_input(self, ctx, session, input_text, *args):
    """Hanterar input för [step]-steget - använder ny modul"""
    success, error = await self.[step_name]_step.handle_input(ctx, session, input_text, *args)
    
    if success:
        session.update_context()
        self.save_session(session)
        self.next_step(session)
        await self.show_current_step(ctx, session)
```

## Checklista för varje steg

- [ ] Identifiera all kod relaterad till steget
  - [ ] `step_[name]` metod
  - [ ] `handle_[key]_input` metod
  - [ ] Hjälpmetoder specifika för steget
  - [ ] Data/konstanter specifika för steget

- [ ] Skapa ny step-modul
  - [ ] Ärv från BaseStep
  - [ ] Implementera alla abstrakta metoder
  - [ ] Flytta step-specifik logik
  - [ ] Lägg till valideringslogik
  - [ ] Lägg till hjälpmetoder (get_summary, get_help_text)

- [ ] Uppdatera interactive_chargen.py
  - [ ] Import av ny modul
  - [ ] Initiera i __init__
  - [ ] Ersätt gamla metoder med anrop till modulen
  - [ ] Behåll backwards compatibility

- [ ] Testa
  - [ ] Import fungerar
  - [ ] Step visas korrekt
  - [ ] Input hanteras korrekt
  - [ ] Nästa steg triggas
  - [ ] Data sparas i session

## Fördelar med mönstret

1. **Separation of Concerns** - Varje steg är isolerat
2. **Testbarhet** - Kan testa varje steg separat
3. **Återanvändbarhet** - Steps kan användas i andra kontexter
4. **Läsbarhet** - Mindre, fokuserade filer
5. **Underhållbarhet** - Enklare att hitta och fixa buggar

## Nästa steg att migrera (i ordning)

### Enkla steg (börja här):
1. ✅ Gender (kön) - KLAR
2. Age (ålder) - ~100 rader
3. Culture (kultur) - ~150 rader

### Medelkomplexa steg:
4. Homeland (hemland) - ~200 rader
5. Attributes (attribut) - ~200 rader
6. Parents (föräldrar) - ~100 rader

### Komplexa steg:
7. Race (folkslag) - ~400 rader, inkluderar Thalamur-special
8. Special Rules (specialregler) - ~250 rader, Cirefalier-special
9. Character Traits (karaktärsdrag) - ~300 rader
10. Family Background (familjebakgrund) - ~800 rader
11. Background Events (bakgrundshändelser) - ~700 rader

### Speciella fall:
- **Thalamur citizenship** - Separat handler-modul
- **Cirefalier field störningar** - Separat handler-modul
- **Ätt-baserad placering** - Del av background-modulen

## Tips för migration

1. **Börja med enkla steg** för att etablera mönstret
2. **Testa efter varje steg** för att säkerställa inget går sönder
3. **Dokumentera specialfall** direkt i koden
4. **Behåll session-kompatibilitet** så gamla sessioner fungerar
5. **Gör en commit efter varje lyckad migration**

## Gemensam funktionalitet att extrahera

När flera steg är migrerade, extrahera gemensam funktionalitet till:

- `formatters/embed_builder.py` - Standardiserad embed-skapning
- `handlers/input_validator.py` - Gemensam input-validering
- `handlers/dice_handler.py` - Tärningsslag för attribut etc.
- `data/table_loader.py` - Centraliserad tabell-laddning
- `utils/name_generator.py` - Namngenererering för familj etc.

## Estimerad tidsåtgång

- **Enkelt steg:** 30-60 minuter
- **Medelkomplext steg:** 1-2 timmar
- **Komplext steg:** 2-4 timmar
- **Total refaktorering:** 12-15 arbetsdagar

## Rollback-strategi

Om något går fel:
1. Git revert till senaste working commit
2. Återställ från `backup_chargen_refactoring_[datum]/`
3. Ta bort nya filer i `src/character_creation/`
4. Återställ gamla imports i `interactive_chargen.py`