from __future__ import annotations

from typing import Any


def retrieve_top_chunks(query: str, all_chunks: list[dict[str, Any]], top_k: int = 5) -> list[dict[str, Any]]:
    """Retrieve the most relevant chunks for a query.

    Placeholder: returns first top_k chunks. In production this performs
    vector similarity search against pgvector embeddings.
    """
    return all_chunks[:top_k]
