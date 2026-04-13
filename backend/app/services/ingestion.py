from __future__ import annotations

import uuid

import sqlalchemy as sa
from sqlalchemy.orm import Session

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


def run_ingestion_pipeline(db: Session, document_id: uuid.UUID, job_id: uuid.UUID) -> None:
    job = db.get(Job, job_id)
    job.status = "running"
    db.commit()

    try:
        doc = db.get(Document, document_id)

        # 1. Parse PDF pages
        pages = extract_pages(doc.file_path)
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
        for chunk in chunk_records:
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

        # 4. Generate chapter reports
        for i in range(0, len(pages), CHAPTER_SIZE):
            chapter_pages = pages[i : i + CHAPTER_SIZE]
            start_page = chapter_pages[0]["page_number"]
            end_page = chapter_pages[-1]["page_number"]
            title = f"Chapter: Pages {start_page}-{end_page}"
            context = "\n\n".join(p["text"] for p in chapter_pages)
            body = generate_chapter_report(title, context)
            db.add(Report(
                id=uuid.uuid4(), document_id=document_id, title=title, body=body
            ))
        db.commit()

        # 5. Extract glossary
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

    except Exception as e:
        db.rollback()
        job = db.get(Job, job_id)
        job.status = "failed"
        job.error_message = str(e)[:500]
        db.commit()
