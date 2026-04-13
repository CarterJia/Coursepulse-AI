from __future__ import annotations

import json

from app.services.openai_client import get_openai_client
from app.services.prompts import GLOSSARY_EXTRACT_PROMPT


def extract_glossary(text: str) -> list[dict[str, str]]:
    client = get_openai_client()
    prompt = GLOSSARY_EXTRACT_PROMPT.format(text=text)
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
    )
    raw = response.choices[0].message.content.strip()
    # Strip markdown code fences if present
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1].rsplit("```", 1)[0]
    return json.loads(raw)
