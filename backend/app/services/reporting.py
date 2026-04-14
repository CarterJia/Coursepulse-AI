"""Reporting service — two roles.

Legacy role (kept for backward compatibility):
  - ``build_report_prompt``: assembles a prompt from retrieval chunks.
  - ``generate_chapter_report``: calls DeepSeek to produce a section report.
    Used by the ``/reports/section`` API route and by ingestion.

New pipeline (Pass-2 topic writer):
  - ``generate_topic_card``: generates one topic card's Markdown via a single
    LLM call (DeepSeek, temperature 0.4).
  - ``generate_all_topic_cards``: dispatches N topic cards concurrently on a
    ``ThreadPoolExecutor`` (default 4 workers), preserving input order.
"""
from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from app.services.openai_client import get_openai_client
from app.services.prompts import CHAPTER_REPORT_PROMPT, TOPIC_WRITE_PROMPT

logger = logging.getLogger(__name__)

MAX_PASS2_WORKERS = 4


# ---------------------------------------------------------------------------
# Legacy functions — do NOT remove; still used by /reports/section and ingestion
# ---------------------------------------------------------------------------


def build_report_prompt(query: str, chunks: list[dict[str, Any]]) -> str:
    context_parts: list[str] = []
    for chunk in chunks:
        page = chunk.get("page_number", "?")
        text = chunk.get("text", "")
        context_parts.append(f"[Page {page}] {text}")
    context_block = "\n\n".join(context_parts)
    return (
        f"You are a teaching assistant. Using the following course material as context, "
        f"produce a clear, logically structured explanation.\n\n"
        f"## Context\n\n{context_block}\n\n"
        f"## Task\n\n{query}"
    )


def generate_chapter_report(chapter_title: str, context: str) -> str:
    client = get_openai_client()
    prompt = CHAPTER_REPORT_PROMPT.format(chapter_title=chapter_title, context=context)
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )
    return response.choices[0].message.content


# ---------------------------------------------------------------------------
# Pass-2 topic writer
# ---------------------------------------------------------------------------


def _build_topic_pages_block(pages: list[dict], source_pages: list[int]) -> str:
    wanted = set(source_pages)
    parts: list[str] = []
    for p in pages:
        if p["page_number"] in wanted:
            parts.append(f"[PAGE {p['page_number']}]\n{p['text']}")
    return "\n\n".join(parts)


def _build_image_paths_block(
    image_manifest: dict[int, list[str]],
    uses_pages: list[int],
    document_id: str,
) -> str:
    paths: list[str] = []
    for page in uses_pages:
        for filename in image_manifest.get(page, []):
            paths.append(f"/api/files/{document_id}/{filename}")
    if not paths:
        return "(无可用图片, 如需图示请输出 Mermaid 代码块)"
    return "\n".join(f"- {p}" for p in paths)


def generate_topic_card(
    topic: dict,
    pages: list[dict],
    image_manifest: dict[int, list[str]],
    document_id: str,
) -> str:
    """Pass-2: generate one topic card's Markdown."""
    client = get_openai_client()
    prompt = TOPIC_WRITE_PROMPT.format(
        topic_title=topic["title"],
        source_pages=topic["source_pages"],
        image_paths_block=_build_image_paths_block(
            image_manifest, topic["uses_images_from_pages"], document_id
        ),
        key_points="; ".join(topic["key_points"]) or "(无)",
        exam_tips="; ".join(topic["exam_tips"]) or "(无)",
        common_mistakes="; ".join(topic["common_mistakes"]) or "(无)",
        pages_block=_build_topic_pages_block(pages, topic["source_pages"]),
    )
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4,
    )
    return response.choices[0].message.content or ""


def generate_all_topic_cards(
    topics: list[dict],
    pages: list[dict],
    image_manifest: dict[int, list[str]],
    document_id: str,
    max_workers: int = MAX_PASS2_WORKERS,
) -> list[str]:
    """Run Pass-2 concurrently. Returns cards in the same order as topics."""
    if not topics:
        return []
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = [
            pool.submit(generate_topic_card, t, pages, image_manifest, document_id)
            for t in topics
        ]
        return [f.result() for f in futures]
