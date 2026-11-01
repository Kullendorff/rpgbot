# GEMINI.md — Antigravity Workspace Rules & Claude Context Bridge

Denna fil kompletterar `AGENTS.md` så att Antigravity får tillgång till all uppdaterad arkitektur, regler och kontext från `CLAUDE.md`, `CURRENT_STATE.md` och `.claude/memory/learnings.md` utan att några befintliga filer tas bort eller skrivs över.

## Viktiga Kontextfiler i Projektet

Vid arbete i detta repo, konsultera vid behov:
- `CLAUDE.md` — Den mest uppdaterade arkitektur- och kommandobeskrivningen (mer aktuell än `AGENTS.md`).
- `CURRENT_STATE.md` — Aktuell projektstatus, senaste sessionernas ändringar och prioriterad backlog.
- `cc_was_here.md` — Korta sessionsnoteringar från senaste arbetspassen.
- `.claude/memory/learnings.md` — Dokumenterade tekniska lärdomar och mönster (obs: vissa äldre sektioner om AI/Pinecone och chargen är historiska).
- `.agents/skills/run-bot/SKILL.md` — Skill för att starta, verifiera och stoppa boten lokalt (`/run-bot`).

---

## Kritiska Utvecklings- och Testregler (från `CLAUDE.md`)

### Miljövariabler (`.env`)
- `DISCORD_TOKEN` — Krävs (boten är sedan 2026-08-24 helt fri från AI-/Pinecone-beroenden).
- `CHANNEL_IDS` — Valfritt (kommaseparerade Discord-kanal-ID:n, loggas vid uppstart).
- `GUILD_ID` — Valfritt men starkt rekommenderat vid utveckling (ger omedelbar guild-scoped slash-command-sync istället för global sync som tar upp till ~1 timme).
- `DEBUG_MODE` — Valfritt (`true` registrerar debug-kommando för user-info).

### Testning (KRITISKT)
- Testerna använder `unittest` (ej `pytest`).
- **Kör ALLTID tester som skript, ALDRIG med `-m unittest tests.X`!**
  Ett `tests`-paket installerat i `site-packages` (från ett orelaterat beroende) skuggar den lokala `tests/`-katalogen vid modulimport och exekverar fel paket i tystnad.
  Använd alltid:
  ```powershell
  python tests/test_X.py
  ```
- Aktuella testfiler i `tests/`:
  - `tests/test_dragonbane_dice.py`
  - `tests/test_eon_commands_registration.py`
  - `tests/test_eon_mechanics.py`
  - `tests/test_starwars_dice.py`
  - `tests/test_deltagreen_agent_manager.py`
  - `tests/test_deltagreen_project_flow.py`
  - `tests/test_deltagreen_projection.py`
  - `tests/test_deltagreen_san_cache.py`

---

## Uppdaterad Arkitektur & Modulöversikt (komplement till `AGENTS.md`)

Utöver det som står i `AGENTS.md` gäller följande aktuella struktur (se `CLAUDE.md` för detaljer):

### Aktiva Spelmoduler (Slash Commands)
- **Generiska tärnings-, stats-, utility- och GM-kommandon** (`src/commands/`):
  - `slash_dice_commands.py`: `/roll`, `/ex`, `/count`, `/chance`
  - `slash_admin_commands.py`: `/startsession`, `/endsession`, `/showsession`, `/secret_roll`, `/secret_ex`, `/secret_count`, `/gm_override`, `/session_rollback`, `/player_stats`
  - `slash_utility_commands.py`: `/help`, `/stats`, `/mystats`, `/allstats`, `/mystatsall`
  - `slash_comment_commands.py`: `/kommentarer` (`app_commands.Group`)
  - `slash_manipulation_commands.py`: `/manipulation` (`app_commands.Group`)
- **EON** (`src/eon/`):
  - Mekanik (`hit_tables.py`, `damage_tables.py`, `fumble_tables.py`, `combat_manager.py`) + `EonCommands`-Cog (`commands.py`).
  - Kommandon: `/eon_hugg`, `/eon_stick`, `/eon_kross`, `/eon_fummel`, `/eon_regel`, `/eon_hoj`.
  - Obs: `src/hit_system.py` i roten är en gammal oanvänd fil — förväxla den inte med `src/eon/hit_tables.py` (eller `src/hit_tables.py`).
- **Delta Green** (`src/deltagreen/`):
  - d100-baserat system inkl. bond-projektion (`san_check_cache.py`, `/dgproject`).
  - Kommandon: `/dgcheck`, `/dgstat`, `/dgluck`, `/dglethality`, `/dgsan`, `/dgagent`, `/dgallt`, `/dgroll`, `/dggmallt`, `/dggmroll`, `/dggmstatus`, `/dggmset`, `/dgstartsession`, `/dgendsession`, `/dgdmg`, `/dggmdmg`, `/dggmreset`, `/dgproject`.
- **Dragonbane / Drakar och Demoner** (`src/dragonbane/`):
  - `dice.py` + `commands.py` (Cog). Inkluderar husregel för stapling av fördel/nackdel (`antal`-parameter) samt normalisering av litet `t` -> `d` i tärningsuttryck.
  - Kommandon: `/dod_slag`, `/dod_fv`, `/dod_skada`, `/dod_pressa`, `/dod_hoj`, `/dod_skrack`, `/dod_mumie`, `/dod_init`.
- **Star Wars D6 (WEG40120, 2nd Ed. R&E)** (`src/starwars/`):
  - `dice.py` (ren, testbar tärningsmotor med Wild Die och injicerbar `Random`) + `commands.py` (Cog + `CharacterPointView`).
  - Kommandon: `/sw_slag`, `/sw_motstand`, `/sw_svarighet`, `/sw_init`.
- **Spindelmodulen** (`src/spindel/`):
  - Utflyttad till eget paket `src/spindel/` och **avstängd tills vidare** via `config/feature_flags.py` (`slash_spindel_enabled: False`).
- **Skjut Dem I Huvudet (SDIH)** (`src/skjutdomihuvudet/`):
  - Använder fortfarande prefix-kommandon; nästa mål för slash-command-migrering.

### Viktiga Saneringar som Redan är Genomförda (efter att `AGENTS.md` skrevs)
- **Legacy prefix-lagret är raderat** (commit `421e3d0`, 2026-08-23): `src/commands/*_commands.py` och `src/stats_commands.py` är redan borttagna.
- **AI/kunskapsbasen är helt raderad** (2026-08-24): Pinecone, Whoosh, SentenceTransformer, Claude API, `/ask`, `/sök`, `/allt` är borttagna.
- **Karaktärsskapande är pensionerat** (commit `dd3bb20`): `src/character_creation/` och `src/data/` är tomma restkataloger.
