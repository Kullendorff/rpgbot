import os
import faiss
import openai
import numpy as np
import nltk
import tiktoken
import time
from dotenv import load_dotenv

# 1. Ladda din .env om du vill hämta OpenAI-nyckeln därifrån.
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY  # Ställ in API-nyckeln

# 2. Ladda ner NLTK:s punkt-tokenizer (bara första gången).
nltk.download('punkt')

BATCH_SIZE = 10  # Antal chunkar att batcha per API-anrop

def split_text_into_chunks(text: str, max_tokens: int = 500, overlap: int = 50) -> list:
    """Delar upp texten i chunkar med en ungefärlig övre gräns (max_tokens)."""
    encoder = tiktoken.encoding_for_model("gpt-4")
    sentences = nltk.sent_tokenize(text)

    chunks = []
    current_chunk = []
    current_size = 0

    for sent in sentences:
        sent_size = len(encoder.encode(sent))

        if current_size + sent_size > max_tokens:
            chunks.append(" ".join(current_chunk))

            if overlap > 0:
                overlap_text = current_chunk[-overlap:] if overlap < len(current_chunk) else current_chunk
                current_chunk = overlap_text[:]
                current_size = sum(len(encoder.encode(s)) for s in current_chunk)
            else:
                current_chunk = []
                current_size = 0

        current_chunk.append(sent)
        current_size += sent_size

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks

def load_knowledge_chunks(file_path: str = "full_knowledge.txt", max_tokens: int = 500, overlap: int = 50) -> list:
    """Läser in en textfil och delar upp den i chunkar."""
    with open(file_path, "r", encoding="utf-8") as f:
        raw_text = f.read()

    sections = raw_text.split("### ")
    all_chunks = []

    for sec in sections:
        sec = sec.strip()
        if not sec:
            continue
        
        lines = sec.split("\n", 1)
        if len(lines) == 2:
            pdf_name, pdf_text = lines[0], lines[1]
            chunked = split_text_into_chunks(pdf_text, max_tokens=max_tokens, overlap=overlap)
            for ch in chunked:
                labeled_chunk = f"[{pdf_name}]\n{ch}"
                all_chunks.append(labeled_chunk)
        else:
            all_chunks.append(sec)

    return all_chunks

def get_embeddings(texts: list) -> np.ndarray:
    """Skapar embeddings i batchar för att snabba upp processen."""
    response = openai.Embedding.create(
        model="text-embedding-ada-002",
        input=texts
    )
    return np.array([d["embedding"] for d in response["data"]], dtype=np.float32)

def create_faiss_index(knowledge_chunks: list, index_file: str = "knowledge_index.faiss", texts_file: str = "knowledge_texts.npy") -> None:
    """Skapar ett FAISS-index av givna text-chunkar."""
    dimension = 1536  # dimension för text-embedding-ada-002
    index = faiss.IndexFlatL2(dimension)

    embeddings = []
    start_time = time.time()

    for i in range(0, len(knowledge_chunks), BATCH_SIZE):
        batch = knowledge_chunks[i:i + BATCH_SIZE]
        try:
            batch_embeddings = get_embeddings(batch)
            embeddings.extend(batch_embeddings)
        except Exception as e:
            print(f"❌ Fel vid embedding av batch {i}-{i+len(batch)}: {e}")
            # Lägg till nollvektorer för att hantera misslyckade anrop
            for _ in batch:
                embeddings.append(np.zeros(dimension, dtype=np.float32))

        # Statusuppdatering var 1000:e chunk
        if (i + BATCH_SIZE) % 1000 < BATCH_SIZE:
            elapsed_time = time.time() - start_time
            processed = i + BATCH_SIZE
            estimated_total_time = (elapsed_time / processed) * len(knowledge_chunks)
            remaining_time = estimated_total_time - elapsed_time

            print(f"✅ {processed}/{len(knowledge_chunks)} chunkar bearbetade. "
                  f"Uppskattad återstående tid: {remaining_time / 60:.1f} min")

    embeddings_np = np.array(embeddings, dtype=np.float32)
    index.add(embeddings_np)

    # Spara index
    faiss.write_index(index, index_file)
    np.save(texts_file, np.array(knowledge_chunks, dtype=object), allow_pickle=True)

    print(f"✅ FAISS-index skapat och sparat som '{index_file}'")
    print(f"✅ Text-chunkar sparade i '{texts_file}'")
    print(f"Totalt antal chunkar: {len(knowledge_chunks)}")

if __name__ == "__main__":
    knowledge_chunks = load_knowledge_chunks(
        file_path="full_knowledge.txt",
        max_tokens=500,
        overlap=50
    )

    print(f"Läste in {len(knowledge_chunks)} chunkar. Exempel på en chunk:")
    print("------------------------------------------------------------")
    print(knowledge_chunks[0][:300], "...")
    print("------------------------------------------------------------")

    create_faiss_index(
        knowledge_chunks,
        index_file="knowledge_index.faiss",
        texts_file="knowledge_texts.npy"
    )
