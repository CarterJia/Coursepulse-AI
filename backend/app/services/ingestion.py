from __future__ import annotations

import logging
import os
import uuid

import sqlalchemy as sa
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import SessionLocal
from app.models.course import Course
from app.models.document import Document, DocumentPage
from app.models.job import Job
from app.models.knowledge_chunk import Embedding, KnowledgeChunk
from app.models.report import GlossaryEntry
from app.services.chunking import build_chunks
from app.services.embedding import generate_embedding
from app.services.glossary import extract_glossary
from app.services.image_extraction import extract_images
from app.services.parser import extract_pages
from app.services.reporting import run_report_pipeline

logger = logging.getLogger(__name__)


def get_or_create_default_course(db: Session) -> Course:
    course = db.query(Course).filter(Course.name == "Default Course").first()
    if not course:
        course = Course(id=uuid.uuid4(), name="Default Course")
        db.add(course)
        db.commit()
        db.refresh(course)
    return course


def create_document_record(
    db: Session, filename: str, file_path: str, mime_type: str, course_id: uuid.UUID
) -> Document:
    doc = Document(
        id=uuid.uuid4(),
        course_id=course_id,
        filename=filename,
        file_path=file_path,
        mime_type=mime_type,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


def create_ingestion_job(db: Session) -> Job:
    job = Job(id=uuid.uuid4(), job_type="ingestion", status="queued")
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def _derived_dir(document_id: uuid.UUID) -> str:
    root = settings.file_storage_root
    return os.path.join(root, "derived", str(document_id))


def run_ingestion_pipeline(document_id: uuid.UUID, job_id: uuid.UUID) -> None:
    """Full pipeline, owns its own DB session (runs as BackgroundTask)."""
    db = SessionLocal()
    try:
        job = db.get(Job, job_id)
        job.status = "running"
        db.commit()

        doc = db.get(Document, document_id)
        logger.info("Starting ingestion for document %s (%s)", document_id, doc.filename)

        # 1. Parse PDF pages
        pages = extract_pages(doc.file_path)
        logger.info("Parsed %d pages", len(pages))
        for p in pages:
            db.add(DocumentPage(
                id=uuid.uuid4(),
                document_id=document_id,
                page_number=p["page_number"],
                text_content=p["text"],
            ))
        db.commit()

        # 2. Extract embedded images
        image_manifest = extract_images(doc.file_path, _derived_dir(document_id))
        logger.info("Extracted images from %d page(s)", len(image_manifest))

        # 3. Chunk pages
        raw_chunks = build_chunks(pages)
        chunk_records: list[KnowledgeChunk] = []
        for c in raw_chunks:
            chunk = KnowledgeChunk(
                id=uuid.uuid4(),
                document_id=document_id,
                page_number=c["page_number"],
                text=c["text"],
                chunk_index=c["chunk_index"],
            )
            db.add(chunk)
            chunk_records.append(chunk)
        db.commit()
        logger.info("Built %d chunks", len(chunk_records))

        # 4. Embed chunks
        for chunk in chunk_records:
            vector = generate_embedding(chunk.text)
            db.execute(
                sa.text(
                    "INSERT INTO embeddings (id, chunk_id, vector, created_at) "
                    "VALUES (:id, :chunk_id, :vector, NOW())"
                ),
                {"id": str(uuid.uuid4()), "chunk_id": str(chunk.id), "vector": str(vector)},
            )
        db.commit()
        logger.info("Embedded %d chunks", len(chunk_records))

        # 5. Two-pass report pipeline (writes all section-typed rows)
        run_report_pipeline(db, document_id, pages, image_manifest)
        db.commit()
        logger.info("Report pipeline complete for document %s", document_id)

        # 6. Glossary extraction
        all_text = "\n\n".join(p["text"] for p in pages)
        for item in extract_glossary(all_text):
            db.add(GlossaryEntry(
                id=uuid.uuid4(),
                document_id=document_id,
                term=item["term"],
                definition=item["definition"],
                analogy=item.get("analogy"),
            ))
        db.commit()

        job.status = "succeeded"
        db.commit()
        logger.info("Ingestion completed successfully for document %s", document_id)

    except Exception as e:
        logger.exception("Ingestion failed for document %s: %s", document_id, e)
        db.rollback()
        job = db.get(Job, job_id)
        if job:
            job.status = "failed"
            job.error_message = str(e)[:500]
            db.commit()
    finally:
        db.close()
