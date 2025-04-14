import json
import os
import faiss
import numpy as np
from typing import List, Dict, Optional
from pathlib import Path
import ollama
from openai import OpenAI
from tqdm import tqdm

from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

EMBEDDING_DIM = 1536

# ----------------------------
# Load FAISS index and metadata
# ----------------------------
def load_faiss_and_metadata(index_path: str, metadata_path:str):
    index = faiss.read_index(index_path)
    with open(metadata_path, 'r') as f:
        metadata = json.load(f)
    print(f"Loaded FAISS index with {index.ntotal} vectors and {len(metadata)} metadata entries.")
    return index, metadata

# ----------------------------
# Embed a user query (OpenAI -> Ollama fallback)
# ----------------------------
def embed_query(text: str, model_name: str = "nomic-embed-text") -> List[Dict]:

    if text.strip():
        try:
            response = client.embeddings.create(input=text,model="text-embedding-3-small")
            return response.data[0].embedding
        except Exception as e:
            print(f"OpenAI embedding failed: {e}. Trying Ollama...")
            try:
                
                response = ollama.embeddings(model=model_name, prompt=text)
                return response["embedding"]
            except Exception as ollama_e:
                print(f"Ollama embedding also failed: {ollama_e}. Returning zero vector.")
                return [0.0] * EMBEDDING_DIM
    return [0.0] * EMBEDDING_DIM


#----------------------------
# Retrieve top-k similar chunks
# ----------------------------

def retrieve_top_k(index, metadata, query_vector, k=5):
    D, I = index.search(np.array([query_vector], dtype="float32"), k)
    results = []
    for i, score in zip(I[0], D[0]):
        if i < len(metadata):
            chunk = metadata[i]
            results.append({
                "score": round(float(score), 2),
                "source": chunk.get("source", ""),
                "title": chunk.get("title", ""),
                "text": chunk.get("text", "")[:500]  # limit preview
            })
    return results


    # filtered_results = results
    # if filter_sources:
    #     filtered_results = [r for r in results if r.get("source") in filter_sources]
    #     if not filtered_results:
    #         print("⚠️ No results after filtering by source — falling back to unfiltered results.")
    #         filtered_results = results

    # Sort and return top-k overall
    # sorted_results = sorted(filtered_results, key=lambda x: x["score"])
    # return sorted_results[:k]

    # return {"text": text_results, "image": img_results}



# ----------------------------
# Generate output with GPT-4 based on retrieved context
# ----------------------------
def generate_with_gpt(query: str, top_k: int = 5) -> str:
    # Load indexes
    text_index, text_meta = load_faiss_and_metadata("/Users/sharvari/Downloads/CAFB_Challenge/outputs/faiss_index.index", "/Users/sharvari/Downloads/CAFB_Challenge/outputs/faiss_metadata.json")
    image_index, image_meta = load_faiss_and_metadata("/Users/sharvari/Downloads/CAFB_Challenge/outputs/faiss_index_images.index", "/Users/sharvari/Downloads/CAFB_Challenge/outputs/faiss_metadata_images.json")

    # Embed query
    query_vec = embed_query(query)

    # Retrieve top-k chunks
    text_results = retrieve_top_k(text_index, text_meta, query_vec, k=top_k)
    image_results = retrieve_top_k(image_index, image_meta, query_vec, k=2)

    # Combine text and image context
    combined_texts = [r["text"] for r in text_results + image_results]
    combined_context = "\n\n".join(combined_texts)[:3000]  # Limit token length for prompt

    # Create GPT prompt
    prompt = (
        f"You are a helpful assistant for the Capital Area Food Bank.\n"
        f"Based on the following retrieved information, write a clear and concise answer to the user's query:\n"
        f"\n---\n{combined_context}\n---\n\nUser question: {query}\n\nAnswer:"
    )

    # Call GPT-4
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a nonprofit expert who writes helpful summaries."},
            {"role": "user", "content": prompt}
        ]
    )

    return response.choices[0].message.content.strip()



#----------------------------
# Main: Search text + image indexes
# ----------------------------
if __name__ == "__main__":
    query = input("Enter your query: ")
    query_vec = embed_query(query)

    # Load text index and search
    text_index, text_meta = load_faiss_and_metadata("/Users/sharvari/Downloads/CAFB_Challenge/outputs/faiss_index.index", "/Users/sharvari/Downloads/CAFB_Challenge/outputs/faiss_metadata.json")
    text_results = retrieve_top_k(text_index, text_meta, query_vec, k=5)

    # Load image index and search
    image_index, image_meta = load_faiss_and_metadata("/Users/sharvari/Downloads/CAFB_Challenge/outputs/faiss_index_images.index", "/Users/sharvari/Downloads/CAFB_Challenge/outputs/faiss_metadata_images.json")
    #image_results = retrieve_top_k(image_index, image_meta, query_vec, k=3)
    raw_image_results = retrieve_top_k(image_index, image_meta, query_vec, k=10)

    seen = set()
    image_results = []
    for r in raw_image_results:
        key = (r['title'], r['text'][:100])  # or use image_name if available
        if key not in seen:
            seen.add(key)
            image_results.append(r)
        if len(image_results) >= 3:  # limit final results
            break


    # Show results
    print("\n\U0001F4C4 Top Text Results:")
    for r in text_results:
        print(f"\nText ({r['score']}): {r['title']}\n{r['text']}")

    print("\n\U0001F5BC️ Top Image Results:")
    for r in image_results:
        print(f"\nImage ({r['score']}): {r['title']}\n{r['text']}")
