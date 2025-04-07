# Diceroller Discord Bot

En Discord-bot för tärningskast och kunskapshantering för rollspelet EON.
(samt även för Skjut dem i Huvudet)

## Funktioner

- Tärningskast (!roll, !ex, !count)
- Hemliga tärningskast för spelledaren (!secret)
- Kunskapsbas med information från rollspelsböcker (!ask, !sök, !allt)
- Regler (!regel)
- Stridssimulering (!hugg, !stick, !kross, !fummel)
- Statistik (!stats, !mystats)
- Sessionshantering (!startsession, !endsession)
- Spårning av perfekta slag och fummel för obegränsade T6-slag (!ex)

## Projektstruktur

```
diceroller/
├── src/                    # Huvudkällkod
│   ├── __init__.py
│   ├── main.py             # Botens huvudfil
│   ├── color_handler.py    # Hanterar användares färger för inbäddningar
│   ├── roll_tracker.py     # Spårar tärningskast för statistik
│   ├── combat_manager.py   # Hanterar stridsrelaterade kommandon
│   ├── damage_tables.py    # Skadeberäkning
│   ├── hit_tables.py       # Träfftabeller
│   ├── fumble_tables.py    # Fummeltabeller
│   └── hit_system.py       # Stridsystem
├── data/                   # Databaser och datalager
│   ├── knowledge_index/    # Kunskapsindexfiler (Whoosh/FAISS)
│   ├── extracted_text/     # Utdragen text från PDF:er
│   ├── rules/              # Regelreferenser
│   ├── rolls.db            # SQLite-databas för tärningskast
│   └── user_colors.json    # Användarfärginställningar
├── utils/                  # Hjälpskript
│   ├── convert_pdfs.py     # Konverterar PDF:er till text
│   ├── extract_all_pdfs.py # Extraherar text från alla PDF:er
│   └── index_knowledge.py  # Indexerar kunskap för sökning
├── docs/                   # Dokumentation
│   └── images/             # Bilder
├── tests/                  # Testfiler
├── backups/                # Backupfiler
├── .env                    # Miljövariabler (API-nycklar etc.)
└── requirements.txt        # Paketberoenden
```

## Installation

1. Klona projektet
2. Installera beroenden: `pip install -r requirements.txt`
3. Generera kunskapsdatabas: `python utils/extract_all_pdfs.py` och sedan `python utils/index_knowledge.py`
4. Skapa en `.env`-fil med följande innehåll:
   ```
   DISCORD_TOKEN=din_discord_token
   CHANNEL_IDS=kanal1,kanal2  # valfritt
   PINECONE_API_KEY=din_pinecone_api_nyckel
   ANTHROPIC_API_KEY=din_claude_api_nyckel
   OPENAI_API_KEY=din_openai_api_nyckel
   PINECONE_INDEX_NAME=rpg-knowledge
   ```
5. Kör migrations-skript (om databasen redan finns): `python utils/migrate_database_perfect_fumble.py`
6. Starta boten: `python src/main.py`

## Kommandon

Se `!dicehelp` för en fullständig lista över kommandon.

## Perfekta slag och fummel

Boten spårar nu perfekta slag och fummel för obegränsade T6-slag (!ex):

- **!ex** (obegränsade T6-slag):
  - Perfekt slag: För 1T6 om resultatet är 1-3, eller för flera T6 om högst en tärning inte visar 1
  - Fummel: Två eller fler 6:or i första kastomgången

Detta visas visuellt i Discord-meddelandet när dessa speciella utfall inträffar.

## Utveckling

För att bidra till projektet:

1. Skapa en fork av projektet
2. Skapa en ny branch för din funktion/buggfix
3. Skicka en pull request med dina ändringar

## Licens

Detta projekt är licensierat under MIT-licensen. Se LICENSE-filen för mer information.
