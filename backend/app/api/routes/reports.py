from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.report import SectionReportRequest, SectionReportResponse
from app.services.reporting import generate_chapter_report
from app.services.retrieval import retrieve_top_chunks

router = APIRouter()


@router.post("/reports/section", response_model=SectionReportResponse)
def create_section_report(
    req: SectionReportRequest,
    db: Session = Depends(get_db),
) -> SectionReportResponse:
    chunks = retrieve_top_chunks(db, req.query, req.document_id)
    context = "\n\n".join(c["text"] for c in chunks)
    body = generate_chapter_report(req.query, context)
    return SectionReportResponse(title=req.query, body=body)
