from unittest.mock import MagicMock, patch
import numpy as np

from app.services.embedding import generate_embedding, EMBEDDING_DIM


@patch("app.services.embedding._get_model")
def test_generate_embedding_returns_correct_dim(mock_get_model):
    mock_model = MagicMock()
    mock_model.encode.return_value = np.random.randn(EMBEDDING_DIM).astype(np.float32)
    mock_get_model.return_value = mock_model

    result = generate_embedding("test text")

    assert len(result) == EMBEDDING_DIM
    mock_model.encode.assert_called_once_with("test text", normalize_embeddings=True)
