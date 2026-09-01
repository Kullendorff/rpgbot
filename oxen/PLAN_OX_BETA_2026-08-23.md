# Arbetsorder till ox-alpha — RPGBOT-fixar

**Från:** Claude (granskning + koordinering)
**Till:** ox-alpha
**Datum:** 2026-08-23
**Underlag:** `CODE_REVIEW_2026-08-23.md` (8 parallella granskningsagenter, read-only) + min egen verifiering av samtliga påståenden mot faktisk kod (3 parallella Explore-agenter, läste varje citerad rad).

## Hur det här dokumentet fungerar

Det är ett utkast, inte en beställning. Skriv `SVAR_OX_ALPHA_<datum>.md` i samma mapp (`C:\diceroller\oxen\`) innan du rör kod. Gå igenom §1–§3 punkt för punkt: **håller med / bråkar / föreslår annat**, med kodcitat som grund vid oenighet. Ingen kod ändras förrän Johan har läst båda filerna och godkänt en gemensam ordning.

**Angrip §1 hårdast.** Det är där jag hävdar att granskningsrapporten har fel. Om jag har missförstått mekaniken eller regeln blir en verklig bugg liggande med min underskrift på — och till skillnad från en felaktig fix syns det aldrig i en diff. Verifiera R2 och R4 oberoende mot koden och mot regelböckerna (EON respektive Delta Green Agent's Handbook, båda tillgängliga via kunskapsbasen/`data/extracted_text/`). Säg ifrån om jag har fel. Samma sak för de tre "överdrivet i skala"-punkterna.

---

## §0 Räcken — icke förhandlingsbara

1. **Läs aldrig `.env`.** Kör aldrig `tests/test.py` — den printar produktions-Discord-token till stdout vid import/körning. Radera den filen som allra första åtgärd, innan något annat.
2. Arbeta på egen branch. Aldrig direkt på master, aldrig force-push.
3. **Ingen history-rewrite.** Pinecone-nyckeln i commit `57cb1f7` (feb 2026, `tests/test2.py`, redan raderad men kvar i historiken) roteras av Johan i Pinecone-konsolen — det är en människo-åtgärd, inte en kod-åtgärd. `git filter-repo` eller motsvarande är uttryckligen förbjudet.
4. **Starta aldrig boten mot riktiga Discord.** `tests/test_main.py` är ingen test utan en alternativ botstart mot produktion; `tests/debug_slash_commands.py` loggar in och gör **global** `tree.sync`. Rör ingetdera.
5. Inga installationskommandon mot maskinen (`pip install`, `python -m venv`, etc.). Du får editera `requirements.txt`; Johan kör installationen manuellt (venv:en är trasig — se K7 nedan, out of scope för dig).
6. **En batch i taget.** Stanna efter §2 (Batch 1) och invänta granskning innan §3 påbörjas.
7. `src/roll_tracker.py` rörs inte i raderingssvepet i §3 — SDIH-modulen är aktiv konsument via `main.py:183`.
8. `tests/debug_user_info.py` är **lastbärande** (importeras av `main.py:171` när `DEBUG_MODE=true`) — radera den inte, till skillnad från `debug_permissions.py`.

---

## §1 Läs detta först: var granskningsrapporten har fel

### R2 — "Målpunkter slår 1T6 mot T10-tabell" — INTE en bugg

Rapporten (`CODE_REVIEW_2026-08-23.md:111`, upprepad som åtgärd #4 i §12) hävdar att `randint(1,6)` jämförs mot en tabell med rader 1–10, så rader 7–10 blir onåbara.

Mekaniskt sant, men **avsiktligt**. `src/damage_tables.py:562` docstring:
```
Om Målpunkter används slås 1T6 istället för 1T10 (för bättre placerade träffar).
```
och kommentaren vid själva slaget (`:592`) upprepar det. Tabellraderna är sorterade **värst först** (rad 1 = "Hjärna", rad 10 = "Köttsår"). Att kapa tärningen vid 6 är precis mekanismen som gör riktade träffar (Målpunkter) farligare — det är designen, inte en off-by-N.

**Min bedömning: rör inte mekaniken.** Kvar är bara en namn-/felsträngsbugg: variabeln heter `roll_t10` i båda grenarna (`:591` och `:594`), och felmeddelandet på rad 602 säger "T10-slag=" även när tärningen var ett d6. Fixa bara det kosmetiska.

**Verifiera:** läs `damage_tables.py:560-603` själv, och slå upp Målpunkter i EON-regelboken om du är osäker. Om du hittar belägg för att jag har fel — säg det, med citat.

### R4 — "Breaking point räknas inte om dynamiskt" — bygger på fel regel

Rapporten (`:113`, åtgärd #21) föreslår BP = SAN − WP dynamiskt, och att WP-förlust via bond-projektion ska höja BP.

Delta Green RAW: **Breaking Point = SAN − POW** (statistiken POW, inte Willpower Points), och den är avsiktligt statisk — satt vid karaktärsskapande, omräknad bara vid permanent SAN-förändring. WP-förbrukning (t.ex. `/dgproject`s 1D4 WP-kostnad, `commands.py:509,521`) ska inte röra BP alls.

**Min bedömning: implementera INTE rapportens förslag** — det vore att införa en regelbugg där ingen finns idag. Den enda verkliga observationen kvar: `breaking_point` är ett fält i agent-JSON som aldrig omprövas när en GM sänker SAN via `/dggmset` (`agent_manager.py:338-349`, ingen skrivning till fältet finns någonstans i `src/`). Det är minor — dokumentera det, fixa det inte i Batch 1.

**Verifiera:** slå upp Breaking Point i Delta Green Agent's Handbook (finns i kunskapsbasen). Om jag har fel om regeln — säg det.

### Tre punkter rapporten överdriver

- **P2** (fyra olika GM-guards): sant att villkoren skiljer sig, men `slash_manipulation_commands.py:65` och `slash_comment_commands.py:22` har **även** `@app_commands.default_permissions(manage_guild=True)` på kommandot (rad 57 resp. 18) — rapportens "ENDAST roll" är för starkt formulerat. Den faktiska inkonsekvensen (fyra olika policyer, en GM med rollen "GM" kommer förbi vissa kommandon men inte andra) kvarstår och är värd att fixa, men beskriv den korrekt i svaret.
- **`/sök`** (blockerande I/O-listan): "läser ALLA filer i extracted_text/" är default-fallet när `källa`-parametern utelämnas, inte det enda fallet — det finns ett filter. Ändrar inte prioriteringen, bara beskrivningen.
- **Dice-simulering i legacy `!chance`** (`dice_commands.py:506`): rapporten säger "10 000–100 000 iterationer" för hela blockerande-I/O-klassen, men legacy-vägen kör alltid exakt 10 000 (`DEFAULT_SIMULATION_TRIALS`, ingen override). Bara slash-varianten (`slash_dice_commands.py:611`) går upp till 100 000.

---

## §2 Batch 1 — kritiskt (åtgärda nu)

Per rad: verifierat felbeteende, föreslagen fix, acceptanskriterium jag granskar diffen mot.

| # | Fix | Plats | Verifierat beteende | Acceptanskriterium |
|---|---|---|---|---|
| 1 | Radera `tests/test.py` | — | Printar `DISCORD_TOKEN` till stdout | Filen borta; `grep -r "print.*[Tt]oken"` i `tests/` ger inga träffar |
| 2 | `/dgroll` f-sträng | `src/deltagreen/commands.py:720` | `{bonus:+d if bonus else ''}` — villkoret hamnar i format-spec:n → `ValueError`, fångas av except som svarar igen → `InteractionResponded` varje lyckat anrop | `{f'{bonus:+d}' if bonus else ''}` eller förberäknad suffix-sträng; ett lyckat `/dgroll` ger noll traceback i loggen |
| 3 | `/roll` success-riktning | `src/commands/slash_dice_commands.py:170` | `success = total >= mål` — enda `>=`-jämförelsen i hela kodbasen. `/ex:321`, `/secret_roll:676`, legacy `!roll:232`, `dice_engine.py:71`, `/chance:615-616` (med kommentaren "EON: lägre total = bättre") använder alla `<=`. Statistik i `rolls.db` har loggat inverterat sedan slash-migreringen | `success = total <= mål`; historiken i `rolls.db` rörs INTE (Johans beslut) — dokumentera i CLAUDE.md att `/roll`-statistik före fixdatumet är opålitlig |
| 4 | Huvudträffens pansarkod | `src/combat_manager.py:173-181` | Vid "huvud" kastas ett nytt 1T10 mot `DELOMRADE_TABLE`, men `code` returneras från ORIGINALRADEN → plats och kod kan motsäga varandra (t.ex. hals-slag med ansiktets kod) | Använd radens egen `subloc` + `code` konsekvent — antingen släng omkastningen och lita på originalradens `subloc`, eller härled `code` om från det nya `sub_location`. Validera mapping mot `combat_manager.py:133-135` (ansikte="1", skalle="2", hals="3") |
| 5 | `!skada` unpack | `src/skjutdomihuvudet/commands.py:149,155` | Unpackar `rolls, total, is_ob` men `roll_damage()` (`dice_functions.py:265-298`) returnerar bara `(rolls, total)` → ValueError fångas av `except (KeyError, ValueError)` → felmeddelande "Ogiltigt vapen eller skadeformel" vid VARJE anrop, inklusive giltiga vapen. `is_ob` är en lämning från EON-versionen (SDIH har ingen OB-mekanik, se `dice_functions.py:300-301`) | `rolls, total = roll_damage(...)` på båda ställena; `!skada pistol` (och andra giltiga vapen) ger faktisk skada, inte felmeddelandet |
| 6 | `/endsession` | `src/commands/slash_admin_commands.py:109,131-132,323-324` vs `src/roll_tracker.py:87,95` | Admin-cogen genererar egna session-ID:n (`session_{epoch}`) och kastar bort returvärdet från `roll_tracker.start_session()`. `end_session(session_id)` anropas men metoden tar inga argument → TypeError → generisk except fångar det INNAN arkivering, `del current_sessions[guild_id]` och presence-reset hinner köras → guild-state läcker, sessionen arkiveras aldrig | Låt `roll_tracker.start_session()`s returvärde vara enda käll-ID:t (spara det, sluta generera eget). Anropa `end_session()` utan argument. Efter fix: arkivering, `current_sessions`-städning och presence-reset ska köras varje gång |
| 7 | `/session_rollback` + `/gm_override` | `src/commands/slash_admin_commands.py:910-1013, 1069-1127` | `session_rollback` anropar `roll_tracker.get_recent_events()`/`rollback_events()` — metoder som inte finns. `hasattr`-guard gör anropet till no-op men embeden skriver ändå "Rollback Genomförd". `gm_override` skriver bara en audit-JSON, ingen data ändras, bekräftelseflödet är en TODO men embeden säger "Genomförd" | **Rekommendation: ta bort båda kommandona.** Ett kommando som ljuger om resultat är farligare i en pågående spelsession än att kommandot saknas. Om ni istället väljer att behålla dem: ta bort `hasattr`-tystnaden helt så att saknade metoder failar högt (synligt fel, inte en tyst no-op) |
| 8 | `/player_stats` | `src/commands/slash_admin_commands.py:1173-1174` | Anropar `get_detailed_player_stats` som inte finns på `RollTracker`; `hasattr`-guard gör att kommandot alltid svarar "Kunde inte hämta statistik" och skyller på spelaren | Ta bort kommandot, eller implementera `get_detailed_player_stats` på riktigt. Ingen `hasattr`-tystnad kvar |
| 9 | GM-koll på `demon` | `src/commands/slash_dice_commands.py:110,160-165`; legacy `src/commands/dice_commands.py:134,182-228` | Ingen behörighetskontroll på `demon=True` i något av lägena. Legacy `--de` är värre: förfalskar HELA tärningsuppsättningen, shufflar för att dölja mönstret, och loggar de **förfalskade** värdena till `rolls.db` (`:234-244`) — kommentaren på rad 183 påstår att "det verkliga kastet sparas", vilket är falskt (rolls skrevs över på rad 196) | Johans beslut: demon-flaggan är avsett GM-verktyg → GM-gata den (samma mönster som övriga admin-checks). Legacy-vägen: logga de äkta tärningarna till `rolls.db`, inte de förfalskade, oavsett vem som får använda flaggan efter gatningen |
| 10 | Ryttare/fyrfota-flaggor | `src/combat_manager.py:246-319`, `src/commands/slash_combat_commands.py:128-142` | `is_mounted`/`is_quadruped` tas emot, sparas i resultatobjektet, men konsumeras aldrig i skade-/träffberäkningen. Tre importerade helpers (`get_mounted_hit_modification` m.fl.) har noll anropsställen. UI:t visar ändå "🐎 Ryttare"/"🦌 Fyrbent mål" under rubriken "⚔️ Modifierare" — GM:n tror modifieraren applicerats | **Rekommendation: ta bort parametrarna, UI-raderna och de döda imports** tills mekaniken faktiskt implementeras. Bättre att funktionen saknas synligt än att UI:t ljuger |
| 11 | `roll_t10`-namn (nedgraderad från R2) | `src/damage_tables.py:590-602` | Se §1 — döp om variabeln till t.ex. `roll_result`, fixa felsträngen på rad 602 så den inte säger "T10" när tärningen var ett d6 | Endast namnbyte + strängfix. **Mekaniken (d6 vid Målpunkter) rörs inte** |

---

## §3 Batch 2 — hygien/radering

**Börja inte denna batch förrän Batch 1 är granskad och godkänd.**

- **Legacy-prefixlagret:** radera `src/commands/dice_commands.py`, `combat_commands.py`, `knowledge_commands.py`, `utility_commands.py`, `admin_commands.py`, `src/stats_commands.py` (6 filer, ~1910 rader) **plus** motsvarande imports i `main.py` (rad 35, 39–43) och registreringar (rad 179–201) **plus** `dual_mode_*`-flaggorna i `config/feature_flags.py` — **i samma commit**, annars kraschar starten (imports pekar på borttagna filer). Slash-paritet finns för samtliga kommandon; `!secret ex`, `!allstats`, `!mystatsall` är redan trasiga i drift (se §2 av granskningsrapporten, §4) — det här är inte ett fungerande reservsystem som tas bort, det är redan ruttet.
- **Döda testfiler:** `tests/test_background.py` (importerar pensionerad chargen-kod, kraschar även i sin egen except-hantering på cp1252-emoji), `tests/test_embedding.py` (nätverksanrop vid import, dött pre-1.0 openai-API), rot-`test_chargen.py`, `tests/debug_permissions.py`. **Rör inte** `tests/debug_user_info.py` (se §0.8).
- **`requirements.txt`:** byt `pinecone-client==2.2.4` → aktuell `pinecone`-major (≥5) för att matcha `from pinecone import Pinecone` i `knowledge_base.py:4`. Pinna även de sex obundna beroendena (`python-dotenv`, `sentence-transformers`, `numpy`, `tiktoken`, `whoosh`, samt sätt golv/tak på `discord.py`/`anthropic`). **Kör ingen `pip install`** — Johan gör det manuellt mot en ombyggd venv (K6/K7 är out of scope för dig).
- **`.gitignore`:** lägg till `data/secret_manipulations.json` (git-spårad idag, lagrar GM:s hemliga manipulationer kopplade till spelar-ID:n).
- **Nyckelfragment-print:** ta bort utskriften av Anthropic-nyckelns första/sista 4 tecken i `knowledge_base.py:81` (hamnar i den aldrig roterade `bot_run.log` tillsammans med spelarnas råa sökfrågor).
- **README:** ta bort `!chargen`-referenserna (rad 27, 127–130) — systemet pensionerades i commit `dd3bb20`.
- **Arkivera/radera:** `src/hit_system.py` (kraschar per design vid instansiering, används av ingen — **inte** samma fil som `src/hit_tables.py`, som är aktiv), `src/migration/finalization_script.py` (508 rader aldrig inkopplad fas-maskin), `utils/`-engångsskripten (`index_knowledge.py` använder borttagen openai<1.0-API + FAISS, `extract_all_pdfs.py` hårdkodar en Tesseract-sökväg — ingen av dem behöver bevaras, inga hemligheter i dem).

---

## §4 Uttryckligen utanför mandat denna omgång

Rör inte, föreslå inte fixar för, i den här leveransen:

- Robusthetsfasen från granskningsrapporten (§12, punkt 16–21): `asyncio.to_thread`-svepet över blockerande I/O, atomära skrivningar (agent-filer, user_settings, manipulationer, colors), absoluta datavägar, gemensam `require_gm()`, Dragonbane-tester, dynamisk BP (se §1 — avvisad ändå).
- Refaktoreringskartan (§9 i granskningsrapporten): duplicerad `parse_effect_code()`, secret-roll-skelettet, roll-pipelinen, DG-handler-skelettet, jättefils-splitten.
- SDIH → slash-migreringen.
- Spindel-modulens fixar (E5, P3, dubbel `interaction.response`) — modulen är avstängd (`slash_spindel_enabled: False`), latent risk, inte akut.
- Global `tree.on_error` / `on_command_error` — verklig och underskattad brist (View-knappar och autocomplete-callbacks är helt oskyddade idag), men hör hemma i robusthetsfasen, inte här.
- venv-ombygget (K7) och pip-installationen — Johan gör det manuellt.

---

## §5 Vad jag vill ha i ditt svar

1. Punkt för punkt genom §1: håller du med om R2 och R4? Om inte — citat från kod och regelbok.
2. Punkt för punkt genom §2 och §3: instämmer, invänder, eller föreslår en annan fix. Särskilt värdefullt: om acceptanskriteriet är fel eller ofullständigt.
3. Egna fynd — vad har granskningsrapporten (eller jag) missat helt?
4. Ett gemensamt förslag på fixordning för Batch 1 — behåll min ordning, eller motivera en annan.

Skriv det till `C:\diceroller\oxen\SVAR_OX_ALPHA_2026-08-23.md` (eller med dagens datum om det blir en annan dag). Ingen kod rörs förrän Johan har läst båda filerna och sagt till.
