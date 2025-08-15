#!/usr/bin/env python3
"""
Test för automatic_background.py
Testar familjebakgrundsgenerering
"""

import sys
import os

# Lägg till src-mappen i Python-sökvägen
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    from automatic_background import AutomaticBackgroundGenerator
    
    def test_background_generation():
        """Testar bakgrundsgenerering för olika folkslag"""
        
        generator = AutomaticBackgroundGenerator()
        
        test_cases = [
            ("vanarer", 25),
            ("sanari", 150),  # Alv
            ("ghor", 45),     # Dvärg  
            ("marnakh", 30),  # Tirak
        ]
        
        print("=== Test av Automatisk Bakgrundsgenerering ===\n")
        
        for race, age in test_cases:
            print(f"🧪 Testar {race.capitalize()}, {age} år:")
            try:
                background = generator.generate_complete_background(race, age)
                summary = generator.format_background_summary(background)
                
                print("✅ Generering lyckades!")
                print("📋 Resultat:")
                print(summary)
                print("\n" + "="*50 + "\n")
                
            except Exception as e:
                print(f"❌ Fel: {str(e)}")
                import traceback
                traceback.print_exc()
                print("\n" + "="*50 + "\n")
    
    if __name__ == "__main__":
        test_background_generation()
        
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Se till att automatic_background.py finns i src/ mappen")
except Exception as e:
    print(f"❌ Oväntat fel: {e}")
    import traceback
    traceback.print_exc()
