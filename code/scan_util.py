# scan_util.py
import os
import json
import hashlib
from pathlib import Path
from typing import Dict

def calculate_file_hash(file_path: str) -> str:
    """Compute SHA-1 hash of a file."""
    h = hashlib.sha1()
    with open(file_path, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

def scan_data_folder(folder_path: str, hash_record_path: str = "data/file_hashes.json") -> Dict:
    """Compare file hashes to previous run. Return new/updated files and new hash record."""
    folder = Path(folder_path)
    previous_hashes = {}
    if os.path.exists(hash_record_path):
        with open(hash_record_path, "r") as f:
            previous_hashes = json.load(f)

    updated_files = []
    new_hashes = {}

    for file_path in folder.glob("**/*"):
        if file_path.is_file():
            path_str = str(file_path)
            new_hash = calculate_file_hash(path_str)
            new_hashes[path_str] = new_hash
            if path_str not in previous_hashes or previous_hashes[path_str] != new_hash:
                updated_files.append(path_str)

    return {
        "updated_files": updated_files,
        "new_hash_record": new_hashes
    }
