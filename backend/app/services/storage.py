import os
import uuid
from pathlib import Path


def save_upload(file_bytes: bytes, filename: str, sub_dir: str = "slides") -> str:
    root = os.getenv("FILE_STORAGE_ROOT", "/app/storage")
    dest_dir = Path(root) / sub_dir
    dest_dir.mkdir(parents=True, exist_ok=True)
    unique_name = f"{uuid.uuid4().hex}_{filename}"
    dest_path = dest_dir / unique_name
    dest_path.write_bytes(file_bytes)
    return str(dest_path)
