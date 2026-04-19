# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Environment Setup
- `pip install -r requirements.txt` - Install Python dependencies
- Create `.env` file with required API keys:
  - DISCORD_TOKEN (Discord bot token)
  - PINECONE_API_KEY (for knowledge search)
  - ANTHROPIC_API_KEY (for Claude integration)
  - OPENAI_API_KEY (optional)
  - PINECONE_INDEX_NAME (default: "rpg-knowledge")
  - CHANNEL_IDS (comma-separated Discord channel IDs, optional)

### Running the Application
- `python src/main.py` - Start the Discord bot
- `python launcher/eon_bot_launcher.py` - Start the GUI launcher

### Knowledge Base Management
- `python utils/extract_all_pdfs.py` - Extract text from PDF files
- `python utils/index_knowledge.py` - Create/update knowledge search index
- `python utils/migrate_database_perfect_fumble.py` - Migrate database schema

### Testing
- `python tests/test.py` - Basic tests
- `python tests/test_embedding.py` - Test embedding functionality

## Architecture Overview

This is a Discord bot for the Swedish RPG "EON" (and some functionality for "Skjut Dem I Huvudet"). The bot provides dice rolling, combat simulation, rule lookups, and knowledge base queries.

### Core Components

**src/main.py** - Main bot entry point with Discord slash command handlers. Uses discord.py with slash commands (`/`). Integrates with Pinecone for vector search, Anthropic Claude for AI responses, and local SQLite for roll tracking.

**Knowledge System** - Two-tiered search:
- Whoosh index (`data/knowledge_index/`) for full-text search
- Pinecone vector database for semantic search
- Extracted text from RPG books stored in `data/extracted_text/`

**Combat System** - Modular combat mechanics:
- `src/combat_manager.py` - Main combat orchestration
- `src/hit_system.py` - Hit calculation logic
- `src/damage_tables.py` - Damage calculation by weapon type
- `src/fumble_tables.py` - Critical failure handling

**Roll Tracking** - SQLite database (`data/rolls.db`) tracks all dice rolls for statistics. Supports "perfect rolls" and "fumbles" for unlimited d6 rolls (`/ex` command).

**Embed Standardization** - All Discord embeds use centralized factory:
- `src/core/embed_factory.py` - Consistent visual profile across all commands
- Standard colors, emojis, and formatting
- User-specific color preferences

### Key Features (All Slash Commands)

- **Dice Commands**: `/roll`, `/ex` (unlimited d6), `/count`, `/chance`
- **Knowledge**: `/ask`, `/sök`, `/allt` - Query RPG rule database using AI
- **Combat**: `/hugg`, `/stick`, `/kross`, `/fummel` - Weapon attack simulation
- **Rules**: `/regel` - Quick rule lookups from `data/rules/`
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
  - `slash_knowledge_commands.py` - AI-powered knowledge search
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

- `data/extracted_text/` - Text extracted from RPG PDFs
- `data/rules/` - Quick reference rule files (txt format)
- `data/sdih_decks/` - Card deck data for SDIH game
- `data/user_colors.json` - User color preferences
- `data/deltagreen/` - Delta Green module data
- `data/character_tables/` - EON character-related tables

The knowledge base requires manual setup of PDF extraction and indexing before the bot can answer rule questions effectively.

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
