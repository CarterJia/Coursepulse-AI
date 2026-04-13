from fastapi import APIRouter, HTTPException

from app.schemas.job import JobStatusResponse
from app.tasks.jobs import get_job

router = APIRouter()


@router.get("/jobs/{job_id}", response_model=JobStatusResponse)
def job_status(job_id: str) -> JobStatusResponse:
    job = get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobStatusResponse(**job)
