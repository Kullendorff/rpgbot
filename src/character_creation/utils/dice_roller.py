"""
Dice Rolling Utilities for Character Creation

This module provides dice rolling functions specifically for character creation,
including T100 rolls, range checking, and random selections.
"""

import random
from typing import List, Optional, Tuple, Any


class CharacterDiceRoller:
    """Utility class for character creation dice rolls."""
    
    @staticmethod
    def roll_d100() -> int:
        """
        Roll a single d100 (1-100).
        
        Returns:
            Random number between 1 and 100
        """
        return random.randint(1, 100)
    
    @staticmethod
    def roll_multiple_d6(count: int) -> List[int]:
        """
        Roll multiple d6 dice.
        
        Args:
            count: Number of dice to roll
            
        Returns:
            List of dice results
        """
        return [random.randint(1, 6) for _ in range(count)]
    
    @staticmethod
    def roll_attributes_3d6() -> List[int]:
        """
        Roll 9 attributes using 3d6 each.
        
        Returns:
            List of 9 attribute values
        """
        return [sum(CharacterDiceRoller.roll_multiple_d6(3)) for _ in range(9)]
    
    @staticmethod
    def roll_attributes_4d6_drop_lowest() -> List[int]:
        """
        Roll 9 attributes using 4d6, drop lowest.
        
        Returns:
            List of 9 attribute values
        """
        attributes = []
        for _ in range(9):
            rolls = sorted(CharacterDiceRoller.roll_multiple_d6(4), reverse=True)
            attributes.append(sum(rolls[:3]))  # Take best 3 of 4
        return attributes
    
    @staticmethod
    def roll_attributes_2d6_plus_9() -> List[int]:
        """
        Roll 9 attributes using 2d6+9.
        
        Returns:
            List of 9 attribute values
        """
        return [sum(CharacterDiceRoller.roll_multiple_d6(2)) + 9 for _ in range(9)]
    
    @staticmethod
    def is_value_in_range(value: int, range_str: str) -> bool:
        """
        Check if a value falls within a range string.
        
        Args:
            value: The value to check
            range_str: Range string like "1-64", "99-99", or "100"
            
        Returns:
            True if value is in range, False otherwise
        """
        try:
            range_str = range_str.strip()
            
            if '-' in range_str:
                start, end = range_str.split('-', 1)
                return int(start) <= value <= int(end)
            else:
                # Single number
                return value == int(range_str)
        except (ValueError, AttributeError):
            return False
    
    @staticmethod
    def find_table_result(roll: int, table: List[dict], 
                         range_key: str = 'range', 
                         result_key: str = 'result') -> Optional[dict]:
        """
        Find the matching result from a table based on a dice roll.
        
        Args:
            roll: The dice roll result
            table: List of table entries with ranges
            range_key: Key name for range in table entries
            result_key: Key name for result in table entries
            
        Returns:
            Matching table entry or None if not found
        """
        for entry in table:
            if range_key in entry:
                if CharacterDiceRoller.is_value_in_range(roll, entry[range_key]):
                    return entry
        return None
    
    @staticmethod
    def roll_on_table(table: List[dict], 
                     range_key: str = 'range',
                     result_key: str = 'result') -> Optional[Any]:
        """
        Roll on a table and return the result.
        
        Args:
            table: List of table entries
            range_key: Key name for range in table entries  
            result_key: Key name for result in table entries
            
        Returns:
            The result value or None if table is empty
        """
        if not table:
            return None
            
        roll = CharacterDiceRoller.roll_d100()
        entry = CharacterDiceRoller.find_table_result(roll, table, range_key, result_key)
        
        if entry and result_key in entry:
            return entry[result_key]
        
        return None
    
    @staticmethod
    def calculate_background_rolls_bonus(age: int) -> int:
        """
        Calculate bonus background rolls based on age.
        
        Args:
            age: Character's age
            
        Returns:
            Number of bonus background rolls
        """
        if age >= 100:
            return 5
        elif age >= 81:
            return 4
        elif age >= 61:
            return 3
        elif age >= 46:
            return 2
        elif age >= 31:
            return 1
        else:
            return 0
    
    @staticmethod
    def roll_background_events(base_rolls: int, age_bonus: int = 0) -> int:
        """
        Calculate total number of background event rolls.
        
        Args:
            base_rolls: Base number of rolls
            age_bonus: Age-based bonus rolls
            
        Returns:
            Total number of background rolls
        """
        return max(1, base_rolls + age_bonus)
    
    @staticmethod
    def simulate_rolls(count: int, sides: int = 6) -> Tuple[List[int], int, float]:
        """
        Simulate multiple dice rolls and return statistics.
        
        Args:
            count: Number of dice to roll
            sides: Number of sides per die
            
        Returns:
            Tuple of (individual_rolls, total, average)
        """
        rolls = [random.randint(1, sides) for _ in range(count)]
        total = sum(rolls)
        average = total / count if count > 0 else 0.0
        
        return rolls, total, average
    
    @staticmethod
    def format_dice_result(rolls: List[int], total: Optional[int] = None) -> str:
        """
        Format dice rolls for display.
        
        Args:
            rolls: List of individual dice results
            total: Optional total (calculated if not provided)
            
        Returns:
            Formatted string like "4, 5, 6 (total: 15)"
        """
        if not rolls:
            return "Inga slag"
        
        rolls_str = ", ".join(str(roll) for roll in rolls)
        
        if total is None:
            total = sum(rolls)
        
        if len(rolls) > 1:
            return f"{rolls_str} (total: {total})"
        else:
            return str(rolls[0])
    
    @staticmethod  
    def get_roll_description(method: str) -> str:
        """
        Get description of a dice rolling method.
        
        Args:
            method: Rolling method name
            
        Returns:
            Description string
        """
        descriptions = {
            '3d6': 'Standard: 3d6 för varje attribut (3-18)',
            '4d6': 'Generös: 4d6, ta bästa 3 (3-18, högre genomsnitt)',
            '2d6+9': 'Heroisk: 2d6+9 för varje attribut (11-21)'
        }
        
        return descriptions.get(method, f'Okänd metod: {method}')
    
    @staticmethod
    def validate_dice_expression(expression: str) -> bool:
        """
        Validate a dice expression like '3d6', '1d20', etc.
        
        Args:
            expression: Dice expression to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            expression = expression.lower().strip()
            
            if 'd' not in expression:
                return False
            
            parts = expression.split('d')
            if len(parts) != 2:
                return False
            
            count = int(parts[0])
            sides = int(parts[1])
            
            return count > 0 and sides > 0 and count <= 100 and sides <= 1000
            
        except (ValueError, AttributeError):
            return False