# Johans beslut — grönt ljus för Batch 1

**Till:** ox-alpha
**Från:** Claude (för Johans räkning)
**Datum:** 2026-08-23
**Underlag:** `PLAN_OX_BETA_2026-08-23.md` + `SVAR_OX_ALPHA_2026-08-23.md`

Dialogen är avslutad. Ni var överens om nästan allt; de tre öppna punkterna är nu avgjorda av Johan.

## Beslut på de tre öppna punkterna

1. **Global felhanterare som punkt 0 i Batch 1: JA.** Minimal `tree.on_error`/`on_command_error` (~20 rader, logga med `exc_info=True` + generiskt ephemeralt svar) körs **före** de 11 fixarna, som separat commit. Ingen per-cog-refactor, ingen `_send_error()`-utbyggnad — det hör till robusthetsfasen.
2. **"Batch 1.5" atomära JSON-skrivningar: NEJ.** Det står redan i robusthetsfasen som uttryckligen valdes bort från mandatet. Inget undantag. Tas upp igen som egen beställd batch senare om det blir aktuellt.
3. **bat-fil fail-loud + röktestritual: JA, båda.** Låg risk, rör inte venv/pip, ingen konflikt med att Johan bygger om venv:n manuellt.

## Sökvägskorrigering (bekräftad av mig mot filsystemet)

Ox-alpha hade rätt: `debug_permissions.py`, `debug_slash_commands.py`, `debug_user_info.py` ligger på **repo-roten** (`C:\diceroller\`), inte i `tests/`. Verifierat med `ls` och att `main.py:171` gör `from debug_user_info import register_debug_command` (bar import, förutsätter roten på sys.path). Använd rot-sökvägarna i Batch 2:
- `C:\diceroller\debug_permissions.py` → radera
- `C:\diceroller\debug_user_info.py` → **rör inte**, lastbärande via `DEBUG_MODE`
- `C:\diceroller\debug_slash_commands.py` → farligt (global `tree.sync` mot produktion), ur repot eller bakom explicit bekräftelse — samma slutsats som originaldokumentet, bara rätt sökväg

## Slutgiltig ordning för Batch 1

| # | Åtgärd |
|---|---|
| 0 | Minimal global felhanterare (`tree.on_error` + prefix-motsvarighet) |
| 1 | Radera `tests/test.py` (token-print) |
| 2 | `/dgroll` f-sträng |
| 3 | `/roll` `>=` → `<=` |
| 4 | Huvudträffens pansarkod — härled `code` från det nya delområdet (variant B, självkonsistent) |
| 5 | `!skada` unpack |
| 6 | `/endsession` — `roll_tracker.start_session()`s returvärde som enda ID-källa |
| 7 | Ta bort `/session_rollback` + `/gm_override` |
| 8 | Ta bort `/player_stats` |
| 9 | GM-gata `demon`; legacy loggar äkta tärningar till `rolls.db` |
| 10 | Ta bort ryttare/fyrfota-parametrar, UI-rader, döda imports |
| 11 | Döp om `roll_t10` → `roll_result`, fixa felsträngen |

Alla andra detaljer, citat och acceptanskriterier står kvar oförändrade i `PLAN_OX_BETA_2026-08-23.md` §2.

## Röktest per batch (acceptanskriterium utöver per-fix-kriterierna)

1. `python -m unittest discover -s tests -p "test_*.py"` grönt (efter att punkt 1 raderat `test.py`) — kör aldrig detta **före** punkt 1 är klar (ox-alphas egen lärdom: unittest-discovery har redan en gång i denna utredning triggat token-utskriften i `tests/test.py`).
2. Botstart med samma tolk som produktion, startloggen läst.
3. Live-eld i testkanal: `/dgroll` med bonus 0 och +2, `/roll` strax över/under mål, `!skada pistol`, `/startsession` → `/endsession`, kort `/chance`.
4. Separata commits per fix — bisectbart.

## Batch 2 — oförändrad, med sökvägskorrigeringen ovan och tillägget:

- `start_bot.bat`: lägg till explicit fail (kontrollera errorlevel efter `call .\venv\Scripts\activate.bat`, avbryt med felmeddelande i loggen om det misslyckas) istället för tyst fall-through till system-Python. Rör inte venv:n själv — Johan bygger om den separat.

---

**Grönt ljus: börja Batch 1, punkt 0 först.** Stanna efter Batch 1 och invänta granskning innan Batch 2 påbörjas, per §0.6 i originaldokumentet.

En sak utanför kodarbetet, för Johan att göra oberoende av batcharbetet: överväg att rotera **Discord-token**, inte bara Pinecone-nyckeln — ox-alpha uppger att deras granskningsprocess redan en gång triggat token-utskriften i `tests/test.py` under arbetet.

— Claude
