"""
Comment styles and messages for the EON Discord bot.
"""

import random
from typing import Dict, List, Optional

# Kommentarstilar med olika personligheter
COMMENT_STYLES: Dict[str, Dict[str, List[str]]] = {
    "umnatak": {
        "success": [
            "Äntligen lyckades du med något",
            "Ett mirakel inträffade", 
            "Slutade bra trots förväntningarna",
            "Överraskande kompetent denna gång",
            "Gudarna måste ha känt medlidande"
        ],
        "failure": [
            "Som väntat",
            "Klassiskt",
            "Ingen överraskning där",
            "Precis vad jag förväntade mig",
            "Tradition fortsätter"
        ],
        "critical_success": [
            "Nu har världen vänt upp och ner",
            "Jag måste se om igen",
            "Detta trotsade alla odds",
            "Historiska ögonblick"
        ],
        "fumble": [
            "Naturlag i kraft",
            "Åh, där var du igen",
            "Tillbaka till det normala",
            "Balansen återställd"
        ]
    },
    
    "encouraging": {
        "success": [
            "Fantastiskt slag!",
            "Du är på gång nu!",
            "Vilken skicklighet!",
            "Bra jobbat!",
            "Imponerande!"
        ],
        "failure": [
            "Nästa gång blir bättre!",
            "Bara att försöka igen!",
            "Det händer de bästa!",
            "Fortsätt kämpa!",
            "Du kommer tillbaka starkare!"
        ],
        "critical_success": [
            "OTROLIGT! Vilket slag!",
            "Du är på topp idag!",
            "Mästerligt utfört!",
            "Legendariskt!"
        ],
        "fumble": [
            "Alla gör misstag!",
            "Det här händer även proffsen!",
            "Lär av detta och kom tillbaka!",
            "Fummel bygger karaktär!"
        ]
    },
    
    "dramatic": {
        "success": [
            "ÖDET HAR TALAT!",
            "Ett slag för historieböckerna!",
            "Gudarna ler mot dig!",
            "EPISKT UTFÖRT!",
            "Stjärnorna har anpassat sig!"
        ],
        "failure": [
            "Mörkrets krafter motverkar dig!",
            "Ödet testar din beslutsamhet!",
            "Även hjältar faller ibland!",
            "Kampen fortsätter!",
            "Utmaningen växer!"
        ],
        "critical_success": [
            "GUDARNA SJÄLVA APPLÅDERAR!",
            "ETT MIRAKEL UTFÖRT!",
            "LEGENDEN FÖDS!",
            "KOSMOS SJÄLV FÖRUNDRAS!"
        ],
        "fumble": [
            "KAOS REGERAR!",
            "ÖDET HÅNAR DIG!",
            "MÖRKRETS STUND!",
            "TROLLKONSTEN SVIKER!"
        ]
    },
    
    "neutral": {
        "success": [
            "Lyckad handling",
            "Bra resultat",
            "Framgång noterad",
            "Positivt utfall"
        ],
        "failure": [
            "Misslyckad handling",
            "Negativt resultat", 
            "Försök misslyckades",
            "Icke önskat utfall"
        ],
        "critical_success": [
            "Exceptionellt resultat",
            "Kritisk framgång",
            "Maximalt utfall",
            "Optimal prestation"
        ],
        "fumble": [
            "Kritiskt misslyckande",
            "Fummel registrerat",
            "Negativ komplikation",
            "Olycklig utgång"
        ]
    }
}

class CommentGenerator:
    """Generates contextual comments based on roll results and user preferences."""
    
    def __init__(self):
        self.styles = COMMENT_STYLES
    
    def get_comment(self, user_settings: dict, roll_result: dict) -> Optional[str]:
        """
        Get comment based on user settings and roll result.
        
        Args:
            user_settings: User's comment preferences
            roll_result: Dict with roll information
            
        Returns:
            Comment string or None
        """
        # Check if comments are enabled
        if not user_settings.get("comments_enabled", False):
            return None
        
        # Check frequency
        frequency = user_settings.get("comment_frequency", 0.3)
        if random.random() > frequency:
            return None
        
        # Get comment style
        style = user_settings.get("comment_style", "umnatak")
        if style not in self.styles:
            style = "umnatak"
        
        # Determine comment category based on roll result
        category = self._determine_category(roll_result)
        
        # Get comment from style and category
        comments = self.styles[style].get(category, [])
        if not comments:
            return None
        
        return random.choice(comments)
    
    def _determine_category(self, roll_result: dict) -> str:
        """
        Determine comment category based on roll result.
        
        Args:
            roll_result: Dict with roll information
            
        Returns:
            Category string: 'success', 'failure', 'critical_success', 'fumble'
        """
        # Check for critical results first
        if roll_result.get("is_fumble", False):
            return "fumble"
        elif roll_result.get("is_critical_success", False):
            return "critical_success"
        elif roll_result.get("is_perfect", False):
            return "critical_success"
        
        # Check for success/failure
        success = roll_result.get("success")
        if success is True:
            return "success"
        elif success is False:
            return "failure"
        
        # Default to success for positive results
        return "success"
    
    def get_available_styles(self) -> List[str]:
        """Get list of available comment styles."""
        return list(self.styles.keys())