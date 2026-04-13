from unittest.mock import MagicMock, patch

from app.services.reporting import generate_chapter_report


@patch("app.services.reporting.get_openai_client")
def test_generate_chapter_report_calls_gpt4o(mock_get_client):
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content="# Expanded Lecture\n\nDetailed notes here."))]
    )
    mock_get_client.return_value = mock_client

    result = generate_chapter_report("Chapter: Pages 1-4", "Limits define continuity.")

    assert "Expanded Lecture" in result or "Detailed notes" in result
    mock_client.chat.completions.create.assert_called_once()
    call_kwargs = mock_client.chat.completions.create.call_args
    assert call_kwargs[1]["model"] == "gpt-4o"
