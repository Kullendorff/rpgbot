#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enkelt test för att verifiera att det interaktiva karaktärsskapande-systemet fungerar
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from interactive_chargen import InteractiveCharacterCreator, CharacterSession

def test_chargen_basic():
    """Test grundläggande chargen-funktionalitet"""
    print("Testar InteractiveCharacterCreator...")
    
    # Skapa chargen med test data directory
    chargen = InteractiveCharacterCreator()
    
    print(f"CharGen skapad med {len(chargen.steps)} steg")
    print(f"TableProcessor laddad med {len(chargen.table_processor.tables)} tabeller")
    print(f"Session directory: {chargen.session_dir}")
    
    # Testa session-skapande
    print("\nTestar session management...")
    
    test_user_id = "test_user_123"
    session = chargen.start_session(test_user_id)
    
    print(f"Session skapad for anvandare {test_user_id}")
    print(f"Nuvarande steg: {session.current_step}")
    print(f"Max steg: {session.max_steps}")
    
    # Testa att sessionen sparas
    retrieved_session = chargen.get_session(test_user_id)
    assert retrieved_session is not None, "Session kunde inte hamtas"
    print("Session sparning och hamtning fungerar")
    
    # Testa steg navigation
    print("\nTestar steg navigation...")
    
    current_step = session.current_step
    step_info = chargen.get_current_step_info(session)
    print(f"Steg {current_step}: {step_info['title']}")
    
    # Testa att gå till nästa steg
    success = chargen.next_step(session)
    assert success, "Kunde inte ga till nasta steg"
    assert session.current_step == current_step + 1, "Steg inte uppdaterat"
    print(f"Nasta steg fungerar: nu pa steg {session.current_step}")
    
    # Testa att gå tillbaka
    success = chargen.previous_step(session)
    assert success, "Kunde inte ga tillbaka"
    assert session.current_step == current_step, "Steg inte aterstalli"
    print(f"Foregaende steg fungerar: tillbaka pa steg {session.current_step}")
    
    # Testa att sätta data
    print("\nTestar session data...")
    
    session.data['test_key'] = 'test_value'
    session.data['folkslag'] = 'vanarer'
    session.data['alder'] = 25
    session.update_context()
    chargen.save_session(session)
    
    # Ladda session igen och kontrollera data
    reloaded_session = chargen.load_session(test_user_id)
    assert reloaded_session is not None, "Session kunde inte laddas fran fil"
    assert reloaded_session.data['test_key'] == 'test_value', "Data inte sparad"
    assert reloaded_session.data['folkslag'] == 'vanarer', "Folkslag inte sparad"
    print("Session data sparning/laddning fungerar")
    
    # Testa context uppdatering
    assert reloaded_session.context.folkslag == 'vanarer', "Context inte uppdaterat"
    print("CharacterContext uppdatering fungerar")
    
    # Rensa test session
    chargen.end_session(test_user_id)
    assert chargen.get_session(test_user_id) is None, "Session inte borttagen"
    print("Session cleanup fungerar")
    
    print("\nAlla tester godkanda! Chargen ar redo for anvandning.")

def test_table_integration():
    """Test integration med TableProcessor"""
    print("\nTestar TableProcessor integration...")
    
    chargen = InteractiveCharacterCreator()
    
    # Testa att tabeller laddades
    tables_count = len(chargen.table_processor.tables)
    text_files_count = len(chargen.table_processor.text_files)
    
    print(f"{tables_count} JSON-tabeller laddade")
    print(f"{text_files_count} textfiler laddade")
    
    if tables_count > 0:
        # Lista några tabeller
        table_names = list(chargen.table_processor.tables.keys())[:5]
        print(f"Exempel pa tabeller: {', '.join(table_names)}")
    
    if text_files_count > 0:
        # Lista några länder
        countries = list(chargen.table_processor.text_files.keys())[:5]
        print(f"Exempel pa lander: {', '.join(countries)}")
    
    # Testa attribute_modifiers specifikt (krävs för folkslag-steget)
    if 'attribute_modifiers' in chargen.table_processor.tables:
        attr_mod = chargen.table_processor.tables['attribute_modifiers']
        race_count = sum(len(races) for races in attr_mod.values())
        print(f"{race_count} folkslag tillgangliga for karaktersskapande")
        
        # Visa några folkslag
        for category, races in attr_mod.items():
            if races:
                race_names = list(races.keys())[:3]
                print(f"  - {category}: {', '.join(race_names)}...")
                break
    else:
        print("Varning: attribute_modifiers.json inte hittad - folkslag-steg fungerar inte")
    
    print("TableProcessor integration verifierad")

if __name__ == "__main__":
    print("Startar CharGen-test...\n")
    
    try:
        test_chargen_basic()
        test_table_integration()
        
        print("\nALLA TESTER GODKANDA!")
        print("Systemet ar redo for !chargen kommandon i Discord boten.")
        
    except Exception as e:
        print(f"\nTEST MISSLYCKADES: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)