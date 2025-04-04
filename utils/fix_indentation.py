#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Skript för att fixa indenteringen i main.py
"""

import os
import sys
from pathlib import Path

def fix_indentation(file_path):
    """
    Fixa indenteringsproblem i given fil.
    """
    try:
        # Läs in filen
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Återställ från backup om den finns
        backup_path = file_path + '.bak'
        if os.path.exists(backup_path):
            print(f"Återställer från backup: {backup_path}")
            with open(backup_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(original_content)
            
            print("Filen har återställts från säkerhetskopian.")
            return True
        else:
            print("Ingen säkerhetskopia hittades.")
            return False
        
    except Exception as e:
        print(f"Ett fel uppstod: {str(e)}")
        return False

if __name__ == "__main__":
    # Bestäm sökväg till main.py
    script_dir = Path(os.path.dirname(os.path.abspath(__file__)))
    project_root = script_dir.parent
    main_py_path = os.path.join(project_root, "src", "main.py")
    
    if not os.path.exists(main_py_path):
        print(f"main.py finns inte på den förväntade sökvägen: {main_py_path}")
        sys.exit(1)
    
    print("Det här skriptet kommer att återställa main.py från säkerhetskopian")
    print("eftersom det verkar ha uppstått problem med indentering.")
    
    answer = input("Vill du fortsätta? (j/n): ")
    if answer.lower() not in ['j', 'ja', 'y', 'yes']:
        print("Avbryter.")
        sys.exit(0)
    
    if fix_indentation(main_py_path):
        print("\nFilen har återställts. Du kan nu försöka göra ändringarna manuellt istället.")
        sys.exit(0)
    else:
        print("\nKunde inte återställa filen.")
        print("Du kan behöva redigera filen manuellt för att fixa indenteringen.")
        sys.exit(1)
