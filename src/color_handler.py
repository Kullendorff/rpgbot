import json
import os
import random
from typing import Dict, Optional

class ColorHandler:
    # Grundläggande färger som konstanter
    DISCORD_RED = 0xFF0000      # Ren röd
    DISCORD_PURPLE = 0x800080   # Lila
    DISCORD_GOLD = 0xFFD700     # Guld/gul - en varm, välkomnande färg
    DISCORD_CYAN = 0x00FFFF     # Cyan - en ljus, klar färg som sticker ut
    DISCORD_GREEN = 0x2ECC71    # Smaragdgrön - behaglig men distinkt

    def __init__(self, storage_file: str = None):
        if storage_file is None:
            # Använd en absolut sökväg baserad på skriptets placering
            script_dir = os.path.dirname(os.path.abspath(__file__))
            data_dir = os.path.join(os.path.dirname(script_dir), 'data')
            # Skapa data-mappen om den inte finns
            os.makedirs(data_dir, exist_ok=True)
            self.storage_file = os.path.join(data_dir, 'user_colors.json')
        else:
            self.storage_file = storage_file
            
        print(f"Använder färgfil: {self.storage_file}")
        
        # Dictionary med fasta färgtilldelningar för specifika användare
        self.fixed_colors: Dict[int, int] = {
            # Användare med begärda färger
            177927888819978240: self.DISCORD_RED,    # Röd enligt önskemål
            368410767189606401: self.DISCORD_PURPLE, # Lila enligt önskemål
            
            # Användare med valda färger
            680064176227352610: self.DISCORD_GOLD,   # Guld - varm och inbjudande
            477800979295633409: self.DISCORD_CYAN,   # Cyan - klar och tydlig
            197809169296916480: self.DISCORD_GREEN   # Smaragdgrön - naturlig men distinkt
        }
        self.colors: Dict[str, int] = self._load_colors()
    
    def get_user_color(self, user_id: int) -> int:
        """
        Hämtar färgen för en användare. Returnerar den fasta färgen om användaren
        har en tilldelad, annars genereras en slumpmässig färg.
        
        Args:
            user_id: Discord-användarens ID
            
        Returns:
            En färgkod som hexadecimalt tal
        """
        # Kontrollera först om användaren har en fast färg
        if user_id in self.fixed_colors:
            return self.fixed_colors[user_id]
            
        # Om ingen fast färg finns, fortsätt med slumpmässig färggenerering
        user_key = str(user_id)
        if user_key not in self.colors:
            hue = random.random()
            saturation = random.uniform(0.5, 0.9)
            value = random.uniform(0.7, 0.9)
            
            color = self._hsv_to_rgb(hue, saturation, value)
            self.colors[user_key] = color
            self._save_colors()
        
        return self.colors[user_key]

    def _hsv_to_rgb(self, h: float, s: float, v: float) -> int:
        """
        Konverterar HSV-färgvärden till RGB hexadecimalt tal.
        
        Args:
            h: Nyans (0.0 till 1.0)
            s: Mättnad (0.0 till 1.0)
            v: Ljusstyrka (0.0 till 1.0)
            
        Returns:
            RGB-värde som hexadecimalt tal
        """
        if s == 0.0:
            rgb = v, v, v
        else:
            i = int(h * 6.0)
            f = (h * 6.0) - i
            p = v * (1.0 - s)
            q = v * (1.0 - s * f)
            t = v * (1.0 - s * (1.0 - f))
            i = i % 6
            
            if i == 0:
                rgb = v, t, p
            elif i == 1:
                rgb = q, v, p
            elif i == 2:
                rgb = p, v, t
            elif i == 3:
                rgb = p, q, v
            elif i == 4:
                rgb = t, p, v
            else:
                rgb = v, p, q
        
        r = int(rgb[0] * 255)
        g = int(rgb[1] * 255)
        b = int(rgb[2] * 255)
        return (r << 16) | (g << 8) | b

    def _load_colors(self) -> Dict[str, int]:
        """Laddar sparade färger från JSON-filen."""
        try:
            if os.path.exists(self.storage_file):
                with open(self.storage_file, 'r') as f:
                    return {str(k): v for k, v in json.load(f).items()}
        except (json.JSONDecodeError, IOError) as e:
            print(f"Varning: Kunde inte ladda färger: {e}")
        return {}
    
    def _save_colors(self) -> None:
        """Sparar färgerna till JSON-filen."""
        try:
            with open(self.storage_file, 'w') as f:
                json.dump(self.colors, f)
        except IOError as e:
            print(f"Varning: Kunde inte spara färger: {e}")

# Exempel på användning:
"""
color_handler = ColorHandler()

# Använd i din Discord-bot
@bot.command()
async def some_command(ctx):
    color = color_handler.get_user_color(ctx.author.id)
    # Använd färgen i embed eller annat...
"""