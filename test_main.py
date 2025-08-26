import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f"{bot.user} has connected to Discord!")
    
    # Just test syncing
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} slash commands with Discord")
        for cmd in synced:
            print(f"  - /{cmd.name}: {cmd.description}")
    except Exception as e:
        print(f'Failed to sync slash commands: {e}')
    
    print("Ready!")

if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)