# Handoff: Dragonbane-modul (för Claude Code)

Den här filen beskriver en färdig ändring som lagts in i repot via Cowork. Mounten i
Cowork-sandboxen låg efter på de senast skrivna filerna, så commit och test gjordes
INTE där. Din uppgift: verifiera integritet, smoke-testa, committa och pusha. Radera
gärna den här filen efteråt (eller behåll som changelog, ditt val).

## Vad som gjorts

En komplett Dragonbane-modul (Drakar och Demoner) har bultats in i boten, byggd på
samma mönster som `src/deltagreen/`: eget paket, Cog med `@app_commands.command`,
embeds via `embed_factory`, registrering i `on_ready` bakom en feature flag.

Ursprunglig tärninglogik och kommandouppsättning är byggd av Jonas
(https://github.com/jonsal/dragonbane). Den anpassades till botens arkitektur och
regelrättades på vägen in.

### Nya filer
- `src/dragonbane/__init__.py`
- `src/dragonbane/dice.py` (ren, testbar tärninglogik, inga discord-beroenden)
- `src/dragonbane/commands.py` (Cog + PushView + `register_slash_dragonbane_commands`)

### Ändrade filer
- `src/core/embed_factory.py` : nya metoder `dragonbane_skill_result`,
  `dragonbane_expression_result`, `dragonbane_damage_result`,
  `dragonbane_initiative_result`, plus `_dragonbane_footer`. Sidfoten krediterar Jonas.
- `src/main.py` : registreringsblock i `on_ready` (direkt efter Delta Green-blocket,
  före sync), gated av `FEATURE_FLAGS.get("slash_dragonbane_enabled", False)`.
- `config/feature_flags.py` : ny flagga `"slash_dragonbane_enabled": True`.
- `README.md` : Dragonbane-sektion i funktionslistan plus rad i Erkännanden.

### Kommandon
- `/dod_slag expression:2T6+1T8+3` : fritt tärningsuttryck (T och d funkar)
- `/dod_fv skill:13 modifier:2 mode:fördel` : färdighetsslag, slag <= FV lyckas,
  1 = drakslag (krit), 20 = demonslag (fummel). Misslyckat (ej demon) visar en
  "Pressa slag"-knapp.
- `/dod_skada dice:1T10 bonus:2` : skadeslag
- `/dod_pressa skill:13 modifier:0 mode:normal grundegenskap:STY` : pressar och drar
  ett tillstånd. `grundegenskap` är valfri; anges den blir tillståndet deterministiskt
  och regelrätt, annars slumpas det med en SL-not.
- `/dod_init characters:Björn,Saga,Ragna` : initiativ

### Regelrättningar jämfört med originalet
1. Initiativ dras nu som en kortlek (unika kort 1-10, lägst agerar först) i stället
   för T10 med återläggning sorterat högst först. Vid fler än 10 stridande används
   flera lekar.
2. Tupel-buggen i `/dod_pressa` (tillståndet skrevs ut som `('Utmattad', 'STY')`) är
   borta; all utskrift går via embed-metoder.
3. Tillstånd vid pressning kan bindas till grundegenskap (deterministiskt) i stället
   för att alltid slumpas.

### Kredit till Jonas finns på tre ställen
- Sidfot på varje Dragonbane-embed: "Dragonbane-modul av Jonas".
- Docstrings i `src/dragonbane/`.
- README: egen sektion och rad under Erkännanden.

## Verifiering som redan gjorts i Cowork
- `src/dragonbane/dice.py`, `src/dragonbane/commands.py` och
  `src/core/embed_factory.py` kompilerar (py_compile).
- Tärninglogiken enhetstestad: drake på 1 (lyckas), demon på 20 (missar), fördel tar
  lägst av två, initiativ ger unika stigande kort (lägst först), tillstånd-mappning
  korrekt, ogiltiga uttryck avvisas.
- `src/main.py`, `config/feature_flags.py` och `README.md` kunde INTE py_compile:as i
  sandboxen pga en mount-lag (de såg avhuggna ut där). På den riktiga filsidan är de
  hela. Det är därför du ska köra verifieringen nedan lokalt.

## Vad du ska göra

### 1. Verifiera integritet och syntax
```bash
python -m py_compile src/main.py config/feature_flags.py src/core/embed_factory.py \
  src/dragonbane/__init__.py src/dragonbane/dice.py src/dragonbane/commands.py
```
Bekräfta att inga `SyntaxError` dyker upp (särskilt att `src/main.py` och
`config/feature_flags.py` är hela, inte trunkerade).

### 2. Snabbtest av tärninglogiken (utan Discord)
```bash
python - <<'PY'
import sys; sys.path.insert(0, "src")
from random import Random
from dragonbane import dice
print(dice.roll_expression("2T6+1T8+3", rng=Random(7)).total)
print([ (e.name, e.card) for e in dice.roll_initiative(["A","B","C"], rng=Random(3)) ])
class Stub:
    def __init__(s,v): s.v=v
    def randint(s,a,b): return s.v
print("drake", dice.dragonbane_skill_check(5, rng=Stub(1)).critical)
print("demon", dice.dragonbane_skill_check(5, rng=Stub(20)).critical)
PY
```

### 3. Smoke-test i Discord (rekommenderas före kvällens spel)
Starta boten och kör `/dod_fv skill:13`, `/dod_init characters:A,B,C` och
`/dod_slag expression:2T6+3`. Kontrollera att embeds renderar och att sidfoten visar
krediten. Om slash-kommandon inte syns direkt: kommandona synkas i `on_ready`; en
guild-sync (GUILD_ID i .env) ger dem direkt, global sync kan ta upp till en timme.

### 4. Committa och pusha (KÖR LOKALT, inte i Cowork-sandboxen)
VIKTIGT: I Cowork-mounten visade `git status` HELA repot som ändrat. Det är en
CRLF-flip (Windows-radslut blir LF genom mounten), inte riktiga ändringar:
`git diff --ignore-all-space` på orörda filer är tom. Lokalt på din dator ser
git bara filerna nedan som ändrade. Därför ska commit och push göras lokalt.

Använd INTE `git add -A` (då drar du med en radslut-churn över hela repot). Stage
bara de avsedda filerna:
```bash
git add src/dragonbane/ src/core/embed_factory.py src/main.py config/feature_flags.py \
  README.md DRAGONBANE_HANDOFF.md
git commit -m "Lägg till Dragonbane-modul (av Jonas)

- Nytt paket src/dragonbane (dice.py, commands.py)
- Dragonbane-embeds i embed_factory med kredit till Jonas i sidfoten
- Registrering i main.py bakom flaggan slash_dragonbane_enabled
- README: Dragonbane-sektion och rad under Erkännanden
- Regelrättat: initiativ som kortlek (lägst först), deterministiska tillstånd, tupel-bugg fixad"
git push
```

Om du hellre vill hålla handoff-filen utanför repot: ta bort
`DRAGONBANE_HANDOFF.md` från `git add`-raden och radera den efter pushen.
