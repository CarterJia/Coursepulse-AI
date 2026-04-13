from __future__ import annotations

import uuid
from typing import Any

# In-memory job store for MVP; replaced by DB queries when Postgres is wired.
_job_store: dict[str, dict[str, Any]] = {}


def create_job(job_type: str) -> str:
    job_id = str(uuid.uuid4())
    _job_store[job_id] = {
        "job_id": job_id,
        "job_type": job_type,
        "status": "queued",
        "error_message": None,
    }
    return job_id


def get_job(job_id: str) -> dict[str, Any] | None:
    return _job_store.get(job_id)


def update_job_status(job_id: str, status: str, error_message: str | None = None) -> None:
    if job_id in _job_store:
        _job_store[job_id]["status"] = status
        if error_message is not None:
            _job_store[job_id]["error_message"] = error_message
