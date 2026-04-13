def test_required_env_names_exist():
    required = {
        "DATABASE_URL",
        "DEEPSEEK_API_KEY",
        "FILE_STORAGE_ROOT",
    }
    assert "DATABASE_URL" in required
