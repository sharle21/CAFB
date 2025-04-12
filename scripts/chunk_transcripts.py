import os
import json
import uuid
from pathlib import Path

# Paths
CAPTIONS_DIR = Path("../data/original/captions/")
OUTPUT_FILE = Path("../data/chunks/transcripts_chunks.json")
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

def chunk_transcripts():
    output = []

    for idx, file in enumerate(sorted(CAPTIONS_DIR.glob("*.txt"))):
        with open(file, 'r', encoding='utf-8') as f:
            text = f.read().strip()

        if not text:
            continue

        chunks = split_into_chunks(text)

        for chunk in chunks:
            output.append({
                "chunk_id": str(uuid.uuid4()),
                "file_name": file.name,
                "source": "transcript",
                "chunk_text": chunk,
                "original_file_id": idx
            })

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2)

    print(f"✅ Wrote {len(output)} chunks from {len(list(CAPTIONS_DIR.glob('*.txt')))} transcript files.")

if __name__ == "__main__":
    chunk_transcripts()
