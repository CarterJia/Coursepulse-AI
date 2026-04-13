import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.document import Document
from app.models.report import GlossaryEntry
from app.schemas.glossary import GlossaryEntryResponse

router = APIRouter()


@router.get("/documents/{document_id}/glossary", response_model=list[GlossaryEntryResponse])
def get_glossary(document_id: str, db: Session = Depends(get_db)):
    doc = db.get(Document, uuid.UUID(document_id))
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    entries = db.query(GlossaryEntry).filter(GlossaryEntry.document_id == doc.id).all()
    return [
        GlossaryEntryResponse(
            id=str(e.id), term=e.term, definition=e.definition, analogy=e.analogy
        )
        for e in entries
    ]
