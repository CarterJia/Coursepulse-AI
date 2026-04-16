from __future__ import annotations

import os

from openai import OpenAI

_client: OpenAI | None = None

DEEPSEEK_BASE_URL = "https://api.deepseek.com"


def get_openai_client(api_key: str | None = None) -> OpenAI:
    """Return an OpenAI-compatible client pointed at DeepSeek.

    When ``api_key`` is provided, a one-shot client is returned without touching
    the module-level cache — this is the BYOK path. When omitted, the cached
    client (created from ``DEEPSEEK_API_KEY``) is used.
    """
    if api_key:
        return OpenAI(api_key=api_key, base_url=DEEPSEEK_BASE_URL)

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
