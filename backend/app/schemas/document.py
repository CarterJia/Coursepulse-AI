from pydantic import BaseModel


class DocumentUploadResponse(BaseModel):
    document_id: str
    job_id: str
    status: str
