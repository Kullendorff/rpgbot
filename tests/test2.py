from pinecone import Pinecone, ServerlessSpec

# Använd din API-nyckel från .env-filen
api_key = "pcsk_4uVtzW_8cWQeAsBDqr3A4XAsNBuHfNEFDkUw5chVUcPgZTbeFpadyiNp2uR5TzrUpgZa32"
pc = Pinecone(api_key=api_key)

# Skapa ett nytt index
pc.create_index(
    name="rpg-knowledge",
    dimension=384,  # Dimension för all-MiniLM-L6-v2 modellen
    metric="cosine",
    spec=ServerlessSpec(cloud="aws", region="us-west-2")
)

print("Index skapat!")