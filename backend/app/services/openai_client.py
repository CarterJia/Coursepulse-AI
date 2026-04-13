from __future__ import annotations

import os

from openai import OpenAI

_client: OpenAI | None = None

DEEPSEEK_BASE_URL = "https://api.deepseek.com"


def get_openai_client() -> OpenAI:
    """Return an OpenAI-compatible client pointed at DeepSeek."""
    global _client
    if _client is None:
        _client = OpenAI(
            api_key=os.getenv("DEEPSEEK_API_KEY", ""),
            base_url=DEEPSEEK_BASE_URL,
        )
    return _client


def reset_openai_client() -> None:
    """Reset the cached client (used in tests)."""
    global _client
    _client = None
