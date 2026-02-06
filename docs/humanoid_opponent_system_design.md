# Humanoid Opponent System - Designdokument

**Status:** Planering/Design-fas ✅ KOMPLETT
**Estimerad implementation:** 28-38 timmar (fasad över 3-4 veckor)
**Dokumentdatum:** 2025-10-13 (v3 - med kompletta tabeller)

---

## Snabb sammanfattning (för diskussion)

Detta system utökar den befintliga Discord-boten för EON RPG med ett komplett combat management-system för humanoid motståndare (NPC:er). Systemet hanterar:

- **Spawning:** GM skapar fiender från templates eller custom (med 26 olika rustningszoner)
- **Strid:** Återanvänder befintliga `/hugg`, `/stick`, `/kross` med ny `fiende:` parameter
- **Stats:** Samlas **dynamiskt** via Discord Modal pop-ups när effekter triggas (STY, Tur, etc.)
- **Specialeffekter:** Automatisk hantering av 15+ EON-specialregler:
  - **Amp** (amputering), **Fast** (vapen fastnat), **Men** (permanenta skador)
  - **Ongoing effects** som vapen fastnat i kropp (+1T/+1S per handling)
  - Automatiska motståndsslag för alla effekter
- **GM Tools:** Ephemeral status-kommandon, AI-genererade beskrivningar, detaljerade rapporter

**Nyckelfunktion:** GM behöver INTE ange alla stats i förväg - boten frågar dynamiskt när behov uppstår och sparar för framtida användning.

---

## Diskussionspunkter

Följande är viktiga tekniska/design-frågor att diskutera:

1. **Discord Modal vs Ephemeral Commands**
   - Modal (pop-up) ger bäst UX men är tekniskt komplexare
   - Fallback om Modal inte funkar?

2. **Ongoing Effects - Automatik vs Manuell**
   - Ska boten automatiskt lägga till +1T/+1S varje runda vid "Fast"?
   - Eller måste GM köra `/runda_tick` manuellt?
   - Ska `/timme_tick` applicera Inre skada automatiskt eller bara visa påminnelse?

3. **Spelare med specialeffekter**
   - Samma Modal-system för spelare?
   - Eller `/registrera_karaktär` för att lagra stats i förväg?

4. **Tabeller som saknas/oklara** ✅ UPPDATERAT
   - ✅ R2-54 (Amputering) - ANALYSERAD
   - ✅ R2-55 (Bryt) - ANALYSERAD
   - ✅ R2-56 (Inre skador) - ANALYSERAD
   - ⚠️ Syrebrist-tabell (sida 68) - behövs fortfarande
   - ❓ **KRITISK FRÅGA:** Vad slår man Bryt mot? Tabellen säger inte! (antar STY)
   - ❓ **KRITISK FRÅGA:** Bruten Nackkotot/Ryggkotot - Förlamning? Död? Behöver kolla regelboken

5. **Fasad implementation**
   - OK att börja med grundsystem (Fas 1-5) och lägga till specialeffekter senare?
   - Eller behövs allt från start?
   - **Rekommendation:** Fasad approach - grundsystem först (vecka 1), tabeller vecka 2

6. **Hand/Fot amputering - Komplex regel** ✅ ANALYSERAD
   - Tre olika outcomes: Klarar STY, Misslyckas STY men klarar Tur (fingrar/tår), Misslyckas båda (full amp)
   - Halverad effekt vid fingrar/tår - OK?

7. **"Avlider omedelbart**" regel**
   - Fotnoten säger "gäller KUN om skadan kommer från övriga skadan från skadetabellen"
   - Hur tolkar vi detta tekniskt?
   - Förslag: Skadan från själva träffen måste också vara dödande (inte bara amputationen)

---

## Innehållsförteckning

1. [Snabb sammanfattning](#snabb-sammanfattning-för-diskussion)
2. [Diskussionspunkter](#diskussionspunkter)
3. [Översikt](#översikt)
4. [EON:s 26 träffområden](#eons-26-träffområden)
5. [EON Specialeffekter och Regelmotor](#eon-specialeffekter-och-regelmotor)
   - Motståndsslag-baserade effekter
   - Direkta effekter
   - Ongoing Effects
   - Tabeller som behövs
6. [Dynamiskt Stats-system](#dynamiskt-stats-system)
   - Hur det fungerar
   - Discord Modal Implementation
   - Stats som kan behövas
7. [Datastruktur](#datastruktur)
   - HumanoidOpponent
   - OngoingEffect
   - OpponentTemplate
8. [Användarflöden](#användarflöden)
9. [Kommandon](#kommandon-fullständig-lista)
10. [Teknisk implementation](#teknisk-implementation)
11. [Fördefinierade templates](#fördefinierade-templates)
12. [Implementation-plan](#implementation-plan-steg-för-steg)
13. [Framtida utökningar](#framtida-utökningar-ej-i-v10)
14. [Anteckningar](#anteckningar)

---

## Översikt

Ett modulärt system för att hantera humanoid motståndare i strid, som återanvänder befintliga EON träfftabeller och skadesystem men lägger till:
- Individuell state tracking per motståndare
- Flexibel rustningskonfiguration per kroppsdel
- Template-system för återanvändning
- Multi-opponent stöd (flera motståndare samtidigt)
- **NYTT:** Omfattande specialeffekt-system (Amp, Fast, Men, Inre skada, etc.)
- **NYTT:** Dynamiskt stats-system med Discord Modals (stats samlas vid behov)
- **NYTT:** Automatiska motståndsslag för alla effekter
- **NYTT:** Ongoing effects tracking (vapen fastnat, kvävning, etc.)

## Befintligt system som återanvänds

✅ **hit_tables.py** - 26 träffområden för humanoider
✅ **damage_tables.py** - Skadetabeller för hugg/stick/kross
✅ **combat_manager.py** - Skadeberäkning och effekter
✅ **/hugg, /stick, /kross** - Träffkommandon

## EON:s 26 träffområden

```
Kod  Delområde
━━━━━━━━━━━━━━━━━━━━━━━━
 1   Ansikte
 2   Skalle
 3   Hals/Nacke
 4   Vänster skuldra
 5   Höger skuldra
 6   Vänster överarm
 7   Höger överarm
 8   Vänster armbåge
 9   Höger armbåge
10   Vänster underarm
11   Höger underarm
12   Vänster hand
13   Höger hand
14   Bröstkorg
15   Mage
16   Underliv
17   Vänster höft
18   Höger höft
19   Vänster lår
20   Höger lår
21   Vänster knä
22   Höger knä
23   Vänster vad
24   Höger vad
25   Vänster fot
26   Höger fot
```

### Logiska grupperingar

- **Huvud**: 1-3 (Ansikte, Skalle, Hals)
- **Vänster arm**: 4, 6, 8, 10, 12 (Skuldra, Överarm, Armbåge, Underarm, Hand)
- **Höger arm**: 5, 7, 9, 11, 13
- **Torso**: 14-16 (Bröstkorg, Mage, Underliv)
- **Vänster ben**: 17, 19, 21, 23, 25 (Höft, Lår, Knä, Vad, Fot)
- **Höger ben**: 18, 20, 22, 24, 26

## EON Specialeffekter och Regelmotor

Ett av systemets kärnfunktioner är att automatiskt hantera EON:s omfattande specialregler för allvarliga skador. Dessa effekter triggas av skadetabellerna och kräver motståndsslag, ongoing tracking och permanenta konsekvenser.

### 1️⃣ Motståndsslag-baserade effekter

Dessa effekter triggas omedelbart vid skada och kräver ett motståndsslag för att avgöra konsekvens.

| Effekt | Trigger | Slag | Vid misslyckande | Permanent? |
|--------|---------|------|------------------|------------|
| **Amp** (Amputering) | Allvarlig huggskada | Ob?T6 vs STY (svårighet från tabell R2-54) | Kroppsdel amputerad | ✅ JA |
| **Fast** (Fastnat vapen) | Allvarlig skada | Ob3T6 vs Tur | Vapen fastnat i kroppen | ❌ (tills lossat) |
| **Faller** (Faller omkull) | Benskada | Ob3T6 vs Chockvärde | Faller till marken (liggande) | ❌ |
| **Tappar** (Tappar föremål) | Armskada | Ob3T6 vs Chockvärde | Tappar vapen/föremål | ❌ |
| **Men - Hjärna** | Huvudskada | Ob3T6 vs Tur | PSY/RÖR/VIL sänks permanent | ✅ JA |
| **Men - Könsorgan** | Underlivsskada | Ob3T6 vs Tur | Permanent könsskada | ✅ JA |
| **Men - Mun/Käke** | Huvudskada | Ob3T6 vs Tur | 1T6-1 tänder, ev. PER-1 | ✅ JA |
| **Men - Muskler/Senor** | Arm/benskada | Ob3T6 vs Tur | STY/RÖR/Förflyttning sänks | ✅ JA |
| **Men - Öga** | Huvudskada | Ob3T6 vs Tur | SYN-4, PER-1, +Ob1T6 precision | ✅ JA |
| **Men - Öra** | Huvudskada | Ob3T6 vs Tur | HÖR-2, ev. PER-1 | ✅ JA |

### 2️⃣ Direkta effekter (inget motståndsslag)

| Effekt | Beskrivning | Konsekvens |
|--------|-------------|------------|
| **Bryt** | Benbrott/ligamentskada | Kroppsdel oanvändbar |
| **Kväv** | Luftstrupe skadad | Syrebrist varje runda (se tabell) |
| **Inre skada** | Vitalt organ skadat | Slå på tabell R2-56 för specifikt organ |
| **Dör** | Dödande skada | Omedelbar död |
| **Förblöder** | Massiv blödning | Dör inom X rundor utan hjälp |

### 3️⃣ Ongoing Effects (kräver kontinuerlig tracking)

**Fast (Vapen fastnat i kropp):**
- **Under effekt:**
  - +1 Trauma per handling med kroppsdelen
  - +1 Smärta per handling med kroppsdelen
  - Dubbla värden vid snabb förflyttning (>2m per fas)
  - Blockerar ALL läkning
  - Omöjligt att lägga förband
  - Vapnet går ej att använda

- **Att lossa:**
  - Normal: Ob3T6 vs STY → Ob1T6 extra T/S/B vid försök
  - Försiktig: +Ob1T6 svårare, vs RÖR istället → Ingen extra skada vid lyckat
  - Hullingar: +Ob1T6 extra svårighet
  - Utomstående hjälper: -Ob1T6 lättare

**Kväv (Kvävning):**
- Varje runda: Syrebrist (se EON sida 68)
- Kräver kirurgi eller magi för att åtgärda

**Inre skada:**
- Punkterad lunga: +2T, +6S permanent
- Olika effekter beroende på organ (tabell R2-56)
- Kräver kirurgi eller magi
- Trauma/Smärta läker normalt, men organskada kvarstår

**Permanenta Men:**
- Statistiksänkningar registreras permanent
- Påverkar alla framtida slag
- Kan INTE läkas (utom med magi)

### 4️⃣ Tabeller som behövs

Följande EON-tabeller måste implementeras eller laddas in:

| Tabell | Beskrivning | Användning | Status |
|--------|-------------|------------|--------|
| **R2-54** | Amputationstabell | Svårighetsgrader för Amp per kroppsdel | ✅ **ANALYSERAD** |
| **R2-55** | Brytartabell | Benbrott/kotor vid "Bryt" | ✅ **ANALYSERAD** |
| **R2-56** | Inre skador | Specifika organskador vid "Inre skada" | ✅ **ANALYSERAD** |
| **Syrebrist** (sida 68) | Kvävningseffekter | Skada per runda vid "Kväv" | ⏳ Behövs |
| Skadetabeller | Alla 26 områden × 3 vapentyper | Redan implementerat! | ✅ Klar |

---

## Detaljerad Tabellanalys

### R2-56: Inre skador (1T10)

**Trigger:** När skadetabell visar "Inre skada" → Slå 1T10

**Tabellstruktur:**

```json
{
  "1-2": {
    "organ": "Magsäcken punkterad",
    "damage_per_hour": {"trauma": 1, "pain": 8},
    "effects": ["Urinering fördubblade", "Extra infektion"],
    "note": "Leder till kraftiga buksmärtor"
  },
  "3-4": {
    "organ": "Tuntarmarna skadade",
    "damage_per_hour": {"trauma": 1, "pain": 8},
    "effects": ["Urinering fördubblade", "Extra infektion"],
    "note": "Leder till en allvarlig buksmärta"
  },
  "5-6": {
    "organ": "Tjocktarmen punkterad",
    "damage_per_hour": {"trauma": 1, "pain": 8},
    "effects": ["Urinering fördubblade", "Två extra infektioner"],
    "note": "Leder till en allvarlig buksmärta"
  },
  "7": {
    "organ": "En njure förstörd",
    "damage_per_hour": {"trauma": 1, "pain": 6},
    "effects": ["Urinering fördubblade"],
    "note": ""
  },
  "8": {
    "organ": "Gallblåsa spräckt",
    "damage_per_hour": {"trauma": 1, "pain": 6},
    "effects": ["Urinering fördubblade"],
    "note": ""
  },
  "9": {
    "organ": "Mjälten spräckt",
    "damage_per_hour": {"trauma": 1, "pain": 6},
    "effects": ["Urinering fördubblade"],
    "note": ""
  },
  "10": {
    "organ": "Levern förstörd",
    "damage_per_hour": {"trauma": 4, "pain": 6},
    "effects": ["Urinering fördubblade", "Två extra infektioner"],
    "note": ""
  }
}
```

**Implementeringskrav:**
- **Ongoing Effect:** Skada appliceras automatiskt varje timme
- **Stopp:** Kräver kirurgi eller magi
- **Kommando:** `/timme_tick` eller `/nästa_timme` för GM
- **Tracking:** Lägg i `ongoing_effects` med `effect_type: "Inre skada"` och metadata om vilket organ

---

### R2-54: Amputationstabell

**Trigger:** När skadetabell visar "Amp" → Lookup svårighetsgrad → Slå mot STY

**Tabellstruktur:**

Svårighetsgrad baseras på:
1. **Kroppsdel** (rad)
2. **Effective Damage** (kolumn): 10-19, 20-29, 30-39, 40-49, 50-59, Varje +10

**Mappning: EON 26 områden → Tabellrader**

| EON Kod | Delområde | Tabellrad | Specialregel |
|---------|-----------|-----------|--------------|
| 1 | Ansikte | "Ansikte" | Avlider omedelbart** |
| 2 | Skalle | "Skalle" | Avlider omedelbart** |
| 3 | Hals/Nacke | "Nacke/hals" | Avlider omedelbart** |
| 4, 5 | Vänster/Höger skuldra | "Skuldra" | T+25, S+25, B+25 |
| 6, 7 | Vänster/Höger överarm | "Överarm" | T+20, S+20, B+20 |
| 8, 9 | Vänster/Höger armbåge | "Armbåge" | T+20, S+20, B+20 |
| 10, 11 | Vänster/Höger underarm | "Underarm" | T+20, S+20, B+20 |
| 12, 13 | Vänster/Höger hand | "Hand" | T+10, S+10, B+10*** |
| 14 | Bröstkorg | "Bröstkorg" | Avlider omedelbart |
| 15 | Mage | "Mage" | Avlider omedelbart |
| 16 | Underliv | "Underliv" | T+25, S+25, B+25 |
| 17, 18 | Vänster/Höger höft | "Höft" | T+25, S+25, B+25 |
| 19, 20 | Vänster/Höger lår | "Lår" | T+25, S+25, B+25 |
| 21, 22 | Vänster/Höger knä | "Knä" | T+20, S+20, B+20 |
| 23, 24 | Vänster/Höger vad | "Vad" | T+20, S+20, B+20 |
| 25, 26 | Vänster/Höger fot | "Fot" | T+10, S+10, B+10*** |

**Specialregler:**

- **\*\*:** "Avlider omedelbart" gäller KUN om skadan kommer från övriga skadan från skadetabellen (inte enbart amputationen)
- **\*\*\*:** Hand/Fot → Slå Ob3T6 mot Tur FÖRST:
  - **Lyckas Tur:** Flera fingrar/tår av, amputationseffekten **halveras** (T+5, S+5, B+5)
  - **Misslyckas Tur:** Full amputering med normal effekt

**JSON-struktur för svårighetsgrader:**

```json
{
  "Ansikte": {
    "10-19": null,
    "20-29": null,
    "30-39": "Ob1T6",
    "40-49": "Ob2T6",
    "50-59": "Ob3T6",
    "per_10": "Ob1T6",
    "amp_effect": "Avlider omedelbart**"
  },
  "Hand": {
    "10-19": "Ob1T6",
    "20-29": "Ob2T6",
    "30-39": "Ob3T6",
    "40-49": "Ob4T6",
    "50-59": "Ob5T6",
    "per_10": "Ob1T6",
    "amp_effect": "T+10, S+10, B+10***"
  }
  // ... fortsättning för alla kroppsdelar
}
```

**Implementeringsflöde:**

```
1. Skada visar "Amp"
2. Lookup: location_code → tabellrad (mappning ovan)
3. Lookup: effective_damage → kolumn → svårighetsgrad (ObXT6)
4. IF svårighetsgrad == null: Ingen amputationsrisk, returnera
5. IF location in ["Hand", "Fot"]:
   a. Discord Modal: Hämta Tur
   b. Slå Ob3T6 mot Tur
   c. IF lyckas: Fingrar/tår av, halvera amp_effect
   d. IF misslyckas: Fortsätt till steg 6
6. Discord Modal: Hämta STY
7. Slå ObXT6 mot STY
8. IF lyckas: Ingen amputering
9. IF misslyckas:
   a. Applicera amp_effect (T/S/B)
   b. Markera kroppsdel som amputerad i permanent_disabilities
   c. IF "Avlider omedelbart": opponent.alive = False
```

---

### R2-55: Brytartabell (Benbrott/Kotor)

**Trigger:** När skadetabell visar "Bryt" → Lookup svårighetsgrad → Slå mot STY (troligen)

**Tabellstruktur:**

Svårighetsgrad baseras på:
1. **Allvarlig skada typ** (rad)
2. **Effective Damage** (kolumn): 10-19, 20-29, 30-39, 40-49, 50-59, Varje +10
3. **+Ob1T6 extra om vapnet är KROSS**

**Mappning: EON 26 områden → Tabellrader**

| EON Kod | Delområde | Tabellrad | Konsekvens |
|---------|-----------|-----------|------------|
| 6-13 | Armar (alla delar) | "Benpipa - Arm" | Arm oanvändbar |
| 19-26 | Ben (alla delar) | "Benpipa - Ben" | Ben oanvändbart, förflyttning påverkas |
| 3 | Hals/Nacke | "Nackkotot" | Förlamning? (behöver kolla) |
| 1 | Ansikte | "Näsa" | Näsan bruten |
| 14 | Bröstkorg | "Revben" | Revben brutet |
| 15, 16 | Mage/Underliv | "Ryggkotot" | Förlamning? (behöver kolla) |
| 2 | Skalle | "Skallben" | Skallben spräckt |

**JSON-struktur:**

```json
{
  "Benpipa - Arm": {
    "10-19": "Ob2T6*",
    "20-29": "Ob3T6*",
    "30-39": "Ob4T6*",
    "40-49": "Ob5T6*",
    "50-59": "Ob6T6*",
    "per_10": "Ob1T6*"
  },
  "Benpipa - Ben": {
    "10-19": "Ob1T6*",
    "20-29": "Ob2T6*",
    "30-39": "Ob3T6*",
    "40-49": "Ob4T6*",
    "50-59": "Ob5T6*",
    "per_10": "Ob1T6*"
  }
  // ... fortsättning
}
```

**Implementeringsflöde:**

```
1. Skada visar "Bryt"
2. Lookup: location_code → tabellrad (mappning ovan)
3. IF tabellrad == null: Ingen brytningsrisk, returnera
4. Lookup: effective_damage → kolumn → svårighetsgrad (ObXT6*)
5. IF weapon_type == "kross": svårighetsgrad += Ob1T6
6. Discord Modal: Hämta STY
7. Slå ObXT6 mot STY
8. IF lyckas: Ingen brytning
9. IF misslyckas:
   a. Markera kroppsdel som bruten i permanent_disabilities
   b. Kroppsdel oanvändbar
   c. IF ben: Förflyttning påverkas (behöver regler)
```

**VIKTIGT - Öppna frågor:**
- Vad slår man Bryt mot? Tabellen säger inte! Antar STY.
- Vad händer vid bruten nackkotot/ryggkotot? Förlamning? Död? Behöver kolla regelboken.
- Hur påverkar bruten benpipa combat mechanics?

## Dynamiskt Stats-system

Ett av systemets smarta funktioner är att **stats samlas dynamiskt** när de behövs, istället för att kräva fullständiga karaktärsblad i förväg.

### Hur det fungerar

```
1. OPPONENT SPAWNAS
   → Endast combat-essentials: namn, CV, tålighet, rustning
   → Inga andra stats ännu

2. FÖRSTA "AMP"-EFFEKTEN TRIGGAS
   → Bot: *visar Discord Modal* "⚠️ AMPUTATIONSRISK! Ange Grimfangs STY:"
   → GM fyller i: "13"
   → Bot slår Ob?T6 mot 13 automatiskt
   → Bot SPARAR STY i opponent.stats.STY = 13

3. SENARE "AMP"-EFFEKT
   → Bot hittar sparad STY = 13
   → Slår automatiskt utan att fråga igen

4. FÖRSTA "FAST"-EFFEKTEN
   → Bot: *visar Discord Modal* "⚠️ VAPEN KAN FASTNA! Ange Grimfangs Tur:"
   → GM fyller i: "11"
   → Bot slår och sparar Tur = 11

5. STATS PERSISTERAS
   → Sparas i opponent JSON-fil
   → Överlever bot-restart
   → Ackumuleras under hela kampanjen
```

### Discord Modal Implementation (Alternativ A)

**Teknisk lösning:** Discord Modal (pop-up formulär)

**Fördelar:**
- ✅ Smidig UX - inget extra kommando
- ✅ Avbryter inte stridsflödet
- ✅ Tydlig visuell prompt
- ✅ GM ser exakt vad som behövs och varför

**Exempel på användarupplevelse:**

```
[Spelare attackerar Grimfang med hugg, får "Amp"-effekt]

Bot (publikt):
🎯 Thorgrim träffar Grimfang i HÖGER ARM!
   Skada: 25 - 2 rustning = 23 effektiv
   Djup huggskada genom muskulatur
   ⚠️ AMPUTATIONSRISK!

Bot → GM (Discord Modal popup):
┌─────────────────────────────────────┐
│  ⚠️ AMPUTATIONSRISK - GRIMFANG     │
│                                     │
│  Höger arm riskerar amputering!     │
│  Slår Ob3T6 mot STY.                │
│                                     │
│  Ange Grimfangs STY:                │
│  ┌─────────────┐                    │
│  │    [  13  ] │                    │
│  └─────────────┘                    │
│                                     │
│     [Avbryt]  [Bekräfta]            │
└─────────────────────────────────────┘

[GM klickar Bekräfta]

Bot (följ-upp, ephemeral till GM):
═══════════════════════════════════════
🎲 AMPUTATIONSSLAG - GRIMFANG
═══════════════════════════════════════
Kroppsdel: Höger arm
STY: 13
Svårighet: Ob3T6 (Normal amputering)

Tärningar: [2, 5, 3] = 10
Resultat: ✅ KLARAR (10 ≤ 13)

→ Höger arm BEHÅLLEN (men allvarligt skadad)

💾 STY sparad för framtida slag
═══════════════════════════════════════
```

### Stats som kan behövas

Följande stats kan efterfrågas dynamiskt under strid:

| Stat | När? | Varför? |
|------|------|---------|
| **STY** | Amp, Lossa fastnat vapen | Motståndsslag för amputering och styrka |
| **Tur** | Fast, Men-effekter | Motståndsslag för lycka/otur |
| **Chockvärde** | Faller, Tappar | Motståndsslag för medvetande |
| **RÖR** | Men-effekter, Försiktig lossning | Påverkas av permanenta men |
| **PSY** | Men - Hjärna | Sänks permanent vid hjärnskada |
| **VIL** | Men - Hjärna | Sänks permanent vid hjärnskada |
| **SYN** | Men - Öga | Sänks permanent vid ögonförlust |
| **HÖR** | Men - Öra | Sänks permanent vid öronförlust |
| **PER** | Men (flera) | Kan sänkas av olika skador |
| **Förflyttning** | Men - Muskler/Senor | Sänks permanent vid benskada |
| **FYS** | Förblöder (eventuellt) | Används för överlevnad |

## Datastruktur

### HumanoidOpponent (runtime-instans)

```python
@dataclass
class HumanoidOpponent:
    """En individuell humanoid motståndare med state tracking"""

    # Identifikation
    instance_id: str          # Unikt ID (t.ex. "grimfang", "grunt_1")
    display_name: str         # Visningsnamn
    template_id: Optional[str] # Vilken mall (om någon)

    # Combat Stats (alltid satta)
    chock_value: int          # CV, vanligen 12-16
    damage_tolerance: int     # Poäng per skadekolumn, vanligen 10

    # Dynamiska Stats (samlas vid behov via Discord Modal)
    stats: Dict[str, int] = {}  # {"STY": 13, "Tur": 11, "RÖR": 10, ...}

    # Rustning per område (1-26)
    armor_by_location: Dict[int, ArmorValues]
    # ArmorValues = {"hugg": int, "kross": int, "stick": int}

    # Current state
    total_trauma: int         # Total T-skada
    total_pain: int           # Total S-skada
    damage_by_location: Dict[int, int]  # Trauma per delområde

    # Status
    conscious: bool = True
    alive: bool = True

    # Ongoing Effects (vapen fastnat, kvävning, etc.)
    ongoing_effects: List[OngoingEffect] = []

    # Permanenta Men
    permanent_disabilities: List[str] = []  # ["Höger arm amputerad", "Vänster öga förstört"]
    stat_modifiers: Dict[str, int] = {}     # {"SYN": -4, "PER": -1}

    # Historik
    active_effects: List[str] = []
    hit_count: int = 0

@dataclass
class OngoingEffect:
    """Pågående effekt som kräver tracking"""
    effect_type: str          # "Fast", "Kväv", "Inre skada"
    location: Optional[int]   # Kroppsdel (1-26) om relevant
    weapon_name: Optional[str] # För "Fast"
    rounds_active: int = 0    # Hur länge effekten pågått
    metadata: Dict = {}       # Extra data per effekt-typ
```

### OpponentTemplate (lagrad i JSON)

Templates innehåller endast **combat-essentials**. Andra stats (STY, Tur, etc.) samlas dynamiskt vid behov.

```json
{
  "id": "ork_krigare",
  "display_name": "Ork Krigare",
  "description": "Typisk ork med ringbrynja och läderhjälm",

  "combat_stats": {
    "chock_value": 14,
    "damage_tolerance": 10
  },

  "armor": {
    "1-3": {"hugg": 2, "kross": 3, "stick": 1},
    "14-16": {"hugg": 4, "kross": 2, "stick": 3},
    "4-13,17-26": {"hugg": 1, "kross": 0, "stick": 1}
  },

  "notes": "Ringbrynja på torso, läderhjälm, läder på armar/ben"
}
```

**OBS:** Ingen `"stats"` sektion! STY, Tur, RÖR etc. läggs till dynamiskt när effekter triggas.

## Användarflöden

### Flöde A: Snabb spawning från mall

```
GM: /spawn_fiende mall:"ork_krigare" namn:"Grimfang"

Bot (ephemeral - bara GM ser):
✅ Grimfang (Ork Krigare) spawnad!
   • CV: 14, Tålighet: 10
   • Rustning: Ringbrynja + läder
```

### Flöde B: Spawna flera från samma mall

```
GM: /spawn_fiende mall:"ork_krigare" antal:3

Bot (ephemeral):
✅ 3 Ork Krigare spawnade:
   • Grunt #1
   • Grunt #2
   • Grunt #3
```

### Flöde C: Interaktiv custom-skapelse

```
GM: /skapa_fiende

Bot (ephemeral):
📝 Skapar ny fiende - Steg 1/4
Namn:

GM: Grimfang

Bot:
📝 Steg 2/4
Chockvärde: (standard: 12)

GM: 14

Bot:
📝 Steg 3/4
Tålighet per skadekolumn: (standard: 10)

GM: 10

Bot:
📝 Steg 4/4 - Rustning
Välj metod:
[📋 Använd mall] [✏️ Ange manuellt] [🚫 Ingen rustning]

GM: [klickar "Ange manuellt"]

Bot:
Ange rustning per område (1-26)
Format: "områden H:X K:Y S:Z"
Exempel: "1-3 H:2 K:3 S:1"

Skriv "hjälp" för områdeslista
Skriv "klar" när färdig

GM: hjälp

Bot:
TRÄFFOMRÅDEN (1-26):
────────────────────────────────
 1. Ansikte        14. Bröstkorg
 2. Skalle         15. Mage
 3. Hals/Nacke     16. Underliv
 4. V.skuldra      17. V.höft
 5. H.skuldra      18. H.höft
 6. V.överarm      19. V.lår
 7. H.överarm      20. H.lår
 8. V.armbåge      21. V.knä
 9. H.armbåge      22. H.knä
10. V.underarm     23. V.vad
11. H.underarm     24. H.vad
12. V.hand         25. V.fot
13. H.hand         26. H.fot

GM: 1-3 H:2 K:3 S:1

Bot:
✓ Rustning satt för område 1-3
  (Ansikte, Skalle, Hals/Nacke)
  Hugg:2, Kross:3, Stick:1

GM: 14-16 H:4 K:2 S:3

Bot:
✓ Rustning satt för område 14-16
  (Bröstkorg, Mage, Underliv)
  Hugg:4, Kross:2, Stick:3

GM: 4-13,17-26 H:1 K:0 S:1

Bot:
✓ Rustning satt för område 4-13,17-26
  (Armar och ben - 20 områden)
  Hugg:1, Kross:0, Stick:1

GM: klar

Bot:
✅ Grimfang skapad!
   • CV: 14, Tålighet: 10
   • Rustning: 26/26 områden konfigurerade

Spara som återanvändbar mall?
[💾 Ja] [❌ Nej]

GM: [klickar "Ja"]

Bot:
Mallnamn:

GM: min_ork

Bot:
✅ Mall "min_ork" sparad!
   Använd med: /spawn_fiende mall:min_ork
```

### Flöde D: Attack mot fiende

```
Spelare: /hugg fiende:"Grimfang" område:"torso" skada:18

Bot (publikt):
🎯 [Spelarnamn] träffar Grimfang i BRÖSTKORG!
   Slår träffområde: 14 (Bröstkorg)

   Skada: 18 - 4 rustning = 14 effektiv
   Djupt sår genom ringbrynja
   T+7, S+14

   Grimfang: T:7/100, S:14/100

Bot → GM (DM):
══════════════════════════════════════════════
🗡️ GRIMFANG - SKADERAPPORT
══════════════════════════════════════════════

【 SENASTE TRÄFF 】
Attackerare: [Spelarnamn]
Område: Bröstkorg (14)
Vapentyp: HUGG
Rå skada: 18
Rustning: 4 (ringbrynja)
Effektiv skada: 14

Skadetyp: Djupt sår genom ringbrynja
TS: T+7, S+14

【 AI-BESKRIVNING 】
"Vapnet biter sig genom ringbrynjans ringar med
ett metalliskt skrapande. Grimfang flämtar till
när bladet går djupt in i bröstet."

【 TOTAL SKADA 】
Trauma (T): 7/100 [0 fyllda rader]
Smärta (S): 14/100 [1 fylld rad]

【 KRITISKA SLAG 】
Chockslag: Ob1T6 mot CV 14
⚠️ CHOCKSLAG KRÄVS! (S-rad fylld)

【 AKTIVA EFFEKTER 】
• Blöder

══════════════════════════════════════════════
```

### Flöde E: Status-check

```
GM: /fiendestatus Grimfang

Bot (ephemeral):
══════════════════════════════════════════════
🗡️ GRIMFANG - STATUS
══════════════════════════════════════════════

【 GRUNDINFO 】
Typ: Ork Krigare
CV: 14, Tålighet: 10
Status: ✅ VID MEDVETANDE, LEVANDE

【 TOTAL SKADA 】
Trauma (T): 15/100 [1 fylld rad]
Smärta (S): 28/100 [2 fyllda rader]

Träffar: 3

【 KRITISKA SLAG 】
Chockslag: Ob3T6 mot CV 14
Dödsslag: Ob1T6 mot CV 14

【 SKADA PER OMRÅDE 】
Bröstkorg (14): 7 trauma
Mage (15): 5 trauma
Vänster arm (10): 3 trauma

【 AKTIVA EFFEKTER 】
• Blöder
• Försvagad

【 RUSTNING 】
Huvud (1-3): H:2 K:3 S:1
Torso (14-16): H:4 K:2 S:3
Armar/Ben: H:1 K:0 S:1

══════════════════════════════════════════════
```

### Flöde F: Lista alla aktiva fiender

```
GM: /fiendestatus_alla

Bot (ephemeral):
══════════════════════════════════════════════
🗡️ AKTIVA FIENDER
══════════════════════════════════════════════

1. Grimfang (Ork Krigare)
   Status: ⚠️ SKADAD
   T:15/100 [1r], S:28/100 [2r]
   Träffar: 3

2. Grunt #1 (Ork Krigare)
   Status: ☠️ DÖD

3. Grunt #2 (Ork Krigare)
   Status: ✅ FRISK
   T:0/100, S:0/100

────────────────────────────────────────────
Totalt: 3 fiender (1 levande, 1 död, 1 frisk)
══════════════════════════════════════════════
```

## Kommandon (fullständig lista)

### Skapelse & Hantering

| Kommando | Beskrivning | Synlighet |
|----------|-------------|-----------|
| `/spawn_fiende` | Spawna fiende från mall | Ephemeral (GM) |
| `/skapa_fiende` | Interaktiv custom-skapelse | Ephemeral (GM) |
| `/ta_bort_fiende [namn]` | Ta bort en fiende | Ephemeral (GM) |
| `/reset_fiender` | Rensa alla fiender | Ephemeral (GM) |

### Status

| Kommando | Beskrivning | Synlighet |
|----------|-------------|-----------|
| `/fiendestatus [namn]` | Visa en fiendes status | Ephemeral (GM) |
| `/fiendestatus_alla` | Lista alla aktiva fiender | Ephemeral (GM) |

### Strid (integration med befintliga)

| Kommando | Ny parameter | Beskrivning |
|----------|--------------|-------------|
| `/hugg` | `fiende:"namn"` | Huggattack mot fiende |
| `/stick` | `fiende:"namn"` | Stickattack mot fiende |
| `/kross` | `fiende:"namn"` | Krossattack mot fiende |

### Ongoing Effects Management

| Kommando | Beskrivning | Synlighet |
|----------|-------------|-----------|
| `/lossa_vapen [fiende] [metod]` | Lossa fastnat vapen (normal/försiktig) | Ephemeral (GM) |
| `/runda_tick [fiende]` | Avancera en stridsrunda (Kväv-effekter) | Ephemeral (GM) |
| `/timme_tick [fiende]` | Avancera en timme (Inre skada-effekter) | Ephemeral (GM) |
| `/ta_bort_effekt [fiende] [effekt]` | Ta bort ongoing effect (kirurgi/magi) | Ephemeral (GM) |

### Templates

| Kommando | Beskrivning | Synlighet |
|----------|-------------|-----------|
| `/spara_mall` | Spara befintlig fiende som mall | Ephemeral (GM) |
| `/lista_mallar` | Lista alla tillgängliga mallar | Ephemeral (GM) |
| `/visa_mall [mall_id]` | Visa detaljer för en mall | Ephemeral (GM) |

## Teknisk implementation

### Filstruktur

```
src/
  humanoid_opponent_manager.py    # Ny: Manager-klass
  humanoid_effect_processor.py    # Ny: Specialeffekt-processor

  # Återanvändning av befintligt:
  hit_tables.py                    # ✓ Används som den är
  damage_tables.py                 # ✓ Används som den är
  combat_manager.py                # ✓ Återanvänd logik

data/
  opponent_templates/              # Ny mapp: Fiende-mallar
    ork_krigare.json
    manniska_soldat.json
    alv_skogvaktare.json
    dvarg_hirdman.json

  opponent_instances/              # Ny mapp: Runtime state
    guild_<id>/
      grimfang.json
      grunt_1.json
      ...

  effect_tables/                   # Ny mapp: EON specialeffekt-tabeller
    amputation_table.json          # R2-54: Amputationstabell
    break_table.json               # R2-55: Brytartabell
    internal_damage_table.json     # R2-56: Inre skador
    suffocation_table.json         # Syrebrist (sida 68)
    location_mapping.json          # Mappning: EON 26 → Tabellrader

commands/
  slash_opponent_commands.py       # Ny: Alla opponent-kommandon
```

### JSON-filernas struktur

**data/effect_tables/location_mapping.json:**

```json
{
  "amputation": {
    "1": "Ansikte",
    "2": "Skalle",
    "3": "Nacke/hals",
    "4": "Skuldra",
    "5": "Skuldra",
    "6": "Överarm",
    "7": "Överarm",
    "8": "Armbåge",
    "9": "Armbåge",
    "10": "Underarm",
    "11": "Underarm",
    "12": "Hand",
    "13": "Hand",
    "14": "Bröstkorg",
    "15": "Mage",
    "16": "Underliv",
    "17": "Höft",
    "18": "Höft",
    "19": "Lår",
    "20": "Lår",
    "21": "Knä",
    "22": "Knä",
    "23": "Vad",
    "24": "Vad",
    "25": "Fot",
    "26": "Fot"
  },
  "break": {
    "6-13": "Benpipa - Arm",
    "19-26": "Benpipa - Ben",
    "3": "Nackkotot",
    "1": "Näsa",
    "14": "Revben",
    "15-16": "Ryggkotot",
    "2": "Skallben"
  }
}
```

**data/effect_tables/amputation_table.json:**

```json
{
  "Ansikte": {
    "ranges": {
      "10-19": null,
      "20-29": null,
      "30-39": 1,
      "40-49": 2,
      "50-59": 3
    },
    "per_10": 1,
    "amp_effect": {
      "type": "death",
      "note": "Avlider omedelbart**"
    }
  },
  "Hand": {
    "ranges": {
      "10-19": 1,
      "20-29": 2,
      "30-39": 3,
      "40-49": 4,
      "50-59": 5
    },
    "per_10": 1,
    "amp_effect": {
      "type": "damage",
      "trauma": 10,
      "pain": 10,
      "bleeding": 10,
      "special": "fingers_toes"
    }
  }
  // ... fortsättning för alla kroppsdelar
}
```

**data/effect_tables/internal_damage_table.json:**

```json
{
  "rolls": {
    "1-2": {
      "organ": "Magsäcken punkterad",
      "trauma_per_hour": 1,
      "pain_per_hour": 8,
      "effects": ["Urinering fördubblade", "Extra infektion"]
    },
    "10": {
      "organ": "Levern förstörd",
      "trauma_per_hour": 4,
      "pain_per_hour": 6,
      "effects": ["Urinering fördubblade", "Två extra infektioner"]
    }
  }
}
```

### Kärnklasser

```python
# humanoid_opponent_manager.py

@dataclass
class ArmorValues:
    """Rustningsvärden för ett område"""
    hugg: int = 0
    kross: int = 0
    stick: int = 0

@dataclass
class HumanoidOpponent:
    """En individuell motståndare"""
    # ... (se ovan)

class OpponentTemplate:
    """Template laddat från JSON"""
    def __init__(self, json_data):
        # Parse JSON
        pass

    def create_instance(self, name: str) -> HumanoidOpponent:
        """Skapa en instans från denna template"""
        pass

class HumanoidOpponentManager:
    """Hanterar alla fiender för en guild"""

    def __init__(self, guild_id: int):
        self.guild_id = guild_id
        self.opponents: Dict[str, HumanoidOpponent] = {}
        self.templates: Dict[str, OpponentTemplate] = {}
        self._load_templates()
        self._load_instances()

    def spawn_from_template(
        self,
        template_id: str,
        name: Optional[str] = None,
        count: int = 1
    ) -> List[HumanoidOpponent]:
        """Spawna fiende(r) från mall"""
        pass

    def create_custom(
        self,
        name: str,
        cv: int,
        tolerance: int,
        armor: Dict[int, ArmorValues]
    ) -> HumanoidOpponent:
        """Skapa custom fiende"""
        pass

    def process_attack(
        self,
        opponent_name: str,
        weapon_type: str,
        location_code: int,  # 1-26
        raw_damage: int
    ) -> DamageResult:
        """
        Processar attack - återanvänder befintligt system!

        1. Hämta motståndare
        2. Hämta rustning för området
        3. Beräkna effektiv skada
        4. Anropa damage_tables.calculate_damage()
        5. Uppdatera state
        6. Kontrollera chock/död
        """
        opponent = self.opponents[opponent_name]
        armor_values = opponent.armor_by_location[location_code]
        armor = getattr(armor_values, weapon_type)

        effective_damage = max(0, raw_damage - armor)

        # Återanvänd befintlig logik!
        from damage_tables import calculate_damage
        damage_result = calculate_damage(
            weapon_type=weapon_type,
            location=location_code,
            effective_damage=effective_damage
        )

        # Uppdatera state
        opponent.total_trauma += damage_result.trauma
        opponent.total_pain += damage_result.pain
        opponent.damage_by_location[location_code] += damage_result.trauma

        # Spara state
        self._save_instance(opponent)

        return damage_result

    def get_opponent(self, name: str) -> Optional[HumanoidOpponent]:
        """Hämta fiende via namn"""
        pass

    def list_opponents(self) -> List[HumanoidOpponent]:
        """Lista alla aktiva fiender"""
        pass

    def remove_opponent(self, name: str):
        """Ta bort en fiende"""
        pass

    def reset(self):
        """Rensa alla fiender"""
        pass
```

### Integration med befintliga kommandon

```python
# I slash_combat_commands.py (befintlig fil)

# Uppdatera /hugg kommandot:
@bot.tree.command(name="hugg")
@app_commands.describe(
    fiende="Fiende att attackera (lämna tom för vanlig attack)",
    område="Träffområde",
    skada="Skadavärde"
)
async def hugg_command(
    interaction: discord.Interaction,
    område: str,
    skada: int,
    fiende: Optional[str] = None  # NY PARAMETER
):
    if fiende:
        # Ny logik: Attack mot fiende
        manager = get_opponent_manager(interaction.guild_id)
        opponent = manager.get_opponent(fiende)

        if not opponent:
            await interaction.response.send_message(
                f"❌ Fiende '{fiende}' finns inte!",
                ephemeral=True
            )
            return

        # Processar attack
        result = manager.process_attack(
            opponent_name=fiende,
            weapon_type="hugg",
            location_code=parse_location(område),
            raw_damage=skada
        )

        # Visa resultat (publikt + GM-DM)
        # ...
    else:
        # Gammal logik: Vanlig träff (som det fungerar nu)
        # ...
```

## Fördefinierade templates

### 1. ork_krigare.json

```json
{
  "id": "ork_krigare",
  "display_name": "Ork Krigare",
  "description": "Typisk ork med ringbrynja och läderhjälm",
  "combat_stats": {
    "chock_value": 14,
    "damage_tolerance": 10
  },
  "armor": {
    "1-3": {"hugg": 2, "kross": 3, "stick": 1},
    "14-16": {"hugg": 4, "kross": 2, "stick": 3},
    "4-13,17-26": {"hugg": 1, "kross": 0, "stick": 1}
  }
}
```

### 2. manniska_soldat.json

```json
{
  "id": "manniska_soldat",
  "display_name": "Människa Soldat",
  "description": "Standard-soldat med ringbrynja på torso",
  "combat_stats": {
    "chock_value": 12,
    "damage_tolerance": 10
  },
  "armor": {
    "14-16": {"hugg": 4, "kross": 2, "stick": 3},
    "1-13,17-26": {"hugg": 0, "kross": 0, "stick": 0}
  }
}
```

### 3. dvarg_hirdman.json

```json
{
  "id": "dvarg_hirdman",
  "display_name": "Dvärg Hirdman",
  "description": "Tungt bepansrad dvärg med plåtrustning",
  "combat_stats": {
    "chock_value": 15,
    "damage_tolerance": 12
  },
  "armor": {
    "1-3": {"hugg": 5, "kross": 6, "stick": 4},
    "4-26": {"hugg": 6, "kross": 4, "stick": 5}
  }
}
```

### 4. alv_skogvaktare.json

```json
{
  "id": "alv_skogvaktare",
  "display_name": "Alv Skogvaktare",
  "description": "Lättrustning i läder",
  "combat_stats": {
    "chock_value": 13,
    "damage_tolerance": 8
  },
  "armor": {
    "1-26": {"hugg": 1, "kross": 0, "stick": 1}
  }
}
```

## Implementation-plan (steg-för-steg)

**VIKTIGT:** Implementeringen är uppdelad i faser där grundsystemet byggs först, sedan läggs specialeffekter till stegvis.

### Fas 1: Grundsystem (2-3 timmar)
**Mål:** Få basfunktionalitet att fungera utan specialeffekter

- [ ] Skapa `HumanoidOpponent` dataclass med alla fält
- [ ] Skapa `OngoingEffect` dataclass
- [ ] Skapa `HumanoidOpponentManager` grundstruktur
- [ ] Implementera template-loading från JSON
- [ ] Implementera `spawn_from_template()`
- [ ] Implementera `process_attack()` (återanvänd damage_tables.py)
- [ ] Grundläggande T/S/B tracking (UTAN specialeffekter ännu)
- [ ] Enkel testning via Python-script

### Fas 2: Spawn-kommandon (1-2 timmar)
- [ ] `/spawn_fiende` - Enkel spawning från mall
- [ ] Autocomplete för template-val
- [ ] Support för auto-namngivning (Grunt #1, #2, etc)
- [ ] Support för `antal` parameter
- [ ] Skapa 4 grundläggande templates (ork, människa, alv, dvärg)

### Fas 3: Interaktiv skapelse (3-4 timmar)
- [ ] `/skapa_fiende` - Multi-step wizard
- [ ] Steg 1: Namn
- [ ] Steg 2: CV
- [ ] Steg 3: Tålighet
- [ ] Steg 4: Rustning (parsing av format "1-3 H:2 K:3 S:1")
- [ ] Hjälpkommando för områdeslista
- [ ] Spara-som-mall funktionalitet

### Fas 4: Attack-integration (2-3 timmar)
- [ ] Uppdatera `/hugg` med `fiende` parameter
- [ ] Uppdatera `/stick` med `fiende` parameter
- [ ] Uppdatera `/kross` med `fiende` parameter
- [ ] Autocomplete för fiende-namn
- [ ] Publikt resultat-meddelande
- [ ] GM-DM rapport med detaljer

### Fas 5: Status-kommandon (1-2 timmar)
- [ ] `/fiendestatus [namn]` - En fiende
- [ ] `/fiendestatus_alla` - Alla fiender
- [ ] Formatera output snyggt
- [ ] Visa ongoing effects
- [ ] Visa permanenta men

### Fas 6: Dynamiska Stats + Discord Modals (3-4 timmar)
**Mål:** Implementera systemet för att samla stats vid behov

- [ ] Skapa Discord Modal-wrapper för stat-förfrågningar
- [ ] Implementera `request_stat()` metod i Manager
- [ ] Stats persistence i opponent JSON
- [ ] Testa med enkel mock-effekt (t.ex. "Tappar")

### Fas 7: Enkla specialeffekter (2-3 timmar)
**Mål:** Implementera effekter UTAN ongoing tracking först

- [ ] **Bryt** - Markera kroppsdel oanvändbar
- [ ] **Tappar** - Ob3T6 vs CV, tappar vapen
- [ ] **Faller** - Ob3T6 vs CV, faller omkull
- [ ] Visa effekter i status-kommandon

### Fas 8: Motståndsslag-baserade effekter (5-6 timmar)
**Mål:** Implementera alla slag-baserade effekter med kompletta tabeller

**Tabell-implementation:**
- [ ] Skapa JSON-fil för R2-54 (Amputationstabell) med alla kroppsdelar och svårighetsgrader
- [ ] Skapa JSON-fil för R2-55 (Brytartabell) med alla skadetyper
- [ ] Skapa JSON-fil för R2-56 (Inre skador) med alla organ
- [ ] Skapa mappning: EON 26 kroppsdelar → Tabellrader (helper-funktion)

**Amp (Amputering) - Komplett implementation:**
- [ ] Lookup svårighetsgrad från R2-54 baserat på kroppsdel + effective_damage
- [ ] Special case: Hand/Fot → Discord Modal för Tur först
- [ ] Slå Ob3T6 mot Tur → Fingrar/tår (halverad effekt) eller full amputering
- [ ] Discord Modal för STY
- [ ] Slå ObXT6 mot STY
- [ ] Vid misslyckande:
  - [ ] Applicera amputationseffekt (T/S/B från tabell)
  - [ ] Markera i permanent_disabilities
  - [ ] Check "Avlider omedelbart" regel (** fotnot)
- [ ] Spara båda stats (Tur + STY) för framtida bruk

**Bryt (Benbrott/Kotor) - Komplett implementation:**
- [ ] Lookup svårighetsgrad från R2-55 baserat på kroppsdel + effective_damage
- [ ] Check: Om weapon_type == "kross" → +Ob1T6
- [ ] Discord Modal för STY
- [ ] Slå ObXT6 mot STY
- [ ] Vid misslyckande:
  - [ ] Markera kroppsdel som bruten i permanent_disabilities
  - [ ] Lägg till "oanvändbar" status
  - [ ] Special: Ben → Förflyttning påverkas

**Fast (Vapen fastnat):**
- [ ] Discord Modal → Tur → Slag → Lägg till OngoingEffect
- [ ] Spara vapnets namn i OngoingEffect metadata

**Men-effekter:**
  - [ ] Hjärna (PSY/RÖR/VIL sänks)
  - [ ] Könsorgan (markera i permanent_disabilities)
  - [ ] Mun/Käke (1T6-1 tänder, PER-1)
  - [ ] Muskler/Senor (STY/RÖR/Förflyttning)
  - [ ] Öga (SYN-4, PER-1)
  - [ ] Öra (HÖR-2, PER-1)

**Infrastructure:**
- [ ] Permanent stat modifiers tracking
- [ ] Helper-funktion för att beräkna "Varje +10" kolumner dynamiskt

### Fas 9: Ongoing Effects Tracking (4-5 timmar)
**Mål:** Hantera effekter som varar över flera rundor/timmar

- [ ] **Inre skada (R2-56) - Timme-baserad:**
  - [ ] När "Inre skada" triggas → Slå 1T10 på R2-56
  - [ ] Identifiera vilket organ (Magsäck, Tuntarmar, Tjocktarm, Njure, Gallblåsa, Mjälte, Lever)
  - [ ] Lägg till OngoingEffect med:
    - `effect_type: "Inre skada"`
    - `metadata: {"organ": "Magsäcken punkterad", "trauma_per_hour": 1, "pain_per_hour": 8, ...}`
  - [ ] Visa organ och effekt i GM-rapport
  - [ ] Kommando `/timme_tick` eller `/nästa_timme` för att applicera skada
  - [ ] Applicera X trauma + Y smärta per timme automatiskt
  - [ ] Special effekter (extra infektioner, urinering)
  - [ ] Kräver kirurgi/magi för att stoppa

- [ ] **Fast (vapen fastnat) - Handling-baserad:**
  - [ ] Lägg till +1T/+1S per handling automatiskt (eller visa varning till GM)
  - [ ] Dubblera vid snabb förflyttning (>2m)
  - [ ] Blockera läkning medan effekt aktiv
  - [ ] Blockera förband på området
  - [ ] Visa i status med vapnets namn

- [ ] **Kväv (kvävning) - Runda-baserad:**
  - [ ] Ladda in syrebrist-tabell (EON sida 68) om tillgänglig
  - [ ] Applicera skada automatiskt per runda
  - [ ] Kommando `/runda_tick` för GM att avancera rundan
  - [ ] Kräver kirurgi/magi för att stoppa

### Fas 10: Lossa vapen-system (2 timmar)
- [ ] `/lossa_vapen [fiende] [metod]` kommando
- [ ] Support för "normal" (STY) och "försiktig" (RÖR)
- [ ] Support för "hjälp" (utomstående, -Ob1T6)
- [ ] Hullingar detection (+Ob1T6)
- [ ] Applicera Ob1T6 extra T/S/B vid försök

### Fas 11: Hantering & Utils (1-2 timmar)
- [ ] `/ta_bort_fiende` - Ta bort en specifik fiende
- [ ] `/reset_fiender` - Rensa alla fiender
- [ ] `/lista_mallar` - Visa alla tillgängliga templates
- [ ] `/visa_mall` - Visa detaljer för en specifik mall
- [ ] `/runda_tick [fiende]` - Avancera en stridsrunda (för Kväv-effekter)
- [ ] `/timme_tick [fiende]` - Avancera en timme (för Inre skada-effekter)
- [ ] `/ta_bort_effekt [fiende] [effekt]` - Ta bort en ongoing effect (kirurgi/magi)

### Fas 12: AI-beskrivningar (1-2 timmar)
- [ ] Integrera Claude för dramatiska beskrivningar
- [ ] Inkludera specialeffekter i beskrivningen
- [ ] Lägg till i GM-rapport
- [ ] Samma stil som spindelsystemet

### Fas 13: Polish & Testing (3-4 timmar)
- [ ] Persistent state (JSON-filer per guild)
- [ ] Error handling för alla Discord Modals
- [ ] Edge cases (t.ex. båda ögon förstörda)
- [ ] Testa alla specialeffekter individuellt
- [ ] Testa kombinerade effekter (Amp + Fast samtidigt)
- [ ] User testing med riktig strid
- [ ] Dokumentation och exempel

**Total estimerad tid: 28-38 timmar**

### Tidsfördelning per fas:

- **Fas 1-5** (Grundsystem): 9-14 timmar
- **Fas 6-7** (Stats + Enkla effekter): 5-7 timmar
- **Fas 8** (Tabeller + Motståndsslag): 5-6 timmar ⚠️ KOMPLEXT
- **Fas 9-10** (Ongoing effects + Lossa vapen): 6-7 timmar ⚠️ KOMPLEXT
- **Fas 11-13** (Utils, AI, Polish): 3-4 timmar

### Rekommenderad implementation-ordning

1. **Vecka 1:** Fas 1-5 (grundsystem, spawning, attack, status)
   - Få systemet att fungera för grundläggande strid
   - **MILESTONE:** Systemet användbart för basic combat
   - Testat och användbart redan här

2. **Vecka 2:** Fas 6-8 (dynamiska stats, enkla effekter, motståndsslag + tabeller)
   - Lägg till specialeffekter stegvis
   - **MILESTONE:** Alla tre tabeller (R2-54, R2-55, R2-56) implementerade
   - Testa varje effekt-kategori innan nästa
   - ⚠️ Komplex vecka med mycket tabell-parsing

3. **Vecka 3:** Fas 9-11 (ongoing effects, lossa vapen, utils)
   - Komplex funktionalitet för timme/runda-tick
   - **MILESTONE:** Inre skada och vapen fastnat fungerar
   - Kräver noggrant testing

4. **Vecka 4:** Fas 12-13 (AI, polish, testing)
   - Finslipning och bugfixar
   - **MILESTONE:** Produktionsklar v1.0
   - User testing med full strid

## Framtida utökningar (ej i v1.0)

- [ ] Support för custom skadetabeller per template
- [ ] Blödningssystem (som gigantspindeln)
- [ ] Gruppattack-kommando (attackera alla fiender på en gång)
- [ ] Import/export av templates mellan guilds
- [ ] Web-baserad template-editor
- [ ] Statistik och analytics
- [ ] Initiativ-tracking för strider
- [ ] Support för non-humanoid templates (drakar, etc)

## Anteckningar

### Designbeslut tagna:
1. ✅ Multi-opponent support (flera samtidigt)
2. ✅ Per-guild lagring av instances
3. ✅ Återanvänd befintliga träfftabeller 100%
4. ✅ Templates i JSON-format (endast combat-essentials)
5. ✅ AI-beskrivningar inkluderade
6. ✅ GM-kommandon som ephemeral (dolda)
7. ✅ Publika attack-resultat för alla spelare
8. ✅ **Dynamiska stats via Discord Modals** (samlas vid behov)
9. ✅ **Automatiska motståndsslag** för alla specialeffekter
10. ✅ **Ongoing effects tracking** (vapen fastnat, kvävning, etc.)
11. ✅ **Permanenta men** persisteras och påverkar framtida slag
12. ✅ **Fasad implementation** - grundsystem först, sedan specialeffekter

### Tekniska beslut:
- **Discord Modal (Alternativ A)** för att hämta stats - pop-up formulär
- Stats sparas i `opponent.stats` dict och persisteras
- Specialeffekter implementeras i faser (enkla först, sedan komplexa)
- Tabeller (R2-54, R2-56) laddas som JSON-filer
- OngoingEffect dataclass för att tracka pågående effekter
- Permanent stat modifiers i `opponent.stat_modifiers`

### Öppna frågor:
- Hur ska vi hantera spelare som får specialeffekter? Samma Discord Modal-system?
- Behöver vi ett `/registrera_karaktär` kommando för spelare?
- Ska "Faller" och "Tappar" påverka combat mechanics (t.ex. svårare att attackera liggande)?
- Hur visualiserar vi ongoing effects bäst i status-kommandot?
- Behöver vi "healing" kommandon för fiender (t.ex. GM vill läka dem)?
- Ska vi kunna "redigera" en redan spawnad fiende (stats, rustning)?
- Behöver vi support för magisk rustning (speciella effekter)?
- Hur hanterar vi "Fumlas" på Men-effekter (extra straff)?
- Ska systemet automatiskt applicera +1T/+1S vid "Fast" varje runda, eller måste GM göra det manuellt?
- Behöver vi en "combat log" som visar hela stridshistoriken?

---

*Dokument skapat: 2025-10-13*
*Senast uppdaterat: 2025-10-13 (inkluderat specialeffekter och dynamiska stats)*

## Ändringshistorik

**2025-10-13 (v3 - KOMPLETT):**
- ✅ **Detaljerad tabellanalys** av R2-54 (Amputation), R2-55 (Bryt), R2-56 (Inre skada)
- ✅ **Mappning** av EON:s 26 kroppsdelar → Tabellrader för alla tre tabeller
- ✅ **JSON-strukturer** för alla effect_tables med exakta svårighetsgrader
- ✅ **Implementeringsflöden** för Amp, Bryt, Inre skada med alla edge cases
- ✅ **Nya kommandon:** `/timme_tick`, `/runda_tick`, `/ta_bort_effekt`
- ✅ **Uppdaterad filstruktur** med data/effect_tables/ mapp
- ✅ **Specialregler:** Hand/Fot-amputering, Kross-bonus, "Avlider omedelbart**"
- ✅ **Ongoing effects** för Inre skada (timme-baserad skada)
- ✅ Uppdaterat estimat till 28-38 timmar med tidsfördelning per fas
- ✅ Identifierat öppna frågor (Bryt-motståndsslag, Nackkotot/Ryggkotot-effekter)

**2025-10-13 (v2):**
- ✅ Lagt till omfattande EON specialeffekter (Amp, Fast, Men, Kväv, Inre skada, etc.)
- ✅ Lagt till dynamiskt stats-system med Discord Modals
- ✅ Lagt till OngoingEffect dataclass för pågående effekter
- ✅ Uppdaterat HumanoidOpponent med stats, ongoing_effects, permanent_disabilities
- ✅ Uppdaterat implementation plan till 13 faser (25-35 timmar)
- ✅ Lagt till diskussionspunkter och snabb sammanfattning
- ✅ Lagt till innehållsförteckning

**2025-10-13 (v1):**
- Initial design med grundläggande combat system
- 26 träffområden, templates, spawning, attack-integration
