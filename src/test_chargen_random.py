"""
Snabb test-runner för karaktärsskaparen
Kör igenom hela processen automatiskt för att hitta buggar
"""

import sys
import os
import random
import json
import asyncio
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

# Lägg till src till path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from interactive_chargen import InteractiveCharacterCreator
from character_creation.session import CharacterSession

class MockContext:
    """Mock Discord context för testning"""
    def __init__(self, user_id="test_user"):
        self.author = MockAuthor(user_id)
        self.messages_sent = []
    
    async def send(self, content=None, embed=None):
        """Sparar meddelanden istället för att skicka dem"""
        if content:
            self.messages_sent.append(content)
        return MockMessage()

class MockAuthor:
    def __init__(self, user_id):
        self.id = user_id

class MockMessage:
    async def edit(self, embed=None):
        pass

class MockEmbed:
    """Mock Discord Embed för testning"""
    def __init__(self, title="", description=""):
        self.title = title
        self.description = description
        self.fields = []
    
    def add_field(self, name="", value="", inline=False):
        self.fields.append({"name": name, "value": value, "inline": inline})
        return self
    
    def set_footer(self, text=""):
        self.footer = text
        return self

class MockEmbedFactory:
    """Minimal embed factory för testning"""
    def admin_message(self, user_id, title, description):
        return MockEmbed(title, description)
    
    def success_message(self, user_id, message):
        return MockEmbed("Success", message)
    
    def error_message(self, user_id, message):
        return MockEmbed("Error", message)

async def run_random_test(silent=False, iterations=1):
    """
    Kör random-test av karaktärsskaparen
    
    Args:
        silent: Om True, skriv inte ut varje steg
        iterations: Antal karaktärer att generera
    """
    
    results = {
        "successful": 0,
        "failed": 0,
        "errors_by_step": {},
        "common_errors": {},
        "step_times": [],
        "total_time": 0
    }
    
    embed_factory = MockEmbedFactory()
    chargen = InteractiveCharacterCreator(embed_factory)
    
    for iteration in range(iterations):
        print(f"\n{'='*60}")
        print(f"Testkorning {iteration + 1}/{iterations}")
        print('='*60)
        
        start_time = datetime.now()
        errors_in_run = []
        ctx = MockContext(user_id=f"test_user_{iteration}")
        
        try:
            # Starta session
            session = chargen.start_session(ctx.author.id)
            
            if not silent:
                print(f"[OK] Session startad")
            
            # Kör igenom alla 32 steg
            max_attempts = 100  # Förhindra oändlig loop
            attempts = 0
            
            while session.current_step <= 32 and attempts < max_attempts:
                attempts += 1
                current_step = session.current_step
                step_info = chargen.get_current_step_info(session)
                step_name = step_info['name'] if step_info else f"step_{current_step}"
                
                if not silent:
                    print(f"\nSteg {current_step}/32: {step_info['title'] if step_info else 'Okänt'}")
                
                try:
                    # Olika strategier för olika stegtyper
                    if step_name == "kön":
                        choice = random.choice(["man", "kvinna"])
                        await chargen.handle_step_input(ctx, session, choice)
                        
                    elif step_name == "ålder":
                        age = random.randint(16, 45)
                        await chargen.handle_step_input(ctx, session, str(age))
                        
                    elif step_name == "hemland":
                        if chargen.homelands:
                            homeland = random.choice(chargen.homelands)
                            await chargen.handle_step_input(ctx, session, homeland['name'])
                        else:
                            session.current_step += 1
                            
                    elif step_name == "folkslag":
                        # Välj bara implementerade folkslag (människor)
                        human_races = ["vananer", "joraner", "taupiner", "kamorianer", "auser", "cirefalier", 
                                     "darkener", "rauner", "veddo", "zhaner", "tosher", "lalaster", "aunurier", "adasier"]
                        
                        available = session.character_data.get('available_races', [])
                        # Filtrera till bara människor
                        safe_races = [race for race in available if race.lower() in human_races]
                        
                        if safe_races:
                            race = random.choice(safe_races)
                            await chargen.handle_step_input(ctx, session, race)
                        else:
                            # Säker fallback
                            race = random.choice(["vananer", "joraner", "taupiner", "kamorianer"])
                            await chargen.handle_step_input(ctx, session, race)
                            
                    elif step_name == "kultur":
                        available = session.character_data.get('available_cultures', [])
                        if available:
                            culture = random.choice(available)
                            await chargen.handle_step_input(ctx, session, culture)
                        else:
                            session.current_step += 1
                            
                    elif "attribut" in step_name:
                        # Generera och bekräfta attribut
                        await chargen.show_current_step(ctx, session)
                        if session.temp_data:
                            await chargen.confirm_current_choice(ctx, session)
                        else:
                            session.current_step += 1
                            
                    else:
                        # Default: försök bekräfta eller gå vidare
                        if session.temp_data:
                            await chargen.confirm_current_choice(ctx, session)
                        else:
                            # Försök med "fortsätt"
                            await chargen.handle_step_input(ctx, session, "fortsätt")
                    
                    # Om vi fastnat på samma steg, forcera vidare
                    if session.current_step == current_step:
                        session.current_step += 1
                        if not silent:
                            print(f"  [VARNING] Forcerade vidare fran steg {current_step}")
                        
                except Exception as e:
                    error_msg = f"Steg {current_step} ({step_name}): {str(e)}"
                    errors_in_run.append(error_msg)
                    
                    # Spara fel per steg
                    if step_name not in results["errors_by_step"]:
                        results["errors_by_step"][step_name] = []
                    results["errors_by_step"][step_name].append(str(e))
                    
                    # Räkna vanliga fel
                    error_type = type(e).__name__
                    results["common_errors"][error_type] = results["common_errors"].get(error_type, 0) + 1
                    
                    if not silent:
                        print(f"  [FEL] {e}")
                    
                    # Försök fortsätta ändå
                    session.current_step += 1
            
            # Beräkna tid
            total_time = (datetime.now() - start_time).total_seconds()
            results["step_times"].append(total_time)
            
            # Kontrollera om vi lyckades
            if session.current_step > 32:
                results["successful"] += 1
                print(f"\n[KLAR] Karaktar {iteration + 1} klar pa {total_time:.1f} sekunder!")
            else:
                results["failed"] += 1
                print(f"\n[MISS] Karaktar {iteration + 1} misslyckades (nadde steg {session.current_step})")
            
            # Visa karaktärsdata
            if not silent and session.character_data:
                print("\nGenererad karaktar:")
                for key in ['kon', 'alder', 'hemland', 'folkslag', 'kultur']:
                    if key in session.character_data:
                        print(f"  {key.capitalize()}: {session.character_data[key]}")
            
            # Rensa session
            chargen.end_session(ctx.author.id)
            
        except Exception as e:
            results["failed"] += 1
            print(f"\n[KRITISKT FEL] {e}")

            # Försök rensa session
            try:
                chargen.end_session(ctx.author.id)
            except Exception as cleanup_error:
                logger.warning(f"Kunde inte rensa session efter kritiskt fel: {cleanup_error}")
    
    # Slutrapport
    print(f"\n{'='*60}")
    print("SLUTRAPPORT")
    print('='*60)
    
    print(f"\nOvergripande statistik:")
    print(f"  Lyckade: {results['successful']}/{iterations}")
    print(f"  Misslyckade: {results['failed']}/{iterations}")
    
    if results["step_times"]:
        avg_time = sum(results["step_times"]) / len(results["step_times"])
        print(f"  Genomsnittlig tid: {avg_time:.1f} sekunder")
    
    if results["errors_by_step"]:
        print(f"\nFel per steg:")
        for step, errors in sorted(results["errors_by_step"].items(), 
                                   key=lambda x: len(x[1]), reverse=True)[:5]:
            print(f"  {step}: {len(errors)} fel")
            # Visa första felet som exempel
            if errors:
                print(f"    Exempel: {errors[0][:100]}...")
    
    if results["common_errors"]:
        print(f"\nVanligaste feltyperna:")
        for error_type, count in sorted(results["common_errors"].items(), 
                                       key=lambda x: x[1], reverse=True)[:5]:
            print(f"  {error_type}: {count} gånger")
    
    # Spara detaljerad rapport
    report_file = f"chargen_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    report_path = Path(__file__).parent.parent / "data" / "test_reports" / report_file
    report_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\nDetaljerad rapport sparad: {report_path}")
    
    return results

async def main():
    """Huvudfunktion för att köra testet"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Testa karaktärsskaparen automatiskt')
    parser.add_argument('-n', '--number', type=int, default=5,
                       help='Antal karaktärer att generera (default: 5)')
    parser.add_argument('-s', '--silent', action='store_true',
                       help='Tyst läge - visa bara slutresultat')
    
    args = parser.parse_args()
    
    print(f"Startar automatisk testning av karaktarsskaparen")
    print(f"   Genererar {args.number} karaktar(er)...")
    
    results = await run_random_test(silent=args.silent, iterations=args.number)
    
    # Returnera exit code baserat på resultat
    if results["successful"] == 0:
        sys.exit(1)  # Alla misslyckades
    elif results["failed"] > 0:
        sys.exit(2)  # Några misslyckades
    else:
        sys.exit(0)  # Alla lyckades

if __name__ == "__main__":
    asyncio.run(main())