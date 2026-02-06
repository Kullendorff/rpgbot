# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 🔄 Background Activities During Development

**Allowed during Diceroller sessions:**
- Moltbook check-ups when explicitly requested
- Token allocation: Diceroller gets 90%, background gets 10%
- In case of conflict: Diceroller always wins

**Trigger examples:**
- "Check Moltbook while I work on this"
- "Monitor Moltbook in the background"
- "What's happening on Moltbook?"

**When background activity is running:**
- Primary focus: Diceroller work (code quality, functionality, testing)
- Secondary: Moltbook (limited scope - quick check/monitoring)
- Report both results when complete

---

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

---

## .claude/ - AI Infrastructure (🆕 Memory System)

### Structure
```
.claude/
└── memory/                  # 🆕 Memory-system
    └── learnings.md         # Diceroller-specifika lärdomar
```

**Global structure** (outside project):
```
~/.claude/
├── hooks/
│   └── session-start.js     # Auto-loader hook (Node.js)
├── memory/
│   └── learnings.md         # Globala lärdomar (alla projekt)
└── settings.json            # Hooks-konfiguration
```

### Memory System

**Vid session-start:**
- SessionStart-hook körs automatiskt (`~/.claude/hooks/session-start.js`)
- Hook läser projekt-filer: `_index.md`, `CLAUDE.md` (denna fil)
- Hook läser **diceroller-specifik** learnings.md (`.claude/memory/learnings.md`)
- Hook läser **global** learnings.md (`~/.claude/memory/learnings.md`)
- Allt laddas automatiskt - full context from the start!

### What's Documented in learnings.md

**Diceroller-specific learnings** (`.claude/memory/learnings.md`):
- **Discord.py migration** (prefix → slash commands)
- **Embed standardization** (centralized factory pattern)
- **Quality-över-speed beslut** (why step-by-step works better)
- **EON rules** (exploderande T6, perfect rolls, fumbles)
- **AI integration** (Claude API, Pinecone gotchas, rate limiting)
- **SQLite patterns** (database locked, migrations, connection pooling)
- **Async patterns** (Discord.py event handling, 3-second timeout)
- **DiceSpec parser** (security, flexibility, error handling)
- **Character creation** (32-step system, TableProcessor)
- **Performance** (memory management for long-running bot)
- **Testing** (automated testing strategy)

**Global learnings** (`~/.claude/memory/learnings.md`):
- Edit-verktyget (matcha korta strängar, inte långa)
- Git triple-check (före push till public repos)
- Validering (testa efter kritiska ändringar)
- Hooks (robust error handling)

### Benefits

- ✅ **Konsistent context** varje session
- ✅ **Inga glömda best practices** - dokumenterade och laddade automatiskt
- ✅ **Dokumenterade lösningar** på vanliga problem
- ✅ **Institutionell kunskap** som byggs upp över tid
- ✅ **Historik av beslut** - varför, inte bara hur

### How to Update learnings.md

**När du löser ett problem eller upptäcker ett mönster:**
1. Lägg till i `.claude/memory/learnings.md`
2. Inkludera: Datum, Problem, Lösning, Kod-exempel
3. Tagga vad det gäller för (Discord.py, AI, EON-rules, etc.)

**Exempel:**
```markdown
## Discord.py: New Gotcha Discovered

**Datum:** YYYY-MM-DD
**Problem:** [Beskriv problem]
**Lösning:** [Konkret lösning]
**Kod-exempel:**
```python
# Lösning här
```
**Gäller:** Discord.py 2.0+ projekt
```

---

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