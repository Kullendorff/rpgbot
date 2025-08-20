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
from automatic_background import AutomaticBackgroundGenerator
from interactive_chargen import InteractiveCharacterCreator

class CharacterCreator:
    """Huvudklass för rollpersonsskapande funktionalitet"""

    def __init__(self, data_dir: str = None):
        if data_dir is None:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(script_dir)
            self.data_dir = os.path.join(project_root, 'data', 'character_tables')
        else:
            self.data_dir = data_dir
        os.makedirs(self.data_dir, exist_ok=True)
        self.tables = self.load_tables()

    def load_tables(self) -> Dict[str, Any]:
        """Laddar alla tabeller från JSON-filer"""
        tables = {}
        table_files = [
            'attribute_modifiers.json', 'background_tables.json', 'physical_traits.json',
            'mental_traits.json', 'social_traits.json', 'disadvantages.json',
            'birth_tables.json', 'property_tables.json', 'events_tables.json'
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
                    tables[filename.replace('.json', '')] = {}
            except Exception as e:
                print(f"Fel vid laddning av {filename}: {e}")
                tables[filename.replace('.json', '')] = {}
        return tables

    def roll_on_table(self, table_name: str, count: int = 1) -> List[Dict[str, Any]]:
        """
        Slår på en specifik tabell och hanterar resultat som ger extra slag.
        Visar även resultatet som ledde till omslaget.
        """
        if table_name not in self.tables:
            return [{"error": f"Tabell '{table_name}' hittades inte"}]
        table = self.tables[table_name]
        if not table:
            return [{"error": f"Tabell '{table_name}' är tom"}]

        all_results = []
        rolls_to_process = list(range(count))
        max_rolls = 50

        while rolls_to_process and len(all_results) < max_rolls:
            rolls_to_process.pop(0)

            roll = random.randint(1, 100)
            result_text = self.find_table_result(table, roll)
            
            current_result = {
                "roll": roll,
                "result": result_text or f"Inget resultat för slag {roll}",
                "table": table_name,
                "is_reroll_trigger": False
            }

            if result_text:
                # FIX: Letar nu efter en mer specifik fras för att vara säker.
                reroll_phrase = "slå två gånger till"
                if reroll_phrase in result_text.lower():
                    current_result["is_reroll_trigger"] = True
                    rolls_to_process.insert(0, 1)
                    rolls_to_process.insert(0, 1)
            
            all_results.append(current_result)
        
        if len(all_results) >= max_rolls:
            print(f"Varning: Nådde maxgränsen på {max_rolls} slag för tabell '{table_name}'.")

        return all_results

    def generate_attributes(self, method: str = "3d6") -> Dict[str, int]:
        attributes = {}
        attribute_names = ["STY", "TÅL", "RÖR", "PER", "PSY", "VIL", "BIL", "SYN", "HÖR"]
        for attr in attribute_names:
            if method == "3d6": attributes[attr] = sum(random.randint(1, 6) for _ in range(3))
            elif method == "4d6": rolls = sorted([random.randint(1, 6) for _ in range(4)], reverse=True); attributes[attr] = sum(rolls[:3])
            elif method == "2d6+9": attributes[attr] = sum(random.randint(1, 6) for _ in range(2)) + 9
            else: raise ValueError(f"Okänd metod: {method}")
        return attributes

    def apply_racial_modifiers(self, attributes: Dict[str, int], race: str) -> Dict[str, int]:
        if 'attribute_modifiers' not in self.tables: return attributes
        race_lower = race.lower()
        modifiers = self.tables['attribute_modifiers']
        race_mods = None
        for category, races in modifiers.items():
            if race_lower in races:
                race_mods = races[race_lower]
                break
        if not race_mods: return attributes
        modified_attributes = attributes.copy()
        for attr, modifier in race_mods.items():
            if attr in modified_attributes:
                modified_attributes[attr] += modifier
                modified_attributes[attr] = max(1, modified_attributes[attr])
        return modified_attributes
        
    def calculate_background_rolls(self, race: str, age: int, attribute_sum: int) -> int:
        base_rolls = {"människa_icke_cirefalier": 7, "människa_cirefalier": 6, "missla": 4, "dvärg": 5, "tirak": 5, "sanari": 5, "thism": 5, "kiriya": 5, "henea": 5, "learam": 5, "pyar": 5}
        race_key = "människa_icke_cirefalier"
        race_lower = race.lower()
        if "cirefalier" in race_lower: race_key = "människa_cirefalier"
        elif "missla" in race_lower: race_key = "missla"
        elif any(r in race_lower for r in ["ghor", "roghan", "zolod", "drezin"]): race_key = "dvärg"
        elif any(r in race_lower for r in ["marnakh", "bazirk", "frakk", "gurd", "truhk"]): race_key = "tirak"
        elif race_lower in base_rolls: race_key = race_lower
        total_rolls = base_rolls.get(race_key, 7)
        if attribute_sum < 70: total_rolls += 2
        elif 71 <= attribute_sum <= 85: total_rolls += 1
        if 31 <= age <= 45: total_rolls += 1
        elif 46 <= age <= 60: total_rolls += 2
        elif 61 <= age <= 80: total_rolls += 3
        elif 81 <= age <= 100: total_rolls += 4
        elif age > 100: total_rolls += 5
        return total_rolls

    def find_table_result(self, table: Dict, roll: int) -> Optional[str]:
        if isinstance(table, dict):
            for key, value in table.items():
                if self.is_roll_in_range(roll, key): return value
            if "ranges" in table:
                for r in table["ranges"]:
                    if self.is_roll_in_range(roll, r.get("range", "")): return r.get("result", "")
        return None

    def is_roll_in_range(self, roll: int, range_str: str) -> bool:
        try:
            range_str = str(range_str).strip()
            if "-" in range_str: start, end = map(int, range_str.split("-")); return start <= roll <= end
            else: return roll == int(range_str)
        except (ValueError, AttributeError): return False

    def generate_complete_npc(self, race: str = None, age: int = None) -> Dict[str, Any]:
        if not race: race = random.choice(["vanarer", "cirefalier", "adasier", "darkener", "lalaster", "learam", "sanari", "thism", "kiriya", "henea", "pyar", "ghor", "roghan", "zolod", "drezin", "marnakh", "bazirk", "frakk"])
        if not age: age = random.randint(20, 60)
        attributes = self.generate_attributes("3d6")
        modified_attributes = self.apply_racial_modifiers(attributes, race)
        attribute_sum = sum(modified_attributes.values())
        chock_value = (modified_attributes["STY"] + modified_attributes["TÅL"] + modified_attributes["VIL"]) // 3
        background_rolls = self.calculate_background_rolls(race, age, attribute_sum)
        background_results = []
        if 'background_tables' in self.tables and background_rolls > 0:
            background_results = self.roll_on_table('background_tables', background_rolls)
        return {"race": race, "age": age, "original_attributes": attributes, "final_attributes": modified_attributes, "attribute_sum": attribute_sum, "chock_value": chock_value, "background_rolls": background_rolls, "background_results": background_results}
    
    def format_character_display(self, character_data: Dict[str, Any]) -> str:
        lines = [f"**Ras:** {character_data['race'].capitalize()}", f"**Ålder:** {character_data['age']} år", "", "**Attribut:**"]
        for attr, value in character_data['final_attributes'].items():
            original = character_data['original_attributes'][attr]
            lines.append(f"{attr}: {value}" + (f" (ursprungligen {original})" if value != original else ""))
        lines.extend([f"\n**Attributsumma:** {character_data['attribute_sum']}", f"**Chockvärde:** {character_data['chock_value']}", f"**Antal bakgrundslag:** {character_data['background_rolls']}"])
        if character_data['background_results']:
            lines.append("\n**Bakgrund:**")
            final_results = [res for res in character_data['background_results'] if not res.get('is_reroll_trigger')]
            for i, result in enumerate(final_results[:5], 1):
                 lines.append(f"{i}. (Slag {result['roll']}) {result['result']}")
            if len(final_results) > 5:
                lines.append(f"... och {len(final_results) - 5} till")
        return "\n".join(lines)


def register_commands(bot, roll_tracker, color_handler, embed_factory):
    """Registrerar rollpersonsskapande-kommandon till boten"""
    
    creator = CharacterCreator()
    bg_generator = AutomaticBackgroundGenerator()
    chargen = InteractiveCharacterCreator(embed_factory)
    
    @bot.command(name='attribut')
    async def attribut_command(ctx: commands.Context, method: str = "3d6"):
        valid_methods = ["3d6", "4d6", "2d6+9"]
        if method not in valid_methods:
            await ctx.send(f"Ogiltigt metod. Använd: {', '.join(valid_methods)}")
            return
        try:
            attributes = creator.generate_attributes(method)
            attribute_sum = sum(attributes.values())
            color = color_handler.get_user_color(ctx.author.id)
            embed = embed_factory.dice_result(
                ctx.author.id,
                ctx.author.display_name,
                "attribut",
                f"Grundattribut ({method})",
                list(attributes.values()),
                attribute_sum,
                None,
                None
            )
            attr_text = "\n".join(f"**{attr}:** {value}" for attr, value in attributes.items())
            embed.add_field(name="Attribut", value=attr_text, inline=True)
            embed.add_field(name="Totalsumma", value=str(attribute_sum), inline=True)
            chock = (attributes["STY"] + attributes["TÅL"] + attributes["VIL"]) // 3
            embed.add_field(name="Chockvärde", value=str(chock), inline=True)
            await ctx.send(embed=embed)
        except ValueError as e:
            await ctx.send(f"Fel: {str(e)}")
    
    @bot.command(name='folkslag')
    async def folkslag_command(ctx: commands.Context, action: str = "lista"):
        if 'attribute_modifiers' not in creator.tables:
            await ctx.send("Inga folkslag laddade ännu.")
            return
        all_races = [race for cat_races in creator.tables['attribute_modifiers'].values() for race in cat_races.keys()]
        if not all_races:
            await ctx.send("Inga folkslag hittades i tabellerna.")
            return
        
        action_lower = action.lower()
        if action_lower == "lista":
            color = color_handler.get_user_color(ctx.author.id)
            embed = embed_factory.admin_message(ctx.author.id, "Tillgängliga Folkslag", "Alla folkslag med attributmodifikationer")
            for category, races in creator.tables['attribute_modifiers'].items():
                if races:
                    race_list = ", ".join(race.capitalize() for race in races.keys())
                    embed.add_field(name=category.capitalize(), value=race_list, inline=False)
            await ctx.send(embed=embed)
        elif action_lower == "slumpa":
            race = random.choice(all_races)
            await folkslag_command.callback(ctx, bot, roll_tracker, color_handler, action=race)
        else:
            race_lower = action.lower()
            race_mods = None
            for category, races in creator.tables['attribute_modifiers'].items():
                if race_lower in races:
                    race_mods = races[race_lower]
                    break
            if not race_mods:
                await ctx.send(f"Folkslag '{action}' hittades inte. Använd `!folkslag lista` för att se alla.")
                return
            color = color_handler.get_user_color(ctx.author.id)
            embed = embed_factory.admin_message(ctx.author.id, f"{race_lower.capitalize()}", "Attributmodifikationer")
            mod_text = "\n".join(f"**{attr}:** {'+' if mod >= 0 else ''}{mod}" for attr, mod in race_mods.items())
            embed.add_field(name="Modifikationer", value=mod_text, inline=False)
            await ctx.send(embed=embed)
    
    @bot.command(name='egenskap')
    async def egenskap_command(ctx: commands.Context, typ: str = "fysisk", antal: int = 1):
        """
        Slår på egenskapstabeller och visar hela händelseförloppet vid omslag.
        """
        valid_types = { "fysisk": "physical_traits", "mental": "mental_traits", "social": "social_traits", "nackdel": "disadvantages" }
        typ_lower = typ.lower()
        if typ_lower not in valid_types:
            await ctx.send(f"Ogiltig typ. Använd: {', '.join(valid_types.keys())}")
            return
        
        if antal < 1 or antal > 10:
            await ctx.send("Antal måste vara mellan 1 och 10.")
            return
        
        table_name = valid_types[typ_lower]
        results = creator.roll_on_table(table_name, antal)
        
        color = color_handler.get_user_color(ctx.author.id)
        embed = embed_factory.dice_result(ctx.author.id, ctx.author.display_name, "egenskap", f"{typ.capitalize()} Egenskap{'er' if antal > 1 else ''}", [], None, None, None)
        
        # FIX: Uppdaterad logik för att visa resultaten korrekt
        for result in results:
            field_name = f"Slag (Tärning: {result['roll']})"
            field_value = result['result']
            
            if result.get('is_reroll_trigger'):
                # Detta var ett slag som ledde till omslag
                field_name += " ➔ Omslag!"
                field_value = f"*{field_value}*" # Kursiv för att visa att det är en instruktion
                embed.add_field(name=field_name, value=field_value, inline=False)
            else:
                # Detta är en faktisk egenskap
                embed.add_field(name=field_name, value=field_value, inline=False)
        
        await ctx.send(embed=embed)

    @bot.command(name='npc')
    async def npc_command(ctx: commands.Context, folkslag: str = None, ålder: int = None):
        try:
            if ålder is not None and (ålder < 1 or ålder > 200):
                await ctx.send("Ålder måste vara mellan 1 och 200 år.")
                return
            character = creator.generate_complete_npc(folkslag, ålder)
            char_text = creator.format_character_display(character)
            color = color_handler.get_user_color(ctx.author.id)
            embed = embed_factory.admin_message(ctx.author.id, "Genererad NPC", char_text)
            embed.set_footer(text=f"Genererad av {ctx.author.display_name}")
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"Ett fel uppstod vid generering av NPC: {str(e)}")
    
    @bot.command(name='bakgrund')
    async def bakgrund_command(ctx: commands.Context, antal: int = 1):
        if antal < 1 or antal > 20:
            await ctx.send("Antal måste vara mellan 1 och 20.")
            return
        results = creator.roll_on_table('background_tables', antal)
        color = color_handler.get_user_color(ctx.author.id)
        embed = embed_factory.dice_result(ctx.author.id, ctx.author.display_name, "bakgrund", f"Huvudbakgrundstabellen ({antal} slag)", [], None, None, None)
        
        for i, result in enumerate(results, 1):
            if 'error' in result:
                embed.add_field(name=f"Slag {i}", value=result['error'], inline=False)
            else:
                # Samma logik som i !egenskap för att visa omslag
                field_name = f"Slag {i} (Tärning: {result['roll']})"
                field_value = result['result']
                if result.get('is_reroll_trigger'):
                    field_name += " ➔ Omslag!"
                    field_value = f"*{field_value}*"
                embed.add_field(name=field_name, value=field_value, inline=False)
        
        await ctx.send(embed=embed)
    
    @bot.command(name='familjebakgrund')
    async def familjebakgrund_command(ctx: commands.Context, folkslag: str, ålder: int):
        """Genererar automatiskt komplett familjebakgrund för en rollperson"""
        if ålder < 1 or ålder > 200:
            await ctx.send("Ålder måste vara mellan 1 och 200 år.")
            return
        
        try:
            # Generera bakgrund
            background = bg_generator.generate_complete_background(folkslag, ålder)
            summary = bg_generator.format_background_summary(background)
            
            color = color_handler.get_user_color(ctx.author.id)
            embed = embed_factory.admin_message(
                ctx.author.id,
                f"Familjebakgrund - {folkslag.capitalize()}, {ålder} år",
                summary
            )
            embed.set_footer(text=f"Genererad av {ctx.author.display_name}")
            
            await ctx.send(embed=embed)
                
        except Exception as e:
            await ctx.send(f"Ett fel uppstod vid generering av familjebakgrund: {str(e)}")
            print(f"Familjebakgrund fel: {e}")  # För debugging
    
    @bot.command(name='chargen')
    async def chargen_command(ctx: commands.Context, action: str = None, *args):
        """Huvudkommando för interaktivt karaktärsskapande"""
        
        if action == "start":
            # Starta ny session
            session = chargen.start_session(str(ctx.author.id))
            await chargen.show_current_step(ctx, session)
        
        elif action == "status":
            # Visa nuvarande progress
            session = chargen.get_session(str(ctx.author.id))
            if session:
                await chargen.show_status(ctx, session)
            else:
                await ctx.send("Du har ingen aktiv karaktärsskapande-session. Använd `!chargen start`")
        
        elif action == "step":
            # Gå till nästa steg
            session = chargen.get_session(str(ctx.author.id))
            if session:
                if chargen.next_step(session):
                    await chargen.show_current_step(ctx, session)
                else:
                    await ctx.send("Du har redan nått det sista steget!")
            else:
                await ctx.send("Ingen aktiv session. Använd `!chargen start`")
        
        elif action == "back":
            # Gå tillbaka ett steg
            session = chargen.get_session(str(ctx.author.id))
            if session:
                if chargen.previous_step(session):
                    await chargen.show_current_step(ctx, session)
                else:
                    await ctx.send("Du är redan på det första steget!")
            else:
                await ctx.send("Ingen aktiv session. Använd `!chargen start`")
        
        elif action == "abort":
            # Avbryt session
            if chargen.end_session(str(ctx.author.id)):
                await ctx.send("✅ Karaktärsskapande avbrutet.")
            else:
                await ctx.send("Du har ingen aktiv session att avbryta.")
        
        elif action in ["fortsätt", "behåll"]:
            # Bekräfta temporär data (generell logik)
            session = chargen.get_session(str(ctx.author.id))
            if session:
                step_info = chargen.get_current_step_info(session)
                
                # För bakgrundshändelser - använd alltid step-specific hantering 
                if step_info and step_info['name'] == 'bakgrundshändelser':
                    await chargen.handle_step_input(ctx, session, action, *args)
                elif session.temp_data:
                    await chargen.confirm_current_choice(ctx, session)
                else:
                    # Om ingen temporär data, kolla om steget har specifik hantering
                    if step_info and hasattr(chargen, f"handle_{step_info['name']}_input"):
                        await chargen.handle_step_input(ctx, session, action, *args)
                    else:
                        await ctx.send("Ingen temporär data att bekräfta.")
            else:
                await ctx.send("Ingen aktiv session. Använd `!chargen start` för att börja skapa en rollperson.")
        
        elif action == "ändra":
            # Rensa temporär data och visa steget igen
            session = chargen.get_session(str(ctx.author.id))
            if session and session.temp_data:
                session.temp_data.clear()
                chargen.save_session(session)
                await ctx.send("🔄 Data rensad. Genererar nytt...")
                await chargen.show_current_step(ctx, session)
            else:
                await ctx.send("Ingen temporär data att ändra.")
        
        elif action == "help":
            # Visa hjälp
            embed = embed_factory.admin_message(
                ctx.author.id,
                "Chargen - Interaktivt Karaktärsskapande",
                "Kommandon för 33-stegs EON karaktärsskapande"
            )
            embed.add_field(
                name="📋 Grundkommandon",
                value="`!chargen start` - Starta ny rollperson\n"
                      "`!chargen status` - Visa progress\n"
                      "`!chargen step` - Nästa steg\n"
                      "`!chargen back` - Föregående steg\n"
                      "`!chargen abort` - Avbryt session",
                inline=False
            )
            embed.add_field(
                name="✅ Bekräftelse",
                value="`!chargen fortsätt` - Bekräfta val\n"
                      "`!chargen ändra` - Generera nytt",
                inline=False
            )
            embed.add_field(
                name="📝 Input",
                value="I de flesta steg skriver du bara: `!chargen [ditt val]`\n"
                      "Exempel: `!chargen kvinna`, `!chargen vanarer`, `!chargen 25`",
                inline=False
            )
            await ctx.send(embed=embed)
        
        elif action is None:
            # Visa huvudmeny
            embed = embed_factory.success_message(
                ctx.author.id,
                "EON Diceroller - Karaktärsskapande\n\nVälkommen till det interaktiva karaktärsskapande-systemet!"
            )
            embed.add_field(
                name="🚀 Kom igång",
                value="`!chargen start` - Starta 33-stegs karaktärsskapande\n"
                      "`!chargen help` - Visa alla kommandon",
                inline=False
            )
            embed.add_field(
                name="🔧 Snabbkommandon",
                value="`!attribut` - Generera attribut\n"
                      "`!folkslag` - Lista folkslag\n"
                      "`!familjebakgrund [folkslag] [ålder]` - Snabb familjebakgrund",
                inline=False
            )
            
            # Visa aktiv session om den finns
            session = chargen.get_session(str(ctx.author.id))
            if session:
                step_info = chargen.get_current_step_info(session)
                embed.add_field(
                    name="📊 Din aktiva session",
                    value=f"Steg {session.current_step}/33: {step_info['title'] if step_info else 'Okänt'}\n"
                          "`!chargen status` för detaljer",
                    inline=False
                )
            
            await ctx.send(embed=embed)
        
        else:
            # Tolka som input för nuvarande steg
            session = chargen.get_session(str(ctx.author.id))
            if session:
                await chargen.handle_step_input(ctx, session, action, *args)
            else:
                await ctx.send("Ingen aktiv session. Använd `!chargen start` för att börja skapa en rollperson.")

    print("Rollpersonsskapande-kommandon har registrerats (attribut, folkslag, egenskap, npc, bakgrund, familjebakgrund, chargen).")