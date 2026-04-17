import os

from pydantic import BaseModel


class Settings(BaseModel):
    app_name: str = "CoursePulse API"
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://coursepulse:coursepulse@db:5432/coursepulse",
    )
    file_storage_root: str = os.getenv("FILE_STORAGE_ROOT", "/app/storage")
    llm_api_key: str = os.getenv("LLM_API_KEY", os.getenv("DEEPSEEK_API_KEY", ""))
    llm_base_url: str = os.getenv("LLM_BASE_URL", "https://api.deepseek.com")
    llm_model: str = os.getenv("LLM_MODEL", "deepseek-chat")
    sample_document_id: str = os.getenv("SAMPLE_DOCUMENT_ID", "")


settings = Settings()
