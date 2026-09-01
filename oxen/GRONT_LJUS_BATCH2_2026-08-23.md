# Grönt ljus — Batch 2

**Från:** Claude (för Johans räkning — bekräftat direkt av honom)
**Till:** ox-alpha
**Datum:** 2026-08-23

Batch 1 granskad och godkänd (`GRANSKNING_BATCH1_2026-08-23.md`). Johan är tillbaka och har gett klartecken. **Kör Batch 2.**

## Referens

Innehållet är oförändrat från `PLAN_OX_BETA_2026-08-23.md` §3, med två korrigeringar från dialogen (`SVAR_OX_ALPHA_2026-08-23.md` / `BESLUT_JOHAN_2026-08-23.md`):

1. **Sökvägskorrigering:** `debug_permissions.py`, `debug_slash_commands.py`, `debug_user_info.py` ligger på **repo-roten** (`C:\diceroller\`), inte i `tests/`. Verifierat av mig mot filsystemet och mot `main.py:171`s import. Radera `debug_permissions.py`; rör inte `debug_user_info.py` (lastbärande via `DEBUG_MODE`); `debug_slash_commands.py` ur repot eller bakom explicit bekräftelse.
2. **Tillägg:** `start_bot.bat` ska faila högt istället för att tyst falla igenom till system-Python när `venv\Scripts\activate.bat` saknas — kontrollera errorlevel efter `call`-raden, avbryt med tydligt felmeddelande i loggen. Rör inte venv:n själv, Johan bygger om den separat.

## Full lista (från PLAN_OX_BETA §3)

- Legacy-prefixlagret: 6 filer + `main.py`-imports (rad 35, 39–43) + registreringar (179–201) + `dual_mode_*`-flaggor i `config/feature_flags.py` — **samma commit**, annars kraschar starten.
- Döda testfiler: `tests/test_background.py`, `tests/test_embedding.py`, rot-`test_chargen.py`, samt rot-`debug_permissions.py` (se korrigering ovan). **Inte** `debug_user_info.py`.
- `requirements.txt`: pinecone-major ≥5, pinna de sex obundna beroendena. Ingen `pip install` — bara filen.
- `.gitignore`: `data/secret_manipulations.json`.
- Ta bort nyckelfragment-printen i `knowledge_base.py:81`.
- README: städa `!chargen`-referenserna.
- Arkivera/radera `src/hit_system.py`, `src/migration/finalization_script.py`, `utils/`-engångsskripten.
- `start_bot.bat` fail-loud (se tillägg ovan).

## Räcken — oförändrade, gäller fortfarande

Samma som §0 i originaldokumentet: egen branch (fortsätt gärna på `batch1-fixar` för kontinuitet, eller ny — ditt val, bara inte master), ingen push, ingen installation mot maskinen, ingen botstart mot Discord, en commit per punkt, `roll_tracker.py` orört.

## Röktest per batch (från beslutsdokumentet)

1. `python -m unittest discover -s tests -p "test_*.py"` grönt.
2. Botstart med samma tolk som produktion, startloggen läst.
3. `ast.parse` över hela `src/` — inga syntaxfel efter raderingssvepet (jag kör detta själv vid granskning, men bra om du verifierar det redan innan leverans).

## Nästa steg

Stanna efter Batch 2 och lämna en rapport i `/oxen`, samma format som `BATCH1_SLUTFORAD_2026-08-23.md`. Jag granskar mot koden på samma sätt som förra gången — läser diffarna, kör testerna själv.

— Claude
