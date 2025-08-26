# EON Discord Bot - Slash Command Konvertering
## Del 3: Admin Commands, Stats & Finalisering

---

## 📋 Förutsättningar

**Innan du börjar Del 3:**
- ✅ Del 1 & 2 är kompletta och stabila
- ✅ Minst 48 timmars test i staging
- ✅ Användare har testat och gett feedback
- ✅ Performance metrics visar acceptabla värden
- ✅ **Embed factory används konsekvent överallt**
- ✅ Inga kritiska buggar kvarstår

---

## 🔐 Admin Commands

### Kritisk Säkerhetsförståelse

**DUBBEL SÄKERHET krävs för admin commands:**

1. **Discord Permission Check:** `@app_commands.default_permissions(manage_guild=True)`
2. **Role Validation i kod:** Kontrollera "Game Master" roll explicit

**VARNING:** Enbart Discord permissions räcker INTE - användare kan override i server settings!

### Implementation Instructions

#### 6.1 Session Management Commands

**För `/startsession` kommandot:**

Säkerhetskrav:
1. Kontrollera Game Master roll FÖRST i funktionen
2. Om ej GM → ephemeral error message via `embed_factory.error_message()`
3. Logga ALLA session starts med user ID och timestamp

Parameters:
- `description: Optional[str]` - Sessionsbeskrivning
- `players: Optional[str]` - Kommaseparerad lista av spelare

Embed feedback:
- Använd `embed_factory.success_message()` för bekräftelse
- Visa session ID och starttid tydligt

Förbättringar att lägga till:
- Auto-notify alla spelare när session startar
- Skapa thread för session-diskussion
- Sätt bot status till "I spelsession"

**För `/endsession` kommandot:**

KRITISKT: Detta kan trigga AI-sammanfattning!
- **MÅSTE använda defer()** omedelbart
- Generera session summary med Claude
- Spara statistik permanent
- Skicka rapport till GM via DM

Implementation:
1. Defer direkt (AI summary tar tid)
2. Samla all session data
3. Generera AI summary om >10 händelser
4. Arkivera session med timestamp
5. Rensa temporär data

**För `/showsession` kommandot:**

Visa:
- Session ID och startid
- Aktiva spelare
- Antal händelser/slag
- Session längd
- Högsta/lägsta slag

#### 6.2 Secret Commands

**KRITISK SKILLNAD:** Prefix hade `!secret roll/ex/count` som ett kommando
**Slash behöver:** Separata `/secret_roll`, `/secret_ex`, `/secret_count`

**För ALLA secret commands:**

Absoluta krav:
1. **ephemeral=True** på ALLA responses
2. GM roll check först
3. Logga användning (för audit)
4. ALDRIG visa i publik kanal
5. **Använd speciella factory methods** för secret embeds (om de finns)

**För `/secret_roll`:**
- Identisk logik som `/roll` MEN ephemeral
- Använd `embed_factory.dice_result()` med ephemeral=True
- Skicka DM till GM med resultat
- Logg i GM-only channel om konfigurerat

**För `/secret_ex`:**
- Som `/ex` men hemlig
- Extra försiktighet med explosion results

**För `/secret_count`:**
- Som `/count` men dold
- Använd för hidden skill checks

#### 6.3 GM Control Commands

**Nya admin commands att lägga till:**

`/gm_override`:
- Ändra valfritt spelarresultat retroaktivt
- Kräver confirmation dialog
- Loggas extensivt

`/session_rollback`:
- Ångra X antal händelser
- Visa preview innan confirm
- Notifiera påverkade spelare

`/player_stats [player]`:
- Visa detaljerad statistik för spelare
- Jämför med genomsnitt
- Identifiera ovanliga mönster

---

## 📊 Stats Commands (Avancerade)

### Implementation Instructions

#### 7.1 Enhanced Stats System

**För `/allstats` (GM only):**

Måste inkludera:
- Per-spelare breakdown
- Session jämförelser
- Trend analysis
- Anomaly detection
- Export möjlighet

Embed creation:
- **ANVÄND:** `embed_factory.stats_overview()` som bas
- För komplexa stats, överväg flera embeds eller pagination
- Använd konsekvent formatering för alla statistik-visningar

Implementation approach:
1. Använd defer() - detta blir data-intensivt
2. Generera multi-page embed med navigation
3. Erbjud olika visualiseringar
4. Cache resultat i 5 minuter

**För `/mystatsall`:**

Personlig statistik med:
- Progression över tid (graf?)
- Personliga rekord
- Jämförelse med egen historik
- Achievement tracking
- Predictive analytics ("Du borde nå nivå X om Y sessioner")

#### 7.2 Statistik Visualisering

**Implementera grafgenerering:**

1. Använd matplotlib/pillow för bilder
2. Generera graphs on-demand
3. Cache genererade bilder
4. Visa som Discord attachments

Grafer att inkludera:
- Tärningsfördelning histogram
- Success rate över tid
- Session aktivitet heatmap
- Skill progression curves

---

## 🏁 Finalisering

### 8.1 Ta Bort Prefix System

**VARNING:** Gör detta SIST efter full verifiering!

#### Steg 1: Soft Deprecation (Vecka 1-2)

1. Lägg till deprecation varning i alla prefix commands:
   ```python
   "⚠️ Detta kommando är föråldrat! Använd /kommando istället"
   ```

2. Logga prefix användning för analys

3. Skicka DM till användare som använder prefix:
   ```
   "Hej! Vi har bytt till slash commands. Prova /help för mer info!"
   ```

#### Steg 2: Gradvis Nedstängning (Vecka 3-4)

1. Inaktivera mindre använda prefix commands
2. Behåll endast kritiska som backup
3. Öka varningsfrekvens

#### Steg 3: Full Migration (Vecka 5+)

1. **Backup en sista gång**
2. Kommentera ut ALL prefix registrering
3. Ta bort prefix command imports
4. Rensa unused dependencies
5. Uppdatera documentation

### 8.2 Cleanup Tasks

**Kod-rensning:**

1. Ta bort:
   - Alla `@bot.command` decorators
   - Command parsing logic för `*args`
   - Flag parsing (`--de`, `--ryttare`)
   - Prefix-specific error handlers

2. Uppdatera:
   - README med nya commands
   - Help documentation
   - User guides
   - API documentation

3. Optimera:
   - Kombinera duplicerad kod
   - Förenkla command struktur
   - Ta bort legacy workarounds

### 8.3 Performance Optimization

**Efter full migration:**

1. **Profile hela systemet:**
   - Identifiera bottlenecks
   - Mät memory usage
   - Analysera API call patterns

2. **Optimera databas:**
   - Index på ofta sökta fält
   - Arkivera gammal data
   - Optimera queries

3. **Cache aggressivt:**
   - Command descriptions
   - User preferences
   - Vanliga queries
   - Regel-innehåll

---

## 🧪 Final Testing Protocol

### Regression Testing:
- [ ] ALLA commands från Del 1-3 fungerar
- [ ] Permissions enforcement verified
- [ ] Ephemeral messages där appropriate
- [ ] Defer() används korrekt överallt
- [ ] **Alla embeds kommer från embed_factory**
- [ ] **Visuell konsistens mellan alla command-typer**

### Load Testing:
- [ ] 50 simultana commands
- [ ] 10 concurrent AI queries
- [ ] 1000 rolls på 1 minut
- [ ] Memory usage stabil

### Security Testing:
- [ ] Non-GM kan inte köra admin commands
- [ ] Secret commands är verkligen hemliga
- [ ] Injection attacks blockerade
- [ ] Rate limiting fungerar

### User Acceptance:
- [ ] 10+ användare testat i 48h
- [ ] Feedback insamlad och addresserad
- [ ] Documentation uppdaterad
- [ ] Training genomförd

---

## 📝 Go-Live Checklist

### Pre-Launch (T-24h):
- [ ] Full backup av production
- [ ] Announcement i Discord
- [ ] Maintenance window schemalagd
- [ ] Rollback plan dokumenterad
- [ ] Support team briefad

### Launch (T-0):
- [ ] Stop production bot
- [ ] Deploy nya versionen
- [ ] Kör smoke tests
- [ ] Verifiera slash commands syncar
- [ ] Start monitoring

### Post-Launch (T+1h):
- [ ] Kontrollera error logs
- [ ] Verifiera performance metrics
- [ ] Första användare testar
- [ ] Inga kritiska issues
- [ ] Announce success

### Stabilization (T+24h):
- [ ] Analysera usage patterns
- [ ] Adressera minor issues
- [ ] Samla user feedback
- [ ] Plan improvements
- [ ] Arkivera gamla prefix kod

---

## 🎯 Success Metrics

**Efter 1 vecka bör du se:**
- 95%+ commands använder slash
- <1% error rate
- 50% snabbare average response time
- 90%+ user satisfaction
- 0 säkerhetsincidenter

**Efter 1 månad:**
- 100% slash adoption
- Prefix system helt borttaget
- Förbättrad user engagement
- Färre support requests
- Nya features baserat på slash capabilities

---

## 🚀 Framtida Förbättringar

**När migrationen är klar, överväg:**

1. **Context Menu Commands:**
   - Högerklick på meddelande → "Roll for initiative"
   - Högerklick på användare → "Visa stats"

2. **Modal Forms:**
   - Character creation wizard
   - Complex dice expressions builder
   - Session feedback forms

3. **Button/Select Interactions:**
   - Interactive combat tracker
   - Skill trees med buttons
   - Equipment management

4. **Advanced Features:**
   - Scheduled commands
   - Recurring sessions
   - Tournament modes
   - Achievement system

---

## 🏆 Slutsats

**Grattis!** När du följt alla tre delar har du:

✅ Moderniserat hela bot-infrastrukturen  
✅ Förbättrat user experience dramatiskt  
✅ Implementerat proper säkerhet  
✅ Optimerat performance  
✅ Framtidssäkrat för kommande Discord-features  

---

## 🆘 Troubleshooting Guide

### Vanligaste Problemen och Lösningar

#### Problem: "Application did not respond"
**Orsaker och lösningar:**
1. Glömt defer() → Lägg till direkt efter interaction parameter
2. Använder response.send efter defer() → Byt till followup.send
3. Försöker svara två gånger → Kontrollera response.is_done()

#### Problem: Commands syns inte efter sync
**Orsaker och lösningar:**
1. Discord cache → Vänta upp till 1 timme
2. Guild-specific sync → Använd global sync istället
3. Permission konflikt → Kontrollera bot och command permissions

#### Problem: "Unknown interaction"
**Orsaker och lösningar:**
1. Interaction expired (>15 min) → Implementera refresh mechanism
2. Bot restarted mid-interaction → Spara state persistent
3. Network timeout → Implementera retry logic

#### Problem: Ephemeral messages syns för alla
**Orsaker och lösningar:**
1. ephemeral=True på fel ställe → Måste vara i första response
2. Followup inte ephemeral → Alla followups måste också vara ephemeral
3. Embed limits → Ephemeral har samma limits som vanliga

#### Problem: Rate limiting issues
**Orsaker och lösningar:**
1. För många syncs → Cacha sync, kör max 1/timme
2. Spam protection → Implementera cooldowns
3. API throttling → Använd exponential backoff

---

## 📚 Referensdokumentation

### Discord.py Slash Command Essentials

**Response timing:**
- Initial response: 3 sekunder max
- Efter defer(): 15 minuter för första followup
- Followups: Obegränsat (inom rimliga gränser)

**Parameter limits:**
- Max 25 choices per parameter
- Max 25 autocomplete suggestions
- Command description: Max 100 tecken
- Parameter description: Max 100 tecken

**Embed limits (viktigt med embed_factory):**
- Title: 256 tecken
- Description: 4096 tecken
- Fields: 25 st max
- Field name: 256 tecken
- Field value: 1024 tecken
- Footer: 2048 tecken
- Total: 6000 tecken

**Best Practices:**
1. Alltid validera permissions i kod (inte bara Discord)
2. Använd typing hints för alla parameters
3. **Använd alltid embed_factory för konsekvent utseende**
4. Implementera graceful degradation
5. Logga alla admin actions
6. Cache där möjligt

---

## 🔄 Migration Rollback Plan

### Om något går katastrofalt fel:

#### Immediate Rollback (< 5 min):
1. Stoppa boten omedelbart
2. Återställ från senaste backup
3. Starta med gamla koden
4. Meddela användare om tillfälligt avbrott

#### Gradual Rollback (< 1 timme):
1. Re-aktivera prefix commands
2. Kör dual mode temporärt
3. Fix kritiska issues
4. Planera ny migration

#### Full Rollback (< 24 timmar):
1. Git revert till pre-migration tag
2. Restore databas backup
3. Clear alla slash commands
4. Kommunicera tydligt med community
5. Post-mortem analys

### Rollback Script:
```bash
#!/bin/bash
# emergency_rollback.sh

echo "🚨 INITIATING EMERGENCY ROLLBACK"

# Stop bot
systemctl stop eon-bot

# Backup current (broken) state
cp -r /bot /bot_broken_$(date +%s)

# Restore from backup
cp -r /backups/latest/* /bot/

# Restore git state
cd /bot
git checkout backup-pre-slash-$(date +%Y%m%d)

# Clear slash commands via special script
python clear_slash_commands.py

# Restart with old version
systemctl start eon-bot

echo "✅ Rollback complete - verify functionality"
```

---

## 📊 Metrics Tracking

### Implementera följande mätpunkter:

**Performance Metrics:**
- Command response time (p50, p95, p99)
- Defer usage rate
- Timeout frequency
- Cache hit rate
- Error rate per command

**Usage Metrics:**
- Commands per hour/day
- Unique users per day
- Most/least used commands
- Peak usage times
- Feature adoption rate

**Quality Metrics:**
- User satisfaction (feedback)
- Support tickets
- Bug reports
- Feature requests
- Retention rate

### Dashboard Förslag:
Skapa enkelt dashboard som visar:
1. Real-time command usage
2. Error rate trend
3. Response time graph
4. Active sessions
5. System health

---

## 💡 Lessons Learned

### Vad som brukar gå fel:

1. **Underskatta tidsåtgång** - Lägg till 50% buffer
2. **Glömma edge cases** - Testa med extremvärden
3. **Ignorera user feedback** - Lyssna tidigt och ofta
4. **Skippa documentation** - Dokumentera medan du bygger
5. **Rush deployment** - Ta det lugnt, gör rätt

### Tips för framgång:

1. **Involvera community** tidigt
2. **Testa omfattande** innan launch
3. **Ha tydlig rollback** plan
4. **Kommunicera transparent** om ändringar
5. **Fira milestones** med teamet

---

## 🎓 Utbildningsmaterial

### För Användare:

Skapa följande guides:
1. "Från ! till / - Snabbguide"
2. "Nya Features i Slash Commands"
3. "Vanliga Frågor och Svar"
4. Video tutorial (5-10 min)
5. Cheat sheet (1 sida PDF)

### För Game Masters:

Specialguide som täcker:
1. Alla admin commands
2. Secret commands usage
3. Session management
4. Stats och analytics
5. Troubleshooting

### För Utvecklare:

Teknisk dokumentation:
1. Architecture overview
2. API documentation
3. Extension guide
4. Contributing guidelines
5. Testing procedures

---

## 🏗️ Arkitektur Efter Migration

### Förbättrad Struktur:
```
src/
├── commands/
│   ├── slash/
│   │   ├── dice.py
│   │   ├── combat.py
│   │   ├── knowledge.py
│   │   ├── admin.py
│   │   └── utility.py
│   └── groups/
│       ├── player_commands.py
│       └── gm_commands.py
├── core/
│   ├── bot.py
│   ├── database.py
│   └── cache.py
├── utils/
│   ├── timeout_handler.py
│   ├── permission_checker.py
│   └── response_formatter.py
├── migrations/
│   ├── helpers.py
│   └── rollback.py
└── tests/
    ├── unit/
    ├── integration/
    └── e2e/
```

---

## ✨ Slutord

**Du har nu genomfört en av de största moderniseringarna av EON Discord Bot!**

Denna migration ger:
- **Bättre användarupplevelse** med autocomplete och validering
- **Högre säkerhet** med proper permission handling
- **Snabbare utveckling** av nya features
- **Enklare underhåll** med modern arkitektur
- **Framtidssäkring** för kommande Discord-features

**Kom ihåg:**
- Varje förbättring tar tid
- Perfekt är fienden till bra
- User feedback är guld värt
- Dokumentation sparar framtida huvudvärk
- Ha kul med projektet!

---

## 📞 Support och Hjälp

Om du fastnar:
1. Kolla Discord.py dokumentation
2. Sök i Discord Developers server
3. Testa i isolation först
4. Logga extensively
5. Be om code review

**Lycka till med migrationen! 🚀**