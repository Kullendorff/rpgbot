# EON Discord Bot - Slash Command Konvertering
## Del 1: Förberedelser & Dice Commands

---

## 🎯 Översikt

Detta är en instruktionsguide för att migrera EON Discord Bot från prefix-kommandon till slash-kommandon. Guiden är uppdelad i tre delar för säker och systematisk migration.

**Mål:** Konvertera alla `!kommando` till `/kommando` med förbättrad UX och bibehållen funktionalitet.

---

## ⚠️ Kritiska Förberedelser

### 1. Säkerhetsåtgärder FÖRST

**Skapa omfattande backup:**
- Kopiera HELA `src/` mappen till `backup_[datum]/`
- Kopiera `main.py` till `main_backup.py`
- Skapa git commit med beskrivande meddelande
- Dokumentera nuvarande bot-version och dependencies

**Varför:** Om något går fel måste du kunna återställa snabbt.

### 1.5 Verifiera Embed Factory

**FÖRUTSÄTTNING:** Embed standardisering är genomförd enligt `eon_embed_standardization.md`

**Kontrollera att följande finns:**
- `src/core/embed_factory.py` existerar och fungerar
- Alla prefix commands använder redan embed factory
- Inga `discord.Embed()` anrop finns utanför factory
- Visual konsistens är verifierad

### 2. Analysera befintlig kod

**Studera följande filer noggrant INNAN du börjar:**

1. **`src/commands/dice_commands.py`**
   - Förstå hur `*args` parsas till parametrar
   - Notera alla flags som `--de`, `--ryttare`
   - Identifiera special cases (Umnatak handling, demon inspiration)

2. **`src/main.py`**
   - Hitta var slash commands clearas (MÅSTE tas bort)
   - Förstå hur commands registreras nu
   - Notera alla dependencies som skickas till commands

3. **`src/core/`** moduler
   - Förstå dice_parser, dice_engine strukturen
   - Notera constants som MAX_DICE, MAX_SIDES

### 3. Skapa testmiljö

**Sätt upp separat test-bot:**
- Använd ANNAN bot token för testning
- Skapa test-server med bara dig som medlem
- Aktivera alla Intents och Permissions
- Logga ALLT under testning

---

## 🏗️ Implementation Strategy

### Fas 1: Setup Migration Framework

#### 1.1 Ta bort slash clearing

**I `main.py`, hitta och RADERA:**
```python
# Leta efter något som:
bot.tree.clear_commands(guild=None)
await bot.tree.sync()
print('Cleared all slash commands...')
```

**Varför:** Detta blockerar alla slash commands!

#### 1.2 Skapa migration helper

**Skapa ny fil `src/migration/helper.py` med:**

- **Klass för säker migration** som hanterar:
  - Logging av både gamla och nya kommandon
  - Felhantering och rollback-möjlighet
  - Performance monitoring
  - Feature flags för gradvis aktivering
  - Integration med embed_factory

- **Smart defer handler** som:
  - Automatiskt använder defer() för långsamma operationer
  - Ger användaren feedback vid väntetider
  - Hanterar Discord's 3-sekunder timeout korrekt

- **Parameter converter** som:
  - Konverterar `*args` strings till strukturerade parametrar
  - Mappar gamla flags (`--de`) till booleans (`demon=True`)
  - Validerar input med Discord's inbyggda validators

#### 1.3 Implementera feature flags

**Skapa `config/feature_flags.py`:**
- Flag för varje command-grupp (dice, combat, admin, etc.)
- Möjlighet att köra dual mode (både prefix och slash)
- Per-command enable/disable för testing

**Användning:**
```python
if FEATURE_FLAGS['slash_dice_enabled']:
    # Registrera slash dice commands
```

---

## 🎲 Fas 2: Dice Commands Migration

### Steg-för-steg instruktioner:

#### 2.1 Skapa `src/commands/slash_dice_commands.py`

**Struktur att följa:**

1. **Använd commands.GroupCog** för bättre organisation
2. **Inkludera embed_factory** som dependency i constructor
3. **Implementera varje dice command** med följande ändringar:

**För `/roll` kommandot:**
- **Parameter mapping:**
  - `*args` → `dice: str`, `target: Optional[int]`, `demon: Optional[bool]`
  - Använd `app_commands.Range[int, 1, 100]` för target validering
  - `--de` flag → `demon: bool` parameter

- **Embed creation:**
  - ANVÄND: `embed_factory.dice_result()` 
  - ALDRIG: `discord.Embed()` direkt
  - Skicka rätt parametrar till factory method

- **Behåll exakt logik för:**
  - Demon inspiration manipulation
  - Umnatak special handling  
  - Roll tracking för statistik

**För `/ex` kommandot:**
- Validera att endast d6 används (ge tydligt fel annars)
- Behåll unlimited dice explosion mechanics
- Markera perfekt (alla 6:or) och fummel (alla 1:or)

**För `/count` kommandot:**
- Target parameter är OBLIGATORISK (inte optional som i prefix)
- Visa visuell representation av framgångar
- Hantera stora dice pools effektivt

**För `/chance` kommandot:**
- **MÅSTE använda defer()** - Detta tar alltid >3 sekunder
- Lägg till progress feedback för användaren
- Visa resultat som både procent och odds

#### 2.2 Registrera commands korrekt

**I `main.py` on_ready():**

1. **Import slash commands** (men behåll prefix imports om dual mode)
2. **Registrera med rätt dependencies:**
   ```python
   # Se till att skicka roll_tracker, color_handler, embed_factory, knowledge_base
   # embed_factory MÅSTE inkluderas för alla slash commands
   ```
3. **Synka EN gång i slutet:**
   ```python
   synced = await bot.tree.sync()
   print(f"Synced {len(synced)} slash commands")
   ```

#### 2.3 Implementera autocomplete

**För dice notation autocomplete:**
- Föreslå vanliga EON-kombinationer (3d6, 4d6, etc.)
- Filtrera baserat på vad användaren skriver
- Max 25 förslag (Discord limit)

---

## 🧪 Testprotokoll

### Obligatoriska tester innan nästa fas:

#### Grundfunktionalitet:
- [ ] `/roll dice:3d6` - Grundläggande slag fungerar
- [ ] `/roll dice:3d6+2 target:15` - Modifierare och target
- [ ] Autocomplete föreslår rätt alternativ
- [ ] Felmeddelanden är på svenska och hjälpsamma

#### Special cases:
- [ ] Demon inspiration kräver GM roll
- [ ] Umnatak får sarkastiska kommentarer
- [ ] Stora dice pools (50+ tärningar) hanteras

#### Error handling:
- [ ] Ogiltig notation ger tydligt fel
- [ ] För stora värden respekterar MAX_DICE/MAX_SIDES
- [ ] Timeout hanteras gracefully

#### Backwards compatibility:
- [ ] `!roll 3d6` fungerar fortfarande (om dual mode)
- [ ] Statistik trackas för båda systemen
- [ ] Ingen konflikt mellan prefix och slash

### Performance krav:
- **Instant response (<500ms):** roll, ex, count
- **Använd defer() (>3s):** chance, alla AI operations
- **Ingen timeout:** Alla kommandon ska svara inom 45s

---

## 🚨 Vanliga Problem och Lösningar

### Problem 1: "Interaction failed"
**Orsak:** Tar >3 sekunder utan defer()
**Lösning:** Använd defer() för alla operationer som kan ta tid

### Problem 2: Commands syns inte i Discord
**Orsak:** Sync misslyckades eller permissions fel
**Lösning:** 
- Kontrollera bot.tree.sync() körs
- Verifiera bot har applications.commands scope
- Vänta upp till 1 timme (Discord cache)

### Problem 3: "Missing Access"
**Orsak:** Bot saknar permissions
**Lösning:** Re-invite bot med korrekta permissions

### Problem 4: Slash commands fungerar inte i DMs
**Orsak:** Guild-specific commands
**Lösning:** Använd global commands (guild=None)

---

## ✅ Checklista innan Del 2

**Tekniskt:**
- [ ] Backup skapad och verifierad
- [ ] Migration helper implementerad och testad
- [ ] Feature flags fungerar
- [ ] Alla dice commands migrerade
- [ ] Autocomplete implementerad
- [ ] Error handling testad

**Funktionellt:**
- [ ] Alla dice commands ger samma resultat som prefix
- [ ] Special cases (demon, Umnatak) fungerar
- [ ] Performance är acceptabel
- [ ] Användare kan hitta commands lätt

**Dokumentation:**
- [ ] Loggning visar vad som händer
- [ ] Rollback-plan dokumenterad
- [ ] Test-resultat sparade

---

## 📊 Förväntade Förbättringar

Efter korrekt implementation ska du se:
- **50% färre user errors** (tack vare type validation)
- **Bättre discoverability** (autocomplete hjälper användare)
- **Snabbare response** (ingen string parsing)
- **Mer konsistent UX** (Discord hanterar UI)

---

## Nästa Steg

När Del 1 är klar och alla tester passerar:
1. Låt test-användare prova i 24 timmar
2. Samla feedback och justera
3. Fortsätt till Del 2 (Knowledge, Combat & Utility Commands)