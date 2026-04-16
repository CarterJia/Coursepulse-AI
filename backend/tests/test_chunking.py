from app.services.chunking import build_chunks


def test_build_chunks_splits_pages_into_searchable_units():
    pages = [
        {"page_number": 1, "text": "Limits define continuity. Derivatives measure change."}
    ]
    chunks = build_chunks(pages)
    assert len(chunks) >= 1
    assert chunks[0]["page_number"] == 1
    assert "continuity" in chunks[0]["text"].lower()
