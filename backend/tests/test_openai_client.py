from app.services.openai_client import get_openai_client, reset_openai_client


def test_get_openai_client_returns_client(monkeypatch):
    reset_openai_client()
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")
    client = get_openai_client()
    assert client is not None
    assert client.api_key == "sk-test-key"
    reset_openai_client()
