from __future__ import annotations

import uuid

from app.tasks.jobs import create_job


def create_assignment_record(filename: str, file_path: str, mime_type: str) -> str:
    return str(uuid.uuid4())


def create_diagnosis_job(assignment_id: str) -> str:
    return create_job("diagnosis")
