#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Patch-skript för att lägga till stöd för perfekta slag och fummel i ex-kommandot.
"""

import os
import re
import sys
from pathlib import Path

def patch_file(file_path):
    """
    Uppdaterar main.py för att lägga till stöd för perfekta slag och fummel i ex-kommandot.
    
    Args:
        file_path (str): Sökväg till main.py-filen
    
    Returns:
        bool: True om patchen lyckades, False annars
    """
    if not os.path.exists(file_path):
        print(f"Filen finns inte: {file_path}")
        return False
    
    # Läs in filen
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Gör säkerhetskopia
    backup_path = file_path + '.bak'
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Säkerhetskopia skapad: {backup_path}")
    
    # Patches att göra
    patches = [
        # 1. Uppdatera log_roll-anrop i ex-kommandot för att lägga till is_perfect och is_fumble
        {
            'pattern': r'(roll_tracker\.log_roll\(\s*user_id=str\(ctx\.author\.id\),\s*user_name=ctx\.author\.display_name,\s*command_type=\'ex\',\s*num_dice=num_dice,\s*sides=6,\s*roll_values=all_rolls,\s*modifier=modifier,\s*target=target,\s*success=success\s*\))',
            'replacement': r'roll_tracker.log_roll(\n            user_id=str(ctx.author.id),\n            user_name=ctx.author.display_name,\n            command_type=\'ex\',\n            num_dice=num_dice,\n            sides=6,\n            roll_values=all_rolls,\n            modifier=modifier,\n            target=target,\n            success=success,\n            is_perfect=perfect_candidate,\n            is_fumble=fumble_candidate\n        )'
        },
        
        # 2. Lägg till visuell indikation av perfekta slag och fummel i ex-kommandots utdata
        {
            'pattern': r'(if target is not None:\s*difference: int = target - final_total\s*embed\.add_field\(\s*name=f"Motståndsv[^"]*",\s*value=f"{result_text}\\n\(Marginal: {difference:.\d}\)",\s*inline=False\s*\)\s*else:\s*embed\.add_field\(name="Resultat", value=result_text, inline=False\))',
            'replacement': r'if target is not None:\n            difference: int = target - final_total\n            embed.add_field(\n                name=f"Motståndsv\\u00e4rde: {target}",\n                value=f"{result_text}\\n(Marginal: {difference:+d})",\n                inline=False\n            )\n        else:\n            embed.add_field(name="Resultat", value=result_text, inline=False)\n            \n        # Lägg till information om perfekt slag eller fummel\n        if perfect_candidate or fumble_candidate:\n            special_result = []\n            if perfect_candidate:\n                special_result.append("\\u2728 **PERFEKT SLAG!** Tärningsoraklet ler mot dig.")\n            if fumble_candidate:\n                special_result.append("\\ud83d\\udca5 **FUMMEL!** Tärningsoraklet skrattar åt din olycka.")\n                \n            embed.add_field(\n                name="Särskilt Utfall",\n                value="\\n".join(special_result),\n                inline=False\n            )'
        },
        
        # 3. Uppdatera secret_roll för att lägga till is_perfect och is_fumble för ex-kommandot
        {
            'pattern': r'(# Identifiera perfekta slag och fummel för hemliga slag.*?command_type=f\'secret_{command_type}\',[^)]*\))',
            'replacement': r'# Identifiera perfekta slag och fummel för hemliga obegränsade T6-slag\n        is_perfect = False\n        is_fumble = False\n        \n        if command_type == "ex":\n            # Använd den befintliga logiken från ex-kommandot för perfekta och fummel\n            if num_dice == 1:\n                if initial_rolls[0] in [1, 2, 3]:\n                    is_perfect = True\n            else:\n                not_one_count: int = sum(1 for r in initial_rolls if r != 1)\n                if not_one_count <= 1:\n                    is_perfect = True\n\n            six_count: int = sum(1 for r in initial_rolls if r == 6)\n            is_fumble = (six_count >= 2)\n            \n            # Logga det hemliga slaget med perfekt/fummel-information för !ex\n            roll_tracker.log_roll(\n                user_id=str(ctx.author.id),\n                user_name=ctx.author.display_name,\n                command_type=f\'secret_ex\',\n                num_dice=num_dice,\n                sides=sides,\n                roll_values=all_rolls,\n                modifier=modifier,\n                target=target,\n                success=success if \'success\' in locals() else None,\n                is_perfect=is_perfect,\n                is_fumble=is_fumble\n            )\n        else:\n            # Logga vanliga hemliga slag utan perfekt/fummel-information\n            roll_tracker.log_roll(\n                user_id=str(ctx.author.id),\n                user_name=ctx.author.display_name,\n                command_type=f\'secret_{command_type}\',\n                num_dice=num_dice,\n                sides=sides,\n                roll_values=rolls if command_type != "ex" else all_rolls,\n                modifier=modifier,\n                target=target,\n                success=success if \'success\' in locals() else None\n            )',
            'flags': re.DOTALL
        }
    ]
    
    # Applicera patches
    patched_content = content
    change_count = 0
    
    for patch in patches:
        flags = patch.get('flags', 0)
        pattern = re.compile(patch['pattern'], flags)
        match = pattern.search(patched_content)
        
        if match:
            # Ersätt den första förekomsten av mönstret
            patched_content = pattern.sub(patch['replacement'], patched_content, count=1)
            change_count += 1
            print(f"Ändring {change_count} lyckades.")
        else:
            print(f"Varning: Kunde inte hitta mönster för ändring {change_count + 1}.")
            print("Skriptet kanske behöver uppdateras för din version av main.py.")
    
    # Spara den patchade filen
    if change_count > 0:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(patched_content)
        print(f"Fil uppdaterad med {change_count} ändringar.")
        return True
    else:
        print("Inga ändringar gjordes.")
        return False

def verify_patches():
    """
    Kontrollerar att patch-skriptet har korrekt version av main.py och att patcharna är kompatibla.
    """
    print("Det här skriptet förutsätter att du använder en relativt ny version av main.py.")
    print("Skriptet kommer att göra en säkerhetskopia av din fil innan ändringar görs.")
    print("Om skriptet misslyckas, kan du återställa från säkerhetskopian (.bak-filen).")
    
    answer = input("Vill du fortsätta? (j/n): ")
    return answer.lower() in ['j', 'ja', 'y', 'yes']

if __name__ == "__main__":
    # Bestäm sökväg till main.py
    script_dir = Path(os.path.dirname(os.path.abspath(__file__)))
    project_root = script_dir.parent
    main_py_path = os.path.join(project_root, "src", "main.py")
    
    if not os.path.exists(main_py_path):
        print(f"main.py finns inte på den förväntade sökvägen: {main_py_path}")
        sys.exit(1)
    
    if not verify_patches():
        print("Avbryter.")
        sys.exit(0)
    
    print(f"Patchar filen: {main_py_path}")
    success = patch_file(main_py_path)
    
    if success:
        print("\nPatchning slutförd!")
        print("Kör 'python utils/migrate_database_perfect_fumble.py' för att uppdatera databasen.")
        print("Starta sedan om boten för att aktivera ändringarna.")
        sys.exit(0)
    else:
        print("\nPatchning misslyckades.")
        print("Du kan försöka göra ändringarna manuellt genom att följa instruktionerna i kommentarerna i skriptet.")
        sys.exit(1)
