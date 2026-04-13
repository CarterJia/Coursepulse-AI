from pydantic import BaseModel


class DocumentUploadResponse(BaseModel):
    document_id: str
    job_id: str
    status: str


class DocumentListResponse(BaseModel):
    id: str
    filename: str
    mime_type: str
    created_at: str


class ReportSummary(BaseModel):
    id: str
    title: str
    body: str


class DocumentDetailResponse(BaseModel):
    id: str
    filename: str
    mime_type: str
    created_at: str
    reports: list[ReportSummary]
