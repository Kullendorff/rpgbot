import openai

# Importera API-nyckel från .env-fil istället för att hårdkoda den
import os
from dotenv import load_dotenv

# Ladda miljövariabler från .env
load_dotenv()

# Använd miljövariabel för API-nyckel
openai.api_key = os.getenv("OPENAI_API_KEY")  # Lägg till denna i din .env-fil

response = openai.Embedding.create(
    model="text-embedding-ada-002",
    input=["Hello world"]
)
print(response)
