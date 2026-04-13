from fastapi import APIRouter, UploadFile
from starlette.responses import JSONResponse

from app.schemas.document import DocumentUploadResponse
from app.services.ingestion import create_document_record, create_ingestion_job
from app.services.storage import save_upload

router = APIRouter()


@router.post("/documents/upload", response_model=DocumentUploadResponse, status_code=202)
async def upload_document(file: UploadFile) -> JSONResponse:
    content = await file.read()
    file_path = save_upload(content, file.filename or "unknown", sub_dir="slides")
    document_id = create_document_record(file.filename or "unknown", file_path, file.content_type or "application/octet-stream")
    job_id = create_ingestion_job(document_id)
    return JSONResponse(
        status_code=202,
        content={"document_id": document_id, "job_id": job_id, "status": "queued"},
    )
