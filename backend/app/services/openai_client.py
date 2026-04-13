from __future__ import annotations

import os

from openai import OpenAI

_client: OpenAI | None = None


def get_openai_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=os.getenv("OPENAI_API_KEY", ""))
    return _client


def reset_openai_client() -> None:
    """Reset the cached client (used in tests)."""
    global _client
    _client = None
