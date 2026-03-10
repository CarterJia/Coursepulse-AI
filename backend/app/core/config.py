from pydantic import BaseModel


class Settings(BaseModel):
    app_name: str = "CoursePulse API"


settings = Settings()
