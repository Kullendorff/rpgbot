"""
Hemlig tärnings-manipulation system för GM.
Hanterar automatisk framgång/misslyckande utan att spelare vet om det.
"""

import json
import os
from typing import Dict, Optional, Any, List
from datetime import datetime
import random

class ManipulationManager:
    def __init__(self, data_dir: str = "data"):
        """
        Initialize manipulation manager.
        
        Args:
            data_dir: Directory to store manipulation data
        """
        self.data_dir = data_dir
        self.manipulation_file = os.path.join(data_dir, "secret_manipulations.json")
        self.active_manipulations = {}
        self._ensure_data_dir()
        self._load_manipulations()
    
    def _ensure_data_dir(self):
        """Ensure data directory exists."""
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
    
    def _load_manipulations(self):
        """Load active manipulations from file."""
        try:
            if os.path.exists(self.manipulation_file):
                with open(self.manipulation_file, 'r', encoding='utf-8') as f:
                    self.active_manipulations = json.load(f)
            else:
                self.active_manipulations = {}
        except Exception as e:
            print(f"Error loading manipulations: {e}")
            self.active_manipulations = {}
    
    def _save_manipulations(self):
        """Save active manipulations to file."""
        try:
            with open(self.manipulation_file, 'w', encoding='utf-8') as f:
                json.dump(self.active_manipulations, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving manipulations: {e}")
    
    def set_player_manipulation(self, user_id: str, manipulation_type: str, gm_id: str) -> bool:
        """
        Set manipulation for a player.
        
        Args:
            user_id: Target player's Discord user ID
            manipulation_type: 'lycka' (auto-success) or 'olycka' (auto-fail)
            gm_id: GM who activated this manipulation
            
        Returns:
            True if successful
        """
        valid_types = ['lycka', 'olycka']
        if manipulation_type not in valid_types:
            return False
        
        try:
            manipulation_data = {
                "type": manipulation_type,
                "target": "player",
                "activated_by": gm_id,
                "activated_at": datetime.now().isoformat(),
                "rolls_affected": 0
            }
            
            self.active_manipulations[user_id] = manipulation_data
            self._save_manipulations()
            
            print(f"[SECRET] Manipulation '{manipulation_type}' activated for user {user_id} by GM {gm_id}")
            return True
        except Exception as e:
            print(f"Error setting player manipulation: {e}")
            return False
    
    def set_gm_manipulation(self, gm_id: str, manipulation_type: str) -> bool:
        """
        Set manipulation for GM themselves.
        
        Args:
            gm_id: GM's Discord user ID
            manipulation_type: 'gudomlig' (auto-success) or 'förbannelse' (auto-fail)
            
        Returns:
            True if successful
        """
        valid_types = ['gudomlig', 'förbannelse']
        if manipulation_type not in valid_types:
            return False
        
        try:
            manipulation_data = {
                "type": manipulation_type,
                "target": "gm",
                "activated_by": gm_id,
                "activated_at": datetime.now().isoformat(),
                "rolls_affected": 0
            }
            
            self.active_manipulations[gm_id] = manipulation_data
            self._save_manipulations()
            
            print(f"[SECRET] GM manipulation '{manipulation_type}' activated for GM {gm_id}")
            return True
        except Exception as e:
            print(f"Error setting GM manipulation: {e}")
            return False
    
    def remove_manipulation(self, user_id: str) -> bool:
        """
        Remove manipulation for a user.
        
        Args:
            user_id: User's Discord user ID
            
        Returns:
            True if manipulation was removed
        """
        try:
            if user_id in self.active_manipulations:
                del self.active_manipulations[user_id]
                self._save_manipulations()
                print(f"[SECRET] Manipulation removed for user {user_id}")
                return True
            return False
        except Exception as e:
            print(f"Error removing manipulation: {e}")
            return False
    
    def get_manipulation(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get active manipulation for a user.
        
        Args:
            user_id: User's Discord user ID
            
        Returns:
            Manipulation data or None
        """
        return self.active_manipulations.get(user_id)
    
    def get_all_manipulations(self) -> Dict[str, Dict[str, Any]]:
        """Get all active manipulations."""
        return self.active_manipulations.copy()
    
    def manipulate_roll_result(self, user_id: str, original_rolls: List[int], 
                              sides: int, modifier: int, target: Optional[int]) -> tuple:
        """
        Manipulate roll result if user has active manipulation.
        
        Args:
            user_id: User's Discord user ID
            original_rolls: Original dice roll values
            sides: Number of sides on dice
            modifier: Roll modifier
            target: Target value (if any)
            
        Returns:
            Tuple of (manipulated_rolls, was_manipulated, manipulation_type)
        """
        manipulation = self.get_manipulation(str(user_id))
        if not manipulation:
            return original_rolls, False, None
        
        manipulation_type = manipulation["type"]
        
        try:
            # Update roll count
            manipulation["rolls_affected"] += 1
            self._save_manipulations()
            
            # Only manipulate if there's a target to succeed/fail against
            if target is None:
                return original_rolls, False, manipulation_type
            
            current_total = sum(original_rolls) + modifier
            
            if manipulation_type in ["lycka", "gudomlig"]:
                # AUTO-SUCCESS: Ensure roll succeeds
                if current_total >= target:
                    # Already succeeding, no need to manipulate
                    return original_rolls, False, manipulation_type
                else:
                    # Need to manipulate to succeed
                    needed_total = target
                    needed_dice_sum = needed_total - modifier
                    
                    # Create believable manipulated rolls that sum to needed value
                    manipulated_rolls = self._create_believable_rolls(
                        original_rolls, needed_dice_sum, sides, "success"
                    )
                    
                    print(f"[SECRET] {manipulation_type.upper()} manipulation: {original_rolls} -> {manipulated_rolls}")
                    return manipulated_rolls, True, manipulation_type
            
            elif manipulation_type in ["olycka", "förbannelse"]:
                # AUTO-FAIL: Ensure roll fails
                if current_total < target:
                    # Already failing, no need to manipulate
                    return original_rolls, False, manipulation_type
                else:
                    # Need to manipulate to fail
                    needed_total = target - 1
                    needed_dice_sum = needed_total - modifier
                    
                    # Ensure we don't go below minimum possible
                    min_possible = len(original_rolls)
                    if needed_dice_sum < min_possible:
                        needed_dice_sum = min_possible
                    
                    # Create believable manipulated rolls that sum to needed value
                    manipulated_rolls = self._create_believable_rolls(
                        original_rolls, needed_dice_sum, sides, "failure"
                    )
                    
                    print(f"[SECRET] {manipulation_type.upper()} manipulation: {original_rolls} -> {manipulated_rolls}")
                    return manipulated_rolls, True, manipulation_type
            
        except Exception as e:
            print(f"Error manipulating roll: {e}")
            return original_rolls, False, manipulation_type
        
        return original_rolls, False, manipulation_type
    
    def _create_believable_rolls(self, original_rolls: List[int], target_sum: int, 
                                sides: int, intent: str) -> List[int]:
        """
        Create believable manipulated rolls that sum to target.
        
        Args:
            original_rolls: Original roll values
            target_sum: Target sum for manipulated rolls
            sides: Number of sides on dice
            intent: "success" or "failure"
            
        Returns:
            List of manipulated roll values
        """
        num_dice = len(original_rolls)
        min_sum = num_dice  # Minimum possible (all 1s)
        max_sum = num_dice * sides  # Maximum possible
        
        # Ensure target is within possible range
        target_sum = max(min_sum, min(target_sum, max_sum))
        
        # Start with original rolls and adjust gradually
        manipulated = original_rolls.copy()
        current_sum = sum(manipulated)
        
        # If we need to increase the sum
        while current_sum < target_sum:
            # Find a die that can be increased
            for i in range(num_dice):
                if manipulated[i] < sides and current_sum < target_sum:
                    increase = min(sides - manipulated[i], target_sum - current_sum)
                    manipulated[i] += increase
                    current_sum += increase
                    if current_sum >= target_sum:
                        break
        
        # If we need to decrease the sum
        while current_sum > target_sum:
            # Find a die that can be decreased
            for i in range(num_dice):
                if manipulated[i] > 1 and current_sum > target_sum:
                    decrease = min(manipulated[i] - 1, current_sum - target_sum)
                    manipulated[i] -= decrease
                    current_sum -= decrease
                    if current_sum <= target_sum:
                        break
        
        # Add some randomness to make it look natural
        # Occasionally swap values between dice while maintaining sum
        if random.random() < 0.3:  # 30% chance
            for _ in range(random.randint(1, 3)):
                i, j = random.sample(range(num_dice), 2)
                if manipulated[i] > 1 and manipulated[j] < sides:
                    if random.random() < 0.5:
                        manipulated[i] -= 1
                        manipulated[j] += 1
        
        return manipulated
    
    def clear_all_manipulations(self) -> int:
        """
        Clear all active manipulations.
        
        Returns:
            Number of manipulations cleared
        """
        count = len(self.active_manipulations)
        self.active_manipulations = {}
        self._save_manipulations()
        print(f"[SECRET] Cleared {count} active manipulations")
        return count