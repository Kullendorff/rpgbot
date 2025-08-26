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

This is a Discord bot for the Swedish RPG "EON" (and some functionality for "Skjut Dem I Huvudet"). The bot provides dice rolling, combat simulation, rule lookups, knowledge base queries, and a comprehensive character creation system.

### Core Components

**src/main.py** - Main bot entry point with Discord slash command handlers. Uses discord.py with slash commands (`/`). Integrates with Pinecone for vector search, Anthropic Claude for AI responses, and local SQLite for roll tracking.

**Knowledge System** - Two-tiered search:
- Whoosh index (`data/knowledge_index/`) for full-text search
- Pinecone vector database for semantic search
- Extracted text from RPG books stored in `data/extracted_text/`

**Combat System** - Modular combat mechanics:
- `combat_manager.py` - Main combat orchestration
- `hit_system.py` - Hit calculation logic
- `damage_tables.py` - Damage calculation by weapon type
- `fumble_tables.py` - Critical failure handling

**Character Creation System** - Session-based character creation for EON:
- `character_creation.py` - 32-step character creation process
- `TableProcessor` - Automatic table handling for all EON tables
- JSON-based data storage in `data/raser/` and related directories
- Full support for humans, partial support for elves/dwarves/tiraks

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
- **Character Creation**: `/create_character` - Interactive session-based character generation


### Module Structure

- `src/core/` - Core systems:
  - `embed_factory.py` - Centralized Discord embed creation
  - `color_handler.py` - Per-user Discord embed colors
  
- `src/commands/` - Slash command implementations:
  - `slash_dice_commands.py` - Dice rolling with autocomplete
  - `slash_combat_commands.py` - Combat mechanics
  - `slash_knowledge_commands.py` - AI-powered knowledge search
  - `slash_stats_commands.py` - Statistics and analytics
  - `slash_admin_commands.py` - GM/admin tools
  
- `src/character_creation/` - Character generation system
- `src/utils/` - Utility functions and helpers
- `skjutdomihuvudet/` - Separate module for "Skjut Dem I Huvudet" RPG functionality

### Data Files

- `data/extracted_text/` - Text extracted from RPG PDFs
- `data/rules/` - Quick reference rule files (txt format)
- `data/sdih_decks/` - Card deck data for SDIH game
- `data/user_colors.json` - User color preferences
- `data/raser/` - Character creation race data (JSON)
- `data/bakgrund/` - Background tables for character creation
- `data/landerhemort/` - Homeland and origin data

The knowledge base requires manual setup of PDF extraction and indexing before the bot can answer rule questions effectively.

## Recent Major Updates

### Completed Migrations
- **Embed Standardization** - All embeds now use centralized factory for consistent UX
- **Slash Command Migration** - Full conversion from prefix (`!`) to slash (`/`) commands
- **Character Creation System** - Complete implementation for human characters with Thalamur special cases

### Current Development Focus
- Extending character creation to support non-human races (elves, dwarves, tiraks)
- Performance optimizations for AI knowledge queries
- Enhanced session management for GMs

# About Speed and Robustness ..

## Quality and Robustness Over Speed

Your absolute highest priority is the quality, maintainability, and robustness of the code. Never sacrifice code quality for a faster or simpler-looking solution.

- **Avoid "batch solutions":** Do not attempt to solve complex problems in one single, large step. I have noticed this often leads to new, unforeseen issues.
- **Adopt a step-by-step approach:** Break down every task into smaller, logical sub-tasks. Address them methodically, one by one. This ensures a more robust and well-thought-out final implementation.
- **Think about consequences:** Before suggesting code, consider its impact on the existing codebase. Think about potential side effects, edge cases, and long-term maintainability.
- **Ask clarifying questions:** If a request is ambiguous, or could be interpreted in a way that leads to a "quick and dirty" solution, ask me for clarification first.
- **The only exception:** This principle is your primary directive and should be followed at all times, **unless I explicitly use phrases like "quick and dirty", "prototype", "just make it work for now", or "prioritize speed".** Only then are you permitted to lower the quality standards for the sake of velocity.

Thank you for adhering to these guidelines to help me write better, more reliable code.