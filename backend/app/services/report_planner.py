"""Pass-1 plan generation: validator, LLM call with retry, fallback.

This file evolves across Task 4 (validator), Task 5 (generate_plan), Task 6 (fallback).
"""

from __future__ import annotations

import json
import logging
from typing import Any

from app.services.openai_client import get_openai_client
from app.services.prompts import REPORT_PLAN_PROMPT, build_retry_prompt

logger = logging.getLogger(__name__)


class PlanValidationError(ValueError):
    pass


def _require(plan: dict, key: str) -> Any:
    if key not in plan:
        raise PlanValidationError(f"Missing required key: {key}")
    return plan[key]


def _require_list(value: Any, label: str) -> list:
    if not isinstance(value, list):
        raise PlanValidationError(f"{label} must be a list, got {type(value).__name__}")
    return value


def _require_list_of_ints(value: Any, label: str) -> list[int]:
    value = _require_list(value, label)
    for item in value:
        if not isinstance(item, int) or isinstance(item, bool):
            raise PlanValidationError(f"{label} must contain ints, got {type(item).__name__}")
    return value


def validate_plan(plan: Any, max_page: int) -> None:
    """Raise PlanValidationError if plan does not match the expected schema.

    max_page is the highest valid 1-indexed page number in the source PDF.
    """
    if not isinstance(plan, dict):
        raise PlanValidationError(f"plan must be a dict, got {type(plan).__name__}")

    overview = _require(plan, "overview")
    if not isinstance(overview, str) or not overview.strip():
        raise PlanValidationError("overview must be a non-empty string")

    tldr = _require_list(_require(plan, "tldr"), "tldr")
    for item in tldr:
        if not isinstance(item, str):
            raise PlanValidationError("tldr items must be strings")

    topics = _require_list(_require(plan, "topics"), "topics")
    if not topics:
        raise PlanValidationError("topics must not be empty")
    for i, t in enumerate(topics):
        if not isinstance(t, dict):
            raise PlanValidationError(f"topics[{i}] must be a dict")
        for key in ("title", "source_pages", "uses_images_from_pages",
                    "key_points", "exam_tips", "common_mistakes"):
            if key not in t:
                raise PlanValidationError(f"topics[{i}] missing key: {key}")
        pages = _require_list_of_ints(t["source_pages"], f"topics[{i}].source_pages")
        for p in pages:
            if p < 1 or p > max_page:
                raise PlanValidationError(
                    f"topics[{i}].source_pages contains out-of-range page {p} (max {max_page})"
                )
        _require_list_of_ints(t["uses_images_from_pages"], f"topics[{i}].uses_images_from_pages")
        for list_key in ("key_points", "exam_tips", "common_mistakes"):
            items = _require_list(t[list_key], f"topics[{i}].{list_key}")
            for item in items:
                if not isinstance(item, str):
                    raise PlanValidationError(f"topics[{i}].{list_key} items must be strings")

        # search_keywords: optional — default to [] if LLM omits it
        search_kw = t.get("search_keywords")
        if search_kw is None:
            t["search_keywords"] = []
        else:
            _require_list(search_kw, f"topics[{i}].search_keywords")
            for kw in search_kw:
                if not isinstance(kw, str):
                    raise PlanValidationError(f"topics[{i}].search_keywords items must be strings")

    exam_summary = _require(plan, "exam_summary")
    if not isinstance(exam_summary, dict):
        raise PlanValidationError("exam_summary must be a dict")
    for key in ("must_know", "common_pitfalls"):
        if key not in exam_summary:
            raise PlanValidationError(f"exam_summary missing key: {key}")
        _require_list(exam_summary[key], f"exam_summary.{key}")

    quick_review = _require_list(_require(plan, "quick_review"), "quick_review")
    for item in quick_review:
        if not isinstance(item, str):
            raise PlanValidationError("quick_review items must be strings")


def _build_pages_block(pages: list[dict]) -> str:
    parts: list[str] = []
    for p in pages:
        parts.append(f"[PAGE {p['page_number']}]\n{p['text']}")
    return "\n\n".join(parts)


def _build_image_manifest_block(manifest: dict[int, list[str]]) -> str:
    if not manifest:
        return "(本课件未提取到任何嵌入图片)"
    lines: list[str] = []
    for page, files in sorted(manifest.items()):
        lines.append(f"- 第 {page} 页有 {len(files)} 张图片")
    return "\n".join(lines)


def generate_plan(
    pages: list[dict],
    image_manifest: dict[int, list[str]],
    max_retries: int = 5,
    api_key: str | None = None,
) -> dict:
    """Pass-1 call: build a validated report plan via DeepSeek JSON mode with retries.

    Returns a validated plan dict on success. On total failure, raises
    PlanValidationError (caller should fall back).
    """
    client = get_openai_client(api_key=api_key)
    max_page = max((p["page_number"] for p in pages), default=0)

    pages_block = _build_pages_block(pages)
    manifest_block = _build_image_manifest_block(image_manifest)
    base_prompt = REPORT_PLAN_PROMPT.format(
        pages_block=pages_block,
        image_manifest_block=manifest_block,
    )

    current_prompt = base_prompt
    last_error = None
    last_response = None

    for attempt in range(max_retries):
        content = ""
        try:
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": current_prompt}],
                response_format={"type": "json_object"},
                temperature=0.2,
            )
            content = response.choices[0].message.content or ""
            plan = json.loads(content)
            validate_plan(plan, max_page=max_page)
            logger.info("Pass-1 plan generated on attempt %d", attempt + 1)
            return plan
        except (json.JSONDecodeError, PlanValidationError) as e:
            last_error = str(e)
            last_response = content
            logger.warning("Pass-1 attempt %d failed: %s", attempt + 1, last_error)
            current_prompt = build_retry_prompt(base_prompt, last_response, last_error)
            continue

    raise PlanValidationError(
        f"Pass-1 failed after {max_retries} attempts. Last error: {last_error}"
    )


FALLBACK_CHAPTER_SIZE = 4


def build_fallback_plan(pages: list[dict]) -> dict:
    """Build a minimal valid plan by chunking every 4 pages.

    Used when Pass-1 fails all retries. Produces a degraded but complete plan
    that downstream can consume identically.
    """
    topics: list[dict] = []
    for i in range(0, len(pages), FALLBACK_CHAPTER_SIZE):
        chunk = pages[i : i + FALLBACK_CHAPTER_SIZE]
        source_pages = [p["page_number"] for p in chunk]
        start = source_pages[0]
        end = source_pages[-1]
        topics.append({
            "title": f"章节 (第 {start}-{end} 页)" if start != end else f"章节 (第 {start} 页)",
            "source_pages": source_pages,
            "uses_images_from_pages": [],
            "key_points": ["(此主题由机械分块生成, 无语义摘要)"],
            "exam_tips": ["(无可用考点提示, 请直接阅读原课件)"],
            "common_mistakes": ["(无可用易错点提示)"],
            "search_keywords": [],
        })

    return {
        "overview": "本课件生成计划时 LLM 失败, 已退化为按页分块模式. 建议重新上传或检查 API 连通性.",
        "tldr": [
            "LLM 计划生成失败, 下列章节为机械分块",
            "每章节对应固定页数 (默认 4 页)",
            "仍会对每段调用 LLM 生成展开讲解",
            "考点与易错点提示不可用",
            "建议重新上传以获得完整报告",
        ],
        "topics": topics,
        "exam_summary": {
            "must_know": ["(无可用汇总, 请参考各章节原文)"],
            "common_pitfalls": ["(无可用易错点汇总)"],
        },
        "quick_review": ["阅读各章节原文", "重新上传以重试完整流水线"],
    }
