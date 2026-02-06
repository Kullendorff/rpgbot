# ARKIVDOKUMENTATION: EON Karaktärsskapande-System

**Status:** Pensionerad 2026-02-06
**Syfte:** Referensdokumentation for framtida rekonstruktion

---

## 1. STEG-ORDNING (33 Steg)

| Steg | Modul | Namn | Data-nyckel | Speciallogik |
|------|-------|------|-------------|--------------|
| 1 | GenderStep | Kon | `kon` | 3 val: kvinna, man, annat |
| 2 | HomelandStep | Hemland | `hemland` | 36 hemlaender fraan txt-filer |
| 3 | RaceStep | Folkslag | `folkslag` | **THALAMUR SPECIAL**: medborgare/folket |
| 4 | AgeStep | Alder | `alder` | Bakgrundslag-bonus +1-5 |
| 5 | CultureStep | Kultur | `kultur` | Faerdighetsbonus fraan huvudnaring.json |
| 6 | AttributesStep | Grundattribut | `attribut` | 3 metoder: 3d6, 4d6, 2d6+9 |
| 7 | SpecialRulesStep | Specialregler | `specialregler` | **CIREFALIER**: field_storning.json |
| 8 | TraitsStep | Karaktaersdrag | `traits` | 6 traits, race-specifika T6-modifier |
| 9-11 | FamilyStep | Familjebakgrund | `familj` | AutomaticBackgroundGenerator |
| 12 | BackgroundStep | Bakgrundsslag-antal | `antal_bakgrundslag` | T100-berakning per ras/alder |
| 13 | BackgroundStep | Huvudbakgrund | `huvudbakgrund_results` | TableProcessor-rullar |
| 14 | BackgroundStep | Bakgrundshaendelser | `bakgrundshandelser` | Processerar varje resultat |
| 15-31 | (Reserverade) | (Framtida) | - | Ej implementerade |
| 32 | SummaryStep | Sammanfattning | `summary` | Visar komplett karaktaer |

---

## 2. DATA-MODELL

### session.data (Permanent lagring)

```python
{
    # Steg 1-5: Grundlaeggande
    'kon': 'kvinna' | 'man' | 'annat',
    'hemland': 'thalamur',          # lowercase
    'hemland_title': 'Thalamur',    # display
    'folkslag': 'Vanar',
    'folkslag_variant': None,       # optional variant
    'use_thalamur_special': True,   # if Thalamur
    'thalamur_samhallsklass': 'Medborgare' | 'Folket',
    'thalamur_special': 'thalasker_medborgare' | 'thalasker_folket',
    'alder': 25,
    'alder_bakgrundslag_bonus': 0-5,
    'kultur': 'civiliserad',
    'kultur_title': 'Civiliserad',
    'kultur_bonus': ['Skepnad +1', '+2 Vaepnade Strider'],
    'kultur_info': {full kultur dict},

    # Steg 6-8: Attribut & Traits
    'attribut': {
        'STY': 14, 'TAL': 12, 'ROR': 11, 'PER': 13, 'PSY': 10,
        'VIL': 12, 'BIL': 9, 'SYN': 13, 'HOR': 11
    },
    'attribut_summa': 115,
    'attribut_chockvaerde': 13,
    'attribut_metod': '3d6',
    'specialregler': {...},
    'traits': {
        'lojalitet': 15, 'heder': 12, 'amor': 9,
        'aggression': 11, 'tro': 14, 'generositet': 10
    },

    # Steg 9: Familj
    'familj': {
        'basic': {
            'birth_info': '...',
            'siblings': [...],
            'father': {status, age, death_cause},
            'mother': {status, age, death_cause},
        },
        'profession': 'Bonde',
        'special_family': {...},
        'thalask_family': {...}  # If Thalasker
    },

    # Steg 12-14: Bakgrund
    'antal_bakgrundslag': 7,
    'huvudbakgrund_results': [{roll, result, description}, ...],
    'bakgrundshandelser': [{event, processed, ...}, ...],
}
```

### session.temp_data (Temporaer foere bekraeftelse)

```python
{
    'folkslag': {'name': 'Vanar', 'title': 'Vanar', 'category': 'human'},
    'culture_options': [{'number': 1, 'key': 'civiliserad', ...}],
    'attribut': {...},
    'traits': {...},
}
```

---

## 3. DATA-FILER (data/character_tables/)

```
data/character_tables/
+-- landerhemort/              # 36 hemlaender som .txt
|   +-- thalamur.txt
|   +-- det_cirefaliska_samvaeldet.txt
|   +-- ...
+-- folkslag/
|   +-- humans/               # ~15 folk
|   +-- alver/                # ~7 elf races
|   +-- dvaergar/             # ~4 dwarf races
|   +-- tiraker/              # ~5 tirak races
|   +-- attribute_modifiers.json
+-- familj/
|   +-- huvudnaring.json      # Kulturdata
|   +-- familj_ovr.json       # Allmaenna familjetabeller
|   +-- familj_thalask.json   # Thalasker special
+-- bord/
|   +-- bord_ovr_civ.json     # Boerd foer civiliserade
|   +-- bord_primitiva.json
|   +-- bord_cirefalier.json  # Cirefalier special
|   +-- bord_thalask.json     # Thalasker special
|   +-- bord_asharier.json
+-- handelser/
|   +-- alver_hand.json       # Elf events
|   +-- thalask_hand.json     # Thalasker events
|   +-- thalask_atte.json     # Thalasker aett-events
|   +-- ovriga_handelser.json
+-- huvudbakgrund.json        # Huvudbakgrundstabell (T100)
+-- field_storning.json       # Cirefalier faeltstoerningar
+-- homeland_races.json       # T100 hemland->folkslag mapping
+-- mental_traits.json
+-- physical_traits.json
+-- social_traits.json
+-- disadvantages.json
+-- supernatural_trait.json
+-- livsprinciper.json
+-- egenheter.json
+-- agodelar.json
+-- formogenhet.json
```

---

## 4. ARKITEKTUR

### BaseStep ABC-Pattern

```python
class BaseStep(ABC):
    def __init__(self, step_name: str, step_number: int):
        self.step_name = "kon"
        self.step_number = 1
        self.next_step = None
        self.previous_step = None

    @abstractmethod
    async def execute(ctx, session) -> discord.Embed: ...

    @abstractmethod
    async def handle_input(ctx, session, input_text) -> (bool, str?): ...

    @abstractmethod
    def validate_prerequisites(session) -> (bool, str?): ...

    def save_step_data(session, data: Dict): ...
    def validate_data(session) -> bool: ...
    def can_skip(session) -> bool: ...
```

### CharacterSession

```python
@dataclass
class CharacterSession:
    user_id: str
    current_step: int = 1
    max_steps: int = 32
    data: Dict[str, Any] = None
    temp_data: Dict[str, Any] = None
    context: CharacterContext = None
    created_at: datetime = None

    def update_context() -> None
    def increment_step() -> None
    def commit_temp_data() -> None
    def clear_temp_data() -> None
    def save_to_file(directory) -> None
    @classmethod from_dict(data) -> CharacterSession
```

### TableProcessor

```python
class TableProcessor:
    def roll_on_table(table_name, subtable_name?, context?) -> TableResult
    def roll_with_auto_resolution(table_name, subtable_name?, context?) -> TableResult
    def _resolve_conditionals(range_data, context) -> Dict

class CharacterContext:
    folkslag: str   # 'alv' | 'dvaerg' | 'tirak' | 'maenniska'
    stam: str?      # 'henea' | 'kiriya' | 'sanari' etc.
    social_class: str?
    kultur: str     # 'civiliserad' | 'primitiv'
    location: str?  # 'hamnstad' | 'inlandsstad' | 'landsbygd'
```

---

## 5. THALAMUR SPECIAL-LOGIK

```
homeland == "thalamur"
  -> _handle_thalamur_special()
     +-- "medborgare":
     |   folkslag = 'Thalasker'
     |   thalamur_special = 'thalasker_medborgare'
     |   thalamur_samhallsklass = 'Medborgare'
     |   -> Anvander familj_thalask.json
     |   -> Anvander thalask_hand.json + thalask_atte.json
     |
     +-- "folket":
         folkslag = 'Vanar'
         thalamur_special = 'thalasker_folket'
         thalamur_samhallsklass = 'Folket'
         -> Anvander standard familjetabeller
```

---

## 6. RAS-SUPPORT STATUS

### Fullt implementerat
- **Vanar** (human) - Standardrasen
- **Cirefalier** (human) - Med field_storning.json
- **Thalasker** (human) - Med aette-system
- **Pyar** (elf) - Med mentorskap

### Partiellt implementerat
- **Ghor** (dwarf) - Attribut, familj
- **Marnakh** (tirak) - Attribut, familj
- **Sanari, Thism** (elves) - Attribut, familj

### Ej implementerat
- Kiriya, Learam, Henea (elves)
- Roghan, Drezin, Zolod (dwarves)
- Bazirk, Frakk, Gurd, Truhk (tiraks)

---

## 7. KAENDA BUGGAR

1. **race.py rad 199**: `session.temp_data = {..}` OEVERSKRIVER all temp_data
   Fix: `session.temp_data.update({..})`

2. **HomelandRaceMapper**: homeland_races.json fallback till hardkodad lista

3. **AttributesStep**: Modifier-fil foervaentar annan struktur aen vad step laddar

4. **TraitsStep**: Ofullstaendig race-mapping, saknar fallback

5. **SpecialRulesStep**: Cirefalier multi-roll TODO, inte implementerat

---

## 8. DESIGN-BESLUT

1. **Modulaer step-arkitektur**: Separation of concerns, enkel testning
2. **session.data vs temp_data**: Bekraeftad vs pending data, tillater back-stepping
3. **T100 race-selection**: Realistiska sannolikheter per hemland
4. **CharacterContext**: TableProcessor behoever context foer conditional logic
5. **AutomaticBackgroundGenerator**: Komplett familjegenerering utan manuella tabeller
6. **Thalamur som samhaellsklass**: Medborgare/Folket aer samma ras, olika klass

---

## 9. ATERSKAPANDE

Foer att aaterskapa systemet:

1. Borja med `BaseStep` ABC + `CharacterSession` dataclass
2. Implementera enkla steg foerst: Gender, Homeland, Age
3. Lagg till RaceStep med Thalamur-special
4. Bygg TableProcessor foer JSON-tabeller
5. Implementera AttributesStep med race modifiers
6. Lagg till Family + Background (mest komplexa stegen)
7. Data-filerna i `data/character_tables/` aer intakta och kan ateranvaendas direkt

**Notera:** All data-filer (JSON/TXT) behoells - bara Python-koden tas bort.
