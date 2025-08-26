"""
Character Session Management

This module handles character creation sessions, including data storage,
context management, and session lifecycle.
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path

# Import från befintliga system
from eon_table_processor import CharacterContext, create_character_context


@dataclass
class CharacterSession:
    """Hanterar en pågående karaktärsskapande-session för en användare"""
    user_id: str
    current_step: int = 1
    max_steps: int = 32
    data: Dict[str, Any] = None
    temp_data: Dict[str, Any] = None  # Temporär data innan bekräftelse
    context: CharacterContext = None
    created_at: datetime = None
    
    def __post_init__(self):
        if self.data is None:
            self.data = {}
        if self.temp_data is None:
            self.temp_data = {}
        if self.context is None:
            self.context = CharacterContext()
        if self.created_at is None:
            self.created_at = datetime.now()
    
    def update_context(self):
        """Uppdaterar CharacterContext baserat på nuvarande session-data"""
        if 'folkslag' in self.data:
            self.context = create_character_context(
                folkslag=self.data['folkslag'],
                kultur=self.data.get('kultur'),
                social_class=self.data.get('social_class')
            )
            # Lägg till stam för alver om det finns
            if 'stam' in self.data:
                self.context.stam = self.data['stam']
            if 'location' in self.data:
                self.context.location = self.data['location']
    
    def to_dict(self) -> Dict[str, Any]:
        """Konverterar session till dictionary för serialisering"""
        return {
            'user_id': self.user_id,
            'current_step': self.current_step,
            'max_steps': self.max_steps,
            'data': self.data,
            'temp_data': self.temp_data,
            'created_at': self.created_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CharacterSession':
        """Skapar session från dictionary"""
        session = cls(
            user_id=data['user_id'],
            current_step=data['current_step'],
            max_steps=data.get('max_steps', 33),
            data=data.get('data', {}),
            temp_data=data.get('temp_data', {}),
            created_at=datetime.fromisoformat(data['created_at'])
        )
        session.update_context()
        return session
    
    @property
    def character_data(self) -> Dict[str, Any]:
        """Alias för data för kompatibilitet"""
        return self.data
    
    def get_step_progress(self) -> str:
        """Returnerar formaterad progress-sträng"""
        return f"Steg {self.current_step}/{self.max_steps}"
    
    def is_complete(self) -> bool:
        """Kontrollerar om sessionen är färdig"""
        return self.current_step > self.max_steps
    
    def increment_step(self) -> None:
        """Ökar current_step med 1"""
        self.current_step += 1
    
    def decrement_step(self) -> None:
        """Minskar current_step med 1"""
        if self.current_step > 1:
            self.current_step -= 1
    
    def set_step(self, step: int) -> None:
        """Sätter current_step till specifikt värde"""
        if 1 <= step <= self.max_steps + 1:
            self.current_step = step
    
    def clear_temp_data(self) -> None:
        """Rensar temporär data"""
        self.temp_data = {}
    
    def commit_temp_data(self) -> None:
        """Flyttar temporär data till permanent data"""
        if self.temp_data:
            self.data.update(self.temp_data)
            self.clear_temp_data()
            self.update_context()
    
    def save_to_file(self, directory: Path) -> None:
        """Sparar session till fil"""
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)
        
        filepath = directory / f"session_{self.user_id}.json"
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)
    
    @classmethod
    def load_from_file(cls, directory: Path, user_id: str) -> Optional['CharacterSession']:
        """Laddar session från fil"""
        filepath = Path(directory) / f"session_{user_id}.json"
        if not filepath.exists():
            return None
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return cls.from_dict(data)
        except (json.JSONDecodeError, KeyError, ValueError):
            return None
    
    def delete_file(self, directory: Path) -> None:
        """Tar bort sessionsfil"""
        filepath = Path(directory) / f"session_{self.user_id}.json"
        if filepath.exists():
            filepath.unlink()