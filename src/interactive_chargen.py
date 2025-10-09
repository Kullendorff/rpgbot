"""
Interaktivt karaktärsskapande-system för EON Diceroller Bot
Implementerar en komplett 33-stegs karaktärsskapande-process med session management
"""

import json
import os
import discord
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from pathlib import Path

# Import av befintliga system
from eon_table_processor import TableProcessor, CharacterContext, create_character_context
from automatic_background import AutomaticBackgroundGenerator
import random

# Import CharacterSession från nya platsen
from character_creation.session import CharacterSession

# Import av nya step-moduler
from character_creation.steps.gender import GenderStep
from character_creation.steps.age import AgeStep
from character_creation.steps.homeland import HomelandStep
from character_creation.steps.race import RaceStep
from character_creation.steps.culture import CultureStep
from character_creation.steps.attributes import AttributesStep
from character_creation.steps.special_rules import SpecialRulesStep
from character_creation.steps.traits import TraitsStep
from character_creation.steps.family import FamilyStep
from character_creation.steps.background import BackgroundStep
from character_creation.steps.summary import SummaryStep

class InteractiveCharacterCreator:
    """Huvudklass för interaktivt karaktärsskapande med full EON TableProcessor integration"""
    
    def __init__(self, embed_factory, data_dir: str = None):
        self.active_sessions: Dict[str, CharacterSession] = {}
        self.embed_factory = embed_factory
        
        # Integration med befintliga system
        self.table_processor = TableProcessor(data_dir)
        self.bg_generator = AutomaticBackgroundGenerator()
        
        # Sätt upp data directory för session persistens
        if data_dir is None:
            script_dir = Path(__file__).parent
            project_root = script_dir.parent
            self.session_dir = project_root / 'data' / 'character_tables' / 'sessions'
            self.data_dir = project_root / 'data' / 'character_tables'
        else:
            self.session_dir = Path(data_dir) / 'sessions'
            self.data_dir = Path(data_dir)
        
        self.session_dir.mkdir(parents=True, exist_ok=True)
        
        # Ladda hemländer, folkslag och kulturer separat
        self.homelands = self.load_homelands()
        self.folkslag_data = self.load_folkslag()
        self.culture_data = self.load_culture_data()
        self.thalamur_atter_data = None  # Laddas vid behov
        self.thalask_family_data = None  # Laddas vid behov
        
        # Initiera step-moduler
        self.gender_step = GenderStep(self.embed_factory)
        self.age_step = AgeStep(self.embed_factory)
        self.homeland_step = HomelandStep(self.embed_factory, self.data_dir)
        self.race_step = RaceStep(self.embed_factory, self.data_dir)
        self.culture_step = CultureStep(self.embed_factory, self.data_dir)
        self.attributes_step = AttributesStep(self.embed_factory, self.data_dir)
        self.special_rules_step = SpecialRulesStep(self.embed_factory, self.data_dir)
        self.traits_step = TraitsStep(self.embed_factory, self.data_dir)
        self.family_step = FamilyStep(self.embed_factory, self.data_dir, self.bg_generator, self.table_processor)
        self.background_step = BackgroundStep(self.embed_factory, self.data_dir, self.table_processor)
        self.summary_step = SummaryStep(self.embed_factory, self.data_dir)
        
        # Definiera alla 33 steg
        self.steps = self._define_steps()
        
        # Ladda befintliga sessioner vid start
        self._load_existing_sessions()
    
    def load_homelands(self) -> List[Dict[str, str]]:
        """Laddar alla länder från landerhemort/ mappen"""
        homelands = []
        
        # Sätt korrekt data_dir om inte redan satt
        if not hasattr(self, 'data_dir'):
            script_dir = Path(__file__).parent
            project_root = script_dir.parent
            self.data_dir = project_root / 'data' / 'character_tables'
        
        homeland_dir = self.data_dir / 'landerhemort'
        
        if not homeland_dir.exists():
            print(f"Varning: Kan inte hitta {homeland_dir}")
            return []
        
        # Läs alla .txt filer i landerhemort/
        for txt_file in sorted(homeland_dir.glob("*.txt")):
            try:
                with open(txt_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    
                land_name = txt_file.stem  # Filnamn utan .txt
                
                # Extrahera första raden som titel (om möjligt)
                lines = content.split('\n')
                title = lines[0] if lines else land_name
                
                homelands.append({
                    'name': land_name,
                    'title': title,
                    'description': content
                })
                
            except Exception as e:
                print(f"Fel vid laddning av {txt_file}: {e}")
        
        print(f"Laddade {len(homelands)} hemländer")
        return homelands
    
    def load_folkslag(self) -> Dict[str, List[Dict[str, str]]]:
        """Laddar alla folkslag från folkslag/ undermappar"""
        folkslag_data = {}
        
        # Sätt korrekt data_dir om inte redan satt
        if not hasattr(self, 'data_dir'):
            script_dir = Path(__file__).parent
            project_root = script_dir.parent
            self.data_dir = project_root / 'data' / 'character_tables'
        
        folkslag_dir = self.data_dir / 'folkslag'
        
        if not folkslag_dir.exists():
            print(f"Varning: Kan inte hitta {folkslag_dir}")
            return {}
        
        # Gå igenom alla undermappar (humans/, alver/, dvärgar/)
        for subfolder in folkslag_dir.iterdir():
            if subfolder.is_dir() and subfolder.name != '__pycache__':
                category_name = subfolder.name
                folkslag_data[category_name] = []
                
                # Läs alla .txt filer i undermappen
                for txt_file in sorted(subfolder.glob("*.txt")):
                    try:
                        with open(txt_file, 'r', encoding='utf-8') as f:
                            content = f.read().strip()
                        
                        folkslag_name = txt_file.stem
                        
                        # Extrahera första raden som titel
                        lines = content.split('\n')
                        title = lines[0] if lines else folkslag_name
                        
                        folkslag_data[category_name].append({
                            'name': folkslag_name,
                            'title': title,
                            'description': content,
                            'category': category_name
                        })
                        
                    except Exception as e:
                        print(f"Fel vid laddning av {txt_file}: {e}")
        
        total_folkslag = sum(len(races) for races in folkslag_data.values())
        print(f"Laddade {total_folkslag} folkslag i {len(folkslag_data)} kategorier")
        return folkslag_data
    
    def load_culture_data(self) -> Dict[str, Any]:
        """Laddar kulturdata från huvudnaring.json"""
        culture_data = {}
        
        # Sätt korrekt data_dir om inte redan satt
        if not hasattr(self, 'data_dir'):
            script_dir = Path(__file__).parent
            project_root = script_dir.parent
            self.data_dir = project_root / 'data' / 'character_tables'
        
        huvudnaring_file = self.data_dir / 'familj' / 'huvudnaring.json'
        
        if not huvudnaring_file.exists():
            print(f"Varning: Kan inte hitta {huvudnaring_file}")
            return {}
        
        try:
            with open(huvudnaring_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Extrahera kulturkategorierna från huvudnäring
            if 'familj_huvudnäring' in data:
                culture_data = data['familj_huvudnäring']
                print(f"Laddade {len(culture_data)} kulturkategorier från huvudnaring.json")
            else:
                print("Varning: Kunde inte hitta 'familj_huvudnäring' i huvudnaring.json")
                
        except Exception as e:
            print(f"Fel vid laddning av {huvudnaring_file}: {e}")
        
        return culture_data
    
    
    def _define_steps(self) -> List[Dict[str, Any]]:
        """Definierar alla 32 steg i EON karaktärsskapande-processen (Religion hoppas över)"""
        return [
            {"id": 1, "name": "kön", "title": "Kön", "handler": self.step_gender},
            {"id": 2, "name": "hemland", "title": "Hemland", "handler": self.step_homeland},
            {"id": 3, "name": "folkslag", "title": "Folkslag", "handler": self.step_race},
            {"id": 4, "name": "ålder", "title": "Ålder", "handler": self.step_age},
            {"id": 5, "name": "kultur", "title": "Kultur", "handler": self.step_culture},
            {"id": 6, "name": "attribut", "title": "Grundattribut", "handler": self.step_attributes},
            {"id": 7, "name": "specialregler", "title": "Specialregler", "handler": self.step_special_rules},
            {"id": 8, "name": "karaktärsdrag", "title": "Karaktärsdrag", "handler": self.step_character_traits},
            
            # FAMILJ KOMMER FÖRE BAKGRUNDSLAG I EON
            {"id": 9, "name": "familjebakgrund", "title": "Familjebakgrund", "handler": self.step_family_background},
            {"id": 10, "name": "familjetabeller", "title": "Familjetabeller", "handler": self.step_family_tables},
            {"id": 11, "name": "föräldrar", "title": "Föräldrar", "handler": self.step_parents},
            
            # BAKGRUNDSLAG EFTER FAMILJ
            {"id": 12, "name": "bakgrundslag_antal", "title": "Antal bakgrundslag", "handler": self.step_background_count},
            {"id": 13, "name": "huvudbakgrund", "title": "Huvudbakgrundstabellen", "handler": self.step_main_background},
            {"id": 14, "name": "bakgrundshändelser", "title": "Bakgrundshändelser", "handler": self.step_background_events},
            
            # Resterande steg (kommer senare)
            {"id": 15, "name": "sammanfattning", "title": "Karaktärssammanfattning", "handler": self.step_final_summary},
            # Steg 16-32 hanteras manuellt
        ]
    
    def _load_existing_sessions(self):
        """Laddar befintliga sessioner från disk vid start"""
        try:
            for session_file in self.session_dir.glob("*.json"):
                user_id = session_file.stem
                session = self.load_session(user_id)
                if session:
                    self.active_sessions[user_id] = session
        except Exception as e:
            print(f"Fel vid laddning av befintliga sessioner: {e}")
    
    def start_session(self, user_id: str) -> CharacterSession:
        """Startar en ny karaktärsskapande-session för användare"""
        # Avsluta befintlig session om den finns
        if user_id in self.active_sessions:
            self.end_session(user_id)
        
        session = CharacterSession(user_id=user_id)
        self.active_sessions[user_id] = session
        self.save_session(session)
        return session
    
    def get_session(self, user_id: str) -> Optional[CharacterSession]:
        """Hämtar aktiv session för användare"""
        return self.active_sessions.get(user_id)
    
    def end_session(self, user_id: str) -> bool:
        """Avslutar session för användare"""
        if user_id in self.active_sessions:
            del self.active_sessions[user_id]
            
            # Ta bort session-fil
            session_file = self.session_dir / f"{user_id}.json"
            if session_file.exists():
                session_file.unlink()
            return True
        return False
    
    def save_session(self, session: CharacterSession):
        """Sparar session till JSON-fil"""
        try:
            session_file = self.session_dir / f"{session.user_id}.json"
            session_dict = session.to_dict()
            
            # Debug what we're saving
            print(f"DEBUG - Saving session for {session.user_id}: step={session.current_step}")
            print(f"DEBUG - Data keys: {list(session.data.keys())}")
            if 'folkslag' in session.data:
                print(f"DEBUG - Saving folkslag: '{session.data['folkslag']}'")
                
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(session_dict, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Fel vid sparning av session för {session.user_id}: {e}")
    
    def load_session(self, user_id: str) -> Optional[CharacterSession]:
        """Laddar sparad session från fil"""
        try:
            session_file = self.session_dir / f"{user_id}.json"
            if not session_file.exists():
                return None
            
            with open(session_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            session = CharacterSession.from_dict(data)
            print(f"DEBUG - Loaded session for {user_id}: step={session.current_step}, folkslag in data={('folkslag' in session.data)}")
            if 'folkslag' in session.data:
                print(f"DEBUG - Folkslag value: '{session.data['folkslag']}'")
            return session
        except Exception as e:
            print(f"Fel vid laddning av session för {user_id}: {e}")
            return None
    
    def get_current_step_info(self, session: CharacterSession) -> Dict[str, Any]:
        """Hämtar information om nuvarande steg"""
        if 1 <= session.current_step <= len(self.steps):
            return self.steps[session.current_step - 1]
        return None
    
    def next_step(self, session: CharacterSession) -> bool:
        """Går till nästa steg om möjligt"""
        if session.current_step < session.max_steps:
            session.current_step += 1
            self.save_session(session)
            return True
        return False
    
    def previous_step(self, session: CharacterSession) -> bool:
        """Går tillbaka ett steg om möjligt"""
        if session.current_step > 1:
            session.current_step -= 1
            self.save_session(session)
            return True
        return False
    
    async def show_current_step(self, ctx, session: CharacterSession):
        """Visar nuvarande steg för användaren"""
        # Kontrollera om Thalamur citizenship-steg ska köras först
        if session.data.get('thalamur_citizenship_pending'):
            session.data.pop('thalamur_citizenship_pending', None)
            session.data['current_special_step'] = 'thalamur_citizenship'
            self.save_session(session)
            await self.step_thalamur_citizenship(ctx, session)
            return
        
        step_info = self.get_current_step_info(session)
        if step_info:
            await step_info["handler"](ctx, session)
        else:
            await ctx.send("❌ Ogiltigt steg-nummer.")
    
    async def show_status(self, ctx, session: CharacterSession):
        """Visar nuvarande status och progress för sessionen"""
        step_info = self.get_current_step_info(session)
        
        embed = self.embed_factory.admin_message(
            session.user_id,
            "Karaktärsskapande Status",
            f"Steg {session.current_step}/{session.max_steps}: {step_info['title'] if step_info else 'Okänt'}"
        )
        
        # Visa fastställd data
        if session.data:
            completed_fields = []
            for key, value in session.data.items():
                if isinstance(value, dict):
                    completed_fields.append(f"**{key.capitalize()}:** Komplex data")
                else:
                    completed_fields.append(f"**{key.capitalize()}:** {value}")
            
            if completed_fields:
                embed.add_field(
                    name="✅ Fastställda val",
                    value="\n".join(completed_fields[:10]),  # Begränsa till 10 för Discord limit
                    inline=False
                )
                
                if len(completed_fields) > 10:
                    embed.add_field(
                        name="📋 Och mer...",
                        value=f"+{len(completed_fields) - 10} fler val",
                        inline=False
                    )
        
        # Visa temporär data
        if session.temp_data:
            embed.add_field(
                name="⏳ Väntar på bekräftelse",
                value="Använd `!chargen fortsätt` eller `!chargen ändra`",
                inline=False
            )
        
        # Progress bar
        progress = session.current_step / session.max_steps
        progress_bar = "█" * int(progress * 20) + "░" * (20 - int(progress * 20))
        embed.add_field(
            name="📈 Progress",
            value=f"`{progress_bar}` {progress*100:.1f}%",
            inline=False
        )
        
        embed.set_footer(text=f"Startad: {session.created_at.strftime('%Y-%m-%d %H:%M')}")
        await ctx.send(embed=embed)
    
    async def handle_step_input(self, ctx, session: CharacterSession, input_text: str, *args):
        """Hanterar input för nuvarande steg"""
        # Kontrollera om vi är i ett special-steg
        special_step = session.data.get('current_special_step')
        if special_step == 'thalamur_citizenship':
            await self.handle_thalamur_citizenship_input(ctx, session, input_text, *args)
            return
        
        step_info = self.get_current_step_info(session)
        if step_info and hasattr(self, f"handle_{step_info['name']}_input"):
            handler_name = f"handle_{step_info['name']}_input"
            handler = getattr(self, handler_name)
            await handler(ctx, session, input_text, *args)
        else:
            await ctx.send(f"❌ Inget input-hantering för steg {session.current_step}")
    
    # =================
    # STEG-HANTERARE
    # =================
    
    async def step_gender(self, ctx, session: CharacterSession):
        """Steg 1: Välj kön - använder ny modul"""
        await self.gender_step.execute(ctx, session)
    
    async def handle_kön_input(self, ctx, session: CharacterSession, input_text: str, *args):
        """Hanterar input för kön-steget - använder ny modul"""
        success, error = await self.gender_step.handle_input(ctx, session, input_text, *args)
        
        if success:
            # Uppdatera och spara session
            session.update_context()
            self.save_session(session)
            
            # Gå till nästa steg automatiskt
            self.next_step(session)
            await self.show_current_step(ctx, session)
    
    async def step_homeland(self, ctx, session: CharacterSession):
        """Steg 2: Välj hemland - använder ny modul"""
        await self.homeland_step.execute(ctx, session)
    
    async def handle_hemland_input(self, ctx, session: CharacterSession, input_text: str, *args):
        """Hanterar användarinput för hemlandsval - använder ny modul"""
        success, error = await self.homeland_step.handle_input(ctx, session, input_text, *args)
        
        if success:
            # Uppdatera och spara session
            session.update_context()
            self.save_session(session)
            
            # Gå till nästa steg automatiskt
            self.next_step(session)
            await self.show_current_step(ctx, session)
    
    async def show_homeland_choice(self, ctx, session: CharacterSession, homeland: Dict[str, str]):
        """Visar valt hemland med full beskrivning"""
        description = homeland['description']
        
        # Dela upp långa beskrivningar i chunks för Discord
        max_desc_length = 1800  # Discord embed description limit
        
        if len(description) <= max_desc_length:
            # Kort beskrivning - visa allt i en embed
            embed = self.embed_factory.success_message(
                session.user_id,
                f"🏰 Valt hemland: {homeland['title']}\n\n{description}"
            )
            embed.set_footer(text="Skriv: !chargen fortsätt eller !chargen ändra")
            await ctx.send(embed=embed)
        else:
            # Lång beskrivning - dela upp i FLERA EMBEDS (inte code blocks)
            chunks = [description[i:i + max_desc_length] 
                     for i in range(0, len(description), max_desc_length)]
            
            for i, chunk in enumerate(chunks):
                if i == 0:
                    # Första chunken - med titel
                    embed = self.embed_factory.success_message(
                        session.user_id,
                        f"🏰 Valt hemland: {homeland['title']}\n\n{chunk}"
                    )
                elif i == len(chunks) - 1:
                    # Sista chunken - med footer
                    embed = self.embed_factory.success_message(
                        session.user_id,
                        chunk
                    )
                    embed.set_footer(text="Skriv: !chargen fortsätt eller !chargen ändra")
                else:
                    # Mellan-chunkar - bara beskrivning
                    embed = self.embed_factory.success_message(
                        session.user_id,
                        chunk
                    )
                
                await ctx.send(embed=embed)
        
        # Spara temporärt och vänta på bekräftelse
        session.temp_data = {'hemland': homeland}
        self.save_session(session)
    
    async def show_all_homelands(self, ctx, session: CharacterSession):
        """Visar alla länder i numrerad lista"""
        
        if not self.homelands:
            await ctx.send("❌ Inga länder tillgängliga.")
            return
        
        # Dela upp i chunks för att inte överskrida Discord-gränser
        chunk_size = 20
        chunks = [self.homelands[i:i + chunk_size] 
                  for i in range(0, len(self.homelands), chunk_size)]
        
        for chunk_num, chunk in enumerate(chunks, 1):
            embed = self.embed_factory.admin_message(
                session.user_id,
                f"Tillgängliga länder (Del {chunk_num}/{len(chunks)})",
                ""
            )
            
            land_list = []
            start_num = (chunk_num - 1) * chunk_size + 1
            
            for i, homeland in enumerate(chunk, start_num):
                land_list.append(f"{i}. {homeland['title']}")
            
            embed.add_field(
                name=f"Länder {start_num}-{start_num + len(chunk) - 1}:",
                value="\n".join(land_list),
                inline=False
            )
            
            if chunk_num == len(chunks):
                embed.set_footer(text="Skriv: !chargen [nummer] eller !chargen [namn]")
            
            await ctx.send(embed=embed)
    
    async def handle_thalamur_folkslag(self, ctx, session: CharacterSession):
        """Hanterar specialregler för Thalamur - alla är Vanar, val mellan Medborgare/Folket"""
        embed = self.embed_factory.admin_message(
            session.user_id,
            "Steg 3/32: Thalamur Samhällsklass",
            "Alla från **Thalamur** är **Vanar** som folkslag. Du måste välja samhällsklass:"
        )
        
        embed.add_field(
            name="👑 Medborgare",
            value="• Mäktiga i samhället\n• Många är magiker (Thalasker)\n• Kan nå politisk makt\n• Tillhör en av de 9 ätterna\n• Ofta födda in i medborgarskap",
            inline=False
        )
        
        embed.add_field(
            name="👥 Folket",
            value="• Maktlösa i samhället\n• Vanliga människor\n• Ingen politisk makt\n• Ingen ätt-tillhörighet\n• Kan inte bli medborgare (utan 20 års armétjänst)",
            inline=False
        )
        
        embed.add_field(
            name="📋 Välj samhällsklass:",
            value="`!chargen medborgare` - Bli Thalamur Medborgare\n" +
                  "`!chargen folket` - Bli av Folket",
            inline=False
        )
        
        embed.set_footer(text="Alla Thalamurer är Vanar - skillnaden är samhällsklass")
        await ctx.send(embed=embed)
    
    async def handle_thalamur_input(self, ctx, session: CharacterSession, input_text: str, *args):
        """Hanterar input för Thalamur samhällsklass-val"""
        input_lower = input_text.strip().lower()
        
        if input_lower in ['medborgare', 'medborgaren']:
            # Vald Medborgare
            session.data['folkslag'] = 'Vanar'
            session.data['thalamur_samhällsklass'] = 'Medborgare'
            session.data['thalamur_special'] = 'thalasker_medborgare'
            
            await ctx.send("✅ Du är nu **Vanar Medborgare** från Thalamur!\n*Mäktig samhällsklass med potential för magi och politisk makt.*")
            
            # För Medborgare, lägg till medborgarätt-steg (ätt-val)
            self.insert_thalamur_citizenship_step(session)
            
            # Gå till nästa steg
            if self.next_step(session):
                await self.show_current_step(ctx, session)
        
        elif input_lower in ['folket', 'folk']:
            # Vald Folket
            session.data['folkslag'] = 'Vanar'
            session.data['thalamur_samhällsklass'] = 'Folket'
            session.data['thalamur_special'] = 'thalasker_folket'
            
            await ctx.send("✅ Du är nu **Vanar av Folket** från Thalamur!\n*Maktlös samhällsklass, vanliga människor utan politisk makt.*")
            
            # Gå till nästa steg (ingen ätt för Folket)
            if self.next_step(session):
                await self.show_current_step(ctx, session)
        
        else:
            await ctx.send("❌ Ogiltigt val. Använd:\n`!chargen medborgare` - Bli Medborgare\n`!chargen folket` - Bli av Folket")
    
    
    def insert_thalamur_citizenship_step(self, session: CharacterSession):
        """Markerar att Thalaskisk medborgarätt-steg ska köras efter current_step"""
        # Spara vilket steg vi var på innan citizenship-steget
        session.data['thalamur_citizenship_return_step'] = session.current_step
        # Lägg till en flagga i session data för att indikera att citizenship-steget ska köras
        session.data['thalamur_citizenship_pending'] = True
        self.save_session(session)
    
    async def step_thalamur_citizenship(self, ctx, session: CharacterSession):
        """Steg för Thalaskisk medborgarätt - endast för Thalamur Medborgare"""
        # Kontrollera att det är relevant
        if (session.data.get('thalamur_special') != 'thalasker_medborgare' or 
            session.data.get('thalamur_samhällsklass') != 'Medborgare'):
            # Hoppa över detta steg
            await ctx.send("⏭️ Thalaskisk medborgarätt: Inte relevant för din karaktär")
            if self.next_step(session):
                await self.show_current_step(ctx, session)
            return
        
        embed = self.embed_factory.admin_message(session.user_id, "🏛️ Thalaskisk Medborgarätt", "Som **Thalamur Medborgare** tillhör du en av rikets medborgarätter (ätter):")
        
        embed.add_field(
            name="🎲 Slumpmässig ätt",
            value="`!chargen slåätt` - Slå 1d10 på tabellen för slumpmässig ätt",
            inline=False
        )
        
        embed.add_field(
            name="📋 Välj själv", 
            value="`!chargen listaätter` - Visa alla 9 ätter och välj\n`!chargen [ättnamn]` - Välj specifik ätt direkt",
            inline=False
        )
        
        embed.add_field(
            name="💎 Tillgängliga ätter:",
            value="• **Abhixia** - Alkemi och pyrotropi\n• **Arginakus** - Forskare och magiker\n• **Cartika** - Traditionalister och administratörer\n• **Harim** - Krigsmakt och järnhand\n• **Kobinku** - Mystik och svartkonst",
            inline=False
        )
        
        embed.add_field(
            name="💎 Fler ätter:",
            value="• **Myrdinor** - Folknära krigare\n• **Sala** - Rika affärsmän\n• **Vaganda** - Kunskapssökare\n• **Zadhaz** - Diplomater och konstnärer",
            inline=False
        )
        
        embed.set_footer(text="Varje ätt ger olika bonusar och färdigheter")
        await ctx.send(embed=embed)
    
    async def handle_thalamur_citizenship_input(self, ctx, session: CharacterSession, input_text: str, *args):
        """Hanterar input för Thalaskisk medborgarätt"""
        input_lower = input_text.strip().lower()
        
        if input_lower in ['slåätt', 'slå', 'random']:
            await self.roll_thalamur_citizenship(ctx, session)
        elif input_lower in ['listaätter', 'lista', 'ätter']:
            await self.show_all_thalamur_atter(ctx, session)
        elif input_lower in ['abhixia', 'arginakus', 'cartika', 'harim', 'kobinku', 'myrdinor', 'sala', 'vaganda', 'zadhaz']:
            await self.select_thalamur_att(ctx, session, input_lower)
        elif input_lower in ['fortsätt', 'behåll', 'ok']:
            # Kontrollera att ätt är vald
            if not session.data.get('thalamur_ätt'):
                await ctx.send("❌ Du måste välja en ätt först!")
                return
            
            # Avsluta special-steget och återvända till rätt steg
            session.data.pop('current_special_step', None)
            
            # Återvända till steget vi var på innan citizenship-steget + gå till nästa
            return_step = session.data.pop('thalamur_citizenship_return_step', session.current_step)
            session.current_step = return_step
            self.save_session(session)
            
            # Gå till nästa steg från där vi var
            if self.next_step(session):
                await self.show_current_step(ctx, session)
        else:
            await ctx.send("❌ Ogiltigt val. Använd:\n`!chargen slåätt` - Slumpmässig ätt\n`!chargen listaätter` - Visa alla ätter\n`!chargen [ättnamn]` - Välj specifik ätt\n`!chargen fortsätt` - Gå vidare (efter att ha valt ätt)")
    
    async def roll_thalamur_citizenship(self, ctx, session: CharacterSession):
        """Slår slumpmässig ätt för Thalamur medborgarätt"""
        if not self.thalamur_atter_data:
            try:
                with open('data/character_tables/folkslag/thalamur_att.json', 'r', encoding='utf-8') as f:
                    self.thalamur_atter_data = json.load(f)
            except FileNotFoundError:
                await ctx.send("❌ Fel: Kunde inte ladda thalamur_att.json")
                return
        
        # Slå 1d10
        roll = random.randint(1, 10)
        
        if roll == 10:
            # Reroll mechanic
            embed = self.embed_factory.admin_message(session.user_id, "🎲 Ätt-slag: 10 - Slå om!", "Du slog 10! Slå om för att få din ätt.")
            embed.set_footer(text="Slår automatiskt om...")
            await ctx.send(embed=embed)
            
            # Slå om automatiskt
            new_roll = random.randint(1, 9)  # 1-9 bara
            await self.assign_thalamur_att_by_number(ctx, session, new_roll, f"(Omslag från 10 → {new_roll})")
        else:
            await self.assign_thalamur_att_by_number(ctx, session, roll)
    
    async def assign_thalamur_att_by_number(self, ctx, session: CharacterSession, roll_number: int, extra_info: str = ""):
        """Tilldelar ätt baserat på nummer (1-9)"""
        att_names = ['abhixia', 'arginakus', 'cartika', 'harim', 'kobinku', 'myrdinor', 'sala', 'vaganda', 'zadhaz']
        
        if roll_number < 1 or roll_number > 9:
            await ctx.send("❌ Ogiltigt ätt-nummer")
            return
        
        selected_att = att_names[roll_number - 1]
        await self.select_thalamur_att(ctx, session, selected_att, f"🎲 Slag: {roll_number} {extra_info}")
    
    async def show_all_thalamur_atter(self, ctx, session: CharacterSession):
        """Visar alla Thalamur ätter i detalj"""
        if not self.thalamur_atter_data:
            try:
                with open('data/character_tables/folkslag/thalamur_att.json', 'r', encoding='utf-8') as f:
                    self.thalamur_atter_data = json.load(f)
            except FileNotFoundError:
                await ctx.send("❌ Fel: Kunde inte ladda thalamur_att.json")
                return
        
        atter = self.thalamur_atter_data.get('thalamuriska_atter', {})
        
        # Skapa flera embeds för alla ätter
        embeds = []
        counter = 1
        
        for att_key, att_data in atter.items():
            embed = self.embed_factory.admin_message(
                session.user_id,
                f"Ätt {counter}: {att_data['titel']}",
                att_data['beskrivning']
            )
            
            bonusar = att_data.get('bonusar', {})
            
            # Placera slag
            if 'placera_slag' in bonusar:
                embed.add_field(
                    name="🎯 Placera bakgrundslag på:",
                    value="\n".join([f"• {slag.title()}" for slag in bonusar['placera_slag']]),
                    inline=False
                )
            
            # Lättlärda färdigheter
            if 'lattlarda_fardigheter' in bonusar:
                embed.add_field(
                    name="📚 Lättlärda färdigheter:",
                    value="\n".join([f"• {skill.title()}" for skill in bonusar['lattlarda_fardigheter']]),
                    inline=False
                )
            
            # Extra kontakter
            if 'extra_kontakter' in bonusar:
                embed.add_field(
                    name="👥 Extra kontakter:",
                    value=f"+{bonusar['extra_kontakter']} kontakter",
                    inline=True
                )
            
            # Special regel
            if 'special_regel' in bonusar:
                embed.add_field(
                    name="⚠️ Specialregel:",
                    value=bonusar['special_regel'],
                    inline=False
                )
            
            embed.set_footer(text=f"Använd: !chargen {att_key} för att välja denna ätt")
            embeds.append(embed)
            counter += 1
        
        # Skicka alla embeds
        for embed in embeds:
            await ctx.send(embed=embed)
    
    async def select_thalamur_att(self, ctx, session: CharacterSession, att_name: str, roll_info: str = ""):
        """Väljer specifik Thalamur ätt"""
        if not self.thalamur_atter_data:
            try:
                with open('data/character_tables/folkslag/thalamur_att.json', 'r', encoding='utf-8') as f:
                    self.thalamur_atter_data = json.load(f)
            except FileNotFoundError:
                await ctx.send("❌ Fel: Kunde inte ladda thalamur_att.json")
                return
        
        atter = self.thalamur_atter_data.get('thalamuriska_atter', {})
        att_data = atter.get(att_name.lower())
        
        if not att_data:
            await ctx.send(f"❌ Ätt '{att_name}' hittades inte")
            return
        
        # Spara valet
        session.data['thalamur_ätt'] = att_name.lower()
        session.data['thalamur_ätt_data'] = att_data
        self.save_session(session)
        
        # Visa bekräftelse
        embed = self.embed_factory.admin_message(
            session.user_id, 
            f"✅ Vald ätt: {att_data['titel']}", 
            f"{roll_info}\n\n{att_data['beskrivning']}"
        )
        
        bonusar = att_data.get('bonusar', {})
        
        # Visa alla bonusar
        if 'placera_slag' in bonusar:
            embed.add_field(
                name="🎯 Får placera bakgrundslag på:",
                value="\n".join([f"• {slag.title()}" for slag in bonusar['placera_slag']]),
                inline=False
            )
        
        if 'lattlarda_fardigheter' in bonusar:
            embed.add_field(
                name="📚 Lättlärda färdigheter:",
                value="\n".join([f"• {skill.title()}" for skill in bonusar['lattlarda_fardigheter']]),
                inline=False
            )
        
        if 'extra_kontakter' in bonusar:
            embed.add_field(
                name="👥 Bonuskontakter:",
                value=f"+{bonusar['extra_kontakter']} extra kontakter",
                inline=True
            )
        
        if 'special_regel' in bonusar:
            embed.add_field(
                name="⚠️ Specialregel:",
                value=bonusar['special_regel'],
                inline=False
            )
        
        embed.set_footer(text="!chargen fortsätt för att gå vidare")
        await ctx.send(embed=embed)
    
    async def step_race(self, ctx, session: CharacterSession):
        """Steg 3: Välj folkslag - använder ny modul"""
        await self.race_step.execute(ctx, session)
    
    async def handle_folkslag_input(self, ctx, session: CharacterSession, input_text: str, *args):
        """Hanterar input för folkslag - använder ny modul"""
        success, error = await self.race_step.handle_input(ctx, session, input_text, *args)
        if success:
            session.update_context()
            self.save_session(session)
            self.next_step(session)
            await self.show_current_step(ctx, session)
    
    async def show_folkslag_choice(self, ctx, session: CharacterSession, folkslag: Dict[str, str]):
        """Visar valt folkslag med full beskrivning och attributmodifierare"""
        description = folkslag['description']
        
        # Skapa huvudembed med titel
        embed = self.embed_factory.admin_message(
            session.user_id, 
            f"🏛️ Valt folkslag: {folkslag['title']}", 
            "Dina attributmodifierare och färdigheter:"
        )
        
        # Lägg till attributmodifierare från attribute_modifiers.json
        modifiers = self._get_race_modifiers(folkslag['name'])
        if modifiers:
            mod_text = "\n".join(f"**{attr}:** {'+' if mod >= 0 else ''}{mod}" 
                                for attr, mod in modifiers.items())
            embed.add_field(name="Attributmodifierare:", value=mod_text, inline=False)
        
        # Hantera beskrivning (kan vara lång)
        max_desc_length = 1200  # Plats för attributmodifierare
        
        if len(description) <= max_desc_length:
            # Kort beskrivning - lägg till i samma embed
            embed.description = description
            embed.set_footer(text="Skriv: !chargen fortsätt eller !chargen ändra")
            await ctx.send(embed=embed)
        else:
            # Lång beskrivning - första embed med attributmodifierare
            embed.set_footer(text="Skriv: !chargen fortsätt eller !chargen ändra")
            await ctx.send(embed)
            
            # Dela upp beskrivningen i flera embeds
            chunks = [description[i:i + 1800] 
                     for i in range(0, len(description), 1800)]
            
            for i, chunk in enumerate(chunks):
                embed = self.embed_factory.admin_message(
                    session.user_id, 
                    f"Beskrivning (del {i+1}/{len(chunks)})", 
                    chunk
                )
                
                # Lägg bara footer på sista chunken OM den inte redan finns
                if i == len(chunks) - 1:
                    embed.set_footer(text="(Fortsättning från folkslag-beskrivning)")
                
                await ctx.send(embed=embed)
        
        # Spara temporärt och vänta på bekräftelse
        session.temp_data = {'folkslag': folkslag}
        self.save_session(session)
    
    async def show_all_folkslag(self, ctx, session: CharacterSession):
        """Visar alla folkslag i numrerad lista"""
        
        all_folkslag = session.temp_data.get('all_folkslag', [])
        if not all_folkslag:
            await ctx.send("❌ Inga folkslag tillgängliga.")
            return
        
        # Dela upp i chunks för att inte överskrida Discord-gränser
        chunk_size = 20
        chunks = [all_folkslag[i:i + chunk_size] 
                  for i in range(0, len(all_folkslag), chunk_size)]
        
        for chunk_num, chunk in enumerate(chunks, 1):
            embed = self.embed_factory.admin_message(
                session.user_id, 
                f"🏛️ Tillgängliga folkslag (Del {chunk_num}/{len(chunks)})", 
                "Välj ett folkslag från listan nedan:"
            )
            
            folkslag_list = []
            start_num = (chunk_num - 1) * chunk_size + 1
            
            for i, folkslag in enumerate(chunk, start_num):
                folkslag_list.append(f"{i}. {folkslag['title']} ({folkslag['category']})")
            
            embed.add_field(
                name=f"Folkslag {start_num}-{start_num + len(chunk) - 1}:",
                value="\n".join(folkslag_list),
                inline=False
            )
            
            if chunk_num == len(chunks):
                embed.set_footer(text="Skriv: !chargen [nummer] eller !chargen [namn]")
            
            await ctx.send(embed=embed)
    
    def _get_race_modifiers(self, race_name: str) -> Dict[str, int]:
        """Hämtar attributmodifierare för ett folkslag"""
        if 'attribute_modifiers' not in self.table_processor.tables:
            return {}
        
        races_data = self.table_processor.tables['attribute_modifiers']
        
        # Sök i alla kategorier
        for category, races in races_data.items():
            if race_name.lower() in races:
                return races[race_name.lower()]
        
        return {}
    
    async def confirm_current_choice(self, ctx, session: CharacterSession):
        """Bekräftar det nuvarande valet och går vidare"""
        
        if not session.temp_data:
            await ctx.send("❌ Inget val att bekräfta.")
            return
        
        current_step = session.current_step
        step_info = self.get_current_step_info(session)
        
        # If step_info is None, we're beyond defined steps
        if not step_info:
            await ctx.send("❌ Detta steg är inte implementerat än.")
            return
        
        if step_info['name'] == 'hemland' and 'hemland' in session.temp_data:
            selected_homeland = session.temp_data['hemland']
            session.data['hemland'] = selected_homeland['name']
            session.data['hemland_title'] = selected_homeland['title']
            
            await ctx.send(f"✅ Hemland bekräftat: **{selected_homeland['title']}**")
            
        elif step_info['name'] == 'folkslag' and 'folkslag' in session.temp_data:
            selected_folkslag = session.temp_data['folkslag']
            session.data['folkslag'] = selected_folkslag['name']
            session.data['folkslag_title'] = selected_folkslag['title']
            session.data['folkslag_category'] = selected_folkslag['category']
            print(f"DEBUG - confirm_current_choice: Moved folkslag='{selected_folkslag['name']}' from temp_data to data")
            print(f"DEBUG - Session data now contains: {list(session.data.keys())}")
            
            # Uppdatera context för TableProcessor
            session.update_context()
            
            await ctx.send(f"✅ Folkslag bekräftat: **{selected_folkslag['title']}**")
        
        elif step_info['name'] == 'familjebakgrund' and 'awaiting_family_confirmation' in session.temp_data:
            # Bekräfta KOMPLETT familjebakgrund
            complete_family = session.temp_data['komplett_familjebakgrund']
            session.data['komplett_familjebakgrund'] = complete_family
            
            # Extrahera och applicera alla benefits automatiskt
            await self.apply_complete_family_benefits(session)
            
            await ctx.send("✅ **Komplett familjebakgrund bekräftad!** Alla färdigheter och attributeffekter applicerade.")
        
        elif step_info['name'] == 'attribut' and 'awaiting_attribute_confirmation' in session.temp_data:
            # Bekräfta attribut
            session.data['attribut'] = session.temp_data['attribut']
            session.data['grundattribut'] = session.temp_data['grundattribut']
            session.data['attribut_metod'] = session.temp_data['metod']
            session.data['attribut_summa'] = session.temp_data['attribut_summa']
            session.data['chockvärde'] = session.temp_data['chockvärde']
            
            await ctx.send(f"✅ **Attribut bekräftade!** (Metod: {session.temp_data['metod']}, Summa: {session.temp_data['attribut_summa']})")
        
        # Rensa temp data och gå till nästa steg
        session.temp_data.clear()
        session.update_context()
        self.save_session(session)
        
        # Gå till nästa steg automatiskt
        if self.next_step(session):
            await self.show_current_step(ctx, session)
    
    async def step_age(self, ctx, session: CharacterSession):
        """Steg 4: Välj ålder - använder ny modul"""
        await self.age_step.execute(ctx, session)
    
    async def handle_ålder_input(self, ctx, session: CharacterSession, input_text: str, *args):
        """Hanterar input för ålder-steget - använder ny modul"""
        success, error = await self.age_step.handle_input(ctx, session, input_text, *args)
        
        if success:
            # Uppdatera och spara session
            session.update_context()
            self.save_session(session)
            
            # Gå till nästa steg automatiskt
            self.next_step(session)
            await self.show_current_step(ctx, session)
    
    async def handle_kultur_input(self, ctx, session: CharacterSession, input_text: str, *args):
        """Hanterar input för kultur-steget - använder ny modul"""
        success, error = await self.culture_step.handle_input(ctx, session, input_text, *args)
        if success:
            session.update_context()
            self.save_session(session)
            self.next_step(session)
            await self.show_current_step(ctx, session)
    
    async def show_culture_info(self, ctx, culture_info: Dict[str, Any]):
        """Visar detaljerad information om en kultur"""
        culture_data = culture_info['info']
        
        embed = self.embed_factory.admin_message(
            ctx.author.id, 
            f"🏛️ {culture_info['title']}", 
            culture_data.get('beskrivning', 'Ingen beskrivning tillgänglig')
        )
        
        # Visa några exempel på professioner från denna kultur
        ranges = culture_data.get('ranges', {})
        if ranges:
            profession_examples = []
            example_count = 0
            
            for range_key, range_data in ranges.items():
                if example_count < 5:  # Visa max 5 exempel
                    profession = range_data.get('profession', 'Okänd')
                    profession_examples.append(f"• {profession.capitalize()}")
                    example_count += 1
            
            if profession_examples:
                embed.add_field(
                    name="Exempel på familjeyrken:",
                    value="\n".join(profession_examples),
                    inline=False
                )
        
        # Visa färdighetsbonus-info
        skill_bonus = culture_data.get('skill_bonus', '')
        if skill_bonus:
            embed.add_field(
                name="Färdighetsbonus:",
                value=f"Varje färdighet får {skill_bonus} poäng",
                inline=False
            )
        
        embed.set_footer(text="Gå tillbaka med !chargen för att välja")
        await ctx.send(embed=embed)
    
    async def handle_attribut_input(self, ctx, session: CharacterSession, input_text: str, *args):
        """Hanterar input för attribut-steget - använder ny modul"""
        success, error = await self.attributes_step.handle_input(ctx, session, input_text, *args)
        if success:
            session.update_context()
            self.save_session(session)
            self.next_step(session)
            await self.show_current_step(ctx, session)
    
    # Placeholder för resterande steg-hanterare
    async def step_culture(self, ctx, session: CharacterSession):
        """Steg 5: Välj kultur - använder ny modul"""
        await self.culture_step.execute(ctx, session)
    
    async def step_attributes(self, ctx, session: CharacterSession):
        """Steg 6: Generera grundattribut - använder ny modul"""
        await self.attributes_step.execute(ctx, session)
    
    async def step_special_rules(self, ctx, session: CharacterSession):
        """Steg 7: Specialregler - använder ny modul"""
        await self.special_rules_step.execute(ctx, session)
    
    
    
    async def handle_specialregler_input(self, ctx, session: CharacterSession, input_text: str, *args):
        """Hanterar input för specialregler - använder ny modul"""
        success, error = await self.special_rules_step.handle_input(ctx, session, input_text, *args)
        if success:
            session.update_context()
            self.save_session(session)
            self.next_step(session)
            await self.show_current_step(ctx, session)
    
    async def step_character_traits(self, ctx, session: CharacterSession):
        """Steg 8: Karaktärsdrag - använder ny modul"""
        await self.traits_step.execute(ctx, session)
    
    async def handle_karaktärsdrag_input(self, ctx, session: CharacterSession, input_text: str, *args):
        """Hanterar input för karaktärsdrag-steget - använder ny modul"""
        success, error = await self.traits_step.handle_input(ctx, session, input_text, *args)
        if success:
            session.update_context()
            self.save_session(session)
            self.next_step(session)
            await self.show_current_step(ctx, session)
    
    async def handle_familjebakgrund_input(self, ctx, session: CharacterSession, input_text: str, *args):
        """Hanterar input för familjebakgrund-steget - använder ny modul"""
        success, error = await self.family_step.handle_input(ctx, session, input_text, *args)
        if success:
            session.update_context()
            self.save_session(session)
            self.next_step(session)
            await self.show_current_step(ctx, session)
    
    async def roll_character_traits(self, ctx, session: CharacterSession):
        """Slår karaktärsdrag baserat på folkslag"""
        folkslag = session.data.get('folkslag', '').lower()
        
        # Karaktärsdrag och deras tärningsslag per folkslag
        trait_dice = self.get_character_trait_dice(folkslag, session)
        
        if not trait_dice:
            await ctx.send(f"❌ Karaktärsdrag inte implementerat för folkslag: {folkslag}")
            # Gå vidare ändå
            if self.next_step(session):
                await self.show_current_step(ctx, session)
            return
        
        # Slå alla karaktärsdrag
        results = {}
        for trait, dice_formula in trait_dice.items():
            roll_result = self.roll_dice_formula(dice_formula)
            results[trait] = {
                'value': roll_result,
                'dice': dice_formula
            }
        
        # Visa resultaten
        folkslag_display = session.data.get('folkslag', '').capitalize()
        
        # Specialvisning för Thalamur Medborgare
        if (session.data.get('thalamur_special') == 'thalasker_medborgare' and 
            session.data.get('thalamur_samhällsklass') == 'Medborgare'):
            folkslag_display = "Thalasker"
        
        embed = self.embed_factory.admin_message(
            session.user_id, 
            "🎭 Dina Karaktärsdrag", 
            f"Karaktärsdrag för **{folkslag_display}**:"
        )
        
        for trait, data in results.items():
            embed.add_field(
                name=f"{trait.capitalize()}",
                value=f"**{data['value']}** ({data['dice']})",
                inline=True
            )
        
        # Spara i temp_data för bekräftelse
        session.temp_data = {'karaktärsdrag': results}
        self.save_session(session)
        
        embed.set_footer(text="!chargen fortsätt för att behålla, !chargen slåom för att slå om")
        await ctx.send(embed=embed)
    
    def get_character_trait_dice(self, folkslag: str, session: CharacterSession = None) -> dict:
        """Returnerar tärningsslag för karaktärsdrag baserat på folkslag"""
        folkslag_lower = folkslag.lower()
        
        # Specialhantering för Thalamur Medborgare - de använder Thalasker-karaktärsdrag
        if (session and session.data.get('thalamur_special') == 'thalasker_medborgare' and 
            session.data.get('thalamur_samhällsklass') == 'Medborgare'):
            folkslag_lower = 'thalasker'
        
        # Mappning enligt tabellen du gav (ignorerar Resurser)
        trait_mapping = {
            'soldarn': {
                'lojalitet': '1d6+12',
                'heder': '3d6', 
                'amor': '3d6',
                'aggression': '3d6',
                'tro': '1d6+12',
                'generositet': '3d6',
                'rykte': '3d6'
            },
            'asharier': {
                'lojalitet': '3d6',
                'heder': '3d6',
                'amor': '3d6', 
                'aggression': '3d6',
                'tro': '3d6',
                'generositet': '1d6+2',
                'rykte': '3d6'
            },
            'auser': {
                'lojalitet': '3d6',
                'heder': '3d6',
                'amor': '3d6',
                'aggression': '3d6', 
                'tro': '1d6+12',
                'generositet': '3d6',
                'rykte': '3d6'
            },
            'thalasker': {
                'lojalitet': '3d6',
                'heder': '3d6',
                'amor': '3d6',
                'aggression': '3d6',
                'tro': '3d6',
                'generositet': '3d6', 
                'rykte': '2d6+6'
            },
            'pyar': {
                'lojalitet': '2d6+6',
                'heder': '3d6',
                'amor': '2d6+1',
                'aggression': '3d6',
                'tro': '2d6+1',
                'generositet': '2d6+6',
                'rykte': '2d6+1'
            },
            'kiriya': {
                'lojalitet': '2d6+6',
                'heder': '3d6',
                'amor': '2d6+1',
                'aggression': '3d6',
                'tro': '2d6+1',
                'generositet': '2d6+6',
                'rykte': '3d6'
            },
            'thism': {
                'lojalitet': '2d6+6',
                'heder': '2d6+6',
                'amor': '2d6+1',
                'aggression': '2d6+6',
                'tro': '2d6+1',
                'generositet': '2d6+6',
                'rykte': '3d6'
            },
            'sanari': {
                'lojalitet': '2d6+6',
                'heder': '2d6+1',
                'amor': '2d6+1',
                'aggression': '2d6+1',
                'tro': '2d6+1',
                'generositet': '2d6+1',
                'rykte': '2d6+6'
            },
            'léaram': {
                'lojalitet': '2d6+6',
                'heder': '2d6+6',
                'amor': '2d6+1',
                'aggression': '2d6+6',
                'tro': '3d6',
                'generositet': '2d6+6',
                'rykte': '3d6'
            },
            'henéa': {
                'lojalitet': '2d6+6',
                'heder': '3d6',
                'amor': '2d6+1',
                'aggression': '1d6+12',
                'tro': '2d6+6',
                'generositet': '2d6+1',
                'rykte': '2d6+1'
            },
            'cirefalier': {
                'lojalitet': '2d6+6',
                'heder': '3d6',
                'amor': '3d6',
                'aggression': '3d6',
                'tro': '2d6+6',
                'generositet': '3d6',
                'rykte': '3d6'
            },
            'vanar': {
                'lojalitet': '3d6',
                'heder': '3d6',
                'amor': '3d6',
                'aggression': '3d6',
                'tro': '3d6',
                'generositet': '3d6',
                'rykte': '3d6'
            }
        }
        
        # Försök hitta exact match för folkslag/nationalitet i listan
        for folk_key, traits in trait_mapping.items():
            if folk_key in folkslag_lower or folkslag_lower in folk_key:
                return traits
        
        # Om folkslagets nationalitet INTE finns i listan - använd 3d6 på alla
        return {
            'lojalitet': '3d6',
            'heder': '3d6',
            'amor': '3d6',
            'aggression': '3d6',
            'tro': '3d6',
            'generositet': '3d6',
            'rykte': '3d6'
        }
    
    def roll_dice_formula(self, formula: str) -> int:
        """Slår tärningar enligt formel som '3d6', '2d6+6', '1d6+12'"""
        import re
        
        # Parse formula som "XdY+Z" eller "XdY"
        match = re.match(r'(\d+)d(\d+)(?:\+(\d+))?', formula.lower())
        if not match:
            return 0
        
        num_dice = int(match.group(1))
        dice_sides = int(match.group(2))
        modifier = int(match.group(3)) if match.group(3) else 0
        
        # Slå tärningarna
        total = sum(random.randint(1, dice_sides) for _ in range(num_dice)) + modifier
        return total
    
    async def roll_egendom_table(self, session: CharacterSession, table_data: dict, original_result: dict) -> dict:
        """Slår på egendomstabell med kultur-specifik logik"""
        # Bestäm vilken egendomstabell som ska användas
        egendom_table_key = self.determine_egendom_table(session)
        
        if egendom_table_key not in table_data['egendomstabeller']:
            # Fallback till civiliserad_landsbygd om tabellen inte finns
            egendom_table_key = 'civiliserad_landsbygd'
        
        egendom_table = table_data['egendomstabeller'][egendom_table_key]
        
        # Slå på den valda egendomstabellen
        roll = random.randint(1, 100)
        result_data = self.find_egendom_result(egendom_table, roll, session)
        
        return {
            'table_type': 'egendom',
            'table_file': 'egendom.json',
            'roll': roll,
            'result': result_data['description'],
            'result_key': result_data['result'],
            'egendom_table': egendom_table_key,
            'special_rule': result_data.get('special_rule'),
            'options': result_data.get('options')
        }
    
    def determine_egendom_table(self, session: CharacterSession) -> str:
        """Bestämmer vilken egendomstabell som ska användas baserat på karaktärens bakgrund"""
        folkslag = session.data.get('folkslag', '').lower()
        kultur = session.data.get('kultur', '').lower()  # Detta är valet från steg 5
        
        # Dvärgspecifik hantering
        if any(dvarg in folkslag for dvarg in ['ghor', 'drezin', 'roghan']):
            return 'dvarg_ghor_drezin_roghan'
        
        # Missla-specifik hantering  
        if 'missla' in folkslag:
            return 'missla'
        
        # Använd kulturen från steg 5 för att bestämma egendomstabell
        # Baserat på huvudnaring.json kategorierna:
        if 'primitiv' in kultur:
            return 'primitiv'
        elif any(stad in kultur for stad in ['hamnstad', 'inlandstad', 'stad']):
            return 'civiliserad_stad'
        elif any(land in kultur for land in ['landsbygd', 'gård']):
            return 'civiliserad_landsbygd'
        
        # Fallback baserat på huvudnaring-kategorierna från steg 5:
        # - adlig_civiliserad -> civiliserad_stad (adeln bor ofta i städer)
        # - civiliserad_landsbygd -> civiliserad_landsbygd
        # - civiliserad_hamnstad -> civiliserad_stad  
        # - civiliserad_inlandstad -> civiliserad_stad
        # - primitiv_jägar_fiskare -> primitiv
        # - primitiv_nomad -> primitiv
        # - primitiv_bonde -> civiliserad_landsbygd (bonde = jordbruk)
        
        if 'adlig' in kultur:
            return 'civiliserad_stad'
        elif 'hamnstad' in kultur or 'inlandstad' in kultur:
            return 'civiliserad_stad'
        elif 'jägar' in kultur or 'nomad' in kultur:
            return 'primitiv'
        elif 'bonde' in kultur:
            return 'civiliserad_landsbygd'
        
        # Default: civiliserad landsbygd
        return 'civiliserad_landsbygd'
    
    def find_egendom_result(self, egendom_table: dict, roll: int, session: CharacterSession) -> dict:
        """Hittar resultat från egendomstabell och hanterar speciella fall"""
        ranges = egendom_table.get('ranges', {})
        
        for range_key, range_data in ranges.items():
            if self._is_roll_in_range(roll, range_key):
                result = {
                    'result': range_data['result'],
                    'description': range_data['description']
                }
                
                # Hantera speciella regler
                if 'special_rule' in range_data:
                    result['special_rule'] = range_data['special_rule']
                
                # Hantera options (för missla - landsbygd vs stad)
                if 'options' in range_data:
                    result['options'] = range_data['options']
                    # För missla, bestäm landsbygd vs stad baserat på hemland/kultur
                    if session.data.get('folkslag', '').lower() == 'missla':
                        miljö = self.determine_missla_environment(session)
                        if miljö in range_data['options']:
                            result['description'] = range_data['options'][miljö]
                        
                return result
        
        return {
            'result': 'error',
            'description': f'Inget resultat för slag {roll}'
        }
    
    def determine_missla_environment(self, session: CharacterSession) -> str:
        """Bestämmer om en missla bor på landsbygden eller i stad"""
        hemland = session.data.get('hemland', '').lower()
        kultur = session.data.get('kultur', '').lower()
        
        # Kolla indikatorer för stadsmiljö
        if any(stad in hemland for stad in ['stad', 'city', 'urban']) or \
           any(stad in kultur for stad in ['stad', 'urban', 'handels']):
            return 'stad'
        
        return 'landsbygd'
    
    def find_subtable_result_with_conditions(self, table_data: Dict[str, Any], roll: int, session: CharacterSession) -> Dict[str, str]:
        """Hittar resultat från undertabell och hanterar conditional logik"""
        # Först försök hitta resultatet i tabellen
        result_entry = self.find_table_entry(table_data, roll)
        
        if not result_entry:
            return {
                'result': 'error',
                'description': f'Inget resultat för slag {roll}'
            }
        
        # Kolla om det är ett conditional resultat
        if 'conditions' in result_entry:
            return self.resolve_conditional_result(result_entry, session)
        
        # Vanligt resultat
        return {
            'result': result_entry.get('result', 'unknown'),
            'description': result_entry.get('description', f'Resultat för slag {roll}')
        }
    
    def find_table_entry(self, table_data: Dict[str, Any], roll: int) -> Dict[str, Any]:
        """Hittar tabellpost för ett givet slag"""
        # Hantera EON tabellstruktur med bakgrundstabeller
        if 'bakgrundstabeller' in table_data:
            for section_name, section_data in table_data['bakgrundstabeller'].items():
                if 'ranges' in section_data:
                    ranges = section_data['ranges']
                    for range_key, range_data in ranges.items():
                        if self._is_roll_in_range(roll, range_key):
                            return range_data
        
        # Hantera händelsetabeller struktur
        if 'händelsetabeller' in table_data:
            for section_name, section_data in table_data['händelsetabeller'].items():
                if 'ranges' in section_data:
                    ranges = section_data['ranges']
                    for range_key, range_data in ranges.items():
                        if self._is_roll_in_range(roll, range_key):
                            return range_data
        
        # Direkta ranges
        if 'ranges' in table_data:
            ranges = table_data['ranges']
            for range_key, range_data in ranges.items():
                if self._is_roll_in_range(roll, range_key):
                    return range_data
        
        return None
    
    def resolve_conditional_result(self, result_entry: Dict[str, Any], session: CharacterSession) -> Dict[str, str]:
        """Löser conditional resultat baserat på spelarens egenskaper"""
        conditions = result_entry.get('conditions', {})
        folkslag = session.data.get('folkslag', '').lower()
        
        # Kolla dvärg-villkor
        if 'is_dvärg' in conditions and any(dvarg in folkslag for dvarg in ['ghor', 'drezin', 'roghan', 'dvärg']):
            condition_result = conditions['is_dvärg']
            return {
                'result': condition_result.get('result', 'dvärg_result'),
                'description': condition_result.get('description', 'Dvärg-specifikt resultat')
            }
        
        if 'not_dvärg' in conditions and not any(dvarg in folkslag for dvarg in ['ghor', 'drezin', 'roghan', 'dvärg']):
            condition_result = conditions['not_dvärg']
            return {
                'result': condition_result.get('result', 'icke_dvärg_result'),
                'description': condition_result.get('description', 'Icke-dvärg resultat')
            }
        
        # Kolla riddare-villkor (kan utökas senare)
        kultur = session.data.get('kultur', '').lower()
        if 'not_riddare' in conditions and 'adlig' not in kultur:
            condition_result = conditions['not_riddare']
            return {
                'result': condition_result.get('result', 'icke_riddare_result'),
                'description': condition_result.get('description', 'Icke-riddare resultat')
            }
        
        if 'is_riddare' in conditions and 'adlig' in kultur:
            condition_result = conditions['is_riddare']
            return {
                'result': condition_result.get('result', 'riddare_result'),
                'description': condition_result.get('description', 'Riddare-specifikt resultat')
            }
        
        # Fallback till första condition om ingen matchar
        first_condition = next(iter(conditions.values()))
        return {
            'result': first_condition.get('result', 'fallback_result'),
            'description': first_condition.get('description', 'Fallback resultat')
        }
    
    async def step_family_background(self, ctx, session: CharacterSession):
        """Steg 9: Family background generation using modular system"""
        await self.family_step.execute(ctx, session)
    
    async def generate_complete_family_system(self, session: CharacterSession, family_generation_race: str, age: int, kultur: str, hemland: str) -> Dict[str, Any]:
        """Genererar ALLA familj-aspekter på en gång"""
        complete_family = {}
        
        # 1. GRUNDLÄGGANDE FAMILJ (befintlig AutomaticBackgroundGenerator)
        basic_family = self.bg_generator.generate_complete_background(family_generation_race, age)
        # Konvertera FamilyBackground dataclass till dict för JSON-serialisering
        complete_family['basic'] = self._convert_family_background_to_dict(basic_family)
        
        # 2. FAMILJENS HUVUDNÄRING (baserat på kultur från steg 5)
        profession_result = self.generate_family_profession(kultur)
        complete_family['profession'] = profession_result
        
        # 3. FAMILJETABELLER (specialegenskaper)  
        family_special = self.generate_family_special_tables(family_generation_race, kultur, session)
        complete_family['special'] = family_special
        
        # 4. RASSPECIFIKA TILLÄGG
        race_specific = self.generate_race_specific_family(family_generation_race, age)
        complete_family['race_specific'] = race_specific
        
        return complete_family
    
    def generate_family_profession(self, kultur: str) -> Dict[str, Any]:
        """Genererar familjens huvudnäring baserat på kultur från steg 5"""
        if not self.culture_data or kultur not in self.culture_data:
            return {"error": f"Kunde inte hitta kulturdata för: {kultur}"}
        
        culture_table = self.culture_data[kultur]
        ranges = culture_table.get('ranges', {})
        
        if not ranges:
            return {"error": f"Inga professioner hittades för kultur: {kultur}"}
        
        # Slå 1d100 för profession
        roll = random.randint(1, 100)
        
        # Hitta rätt resultat
        for range_key, range_data in ranges.items():
            if self._is_roll_in_range(roll, range_key):
                profession = range_data.get('profession', 'Okänd')
                skills = range_data.get('skills', [])
                special_rule = range_data.get('special_rule', '')
                skill_bonus = culture_table.get('skill_bonus', '1d6+1')
                
                return {
                    'roll': roll,
                    'profession': profession,
                    'skills': skills,
                    'skill_bonus': skill_bonus,
                    'special_rule': special_rule,
                    'table_title': culture_table.get('titel', kultur)
                }
        
        return {"error": f"Inget resultat för slag {roll} i {kultur}"}
    
    def generate_family_special_tables(self, race: str, kultur: str, session: CharacterSession = None) -> Dict[str, Any]:
        """Genererar familjetabeller för specialegenskaper"""
        # Kontrollera om det är Thalamur Thalasker Medborgare
        if session and session.data.get('thalamur_special') == 'thalasker_medborgare':
            return self.generate_thalask_family_table(session)
        
        # Standard familjetabeller för andra raser/kulturer (placeholder)
        return {
            'economic_status': 'Genomsnittlig ekonomi',
            'family_trait': 'Familjen är känd för sin hederlighet',
            'note': 'Standard familjetabeller implementeras senare'
        }
    
    def generate_thalask_family_table(self, session: CharacterSession) -> Dict[str, Any]:
        """Genererar Thalaskisk familjetabell för Medborgare"""
        # Ladda Thalaskisk familjetabell om inte redan laddad
        if not self.thalask_family_data:
            try:
                with open('data/character_tables/familj/familj_thalask.json', 'r', encoding='utf-8') as f:
                    self.thalask_family_data = json.load(f)
            except FileNotFoundError:
                return {"error": "Kunde inte ladda familj_thalask.json"}
        
        family_table = self.thalask_family_data.get('familjetabeller', {}).get('thalasker_medborgare', {})
        if not family_table:
            return {"error": "Thalasker Medborgare tabell hittades inte"}
        
        # Slå 1d100 på tabellen
        roll = random.randint(1, 100)
        ranges = family_table.get('ranges', {})
        
        for range_key, range_data in ranges.items():
            if self._is_roll_in_range(roll, range_key):
                result = {
                    'roll': roll,
                    'result_key': range_data.get('result', ''),
                    'description': range_data.get('description', ''),
                    'table_title': family_table.get('titel', 'Thalaskisk Familj'),
                    'source': 'familj_thalask.json'
                }
                
                # Hantera subtabeller
                if range_data.get('has_subtable') and 'subtable' in range_data:
                    subtable_result = self.roll_on_subtable(range_data['subtable'])
                    result['subtable_result'] = subtable_result
                
                # Hantera special rules
                special_rule = range_data.get('special_rule', '')
                if special_rule:
                    result['special_rule'] = special_rule
                    result = self.apply_thalask_special_rule(result, special_rule, session)
                
                # Hantera skill bonuses
                skill_bonus = range_data.get('skill_bonus', '')
                if skill_bonus:
                    result['skill_bonus'] = skill_bonus
                    self.apply_skill_bonus_to_session(session, skill_bonus)
                
                return result
        
        return {"error": f"Inget resultat för slag {roll} i Thalaskisk familjetabell"}
    
    def apply_thalask_special_rule(self, result: Dict[str, Any], special_rule: str, session: CharacterSession) -> Dict[str, Any]:
        """Applicerar specialregler från Thalaskisk familjetabell"""
        if special_rule == 'roll_on_formogenhet_and_egendom_tables':
            # Mycket rik familj - extra slag på förmögenhet och egendom
            result['extra_rolls'] = {
                'formogenhet': 'Gratis slag på förmögenhet-tabellen',
                'egendom': 'Gratis slag på egendom-tabellen',
                'note': 'Familjen äger egendomen, rollpersonen äger förmögenheten'
            }
        elif special_rule == 'roll_on_overnaturliga_egenskaper_r1-37':
            # Adopterad med övernaturliga förmågor
            result['supernatural_ability'] = 'Slå på Övernaturliga egenskaper (R1-37)'
        elif special_rule == 'giftermal_svarare_ob2t6':
            # Ärftlig sjukdom - svårare giftermål
            result['marriage_penalty'] = 'Giftermål två nivåer svårare (+Ob2T6)'
        elif special_rule == 'roll_twice_and_combine':
            # Slå två gånger och kombinera resultaten
            second_roll = self.generate_thalask_family_table(session)
            result['second_result'] = second_roll
        
        return result
    
    def apply_skill_bonus_to_session(self, session: CharacterSession, skill_bonus: str):
        """Applicerar färdighetsbonus från familjetabell till session"""
        # Spara färdighetsbonus för senare användning
        if 'familj_skill_bonuses' not in session.data:
            session.data['familj_skill_bonuses'] = []
        
        session.data['familj_skill_bonuses'].append({
            'source': 'Thalaskisk familjetabell',
            'bonus': skill_bonus
        })
        self.save_session(session)
    
    def roll_on_subtable(self, subtable: Dict[str, Any]) -> Dict[str, Any]:
        """Slår på en subtabell"""
        roll = random.randint(1, 100)
        ranges = subtable.get('ranges', {})
        
        for range_key, range_data in ranges.items():
            if self._is_roll_in_range(roll, range_key):
                return {
                    'roll': roll,
                    'result_key': range_data.get('result', ''),
                    'description': range_data.get('description', ''),
                    'special_rule': range_data.get('special_rule', '')
                }
        
        return {"error": f"Inget subtable-resultat för slag {roll}"}
    
    def generate_race_specific_family(self, race: str, age: int) -> Dict[str, Any]:
        """Genererar rasspecifika familj-aspekter"""
        race_specific = {}
        
        # ALV-SPECIFIKT: Hushåll + Mentor
        if race.lower() in ['sanari', 'thism', 'kiriya', 'henea', 'learam', 'pyar']:
            race_specific['household'] = self.generate_elf_household()
            race_specific['mentor'] = self.generate_elf_mentor_details()
        
        # DVÄRG-SPECIFIKT: Samhällsklass
        elif race.lower() in ['ghor', 'roghan', 'zolod', 'drezin']:
            race_specific['social_class'] = self.generate_dwarf_social_class()
        
        # TIRAK-SPECIFIKT: Klanstruktur (placeholder)
        elif race.lower() in ['marnakh', 'bazirk', 'frakk']:
            race_specific['clan_info'] = {'note': 'Tirak-klanstruktur implementeras senare'}
        
        return race_specific
    
    def generate_elf_household(self) -> Dict[str, Any]:
        """Genererar alv-hushåll med färdighetsbonus"""
        # Enkelt exempel - detta skulle läsas från tabeller
        households = [
            {'name': 'Aethel', 'skills': ['etickett', 'bokhållning']},
            {'name': 'Catharion', 'skills': ['etickett', 'bokhållning']},  
            {'name': 'Dorthann', 'skills': ['hantverk', 'värdera']},
            {'name': 'Galindreth', 'skills': ['historia', 'språk']},
        ]
        
        selected = random.choice(households)
        return {
            'name': selected['name'],
            'skills': selected['skills'],
            'bonus': 'ob1T6+1'
        }
    
    def generate_elf_mentor_details(self) -> Dict[str, Any]:
        """Genererar alv-mentor med färdighetsbonus"""
        personalities = ['Allvarlig', 'Vänlig', 'Sträng', 'Vis', 'Excentrisk', 'Tålmodig']
        skills = ['besvärjelse', 'ockultism', 'bibliotekskunskap', 'historia']
        
        return {
            'personality': random.choice(personalities),
            'skills': random.sample(skills, 2),  # Välj 2 färdigheter
            'bonus': '1T6+4'
        }
    
    def generate_dwarf_social_class(self) -> Dict[str, Any]:
        """Genererar dvärg-samhällsklass med attributeffekter"""
        social_classes = [
            {'name': 'Grävare', 'attributes': {'STY': 1, 'PER': -1}},
            {'name': 'Hantverkare', 'attributes': {'BIL': 1, 'STY': 1}},
            {'name': 'Handelsman', 'attributes': {'PSY': 1, 'VIL': 1}},
            {'name': 'Krigaradel', 'attributes': {'STY': 2, 'VIL': 1}},
        ]
        
        selected = random.choice(social_classes)
        return {
            'name': selected['name'],
            'attribute_effects': selected['attributes']
        }
    
    async def display_complete_family(self, ctx, session: CharacterSession, complete_family: Dict[str, Any]):
        """Visar den kompletta familjebakgrunden som enhetliga embeds"""
        
        # Bygg komplett summary
        summary_parts = []
        
        # 1. GRUNDLÄGGANDE FAMILJ
        basic = complete_family.get('basic')
        if basic:
            basic_summary = self._format_family_dict_summary(basic)
            summary_parts.append("📅 **GRUNDLÄGGANDE FAMILJ**")
            summary_parts.append(basic_summary)
        
        # 2. FAMILJENS HUVUDNÄRING
        profession = complete_family.get('profession', {})
        if profession and 'profession' in profession:
            summary_parts.append(f"\n💼 **FAMILJENS HUVUDNÄRING**")
            summary_parts.append(f"Familjen arbetar som **{profession['profession']}** (Slag: {profession['roll']})")
            if profession.get('skills'):
                skills_text = ", ".join(profession['skills'])
                summary_parts.append(f"Färdigheter: {skills_text} (Bonus: {profession.get('skill_bonus', '1d6+1')})")
            if profession.get('special_rule'):
                summary_parts.append(f"Specialregel: {profession['special_rule']}")
        
        # 2.5. THALASKISKA FAMILJETABELLER
        special = complete_family.get('special', {})
        if special and special.get('source') == 'familj_thalask.json':
            summary_parts.append(f"\n🏛️ **THALASKISK FAMILJ**")
            summary_parts.append(f"**{special.get('table_title', 'Thalaskisk Familj')}** (Slag: {special.get('roll', '?')})")
            
            # Huvudresultat
            result_key = special.get('result_key', '').replace('_', ' ').title()
            summary_parts.append(f"**{result_key}**")
            summary_parts.append(special.get('description', ''))
            
            # Subtabell-resultat
            if 'subtable_result' in special:
                subtable = special['subtable_result']
                subtable_key = subtable.get('result_key', '').replace('_', ' ').title()
                summary_parts.append(f"└── **{subtable_key}** (Underslag: {subtable.get('roll', '?')})")
                summary_parts.append(f"    {subtable.get('description', '')}")
            
            # Specialregler
            if 'extra_rolls' in special:
                extra = special['extra_rolls']
                summary_parts.append(f"**Specialeffekt:** {extra.get('note', '')}")
                summary_parts.append(f"• {extra.get('formogenhet', '')}")
                summary_parts.append(f"• {extra.get('egendom', '')}")
            
            if 'supernatural_ability' in special:
                summary_parts.append(f"**Övernaturlig förmåga:** {special['supernatural_ability']}")
            
            if 'marriage_penalty' in special:
                summary_parts.append(f"**Giftermålseffekt:** {special['marriage_penalty']}")
            
            # Andra slag (från "slå två gånger")
            if 'second_result' in special:
                second = special['second_result']
                if not second.get('error'):
                    second_key = second.get('result_key', '').replace('_', ' ').title()
                    summary_parts.append(f"\n**Ytterligare resultat:** {second_key}")
                    summary_parts.append(second.get('description', ''))
            
            # Färdighetsbonus
            if 'skill_bonus' in special:
                summary_parts.append(f"**Färdighetsbonus:** {special['skill_bonus']}")
        
        # 3. RASSPECIFIKA TILLÄGG
        race_specific = complete_family.get('race_specific', {})
        if race_specific:
            summary_parts.append(f"\n🏛️ **RASSPECIFIKA EGENSKAPER**")
            
            # Alv-hushåll
            if 'household' in race_specific:
                household = race_specific['household']
                summary_parts.append(f"Hushåll: **{household['name']}**")
                skills_text = ", ".join(household['skills'])
                summary_parts.append(f"Hushållsfärdigheter: {skills_text} ({household['bonus']})")
            
            # Alv-mentor
            if 'mentor' in race_specific:
                mentor = race_specific['mentor']
                skills_text = ", ".join(mentor['skills'])
                summary_parts.append(f"Mentor: **{mentor['personality']} personlighet**")
                summary_parts.append(f"Mentorfärdigheter: {skills_text} ({mentor['bonus']})")
            
            # Dvärg-samhällsklass
            if 'social_class' in race_specific:
                social = race_specific['social_class']
                summary_parts.append(f"Samhällsklass: **{social['name']}**")
                attr_effects = []
                for attr, mod in social['attribute_effects'].items():
                    attr_effects.append(f"{attr}{mod:+d}")
                summary_parts.append(f"Attributeffekter: {', '.join(attr_effects)}")
        
        # Skapa final summary
        full_summary = "\n".join(summary_parts)
        
        # Dela upp i embeds för enhetlig formatering
        await self.send_family_summary_embeds(ctx, session, full_summary, complete_family)
    
    async def send_family_summary_embeds(self, ctx, session: CharacterSession, summary: str, complete_family: Dict[str, Any]):
        """Skickar familjebakgrund som enhetliga embeds"""
        max_length = 1800
        
        chunks = [summary[i:i + max_length] 
                 for i in range(0, len(summary), max_length)]
        
        for i, chunk in enumerate(chunks):
            if i == 0 and len(chunks) == 1:
                # Bara en chunk - med titel och valalternativ
                embed = self.embed_factory.admin_message(
                    session.user_id, 
                    "👨‍👩‍👧‍👦 Steg 9/32: Komplett Familjebakgrund", 
                    chunk
                )
                embed.add_field(
                    name="📋 Vad vill du göra?",
                    value="`!chargen fortsätt` - Fortsätt med denna familjebakgrund\n" +
                          "`!chargen ändra` - Generera ny familjebakgrund",
                    inline=False
                )
            elif i == 0:
                # Första chunken av flera - bara med titel
                embed = self.embed_factory.admin_message(
                    session.user_id, 
                    "👨‍👩‍👧‍👦 Steg 9/32: Komplett Familjebakgrund", 
                    chunk
                )
            elif i == len(chunks) - 1:
                # Sista chunken av flera - med valalternativ
                embed = self.embed_factory.admin_message(
                    session.user_id, 
                    "Familjebakgrund (slutdel)", 
                    chunk
                )
                embed.add_field(
                    name="📋 Vad vill du göra?",
                    value="`!chargen fortsätt` - Fortsätt med denna familjebakgrund\n" +
                          "`!chargen ändra` - Generera ny familjebakgrund",
                    inline=False
                )
            else:
                # Mellan-chunkar
                embed = self.embed_factory.admin_message(
                    session.user_id, 
                    "Familjebakgrund (fortsättning)", 
                    chunk
                )
            
            await ctx.send(embed=embed)
        
        # Spara kompletta familjedata för bekräftelse
        session.temp_data = {
            'komplett_familjebakgrund': complete_family,
            'awaiting_family_confirmation': True
        }
        self.save_session(session)
    
    async def apply_complete_family_benefits(self, session: CharacterSession):
        """Applicerar alla färdighetsbonus och attributeffekter från kompletta familjebakgrunden"""
        
        family_data = session.data.get('komplett_familjebakgrund', {})
        
        # Initiera tracking för benefits
        if 'färdigheter' not in session.data:
            session.data['färdigheter'] = {}
        if 'attribut_bonusar' not in session.data:
            session.data['attribut_bonusar'] = {}
        
        # 1. PROFESSION BENEFITS (från huvudnäring)
        profession = family_data.get('profession', {})
        if profession and 'skills' in profession:
            skill_bonus = profession.get('skill_bonus', '1d6+1')
            for skill in profession['skills']:
                if skill.startswith('1 valfri'):
                    # Hantera valfria färdigheter senare
                    continue
                bonus_value = self._roll_dice_string(skill_bonus)
                current = session.data['färdigheter'].get(skill, 0)
                session.data['färdigheter'][skill] = current + bonus_value
        
        # 2. RASSPECIFIKA BENEFITS  
        race_specific = family_data.get('race_specific', {})
        
        # Alv-hushåll färdigheter
        if 'household' in race_specific:
            household = race_specific['household']
            for skill in household.get('skills', []):
                bonus = random.randint(1, 6) + 1  # ob1T6+1
                current = session.data['färdigheter'].get(skill, 0)
                session.data['färdigheter'][skill] = current + bonus
        
        # Alv-mentor färdigheter
        if 'mentor' in race_specific:
            mentor = race_specific['mentor']
            for skill in mentor.get('skills', []):
                bonus = random.randint(1, 6) + 4  # 1T6+4
                current = session.data['färdigheter'].get(skill, 0)
                session.data['färdigheter'][skill] = current + bonus
        
        # Dvärg-samhällsklass attribut
        if 'social_class' in race_specific:
            social_class = race_specific['social_class']
            for attr, modifier in social_class.get('attribute_effects', {}).items():
                current = session.data['attribut_bonusar'].get(attr, 0)
                session.data['attribut_bonusar'][attr] = current + modifier
        
        # Spara alla ändringar
        self.save_session(session)
    
    def _roll_dice_string(self, dice_str: str) -> int:
        """Enkelt tärningsslag för benefit-beräkning"""
        try:
            if 't6' in dice_str.lower():
                return self.table_processor._roll_eon_dice(dice_str)
            elif dice_str == '1d6+1':
                return random.randint(1, 6) + 1
            else:
                # Fallback för enkla värden
                if '+' in dice_str:
                    return int(dice_str.replace('+', ''))
                return int(dice_str)
        except:
            return 1  # Säker fallback
    
    def _is_roll_in_range(self, roll: int, range_str: str) -> bool:
        """Kontrollerar om ett tärningsslag ligger inom ett intervall"""
        try:
            range_str = str(range_str).strip()
            if "-" in range_str: 
                start, end = map(int, range_str.split("-"))
                return start <= roll <= end
            else: 
                return roll == int(range_str)
        except (ValueError, AttributeError): 
            return False
    
    def calculate_background_rolls(self, race: str, age: int, attribute_sum: int) -> int:
        """Beräknar antal bakgrundslag (samma logik som character_creation.py)"""
        base_rolls = self.get_base_rolls_for_race(race)
        total_rolls = base_rolls
        
        # Attributsumma bonus
        if attribute_sum < 70: 
            total_rolls += 2
        elif 71 <= attribute_sum <= 85: 
            total_rolls += 1
        
        # Åldersbonus
        if 31 <= age <= 45: total_rolls += 1
        elif 46 <= age <= 60: total_rolls += 2
        elif 61 <= age <= 80: total_rolls += 3
        elif 81 <= age <= 100: total_rolls += 4
        elif age > 100: total_rolls += 5
        
        return total_rolls
    
    def get_base_rolls_for_race(self, race: str) -> int:
        """Returnerar grundantal bakgrundslag för olika folkslag"""
        base_rolls = {
            "vanarer": 7, "cirefalier": 6, "adasier": 7, "darkener": 7, "lalaster": 7,
            "misslor": 4,
            "ghor": 5, "roghan": 5, "zolod": 5, "drezin": 5,  # dvärgar
            "marnakh": 5, "bazirk": 5, "frakk": 5,  # tiraker  
            "sanari": 5, "thism": 5, "kiriya": 5, "henea": 5, "learam": 5, "pyar": 5  # alver
        }
        
        race_lower = race.lower()
        return base_rolls.get(race_lower, 7)  # Default för människor
    
    def _convert_family_background_to_dict(self, family_bg) -> Dict[str, Any]:
        """Konverterar FamilyBackground dataclass till dict för JSON-serialisering"""
        try:
            # Konvertera huvudobjektet till dict
            result = {
                'birth_info': family_bg.birth_info,
                'family_special': family_bg.family_special,
                'mentor_info': family_bg.mentor_info
            }
            
            # Konvertera syskon-lista
            result['siblings'] = []
            for sibling in family_bg.siblings:
                result['siblings'].append({
                    'gender': sibling.gender,
                    'age': sibling.age,
                    'relationship': sibling.relationship,
                    'is_illegitimate': sibling.is_illegitimate
                })
            
            # Konvertera föräldrar
            result['father'] = {
                'status': family_bg.father.status,
                'age': family_bg.father.age,
                'death_cause': family_bg.father.death_cause
            }
            
            result['mother'] = {
                'status': family_bg.mother.status,
                'age': family_bg.mother.age,
                'death_cause': family_bg.mother.death_cause
            }
            
            return result
            
        except Exception as e:
            # Fallback - returnera grundläggande info
            print(f"Varning: Kunde inte konvertera FamilyBackground: {e}")
            return {
                'birth_info': str(getattr(family_bg, 'birth_info', 'Okänd födelseinformation')),
                'siblings': [],
                'father': {'status': 'okänd'},
                'mother': {'status': 'okänd'}, 
                'family_special': str(getattr(family_bg, 'family_special', 'Ingen specialinformation')),
                'mentor_info': getattr(family_bg, 'mentor_info', None)
            }
    
    def _format_family_dict_summary(self, family_dict: Dict[str, Any]) -> str:
        """Formaterar familje-dict till läsbar text"""
        summary_parts = []
        
        # Födelseinformation
        if family_dict.get('birth_info'):
            summary_parts.append(f"🎂 **Födelse:** {family_dict['birth_info']}")
        
        # Syskon
        siblings = family_dict.get('siblings', [])
        if siblings:
            sibling_counts = {}
            for sibling in siblings:
                key = f"{sibling['relationship']} {sibling['gender']}"
                sibling_counts[key] = sibling_counts.get(key, 0) + 1
            
            sibling_text = []
            for desc, count in sibling_counts.items():
                if count == 1:
                    sibling_text.append(f"{count} {desc}")
                else:
                    # Plural form
                    if 'bror' in desc:
                        sibling_text.append(f"{count} {desc.replace('bror', 'bröder')}")
                    elif 'syster' in desc:
                        sibling_text.append(f"{count} {desc.replace('syster', 'systrar')}")
                    else:
                        sibling_text.append(f"{count} {desc}")
            
            summary_parts.append(f"👥 **Syskon:** {', '.join(sibling_text)}")
        
        # Föräldrar
        father = family_dict.get('father', {})
        mother = family_dict.get('mother', {})
        if father or mother:
            parent_info = []
            if father.get('status') == 'lever' and mother.get('status') == 'lever':
                parent_info.append("båda lever")
                if father.get('age') and mother.get('age'):
                    parent_info.append(f"(far {father['age']} år, mor {mother['age']} år)")
            else:
                if father.get('status'):
                    parent_info.append(f"far: {father['status']}")
                if mother.get('status'):
                    parent_info.append(f"mor: {mother['status']}")
            
            summary_parts.append(f"👨‍👩‍👧‍👦 **Föräldrar:** {', '.join(parent_info)}")
        
        # Familjespecialitet
        if family_dict.get('family_special'):
            summary_parts.append(f"🏠 **Familjen:** {family_dict['family_special']}")
        
        # Alv-mentor info
        if family_dict.get('mentor_info'):
            summary_parts.append(f"🧙‍♂️ **Mentor:** {family_dict['mentor_info']}")
        
        return "\n".join(summary_parts)
    
    async def step_family_tables(self, ctx, session: CharacterSession):
        """Steg 10: Family tables - Skipped, handled by family step"""
        await ctx.send("⏭️ Steg 10: Familjetabeller redan inkluderade i komplett familjebakgrund")
        
        # Automatically go to next step
        if self.next_step(session):
            await self.show_current_step(ctx, session)
    
    async def step_parents(self, ctx, session: CharacterSession):
        """Steg 11: Parents - Skipped, handled by family step"""  
        await ctx.send("⏭️ Steg 11: Föräldrar redan inkluderade i komplett familjebakgrund")
        
        # Automatically go to next step
        if self.next_step(session):
            await self.show_current_step(ctx, session)
    
    async def step_background_count(self, ctx, session: CharacterSession):
        """Steg 12: Background count - using modular system"""
        await self.background_step.execute(ctx, session)
    
    async def handle_bakgrundslag_antal_input(self, ctx, session: CharacterSession, input_text: str, *args):
        """Hanterar input för bakgrundslag-räkning - använder ny modul"""
        success, error = await self.background_step.handle_input(ctx, session, input_text, *args)
        if success:
            session.update_context()
            self.save_session(session)
            self.next_step(session)
            await self.show_current_step(ctx, session)
    
    async def step_main_background(self, ctx, session: CharacterSession):
        """Steg 13: Main background table - using modular system"""
        await self.background_step.execute(ctx, session)
    
    def has_placeable_background_rolls(self, session: CharacterSession) -> bool:
        """Kontrollerar om spelaren har ätt-baserade placeringsmöjligheter"""
        thalamur_att_data = session.data.get('thalamur_ätt_data')
        if not thalamur_att_data:
            return False
        
        bonusar = thalamur_att_data.get('bonusar', {})
        placera_slag = bonusar.get('placera_slag', [])
        return len(placera_slag) > 0
    
    async def handle_att_based_placement(self, ctx, session: CharacterSession, antal_slag: int):
        """Hanterar ätt-baserad placering av bakgrundslag"""
        thalamur_att_data = session.data.get('thalamur_ätt_data', {})
        bonusar = thalamur_att_data.get('bonusar', {})
        placera_slag = bonusar.get('placera_slag', [])
        att_namn = thalamur_att_data.get('titel', 'Okänd ätt')
        
        embed = self.embed_factory.admin_message(
            session.user_id, 
            "🎯 Steg 13/32: Ätt-baserad Bakgrundslagplacering", 
            f"Som medlem av **{att_namn}** kan du placera vissa av dina {antal_slag} bakgrundslag:"
        )
        
        # Visa tillgängliga placeringar
        placement_text = []
        for i, kategori in enumerate(placera_slag, 1):
            kategori_display = kategori.replace('_', ' ').title()
            placement_text.append(f"{i}. **{kategori_display}**")
        
        embed.add_field(
            name="🏛️ Tillgängliga placeringar:",
            value="\n".join(placement_text),
            inline=False
        )
        
        embed.add_field(
            name="📋 Ditt val:",
            value=f"`!chargen placera` - Välj var du vill placera slag\n" +
                  f"`!chargen slumpmässigt` - Slå alla slag slumpmässigt",
            inline=False
        )
        
        embed.set_footer(text="Ätt-baserad placering ger dig mer kontroll över din karaktärs bakgrund")
        await ctx.send(embed=embed)
        
        # Spara data för val
        session.temp_data = {
            'placement_mode': True,
            'total_rolls': antal_slag,
            'available_placements': placera_slag,
            'placed_rolls': [],
            'remaining_rolls': antal_slag
        }
        self.save_session(session)
    
    async def perform_random_background_rolls(self, ctx, session: CharacterSession, antal_slag: int):
        """Utför standard slumpmässiga bakgrundslag"""
        # Ladda huvudbakgrundstabellen
        background_table = self.load_huvudbakgrundstabell()
        if not background_table:
            await ctx.send("❌ Fel: Kunde inte ladda huvudbakgrundstabellen.")
            return
        
        await ctx.send(f"🎲 Slår {antal_slag} gånger på huvudbakgrundstabellen...")
        
        # Utför alla slag
        results = []
        for i in range(antal_slag):
            roll = random.randint(1, 100)
            result = self.find_background_result(background_table, roll)
            
            result_data = {
                'roll': roll,
                'result_key': result['result'],
                'description': result['description'],
                'roll_number': i + 1
            }
            results.append(result_data)
        
        # Spara resultaten
        session.data['huvudbakgrund_results'] = results
        self.save_session(session)
        
        # Visa resultaten
        await self.display_background_results(ctx, session, results)
    
    async def handle_huvudbakgrund_input(self, ctx, session: CharacterSession, input_text: str, *args):
        """Hanterar input för huvudbakgrundstabellen-steget - använder ny modul"""
        success, error = await self.background_step.handle_input(ctx, session, input_text, *args)
        if success:
            session.update_context()
            self.save_session(session)
            self.next_step(session)
            await self.show_current_step(ctx, session)
    
    async def handle_placement_input(self, ctx, session: CharacterSession, input_text: str):
        """Hanterar input för ätt-baserad placering"""
        current_phase = session.temp_data.get('current_phase', 'initial')
        
        if current_phase == 'initial':
            if input_text in ['placera', 'place']:
                await self.start_placement_process(ctx, session)
            elif input_text in ['slumpmässigt', 'random', 'slumpmassigt']:
                await ctx.send("🎲 Väljer att slå alla slag slumpmässigt...")
                antal_slag = session.temp_data.get('total_rolls', 0)
                session.temp_data.clear()
                self.save_session(session)
                await self.perform_random_background_rolls(ctx, session, antal_slag)
            else:
                await ctx.send("❌ Ogiltigt val. Använd:\n`!chargen placera` - Börja placera slag\n`!chargen slumpmässigt` - Slå alla slag slumpmässigt")
        
        elif current_phase == 'selecting_category':
            await self.handle_category_selection(ctx, session, input_text)
    
    async def start_placement_process(self, ctx, session: CharacterSession):
        """Startar processen för att placera bakgrundslag"""
        available_placements = session.temp_data.get('available_placements', [])
        remaining_rolls = session.temp_data.get('remaining_rolls', 0)
        
        if remaining_rolls <= 0:
            await ctx.send("✅ Alla slag har placerats! Fortsätter till nästa steg...")
            # Samla alla placerade slag och utför dem
            await self.execute_placed_rolls(ctx, session)
            return
        
        embed = self.embed_factory.admin_message(
            session.user_id, 
            "🎯 Placera Bakgrundslag", 
            f"Du har **{remaining_rolls}** slag kvar att placera."
        )
        
        # Visa tillgängliga kategorier
        placement_text = []
        for i, kategori in enumerate(available_placements, 1):
            kategori_display = kategori.replace('_', ' ').title()
            placement_text.append(f"`!chargen {i}` - **{kategori_display}**")
        
        embed.add_field(
            name="🏛️ Välj kategori att placera slag på:",
            value="\n".join(placement_text),
            inline=False
        )
        
        embed.add_field(
            name="⚡ Alternativ:",
            value="`!chargen slumpmässigt` - Slå resterande slag slumpmässigt\n`!chargen klar` - Avsluta placering (om alla placerade)",
            inline=False
        )
        
        await ctx.send(embed=embed)
        
        # Uppdatera läge
        session.temp_data['current_phase'] = 'selecting_category'
        self.save_session(session)
    
    async def handle_category_selection(self, ctx, session: CharacterSession, input_text: str):
        """Hanterar kategori-val för placering"""
        available_placements = session.temp_data.get('available_placements', [])
        
        try:
            choice_num = int(input_text)
            if 1 <= choice_num <= len(available_placements):
                selected_category = available_placements[choice_num - 1]
                await self.place_roll_in_category(ctx, session, selected_category)
                return
        except ValueError:
            pass
        
        if input_text in ['slumpmässigt', 'random']:
            remaining_rolls = session.temp_data.get('remaining_rolls', 0)
            await ctx.send(f"🎲 Slår resterande {remaining_rolls} slag slumpmässigt...")
            await self.execute_remaining_random_rolls(ctx, session)
        elif input_text in ['klar', 'done']:
            if session.temp_data.get('remaining_rolls', 0) <= 0:
                await self.execute_placed_rolls(ctx, session)
            else:
                await ctx.send("❌ Du har fortfarande slag kvar att placera!")
        else:
            await ctx.send("❌ Ogiltigt val. Välj ett nummer eller använd 'slumpmässigt'/'klar'.")
    
    async def place_roll_in_category(self, ctx, session: CharacterSession, category: str):
        """Placerar ett slag i vald kategori"""
        placed_rolls = session.temp_data.get('placed_rolls', [])
        remaining_rolls = session.temp_data.get('remaining_rolls', 0)
        
        # Mappa kategori till huvudbakgrundstabellens resultat
        category_mapping = {
            'förmögenhet': 'förmögenhet',
            'föremål': 'föremål_ägodelar', 
            'egendom': 'egendom',
            'mentala_egenskaper': 'mentala_egenskaper',
            'mentala egenskaper': 'mentala_egenskaper',  # Hantera mellanslag-variant
            'fysiska_egenskaper': 'fysiska_egenskaper',
            'fysiska egenskaper': 'fysiska_egenskaper',  # Hantera mellanslag-variant
            'övernaturliga_egenskaper': 'övernaturliga_egenskaper',
            'övernaturliga egenskaper': 'övernaturliga_egenskaper'  # Hantera mellanslag-variant
        }
        
        table_result = category_mapping.get(category)
        if not table_result:
            await ctx.send(f"❌ Okänd kategori: {category}")
            return
        
        # Lägg till placering
        placed_rolls.append({
            'category': category,
            'table_result': table_result,
            'roll_number': len(placed_rolls) + 1,
            'placed': True
        })
        
        remaining_rolls -= 1
        category_display = category.replace('_', ' ').title()
        
        await ctx.send(f"✅ Placerade slag #{len(placed_rolls)} på **{category_display}**")
        
        # Uppdatera session
        session.temp_data['placed_rolls'] = placed_rolls
        session.temp_data['remaining_rolls'] = remaining_rolls
        self.save_session(session)
        
        # Fortsätt placeringsprocessen
        if remaining_rolls > 0:
            await self.start_placement_process(ctx, session)
        else:
            await ctx.send("✅ Alla slag placerade! Utför nu alla slag...")
            await self.execute_placed_rolls(ctx, session)
    
    async def execute_placed_rolls(self, ctx, session: CharacterSession):
        """Utför alla placerade slag"""
        placed_rolls = session.temp_data.get('placed_rolls', [])
        
        if not placed_rolls:
            await ctx.send("❌ Inga slag att utföra!")
            return
        
        results = []
        
        # Utför alla placerade slag
        for roll_data in placed_rolls:
            result_data = {
                'roll': 'Placerat',
                'result_key': roll_data['table_result'],
                'description': f"Placerat slag på {roll_data['category'].replace('_', ' ').title()}",
                'roll_number': roll_data['roll_number'],
                'placed': True
            }
            results.append(result_data)
        
        # Spara resultaten
        session.data['huvudbakgrund_results'] = results
        session.temp_data.clear()
        self.save_session(session)
        
        # Visa resultaten
        await self.display_background_results(ctx, session, results)
    
    async def execute_remaining_random_rolls(self, ctx, session: CharacterSession):
        """Utför resterande slag slumpmässigt"""
        placed_rolls = session.temp_data.get('placed_rolls', [])
        remaining_rolls = session.temp_data.get('remaining_rolls', 0)
        
        # Ladda huvudbakgrundstabellen
        background_table = self.load_huvudbakgrundstabell()
        if not background_table:
            await ctx.send("❌ Fel: Kunde inte ladda huvudbakgrundstabellen.")
            return
        
        results = []
        
        # Lägg till redan placerade slag
        for roll_data in placed_rolls:
            result_data = {
                'roll': 'Placerat',
                'result_key': roll_data['table_result'],
                'description': f"Placerat slag på {roll_data['category'].replace('_', ' ').title()}",
                'roll_number': roll_data['roll_number'],
                'placed': True
            }
            results.append(result_data)
        
        # Utför resterande slumpmässiga slag
        for i in range(remaining_rolls):
            roll = random.randint(1, 100)
            result = self.find_background_result(background_table, roll)
            
            result_data = {
                'roll': roll,
                'result_key': result['result'],
                'description': result['description'],
                'roll_number': len(placed_rolls) + i + 1,
                'placed': False
            }
            results.append(result_data)
        
        # Spara resultaten
        session.data['huvudbakgrund_results'] = results
        session.temp_data.clear()
        self.save_session(session)
        
        # Visa resultaten
        await self.display_background_results(ctx, session, results)
    
    def load_huvudbakgrundstabell(self) -> Dict[str, Any]:
        """Laddar huvudbakgrundstabellen från JSON"""
        try:
            filepath = os.path.join(self.data_dir, 'huvudbakgrund.json')
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data['bakgrundstabeller']['huvudtabell']
        except Exception as e:
            print(f"Fel vid laddning av huvudbakgrundstabellen: {e}")
            return None
    
    def find_background_result(self, table: Dict[str, Any], roll: int) -> Dict[str, Any]:
        """Hittar resultat från huvudbakgrundstabellen baserat på slag"""
        ranges = table.get('ranges', {})
        
        for range_key, range_data in ranges.items():
            if self._is_roll_in_range(roll, range_key):
                return {
                    'result': range_data['result'],
                    'description': range_data['description']
                }
        
        # Fallback om inget hittas
        return {
            'result': 'okänt',
            'description': f'Okänt resultat för slag {roll}'
        }
    
    async def display_background_results(self, ctx, session: CharacterSession, results: List[Dict[str, Any]]):
        """Visar resultaten från huvudbakgrundstabellen"""
        embed = self.embed_factory.admin_message(
            session.user_id, 
            "🎲 Steg 13/32: Huvudbakgrundstabellen", 
            f"Resultat från {len(results)} slag:"
        )
        
        # Gruppera resultat för bättre visning
        result_groups = {}
        for result in results:
            key = result['result_key']
            if key not in result_groups:
                result_groups[key] = []
            result_groups[key].append(result)
        
        # Visa grupperade resultat
        for result_type, group_results in result_groups.items():
            if len(group_results) == 1:
                result = group_results[0]
                if result.get('placed'):
                    field_name = f"Slag {result['roll_number']}: {result['description']}"
                    field_value = f"🎯 **Placerat** → {result_type.replace('_', ' ').title()}"
                else:
                    field_name = f"Slag {result['roll_number']}: {result['description']}"
                    field_value = f"🎲 Slog {result['roll']} → {result_type.replace('_', ' ').title()}"
            else:
                placed_count = sum(1 for r in group_results if r.get('placed'))
                random_count = len(group_results) - placed_count
                
                field_name = f"{len(group_results)}x {group_results[0]['description']}"
                
                value_parts = []
                if placed_count > 0:
                    value_parts.append(f"🎯 {placed_count} placerade")
                if random_count > 0:
                    random_rolls = [r['roll'] for r in group_results if not r.get('placed')]
                    value_parts.append(f"🎲 {random_count} slumpmässiga ({', '.join(map(str, random_rolls))})")
                
                field_value = f"{' + '.join(value_parts)} → {result_type.replace('_', ' ').title()}"
            
            embed.add_field(
                name=field_name,
                value=field_value,
                inline=False
            )
        
        embed.add_field(
            name="📋 Nästa steg:",
            value="Fortsätt med `!chargen fortsätt` för att bearbeta bakgrundshändelserna",
            inline=False
        )
        
        await ctx.send(embed=embed)
    
    async def step_background_events(self, ctx, session: CharacterSession):
        """Steg 14: Background events - using modular system"""
        await self.background_step.execute(ctx, session)
    
    def get_table_display_name(self, table_type: str) -> str:
        """Returnerar ett läsbart namn för tabelltyper"""
        display_names = {
            'extra_slag_familj': 'Extra Slag på Familjetabeller',
            'fysiska_egenskaper': 'Fysiska Egenskaper',
            'mentala_egenskaper': 'Mentala Egenskaper',
            'övernaturliga_egenskaper': 'Övernaturliga Egenskaper',
            'nackdelar': 'Nackdelar',
            'föremål_ägodelar': 'Föremål & Ägodelar',
            'förmögenhet': 'Förmögenhet',
            'händelser': 'Händelser',
            'börd': 'Börd',
            'egendom': 'Egendom'
        }
        return display_names.get(table_type, table_type.replace('_', ' ').title())
    
    async def roll_specific_background_table(self, ctx, session: CharacterSession, result_type: str, original_result: Dict) -> Dict[str, Any]:
        """Slår på en specifik bakgrundstabell baserat på resultattyp"""
        table_mapping = {
            'fysiska_egenskaper': 'physical_traits.json',
            'mentala_egenskaper': 'mental_traits.json', 
            'övernaturliga_egenskaper': 'supernatural_trait.json',
            'nackdelar': 'disadvantages.json',
            'föremål_ägodelar': 'agodelar.json',
            'förmögenhet': 'formogenhet.json',
            'händelser': self.get_events_table_for_race(session),
            'börd': self.get_birth_table_for_race(session),
            'extra_slag_familj': 'familj/familj_ovr.json',
            'egendom': 'egendom.json'
        }
        
        table_file = table_mapping.get(result_type)
        if not table_file:
            return None
        
        try:
            # Ladda tabellen
            table_data = self.load_background_subtable(table_file)
            if not table_data:
                return None
            
            # Speciell hantering för egendomstabeller
            if result_type == 'egendom':
                return await self.roll_egendom_table(session, table_data, original_result)
            
            # Slå på tabellen
            roll = random.randint(1, 100)
            result_data = self.find_subtable_result_with_conditions(table_data, roll, session)
            
            return {
                'table_type': result_type,
                'table_file': table_file,
                'roll': roll,
                'result': result_data['description'],
                'result_key': result_data['result'],
                'original_main_roll': original_result
            }
            
        except Exception as e:
            print(f"Fel vid tabellslag för {result_type}: {e}")
            return None
    
    def get_events_table_for_race(self, session: CharacterSession) -> str:
        """Väljer händelsetabell baserat på ras"""
        race = session.data.get('folkslag', '').lower()
        
        # Specifika händelsetabeller för olika raser
        if any(x in race for x in ['sanari', 'thism', 'kiriya', 'henea', 'learam', 'pyar']):
            return 'handelser/alver_hand.json'
        elif 'thalask' in race:
            return 'handelser/thalask_hand.json'
        else:
            return 'handelser/ovriga_handelser.json'
    
    def get_birth_table_for_race(self, session: CharacterSession) -> str:
        """Väljer bördstabell baserat på ras/kultur"""
        race = session.data.get('folkslag', '').lower()
        kultur = session.data.get('kultur', '').lower()
        
        # Specifika börd-tabeller baserat på kultur/civilisation
        if 'cirefalier' in race:
            return 'bord/bord_cirefalier.json'
        elif 'thalask' in race:
            return 'bord/bord_thalask.json'
        elif 'primitiv' in kultur:
            return 'bord/bord_primitiva.json'
        elif 'asharier' in race:
            return 'bord/bord_asharier.json'
        else:
            return 'bord/bord_ovr_civ.json'  # Övrig civiliserad
    
    def load_background_subtable(self, filename: str) -> Dict[str, Any]:
        """Laddar en bakgrundsundertabell från fil"""
        try:
            filepath = os.path.join(self.data_dir, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Fel vid laddning av {filename}: {e}")
            return None
    
    def find_subtable_result(self, table_data: Dict[str, Any], roll: int) -> str:
        """Hittar resultat från en undertabell"""
        # Hantera EON tabellstruktur med bakgrundstabeller
        if 'bakgrundstabeller' in table_data:
            # Leta efter första undertabellen i bakgrundstabeller
            for section_name, section_data in table_data['bakgrundstabeller'].items():
                if 'ranges' in section_data:
                    ranges = section_data['ranges']
                    for range_key, range_data in ranges.items():
                        if self._is_roll_in_range(roll, range_key):
                            # Returnera antingen description eller result, description är förstaval
                            return range_data.get('description', range_data.get('result', f'Resultat för slag {roll}'))
        
        # Hantera familjetabeller struktur
        if 'familjetabeller' in table_data:
            # Leta efter första undertabellen i familjetabeller
            for section_name, section_data in table_data['familjetabeller'].items():
                if 'ranges' in section_data:
                    ranges = section_data['ranges']
                    for range_key, range_data in ranges.items():
                        if self._is_roll_in_range(roll, range_key):
                            # Returnera antingen description eller result, description är förstaval
                            return range_data.get('description', range_data.get('result', f'Resultat för slag {roll}'))
        
        # Hantera egendomstabeller struktur - behöver välja rätt undertabell baserat på kultur
        if 'egendomstabeller' in table_data:
            # Vi behöver bestämma vilken egendomstabell som ska användas
            # Detta kommer att hanteras av en separat metod som tar hänsyn till kultur/miljö
            return f"Egendom (behöver kultur-specifik hantering)"
        
        # Direkta ranges på rotnivån
        if 'ranges' in table_data:
            ranges = table_data['ranges']
            for range_key, range_data in ranges.items():
                if self._is_roll_in_range(roll, range_key):
                    if isinstance(range_data, dict):
                        return range_data.get('description', range_data.get('result', f'Resultat för slag {roll}'))
                    else:
                        return str(range_data)
        
        # Alternativ struktur - direkt nyckel-värde på rotnivå
        for key, value in table_data.items():
            if self._is_roll_in_range(roll, key):
                if isinstance(value, dict):
                    return value.get('description', value.get('result', str(value)))
                else:
                    return str(value)
        
        return f"Inget resultat för slag {roll}"
    
    async def show_background_result_with_options(self, ctx, session: CharacterSession, detailed_result: Dict, original_result: Dict):
        """Visar bakgrundsresultat med behåll/slå om-alternativ"""
        embed = self.embed_factory.admin_message(
            session.user_id, 
            f"🎯 Slag {session.data['current_background_index'] + 1}: {original_result['description']}", 
            f"Ursprungligt slag: {original_result['roll']} → {self.get_table_display_name(detailed_result['table_type'])}"
        )
        
        embed.add_field(
            name=f"🎲 Detaljerat slag (1d100: {detailed_result['roll']})",
            value=f"**{detailed_result['result']}**",
            inline=False
        )
        
        embed.add_field(
            name="📋 Vad vill du göra?",
            value="`!chargen fortsätt` - Fortsätt med detta resultat\n" +
                  "`!chargen slåom` - Slå om på samma tabell\n" +
                  "`!chargen hoppa` - Hoppa över detta slag",
            inline=False
        )
        
        # Spara temporärt resultat
        session.temp_data['current_detailed_result'] = detailed_result
        self.save_session(session)
        
        await ctx.send(embed=embed)
    
    async def advance_to_next_background_roll(self, ctx, session: CharacterSession):
        """Går vidare till nästa bakgrundslag"""
        old_index = session.data['current_background_index']
        session.data['current_background_index'] += 1
        new_index = session.data['current_background_index']
        session.temp_data.clear()
        self.save_session(session)
        
        # Debug
        
        # Visa nästa slag eller avsluta
        await self.step_background_events(ctx, session)
    
    async def show_final_background_summary(self, ctx, session: CharacterSession):
        """Visar slutlig sammanfattning av alla bakgrundsslag"""
        processed_results = session.data.get('processed_background_results', [])
        
        embed = self.embed_factory.admin_message(
            session.user_id, 
            "🏆 Steg 14/32: Bakgrundshändelser - Sammanfattning", 
            f"Alla {len(processed_results)} bakgrundsslag är nu bearbetade:"
        )
        
        for i, result in enumerate(processed_results, 1):
            embed.add_field(
                name=f"Slag {i}: {result.get('category', 'Okänt')}",
                value=f"🎲 {result.get('roll', 'N/A')} → {result.get('result', 'Inget resultat')}",
                inline=False
            )
        
        embed.add_field(
            name="📋 Nästa steg:",
            value="Fortsätt med `!chargen fortsätt` för att gå vidare till nästa fas",
            inline=False
        )
        
        await ctx.send(embed=embed)
    
    async def handle_bakgrundshändelser_input(self, ctx, session: CharacterSession, input_text: str, *args):
        """Hanterar input för bakgrundshändelser-steget - använder ny modul"""
        success, error = await self.background_step.handle_input(ctx, session, input_text, *args)
        if success:
            session.update_context()
            self.save_session(session)
            self.next_step(session)
            await self.show_current_step(ctx, session)
    
    async def step_final_summary(self, ctx, session: CharacterSession):
        """Steg 15: Character summary - using modular system"""
        await self.summary_step.execute(ctx, session)
        
        # End the session after summary is complete
        self.end_session(str(ctx.author.id))
    
    def collect_all_skill_bonuses(self, session: CharacterSession) -> Dict[str, List[Dict[str, str]]]:
        """Samlar alla färdighetsbonus från olika källor"""
        skill_bonuses = {}
        
        # 1. Från familjens huvudnäring (profession)
        family_data = session.data.get('komplett_familjebakgrund', {})
        profession = family_data.get('profession', {})
        if profession and 'skills' in profession:
            skill_bonus = profession.get('skill_bonus', '1d6+1')
            for skill in profession['skills']:
                if skill not in skill_bonuses:
                    skill_bonuses[skill] = []
                skill_bonuses[skill].append({
                    'source': 'Familjens huvudnäring',
                    'bonus': skill_bonus
                })
        
        # 2. Från rasspecifika egenskaper
        race_specific = family_data.get('race_specific', {})
        
        # Alv-hushåll
        if 'household' in race_specific:
            household = race_specific['household']
            if 'skills' in household:
                bonus = household.get('bonus', '1d6+1')
                for skill in household['skills']:
                    if skill not in skill_bonuses:
                        skill_bonuses[skill] = []
                    skill_bonuses[skill].append({
                        'source': f"Alv-hushåll ({household.get('name', 'Okänt')})",
                        'bonus': bonus
                    })
        
        # Alv-mentor
        if 'mentor' in race_specific:
            mentor = race_specific['mentor']
            if 'skills' in mentor:
                bonus = mentor.get('bonus', '1d6+4')
                for skill in mentor['skills']:
                    if skill not in skill_bonuses:
                        skill_bonuses[skill] = []
                    skill_bonuses[skill].append({
                        'source': 'Alv-mentor',
                        'bonus': bonus
                    })
        
        # 2.5. Från Thalaskiska familjetabeller
        thalask_bonuses = session.data.get('familj_skill_bonuses', [])
        for bonus_data in thalask_bonuses:
            source = bonus_data.get('source', 'Thalaskisk familj')
            bonus = bonus_data.get('bonus', '')
            
            # Parse bonus string för att hitta specifika färdigheter
            if 'sjunga_dansa_berattarkonst_musik' in bonus:
                skills = ['sjunga', 'dansa', 'berättarkonst', 'musik']
                for skill in skills:
                    if skill not in skill_bonuses:
                        skill_bonuses[skill] = []
                    skill_bonuses[skill].append({
                        'source': source,
                        'bonus': '1d6+4 enheter'
                    })
            elif 'etikett' in bonus:
                if 'etikett' not in skill_bonuses:
                    skill_bonuses['etikett'] = []
                skill_bonuses['etikett'].append({
                    'source': source,
                    'bonus': '1d6+2 enheter'
                })
            else:
                # Generisk bonus
                skill_bonuses.setdefault('Diverse Thalaskiska färdigheter', []).append({
                    'source': source,
                    'bonus': bonus
                })
        
        # 3. Från bakgrundshändelser (leta efter färdighetsrelaterade händelser)
        processed_results = session.data.get('processed_background_results', [])
        for result in processed_results:
            result_text = result.get('result', '').lower()
            
            # Leta efter vissa nyckelord som indikerar färdighetsbonus
            if 'färdighet' in result_text or 'enhet' in result_text:
                # Extrahera färdighet om möjligt (enkel implementation)
                category = result.get('category', 'Bakgrundshändelse')
                if 'skill_extracted' not in result:  # Undvik duplicering
                    skill_bonuses.setdefault('Diverse färdigheter', []).append({
                        'source': category,
                        'bonus': 'Varierar (se beskrivning)'
                    })
        
        # 4. Från lagrade färdigheter (om systemet har sparat dem)
        stored_skills = session.data.get('färdigheter', {})
        for skill, bonus_value in stored_skills.items():
            if skill not in skill_bonuses:
                skill_bonuses[skill] = []
            skill_bonuses[skill].append({
                'source': 'Applicerad bonus',
                'bonus': f'+{bonus_value}'
            })
        
        return skill_bonuses
    
    async def handle_sammanfattning_input(self, ctx, session: CharacterSession, input_text: str, *args):
        """Hanterar input för sammanfattning-steget (avslutar sessionen)"""
        await ctx.send("Karaktärsskapandet är slutfört! Använd `!chargen start` för att skapa en ny karaktär.")
    
    async def step_skills(self, ctx, session: CharacterSession):
        await ctx.send("🚧 Steg 17: Färdigheter - Kommer snart...")
    
    async def step_equipment(self, ctx, session: CharacterSession):
        await ctx.send("🚧 Steg 18: Utrustning - Kommer snart...")