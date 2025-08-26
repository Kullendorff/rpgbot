"""
Homeland Race Mapper Utility

This module provides intelligent mapping between homelands and their
common races, including percentage-based random generation and subtables.
"""

import json
import random
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path


class HomelandRaceMapper:
    """Maps homelands to their common races with intelligent filtering."""
    
    def __init__(self, data_dir: Optional[Path] = None):
        """
        Initialize the homeland race mapper.
        
        Args:
            data_dir: Optional data directory path
        """
        self.data_dir = data_dir or self._get_default_data_dir()
        self.homeland_races_data: Optional[Dict] = None
        self._load_data()
    
    def _get_default_data_dir(self) -> Path:
        """Get default data directory."""
        script_dir = Path(__file__).parent
        project_root = script_dir.parent.parent.parent
        return project_root / 'data' / 'character_tables'
    
    def _load_data(self) -> None:
        """Load homeland races data from JSON file."""
        homeland_races_file = self.data_dir / 'homeland_races.json'
        
        if not homeland_races_file.exists():
            print(f"Warning: Could not find {homeland_races_file}")
            self.homeland_races_data = {}
            return
        
        try:
            with open(homeland_races_file, 'r', encoding='utf-8') as f:
                self.homeland_races_data = json.load(f)
            print(f"Loaded race data for {len(self.homeland_races_data)} homelands")
        except Exception as e:
            print(f"Error loading homeland races data: {e}")
            self.homeland_races_data = {}
    
    def get_races_for_homeland(self, homeland: str) -> List[Dict[str, Any]]:
        """
        Get filtered list of races for a specific homeland.
        
        Args:
            homeland: The homeland name
            
        Returns:
            List of race dictionaries with name and details
        """
        if not self.homeland_races_data:
            return []
        
        homeland_data = self.homeland_races_data.get(homeland, [])
        races = []
        
        for race_entry in homeland_data:
            # Skip "Annat folkslag" from the displayed list
            if race_entry.get('folkslag') == 'Annat folkslag':
                continue
                
            race_info = {
                'name': race_entry.get('folkslag', 'Unknown'),
                'range': race_entry.get('range', ''),
                'has_subtable': 'subtable' in race_entry,
                'subtable': race_entry.get('subtable', [])
            }
            races.append(race_info)
        
        return races
    
    def get_unique_race_names(self, homeland: str) -> List[str]:
        """
        Get unique race names for display (no duplicates, no "Annat folkslag").
        
        Args:
            homeland: The homeland name
            
        Returns:
            List of unique race names
        """
        races = self.get_races_for_homeland(homeland)
        unique_names = []
        seen = set()
        
        for race in races:
            name = race['name']
            if name not in seen:
                unique_names.append(name)
                seen.add(name)
        
        return unique_names
    
    def roll_random_race(self, homeland: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Roll a random race for a homeland using T100.
        
        Args:
            homeland: The homeland name
            
        Returns:
            Tuple of (race_name, variant_name) or (None, None) if failed
        """
        if not self.homeland_races_data or homeland not in self.homeland_races_data:
            return None, None
        
        # Roll T100
        roll = random.randint(1, 100)
        homeland_data = self.homeland_races_data[homeland]
        
        # Find matching race entry
        selected_race = None
        for race_entry in homeland_data:
            range_str = race_entry.get('range', '')
            if self._is_in_range(roll, range_str):
                selected_race = race_entry
                break
        
        if not selected_race:
            return None, None
        
        race_name = selected_race.get('folkslag', 'Unknown')
        variant_name = None
        
        # If race has subtable, roll for variant
        if 'subtable' in selected_race:
            subtable = selected_race['subtable']
            variant_roll = random.randint(1, 100)
            
            for variant_entry in subtable:
                variant_range = variant_entry.get('range', '')
                if self._is_in_range(variant_roll, variant_range):
                    variant_name = variant_entry.get('variant', 'Unknown')
                    break
        
        return race_name, variant_name
    
    def _is_in_range(self, value: int, range_str: str) -> bool:
        """
        Check if a value is within a range string (e.g., "1-64", "99-99").
        
        Args:
            value: The value to check
            range_str: Range string like "1-64"
            
        Returns:
            True if value is in range, False otherwise
        """
        try:
            if '-' in range_str:
                start, end = range_str.split('-', 1)
                return int(start) <= value <= int(end)
            else:
                # Single number
                return value == int(range_str)
        except (ValueError, AttributeError):
            return False
    
    def validate_race_choice(self, homeland: str, race_input: str) -> Optional[str]:
        """
        Validate and normalize a race choice input.
        
        Args:
            homeland: The homeland name
            race_input: User's race input (name or number)
            
        Returns:
            Normalized race name if valid, None otherwise
        """
        available_races = self.get_unique_race_names(homeland)
        
        if not available_races:
            return None
        
        # Try as number first
        try:
            race_index = int(race_input.strip()) - 1  # Convert to 0-based
            if 0 <= race_index < len(available_races):
                return available_races[race_index]
        except ValueError:
            pass
        
        # Try as name (case insensitive)
        race_input_lower = race_input.lower().strip()
        for race_name in available_races:
            if race_name.lower() == race_input_lower:
                return race_name
        
        # Try partial matching
        matches = [race for race in available_races 
                  if race_input_lower in race.lower()]
        
        if len(matches) == 1:
            return matches[0]
        
        return None
    
    def get_homeland_list(self) -> List[str]:
        """
        Get list of all available homelands.
        
        Returns:
            List of homeland names
        """
        if not self.homeland_races_data:
            return []
        return list(self.homeland_races_data.keys())
    
    def has_homeland(self, homeland: str) -> bool:
        """
        Check if homeland exists in data.
        
        Args:
            homeland: The homeland name
            
        Returns:
            True if homeland exists, False otherwise
        """
        return bool(self.homeland_races_data and homeland in self.homeland_races_data)
    
    def get_race_statistics(self, homeland: str) -> Dict[str, Any]:
        """
        Get statistics about races in a homeland.
        
        Args:
            homeland: The homeland name
            
        Returns:
            Dictionary with race statistics
        """
        races = self.get_races_for_homeland(homeland)
        
        return {
            'total_races': len(races),
            'races_with_subtables': len([r for r in races if r['has_subtable']]),
            'unique_races': len(self.get_unique_race_names(homeland)),
            'race_names': [r['name'] for r in races]
        }
    
    def format_race_display(self, homeland: str) -> str:
        """
        Format races for display in Discord embed.
        
        Args:
            homeland: The homeland name
            
        Returns:
            Formatted string for Discord display
        """
        races = self.get_unique_race_names(homeland)
        
        if not races:
            return "Inga raser tillgängliga för detta hemland."
        
        formatted_races = []
        for i, race in enumerate(races, 1):
            formatted_races.append(f"{i}. {race}")
        
        return "\n".join(formatted_races)
    
    def reload_data(self) -> bool:
        """
        Reload data from file.
        
        Returns:
            True if reload successful, False otherwise
        """
        try:
            self._load_data()
            return bool(self.homeland_races_data)
        except Exception as e:
            print(f"Error reloading homeland race data: {e}")
            return False