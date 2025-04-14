import json
import os
import faiss
import numpy as np
from typing import List, Dict
from pathlib import Path
import ollama
from openai import OpenAI
from tqdm import tqdm
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))



EMBEDDING_DIM = 1536
BATCH_SIZE = 32



def load_chunks(folder_path: str, filter_source: str = None, include_images: bool = False) -> List[Dict]:
    all_chunks = []
    folder = Path(folder_path)
    for file in folder.glob("chunks_*.jsonl"):
        if not include_images and file.name in ("chunks_ppt_images.jsonl", "chunks_collateral_images.jsonl"):
            continue
        with open(file, 'r', encoding='utf-8') as f:
            file_chunks = []
            for line in f:
                if line.strip():
                    chunk = json.loads(line.strip())
                    if not filter_source or chunk.get("source") == filter_source:
                        file_chunks.append(chunk)
            print(f"Loaded {len(file_chunks)} chunks from {file.name}")
            all_chunks.extend(file_chunks)
    return all_chunks



# ----------------------------
# Embed using OpenAI (batched) → Ollama fallback (per chunk)
# ----------------------------
def embed_chunks(chunks: List[Dict], model_name: str = "nomic-embed-text") -> List[List[float]]:
    embeddings = []
    for i in tqdm(range(0, len(chunks), BATCH_SIZE), desc="Embedding text chunks"):
        batch = chunks[i:i + BATCH_SIZE]
        texts = [c.get("text", "").strip() for c in batch]
        try:
            response = client.embeddings.create(input=texts, model="text-embedding-3-small")
            for j in range(len(batch)):
                embeddings.append(response.data[j].embedding)
        except Exception as e:
            print(f"OpenAI batch failed: {e}. Falling back to Ollama per chunk.")
            for text in texts:
                try:
                    response = ollama.embeddings(model=model_name, prompt=text)
                    embeddings.append(response["embedding"])
                except Exception as ollama_e:
                    print(f"Ollama failed: {ollama_e}. Using zero vector.")
                    embeddings.append([0.0] * EMBEDDING_DIM)
    return embeddings



# ----------------------------
# Save FAISS index + metadata
# ----------------------------

def save_index(embeddings: List[List[float]], chunks: List[Dict], index_path: str, metadata_path: str):
    embedding_matrix = np.array(embeddings).astype("float32")
    index = faiss.IndexFlatL2(EMBEDDING_DIM)
    index.add(embedding_matrix)
    faiss.write_index(index, index_path)
    with open(metadata_path, 'w') as f:
        json.dump(chunks, f)
    print(f"✅ Saved FAISS text index and metadata ({len(chunks)} chunks).")



# ----------------------------
# Main
# ----------------------------
if __name__ == "__main__":
    chunks = load_chunks("/Users/sharvari/Downloads/CAFB_Challenge/outputs")
    embeddings = embed_chunks(chunks)
    save_index(embeddings, chunks, "/Users/sharvari/Downloads/CAFB_Challenge/outputs/faiss_index.index",
                "/Users/sharvari/Downloads/CAFB_Challenge/outputs/faiss_metadata.json")



