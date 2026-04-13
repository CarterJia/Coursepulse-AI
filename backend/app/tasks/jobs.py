from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.models.job import Job


def create_job(db: Session, job_type: str) -> Job:
    job = Job(id=uuid.uuid4(), job_type=job_type, status="queued")
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def get_job(db: Session, job_id: str) -> Job | None:
    return db.get(Job, uuid.UUID(job_id) if isinstance(job_id, str) else job_id)


def update_job_status(db: Session, job_id: str, status: str, error_message: str | None = None) -> None:
    job = get_job(db, job_id)
    if job:
        job.status = status
        if error_message is not None:
            job.error_message = error_message
        db.commit()
