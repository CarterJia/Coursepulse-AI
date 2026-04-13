from __future__ import annotations


def generate_embedding(text: str) -> list[float]:
    """Placeholder embedding generator.

    In production this calls OpenAI text-embedding-3-small.
    For now returns a zero vector of the correct dimension.
    """
    return [0.0] * 1536
