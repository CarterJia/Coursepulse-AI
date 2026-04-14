from fastapi import APIRouter, BackgroundTasks, Depends, UploadFile
from sqlalchemy.orm import Session
from starlette.responses import JSONResponse

from app.db.session import get_db
from app.schemas.document import DocumentDetailResponse, DocumentListResponse, DocumentUploadResponse
from app.services.ingestion import (
    create_document_record,
    create_ingestion_job,
    get_or_create_default_course,
    run_ingestion_pipeline,
)
from app.services.storage import save_upload

router = APIRouter()


@router.post("/documents/upload", response_model=DocumentUploadResponse, status_code=202)
async def upload_document(
    file: UploadFile,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> JSONResponse:
    content = await file.read()
    file_path = save_upload(content, file.filename or "unknown", sub_dir="slides")
    course = get_or_create_default_course(db)
    doc = create_document_record(
        db, file.filename or "unknown", file_path, file.content_type or "application/octet-stream", course.id
    )
    job = create_ingestion_job(db)
    background_tasks.add_task(run_ingestion_pipeline, doc.id, job.id)
    return JSONResponse(
        status_code=202,
        content={"document_id": str(doc.id), "job_id": str(job.id), "status": "queued"},
    )


@router.get("/documents", response_model=list[DocumentListResponse])
def list_documents(db: Session = Depends(get_db)):
    from app.models.document import Document
    docs = db.query(Document).order_by(Document.created_at.desc()).all()
    return [
        DocumentListResponse(
            id=str(d.id), filename=d.filename, mime_type=d.mime_type, created_at=d.created_at.isoformat()
        )
        for d in docs
    ]


@router.get("/documents/{document_id}", response_model=DocumentDetailResponse)
def get_document(document_id: str, db: Session = Depends(get_db)):
    import uuid
    from fastapi import HTTPException
    from app.models.document import Document
    from app.models.report import Report
    doc = db.get(Document, uuid.UUID(document_id))
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    reports = db.query(Report).filter(Report.document_id == doc.id).order_by(Report.created_at).all()
    return DocumentDetailResponse(
        id=str(doc.id),
        filename=doc.filename,
        mime_type=doc.mime_type,
        created_at=doc.created_at.isoformat(),
        reports=[
            {"id": str(r.id), "title": r.title, "body": r.body, "section_type": r.section_type}
            for r in reports
        ],
    )
