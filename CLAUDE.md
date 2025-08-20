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

**src/main.py** - Main bot entry point with Discord command handlers. Uses discord.py with command prefix `!`. Integrates with Pinecone for vector search, Anthropic Claude for AI responses, and local SQLite for roll tracking.

**Knowledge System** - Two-tiered search:
- Whoosh index (`data/knowledge_index/`) for full-text search
- Pinecone vector database for semantic search
- Extracted text from RPG books stored in `data/extracted_text/`

**Combat System** - Modular combat mechanics:
- `combat_manager.py` - Main combat orchestration
- `hit_system.py` - Hit calculation logic
- `damage_tables.py` - Damage calculation by weapon type
- `fumble_tables.py` - Critical failure handling

**Roll Tracking** - SQLite database (`data/rolls.db`) tracks all dice rolls for statistics. Supports "perfect rolls" and "fumbles" for unlimited d6 rolls (`!ex` command).

### Key Features

- **Dice Commands**: `!roll`, `!ex` (unlimited d6), `!count`, `!secret`
- **Knowledge**: `!ask`, `!sök`, `!allt` - Query RPG rule database using AI
- **Combat**: `!hugg`, `!stick`, `!kross`, `!fummel` - Weapon attack simulation
- **Rules**: `!regel` - Quick rule lookups from `data/rules/`
- **Stats**: `!stats`, `!mystats` - Roll statistics and session tracking

### Special User Handling

The bot includes special sarcastic responses for user ID "680064176227352610" (Umnatak), loaded from `data/config/umnak_comments.txt`.

### Module Structure

- `color_handler.py` - Per-user Discord embed colors
- `roll_tracker.py` - Database operations for roll statistics  
- `stats_commands.py` - Statistics command implementations
- `skjutdomihuvudet/` - Separate module for "Skjut Dem I Huvudet" RPG functionality

### Data Files

- `data/extracted_text/` - Text extracted from RPG PDFs
- `data/rules/` - Quick reference rule files (txt format)
- `data/sdih_decks/` - Card deck data for SDIH game
- `data/user_colors.json` - User color preferences

The knowledge base requires manual setup of PDF extraction and indexing before the bot can answer rule questions effectively.

# About Speed and Robustness ..

## Quality and Robustness Over Speed

Your absolute highest priority is the quality, maintainability, and robustness of the code. Never sacrifice code quality for a faster or simpler-looking solution.

- **Avoid "batch solutions":** Do not attempt to solve complex problems in one single, large step. I have noticed this often leads to new, unforeseen issues.
- **Adopt a step-by-step approach:** Break down every task into smaller, logical sub-tasks. Address them methodically, one by one. This ensures a more robust and well-thought-out final implementation.
- **Think about consequences:** Before suggesting code, consider its impact on the existing codebase. Think about potential side effects, edge cases, and long-term maintainability.
- **Ask clarifying questions:** If a request is ambiguous, or could be interpreted in a way that leads to a "quick and dirty" solution, ask me for clarification first.
- **The only exception:** This principle is your primary directive and should be followed at all times, **unless I explicitly use phrases like "quick and dirty", "prototype", "just make it work for now", or "prioritize speed".** Only then are you permitted to lower the quality standards for the sake of velocity.

Thank you for adhering to these guidelines to help me write better, more reliable code.