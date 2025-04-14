import json
import os
import faiss
import numpy as np
from typing import List, Dict
from pathlib import Path
from tqdm import tqdm
from openai import OpenAI
import ollama
from embedder import load_chunks
from dotenv import load_dotenv
import shutil

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

EMBEDDING_DIM = 1536  # or 1536 if you're using text-embedding-3-small
BATCH_SIZE = 32


# ----------------------------
# Load full collateral and ppt context
# ----------------------------
def load_text_context_map(json_path: str, mode: str) -> Dict[str, Dict[int, str]]:
    """Returns {file_name: {page_or_slide_number: text}}"""
    text_map = {}
    with open(json_path, 'r') as f:
        for line in f:
            obj = json.loads(line.strip())
            fname = obj['file_name']
            text_map[fname] = {}
            for para in obj['text_data']:
                number = para.get("page") if mode == "collateral" else para.get("slide")
                if number is not None:
                    text_map[fname].setdefault(number, [])
                    text_map[fname][number].append(para["text"])
            for num in text_map[fname]:
                text_map[fname][num] = " ".join(text_map[fname][num])
    return text_map


# ----------------------------
# Load image chunks and enrich with text + extra metadata
# ----------------------------
def load_image_chunks(folder_path: str,
                      collateral_map: Dict[str, Dict[int, str]],
                      ppt_map: Dict[str, Dict[int, str]]) -> List[Dict]:
    enriched_chunks = []
    folder = Path(folder_path)
    for fname in ["chunks_collateral_images.jsonl", "chunks_ppt_images.jsonl"]:
        with open(folder / fname, 'r', encoding='utf-8') as f:
            for line in f:
                chunk = json.loads(line.strip())
                meta = chunk.get("metadata", {})
                if fname == "chunks_collateral_images.jsonl":
                    source_file = meta.get("source_pdf")
                    page = meta.get("page_number")
                    context = collateral_map.get(source_file, {}).get(page, "")
                    chunk["source"] = "collateral_image"
                    chunk["title"] = source_file
                else:
                    source_file = meta.get("original_ppt")
                    page = meta.get("slide_number")
                    context = ppt_map.get(source_file, {}).get(page, "")
                    chunk["source"] = "powerpoint_image"
                    chunk["title"] = source_file

                # Enriched contextual text
                doc_type = "presentation slide" if "ppt" in fname else "report page"
                chunk["text"] = (
                    f"This image was extracted from {doc_type} {page} in {source_file}, a file related to the Capital Area Food Bank. "
                    f"The content of this visual may include themes like food programs, community partnerships, nutrition, or hunger relief. "
                    f"Page/slide context: {context}"
                ).strip()
                enriched_chunks.append(chunk)
    print(f"Loaded and enriched {len(enriched_chunks)} image chunks.")
    return enriched_chunks

                


#----------------------------
# Load image chunks (collateral + ppt)
# ----------------------------

def embed_chunks(chunks: List[Dict], model_name: str = "nomic-embed-text") -> List[List[float]]:
    embeddings = []
    for i in tqdm(range(0, len(chunks), BATCH_SIZE), desc="Embedding chunks"):
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
    print(f"✅ Saved FAISS image index and metadata ({len(chunks)} chunks).")

# ----------------------------
# Main
# ----------------------------
if __name__ == "__main__":
    collateral_map = load_text_context_map("/Users/sharvari/Downloads/CAFB_Challenge/data/collateral.jsonl", mode="collateral")
    ppt_map = load_text_context_map("/Users/sharvari/Downloads/CAFB_Challenge/data/powerpoints.jsonl", mode="ppt")

    enriched_chunks = load_image_chunks("outputs", collateral_map, ppt_map)
    embeddings = embed_chunks(enriched_chunks)

    old_index_path = "/Users/sharvari/Downloads/CAFB_Challenge/outputs/faiss_index_images.index"
    old_metadata_path = "/Users/sharvari/Downloads/CAFB_Challenge/outputs/faiss_metadata_images.json"

    if os.path.exists(old_index_path):
        shutil.copyfile(old_index_path, "/Users/sharvari/Downloads/CAFB_Challenge/outputs/faiss_index_images_backup.index")
        print("🗂️ Backed up previous FAISS index as faiss_index_images_backup.index")

    if os.path.exists(old_metadata_path):
        shutil.copyfile(old_metadata_path, "/Users/sharvari/Downloads/CAFB_Challenge/outputs/faiss_metadata_images_backup.json")
        print("🗂️ Backed up previous metadata as faiss_metadata_images_backup.json")

    save_index(embeddings, enriched_chunks, "/Users/sharvari/Downloads/CAFB_Challenge/outputs/faiss_index_images.index", "/Users/sharvari/Downloads/CAFB_Challenge/outputs/faiss_metadata_images.json")
