from __future__ import annotations

import logging
import uuid

import sqlalchemy as sa
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.course import Course
from app.models.document import Document, DocumentPage
from app.models.job import Job
from app.models.knowledge_chunk import Embedding, KnowledgeChunk
from app.models.report import GlossaryEntry, Report
from app.services.chunking import build_chunks
from app.services.embedding import generate_embedding
from app.services.glossary import extract_glossary
from app.services.parser import extract_pages
from app.services.reporting import generate_chapter_report

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


CHAPTER_SIZE = 4


def run_ingestion_pipeline(document_id: uuid.UUID, job_id: uuid.UUID) -> None:
    """Run the full ingestion pipeline with its own DB session.

    This function creates its own session because it runs as a BackgroundTask,
    after the request's session has already been closed.
    """
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

        # 2. Chunk pages
        raw_chunks = build_chunks(pages)
        logger.info("Built %d chunks", len(raw_chunks))
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

        # 3. Embed chunks (raw SQL for pgvector column)
        for idx, chunk in enumerate(chunk_records):
            vector = generate_embedding(chunk.text)
            emb_id = uuid.uuid4()
            db.execute(
                sa.text(
                    "INSERT INTO embeddings (id, chunk_id, vector, created_at) "
                    "VALUES (:id, :chunk_id, :vector, NOW())"
                ),
                {"id": str(emb_id), "chunk_id": str(chunk.id), "vector": str(vector)},
            )
        db.commit()
        logger.info("Embedded %d chunks", len(chunk_records))

        # 4. Generate chapter reports
        num_chapters = (len(pages) + CHAPTER_SIZE - 1) // CHAPTER_SIZE
        for i in range(0, len(pages), CHAPTER_SIZE):
            chapter_pages = pages[i : i + CHAPTER_SIZE]
            start_page = chapter_pages[0]["page_number"]
            end_page = chapter_pages[-1]["page_number"]
            title = f"Chapter: Pages {start_page}-{end_page}"
            context = "\n\n".join(p["text"] for p in chapter_pages)
            chapter_num = i // CHAPTER_SIZE + 1
            logger.info("Generating report %d/%d: %s", chapter_num, num_chapters, title)
            body = generate_chapter_report(title, context)
            db.add(Report(
                id=uuid.uuid4(), document_id=document_id, title=title, body=body
            ))
            db.commit()  # commit after each chapter so progress is visible
        logger.info("Generated %d chapter reports", num_chapters)

        # 5. Extract glossary
        all_text = "\n\n".join(p["text"] for p in pages)
        logger.info("Extracting glossary terms...")
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
        job.status = "failed"
        job.error_message = str(e)[:500]
        db.commit()
    finally:
        db.close()
