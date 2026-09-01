# Run Bot Skill

Startar Diceroller/EON-discordboten lokalt så den kan testas i Discord.

## Trigger

`/run-bot` eller när Johan ber om att "starta boten", "sparka igång boten", "kör boten".

## Förutsättningar

- `.env` måste finnas i repo-roten med minst `DISCORD_TOKEN`, `PINECONE_API_KEY`,
  `ANTHROPIC_API_KEY`. Utan `GUILD_ID` i `.env` tar slash-kommando-sync upp till en
  timme (global sync) istället för att synas direkt (guild-sync).

## Workflow

### 1. Kolla om boten redan kör

Ett gammalt `.run_bot.pid` kan ligga kvar från en tidigare session utan att processen
faktiskt lever — verifiera mot verklig processlista, lita inte på pid-filen ensam.

```bash
tasklist //FI "IMAGENAME eq python.exe"
```

Om ett python.exe redan kör och du är osäker på om det är boten: fråga Johan innan du
dödar det (kan vara annat lokalt arbete). Om han bekräftar att det är en gammal
bot-instans:

```bash
taskkill //PID <pid> //F
```

### 2. Starta boten i bakgrunden

Kör alltid som bakgrundsprocess (`run_in_background: true` i Bash-tool) — boten är
long-running och blockerar annars sessionen.

```bash
python src/main.py > bot_output.log 2>&1 &
echo $! > .run_bot.pid
```

`.run_bot.pid` och `bot_output.log` är gitignorade runtime-artefakter, inte
projektfiler — commita aldrig dessa.

**Obs (Windows/Git Bash-kvirk):** `$!` fångar ibland fel PID för den faktiska
`python.exe`-processen pga hur bakgrundsjobb hanteras i Git Bash på Windows. Verifiera
alltid den riktiga PID:en efteråt med `tasklist //FI "IMAGENAME eq python.exe"` istället
för att bara lita på filen — den kan behövas för att döda rätt process senare.

### 3. Verifiera att den faktiskt startade

`bot_output.log` kan vara tomt en liten stund efter start pga stdout-buffring när
output går till fil istället för terminal. Den auktoritativa källan är
`logs/eon_bot.log` (loggning_config.py), som flushar direkt. Vänta ~10-15 sekunder
och kolla:

```bash
tail -n 20 logs/eon_bot.log
```

Leta efter:
- `Alla kommandon har registrerats och boten är redo!` — boten är uppe och kommandona
  synkade
- `Kunskapsbasen initierad och redo att användas.` — Pinecone + Codex API-koppling OK
  (kommer strax efter, laddas async via `ensure_ready()` och blockerar inte "redo"-
  meddelandet ovan)

Om ingen ny rad dyker upp alls efter 15-20 sekunder: något kraschade tyst, kolla
`bot_output.log` för traceback (encoding kan strula på Windows — icke-ASCII-tecken i
konsolen kan se ut som `�` istället för åäö, det är bara terminal-encoding, inget
verkligt fel).

### 4. Meddela Johan

Boten är redo att testas i Discord. Om `GUILD_ID` inte är satt, påminn om att
kommandona kan dröja upp till en timme innan de syns.

### Stoppa boten

```bash
tasklist //FI "IMAGENAME eq python.exe"
taskkill //PID <verklig-pid> //F
```
