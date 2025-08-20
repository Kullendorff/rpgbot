import tiktoken
from typing import List

def count_tokens(text: str) -> int:
    """Räknar antal tokens i en given text med GPT-4:s tokenräknare."""
    encoder = tiktoken.encoding_for_model("gpt-4")
    return len(encoder.encode(text))
    
def clean_unicode(text):
    """
    Rensar en sträng från eventuella surrogatpar genom att först koda om till bytes 
    och sedan tillbaka till str med felhantering.
    
    Args:
        text (str): Texten som ska rensas
        
    Returns:
        str: Rensad text utan surrogatpar
    """
    if text is None:
        return None
        
    if isinstance(text, str):
        # Omvandla till bytes med 'surrogateescape' och tillbaka med 'replace'
        # Detta ersätter eventuella ogiltiga tecken med U+FFFD (ersättningstecken)
        return text.encode('utf-8', 'surrogateescape').decode('utf-8', 'replace')
    return text

def split_message(message: str, max_length: int = 2000) -> List[str]:
    """Dela upp ett långt meddelande i mindre delar."""
    return [message[i:i+max_length] for i in range(0, len(message), max_length)]