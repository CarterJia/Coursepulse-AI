from __future__ import annotations

from typing import Any

# Maximum characters per chunk; pages shorter than this stay as one chunk.
MAX_CHUNK_CHARS = 1000
OVERLAP_CHARS = 100


def build_chunks(pages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Split extracted pages into searchable text chunks.

    Each page becomes one or more chunks depending on length.
    """
    chunks: list[dict[str, Any]] = []
    for page in pages:
        page_number = page["page_number"]
        text: str = page.get("text", "")
        if not text.strip():
            continue
        if len(text) <= MAX_CHUNK_CHARS:
            chunks.append({"page_number": page_number, "text": text, "chunk_index": 0})
        else:
            idx = 0
            start = 0
            while start < len(text):
                end = start + MAX_CHUNK_CHARS
                chunk_text = text[start:end]
                chunks.append({"page_number": page_number, "text": chunk_text, "chunk_index": idx})
                idx += 1
                start = end - OVERLAP_CHARS
    return chunks
