from __future__ import annotations

from typing import Any

from app.services.openai_client import get_openai_client
from app.services.prompts import CHAPTER_REPORT_PROMPT


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
