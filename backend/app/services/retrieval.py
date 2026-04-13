from __future__ import annotations

from typing import Any

import sqlalchemy as sa
from sqlalchemy.orm import Session

from app.services.embedding import generate_embedding


def retrieve_top_chunks(
    db: Session, query: str, document_id: str, top_k: int = 5
) -> list[dict[str, Any]]:
    query_vector = generate_embedding(query)

    sql = sa.text("""
        SELECT kc.id, kc.text, kc.page_number, kc.chunk_index, kc.document_id
        FROM knowledge_chunks kc
        JOIN embeddings e ON e.chunk_id = kc.id
        WHERE kc.document_id = :doc_id
        ORDER BY e.vector <=> :query_vec
        LIMIT :top_k
    """)

    rows = db.execute(sql, {
        "doc_id": document_id,
        "query_vec": str(query_vector),
        "top_k": top_k,
    }).fetchall()

    return [
        {
            "id": str(row.id),
            "text": row.text,
            "page_number": row.page_number,
            "chunk_index": row.chunk_index,
            "document_id": str(row.document_id),
        }
        for row in rows
    ]
