from pathlib import Path
from typing import List, Dict
import json

def chunk_file(file_path: str) -> List[Dict]:
    from chunk_utils import (
        chunk_blog_post, chunk_grant_proposal, chunk_powerpoint,
        chunk_collateral, chunk_video_captions,
        chunk_powerpoint_images, chunk_collateral_images
    )

    file = Path(file_path)
    doc_id = file.stem

    if file_path.endswith(".jsonl") and "blog" in file.parts:
        with open(file_path, "r", encoding="utf-8") as f:
            return [chunk for i, line in enumerate(f) if line.strip()
                    for chunk in chunk_blog_post(json.loads(line), f"blog_{i:03d}")]
    
    elif file_path.endswith(".json") and "grants" in file.parts:
        with open(file_path, "r") as f:
            return chunk_grant_proposal(json.load(f), doc_id)

    elif file_path.endswith(".json") and "collateral" in file.parts:
        with open(file_path, "r") as f:
            return chunk_collateral(json.load(f), doc_id)

    elif file_path.endswith(".json") and "powerpoint" in file.parts:
        with open(file_path, "r") as f:
            return chunk_powerpoint(json.load(f), doc_id)

    elif file_path.endswith(".txt") and "captions" in file.parts:
        title = file.stem.replace("_", " ")
        return chunk_video_captions(str(file), title, doc_id)

    elif file_path.endswith(".json") and "ppt_images" in file.parts:
        with open(file_path, "r") as f:
            return chunk_powerpoint_images(json.load(f), doc_id)

    elif file_path.endswith(".json") and "collateral_images" in file.parts:
        with open(file_path, "r") as f:
            return chunk_collateral_images(json.load(f), doc_id)

    else:
        print(f"⚠️ Unsupported file for chunking: {file_path}")
        return []
