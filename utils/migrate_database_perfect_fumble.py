#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Migrationsskript för att lägga till kolumner för perfekta slag och fummel i tärningsloggdatabasen.
"""

import sqlite3
import os
import sys

def migrate_database(db_path):
    """
    Lägger till kolumner för perfekta slag och fummel i databasen.
    
    Args:
        db_path (str): Sökväg till databasen
    """
    if not os.path.exists(db_path):
        print(f"Databasen finns inte på sökvägen: {db_path}")
        return False
        
    try:
        with sqlite3.connect(db_path) as conn:
            # Kontrollera om kolumnerna redan existerar
            cursor = conn.execute("PRAGMA table_info(rolls)")
            columns = [column[1] for column in cursor.fetchall()]
            
            # Lägg till kolumner om de inte redan finns
            changes_made = False
            
            if "is_perfect" not in columns:
                conn.execute("ALTER TABLE rolls ADD COLUMN is_perfect INTEGER")
                print("Kolumn 'is_perfect' har lagts till")
                changes_made = True
                
            if "is_fumble" not in columns:
                conn.execute("ALTER TABLE rolls ADD COLUMN is_fumble INTEGER")
                print("Kolumn 'is_fumble' har lagts till")
                changes_made = True
                
            if changes_made:
                print("Migrationen slutfördes framgångsrikt!")
            else:
                print("Inga ändringar behövdes, kolumnerna finns redan")
                
            return True
    except Exception as e:
        print(f"Ett fel uppstod under migrationen: {e}")
        return False

if __name__ == "__main__":
    # Bestäm sökväg till databasen
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    db_path = os.path.join(project_root, "data", "rolls.db")
    
    print(f"Migrerar databasen på sökvägen: {db_path}")
    success = migrate_database(db_path)
    
    if success:
        print("Migrationen lyckades!")
        sys.exit(0)
    else:
        print("Migrationen misslyckades!")
        sys.exit(1)
