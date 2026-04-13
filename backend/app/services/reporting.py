from __future__ import annotations

from typing import Any


def build_report_prompt(query: str, chunks: list[dict[str, Any]]) -> str:
    """Build an LLM prompt that includes retrieved context chunks."""
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


def generate_section_report(query: str, chunks: list[dict[str, Any]]) -> dict[str, str]:
    """Generate a section report (placeholder — returns the prompt as body)."""
    prompt = build_report_prompt(query, chunks)
    # In production, this sends the prompt to Claude / GPT and returns the response.
    return {"title": query, "body": prompt}
