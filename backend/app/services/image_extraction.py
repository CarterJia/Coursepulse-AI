from __future__ import annotations

import os
from pathlib import Path

import fitz


def extract_images(pdf_path: str, out_dir: str) -> dict[int, list[str]]:
    """Extract all embedded images from a PDF.

    Writes files to `out_dir` with names `page_<n>_img_<k>.<ext>`
    (n is 1-indexed page number, k is 0-indexed image index).

    Returns a manifest mapping 1-indexed page number -> list of filenames
    (relative to out_dir). Pages with no images are omitted from the manifest.
    """
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    manifest: dict[int, list[str]] = {}
    doc = fitz.open(pdf_path)
    try:
        for page_index in range(len(doc)):
            page = doc[page_index]
            page_number = page_index + 1
            images = page.get_images(full=False)
            filenames: list[str] = []
            for img_idx, img_info in enumerate(images):
                xref = img_info[0]
                try:
                    base = doc.extract_image(xref)
                except Exception:
                    continue
                ext = base.get("ext", "png")
                filename = f"page_{page_number}_img_{img_idx}.{ext}"
                (out_path / filename).write_bytes(base["image"])
                filenames.append(filename)
            if filenames:
                manifest[page_number] = filenames
    finally:
        doc.close()
    return manifest
