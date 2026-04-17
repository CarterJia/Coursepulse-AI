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
import os
import re
import uuid as _uuid
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.report import Report
from app.services.openai_client import get_openai_client
from app.services.prompts import CHAPTER_REPORT_PROMPT, TOPIC_WRITE_PROMPT
from app.services.report_planner import (
    PlanValidationError,
    build_fallback_plan,
    generate_plan,
)
from app.services.video_recommender import recommend_videos_for_document

logger = logging.getLogger(__name__)

MAX_PASS2_WORKERS = 4

_IMG_PATTERN = re.compile(r"!\[([^\]]*)\]\(/api/files/([^/]+)/([^)]+)\)")

# Matches a line that contains ONLY an inline-math expression (no other text,
# optional ** bold ** wrapper). Captures the math body. Multiline so we can
# find it anywhere in the card body. Non-greedy inside the $...$.
_LONE_INLINE_MATH = re.compile(
    r"^\s*(?:\*\*)?\s*\$([^\$\n]+?)\$\s*(?:\*\*)?\s*$",
    re.MULTILINE,
)

# Same-line $$...$$ — remark-math v6 treats this as *inline*, not display, so
# no ``.katex-display`` class is emitted and our amber frame never triggers.
# Lift it into the three-line canonical form that remark-math recognizes.
_SAME_LINE_DOUBLE_DOLLAR = re.compile(r"\$\$([^\n]+?)\$\$")

# Mermaid fenced code block. We re-wrap unquoted node labels because the LLM
# forgets our "quote labels with parens/commas" rule and breaks the renderer.
_MERMAID_BLOCK = re.compile(r"```mermaid\n(.*?)```", re.DOTALL)
_MERMAID_LABEL_UNSAFE = re.compile(r"[(),;:/\\]")


def _quote_mermaid_labels(code: str) -> str:
    """Wrap unquoted node labels containing special chars in double quotes.

    Mermaid treats `A[N(s,a)]` as a syntax error because the unescaped ``(``
    in the label confuses the parser. The fix is `A["N(s,a)"]`. We do the
    same for diamonds (`{...}`). Paren nodes `(...)` are left alone — they
    collide with mermaid's own round-node syntax and are rarely used by the
    LLM anyway.
    """
    def fix(match: "re.Match[str]") -> str:
        opener, content, closer = match.group(1), match.group(2), match.group(3)
        if '"' in content or not _MERMAID_LABEL_UNSAFE.search(content):
            return match.group(0)
        return f'{opener}"{content.strip()}"{closer}'

    # Square-bracket labels: `A[label]`
    code = re.sub(r"(\[)([^\[\]\n]+?)(\])", fix, code)
    # Diamond labels: `A{label}`
    code = re.sub(r"(\{)([^\{\}\n]+?)(\})", fix, code)
    return code


def _fix_mermaid_blocks(body: str) -> str:
    return _MERMAID_BLOCK.sub(
        lambda m: f"```mermaid\n{_quote_mermaid_labels(m.group(1))}```",
        body,
    )

# Leading "### 主题: X" or "主题: X" / "**主题：X**" — the LLM sometimes still
# emits these despite the prompt forbidding it. The AccordionTrigger already
# shows the title, so the duplicate just adds visual noise.
_LEADING_TITLE_RE = re.compile(
    r"\A(?:\s*(?:#{1,6}\s*)?\*?\*?\s*主题[:：].*?\n+)+",
    re.DOTALL,
)


def _postprocess_topic_card(body: str) -> str:
    """Clean up common LLM formatting drift that the prompt alone can't fix."""
    # 1. Strip "主题: xxx" duplicate headers (any leading stack of them).
    body = _LEADING_TITLE_RE.sub("", body)
    # 2. Lift lone-line $...$ to three-line $$ block so remark-math sees it as display.
    body = _LONE_INLINE_MATH.sub(
        lambda m: f"\n\n$$\n{m.group(1).strip()}\n$$\n\n", body
    )
    # 3. Same-line $$X$$ also gets expanded to three-line form; remark-math v6
    #    refuses to treat same-line $$ as display math.
    body = _SAME_LINE_DOUBLE_DOLLAR.sub(
        lambda m: f"\n\n$$\n{m.group(1).strip()}\n$$\n\n", body
    )
    # 4. Repair unquoted Mermaid node labels so the diagram actually renders.
    body = _fix_mermaid_blocks(body)
    return body


def _strip_missing_images(body: str, document_id: str, derived_root: str) -> str:
    """Remove markdown image refs whose files don't exist under derived_root.

    Hallucinated-path defense: the LLM sometimes references image files it
    imagines (e.g. ``page_7_img_0.png``) that PyMuPDF never extracted.
    Rather than showing a broken-image placeholder, we strip the entire
    ``![](...)`` ref before insert. Refs that exist pass through unchanged.
    """

    def replace(match: "re.Match[str]") -> str:
        ref_doc_id, filename = match.group(2), match.group(3)
        if ref_doc_id != document_id:
            return ""  # wrong doc id → hallucinated
        full_path = os.path.join(derived_root, "derived", ref_doc_id, filename)
        if not os.path.isfile(full_path):
            return ""  # file not on disk → hallucinated
        return match.group(0)

    return _IMG_PATTERN.sub(replace, body)


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


def generate_chapter_report(chapter_title: str, context: str, api_key: str | None = None) -> str:
    client = get_openai_client(api_key=api_key)
    prompt = CHAPTER_REPORT_PROMPT.format(chapter_title=chapter_title, context=context)
    response = client.chat.completions.create(
        model=settings.llm_model,
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
    api_key: str | None = None,
) -> str:
    """Pass-2: generate one topic card's Markdown."""
    client = get_openai_client(api_key=api_key)
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
        model=settings.llm_model,
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
    api_key: str | None = None,
) -> list[str]:
    """Run Pass-2 concurrently. Returns cards in the same order as topics."""
    if not topics:
        return []
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = [
            pool.submit(
                generate_topic_card, t, pages, image_manifest, document_id, api_key=api_key
            )
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
    return "\n".join(f"- {item}" for item in items)


def run_report_pipeline(
    db: Session,
    document_id: _uuid.UUID,
    pages: list[dict],
    image_manifest: dict[int, list[str]],
    api_key: str | None = None,
) -> None:
    """Two-pass pipeline: Pass-1 plan -> Pass-2 topic cards -> write all rows to `reports`.

    Caller commits. On Pass-1 total failure, falls back to page-based plan.
    Every section body is scrubbed of hallucinated image refs before insert.
    """
    # Pass 1
    try:
        plan = generate_plan(pages, image_manifest, max_retries=5, api_key=api_key)
        logger.info("Pass-1 plan generated for document %s", document_id)
    except PlanValidationError as e:
        logger.warning("Pass-1 failed for %s (%s); using fallback plan", document_id, e)
        plan = build_fallback_plan(pages)

    # Pass 2 (concurrent)
    topic_cards = generate_all_topic_cards(
        plan["topics"], pages, image_manifest, document_id=str(document_id), api_key=api_key
    )

    doc_id_str = str(document_id)
    derived_root = settings.file_storage_root

    def _clean(body: str) -> str:
        return _strip_missing_images(body, doc_id_str, derived_root)

    # Write rows
    db.add(Report(
        id=_uuid.uuid4(),
        document_id=document_id,
        title="课件概览",
        body=_clean(plan["overview"]),
        section_type="overview",
    ))
    db.add(Report(
        id=_uuid.uuid4(),
        document_id=document_id,
        title="核心要点速览",
        body=_clean(_render_tldr_body(plan["tldr"])),
        section_type="tldr",
    ))
    for topic, card_body in zip(plan["topics"], topic_cards):
        db.add(Report(
            id=_uuid.uuid4(),
            document_id=document_id,
            title=topic["title"],
            body=_clean(_postprocess_topic_card(card_body)),
            section_type="topic",
        ))
    db.add(Report(
        id=_uuid.uuid4(),
        document_id=document_id,
        title="考点与易错点汇总",
        body=_clean(_render_exam_summary_body(plan["exam_summary"])),
        section_type="exam_summary",
    ))
    db.add(Report(
        id=_uuid.uuid4(),
        document_id=document_id,
        title="30 分钟急救包",
        body=_clean(_render_quick_review_body(plan["quick_review"])),
        section_type="quick_review",
    ))

    # Video recommendations (non-blocking: failure does not affect reports)
    try:
        recommend_videos_for_document(db, document_id, plan["topics"])
    except Exception:
        logger.exception("Video recommendation failed for document %s", document_id)
