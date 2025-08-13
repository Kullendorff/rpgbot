# EON Karaktärsskapande Tabeller - Översikt

## Färdiga JSON-tabeller

### Bakgrundstabeller (Huvudgrupper)
- **huvudbakgrund.json** - Huvudbakgrundstabellen som pekar till andra tabeller (1-2: börd, 3-15: föremål, etc.)
- **agodelar.json** - Föremål & Ägodelar tabell (välgjorda vapen, böcker, riddjur, etc.)
- **formogenhet.json** - Förmögenhetstabell (startkapital från ob3T6 silver till tusentals guldmynt)
- **mental_traits.json** - Mentala egenskaper (barnasinne, bildad, bärsärk, empatisk, etc.)
- **physical_traits.json** - Fysiska egenskaper (alkoholresistent, ambidextriös, extraordinärt stark, etc.)
- **supernatural_trait.json** - Övernaturliga egenskaper (andesyn, andra chans, magisk affinitet, etc.)
- **disadvantages.json** - Nackdelar (alkoholist, blind, döv, feg, förföljd, etc.)
- **social_traits.json** - Sociala egenskaper (OFÄRDIG - bara enkla beskrivningar)

### Familjetabeller
- **familj/familj_ovr.json** - Familjetabell för övriga (adopterad, blodsfejd, religiös familj, etc.)
- **familj/huvudnäring_civ_hamnstad.json** - Familjens huvudnäring för civiliserad hamnstad

### Bördtabeller (per kultur)
- **bord/bord_asharier.json** - Börd för Asharier
- **bord/bord_cirefalier.json** - Börd för Cirefalier  
- **bord/bord_ovr_civ.json** - Börd för övriga civiliserade kulturer
- **bord/bord_primitiva.json** - Börd för primitiva kulturer
- **bord/bord_thalask.json** - Börd för Thalasker

### Händelsetabeller
- **handelser/ovriga_handelser.json** - Händelser för övriga kulturer
- **handelser/alver_hand.json** - Händelser specifika för alver
- **handelser/thalask_hand.json** - Händelser för Thalasker
- **handelser/thalask_atte.json** - Thalaskiska ättetabeller

### Folkslag/Raser
- **folkslag/attribute_modifiers.json** - Attributmodifierare för alla folkslag/raser
- **folkslag/humans/** - Mapp med humanspecifika tabeller (under utveckling)

### Länder/Hemort
- **landerhemort/** - 37 textfiler med detaljerade beskrivningar av länder (Soldarn.txt, Asharien.txt, etc.)

## Tabeller som behöver konverteras/kompletteras

### Behöver JSON-formatering
- **background_tables.json** - Bara enkel lista, behöver full struktur
- **social_traits.json** - Bara enkla beskrivningar, behöver full JSON-struktur med result/description

### Behöver utökas
- **folkslag/** - Många .txt-filer som behöver struktureras som JSON
- **familj/** - Bara en huvudnäringstabell klar, behöver fler (landsbygd, inlandstad, etc.)
- **bord/** - Saknar troligen fler kulturer/folkslag

### Pågående utveckling
- Flera "New Text Document" filer i olika mappar som troligen är work-in-progress

## Format-standard

Alla färdiga tabeller följer detta format:
```json
{
  "tabellnamn": {
    "titel": "Beskrivande titel",
    "beskrivning": "Förklaring av tabellens syfte",
    "dice": "1d100",
    "ranges": {
      "1-25": {
        "result": "kort_nyckel",
        "description": "Full beskrivning från originalet"
      }
    }
  }
}
```

Subtabeller och conditionals hanteras med nested strukturer.

## Status för karaktärsskapandets 33 steg

**Steg 1-4 (Grundläggande val):**
- ✅ Kön: Trivial implementation
- ✅ Hemland: 37 länder klara i textformat
- 🔄 Folkslag: Attributmodifierare klara, behöver beskrivningar
- ✅ Ålder: Bara input + validering

**Steg 5+ (Komplexa tabeller):**
- 🔄 Attribut: Regler finns, behöver implementation  
- 🔄 Bakgrund: Många tabeller klara, men inte alla kopplingar
- ❌ Yrken: Behöver stora tabeller för alla kulturer
- ❌ Färdigheter: Beror på yrke + bakgrund
- ❌ Kontakter: Helt saknas ännu

**Legend:**
- ✅ Klar för implementation
- 🔄 Delvis klar / under utveckling  
- ❌ Behöver skapas från grunden
