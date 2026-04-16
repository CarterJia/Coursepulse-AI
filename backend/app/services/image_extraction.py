from __future__ import annotations

import hashlib
from pathlib import Path

import fitz

MIN_EDGE_PX = 150         # smaller → icon / bullet / decoration
MAX_ASPECT_RATIO = 3.0    # skinnier than 1:3 → separator bar / banner strip
SQUARISH_MAX_EDGE = 250   # tight squares this small are almost always logos / QR
SQUARISH_ASPECT = 1.15    # within ±15% of square
REPEAT_PAGE_RATIO = 0.30  # same image on ≥30% pages → header/footer/logo


def _should_keep(width: int, height: int) -> bool:
    """A-filter: reject by absolute size and shape."""
    if width < MIN_EDGE_PX or height < MIN_EDGE_PX:
        return False
    long_edge = max(width, height)
    short_edge = min(width, height)
    if long_edge / max(short_edge, 1) > MAX_ASPECT_RATIO:
        return False
    # Small square → logo / QR / avatar. Content figures tend to be wide.
    if long_edge < SQUARISH_MAX_EDGE and long_edge / max(short_edge, 1) < SQUARISH_ASPECT:
        return False
    return True


def extract_images(pdf_path: str, out_dir: str) -> dict[int, list[str]]:
    """Extract embedded images from a PDF, filtering out non-content visuals.

    Two-stage filter:
      A — size/ratio: drop icons, separators, small squares (likely logos/QRs).
      B — cross-page dedup: same image hash appearing on ≥30% of pages is
          flagged as header/footer/watermark and dropped entirely.

    Files are written as ``page_<n>_img_<k>.<ext>`` (1-indexed page, 0-indexed
    image slot). Returns manifest mapping page_number -> surviving filenames.
    Pages with no surviving images are omitted.
    """
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    # Collect survivors of A-filter, tagged with sha1 for B-filter.
    candidates: list[tuple[int, int, str, bytes, str]] = []  # (page, idx, ext, bytes, sha1)
    doc = fitz.open(pdf_path)
    try:
        total_pages = len(doc)
        for page_index in range(total_pages):
            page = doc[page_index]
            page_number = page_index + 1
            for img_idx, img_info in enumerate(page.get_images(full=False)):
                xref = img_info[0]
                try:
                    base = doc.extract_image(xref)
                except Exception:
                    continue
                width = base.get("width", 0)
                height = base.get("height", 0)
                if not _should_keep(width, height):
                    continue
                data = base["image"]
                sha1 = hashlib.sha1(data).hexdigest()
                ext = base.get("ext", "png")
                candidates.append((page_number, img_idx, ext, data, sha1))
    finally:
        doc.close()

    # B-filter: hashes that appear on ≥30% of pages get dropped.
    total_pages = max(total_pages, 1)
    hash_pages: dict[str, set[int]] = {}
    for page_number, _idx, _ext, _data, sha1 in candidates:
        hash_pages.setdefault(sha1, set()).add(page_number)
    banned_hashes = {
        h for h, pages in hash_pages.items()
        if len(pages) >= 2 and len(pages) / total_pages >= REPEAT_PAGE_RATIO
    }

    # Persist survivors, deduping within a page by hash too.
    manifest: dict[int, list[str]] = {}
    seen_per_page: dict[int, set[str]] = {}
    for page_number, img_idx, ext, data, sha1 in candidates:
        if sha1 in banned_hashes:
            continue
        page_seen = seen_per_page.setdefault(page_number, set())
        if sha1 in page_seen:
            continue
        page_seen.add(sha1)
        filename = f"page_{page_number}_img_{img_idx}.{ext}"
        (out_path / filename).write_bytes(data)
        manifest.setdefault(page_number, []).append(filename)

    return manifest
