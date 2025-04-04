#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Skript för att lägga till stöd för perfekta slag och fummel i ex-kommandot.
Detta skript använder en mer direkt metod för att hitta och uppdatera de relevanta delarna av koden.
"""

import os
import re
import sys
from pathlib import Path
import ast
import astor  # Du kan behöva installera detta paket: pip install astor

def find_function_node(tree, function_name):
    """Hitta noden för en specifik funktion i AST."""
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == function_name:
            return node
    return None

def modify_ex_command(file_path):
    """
    Modifiera ex_command-funktionen för att lägga till stöd för perfekta slag och fummel.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Hitta ex_command-funktionen
        ex_command_match = re.search(r'@bot\.command\(name=\'ex\'\)\s*async def ex_command\([^)]*\)[^{]*:', content)
        if not ex_command_match:
            print("Kunde inte hitta ex_command-funktionen.")
            return False
        
        # Hitta slutet av funktionen
        start_pos = ex_command_match.start()
        function_content = content[start_pos:]
        
        # Hitta log_roll-anropet i ex_command
        log_roll_match = re.search(r'roll_tracker\.log_roll\([^)]*\)', function_content)
        if not log_roll_match:
            print("Kunde inte hitta log_roll-anropet i ex_command.")
            return False
        
        # Konstruera det nya log_roll-anropet
        old_log_roll = log_roll_match.group(0)
        
        # Kontrollera om is_perfect och is_fumble redan finns i anropet
        if 'is_perfect=' in old_log_roll or 'is_fumble=' in old_log_roll:
            print("is_perfect och is_fumble finns redan i log_roll-anropet.")
        else:
            # Lägg till is_perfect och is_fumble i anropet
            new_log_roll = old_log_roll.rstrip(')')
            if new_log_roll.endswith(','):
                new_log_roll += "\n            is_perfect=perfect_candidate,\n            is_fumble=fumble_candidate\n        )"
            else:
                new_log_roll += ",\n            is_perfect=perfect_candidate,\n            is_fumble=fumble_candidate\n        )"
            
            # Ersätt log_roll-anropet
            updated_function = function_content.replace(old_log_roll, new_log_roll)
            
            # Hitta stället där särskilt utfall ska läggas till
            embed_send_match = re.search(r'await ctx\.send\(embed=embed\)', updated_function)
            if not embed_send_match:
                print("Kunde inte hitta 'await ctx.send(embed=embed)' i ex_command.")
                return False
            
            # Hitta stället där resultattexten visas
            result_field_match = re.search(r'embed\.add_field\(name="Resultat", value=result_text, inline=False\)', updated_function)
            if not result_field_match:
                print("Kunde inte hitta resultatfältet i ex_command.")
                return False
            
            # Lägg till särskilt utfall före await ctx.send
            special_result_code = """
        # Lägg till information om perfekt slag eller fummel
        if perfect_candidate or fumble_candidate:
            special_result = []
            if perfect_candidate:
                special_result.append("✨ **PERFEKT SLAG!** Tärningsoraklet ler mot dig.")
            if fumble_candidate:
                special_result.append("💥 **FUMMEL!** Tärningsoraklet skrattar åt din olycka.")
                
            embed.add_field(
                name="Särskilt Utfall",
                value="\\n".join(special_result),
                inline=False
            )
"""
            result_field_end = result_field_match.end()
            updated_function_with_special = (
                updated_function[:result_field_end] + 
                special_result_code + 
                updated_function[result_field_end:]
            )
            
            # Ersätt hela funktionsinnehållet
            updated_content = content[:start_pos] + updated_function_with_special
            
            # Skapa en säkerhetskopia
            backup_path = file_path + '.bak'
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Säkerhetskopia skapad: {backup_path}")
            
            # Spara den uppdaterade filen
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(updated_content)
            
            print("ex_command har uppdaterats med stöd för perfekta slag och fummel.")
            return True
    except Exception as e:
        print(f"Ett fel uppstod vid uppdatering av ex_command: {e}")
        return False

def modify_secret_roll(file_path):
    """
    Modifiera secret_roll-funktionen för att lägga till stöd för perfekta slag och fummel.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Hitta secret_roll-funktionen
        secret_roll_match = re.search(r'@bot\.command\(name=\'secret\'\)[^{]*\s*@commands\.has_role\(\'Game Master\'\)\s*async def secret_roll\([^)]*\)[^{]*:', content)
        if not secret_roll_match:
            print("Kunde inte hitta secret_roll-funktionen.")
            return False
        
        # Hitta slutet av funktionen
        start_pos = secret_roll_match.start()
        function_content = content[start_pos:]
        
        # Hitta log_roll-anropet i secret_roll
        log_roll_match = re.search(r'# Logga det hemliga slaget.*?roll_tracker\.log_roll\([^)]*\)', function_content, re.DOTALL)
        if not log_roll_match:
            print("Kunde inte hitta log_roll-anropet i secret_roll.")
            return False
        
        # Ersätt hela log_roll-blocket med vår uppdaterade version
        old_log_roll_block = log_roll_match.group(0)
        
        # Kontrollera om is_perfect och is_fumble redan har lagts till
        if 'is_perfect=' in old_log_roll_block or 'is_fumble=' in old_log_roll_block:
            print("is_perfect och is_fumble finns redan i secret_roll-funktionen.")
            return True
        
        # Skapa den nya koden för att hantera ex-kommandon med perfekta slag och fummel
        new_log_roll_block = """
        # Identifiera perfekta slag och fummel för hemliga obegränsade T6-slag
        is_perfect = False
        is_fumble = False
        
        if command_type == "ex":
            # Använd den befintliga logiken från ex-kommandot för perfekta och fummel
            if num_dice == 1:
                if initial_rolls[0] in [1, 2, 3]:
                    is_perfect = True
            else:
                not_one_count: int = sum(1 for r in initial_rolls if r != 1)
                if not_one_count <= 1:
                    is_perfect = True

            six_count: int = sum(1 for r in initial_rolls if r == 6)
            is_fumble = (six_count >= 2)
            
            # Logga det hemliga slaget med perfekt/fummel-information för !ex
            roll_tracker.log_roll(
                user_id=str(ctx.author.id),
                user_name=ctx.author.display_name,
                command_type=f'secret_ex',
                num_dice=num_dice,
                sides=sides,
                roll_values=all_rolls,
                modifier=modifier,
                target=target,
                success=success if 'success' in locals() else None,
                is_perfect=is_perfect,
                is_fumble=is_fumble
            )
        else:
            # Logga vanliga hemliga slag utan perfekt/fummel-information
            roll_tracker.log_roll(
                user_id=str(ctx.author.id),
                user_name=ctx.author.display_name,
                command_type=f'secret_{command_type}',
                num_dice=num_dice,
                sides=sides,
                roll_values=rolls if command_type != "ex" else all_rolls,
                modifier=modifier,
                target=target,
                success=success if 'success' in locals() else None
            )"""
        
        # Ersätt hela det gamla blocket med det nya
        updated_function = function_content.replace(old_log_roll_block, new_log_roll_block)
        
        # Ersätt hela funktionsinnehållet
        updated_content = content[:start_pos] + updated_function
        
        # Skapa en säkerhetskopia om den inte redan finns
        backup_path = file_path + '.bak'
        if not os.path.exists(backup_path):
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Säkerhetskopia skapad: {backup_path}")
        
        # Spara den uppdaterade filen
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        
        print("secret_roll har uppdaterats med stöd för perfekta slag och fummel.")
        return True
    except Exception as e:
        print(f"Ett fel uppstod vid uppdatering av secret_roll: {e}")
        return False

if __name__ == "__main__":
    # Bestäm sökväg till main.py
    script_dir = Path(os.path.dirname(os.path.abspath(__file__)))
    project_root = script_dir.parent
    main_py_path = os.path.join(project_root, "src", "main.py")
    
    if not os.path.exists(main_py_path):
        print(f"main.py finns inte på den förväntade sökvägen: {main_py_path}")
        sys.exit(1)
    
    print("Det här skriptet kommer att uppdatera main.py för att lägga till stöd för")
    print("perfekta slag och fummel i !ex-kommandot och hemliga ex-kommandon.")
    print("En säkerhetskopia kommer att skapas innan ändringar görs.")
    
    answer = input("Vill du fortsätta? (j/n): ")
    if answer.lower() not in ['j', 'ja', 'y', 'yes']:
        print("Avbryter.")
        sys.exit(0)
    
    # Uppdatera ex_command och secret_roll
    ex_updated = modify_ex_command(main_py_path)
    secret_updated = modify_secret_roll(main_py_path)
    
    if ex_updated and secret_updated:
        print("\nBåda funktionerna har uppdaterats framgångsrikt!")
        print("Se till att köra 'python utils/migrate_database_perfect_fumble.py'")
        print("för att uppdatera databasen med kolumnerna för perfekta slag och fummel.")
        print("Starta sedan om boten för att aktivera ändringarna.")
        sys.exit(0)
    elif ex_updated or secret_updated:
        print("\nDelvis uppdatering slutförd.")
        print("Kör 'python utils/migrate_database_perfect_fumble.py' och starta om boten.")
        sys.exit(0)
    else:
        print("\nIngen uppdatering kunde göras.")
        print("Du kan behöva göra ändringarna manuellt. Se dokumentationen i skriptet.")
        sys.exit(1)
