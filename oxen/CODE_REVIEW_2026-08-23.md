# Kodgranskning Deluxe — RPGBOT

**Datum:** 2026-08-23
**Omfattning:** Hela repot C:\diceroller (~22 500 rader Python i `src/`, `config/`, `launcher/`, `utils/`, `tests/`)
**Metod:** 8 parallella granskningsagenter (core, Delta Green, Dragonbane/Star Wars, slash-lager, legacy/delad mekanik, SDIH/spindel, säkerhet, tester/hygien). Read-only — **ingen kod har ändrats**.
**Status:** Granskningsrapport. Åtgärdsförslag är beskrivna, ej utförda.

---

## Executive Summary

Granskningen hittade **~70 unika fynd**: 7 kritiska, cirka 15 höga, resten medel/låg. Tre teman går igenom hela kodbasen:

1. **Kommandon som låtsas fungera.** Flera kommandon skickar "Genomförd!"-embeds medan koden tyst hoppar över själva jobbet (`hasattr`-tystnad, sväljda undantag, fel signaturer). Farligast i spelöppen session när en GM tror att data rullats tillbaka eller ändrats.
2. **Blockerande I/O på event-loopen** — samma bugklass som fixades i augusti (kunskapsbasens 404-interaktioner), men fixen täckte bara init + slash-vägen. Synkrona Claude/Pinecone-anrop, filsökning över alla extracted_text-filer och tärningssimuleringar med upp till 100 000 iterationer fryser fortfarande hela boten.
3. **Arkeologi efter refaktoreringar.** Karaktärsskapningen pensionerades men testerna och README:n glömdes; OB-tärningar togs bort men `!skada` blev liggande död; slash-migreringen lämnade ett legacy-lager som inte underhålls ens när det går sönder. Mycket av detta är säkert att radera — det är dokumenterat nedan.

**Viktigaste enskilda åtgärden:** Pinecone-API-nyckeln från februari ligger fortfarande i **pushad git-historik** på GitHub. Raderad fil ≠ återkallad nyckel — rotera den om det inte redan gjorts.

**Överlag:** Kodbasen är förvånansvärt sund för en hobbybot. Tärningsmotorerna (Star Wars, Delta Green) är senior-klass med injicerbar RNG, explosionsgränser och sidhänvisningar till regelböcker. Ingen kodinjektion, inga hemligheter i trädet, alla admin-kommandon har runtime-behörighetskontroll. Problemkoncentrationen ligger i Discord-lagret (copy-paste-skelett), persistensskiktet (icke-atomära skrivningar) och den gamla kommandokoden.

---

## 1. Kritiska fynd — fixas innan nästa spelsession

### K1. `/session_rollback` och `/gm_override` fejkar framgång
`src/commands/slash_admin_commands.py:958–1002, 1069–1098`

`session_rollback` anropar `roll_tracker.get_recent_events()` och `rollback_events()` — metoder som **inte finns** i RollTracker. `hasattr`-checken gör att anropet tyst hoppas över, och embeden skriver ändå "Session Rollback Genomförd". `gm_override` "ändrar spelarresultat retroaktivt" men skriver bara en audit-JSON — ingen data ändras; bekräftelseflödet är TODO (rad 958) trots att embeden lovar "Bekräfta".
**Impact:** GM tror data rullats tillbaka/ändrats när inget hänt.
**Fix:** Implementera eller ta bort kommandona; låt saknade metoder faila högt (ta bort hasattr-tystnaden).

### K2. `/endsession` kraschar varje gång — två sessionssystem som aldrig möts
`src/commands/slash_admin_commands.py:109, 323–324` mot `src/roll_tracker.py:87, 95`

Admin-cogen genererar egna sessions-ID:n (`session_{epoch}`) medan trackern genererar sina (`YYYYMMDD_HHMMSS`). `get_session_stats(session_id)` returnerar därför alltid `"Session not found"` — statistik och AI-sammanfattning är döda kod. Och `end_session(session_id)` anropas med argument fast metoden tar inga → TypeError varje gång, fångas av generisk except. Sessionen arkiveras aldrig, presence återställs aldrig.
**Fix:** Låt admin-cogen använda returvärdet från `roll_tracker.start_session()` som enda källa för sessions-ID.

### K3. `!skada` är helt död — har aldrig fungerat sedan OB-tärningarna togs bort
`src/skjutdomihuvudet/commands.py:149, 155` mot `src/skjutdomihuvudet/dice_functions.py:265–298`

Kommandot unpackar tre värden (`rolls, total, is_ob`) men `roll_damage()` returnerar bara `(rolls, total)`. ValueError → "Ogiltigt vapen eller skadeformel" vid **varje** anrop, även `!skada pistol`. `is_ob` är en lämning från EON-versionen.
**Fix:** Ta bort `is_ob` från båda unpackningarna.

### K4. `/dgroll` kastar undantag vid VARJE lyckat anrop (regression)
`src/deltagreen/commands.py:720`

```python
f"...({skill_value}%{bonus:+d if bonus else ''})..."
```
Villkoret hamnar i format-spec:n → `ValueError: Invalid format specifier`. Resultatet hinner skickas, men except-blocket försöker sedan svara igen → `InteractionResponded` vid 100 % av anropen. Regression från bond-projektions-commiten.
**Fix:** `{f'{bonus:+d}' if bonus else ''}` eller förberäkna suffixsträngen.

### K5. Huvudträffar: omkastat delområde kan få fel rustningskod
`src/combat_manager.py:173–181`

När träfftabellen ger "huvud" kastas ett *nytt* 1T10 på delområdestabellen, men `code` (pansarkod) returneras från originalraden. Slag 17–20 (= hals, kod "3") kan ge delområde "ansikte" med halsens pansarkod — plats och kod motsäger varandra i embeden. Fördelningen förskjuts dessutom mot tryckt tabell (ansikte ~8 % i stället för tabellvärde).
**Fix:** Använd radens subloc+kod direkt, eller härled koden konsekvent efter omkastet. Validera mot regelboken.

### K6. `requirements.txt` bryter färsk installation
`requirements.txt:5` mot `src/core/knowledge_base.py:4`

Pinns `pinecone-client==2.2.4`, men koden gör `from pinecone import Pinecone` — klassen finns först i ≥3.0. Verifierat: ImportError på exakt 2.2.4. Eftersom `main.py` importerar knowledge_base på modulnivå **startar boten inte alls** efter färsk `pip install -r requirements.txt`.
**Fix:** Pinna aktuell `pinecone`-major (≥5), passa på att pinna övriga beroenden.

### K7. Trasig venv — ingen reproducerbar miljö
`venv/` + `start_bot.bat`

`venv/Scripts/` saknas helt (ingen python.exe, ingen activate.bat) och bas-Python (3.11.8) är avinstallerad. Site-packages innehåller bara halva trädet. `start_bot.bat` försöker aktivera activate.bat som inte finns → cmd faller tyst igenom till system-Python 3.13, som *råkar* ha deps. Boten körs alltså på tur utan att någon planerat det.
**Fix:** Återskapa venv (`py -3.13 -m venv venv` + `pip install -r requirements.txt`) och låt start-scriptet faila högt om activation misslyckas.

---

## 2. Säkerhet

### 2.1 Åtgärda nu

| # | Severity | Fynd | Plats |
|---|----------|------|-------|
| S1 | **HÖG** | **Pinecone-nyckel kvar i pushad git-historik.** `tests/test2.py` (raderad i commit `57cb1f7`, feb 2026) innehöll hårdkodad Pinecone-nyckel. Återställningsbar via `git show 57cb1f7^:tests/test2.py`; commiten är ancestor till `origin/master` → nyckeln ligger på GitHub. Commit-meddelandet säger "should be revoked immediately" men inget tyder på att rotation skedde. | Git-historik |
| S2 | **HÖG** | `tests/test.py` laddar `.env` och `print(f"Token: {token}")`. Unittest-discovery matchar filnamnet → produktions-Discord-token skrivs ut vid varje `python -m unittest discover`. Verifierat i granskningen. | `tests/test.py` |
| S3 | MEDEL | Anthropic-nyckelfragment (4 första + 4 sista tecken) printas till stdout som `start_bot.bat` omdirigerar till beständiga, aldrig roterade `bot_run.log` — tillsammans med spelarnas råa sökfrågor. | `knowledge_base.py:81`, `start_bot.bat` |
| S4 | MEDEL | Launchern sparar Discord-, Pinecone-, Anthropic- och OpenAI-nycklar **okrypterat** i `eon_bot_config.json` bredvid exe:n. | `launcher/eon_bot_launcher.py:402–424` |

**Åtgärd S1:** Rotera/revolka nyckeln på Pinecone-konsolen (rotation slår history-rewrite). Vill man även städa historiken krävs `git filter-repo` + force-push.
**Åtgärd S2–S4:** Radera/byt namn på `tests/test.py`; ta bort nyckelprinten (logga bara "nyckel hittad"); kryptera launcher-konfigen (keyring/DPAPI) eller acceptera risken medvetet på hobby-nivå.

### 2.2 Hygien

- `data/secret_manipulations.json` är **git-spårad** (just nu tom `{}`). Filen lagrar GM:s hemliga tärningsmanipulationer kopplade till spelar-ID:n — nästa session med aktiva manipulationer committas och pushas, inklusive vem som fuskat mot vem. Lägg i `.gitignore`.
- Opinnde beroenden: `pinecone-client==2.2.4` (avvecklad legacy-gren), `anthropic>=0.10.0` (uråldrigt golv), övrigt helt opinnde → icke-reproducerbart + supply-chain-risk. Pinna allt, kör `pip-audit` då och då.
- Råa undantagssträngar returneras till användare i embeds (`ai_handler.py:147`, `knowledge_base.py` ~160) — informationsläckage i låg grad, men logga detaljen internt och visa generiskt fel.
- `/ask`: användarfrågor interpoleras råa i Claude-prompten (prompt injection mot spelledarassistenten möjlig) och query-cachen växer obegränsat. Begränsad impact (svaren renderas bara som embed-text), men sätt cache-max och en kort systeminstruktion.

### 2.3 Vad som är rent (verifierat)

✅ Inga hemligheter i nuvarande träd (svep efter `pcsk_`, `sk-ant-api`, token-mönster: noll träffar)
✅ `.env` korrekt gitignore:ad och **aldrig committad**
✅ Git-historiken innehåller exakt **en** hemlighet (S1) — inga Discord-/OpenAI-/Anthropic-nycklar i någon historisk blob
✅ Ingen injektionsyta: inga `eval(`/`exec(`/`os.system`/`shell=True`/unsafe pickle/yaml någonstans
✅ Path traversal praktiskt omöjligt: filvägar byggs bara av Discord-snowflake-ints
✅ Alla 10 admin-kommandon anropar behörighetskontrollen — inget når utan GM-koll

---

## 3. Regelbuggar — spelet ljuger ibland

| # | Sev | Fynd | Plats |
|---|-----|------|-------|
| R1 | **HÖG** | **`/roll` bedömer framgång bakvänt:** `success = total >= mål`, medan hjälptext, legacy `!roll` och EON:s roll-under-regel säger `<=`. Statistikdatabasen har alltså loggat **inverterade framgångar** sedan slash-migreringen. | `slash_dice_commands.py:170` |
| R2 | **HÖG** | **Målpunkter slår 1T6 mot T10-tabell:** `randint(1,6)` jämförs mot rader 1–10 → raderna 7–10 onåbara, varje rad 1–6 får ~17 % i stället för 10 %. I HUGG/ansikte träffas "Hjärna" (värsta raden) 1 gång av 6 vid målpunkter. Variabeln heter fortfarande `roll_t10`. | `damage_tables.py:591–599` |
| R3 | **HÖG** | **Ryttare-/fyrfota-flaggor är no-ops:** parametrarna tas emot men används aldrig (döda imports av mount-tabellerna), ändå visar kommandona "Ryttare"/"Fyrbent mål" som utförda modifierare. UI:t ljuger för GM:n. | `combat_manager.py:246–301`, `slash_combat_commands.py:130–142` |
| R4 | **HÖG** | **Breaking point räknas inte om:** lagrat statiskt fält i agentfilen, men DG-regeln är BP = SAN − WP dynamiskt. WP-tapp via projection ska höja BP:t — spelare kan passera faktisk BP utan varning. | `deltagreen/agent_manager.py:340` |
| R5 | MEDEL | **Bonus/penalty-dice är flat ±10–40 %, inte RAW** (extra tiotals-tärning, lägsta/högsta). Ej statistiskt ekvivalent, interagerar annorlunda med crit/fumble-band. Kan vara medvetet — dokumentera valet eller implementera tens-die. | `deltagreen/dice_functions.py:155`, `commands.py:61` |
| R6 | MEDEL | **Star Wars Wild Die "Alt B"** kan dra bort en hel exploderad CP-kedja som "en tärning" i stället för högsta enskilda; docstringen medger tolkningen. Dokumentera husregeln spelar-synligt eller striktify mot RAW. | `starwars/dice.py:156–165` |
| R7 | MEDEL | **Tabelldata-avvikelser:** effekten `"Fall"` vs `"Faller"` blandas (STICK bröstkorg/ben mot alla andra); HUGG ben rad 8 har unika divisorer `"T/6, S/5"` (troligen transponeringsfel); STICK_AVSTAND_NORMAL saknar höger "vad" medan vänster har båda. Korrekturläs mot boken. | `damage_tables.py:382, 389, 163, 454–463`, `hit_tables.py:93–108` |
| R8 | LÅG | Star Wars: `doubled()` dubblerar även pips (4D+2→8D+4) — verifiera mot bokexempel; tie-break vid motstådda slag går till initiativtagaren (vissa bord spelar till försvararen) — dokumentera sidref. | `starwars/dice.py:78–80, 302–303` |

Verifierat korrekt (för att vara klar): Dragonbanes drake/demon-gränsmatte, fördel/nackdel före kritbedömning, Star Wars Wild Die-explosion med `MAX_EXPLOSIONS=100`-tak, samtliga svårighetsband Very Easy→Heroic, Delta Greens d100-kantfall (00→100, matchade tiotal/ental, lethality inkl. 00→20).

---

## 4. Kommandon som är döda eller fejkar framgång

Förutom K1–K3 ovan:

- **Legacy `!secret ex`** kraschar alltid: `result_embed` är None när `.add_field` anropas → AttributeError → DM "Ett fel uppstod". (`admin_commands.py:218` vs `295`)
- **Legacy `!allstats`/`!mystatsall`** → NameError: refererar global `embed_factory` som aldrig definieras i modulen. (`stats_commands.py:20, 96`)
- **`/player_stats`** svarar alltid fel: anropar `get_detailed_player_stats` som inte finns. (`slash_admin_commands.py:1173–1174`)
- **Avancerad statistik som aldrig renderar något:** session_comparison, anomalies, progression, personal_records, predictions, command_trends refererar statistiknycklar RollTracker aldrig returnerar. (`slash_utility_commands.py:778–799, 943–1063`)
- **`/stats period day/week/month`** erbjuds som val men koden hanterar bara `"all"` — övriga val returnerar tyst sessionstatistik. (`slash_utility_commands.py:209–214, 231`)
- **`!sdihelp` ljuger:** lovar "`!rull d20+3` fungerar fortfarande" — ingen parsning finns. (`skjutdomihuvudet/commands.py:433`)
- **Döda skelett:** `hit_system.py` (kraschar per design vid instansiering, används av ingen) och `migration/finalization_script.py` (508 rader fas-maskin som aldrig inkopplats).

---

## 5. Återkommande bugklass: blockerande I/O på event-loopen

Augusti-fixen (`ensure_ready`) täckte kunskapsbas-init + slash-vägen. Samma bugclass lever kvar här:

| Plats | Vad som blockerar |
|-------|-------------------|
| `commands/knowledge_commands.py:48,55` + `admin_commands.py:123` | `!ask`/`!allt`/`!endsession` anropar synk Claude/Pinecone direkt i async-ctx (sekunder–tiotals sekunder) |
| `slash_knowledge_commands.py:209–227, 333–348` | `/sök` och `/allt` gör `open().read()` över ALLA filer i `extracted_text/` synkront |
| `slash_dice_commands.py:611` + `dice_commands.py:506` | Tärningssimulering, 10 000–100 000 `unlimited_d6s`-iterationer på loopen ("defer"-kommentaren bevisar att man vet att det tar >3 s — men loopen blockeras ändå) |
| `roll_tracker.py:116–157` | Ny SQLite-connection + PRAGMA per kast, synkront; "database is locked" (5 s default-timeout = frusen bot), varefter except **sväljer slaget helt** — tyst statistikförlust. Ingen WAL, inga index |
| `spindel/small_spider_manager.py:345` + `spider_combat_manager.py:521` | Synkrona `anthropic.messages.create()` i async — fryser boten 2–10 s per attack om modulen aktiveras |

Rätt mönster finns redan i koden: `ai_handler.execute_with_timeout` använder `asyncio.to_thread` + timeout + progress-feedback. Gör det till mallen och svep listan ovan.

Relaterat: **ingen global felhantering finns** — ingen `tree.on_error`, ingen `on_command_error`. Oväntade fel = "The application did not respond" för användaren. (`config/feature_flags.py:46` har till och med en `enable_error_reporting`-flagga som aldrig refererats.)

---

## 6. Behörighet och fusköppningar

| # | Sev | Fynd | Plats |
|---|-----|------|-------|
| P1 | **HÖG** | **Demonisk inspiration utan GM-koll:** vem som helst kan skicka `demon=True` till `/roll` (sämsta tärningen ersätts med max). Legacy `--de` är värre: förfalskar hela tärningsuppsättningen osynligt. | `slash_dice_commands.py:110, 160–165`; `dice_commands.py:182–228` |
| P2 | **HÖG** | **Tre olika GM-guards med olika villkor:** admin-filen kräver manage_guild OCH roll i lista; manipulation/comment-filerna kräver ENDAST roll exakt `'Game Master'` (case-känsligt); utility kräver ENDAST manage_guild. En GM med roll "GM" kan använda vissa kommandon men inte andra. | `slash_admin_commands.py:54–74`, `slash_manipulation_commands.py:65`, `slash_comment_commands.py:22`, `slash_utility_commands.py:719` |
| P3 | **HÖG** | **Spindelns "endast GM"-kommandon saknar all kontroll:** `/spindelreset`, `/reset_småspindlar`, `/spawna_småspindlar` — vem som helst kan nollställa en strid. Dessutom DM:as "GM-rapporten" till den som körde kommandot, inte till GM:n. | `spindel/slash_spider_commands.py:104, 274`; `slash_small_spider_commands.py:54, 277, 346` |
| P4 | HÖG | **Dragonbane push-knapp saknar ägarkontroll:** vem som helst i kanalen kan pressa någons misslyckade slag och få credit/skuld. Star Wars-modulen gör rätt (`owner_id`-koll) — konventionsdivergens mellan systermoduler. | `dragonbane/commands.py:74–141` vs `starwars/commands.py:145` |
| P5 | LÅG | Admin-guards ligger i kommandokroppen i stället för `@app_commands.default_permissions` / `app_commands.check` → kommandona syns för alla, och nya kommandon har inget säkerhetsnät. Runtime-kollen är dock komplett idag (fail-closed på case). | `slash_admin_commands.py:54ff` |

**Fix:** En delad `require_gm(interaction)` + `app_commands.check`s i ett gemensamt admin-/guard-modul, använd överallt; owner_id i PushView; spindelns resets bakom flagga.

---

## 7. Dataintegritet och persistens

- **DG-agentfiler skrivs icke-atomärt** (`open('w')` truncar först) och `get_agent` sväljer korrupta filer → returnerar None → "agenten finns inte". Strömavbritt mitt i kampanj = karaktärspärmen borta, historik (SAN/HP/Bonds) med den. `delete_agent` är permanent utan papperskorg. **Fix:** temp-fil + `os.replace()`, skilj "saknas"/"korrupt" (.bak), flytta till `deleted/` i stället för remove. (`agent_manager.py:100–102, 128, 175`)
- **Samma mönster i `user_settings.py:30–48` och `manipulation_manager.py:31–49`:** icke-atomära skrivningar; vid korrupt JSON vid start nollställs allt tyst (`settings_cache = {}`). ColorHandler likaså (`color_handler.py:119–125`).
- **Relativa datavägar:** `user_settings.py:12`, `manipulation_manager.py:13`, `deltagreen/agent_manager.py:31`, `session_manager.py:21` löser `data/…` mot cwd, medan color_handler/main.py använder projektrot korrekt. Start från fel katalog → inställningar/manipulationer "försvinner" till en ny katalog. Launchern sätter dessutom ingen `cwd=` i Popen.
- **Manipulations-clampen kan misslyckas med att misslyckas:** vid 'olycka'/'förbannelse' med stor positiv modifierare clampas tärningssumman men verifieras aldrig att resultatet faktiskt misslyckas — tärningen "manipuleras" men slår ändå över målet, utan att GM:n får veta. (Spegelproblemet gäller 'lycka' med starkt negativ modifierare.) `manipulation_manager.py:212–218, 253`
- **DG-sessioner:** fuzzy-läs + exakt-skriv duplicerar skills i agentfilen ("firearms" vs "Firearms (Handgun)" blir två nycklar med separata värden, växer per session). Osanerat sessionsnamn i filnamn + sväljd sparfel → sessionsloggen raderas ändå ur active_sessions. (`session_manager.py:156, 170, 205, 215`)
- **Splatterpoäng:** rent minnesläge, global över hela boten (alla kanaler/servrar delar pool, restart nollställer mitt i session) — kontrast: InfectionDeck i samma fil persistelar per guild. (`skjutdomihuvudet/dice_functions.py:58–84`)
- **Session-state-tvist:** global `RollTracker.current_session` mot per-guild `current_sessions` i admin-cogen — två guilds med samtidiga sessioner skriver över varandras tracker-session. (`roll_tracker.py:87` vs `slash_admin_commands.py:40`)

---

## 8. Modul för modul

### 8.1 Core & main (`src/core/`, `src/main.py`, `launcher/`)

- ✅ `KnowledgeBase.ensure_ready()` är mönstergill (double-checked locking, `to_thread`, delat lås). Caveat: ingen timeout på låset (first-run modelldownload kan döda interaktionen ändå); misslyckad init cachas inte negativt.
- ⚠️ **`on_ready` kraschar vid reconnect:** registrering + cog-add körs igen → ClientException avbryter resten (synk, background-task). Dubbel command-sync mot rate limits vid varje resume. Task-referensen sparas aldrig (kan GC:as). Flytta till `setup_hook()` eller vakta med `_setup_done`. (`main.py:104–252`)
- ⚠️ `top_k`-parametern ignoreras (hårdkodade 15; `DEFAULT_TOP_K = 5` används aldrig). (`knowledge_base.py:132`)
- ⚠️ ColoredFormatter muterar loggregistret → ANSI-koder läcker in i `logs/eon_bot.log` (förstör grep/parse). (`logging_config.py:33–40`)
- ⚠️ Launcher kan dead-locka på full stderr-pipe (sekventiell läsning av två pipes). Använd två trådar eller `stderr=STDOUT`. (`eon_bot_launcher.py:57–75`)
- ⚠️ Embed-fabriken clampar field-värden mot Discords 1024-gräns på bara ett ställe — långa tärningsresultat kan ge HTTP 400. (`embed_factory.py`)
- Städa: tunga oanvända imports i `main.py` (numpy, tiktoken, whoosh, Pinecone, SentenceTransformer drar torch vid varje start — lazy-importa), döda feature-flaggor (`dual_mode_*`, `is_dual_mode_enabled` anropas ingenstans — konfiguration som aldrig styrt något).

### 8.2 EON slash-lager (`src/commands/slash_*.py`, ~4 900 rader)

- Copy-paste-kluster 1: `secret_roll`/`secret_ex`/`secret_count` ~390 rader samma skelett (GM-koll → parse → rulla → ephemeral embed → identisk DM-backup ×5). Perfect/fumble-logiken ordagrant kopierad från `ex_slash`. → En `run_secret_roll()`-helper sparar ~250 rader.
- Copy-paste-kluster 2: `roll`/`ex`/`count` ~480 rader samma pipeline. `/ex` har dessutom en avvikande inline-manipulation som plockar på privata `_save_manipulations()` — semantiskt annorlunda än `/roll`s. Felboilerplate `except Exception: …` ×~25 handlers ≈ 200 rader → en cog-nivå error handler.
- **Arkitekturfälla:** `import main` vid anropstillfälle + `sys.path.append` som växer obegränsat vid varje kast, för att nå globals — cirkulärt beroende som bara fungerar för att det sker lazy. Omöjligt att testa isolerat. Injicera beroenden via cog-konstruktorn. (`slash_dice_commands.py:29–42, 77–83, 287–291`)
- **Ephemeral-bugg:** hela `/kommentarer`-gruppen svarar publikt (aktivera/inaktivera/stil/lista broadcastar spelarinställningar till kanalen). `/chance` blandar ephemeral-progress med publikt slutresultat. (`slash_comment_commands.py:53, 85, 133, 178, 240, 290, 318`)
- **DM-krascher:** ingen `guild_only` någonstans — `interaction.user.guild_permissions` i DM = AttributeError före try-blocket, utan global error handler = tyst "did not respond". (`slash_admin_commands.py:61–66, 108, 232` m.fl.)
- Svenska/engelska-blandningen fortsätta skapa verkliga buggar (samma kategori som `/sök`-NameError:n): parameter `målpunkter` men variabler `malpunkter`; period-valen day/week/month ohanterade.

### 8.3 Delta Green (`src/deltagreen/`, ~3 700 rader)

- K4-regressionen ovan, plus: `/dggmset` och `/dggmreset` muterar agentdata direkt och **bypasserar** manager-invarianterna (WP→0 sätter inte unconscious; SAN-sänkning ger ingen BP-kontroll) — två kodvägar, olika regler. Dirigera GM-ändringarna genom `modify_hp/wp/san`. (`commands.py:1158–1159, 1724–1729`)
- Felpath utan `is_done()`-koll i ~15 handlers → `InteractionResponded` vid fel efter defer. Gemensam `_send_error()`-helper löser systemiskt. (`commands.py:127–134` m.fl.)
- `parse_san_loss` returnerar tyst 0 vid oparsbar input ("d4", mellanslag, unicode-minus) — SL tror monstret drar 1d6 men agenterna förlorar ingenting. Validera i kommandolagret. (`dice_functions.py:264–265`)
- Copy-paste: GM-preamble ×5, `dg_agent_roll` ≈ `dg_gm_roll` (~70 rader), bond-matchning duplicerad. Helpers skulle spara ~400 rader och göra felklasserna omöjliga.
- ✅ Mekanikkärnan (dice_functions, san_check_cache, project_onto_bond) är väldesignad, korrekt mot Agent's Handbook, täckt av 43 enhetstester.

### 8.4 Dragonbane & Star Wars (`src/dragonbane/`, `src/starwars/`)

- P4 ovan (push-ägarkontroll) + push-knappen förlorar vald grundegenskap (`PushView` skickas utan `attribute` → pressning slumpar alltid tillstånd, medan `/dod_pressa` stödjer deterministisk mappning). Ad-hoc `Random()` i båda vägarna bryter modulens egen injicerbarhetskonvention. (`dragonbane/commands.py:125, 210, 276`)
- **Dragonbane saknar bestående tester** trots att handoff-dokumentet påstår "tärningslogiken enhetstestad" — testerna finns bara som ad-hoc-skript *i dokumentet*. Spepla `test_starwars_dice.py`-mönstret (SequenceRandom) för skill check/advancement/initiativ.
- Smått: `difficulty_band` returnerar "Heroic" för negativa totaler (kosmetiskt absurt); `pips_warning` är död kod; timeout 60 vs 120 s mellan modulerna utan motivering; initiativparsning + `on_timeout` + felmeddelandemönster duplicerade ordagrant mellan modulerna → extrahera till core (men **inte** tärningsmotorerna — de är fundamentalt olika och ska vara separata).

### 8.5 SkjutdomIHuvudet (`src/skjutdomihuvudet/`)

- K3 (`!skada`) + R-listans vapendata: "basebollträ" (2d6+1) och "baseballbat" (2d6) är samma vapen med olika skada; HIT_ZONES ger torso endast 2/20 — värt koll mot boken.
- `!splatter use <beskrivning>` truncerar tyst till första ordet (positionsparam fångar ett token); parametern heter dessutom `num_players` men används som beskrivningsfält. (`commands.py:597, 624`)
- **Migration-verdict: MEDEL.** 10 prefix-kommandon à ~640 rader; spelmotorn (dice_functions.py) är ren Python utan discord-beroenden — allt arbete är mekanisk omskrivning av Discord-lagret, ~4–8 timmar med `slash_dice_commands.py` som mall. Kopplingen till `roll_tracker` är delvis en **myt**: exakt 3 `log_roll`-anrop, signaturkompatibla, kan även släppas. `color_handler` (6 anrop) kan bytas mot `embed_factory` i samma veva — SDIH bygger embeds manuellt idag, vilket är den egentliga stilavvikelsen. Ingen feature flag finns för SDIH (enda modulen utan) — lägg till vid migreringen.

### 8.6 Spindeln (`src/spindel/`, ~2 400 rader, avstängd)

- **Verdict: FRISK** — dormant-but-clean. Lazy import bakom flaggan (läses aldrig in vid startup), alla importer relativa och löser sig, inga referenser till gamla sökvägar, flytten i commit `827b694` gjord ren (datumsökvägen till och med kommenterad). Aktiveras den idag startar den.
- Men fixa före första riktiga session: E5 (blockerande AI-anrop), P3 (GM-auth), samt `interaction.response` anropat två gånger i felpaths (`InteractionResponded` ohanterat). (`slash_spider_commands.py:98/112`, `slash_small_spider_commands.py:197/286`)
- Småspindlar: namnåteranvändning kan ge dubbletter medan döda spindlar ligger kvar; ingen persistens (gigantspindeln sparar JSON per guild — asymmetrin bitar vid omstart mitt i strid). (`small_spider_manager.py:139–168`)
- Kvarlämnade AI-artefakter: "Infoga här resten av din befintliga kod…" som kommentar. (`dice_functions.py:86–88`)

### 8.7 Legacy prefix-lager — verdict: **säkert att radera nu**

- Enda blockern är `main.py` själv: imports (rad 35, 39–43) + registreringar (rad 179–201) måste bort i **samma ändring**, annars kraschar starten. Trivialt.
- Slash-paritet finns för samtliga kommandon inklusive GM-hemligheterna och statistiken. Två legacy-kommandon är redan trasiga i drift (se §4) — det är inte reservsystem, det är ruttna.
- `is_dual_mode_enabled()` anropas **ingenstans** — flaggorna har aldrig styrt något. Rensa i samma svep.
- ⚠️ Rör INTE `roll_tracker.py` i samma svep — SDIH är aktiv konsument via `main.py:183`.
- `utils/`-skripten är engångsarkeologi: regex-patchare mot en main.py-layout som inte längre finns, `index_knowledge.py` använder borttagen openai<1.0-API + FAISS medan produktion är Pinecone, `extract_all_pdfs.py` hårdkodar Tesseract-sökväg. Arkivera eller radera — inget behöver bevaras. Inga hemligheter i något av dem (nycklar hämtas från .env — bra).

---

## 9. Duplicering — refactor-karta

| Kopia | Var | Åtgärd |
|-------|-----|--------|
| `parse_effect_code()` ×**3** | `damage_tables.py:469–537`, `spider_damage_tables.py:438–482`, `small_spider_tables.py:177–217` — **redan divergerade** (originalet kraschar på None och slänger operatorlösa nycklar; kopiorna är None-säkra och sätter base_damage i stället) | Lyft kanonisk version till `src/core/`, importera överallt |
| Secret-roll-skelett ×3 | `slash_admin_commands.py:513–906` | `run_secret_roll()`-helper (~250 rader) |
| Roll-pipeline ×3 | `slash_dice_commands.py:98–577` | `eon_roll_pipeline()` (~300 rader + ~200 raders felboilerplace via central error handler) |
| DG-handler-skelett ×15 | `deltagreen/commands.py` | `_resolve_agent_or_reply()` + `_run_dg_check_and_respond()` (~400 rader) |
| Initiativparsning, `on_timeout`, felmeddelanden | dragonbane ↔ starwars | `parse_character_list()`, `BaseTimedView`, `_respond_error()` i core |

**Förslag på splitt av jättefilerna** (från slash-granskningen): `admin/session_admin.py` + `admin/secret_rolls.py` + `admin/gm_tools.py` + `admin/guards.py` (lösar P2 samtidigt); `utility/help_commands.py` + `utility/stats_commands.py` (gemensam embed-byggare dödar den döda statistiken) + `utility/rules_commands.py`; och en `eon/`-modul med den delade rull-pipelinen — då blir den planerade `/eon_`-omdöpningen i praktiken bara namnbyten i en fil, och varje modul hamnar under ~400 rader.

---

## 10. Tester & repo-hygien

**Faktisk testkörning** (system-Python 3.13.5, venv trasig — se K7):

| Svit | Resultat |
|------|---------|
| test_starwars_dice.py | 20/20 OK |
| test_deltagreen_agent_manager.py | 15/15 OK |
| test_deltagreen_projection.py | 14/14 OK |
| test_deltagreen_project_flow.py | 5/5 OK |
| test_deltagreen_san_cache.py | 9/9 OK |
| **Totalt** | **63 OK, 0 fail, 3 samlingsfel** (test_background, test_embedding, test_knowledge_base_async — se nedan) |

- **Kärnmotorerna har NOLL tester:** dice_parser (huvudparsern), dice_engine, embed_factory (871 rader), roll_tracker (680), dragonbane/dice.py, sdih/dice_functions.py, hela spindeln, manipulation_manager, combat/tabeller. Prioritera dice_parser + dice_engine — rena funktioner, billiga att testa, högst trafik.
- **Discovery-sprängare:** `tests/test_background.py` (importerar pensionerad chargen-kod, kraschar dessutom i sin egen except-hantering på cp1252-emoji), `tests/test_embedding.py` (nätverksanrop vid import, dött openai<1.0-API). Radera båda + rot-filen `test_chargen.py`. README:n marknadsför fortfarande `!chargen` med 32 steg (rad 27, 127–130) — städa.
- **Falskt grönt ljus:** `test_slash_commands.py`/`test_comment_system_final.py` skriver `[FAIL]` men avslutar alltid exit 0 ("Redo för deployment!" oavsett). `test_main.py` är ingen test utan en alternativ botstart mot riktig Discord.
- **debug_-filerna:** `debug_user_info.py` är **lastbärande** (importeras av main.py:171 vid DEBUG_MODE=true — inte säker att ta bort!), `debug_permissions.py` död (säker att radera), `debug_slash_commands.py` farligt ops-verktyg (loggar in mot produktion och gör **global** tree.sync).
- **Infrastruktur:** ingen conftest.py/pytest.ini/CI; två parallella importrötter (produktion: `from core.x`, tester: `from src.core.x`) — en conftest som normaliserar sys.path + pytest i dev-requirements fixar fällan.
- ✅ Kvaliteten där tester FINNS är oväntat hög: deterministisk RNG-injektion, regelverksreferenser i kommentarerna, disk-persistens verifierad genom återläsning, race-test av kunskapsbasen utan API-nycklar.

---

## 11. Det som faktiskt är bra

1. **Tärningsmotorerna är senior-klass:** rena dice.py utan discord-importer, injicerbar Random, `MAX_EXPLOSIONS`-tak testat med AlwaysSixRandom, dataclass-resultat med rådata (CP-knappen kan räkna om utan omslag), sidhänvisningar till regelböcker i docstrings. Ovanligt disciplinerat.
2. **ensure_ready-fixen** är mönstergill double-checked locking med förklarande kommentarer som bevarar varför.
3. **Säkerhetsbaslinjen är solid för hobby:** ingen injektionsyta, path traversal omöjlig, .env aldrig committad, alla admin-kommandon fail-closed, subprocess endast i GUI-launchern med list-args.
4. **Fail-högt-tabellkoden:** ogiltiga slag och okända områden raisar ValueError som visas för användaren — mycket lättare att upptäcka än tysta felresultat.
5. **Statistikpersistensen:** SQLite med idempotent schemamigration vid startup, aggregeringar i SQL, ingen minnesuppbyggnad — boten kan ligga uppe hur länge som helst.
6. **Delta Green-mekaniken** är korrekt mot Agent's Handbook och täckt av 43 tester — regressionen (K4) sitter i Discord-lagret, inte reglerna.
7. **Per-spel-footers i embed-fabriken** som krediterar modulskaparna (Jonas/Dragonbane, WEG/Star Wars) — fin detalj.

---

## 12. Prioriterad åtgärdsplan

### 🔥 Omedelbart (innan nästa spelsession)
1. **Rotera Pinecone-nyckeln** om det inte skeddes i feb 2026 (S1)
2. Fixa `/dgroll` f-strängen (K4) — en rad
3. Byt `>=` till `<=` i `/roll` (R1) — och notera att statistikhistoriken är inverterad
4. Skala målpunkter mot T10-tabellen (R2)
5. Fixa huvud-delområdets pansarkod (K5) — validera mot boken
6. Fixa `!skada`-unpacken (K3) — två rader
7. Ta bort eller implementera `/session_rollback` + `/gm_override`; fixa `/endsession`-signatur och sessions-ID-källan (K1, K2)
8. GM-koll på `demon=True` (P1)
9. Radera `tests/test.py` (token-utskriften, S2)
10. Återskapa venv + korrekt pinecone-pin (K6, K7)

### 🧹 En kväll: hygien
11. Radera döda testfiler (test_chargen, tests/test_background, tests/test_embedding) + städa README:s !chargen-påståenden
12. `.gitignore:a` `data/secret_manipulations.json`; ta bort nyckelfragment-printen; loggrotation på bot_run.log
13. Radera legacy-lagret (6 filer + main.py-imports + dual_mode-flaggor) — paritet finns, två kommandon är redan ruttna
14. Radera/arkivera utils-engångsscript, hit_system.py, finalization_script.py, debug_permissions.py
15. Global `tree.on_error` + `@app_commands.guild_only` på guild-kommandon

### 🛡️ Nästa fas: robusthet
16. `asyncio.to_thread`-svep enligt §5 (inkl. SQLite: WAL + långlivad connection + index)
17. Atomära skrivningar + .bak överallt (DG-agenter, user_settings, manipulationer, colors)
18. Absoluta datavägar (projektroten) + cwd i launchern
19. En gemensam `require_gm()` + app_commands.checks; owner_id i Dragonbane PushView
20. Dragonbane-tester (spepla Star Wars-mönstret) + dice_parser/dice_engine-täckning
21. Dynamisk breaking point (SAN − WP); dirigera GM-set/reset genom manager-invarianterna

### 🏗️ Refactor-sprint (efter §9-kartan)
22. Extrahera `parse_effect_code()` till core (divergensen är redan verklig)
23. Dela slash_admin/slash_utility enligt modulförslaget; bygg `eon/`-modul med gemensam pipeline
24. SDIH → slash (4–8 h mekaniskt arbete; fixa K3 först så migrerar du ett levande kommando)
25. Vid spindel-aktivering: to_thread på AI-anrop, GM-auth, is_done()-kollar först

---

*Genererad av 8 parallella granskningsagenter (Claude Code), syntetiserad 2026-08-23. Alla fynd är read-only-verifierade mot koden; flera tärningsmatik-buggar bevisade genom isolerad körning.*
