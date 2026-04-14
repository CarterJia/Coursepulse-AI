import mimetypes
import os
import re
import uuid

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.core.config import settings

router = APIRouter()

SAFE_FILENAME = re.compile(r"^[A-Za-z0-9_\-.]+$")


@router.get("/files/{document_id}/{filename}")
def serve_file(document_id: str, filename: str):
    try:
        doc_uuid = uuid.UUID(document_id)
    except (ValueError, AttributeError):
        raise HTTPException(status_code=400, detail="Invalid document id")

    if not SAFE_FILENAME.match(filename) or ".." in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")

    base = os.path.realpath(os.path.join(settings.file_storage_root, "derived", str(doc_uuid)))
    target = os.path.realpath(os.path.join(base, filename))

    if not target.startswith(base + os.sep) and target != base:
        raise HTTPException(status_code=400, detail="Path traversal rejected")

    if not os.path.isfile(target):
        raise HTTPException(status_code=404, detail="File not found")

    mime, _ = mimetypes.guess_type(target)
    return FileResponse(target, media_type=mime or "application/octet-stream")
