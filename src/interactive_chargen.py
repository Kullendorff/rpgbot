"""
Interaktivt karaktärsskapande-system för EON Diceroller Bot
Hanterar steg-för-steg guided karaktärsskapande med sessions
"""

import json
import os
import random
import discord
from typing import Dict, List, Optional, Any, Union
from discord.ext import commands
import asyncio

class CharacterSession:
    """Hanterar en pågående karaktärsskapande-session för en användare"""
    
    def __init__(self, user_id: str, user_name: str):
        self.user_id = user_id
        self.user_name = user_name
        self.current_step = 1
        self.data = {}
        self.created_at = discord.utils.utcnow()
        
    def to_dict(self) -> Dict[str, Any]:
        """Konverterar sessionen till dictionary för serialisering"""
        return {
            'user_id': self.user_id,
            'user_name': self.user_name,
            'current_step': self.current_step,
            'data': self.data,
            'created_at': self.created_at.isoformat()
        }

class InteractiveCharacterCreator:
    """Huvudklass för interaktivt karaktärsskapande"""
    
    def __init__(self, data_dir: str = None):
        if data_dir is None:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(script_dir)
            self.data_dir = os.path.join(project_root, 'data', 'character_tables')
        else:
            self.data_dir = data_dir
            
        # Aktiva sessioner: user_id -> CharacterSession
        self.active_sessions: Dict[str, CharacterSession] = {}
        
        # Ladda data från befintliga filer
        self.load_data()
        
    def load_data(self):
        """Laddar alla nödvändiga data för karaktärsskapande"""
        try:
            # Ladda attributmodifierare
            attr_path = os.path.join(self.data_dir, 'folkslag', 'attribute_modifiers.json')
            with open(attr_path, 'r', encoding='utf-8') as f:
                self.attribute_modifiers = json.load(f)
                
            print("Laddade attributmodifierare för karaktärsskapande")
        except Exception as e:
            print(f"Fel vid laddning av karaktärsdata: {e}")
            self.attribute_modifiers = {}
    
    def get_countries_list(self) -> List[str]:
        """Hämtar lista över alla tillgängliga länder"""
        countries_dir = os.path.join(self.data_dir, 'landerhemort')
        if not os.path.exists(countries_dir):
            return []
            
        countries = []
        for filename in os.listdir(countries_dir):
            if filename.endswith('.txt'):
                country_name = filename[:-4]  # Ta bort .txt
                countries.append(country_name)
        
        return sorted(countries)
    
    def get_country_description(self, country_name: str) -> Optional[str]:
        """Hämtar beskrivning för ett specifikt land"""
        country_file = os.path.join(self.data_dir, 'landerhemort', f'{country_name}.txt')
        if not os.path.exists(country_file):
            return None
            
        try:
            with open(country_file, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"Fel vid läsning av {country_name}: {e}")
            return None
    
    def get_folkslag_list(self) -> List[str]:
        """Hämtar lista över alla tillgängliga folkslag"""
        folkslag_list = []
        
        # Lägg till alla från attribute_modifiers
        for category, races in self.attribute_modifiers.items():
            for race in races.keys():
                folkslag_list.append(race)
        
        return sorted(folkslag_list)
    
    def get_folkslag_description(self, folkslag: str) -> Optional[str]:
        """Hämtar beskrivning för ett specifikt folkslag"""
        # Försök hitta beskrivningsfil
        folkslag_file = os.path.join(self.data_dir, 'folkslag', 'humans', f'{folkslag}.txt')
        if os.path.exists(folkslag_file):
            try:
                with open(folkslag_file, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception as e:
                print(f"Fel vid läsning av {folkslag}: {e}")
        
        # Fallback: visa bara attributmodifierare
        for category, races in self.attribute_modifiers.items():
            if folkslag in races:
                mods = races[folkslag]
                if mods:
                    mod_text = ', '.join(f"{attr}: {'+' if mod >= 0 else ''}{mod}" for attr, mod in mods.items())
                    return f"**{folkslag.capitalize()}**\n\nAttributmodifierare: {mod_text}"
                else:
                    return f"**{folkslag.capitalize()}**\n\nInga attributmodifierare."
        
        return None
    
    def start_session(self, user_id: str, user_name: str) -> CharacterSession:
        """Startar en ny karaktärsskapande-session"""
        session