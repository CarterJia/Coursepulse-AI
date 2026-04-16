from pydantic import BaseModel


class AssignmentUploadResponse(BaseModel):
    assignment_id: str
    job_id: str
    status: str
