from app.services.openai_client import get_openai_client, reset_openai_client, DEEPSEEK_BASE_URL


def test_get_openai_client_returns_deepseek_client(monkeypatch):
    reset_openai_client()
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-test-key")
    client = get_openai_client()
    assert client is not None
    assert client.api_key == "sk-test-key"
    assert str(client.base_url).rstrip("/") == DEEPSEEK_BASE_URL
    reset_openai_client()
