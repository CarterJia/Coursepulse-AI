from pydantic import BaseModel


class JobStatusResponse(BaseModel):
    job_id: str
    job_type: str
    status: str
    error_message: str | None = None
