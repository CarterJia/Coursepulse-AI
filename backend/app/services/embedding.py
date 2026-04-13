from __future__ import annotations

from sentence_transformers import SentenceTransformer

_model: SentenceTransformer | None = None

MODEL_NAME = "BAAI/bge-small-zh-v1.5"
EMBEDDING_DIM = 512


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)
    return _model


def generate_embedding(text: str) -> list[float]:
    model = _get_model()
    vector = model.encode(text, normalize_embeddings=True)
    return vector.tolist()
