from __future__ import annotations

from openai import OpenAI

from app.core.config import settings

_client: OpenAI | None = None


def get_openai_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(
            api_key=settings.llm_api_key,
            base_url=settings.llm_base_url,
        )
    return _client


def reset_openai_client() -> None:
    global _client
    _client = None
