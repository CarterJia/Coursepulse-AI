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
import uuid as _uuid
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from sqlalchemy.orm import Session

from app.models.report import Report
from app.services.openai_client import get_openai_client
from app.services.prompts import CHAPTER_REPORT_PROMPT, TOPIC_WRITE_PROMPT
from app.services.report_planner import (
    PlanValidationError,
    build_fallback_plan,
    generate_plan,
)

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


# ---------------------------------------------------------------------------
# Pipeline orchestration
# ---------------------------------------------------------------------------


def _render_tldr_body(tldr: list[str]) -> str:
    return "\n".join(f"- {item}" for item in tldr)


def _render_exam_summary_body(exam_summary: dict) -> str:
    lines: list[str] = ["### 🔥 必考清单\n"]
    for item in exam_summary.get("must_know", []):
        lines.append(f"- {item}")
    lines.append("\n### 💣 整体易错点\n")
    for item in exam_summary.get("common_pitfalls", []):
        lines.append(f"- {item}")
    return "\n".join(lines)


def _render_quick_review_body(items: list[str]) -> str:
    return "\n".join(f"{i+1}. {item}" for i, item in enumerate(items))


def run_report_pipeline(
    db: Session,
    document_id: _uuid.UUID,
    pages: list[dict],
    image_manifest: dict[int, list[str]],
) -> None:
    """Two-pass pipeline: Pass-1 plan -> Pass-2 topic cards -> write all rows to `reports`.

    Caller commits. On Pass-1 total failure, falls back to page-based plan.
    """
    # Pass 1
    try:
        plan = generate_plan(pages, image_manifest, max_retries=5)
        logger.info("Pass-1 plan generated for document %s", document_id)
    except PlanValidationError as e:
        logger.warning("Pass-1 failed for %s (%s); using fallback plan", document_id, e)
        plan = build_fallback_plan(pages)

    # Pass 2 (concurrent)
    topic_cards = generate_all_topic_cards(
        plan["topics"], pages, image_manifest, document_id=str(document_id)
    )

    # Write rows
    db.add(Report(
        id=_uuid.uuid4(),
        document_id=document_id,
        title="课件概览",
        body=plan["overview"],
        section_type="overview",
    ))
    db.add(Report(
        id=_uuid.uuid4(),
        document_id=document_id,
        title="核心要点速览",
        body=_render_tldr_body(plan["tldr"]),
        section_type="tldr",
    ))
    for topic, card_body in zip(plan["topics"], topic_cards):
        db.add(Report(
            id=_uuid.uuid4(),
            document_id=document_id,
            title=topic["title"],
            body=card_body,
            section_type="topic",
        ))
    db.add(Report(
        id=_uuid.uuid4(),
        document_id=document_id,
        title="考点与易错点汇总",
        body=_render_exam_summary_body(plan["exam_summary"]),
        section_type="exam_summary",
    ))
    db.add(Report(
        id=_uuid.uuid4(),
        document_id=document_id,
        title="30 分钟急救包",
        body=_render_quick_review_body(plan["quick_review"]),
        section_type="quick_review",
    ))
