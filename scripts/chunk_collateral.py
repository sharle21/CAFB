import os
import json
import uuid
from pathlib import Path

# Paths
INPUT_FILE = Path("../data/original/collateral.jsonl")
OUTPUT_FILE = Path("../data/chunks/collateral_chunks.json")

# Create output directory if needed
OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

TARGET_WORDS_PER_CHUNK = 400

def split_into_chunks(text, target_words=TARGET_WORDS_PER_CHUNK):
    sentences = text.split(". ")
    chunks = []
    current_chunk = []
    current_word_count = 0

    for sentence in sentences:
        words = sentence.split()
        word_count = len(words)

        if current_word_count + word_count > target_words and current_chunk:
            chunks.append(". ".join(current_chunk) + ".")
            current_chunk = [sentence]
            current_word_count = word_count
        else:
            current_chunk.append(sentence)
            current_word_count += word_count

    if current_chunk:
        chunks.append(". ".join(current_chunk) + ".")

    return chunks

def chunk_collateral():
    output = []

    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        for idx, line in enumerate(f):
            doc = json.loads(line)
            text_data = doc.get("text_data", [])

            combined_text = " ".join([entry.get("text", "") for entry in text_data]).strip()
            if not combined_text:
                continue

            chunks = split_into_chunks(combined_text)
            for chunk in chunks:
                output.append({
                    "chunk_id": str(uuid.uuid4()),
                    "title": doc.get("file_name", "Untitled"),
                    "source": "collateral",
                    "chunk_text": chunk,
                    "original_doc_id": idx
                })

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2)

    print(f"✅ Wrote {len(output)} chunks to {OUTPUT_FILE}")

if __name__ == "__main__":
    chunk_collateral()
