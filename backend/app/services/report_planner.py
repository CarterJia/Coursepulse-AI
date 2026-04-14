"""Pass-1 plan generation: validator, LLM call with retry, fallback.

This file evolves across Task 4 (validator), Task 5 (generate_plan), Task 6 (fallback).
"""

from __future__ import annotations

from typing import Any


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
