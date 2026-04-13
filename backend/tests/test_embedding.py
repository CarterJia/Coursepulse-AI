from unittest.mock import MagicMock, patch

from app.services.embedding import generate_embedding


@patch("app.services.embedding.get_openai_client")
def test_generate_embedding_calls_openai(mock_get_client):
    mock_client = MagicMock()
    mock_client.embeddings.create.return_value = MagicMock(
        data=[MagicMock(embedding=[0.1] * 1536)]
    )
    mock_get_client.return_value = mock_client

    result = generate_embedding("test text")

    assert len(result) == 1536
    assert result[0] == 0.1
    mock_client.embeddings.create.assert_called_once_with(
        model="text-embedding-3-small",
        input="test text",
    )
