from __future__ import annotations

from pathlib import Path
from typing import Any

import pymupdf


def extract_pages(file_path: str) -> list[dict[str, Any]]:
    """Extract text content from each page of a PDF using PyMuPDF."""
    pages: list[dict[str, Any]] = []
    doc = pymupdf.open(file_path)
    for page_num, page in enumerate(doc, start=1):
        text = page.get_text()
        pages.append({"page_number": page_num, "text": text.strip()})
    doc.close()
    return pages


def extract_pages_from_bytes(data: bytes, filename: str = "doc.pdf") -> list[dict[str, Any]]:
    """Extract pages from in-memory PDF bytes."""
    tmp = Path("/tmp") / filename
    tmp.write_bytes(data)
    try:
        return extract_pages(str(tmp))
    finally:
        tmp.unlink(missing_ok=True)
