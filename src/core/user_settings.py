"""
User settings manager for the EON Discord bot.
Handles user preferences like comment settings, themes, etc.
"""

import json
import os
from typing import Dict, Optional, Any
from datetime import datetime

class UserSettingsManager:
    def __init__(self, data_dir: str = "data"):
        """
        Initialize user settings manager.
        
        Args:
            data_dir: Directory to store user settings file
        """
        self.data_dir = data_dir
        self.settings_file = os.path.join(data_dir, "user_settings.json")
        self.settings_cache = {}
        self._ensure_data_dir()
        self._load_settings()
    
    def _ensure_data_dir(self):
        """Ensure data directory exists."""
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
    
    def _load_settings(self):
        """Load settings from file into cache."""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    self.settings_cache = json.load(f)
            else:
                self.settings_cache = {}
        except Exception as e:
            print(f"Error loading user settings: {e}")
            self.settings_cache = {}
    
    def _save_settings(self):
        """Save settings cache to file."""
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings_cache, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving user settings: {e}")
    
    def get_user_settings(self, user_id: str) -> Dict[str, Any]:
        """
        Get user settings with defaults.
        
        Args:
            user_id: Discord user ID as string
            
        Returns:
            Dict with user settings
        """
        default_settings = {
            "comments_enabled": False,  # DEFAULT: Avstängt
            "comment_frequency": 0.3,   # 30% chans
            "comment_style": "umnatak", # Default stil
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat()
        }
        
        if user_id not in self.settings_cache:
            self.settings_cache[user_id] = default_settings.copy()
            self._save_settings()
        
        return self.settings_cache[user_id].copy()
    
    def set_comments_enabled(self, user_id: str, enabled: bool) -> bool:
        """
        Enable/disable comments for user.
        
        Args:
            user_id: Discord user ID
            enabled: True to enable, False to disable
            
        Returns:
            True if successful
        """
        try:
            settings = self.get_user_settings(user_id)
            settings["comments_enabled"] = enabled
            settings["last_updated"] = datetime.now().isoformat()
            
            self.settings_cache[user_id] = settings
            self._save_settings()
            return True
        except Exception as e:
            print(f"Error setting comments enabled for {user_id}: {e}")
            return False
    
    def set_comment_style(self, user_id: str, style: str) -> bool:
        """
        Set comment style for user.
        
        Args:
            user_id: Discord user ID
            style: Comment style ('umnatak', 'encouraging', 'dramatic', 'neutral')
            
        Returns:
            True if successful
        """
        valid_styles = ['umnatak', 'encouraging', 'dramatic', 'neutral']
        if style not in valid_styles:
            return False
        
        try:
            settings = self.get_user_settings(user_id)
            settings["comment_style"] = style
            settings["last_updated"] = datetime.now().isoformat()
            
            self.settings_cache[user_id] = settings
            self._save_settings()
            return True
        except Exception as e:
            print(f"Error setting comment style for {user_id}: {e}")
            return False
    
    def set_comment_frequency(self, user_id: str, frequency: float) -> bool:
        """
        Set comment frequency for user.
        
        Args:
            user_id: Discord user ID
            frequency: Float between 0.1 and 0.5 (10-50%)
            
        Returns:
            True if successful
        """
        if not (0.1 <= frequency <= 0.5):
            return False
        
        try:
            settings = self.get_user_settings(user_id)
            settings["comment_frequency"] = frequency
            settings["last_updated"] = datetime.now().isoformat()
            
            self.settings_cache[user_id] = settings
            self._save_settings()
            return True
        except Exception as e:
            print(f"Error setting comment frequency for {user_id}: {e}")
            return False