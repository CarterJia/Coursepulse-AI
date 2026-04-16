from __future__ import annotations

import os

from openai import OpenAI

_client: OpenAI | None = None

DEEPSEEK_BASE_URL = "https://api.deepseek.com"


def get_openai_client(*, api_key: str | None = None) -> OpenAI:
    """Return an OpenAI-compatible client pointed at DeepSeek.

    When ``api_key`` is a non-None string, a one-shot client is returned without
    touching the module-level cache — this is the BYOK path. Empty strings are
    honored as-is (the SDK will surface them as 401s, which is the right signal
    for a malformed BYOK header rather than silently falling back to the owner's
    env key). When ``api_key`` is ``None``, the cached env-driven client is used.
    """
    if api_key is not None:
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
