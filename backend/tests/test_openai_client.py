from app.services.openai_client import get_openai_client, reset_openai_client, DEEPSEEK_BASE_URL


def test_get_openai_client_returns_deepseek_client(monkeypatch):
    reset_openai_client()
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-test-key")
    client = get_openai_client()
    assert client is not None
    assert client.api_key == "sk-test-key"
    assert str(client.base_url).rstrip("/") == DEEPSEEK_BASE_URL
    reset_openai_client()


def test_get_openai_client_uses_override_key(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "env-key")
    reset_openai_client()
    client = get_openai_client(api_key="user-key")
    assert client.api_key == "user-key"


def test_get_openai_client_override_does_not_cache(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "env-key")
    reset_openai_client()
    _ = get_openai_client(api_key="user-key")
    default_client = get_openai_client()
    assert default_client.api_key == "env-key"
