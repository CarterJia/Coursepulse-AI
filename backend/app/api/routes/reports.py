from fastapi import APIRouter

from app.schemas.report import SectionReportRequest, SectionReportResponse
from app.services.reporting import generate_section_report
from app.services.retrieval import retrieve_top_chunks

router = APIRouter()

# In-memory placeholder chunk store; replaced by DB queries in later tasks.
_chunk_store: list[dict] = []


@router.post("/reports/section", response_model=SectionReportResponse)
def create_section_report(req: SectionReportRequest) -> SectionReportResponse:
    chunks = retrieve_top_chunks(req.query, _chunk_store)
    result = generate_section_report(req.query, chunks)
    return SectionReportResponse(**result)
