"""
Rollpersonsskapande-modul för EON Diceroller Bot
Hanterar attributgenerering, tabellslag och karaktärsskapande
"""

import json
import os
import random
import discord
from typing import Dict, List, Optional, Tuple, Any
from discord.ext import commands

class CharacterCreator:
    """Huvudklass för rollpersonsskapande funktionalitet"""
    
    def __init__(self, data_dir: str = None):
        if data_dir is None:
            # Hitta data-mappen relativt till skriptets placering
            script_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(script_dir)
            self.data_dir = os.path.join(project_root, 'data', 'character_tables')
        else:
            self.data_dir = data_dir
            
        # Skapa mappen om den inte finns
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Ladda alla tabeller
        self.tables = self.load_tables()
    
    def load_tables(self) -> Dict[str, Any]:
        """Laddar alla tabeller från JSON-filer"""
        tables = {}
        
        # Lista över alla tabellkonfigurationer
        table_files = [
            'attribute_modifiers.json',
            'background_tables.json', 
            'physical_traits.json',
            'mental_traits.json',
            'social_traits.json',
            'disadvantages.json',
            'birth_tables.json',
            'property_tables.json',
            'events_tables.json'
        ]
        
        for filename in table_files:
            filepath = os.path.join(self.data_dir, filename)
            try:
                if os.path.exists(filepath):
                    with open(filepath, 'r', encoding='utf-8') as f:
                        table_name = filename.replace('.json', '')
                        tables[table_name] = json.load(f)
                        print(f"Laddade tabell: {table_name}")
                else:
                    print(f"Varning: Kunde inte hitta tabell {filename}")
                    # Skapa tom tabell som placeholder
                    tables[filename.replace('.json', '')] = {}
            except Exception as e:
                print(f"Fel vid laddning av {filename}: {e}")
                tables[filename.replace('.json', '')] = {}
        
        return tables
    
    def generate_attributes(self, method: str = "3d6") -> Dict[str, int]:
        """
        Genererar grundattribut enligt olika metoder
        
        Args:
            method: Metod för attributgenerering
                   "3d6" - Standard 3T6
                   "4d6" - 4T6, ta bästa 3
                   "2d6+9" - 2T6+9
        
        Returns:
            Dict med attributnamn och värden
        """
        attributes = {}
        attribute_names = ["STY", "TÅL", "RÖR", "PER", "PSY", "VIL", "BIL", "SYN", "HÖR"]
        
        for attr in attribute_names:
            if method == "3d6":
                attributes[attr] = sum(random.randint(1, 6) for _ in range(3))
            elif method == "4d6":
                rolls = [random.randint(1, 6) for _ in range(4)]
                rolls.sort(reverse=True)
                attributes[attr] = sum(rolls[:3])  # Ta de 3 bästa
            elif method == "2d6+9":
                attributes[attr] = sum(random.randint(1, 6) for _ in range(2)) + 9
            else:
                raise ValueError(f"Okänd metod: {method}")
        
        return attributes
    
    def apply_racial_modifiers(self, attributes: Dict[str, int], race: str) -> Dict[str, int]:
        """
        Applicerar rasmodifikationer på attribut
        
        Args:
            attributes: Grundattribut
            race: Rasnamn (t.ex. "adasier", "cirefalier")
        
        Returns:
            Modifierade attribut
        """
        if 'attribute_modifiers' not in self.tables:
            print("Varning: Inga rasmodifikationer laddade")
            return attributes
        
        race_lower = race.lower()
        modifiers = self.tables['attribute_modifiers']
        
        # Hitta rätt rasmodifikationer
        race_mods = None
        for category, races in modifiers.items():
            if race_lower in races:
                race_mods = races[race_lower]
                break
        
        if not race_mods:
            print(f"Varning: Inga modifikationer hittades för ras: {race}")
            return attributes
        
        # Applicera modifikationer
        modified_attributes = attributes.copy()
        for attr, modifier in race_mods.items():
            if attr in modified_attributes:
                modified_attributes[attr] += modifier
                # Säkerställ att attribut inte går under 1
                modified_attributes[attr] = max(1, modified_attributes[attr])
        
        return modified_attributes
    
    def calculate_background_rolls(self, race: str, age: int, attribute_sum: int) -> int:
        """
        Beräknar antal slag på huvudbakgrundstabellen
        
        Args:
            race: Rasnamn
            age: Ålder
            attribute_sum: Summa av alla attribut
        
        Returns:
            Antal slag på huvudbakgrundstabellen
        """
        # Basantal slag beroende på ras
        base_rolls = {
            "människa_icke_cirefalier": 7,
            "människa_cirefalier": 6,
            "missla": 4,
            "dvärg": 5,
            "tirak": 5,
            "sanari": 5,
            "thism": 5,
            "kiriya": 5,
            "henea": 5,
            "learam": 5,
            "pyar": 5
        }
        
        # Försök matcha ras
        race_key = None
        race_lower = race.lower()
        
        if "cirefalier" in race_lower:
            race_key = "människa_cirefalier"
        elif "missla" in race_lower:
            race_key = "missla"
        elif any(dvärgras in race_lower for dvärgras in ["ghor", "roghan", "zolod", "drezin"]):
            race_key = "dvärg"
        elif any(tirakras in race_lower for tirakras in ["marnakh", "bazirk", "frakk", "gurd", "truhk"]):
            race_key = "tirak"
        elif race_lower in ["sanari", "thism", "kiriya", "henea", "learam", "pyar"]:
            race_key = race_lower
        else:
            race_key = "människa_icke_cirefalier"  # Default
        
        total_rolls = base_rolls.get(race_key, 7)
        
        # Modifikationer för låga attribut
        if attribute_sum < 70:
            total_rolls += 2
        elif 71 <= attribute_sum <= 85:
            total_rolls += 1
        
        # Åldersmodifikationer
        if 31 <= age <= 45:
            total_rolls += 1
        elif 46 <= age <= 60:
            total_rolls += 2
        elif 61 <= age <= 80:
            total_rolls += 3
        elif 81 <= age <= 100:
            total_rolls += 4
        elif age > 100:
            total_rolls += 5
        
        return total_rolls
    
    def roll_on_table(self, table_name: str, count: int = 1) -> List[Dict[str, Any]]:
        """
        Slår på en specifik tabell
        
        Args:
            table_name: Namnet på tabellen
            count: Antal slag
        
        Returns:
            Lista med resultat från tabellen
        """
        if table_name not in self.tables:
            return [{"error": f"Tabell '{table_name}' hittades inte"}]
        
        table = self.tables[table_name]
        if not table:
            return [{"error": f"Tabell '{table_name}' är tom"}]
        
        results = []
        for _ in range(count):
            # Slå 1d100 för de flesta tabeller
            roll = random.randint(1, 100)
            
            # Hitta rätt resultat baserat på intervall
            result = self.find_table_result(table, roll)
            if result:
                results.append({
                    "roll": roll,
                    "result": result,
                    "table": table_name
                })
            else:
                results.append({
                    "roll": roll,
                    "error": f"Inget resultat för slag {roll} i tabell {table_name}",
                    "table": table_name
                })
        
        return results
    
    def find_table_result(self, table: Dict, roll: int) -> Optional[str]:
        """
        Hittar rätt resultat i en tabell baserat på ett slag
        
        Args:
            table: Tabelldata
            roll: Tärningsslag (1-100)
        
        Returns:
            Resultattext eller None
        """
        # Hantera olika tabellformat
        if isinstance(table, dict):
            # Format 1: Direkta nycklar {"1": "resultat", "2-5": "annat resultat"}
            for key, value in table.items():
                if self.is_roll_in_range(roll, key):
                    return value
            
            # Format 2: Nested struktur med ranges
            if "ranges" in table:
                for range_data in table["ranges"]:
                    if self.is_roll_in_range(roll, range_data.get("range", "")):
                        return range_data.get("result", "")
        
        return None
    
    def is_roll_in_range(self, roll: int, range_str: str) -> bool:
        """
        Kontrollerar om ett slag faller inom ett specificerat intervall
        
        Args:
            roll: Tärningsslag
            range_str: Intervallsträng (t.ex. "1", "2-5", "95-100")
        
        Returns:
            True om slaget är inom intervallet
        """
        try:
            range_str = str(range_str).strip()
            
            if "-" in range_str:
                # Intervall som "2-5" eller "95-100"
                start, end = map(int, range_str.split("-"))
                return start <= roll <= end
            else:
                # Enskilt tal
                return roll == int(range_str)
        except (ValueError, AttributeError):
            return False
    
    def generate_complete_npc(self, race: str = None, age: int = None) -> Dict[str, Any]:
        """
        Genererar en komplett NPC med attribut, ras och bakgrund
        
        Args:
            race: Specifik ras (eller slumpas)
            age: Specifik ålder (eller slumpas)
        
        Returns:
            Komplett karaktärsdata
        """
        # Slumpa ras om inte angiven
        if not race:
            available_races = [
                "vanarer", "cirefalier", "adasier", "darkener", "lalaster",
                "learam", "sanari", "thism", "kiriya", "henea", "pyar",
                "ghor", "roghan", "zolod", "drezin", "marnakh", "bazirk", "frakk"
            ]
            race = random.choice(available_races)
        
        # Slumpa ålder om inte angiven
        if not age:
            age = random.randint(20, 60)
        
        # Generera grundattribut
        attributes = self.generate_attributes("3d6")
        
        # Applicera rasmodifikationer
        modified_attributes = self.apply_racial_modifiers(attributes, race)
        
        # Beräkna härledda värden
        attribute_sum = sum(modified_attributes.values())
        chock_value = (modified_attributes["STY"] + modified_attributes["TÅL"] + modified_attributes["VIL"]) // 3
        
        # Beräkna antal bakgrundslag
        background_rolls = self.calculate_background_rolls(race, age, attribute_sum)
        
        # Slå på huvudbakgrundstabellen
        background_results = []
        if 'background_tables' in self.tables and background_rolls > 0:
            background_results = self.roll_on_table('background_tables', background_rolls)
        
        return {
            "race": race,
            "age": age,
            "original_attributes": attributes,
            "final_attributes": modified_attributes,
            "attribute_sum": attribute_sum,
            "chock_value": chock_value,
            "background_rolls": background_rolls,
            "background_results": background_results
        }
    
    def format_character_display(self, character_data: Dict[str, Any]) -> str:
        """
        Formaterar karaktärsdata för visning i Discord
        
        Args:
            character_data: Data från generate_complete_npc
        
        Returns:
            Formaterad sträng för Discord-meddelande
        """
        lines = []
        lines.append(f"**Ras:** {character_data['race'].capitalize()}")
        lines.append(f"**Ålder:** {character_data['age']} år")
        lines.append("")
        
        # Attribut
        lines.append("**Attribut:**")
        for attr, value in character_data['final_attributes'].items():
            original = character_data['original_attributes'][attr]
            if value != original:
                lines.append(f"{attr}: {value} (ursprungligen {original})")
            else:
                lines.append(f"{attr}: {value}")
        
        lines.append(f"\n**Attributsumma:** {character_data['attribute_sum']}")
        lines.append(f"**Chockvärde:** {character_data['chock_value']}")
        lines.append(f"**Antal bakgrundslag:** {character_data['background_rolls']}")
        
        # Bakgrundsresultat
        if character_data['background_results']:
            lines.append("\n**Bakgrund:**")
            for i, result in enumerate(character_data['background_results'][:5], 1):
                if 'error' not in result:
                    lines.append(f"{i}. (Slag {result['roll']}) {result['result']}")
                else:
                    lines.append(f"{i}. {result['error']}")
            
            if len(character_data['background_results']) > 5:
                lines.append(f"... och {len(character_data['background_results']) - 5} till")
        
        return "\n".join(lines)

def register_commands(bot, roll_tracker, color_handler):
    """Registrerar rollpersonsskapande-kommandon till boten"""
    
    creator = CharacterCreator()
    
    @bot.command(name='attribut')
    async def attribut_command(ctx: commands.Context, method: str = "3d6"):
        """
        Genererar grundattribut för en rollperson.
        
        Metoder:
          3d6    - Standard 3T6 (9-18)
          4d6    - 4T6, ta bästa 3 (3-18, högre genomsnitt)
          2d6+9  - 2T6+9 (11-21, hög nivå)
        
        Exempel: !attribut 4d6
        """
        valid_methods = ["3d6", "4d6", "2d6+9"]
        
        if method not in valid_methods:
            await ctx.send(f"Ogiltigt metod. Använd: {', '.join(valid_methods)}")
            return
        
        try:
            attributes = creator.generate_attributes(method)
            attribute_sum = sum(attributes.values())
            
            color = color_handler.get_user_color(ctx.author.id)
            embed = discord.Embed(
                title=f"🎲 Grundattribut ({method})",
                description=f"Genererat av {ctx.author.display_name}",
                color=color
            )
            
            # Visa attribut i kolumner
            attr_text = "\n".join(f"**{attr}:** {value}" for attr, value in attributes.items())
            embed.add_field(name="Attribut", value=attr_text, inline=True)
            
            embed.add_field(name="Totalsumma", value=str(attribute_sum), inline=True)
            
            # Chockvärde
            chock = (attributes["STY"] + attributes["TÅL"] + attributes["VIL"]) // 3
            embed.add_field(name="Chockvärde", value=str(chock), inline=True)
            
            await ctx.send(embed=embed)
            
        except ValueError as e:
            await ctx.send(f"Fel: {str(e)}")
    
    @bot.command(name='folkslag')
    async def folkslag_command(ctx: commands.Context, action: str = "lista"):
        """
        Hanterar folkslag och rasmodifikationer.
        
        Användning:
          !folkslag lista     - Visa alla tillgängliga folkslag
          !folkslag slumpa    - Slumpa ett folkslag
          !folkslag [namn]    - Visa modifikationer för specifikt folkslag
        
        Exempel: !folkslag cirefalier
        """
        if action.lower() == "lista":
            # Lista alla tillgängliga folkslag
            if 'attribute_modifiers' not in creator.tables:
                await ctx.send("Inga folkslag laddade ännu.")
                return
            
            all_races = []
            for category, races in creator.tables['attribute_modifiers'].items():
                all_races.extend(races.keys())
            
            if not all_races:
                await ctx.send("Inga folkslag hittades i tabellerna.")
                return
            
            color = color_handler.get_user_color(ctx.author.id)
            embed = discord.Embed(
                title="🏛️ Tillgängliga Folkslag",
                description="Alla folkslag med attributmodifikationer",
                color=color
            )
            
            # Dela upp i kategorier
            for category, races in creator.tables['attribute_modifiers'].items():
                if races:
                    race_list = ", ".join(race.capitalize() for race in races.keys())
                    embed.add_field(
                        name=category.capitalize(),
                        value=race_list,
                        inline=False
                    )
            
            await ctx.send(embed=embed)
            
        elif action.lower() == "slumpa":
            # Slumpa ett folkslag
            all_races = []
            for category, races in creator.tables['attribute_modifiers'].items():
                all_races.extend(races.keys())
            
            if not all_races:
                await ctx.send("Inga folkslag att slumpa från.")
                return
            
            race = random.choice(all_races)
            await folkslag_command(ctx, race)  # Visa det slumpade folkslagets info
            
        else:
            # Visa info för specifikt folkslag
            race_lower = action.lower()
            found_race = None
            race_mods = None
            
            for category, races in creator.tables['attribute_modifiers'].items():
                if race_lower in races:
                    found_race = race_lower
                    race_mods = races[race_lower]
                    break
            
            if not found_race:
                await ctx.send(f"Folkslag '{action}' hittades inte. Använd `!folkslag lista` för att se alla.")
                return
            
            color = color_handler.get_user_color(ctx.author.id)
            embed = discord.Embed(
                title=f"🏛️ {found_race.capitalize()}",
                description="Attributmodifikationer",
                color=color
            )
            
            mod_text = "\n".join(
                f"**{attr}:** {'+' if mod >= 0 else ''}{mod}"
                for attr, mod in race_mods.items()
            )
            
            embed.add_field(name="Modifikationer", value=mod_text, inline=False)
            
            await ctx.send(embed=embed)
    
    @bot.command(name='egenskap')
    async def egenskap_command(ctx: commands.Context, typ: str = "fysisk", antal: int = 1):
        """
        Slår på egenskapstabeller.
        
        Typer:
          fysisk  - Fysiska egenskaper
          mental  - Mentala egenskaper  
          social  - Sociala egenskaper
          nackdel - Nackdelar
        
        Exempel: !egenskap mental 2
        """
        valid_types = {
            "fysisk": "physical_traits",
            "mental": "mental_traits", 
            "social": "social_traits",
            "nackdel": "disadvantages"
        }
        
        if typ.lower() not in valid_types:
            await ctx.send(f"Ogiltigt typ. Använd: {', '.join(valid_types.keys())}")
            return
        
        if antal < 1 or antal > 10:
            await ctx.send("Antal måste vara mellan 1 och 10.")
            return
        
        table_name = valid_types[typ.lower()]
        results = creator.roll_on_table(table_name, antal)
        
        color = color_handler.get_user_color(ctx.author.id)
        embed = discord.Embed(
            title=f"🎲 {typ.capitalize()} Egenskap{'er' if antal > 1 else ''}",
            description=f"Slaget av {ctx.author.display_name}",
            color=color
        )
        
        for i, result in enumerate(results, 1):
            if 'error' in result:
                embed.add_field(
                    name=f"Slag {i}",
                    value=result['error'],
                    inline=False
                )
            else:
                embed.add_field(
                    name=f"Slag {i} (Tärning: {result['roll']})",
                    value=result['result'],
                    inline=False
                )
        
        await ctx.send(embed=embed)
    
    @bot.command(name='npc')
    async def npc_command(ctx: commands.Context, folkslag: str = None, ålder: int = None):
        """
        Genererar en komplett NPC med attribut och bakgrund.
        
        Båda parametrarna är valfria - slumpas om de inte anges.
        
        Exempel: 
          !npc                    - Helt slumpad NPC
          !npc cirefalier         - Cirefalier med slumpad ålder
          !npc vanarer 35         - 35-årig vanare
        """
        try:
            # Validera ålder om angiven
            if ålder is not None and (ålder < 1 or ålder > 200):
                await ctx.send("Ålder måste vara mellan 1 och 200 år.")
                return
            
            # Generera NPC
            character = creator.generate_complete_npc(folkslag, ålder)
            
            # Formatera för visning
            char_text = creator.format_character_display(character)
            
            color = color_handler.get_user_color(ctx.author.id)
            embed = discord.Embed(
                title="🧙‍♂️ Genererad NPC",
                description=char_text,
                color=color
            )
            
            embed.set_footer(text=f"Genererad av {ctx.author.display_name}")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            await ctx.send(f"Ett fel uppstod vid generering av NPC: {str(e)}")
    
    @bot.command(name='bakgrund')
    async def bakgrund_command(ctx: commands.Context, antal: int = 1):
        """
        Slår på huvudbakgrundstabellen.
        
        Exempel: !bakgrund 3
        """
        if antal < 1 or antal > 20:
            await ctx.send("Antal måste vara mellan 1 och 20.")
            return
        
        results = creator.roll_on_table('background_tables', antal)
        
        color = color_handler.get_user_color(ctx.author.id)
        embed = discord.Embed(
            title=f"🎲 Huvudbakgrundstabellen ({antal} slag)",
            description=f"Slaget av {ctx.author.display_name}",
            color=color
        )
        
        for i, result in enumerate(results, 1):
            if 'error' in result:
                embed.add_field(
                    name=f"Slag {i}",
                    value=result['error'],
                    inline=False
                )
            else:
                embed.add_field(
                    name=f"Slag {i} (Tärning: {result['roll']})",
                    value=result['result'],
                    inline=False
                )
        
        await ctx.send(embed=embed)
    
    print("Rollpersonsskapande-kommandon har registrerats (attribut, folkslag, egenskap, npc, bakgrund).")