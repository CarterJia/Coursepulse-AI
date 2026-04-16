import os

from pydantic import BaseModel


class Settings(BaseModel):
    app_name: str = "CoursePulse API"
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://coursepulse:coursepulse@db:5432/coursepulse",
    )
    file_storage_root: str = os.getenv("FILE_STORAGE_ROOT", "/app/storage")
    deepseek_api_key: str = os.getenv("DEEPSEEK_API_KEY", "")
    upload_quota_per_ip: int = int(os.getenv("UPLOAD_QUOTA_PER_IP", "3"))
    sample_document_id: str = os.getenv("SAMPLE_DOCUMENT_ID", "")


settings = Settings()
