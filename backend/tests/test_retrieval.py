from unittest.mock import MagicMock, patch
from uuid import uuid4

from app.services.retrieval import retrieve_top_chunks


@patch("app.services.retrieval.generate_embedding")
def test_retrieve_top_chunks_queries_pgvector(mock_embed):
    mock_embed.return_value = [0.1] * 512

    mock_row = MagicMock()
    mock_row.id = uuid4()
    mock_row.text = "Limits define continuity"
    mock_row.page_number = 1
    mock_row.chunk_index = 0
    mock_row.document_id = uuid4()

    db = MagicMock()
    db.execute.return_value.fetchall.return_value = [mock_row]

    results = retrieve_top_chunks(db, "what are limits", document_id=str(mock_row.document_id), top_k=3)

    assert len(results) == 1
    assert results[0]["text"] == "Limits define continuity"
    mock_embed.assert_called_once_with("what are limits")
