"""
EON TableProcessor - Hanterar komplexa bakgrundstabeller för rollspelet EON
Designad för att hantera hierarkiska tabeller, conditional logic och nested structures
"""

import json
import random
import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

@dataclass
class TableResult:
    """Representerar resultatet från ett tabellslag"""
    result: str                    # Kort nyckel (t.ex. "mentor", "lurad_pÃ¥_pengar")
    description: str               # Full beskrivning från tabellen
    source_table: str             # Vilken tabell resultatet kom från
    roll_value: int               # Värdet som rullades
    sub_results: List['TableResult'] = None  # Resultat från subtabeller
    metadata: Dict[str, Any] = None          # Extra data (skills, bonuses etc.)

    def __post_init__(self):
        if self.sub_results is None:
            self.sub_results = []
        if self.metadata is None:
            self.metadata = {}

@dataclass
class Benefit:
    """Representerar en fördel/bonus från en bakgrundshändelse"""
    benefit_type: str              # "skill", "attribute", "easy_skill", "money"
    target: str                   # "etikett", "STY", "alla_kunskaper" etc.
    value: str                    # "1T6+4", "+2", "lättlärd" etc.
    description: str              # Original beskrivning
    
@dataclass
class BenefitParser:
    """Parsar benefits från tabellbeskrivningar"""
    
    @staticmethod
    def extract_benefits(description: str) -> List['Benefit']:
        """Extraherar alla benefits från en beskrivning"""
        benefits = []
        desc_lower = description.lower()
        
        # Pattern 1: "Du får 1T6+4 enheter att spendera på färdigheten etikett"
        skill_pattern = r'du får ([0-9dt6+\-]+) enheter att spendera på färdigheten (\w+)'
        for match in re.finditer(skill_pattern, desc_lower):
            dice_str, skill_name = match.groups()
            benefits.append(Benefit(
                benefit_type="skill",
                target=skill_name,
                value=dice_str,
                description=match.group(0)
            ))
        
        # Pattern 2: "Öka RPs [attribut] med +2" 
        attr_pattern = r'öka rps? (\w+) med ([+\-]?\d+)'
        for match in re.finditer(attr_pattern, desc_lower):
            attr_name, modifier = match.groups()
            benefits.append(Benefit(
                benefit_type="attribute",
                target=attr_name,
                value=modifier,
                description=match.group(0)
            ))
        
        # Pattern 3: "ALLA kunskapsfärdigheter blir lättlärda"
        if 'alla kunskapsfärdigheter blir lättlärda' in desc_lower:
            benefits.append(Benefit(
                benefit_type="easy_skill",
                target="alla_kunskaper",
                value="lättlärd",
                description="ALLA kunskapsfärdigheter blir lättlärda"
            ))
        
        # Pattern 4: "Alla [kategori] färdigheter blir lättlärda"
        easy_skill_pattern = r'alla (\w+) färdigheter blir lättlärda'
        for match in re.finditer(easy_skill_pattern, desc_lower):
            skill_category = match.groups()[0]
            benefits.append(Benefit(
                benefit_type="easy_skill", 
                target=skill_category,
                value="lättlärd",
                description=match.group(0)
            ))
        
        # Pattern 5: Pengar och förmögenhet
        money_patterns = [
            r'(\d+) kopparmynt',
            r'(\d+) silvermynt', 
            r'(\d+) guldmynt',
            r'([0-9dt6+\-]+) kopparmynt',
            r'([0-9dt6+\-]+) silvermynt',
            r'([0-9dt6+\-]+) guldmynt'
        ]
        
        for pattern in money_patterns:
            for match in re.finditer(pattern, desc_lower):
                amount = match.groups()[0]
                currency = 'koppar' if 'koppar' in match.group(0) else \
                          'silver' if 'silver' in match.group(0) else 'guld'
                benefits.append(Benefit(
                    benefit_type="money",
                    target=currency,
                    value=amount,
                    description=match.group(0)
                ))
        
        return benefits

@dataclass 
class CharacterContext:
    """Karaktärens kontext för conditional logic"""
    folkslag: Optional[str] = None       # "alv", "dvarg", "tirak" etc.
    stam: Optional[str] = None           # "bazirk", "frakk", "marnakh" för tiraker
    social_class: Optional[str] = None   # "riddare", "adlig", "civiliserad"
    kultur: Optional[str] = None         # "primitiv", "civiliserad"
    location: Optional[str] = None       # "hamnstad", "inlandsstad", "landsbygd"

class TableProcessor:
    """
    Hanterar alla EON bakgrundstabeller med stöd för:
    - Hierarkisk navigation (huvudbakgrund -> specifika tabeller)
    - Conditional logic baserat på folkslag/kultur/social_class
    - Nested subtables med egna ranges
    - "Roll twice" mechanics 
    - Textfiler för länder/beskrivningar
    """
    
    def __init__(self, data_dir: str = None):
        if data_dir is None:
            # Auto-detect data directory relative to script location
            script_dir = Path(__file__).parent
            project_root = script_dir.parent
            self.data_dir = project_root / 'data' / 'character_tables'
        else:
            self.data_dir = Path(data_dir)
        self.tables = {}
        self.text_files = {}
        self.load_all_data()
    
    def load_all_data(self):
        """Laddar alla JSON-tabeller och textfiler"""
        try:
            # Ladda JSON-tabeller
            for json_file in self.data_dir.glob("**/*.json"):
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        table_name = json_file.stem
                        self.tables[table_name] = data
                        logger.info(f"Laddade tabell: {table_name}")
                except Exception as e:
                    logger.error(f"Kunde inte ladda {json_file}: {e}")
            
            # Ladda textfiler (länder etc.)
            for txt_file in self.data_dir.glob("**/*.txt"):
                try:
                    with open(txt_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        file_name = txt_file.stem
                        self.text_files[file_name] = content
                        logger.info(f"Laddade textfil: {file_name}")
                except Exception as e:
                    logger.error(f"Kunde inte ladda {txt_file}: {e}")
                    
            logger.info(f"Totalt laddade {len(self.tables)} tabeller och {len(self.text_files)} textfiler")
            
        except Exception as e:
            logger.error(f"Fel vid laddning av data: {e}")
            raise

    def roll_on_table(self, table_name: str, subtable_name: str = None, 
                     context: CharacterContext = None) -> TableResult:
        """
        Huvudfunktion för att rulla på en tabell
        
        Args:
            table_name: Namnet på JSON-filen (utan .json)
            subtable_name: Specifik subtabell inom JSON-filen (t.ex. "huvudtabell")
            context: Karaktärens kontext för conditional logic
        
        Returns:
            TableResult med resultat och eventuella sub-resultat
        """
        if context is None:
            context = CharacterContext()
            
        # Hitta tabellen
        if table_name not in self.tables:
            raise ValueError(f"Tabell '{table_name}' hittades inte")
        
        table_data = self.tables[table_name]
        
        # Navigera till rätt subtabell
        if subtable_name:
            # Hierarkisk navigation: bakgrundstabeller.huvudtabell
            parts = subtable_name.split('.')
            current = table_data
            for part in parts:
                if part in current:
                    current = current[part]
                else:
                    raise ValueError(f"Subtabell '{subtable_name}' hittades inte i '{table_name}'")
            table_config = current
        else:
            # Ta första huvudnyckel om ingen subtabell specificeras
            main_keys = list(table_data.keys())
            if main_keys:
                table_config = table_data[main_keys[0]]
            else:
                raise ValueError(f"Tom tabell: {table_name}")
        
        return self._roll_on_table_config(table_config, table_name, context)
    
    def _roll_on_table_config(self, table_config: Dict, source_table: str, 
                             context: CharacterContext) -> TableResult:
        """Rullar på en specifik tabellkonfiguration"""
        
        if 'dice' not in table_config or 'ranges' not in table_config:
            raise ValueError(f"Ogiltig tabellkonfiguration i {source_table}")
        
        # Rulla tärning
        dice_str = table_config['dice']
        roll_value = self._roll_dice(dice_str)
        
        # Hitta vilket range som matchar
        ranges = table_config['ranges']
        matching_range = None
        
        for range_str, range_data in ranges.items():
            if self._value_in_range(roll_value, range_str):
                matching_range = range_data
                break
        
        if matching_range is None:
            raise ValueError(f"Inget range matchar värde {roll_value} i {source_table}")
        
        # Hantera conditional logic
        final_result = self._resolve_conditionals(matching_range, context)
        
        # Extrahera benefits från beskrivning
        description = final_result.get('description', '')
        benefits = BenefitParser.extract_benefits(description)
        
        # Skapa huvudresultat
        result = TableResult(
            result=final_result.get('result', 'unknown'),
            description=description,
            source_table=source_table,
            roll_value=roll_value,
            metadata={'benefits': benefits} if benefits else None
        )
        
        # Hantera subtabeller
        if final_result.get('has_subtable', False) and 'subtable' in final_result:
            subtable_result = self._roll_on_table_config(
                final_result['subtable'], f"{source_table}_subtable", context
            )
            result.sub_results.append(subtable_result)
        
        # Hantera "roll twice" mechanics (pattern-based)
        if self._should_roll_multiple(final_result):
            num_additional_rolls = self._extract_roll_count(final_result.get('description', ''))
            additional_results = []
            
            for _ in range(num_additional_rolls):
                additional_result = self._roll_on_table_config(table_config, source_table, context)
                additional_results.append(additional_result)
            
            result.sub_results.extend(additional_results)
            
            # Uppdatera description för att visa att det är multiple results
            if num_additional_rolls > 1:
                result.description += f" [Genererade {num_additional_rolls} extra resultat]"
        
        return result
    
    def _resolve_conditionals(self, range_data: Dict, context: CharacterContext) -> Dict:
        """Hanterar conditional logic baserat på karaktärens kontext"""
        
        if 'conditions' not in range_data:
            return range_data
        
        conditions = range_data['conditions']
        
        # Kontrollera varje condition
        for condition_key, condition_result in conditions.items():
            if self._check_condition(condition_key, context):
                return condition_result
        
        # Om ingen condition matchar, returnera default
        return range_data
    
    def _check_condition(self, condition_key: str, context: CharacterContext) -> bool:
        """Kontrollerar en specifik condition mot karaktärens kontext"""
        
        # EON-specifika conditions
        if condition_key == "not_alv_bazirk_frakktirak":
            return not (context.folkslag == "alv" or 
                       (context.folkslag == "tirak" and context.stam in ["bazirk", "frakk"]))
        
        elif condition_key == "is_bazirk_frakktirak":
            return context.folkslag == "tirak" and context.stam in ["bazirk", "frakk"]
        
        elif condition_key == "is_alv":
            return context.folkslag == "alv"
        
        elif condition_key == "not_alv":
            return context.folkslag != "alv"
        
        elif condition_key == "is_tirak":
            return context.folkslag == "tirak"
        
        elif condition_key == "not_tirak":
            return context.folkslag != "tirak"
        
        elif condition_key == "is_riddare":
            return context.social_class == "riddare"
        
        elif condition_key == "not_riddare":
            return context.social_class != "riddare"
        
        elif condition_key == "not_tirak_dvärg":
            return context.folkslag not in ["tirak", "dvärg"]
        
        elif condition_key == "is_dvärg":
            return context.folkslag == "dvärg"
        
        elif condition_key == "not_dvärg":
            return context.folkslag != "dvärg"
        
        # Alv-linjer (från alver_hand.json patterns)
        elif condition_key == "henea":
            return context.folkslag == "alv" and context.stam == "henea"
        
        elif condition_key == "not_henea":
            return not (context.folkslag == "alv" and context.stam == "henea")
        
        elif condition_key == "kiriya":
            return context.folkslag == "alv" and context.stam == "kiriya"
        
        elif condition_key == "thism":
            return context.folkslag == "alv" and context.stam == "thism"
        
        elif condition_key == "sanari":
            return context.folkslag == "alv" and context.stam == "sanari"
        
        elif condition_key == "learam":
            return context.folkslag == "alv" and context.stam == "learam"
        
        elif condition_key == "pyar":
            return context.folkslag == "alv" and context.stam == "pyar"
        
        # Kultur-specifika conditions
        elif condition_key == "civiliserad":
            return context.kultur == "civiliserad"
        
        elif condition_key == "primitiv":
            return context.kultur == "primitiv"
        
        elif condition_key == "not_civiliserad":
            return context.kultur != "civiliserad"
        
        # Lägg till fler conditions vid behov...
        
        logger.warning(f"Okänd condition: {condition_key}")
        return False
    
    def _should_roll_multiple(self, result_data: Dict) -> bool:
        """Kontrollerar om resultatet indikerar att fler slag behövs"""
        description = result_data.get('description', '').lower()
        
        # Pattern matching för roll twice/multiple mechanics
        roll_patterns = [
            'slå två gånger till',
            'slå om två gånger',  
            'roll twice',
            'fler egenskaper',
            'extra slag'
        ]
        
        return any(pattern in description for pattern in roll_patterns)
    
    def _extract_roll_count(self, description: str) -> int:
        """Extraherar antal extra slag från beskrivning"""
        description = description.lower()
        
        # Look for specific numbers
        if 'två' in description or 'two' in description:
            return 2
        elif 'tre' in description or 'three' in description:
            return 3
        elif 'fyra' in description or 'four' in description:
            return 4
        
        # Default för "roll twice" mechanics
        return 2
    
    def _value_in_range(self, value: int, range_str: str) -> bool:
        """Kontrollerar om ett värde är inom ett specificerat range"""
        
        if '-' in range_str:
            # Range som "1-25" eller "66-67"
            start, end = map(int, range_str.split('-'))
            return start <= value <= end
        else:
            # Enskilt värde som "100"
            return value == int(range_str)
    
    def _roll_dice(self, dice_str: str) -> int:
        """Rullar tärningar baserat på notation som '1d100', '2d6+3', 'ob2T6', '2T6' etc."""
        
        dice_str = dice_str.lower().strip()
        
        # Hantera svenska/EON notation först
        if 't6' in dice_str or 't10' in dice_str:
            return self._roll_eon_dice(dice_str)
        
        # Standard d-notation
        if 'd' not in dice_str:
            raise ValueError(f"Ogiltig tärningsnotation: {dice_str}")
        
        # Regex för att matcha: [antal]d[sidor][+/-modifier]
        pattern = r'(\d*)d(\d+)([+-]\d+)?'
        match = re.match(pattern, dice_str)
        
        if not match:
            raise ValueError(f"Kunde inte tolka tärningsnotation: {dice_str}")
        
        count_str, sides_str, modifier_str = match.groups()
        
        count = int(count_str) if count_str else 1
        sides = int(sides_str)
        modifier = int(modifier_str) if modifier_str else 0
        
        # Säkerhetsgränser
        if count > 100 or sides > 1000:
            raise ValueError(f"För många tärningar eller sidor: {dice_str}")
        
        # Rulla tärningarna
        total = sum(random.randint(1, sides) for _ in range(count))
        return total + modifier
    
    def _roll_eon_dice(self, dice_str: str) -> int:
        """Hanterar EON-specifik tärningsnotation som 'ob2T6', '2T6', '1T6+4'"""
        
        dice_str = dice_str.lower().strip()
        
        # Hantera obegränsade slag (ob prefix)
        is_unlimited = dice_str.startswith('ob')
        if is_unlimited:
            dice_str = dice_str[2:]  # Ta bort 'ob' prefix
        
        # Regex för T-notation: [antal]T[sidor][+/-modifier]
        pattern = r'(\d*)t(\d+)([+-]\d+)?'
        match = re.match(pattern, dice_str)
        
        if not match:
            raise ValueError(f"Kunde inte tolka EON tärningsnotation: {dice_str}")
        
        count_str, sides_str, modifier_str = match.groups()
        
        count = int(count_str) if count_str else 1
        sides = int(sides_str)  
        modifier = int(modifier_str) if modifier_str else 0
        
        # Säkerhetsgränser
        if count > 100 or sides > 1000:
            raise ValueError(f"För många tärningar eller sidor: {dice_str}")
        
        if is_unlimited and sides == 6:
            # Använd unlimited d6 logic från dice_engine om tillgänglig
            # Annars enkel approximation
            total = 0
            for _ in range(count):
                die_total = 0
                while True:
                    roll = random.randint(1, 6)
                    if roll == 6:
                        continue  # 6or räknas inte, men triggar fler tärningar
                    else:
                        die_total += roll
                        break
                total += die_total
            return total + modifier
        else:
            # Vanligt tärningsslag
            total = sum(random.randint(1, sides) for _ in range(count))
            return total + modifier

    def get_table_info(self, table_name: str) -> Dict[str, Any]:
        """Returnerar information om en tabell"""
        
        if table_name not in self.tables:
            return None
        
        table_data = self.tables[table_name]
        
        # Extrahera metadata från första subtabellen
        main_key = list(table_data.keys())[0]
        main_table = table_data[main_key]
        
        return {
            'name': table_name,
            'title': main_table.get('titel', ''),
            'description': main_table.get('beskrivning', ''),
            'dice': main_table.get('dice', ''),
            'range_count': len(main_table.get('ranges', {}))
        }
    
    def list_available_tables(self) -> List[str]:
        """Returnerar lista över alla tillgängliga tabeller"""
        return list(self.tables.keys())
    
    def resolve_table_reference(self, result_key: str, context: CharacterContext) -> Optional[str]:
        """Löser cross-references till andra tabeller baserat på resultatnyckel och kontext"""
        
        # Standardmappningar från huvudbakgrund till specifika tabeller
        table_mapping = {
            'mentala_egenskaper': 'mental_traits',
            'fysiska_egenskaper': 'physical_traits', 
            'sociala_egenskaper': 'social_traits',
            'nackdelar': 'disadvantages',
            'supernatural_traits': 'supernatural_trait',
            'börd': self._get_birth_table_for_context(context),
            'händelser': self._get_events_table_for_race(context.folkslag if context else None),
            'familj': 'familj_ovr',
            'ägodelar': 'agodelar',
            'förmögenhet': 'formogenhet'
        }
        
        return table_mapping.get(result_key)
    
    def _get_events_table_for_race(self, folkslag: str) -> str:
        """Bestämmer vilken händelsetabell som ska användas baserat på folkslag"""
        if not folkslag:
            return 'ovriga_handelser'
            
        folkslag_lower = folkslag.lower()
        
        if folkslag_lower == 'alv':
            return 'alver_hand'
        elif folkslag_lower == 'thalask':
            return 'thalask_hand'
        else:
            return 'ovriga_handelser'
    
    def _get_birth_table_for_context(self, context: CharacterContext) -> str:
        """Bestämmer vilken börd-tabell som ska användas baserat på kontext"""
        if not context or not context.kultur:
            return 'bord_ovr_civ'  # Default civiliserad
            
        kultur = context.kultur.lower()
        folkslag = context.folkslag.lower() if context.folkslag else ''
        
        # Specifika bordstabeller baserat på kultur och folkslag
        if kultur == 'primitiv':
            return 'bord_primitiva'
        elif folkslag == 'thalask':
            return 'bord_thalask'
        elif 'ashari' in folkslag or 'asharier' in folkslag:
            return 'bord_asharier'
        elif 'cirefalier' in folkslag:
            return 'bord_cirefalier'
        else:
            return 'bord_ovr_civ'  # Civiliserad övrig som default
    
    def roll_with_auto_resolution(self, table_name: str, subtable_name: str = None,
                                 context: CharacterContext = None, auto_resolve_depth: int = 1) -> TableResult:
        """
        Rullar på tabell med automatisk upplösning av cross-references
        
        Args:
            table_name: Huvudtabell att rulla på
            subtable_name: Specifik subtabell
            context: Karaktärens kontext
            auto_resolve_depth: Hur djupt auto-resolution ska gå (0=av, 1=en nivå, 2=två nivåer)
        """
        if context is None:
            context = CharacterContext()
        
        # Rulla på huvudtabellen
        main_result = self.roll_on_table(table_name, subtable_name, context)
        
        # Auto-resolve om aktiverat och resultat pekar på annan tabell
        if auto_resolve_depth > 0:
            referenced_table = self.resolve_table_reference(main_result.result, context)
            
            if referenced_table and referenced_table in self.tables:
                try:
                    # Rulla på den refererade tabellen
                    sub_result = self.roll_with_auto_resolution(
                        referenced_table, None, context, auto_resolve_depth - 1
                    )
                    main_result.sub_results.append(sub_result)
                    
                    # Uppdatera metadata för att visa att auto-resolution användes
                    if main_result.metadata is None:
                        main_result.metadata = {}
                    main_result.metadata['auto_resolved'] = referenced_table
                    
                except Exception as e:
                    logger.warning(f"Kunde inte auto-resolve till {referenced_table}: {e}")
        
        return main_result

# Hjälpfunktioner för Discord-kommandon

def roll_background_sequence(context: CharacterContext, num_rolls: int = 3, 
                            use_auto_resolution: bool = True) -> List[TableResult]:
    """
    Rullar en sekvens av bakgrundshändelser för karaktärsskapande
    Simulerar EON:s bakgrundssystem med automatisk table resolution
    """
    processor = TableProcessor()
    results = []
    
    for _ in range(num_rolls):
        if use_auto_resolution:
            # Använd nya auto-resolution funktionen
            main_result = processor.roll_with_auto_resolution(
                'huvudbakgrund', 'bakgrundstabeller.huvudtabell', context, auto_resolve_depth=2
            )
        else:
            # Gamla manuella metoden
            main_result = processor.roll_on_table('huvudbakgrund', 'bakgrundstabeller.huvudtabell', context)
            
            # Manuell resolution för bakåtkompatibilitet
            referenced_table = processor.resolve_table_reference(main_result.result, context)
            if referenced_table and referenced_table in processor.tables:
                try:
                    specific_result = processor.roll_on_table(referenced_table, context=context)
                    main_result.sub_results.append(specific_result)
                except Exception as e:
                    logger.warning(f"Kunde inte rulla på {referenced_table}: {e}")
        
        results.append(main_result)
    
    return results

def create_character_context(folkslag: str, kultur: str = None, social_class: str = None) -> CharacterContext:
    """Skapar en CharacterContext från grundläggande information"""
    
    context = CharacterContext(folkslag=folkslag.lower())
    
    # Automatisk härledning av kultur och social_class baserat på folkslag
    if folkslag.lower() == 'alv':
        context.kultur = 'civiliserad'  # De flesta alver
    elif folkslag.lower() == 'tirak':
        context.kultur = 'primitiv'
    elif folkslag.lower() == 'dvärg':
        context.kultur = 'civiliserad'
        
    # Sätt explicit kultur om angiven
    if kultur:
        context.kultur = kultur.lower()
    
    if social_class:
        context.social_class = social_class.lower()
    
    return context
