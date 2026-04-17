from __future__ import annotations

import json
import logging

from app.core.config import settings
from app.services.openai_client import get_openai_client
from app.services.prompts import GLOSSARY_EXTRACT_PROMPT

logger = logging.getLogger(__name__)


def extract_glossary(text: str, api_key: str | None = None) -> list[dict[str, str]]:
    client = get_openai_client(api_key=api_key)
    prompt = GLOSSARY_EXTRACT_PROMPT.format(text=text)
    try:
        response = client.chat.completions.create(
            model=settings.llm_model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.2,
        )
        raw = response.choices[0].message.content.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1].rsplit("```", 1)[0]
        data = json.loads(raw)
    except Exception:
        logger.exception("Glossary extraction failed; returning empty list")
        return []

    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("entries", "glossary", "terms", "items"):
            if isinstance(data.get(key), list):
                return data[key]
    return []
