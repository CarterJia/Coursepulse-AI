from pydantic import BaseModel


class SectionReportRequest(BaseModel):
    query: str
    document_id: str


class SectionReportResponse(BaseModel):
    title: str
    body: str
