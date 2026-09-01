# AGENTS.md

This file provides guidance to Codex (Codex.ai/code) when working with code in this repository.

## Development Commands

### Environment Setup
- `pip install -r requirements.txt` - Install Python dependencies
- Create `.env` file with required API keys:
  - DISCORD_TOKEN (Discord bot token)
  - CHANNEL_IDS (comma-separated Discord channel IDs, optional)

### Running the Application
- `python src/main.py` - Start the Discord bot
- `python launcher/eon_bot_launcher.py` - Start the GUI launcher

### Testing
- Run test files as scripts: `python tests/test_X.py` (e.g. `test_starwars_dice.py`, `test_deltagreen_*.py`)

## Architecture Overview

This is a Discord bot for the Swedish RPG "EON" (and some functionality for "Skjut Dem I Huvudet"). The bot provides dice rolling, combat simulation, and rule lookups.

### Core Components

**src/main.py** - Main bot entry point with Discord slash command handlers. Uses discord.py with slash commands (`/`). Integrates with local SQLite for roll tracking.

**EON Module** - EON mechanics as its own package (`src/eon/`, like deltagreen/dragonbane/starwars):
- `src/eon/combat_manager.py` - Main combat orchestration
- `src/eon/hit_tables.py` - Hit location calculation
- `src/eon/damage_tables.py` - Damage calculation by weapon type
- `src/eon/fumble_tables.py` - Critical failure handling
- `src/eon/commands.py` - `EonCommands` Cog (combat + rules + improvement commands)

**Roll Tracking** - SQLite database (`data/rolls.db`) tracks all dice rolls for statistics. Supports "perfect rolls" and "fumbles" for unlimited d6 rolls (`/ex` command).

**Embed Standardization** - All Discord embeds use centralized factory:
- `src/core/embed_factory.py` - Consistent visual profile across all commands
- Standard colors, emojis, and formatting
- User-specific color preferences

### Key Features (All Slash Commands)

- **Dice Commands**: `/roll`, `/ex` (unlimited d6), `/count`, `/chance`
- **EON**: `/eon_hugg`, `/eon_stick`, `/eon_kross`, `/eon_fummel` - Weapon attack simulation
- **EON Rules**: `/eon_regel` - Quick rule lookups from `data/rules/`; `/eon_hoj` - improvement rolls
- **Stats**: `/stats`, `/mystats` - Roll statistics and session tracking
- **GM Commands**: `/startsession`, `/endsession`, `/secret_roll`, `/gm_override`

### Module Structure

- `src/core/` - Core systems:
  - `embed_factory.py` - Centralized Discord embed creation
  - `constants.py` - Centralized constants and env var config
- `src/color_handler.py` - Per-user Discord embed colors

- `src/commands/` - Slash command implementations:
  - `slash_dice_commands.py` - Dice rolling with autocomplete
  - `slash_combat_commands.py` - Combat mechanics
  - `slash_admin_commands.py` - GM/admin tools
  - `slash_utility_commands.py` - Utility commands
  - `slash_manipulation_commands.py` - Manipulation mechanics
  - `slash_comment_commands.py` - Comment/annotation commands
  - `slash_spider_commands.py` / `slash_small_spider_commands.py` - Spider combat

- `src/deltagreen/` - Delta Green RPG module
- `src/spider_combat_manager.py` / `src/small_spider_manager.py` - Spider combat systems
- `src/utils/` - Utility functions and helpers
- `src/skjutdomihuvudet/` - "Skjut Dem I Huvudet" RPG module

### Data Files

- `data/rules/` - Quick reference rule files (txt format)
- `data/sdih_decks/` - Card deck data for SDIH game
- `data/user_colors.json` - User color preferences
- `data/deltagreen/` - Delta Green module data
- `data/character_tables/` - EON character-related tables

---

## Recent Major Updates

### Completed
- **Embed Standardization** - All embeds now use centralized factory for consistent UX
- **Slash Command Migration** - Full conversion from prefix (`!`) to slash (`/`) commands
- **Character Creation Retired** - System pensionerad (commit `dd3bb20`), docs archived in `docs/character_creation_archive.md`

### Current Development Focus
- Remove legacy prefix commands (5 files, ~1,500 lines) — see CURRENT_STATE.md
- Extract `parse_effect_code()` to shared utility (duplicated in `damage_tables.py`, `spider_damage_tables.py`, `small_spider_tables.py`)
- Split large slash-command files (`slash_admin_commands.py`, `deltagreen/commands.py`)
- Migrate SDIH to slash commands

---

# Quality and Robustness Over Speed

Your absolute highest priority is the quality, maintainability, and robustness of the code. Never sacrifice code quality for a faster or simpler-looking solution.

- **Avoid "batch solutions":** Do not attempt to solve complex problems in one single, large step. I have noticed this often leads to new, unforeseen issues.
- **Adopt a step-by-step approach:** Break down every task into smaller, logical sub-tasks. Address them methodically, one by one. This ensures a more robust and well-thought-out final implementation.
- **Think about consequences:** Before suggesting code, consider its impact on the existing codebase. Think about potential side effects, edge cases, and long-term maintainability.
- **Ask clarifying questions:** If a request is ambiguous, or could be interpreted in a way that leads to a "quick and dirty" solution, ask me for clarification first.
- **The only exception:** This principle is your primary directive and should be followed at all times, **unless I explicitly use phrases like "quick and dirty", "prototype", "just make it work for now", or "prioritize speed".** Only then are you permitted to lower the quality standards for the sake of velocity.

## Imported Claude Cowork project instructions
