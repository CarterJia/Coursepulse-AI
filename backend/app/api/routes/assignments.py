from fastapi import APIRouter, UploadFile
from starlette.responses import JSONResponse

from app.schemas.diagnosis import AssignmentUploadResponse
from app.services.diagnosis import create_assignment_record, create_diagnosis_job
from app.services.storage import save_upload

router = APIRouter()


@router.post("/assignments/upload", response_model=AssignmentUploadResponse, status_code=202)
async def upload_assignment(file: UploadFile) -> JSONResponse:
    content = await file.read()
    file_path = save_upload(content, file.filename or "unknown", sub_dir="assignments")
    assignment_id = create_assignment_record(
        file.filename or "unknown", file_path, file.content_type or "application/octet-stream"
    )
    job_id = create_diagnosis_job(assignment_id)
    return JSONResponse(
        status_code=202,
        content={"assignment_id": assignment_id, "job_id": job_id, "status": "queued"},
    )
