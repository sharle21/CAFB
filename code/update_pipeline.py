import os
import json
from pathlib import Path
from embedder import embed_chunks, save_index, EMBEDDING_DIM
from chunk_utils import chunk_file  # You must have a `chunk_file()` method for single file chunking
from scan_util import scan_data_folder  # From the hashing code earlier
import faiss
import numpy as np
import uuid

# ---- Configs ----
DATA_FOLDER = "data"
OUTPUT_FOLDER = "outputs"
METADATA_PATH = f"{OUTPUT_FOLDER}/faiss_metadata.json"
INDEX_PATH = f"{OUTPUT_FOLDER}/faiss_index.index"
HASH_RECORD_PATH = f"{DATA_FOLDER}/file_hashes.json"

# ---- Step 1: Scan for new/changed files ----
scan_results = scan_data_folder(DATA_FOLDER, HASH_RECORD_PATH)
new_files = scan_results["updated_files"]
new_hash_record = scan_results["new_hash_record"]

if not new_files:
    print("✅ No new or changed files detected. FAISS index is up to date.")
    exit()

print(f"🔍 Detected {len(new_files)} new/updated files.")

# ---- Step 2: Chunk new files ----
all_new_chunks = []
for file_path in new_files:
    chunks = chunk_file(file_path)  # You must define this in chunker.py
    all_new_chunks.extend(chunks)
print(f"🧩 Created {len(all_new_chunks)} new text chunks.")

# ---- Step 3: Embed new chunks ----
new_embeddings = embed_chunks(all_new_chunks)
embedding_matrix = np.array(new_embeddings).astype("float32")

# ---- Step 4: Append to FAISS Index ----
if os.path.exists(INDEX_PATH):
    index = faiss.read_index(INDEX_PATH)
else:
    index = faiss.IndexFlatL2(EMBEDDING_DIM)
index.add(embedding_matrix)
faiss.write_index(index, INDEX_PATH)
print(f"📦 FAISS index updated with {len(new_embeddings)} new vectors.")

# ---- Step 5: Append to Metadata ----
if os.path.exists(METADATA_PATH):
    with open(METADATA_PATH, "r") as f:
        existing_metadata = json.load(f)
else:
    existing_metadata = []

updated_metadata = existing_metadata + all_new_chunks
with open(METADATA_PATH, "w") as f:
    json.dump(updated_metadata, f, indent=2)
print(f"📝 Metadata updated with {len(all_new_chunks)} new chunks.")

# ---- Step 6: Save updated file hash record ----
with open(HASH_RECORD_PATH, "w") as f:
    json.dump(new_hash_record, f, indent=2)

print("✅ Update pipeline complete.")
