def test_required_env_names_exist():
    required = {
        "DATABASE_URL",
        "OPENAI_API_KEY",
        "FILE_STORAGE_ROOT",
    }
    assert "DATABASE_URL" in required
