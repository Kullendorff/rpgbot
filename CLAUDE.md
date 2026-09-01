# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Environment Setup
- `pip install -r requirements.txt` - Install Python dependencies
- Create `.env` file with required API keys:
  - DISCORD_TOKEN (Discord bot token)
  - CHANNEL_IDS (comma-separated Discord channel IDs, optional — logged at startup, not enforced)
  - GUILD_ID (optional but recommended for dev — instant guild-scoped slash command sync instead of a global sync that can take up to an hour)
  - DEBUG_MODE (optional — `true` registers a debug user-info command)

### Running the Application
- `python src/main.py` - Start the Discord bot
- `python launcher/eon_bot_launcher.py` - Start the GUI launcher

### Testing
- Tests use `unittest`, not pytest (pytest isn't in `requirements.txt`, no test file imports it).
- **Run tests as scripts, not as `-m unittest tests.X`** — a `tests` package installed in site-packages (from an unrelated dependency) shadows the local `tests/` directory during module import and silently resolves to the wrong package. Always: `python tests/test_X.py`.
- Real test files: `test_starwars_dice.py`, `test_deltagreen_agent_manager.py`, `test_deltagreen_project_flow.py`, `test_deltagreen_projection.py`, `test_deltagreen_san_cache.py`.
- Deleted 2026-08-23 as dead weight: `tests/test.py` (printed DISCORD_TOKEN to stdout), `tests/test_embedding.py` (pre-1.0 OpenAI SDK), `tests/test_background.py` (imported retired chargen code), root `test_chargen.py`, root `debug_permissions.py`, root `debug_slash_commands.py` (production Discord + global tree.sync), the entire legacy prefix layer (`src/commands/*_commands.py`, `src/stats_commands.py`) and the `utils/` one-time scripts.

## Architecture Overview

This is a Discord bot for the Swedish RPG "EON" (and some functionality for "Skjut Dem I Huvudet"). The bot provides dice rolling, combat simulation, and rule lookups.

### Core Components

**src/main.py** - Main bot entry point with Discord slash command handlers. Uses discord.py with slash commands (`/`). Integrates with local SQLite for roll tracking.

**Combat System** - Modular combat mechanics:
- `src/combat_manager.py` - Main combat orchestration
- `src/hit_tables.py` - Hit calculation logic (imported as `hit_tables` in `main.py`; `src/hit_system.py` is an unused, dead file with a similar name — don't confuse the two)
- `src/damage_tables.py` - Damage calculation by weapon type
- `src/fumble_tables.py` - Critical failure handling

**Roll Tracking** - SQLite database (`data/rolls.db`) tracks all dice rolls for statistics. Supports "perfect rolls" and "fumbles" for unlimited d6 rolls (`/ex` command).

**Embed Standardization** - All Discord embeds use centralized factory:
- `src/core/embed_factory.py` - Consistent visual profile across all commands
- Standard colors, emojis, and formatting
- User-specific color preferences

### Key Features (All Slash Commands)

- **Dice Commands**: `/roll`, `/ex` (unlimited d6), `/count`, `/chance`
- **EON** (paket `src/eon/`): `/eon_hugg`, `/eon_stick`, `/eon_kross`, `/eon_fummel` - Weapon attack simulation
- **EON Rules/Improvement** (`src/eon/`): `/eon_regel` - Quick rule lookups from `data/rules/`; `/eon_hoj` - improvement rolls
- **Stats**: `/stats`, `/mystats` - Roll statistics and session tracking
- **GM Commands**: `/startsession`, `/endsession`, `/showsession`, `/secret_roll`, `/secret_ex`, `/secret_count`, `/gm_override`, `/session_rollback`, `/player_stats`
- **Utility**: `/help`, `/allstats`, `/mystatsall`
- **Comments/Manipulation** (grupper): `/kommentarer` (aktivera/inaktivera/stil/frekvens/status/lista/global_av), `/manipulation` (aktivera/aktivera_id/aktivera_gm/inaktivera/inaktivera_gm/status/rensa_alla)
- **Delta Green** (d100 percentile): `/dgcheck`, `/dgstat`, `/dgluck`, `/dglethality`, `/dgsan`, `/dgagent`, `/dgallt`, `/dgroll`, `/dggmallt`, `/dggmroll`, `/dggmstatus`, `/dggmset`, `/dgstartsession`, `/dgendsession`, `/dgdmg`, `/dggmdmg`, `/dggmreset`
- **Dragonbane** (Drakar och Demoner, modul av Jonas — github.com/jonsal/dragonbane): `/dod_slag`, `/dod_fv`, `/dod_skada`, `/dod_pressa`, `/dod_hoj`, `/dod_skrack`, `/dod_mumie`, `/dod_init`
- **Star Wars D6** (WEG40120, 2nd Ed. R&E): `/sw_slag`, `/sw_motstand`, `/sw_svarighet`, `/sw_init` - Wild Die-tärningsmotor med explosion, Force/Character Points

### Module Structure

- `src/core/` - Core systems:
  - `embed_factory.py` - Centralized Discord embed creation (also holds ~200 lines of de-facto EON-only methods with generic names — `dice_result`, `combat_result`, `stats_overview` — alongside the properly prefixed `dg_*`, `dragonbane_*`, `starwars_*` methods)
  - `constants.py` - Centralized constants and env var config
  - `dice_parser.py`, `dice_engine.py` - EON DiceSpec parsing and exploding-d6 probability
  - `logging_config.py`, `user_settings.py`, `comment_styles.py`, `manipulation_manager.py`
- `src/color_handler.py` - Per-user Discord embed colors (shared across every module)
- `src/migration/` - `helper.py` (`MigrationHelper`, `SlashCommandDecorator`) used by all EON slash-command Cogs for deferred responses and error embeds

- `src/commands/` - Slash command implementations (Cog-based, EON-only unless noted):
  - `slash_dice_commands.py` - Dice rolling with autocomplete
  - `slash_admin_commands.py` - GM/admin tools
  - `slash_utility_commands.py` - Utility commands
  - `slash_manipulation_commands.py` - Manipulation mechanics (`app_commands.Group`, not a Cog; bot-wide feature, not EON-specific)
  - `slash_comment_commands.py` - Comment/annotation commands (`app_commands.Group`, not a Cog; bot-wide feature, not EON-specific)
- `src/eon/` - EON som eget paket (likt deltagreen/dragonbane/starwars):
  - `hit_tables.py`, `damage_tables.py`, `fumble_tables.py`, `combat_manager.py` - Ren mekanik, re-exponerad via `__init__.py` (12 symboler, inga Discord-importer)
  - `commands.py` - `EonCommands`-cogen: stridskommandona + `/eon_regel` + `/eon_hoj`; `register_slash_eon_commands`

- `src/deltagreen/` - Delta Green RPG module (d100 percentile), includes bond-projection mechanics (`san_check_cache.py`)
- `src/dragonbane/` - Dragonbane (Drakar och Demoner) RPG module, `dice.py` + `commands.py` (Cog), modul av Jonas
- `src/starwars/` - Star Wars D6 (WEG40120) RPG module: `dice.py` (ren, testbar tärningsmotor, injicerbar Random), `commands.py` (Cog + CharacterPointView)
- `src/spindel/` - Gigantspindel + småspindelstrid, egen paketmodul. **Avstängd tills vidare** (`config/feature_flags.py`: `slash_spindel_enabled: False`) — flyttades ut ur `src/` och `src/commands/` 2026-08-16, ingen aktiv användning atm. Sätt flaggan till `True` för att slå på `/spindel`, `/spindel_runda`, `/spindelstatus`, `/spindelreset`, `/spindeldump`, `/spawna_småspindlar`, `/attack_småspindel`, `/småspindelstatus`, `/reset_småspindlar` igen.
- `src/utils/` - Utility functions and helpers (`stats_visualizer.py`, `text_utils.py`)
- `src/skjutdomihuvudet/` - "Skjut Dem I Huvudet" RPG module (prefix-only, not yet migrated to slash)
- `src/character_creation/` and `src/data/` - empty directories, dead weight left over from the retired character-creation system; safe to delete whenever someone gets around to it

### Data Files

- `data/rules/` - Quick reference rule files (txt format)
- `data/sdih_decks/` - Card deck data for SDIH game
- `data/user_colors.json` - User color preferences
- `data/deltagreen/` - Delta Green module data
- `data/character_tables/` - EON character-related tables, left over from the retired character-creation system
- `data/rolls.db` - SQLite roll-tracking database
- `data/config/` - `umnak_comments.txt`
- `data/user_settings.json`, `data/secret_manipulations.json` - comment/manipulation system state
- `data/spider_status_*.json` - leftover save state from the (now disabled) spindel module

---

## Recent Major Updates

### Completed
- **Embed Standardization** - All embeds now use centralized factory for consistent UX
- **Character Creation Retired** - System pensionerad (commit `dd3bb20`), docs archived in `docs/character_creation_archive.md`
- **Dragonbane-modulen** (av Jonas) - `/dod_slag`, `/dod_fv`, `/dod_skada`, `/dod_pressa`, `/dod_hoj`, `/dod_skrack`, `/dod_mumie`, `/dod_init`
- **Star Wars D6-modulen** (WEG40120, 2nd Ed. R&E) - `/sw_slag`, `/sw_motstand`, `/sw_svarighet`, `/sw_init`, regler verifierade mot källboken
- **Delta Green bond-projektion** - `/dgproject` ("Projecting Onto a Bond"), `SanCheckCache`
- **Spindel-modulen utflyttad** - egen paketmodul `src/spindel/`, avstängd tills vidare (`slash_spindel_enabled: False`)
- **AI/kunskapsdelen borttagen (2026-08-24)** - hela kunskapsbasen (Pinecone + SentenceTransformer + Claude + Whoosh), `/ask`, `/sök`, `/allt`, AI-sessionssammanfattningen och spindelns AI-beskrivningar raderade; boten kräver nu bara `DISCORD_TOKEN`

### Current Development Focus
- **Slash Command Migration KLAR (2026-08-23)** - legacy-prefixlagret (6 filer, ~1910 rader), dess main.py-registreringar och `dual_mode_*`-flaggorna raderade i commit `421e3d0`. Endast slash kvar; SDIH (`src/skjutdomihuvudet/`) är nästa migrationsmål.
- Extract `parse_effect_code()` to shared utility (duplicated in `damage_tables.py`, `src/spindel/spider_damage_tables.py`, `src/spindel/small_spider_tables.py` — lägre prioritet nu när spindel är avstängd; kräver regelbeslut eftersom else-grenen skiljer sig semantiskt)
- Split large slash-command files (`slash_admin_commands.py` 1304 rader, `slash_utility_commands.py` 1099 rader, `deltagreen/commands.py`)
- Migrate SDIH to slash commands
- **Genomfört (2026-08-24, branch `eon-modul`): EON modulariserad till `src/eon/`** — mekaniken (hit_tables, damage_tables, fumble_tables, combat_manager) + `EonCommands`-cogen, plan/bollplank i `C:\oxen-launch`. Namnbyte enbart för de sex EON-mekanikkommandona (`/eon_hugg`, `/eon_stick`, `/eon_kross`, `/eon_fummel`, `/eon_regel`, `/eon_hoj`); de generiska kommandona (`/roll`, `/help`, `/stats`, `/startsession`...) var aldrig del av genomförandet. `roll_tracker.py`/`color_handler`/`embed_factory` stannar delat. Namnbytet slår igenom vid nästa `bot.tree.sync()` — instant om `GUILD_ID` är satt, annars upp till ~1 h propagation.

---

# Quality and Robustness Over Speed

Your absolute highest priority is the quality, maintainability, and robustness of the code. Never sacrifice code quality for a faster or simpler-looking solution.

- **Avoid "batch solutions":** Do not attempt to solve complex problems in one single, large step. I have noticed this often leads to new, unforeseen issues.
- **Adopt a step-by-step approach:** Break down every task into smaller, logical sub-tasks. Address them methodically, one by one. This ensures a more robust and well-thought-out final implementation.
- **Think about consequences:** Before suggesting code, consider its impact on the existing codebase. Think about potential side effects, edge cases, and long-term maintainability.
- **Ask clarifying questions:** If a request is ambiguous, or could be interpreted in a way that leads to a "quick and dirty" solution, ask me for clarification first.
- **The only exception:** This principle is your primary directive and should be followed at all times, **unless I explicitly use phrases like "quick and dirty", "prototype", "just make it work for now", or "prioritize speed".** Only then are you permitted to lower the quality standards for the sake of velocity.
