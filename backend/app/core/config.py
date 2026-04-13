import os

from pydantic import BaseModel


class Settings(BaseModel):
    app_name: str = "CoursePulse API"
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://coursepulse:coursepulse@db:5432/coursepulse",
    )
    file_storage_root: str = os.getenv("FILE_STORAGE_ROOT", "/app/storage")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")


settings = Settings()
