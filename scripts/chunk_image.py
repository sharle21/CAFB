import os
import json
import uuid
from pathlib import Path

# Paths
IMAGES_DIR = Path("../data/original/images/")
OUTPUT_FILE = Path("../data/chunks/image_captions_chunks.json")
OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

def chunk_image_captions():
    output = []
    files = list(IMAGES_DIR.glob("*-images.jsonl"))

    if not files:
        print("⚠️ No *-images.jsonl files found in:", IMAGES_DIR)
        return

    for file_index, file in enumerate(files):
        with open(file, 'r', encoding='utf-8') as f:
            for line_index, line in enumerate(f):
                try:
                    item = json.loads(line)
                    caption = item.get("caption", "").strip()
                    image_name = item.get("image_file", "unknown")

                    if not caption:
                        continue

                    output.append({
                        "chunk_id": str(uuid.uuid4()),
                        "source": "image",
                        "chunk_text": caption,
                        "image_file": image_name,
                        "source_file": file.name,
                        "original_entry_id": line_index
                    })
                except Exception as e:
                    print(f"⚠️ Skipping line {line_index} in {file.name}: {e}")

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2)

    print(f"✅ Wrote {len(output)} image caption chunks from {len(files)} files.")

if __name__ == "__main__":
    chunk_image_captions()
