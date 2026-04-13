import json
from unittest.mock import MagicMock, patch

from app.services.glossary import extract_glossary


@patch("app.services.glossary.get_openai_client")
def test_extract_glossary_returns_structured_terms(mock_get_client):
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content=json.dumps([
            {"term": "Derivative", "definition": "Rate of change of a function.", "analogy": "Speed of a car."},
            {"term": "Integral", "definition": "Area under a curve."},
        ])))]
    )
    mock_get_client.return_value = mock_client

    result = extract_glossary("Derivatives measure change. Integrals compute area.")

    assert len(result) == 2
    assert result[0]["term"] == "Derivative"
    assert result[1]["term"] == "Integral"
    assert result[0]["analogy"] == "Speed of a car."
