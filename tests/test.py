# test.py
import os
from dotenv import load_dotenv

load_dotenv()
token = os.getenv('DISCORD_TOKEN')
print(f"Token: {token}")