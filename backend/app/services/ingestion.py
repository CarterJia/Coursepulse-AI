import uuid

from app.tasks.jobs import create_job


def create_document_record(filename: str, file_path: str, mime_type: str) -> str:
    return str(uuid.uuid4())


def create_ingestion_job(document_id: str) -> str:
    return create_job("ingestion")
