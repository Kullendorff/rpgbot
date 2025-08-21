#!/usr/bin/env python3
"""
Debug script för slash commands problem.
Kontrollerar permissions, sync status, och registrering.
"""

import sys
import os
import asyncio
import discord
from discord.ext import commands

# Lägg till projekt-root i path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)
sys.path.append(os.path.join(project_root, 'src'))

print("DEBUG: Slash Commands Troubleshooting")
print("=" * 50)

# Test 1: Kontrollera feature flags
print("1. Kontrollerar feature flags...")
try:
    from config.feature_flags import FEATURE_FLAGS, is_command_enabled
    print(f"   slash_dice_enabled: {FEATURE_FLAGS['slash_dice_enabled']}")
    print(f"   dual_mode_dice: {FEATURE_FLAGS['dual_mode_dice']}")
    print(f"   roll enabled: {is_command_enabled('roll', 'dice')}")
    print("   [OK] Feature flags loaded correctly")
except Exception as e:
    print(f"   [FAIL] Feature flags error: {e}")

# Test 2: Kontrollera slash commands registrering
print("\n2. Kontrollerar slash commands registrering...")
try:
    from src.commands.slash_dice_commands import DiceSlashCommands, register_slash_dice_commands
    print("   [OK] Slash commands importerade korrekt")
except Exception as e:
    print(f"   [FAIL] Import error: {e}")

# Test 3: Skapa en minimal test bot för att kontrollera sync
print("\n3. Skapar test bot för sync check...")

async def test_bot_sync():
    """Test bot sync utan att starta hela boten."""
    
    # Konfigurera minimal bot
    intents = discord.Intents.default()
    intents.message_content = True
    
    # Använd samma token som huvudboten
    from dotenv import load_dotenv
    load_dotenv()
    
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        print("   [FAIL] DISCORD_TOKEN inte hittad i .env")
        return
    
    bot = commands.Bot(command_prefix='!', intents=intents)
    
    @bot.event
    async def on_ready():
        print(f"   Bot inloggad som: {bot.user}")
        print(f"   Bot ID: {bot.user.id}")
        
        # Kontrollera nuvarande slash commands
        try:
            current_commands = await bot.tree.fetch_commands()
            print(f"   Nuvarande slash commands: {len(current_commands)}")
            for cmd in current_commands:
                print(f"     - /{cmd.name}: {cmd.description}")
        except Exception as e:
            print(f"   [ERROR] Kunde inte hämta commands: {e}")
        
        # Kontrollera bot permissions
        print(f"   Bot har följande permissions i guild:")
        for guild in bot.guilds:
            member = guild.get_member(bot.user.id)
            if member:
                perms = member.guild_permissions
                print(f"     Guild: {guild.name}")
                print(f"       - administrator: {perms.administrator}")
                print(f"       - manage_guild: {perms.manage_guild}")
                print(f"       - use_slash_commands: {perms.use_slash_commands}")
        
        # Test manuell sync
        print("   Försöker synka slash commands...")
        try:
            synced = await bot.tree.sync()
            print(f"   [OK] Synkade {len(synced)} slash commands")
            for cmd in synced:
                print(f"     - /{cmd.name}")
        except Exception as e:
            print(f"   [FAIL] Sync misslyckades: {e}")
        
        await bot.close()
    
    try:
        await bot.start(token)
    except Exception as e:
        print(f"   [FAIL] Bot start error: {e}")

# Test 4: Kontrollera om bot har rätt invite URL
print("\n4. Kontrollerar bot invite URL...")

def generate_invite_url():
    """Generera korrekt invite URL med slash commands permissions."""
    from dotenv import load_dotenv
    load_dotenv()
    
    # Hämta APPLICATION_ID från DISCORD_TOKEN eller manuellt
    print("   För att aktivera slash commands behöver boten re-invitas med rätt permissions:")
    print("   1. Gå till Discord Developer Portal")
    print("   2. Välj din bot application") 
    print("   3. Gå till OAuth2 > URL Generator")
    print("   4. Välj scopes: 'bot' OCH 'applications.commands'")
    print("   5. Välj bot permissions som behövs")
    print("   6. Använd den genererade URL:en för att re-invita boten")
    print()
    print("   VIKTIGT: Utan 'applications.commands' scope syns INGA slash commands!")

if __name__ == "__main__":
    print("\nKör async test...")
    try:
        asyncio.run(test_bot_sync())
    except KeyboardInterrupt:
        print("\n[INFO] Test avbruten av användare")
    except Exception as e:
        print(f"\n[ERROR] Async test error: {e}")
    
    print("\n" + "=" * 50)
    generate_invite_url()
    
    print("\nTroubleshooting steg:")
    print("1. Kontrollera console output från huvudboten")
    print("2. Re-invita boten med applications.commands scope")
    print("3. Vänta upp till 1 timme för Discord cache")
    print("4. Prova i en test-server först")