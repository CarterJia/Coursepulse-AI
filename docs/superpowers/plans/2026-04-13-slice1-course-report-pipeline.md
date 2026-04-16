# Slice 1: Course Report Pipeline — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Wire the existing skeleton into a fully functional pipeline: upload a PDF → parse → chunk → embed (OpenAI) → generate teaching report (GPT-4o) → extract glossary → display in frontend.

**Architecture:** Replace all placeholder services with real Postgres writes, OpenAI API calls, and pgvector retrieval. Use FastAPI BackgroundTasks for the heavy ingestion pipeline. Frontend fetches real data from the API.

**Tech Stack:** FastAPI, SQLAlchemy, Alembic, OpenAI Python SDK (`openai`), pgvector, PyMuPDF, Next.js, shadcn/ui

---

### File Map

**Backend — modified:**
- `backend/requirements.txt` — add `openai` dependency
- `backend/app/core/config.py` — already has `openai_api_key`
- `backend/app/db/session.py` — already functional, no changes needed
- `backend/app/tasks/jobs.py` — rewrite from in-memory dict to real DB operations
- `backend/app/services/ingestion.py` — rewrite to real DB writes + BackgroundTask orchestration
- `backend/app/services/embedding.py` — rewrite to call OpenAI API
- `backend/app/services/retrieval.py` — rewrite to pgvector cosine similarity
- `backend/app/services/reporting.py` — rewrite to call GPT-4o with structured output
- `backend/app/api/routes/documents.py` — add DB session injection, add GET endpoints
- `backend/app/api/routes/reports.py` — rewrite to query DB
- `backend/app/api/routes/jobs.py` — rewrite to query DB
- `backend/app/schemas/document.py` — add list/detail response schemas
- `backend/app/schemas/report.py` — add report list schema
- `backend/app/main.py` — register new routers, add CORS middleware

**Backend — new:**
- `backend/app/services/openai_client.py` — shared OpenAI client singleton
- `backend/app/services/prompts.py` — centralized prompt templates
- `backend/app/services/glossary.py` — term extraction + explanation
- `backend/app/api/routes/glossary.py` — GET /api/documents/{id}/glossary
- `backend/app/schemas/glossary.py` — glossary response schema
- `backend/tests/test_openai_client.py` — client initialization test
- `backend/tests/test_prompts.py` — prompt template tests
- `backend/tests/test_glossary.py` — glossary extraction test

**Frontend — modified:**
- `frontend/package.json` — add shadcn/ui dependencies
- `frontend/app/page.tsx` — rewrite with shadcn/ui, add document list
- `frontend/app/documents/[id]/page.tsx` — rewrite to fetch real data
- `frontend/components/upload-form.tsx` — rewrite with shadcn/ui Card + Dropzone
- `frontend/components/report-viewer.tsx` — rewrite with Accordion for chapters
- `frontend/components/glossary-panel.tsx` — rewrite with Sheet component
- `frontend/components/job-status.tsx` — rewrite with Progress + Toast
- `frontend/lib/api.ts` — add new endpoint helpers

**Frontend — new:**
- `frontend/components/ui/` — shadcn/ui component files (installed via CLI)
- `frontend/components/document-list.tsx` — list of processed documents
- `frontend/lib/utils.ts` — cn() utility for shadcn/ui
- `frontend/app/globals.css` — update for shadcn/ui CSS variables

---

### Task 1: Add OpenAI SDK and Shared Client

**Files:**
- Modify: `backend/requirements.txt`
- Create: `backend/app/services/openai_client.py`
- Create: `backend/tests/test_openai_client.py`

- [ ] **Step 1: Write the failing test**

Create `backend/tests/test_openai_client.py`:

```python
from app.services.openai_client import get_openai_client


def test_get_openai_client_returns_client(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")
    client = get_openai_client()
    assert client is not None
    assert client.api_key == "sk-test-key"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_openai_client.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'app.services.openai_client'`

- [ ] **Step 3: Write minimal implementation**

Add `openai>=1.40.0` to `backend/requirements.txt` (append after the last line).

Run: `cd /path/to/worktree && source .venv/bin/activate && pip install openai`

Create `backend/app/services/openai_client.py`:

```python
from __future__ import annotations

import os

from openai import OpenAI

_client: OpenAI | None = None


def get_openai_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=os.getenv("OPENAI_API_KEY", ""))
    return _client
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/test_openai_client.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/requirements.txt backend/app/services/openai_client.py backend/tests/test_openai_client.py
git commit -m "feat: add OpenAI client singleton"
```

---

### Task 2: Add Centralized Prompt Templates

**Files:**
- Create: `backend/app/services/prompts.py`
- Create: `backend/tests/test_prompts.py`

- [ ] **Step 1: Write the failing test**

Create `backend/tests/test_prompts.py`:

```python
from app.services.prompts import CHAPTER_REPORT_PROMPT, GLOSSARY_EXTRACT_PROMPT


def test_chapter_report_prompt_has_placeholders():
    assert "{context}" in CHAPTER_REPORT_PROMPT
    assert "{chapter_title}" in CHAPTER_REPORT_PROMPT


def test_glossary_extract_prompt_has_placeholders():
    assert "{text}" in GLOSSARY_EXTRACT_PROMPT
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_prompts.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'app.services.prompts'`

- [ ] **Step 3: Write minimal implementation**

Create `backend/app/services/prompts.py`:

```python
CHAPTER_REPORT_PROMPT = """\
You are an expert teaching assistant. Given the following raw slide content \
from a course chapter titled "{chapter_title}", produce a clear, logically \
structured lecture note that:

1. Expands abbreviated bullet points into full explanations
2. Fills in implicit logical steps between concepts
3. Adds intuitive examples where helpful
4. Preserves all formulas and technical terms exactly

## Slide Content

{context}

## Instructions

Write the expanded lecture note in Markdown. Use ## for section headings. \
Be thorough but concise — aim for 2-3x the length of the original content. \
Write in the same language as the slide content.

Respond with ONLY the lecture note content, no preamble."""

GLOSSARY_EXTRACT_PROMPT = """\
You are a teaching assistant. From the following course material, extract \
all technical terms and jargon that a student might not know.

## Course Material

{text}

## Instructions

For each term, provide:
- term: the exact term as it appears
- definition: a clear 1-2 sentence definition
- analogy: a simple real-world analogy (optional, omit if not helpful)

Respond as a JSON array:
[{{"term": "...", "definition": "...", "analogy": "..."}}]

Only include genuinely technical terms, not common words. Respond with ONLY \
the JSON array, no preamble."""
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/test_prompts.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/prompts.py backend/tests/test_prompts.py
git commit -m "feat: add centralized prompt templates"
```

---

### Task 3: Rewrite Job Service to Use Postgres

**Files:**
- Modify: `backend/app/tasks/jobs.py`
- Modify: `backend/app/api/routes/jobs.py`
- Modify: `backend/tests/test_jobs_api.py`

- [ ] **Step 1: Write the failing test**

Replace `backend/tests/test_jobs_api.py` with:

```python
from unittest.mock import MagicMock
from uuid import uuid4

from fastapi.testclient import TestClient

from app.db.session import get_db
from app.main import app
from app.models.job import Job


def _mock_db_with_job():
    job_id = uuid4()
    mock_job = MagicMock(spec=Job)
    mock_job.id = job_id
    mock_job.job_type = "ingestion"
    mock_job.status = "queued"
    mock_job.error_message = None

    db = MagicMock()
    db.get.return_value = mock_job
    return db, job_id


def test_job_status_returns_queued():
    db, job_id = _mock_db_with_job()
    app.dependency_overrides[get_db] = lambda: db
    client = TestClient(app)
    response = client.get(f"/api/jobs/{job_id}")
    assert response.status_code == 200
    assert response.json()["status"] == "queued"
    app.dependency_overrides.clear()


def test_job_status_returns_404_for_unknown():
    db = MagicMock()
    db.get.return_value = None
    app.dependency_overrides[get_db] = lambda: db
    client = TestClient(app)
    response = client.get(f"/api/jobs/{uuid4()}")
    assert response.status_code == 404
    app.dependency_overrides.clear()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_jobs_api.py -v`
Expected: FAIL because the route still uses in-memory `get_job()`, not DB session.

- [ ] **Step 3: Write minimal implementation**

Rewrite `backend/app/tasks/jobs.py`:

```python
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
```

Rewrite `backend/app/api/routes/jobs.py`:

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.job import JobStatusResponse
from app.tasks.jobs import get_job

router = APIRouter()


@router.get("/jobs/{job_id}", response_model=JobStatusResponse)
def job_status(job_id: str, db: Session = Depends(get_db)) -> JobStatusResponse:
    job = get_job(db, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobStatusResponse(
        job_id=str(job.id),
        job_type=job.job_type,
        status=job.status,
        error_message=job.error_message,
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/test_jobs_api.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/tasks/jobs.py backend/app/api/routes/jobs.py backend/tests/test_jobs_api.py
git commit -m "feat: rewrite job service to use Postgres"
```

---

### Task 4: Rewrite Document Upload with DB Writes and BackgroundTask

**Files:**
- Modify: `backend/app/services/ingestion.py`
- Modify: `backend/app/api/routes/documents.py`
- Modify: `backend/app/schemas/document.py`
- Modify: `backend/tests/test_document_upload.py`
- Modify: `backend/app/main.py` — add CORS middleware

- [ ] **Step 1: Write the failing test**

Replace `backend/tests/test_document_upload.py` with:

```python
from unittest.mock import MagicMock, patch
from uuid import uuid4

from fastapi.testclient import TestClient

from app.db.session import get_db
from app.main import app
from app.models.course import Course
from app.models.document import Document
from app.models.job import Job


def _mock_db():
    db = MagicMock()
    course = MagicMock(spec=Course)
    course.id = uuid4()
    db.query.return_value.filter.return_value.first.return_value = course
    return db


def test_document_upload_creates_record_and_job(tmp_path, monkeypatch):
    monkeypatch.setenv("FILE_STORAGE_ROOT", str(tmp_path))
    db = _mock_db()
    app.dependency_overrides[get_db] = lambda: db
    client = TestClient(app)
    response = client.post(
        "/api/documents/upload",
        files={"file": ("week1.pdf", b"%PDF-1.4 fake", "application/pdf")},
    )
    assert response.status_code == 202
    body = response.json()
    assert "document_id" in body
    assert "job_id" in body
    assert body["status"] == "queued"
    # Verify db.add was called (Document + Job)
    assert db.add.call_count >= 2
    app.dependency_overrides.clear()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_document_upload.py -v`
Expected: FAIL because the current route doesn't use DB session.

- [ ] **Step 3: Write minimal implementation**

Rewrite `backend/app/services/ingestion.py`:

```python
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
```

Rewrite `backend/app/api/routes/documents.py`:

```python
from fastapi import APIRouter, BackgroundTasks, Depends, UploadFile
from sqlalchemy.orm import Session
from starlette.responses import JSONResponse

from app.db.session import get_db
from app.schemas.document import DocumentDetailResponse, DocumentListResponse, DocumentUploadResponse
from app.services.ingestion import (
    create_document_record,
    create_ingestion_job,
    get_or_create_default_course,
    run_ingestion_pipeline,
)
from app.services.storage import save_upload

router = APIRouter()


@router.post("/documents/upload", response_model=DocumentUploadResponse, status_code=202)
async def upload_document(
    file: UploadFile,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> JSONResponse:
    content = await file.read()
    file_path = save_upload(content, file.filename or "unknown", sub_dir="slides")
    course = get_or_create_default_course(db)
    doc = create_document_record(
        db, file.filename or "unknown", file_path, file.content_type or "application/octet-stream", course.id
    )
    job = create_ingestion_job(db)
    background_tasks.add_task(run_ingestion_pipeline, db, doc.id, job.id)
    return JSONResponse(
        status_code=202,
        content={"document_id": str(doc.id), "job_id": str(job.id), "status": "queued"},
    )


@router.get("/documents", response_model=list[DocumentListResponse])
def list_documents(db: Session = Depends(get_db)):
    from app.models.document import Document
    docs = db.query(Document).order_by(Document.created_at.desc()).all()
    return [
        DocumentListResponse(
            id=str(d.id), filename=d.filename, mime_type=d.mime_type, created_at=d.created_at.isoformat()
        )
        for d in docs
    ]


@router.get("/documents/{document_id}", response_model=DocumentDetailResponse)
def get_document(document_id: str, db: Session = Depends(get_db)):
    import uuid
    from fastapi import HTTPException
    from app.models.document import Document
    from app.models.report import Report
    doc = db.get(Document, uuid.UUID(document_id))
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    reports = db.query(Report).filter(Report.document_id == doc.id).order_by(Report.created_at).all()
    return DocumentDetailResponse(
        id=str(doc.id),
        filename=doc.filename,
        mime_type=doc.mime_type,
        created_at=doc.created_at.isoformat(),
        reports=[{"id": str(r.id), "title": r.title, "body": r.body} for r in reports],
    )
```

Update `backend/app/schemas/document.py`:

```python
from pydantic import BaseModel


class DocumentUploadResponse(BaseModel):
    document_id: str
    job_id: str
    status: str


class DocumentListResponse(BaseModel):
    id: str
    filename: str
    mime_type: str
    created_at: str


class ReportSummary(BaseModel):
    id: str
    title: str
    body: str


class DocumentDetailResponse(BaseModel):
    id: str
    filename: str
    mime_type: str
    created_at: str
    reports: list[ReportSummary]
```

Add CORS middleware to `backend/app/main.py`:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.assignments import router as assignments_router
from app.api.routes.documents import router as documents_router
from app.api.routes.health import router as health_router
from app.api.routes.jobs import router as jobs_router
from app.api.routes.reports import router as reports_router

app = FastAPI(title="CoursePulse API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix="/api")
app.include_router(documents_router, prefix="/api")
app.include_router(reports_router, prefix="/api")
app.include_router(jobs_router, prefix="/api")
app.include_router(assignments_router, prefix="/api")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/test_document_upload.py -v`
Expected: PASS

Also run all tests: `cd backend && python -m pytest -v`
Expected: Some old tests may need updating (test_health, test_env_smoke should still pass; test_models should still pass; other tests may need mock DB overrides). Fix any failures.

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/ingestion.py backend/app/api/routes/documents.py backend/app/schemas/document.py backend/app/main.py backend/tests/test_document_upload.py
git commit -m "feat: wire document upload to Postgres with BackgroundTask pipeline"
```

---

### Task 5: Connect Embedding Service to OpenAI API

**Files:**
- Modify: `backend/app/services/embedding.py`
- Modify: `backend/tests/test_chunking.py` (add embedding test)

- [ ] **Step 1: Write the failing test**

Create `backend/tests/test_embedding.py`:

```python
from unittest.mock import MagicMock, patch

from app.services.embedding import generate_embedding


@patch("app.services.embedding.get_openai_client")
def test_generate_embedding_calls_openai(mock_get_client):
    mock_client = MagicMock()
    mock_client.embeddings.create.return_value = MagicMock(
        data=[MagicMock(embedding=[0.1] * 1536)]
    )
    mock_get_client.return_value = mock_client

    result = generate_embedding("test text")

    assert len(result) == 1536
    assert result[0] == 0.1
    mock_client.embeddings.create.assert_called_once_with(
        model="text-embedding-3-small",
        input="test text",
    )
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_embedding.py -v`
Expected: FAIL because current `generate_embedding` returns zeros without calling OpenAI.

- [ ] **Step 3: Write minimal implementation**

Rewrite `backend/app/services/embedding.py`:

```python
from __future__ import annotations

from app.services.openai_client import get_openai_client


def generate_embedding(text: str) -> list[float]:
    client = get_openai_client()
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text,
    )
    return response.data[0].embedding
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/test_embedding.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/embedding.py backend/tests/test_embedding.py
git commit -m "feat: connect embedding service to OpenAI API"
```

---

### Task 6: Implement pgvector Cosine Similarity Retrieval

**Files:**
- Modify: `backend/app/services/retrieval.py`
- Create: `backend/tests/test_retrieval.py`

- [ ] **Step 1: Write the failing test**

Create `backend/tests/test_retrieval.py`:

```python
from unittest.mock import MagicMock, patch
from uuid import uuid4

from app.services.retrieval import retrieve_top_chunks


@patch("app.services.retrieval.generate_embedding")
def test_retrieve_top_chunks_queries_pgvector(mock_embed):
    mock_embed.return_value = [0.1] * 1536

    mock_row = MagicMock()
    mock_row.id = uuid4()
    mock_row.text = "Limits define continuity"
    mock_row.page_number = 1
    mock_row.chunk_index = 0
    mock_row.document_id = uuid4()

    db = MagicMock()
    db.execute.return_value.fetchall.return_value = [mock_row]

    results = retrieve_top_chunks(db, "what are limits", document_id=str(mock_row.document_id), top_k=3)

    assert len(results) == 1
    assert results[0]["text"] == "Limits define continuity"
    mock_embed.assert_called_once_with("what are limits")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_retrieval.py -v`
Expected: FAIL because current `retrieve_top_chunks` has a different signature and no DB.

- [ ] **Step 3: Write minimal implementation**

Rewrite `backend/app/services/retrieval.py`:

```python
from __future__ import annotations

from typing import Any

import sqlalchemy as sa
from sqlalchemy.orm import Session

from app.services.embedding import generate_embedding


def retrieve_top_chunks(
    db: Session, query: str, document_id: str, top_k: int = 5
) -> list[dict[str, Any]]:
    query_vector = generate_embedding(query)

    sql = sa.text("""
        SELECT kc.id, kc.text, kc.page_number, kc.chunk_index, kc.document_id
        FROM knowledge_chunks kc
        JOIN embeddings e ON e.chunk_id = kc.id
        WHERE kc.document_id = :doc_id
        ORDER BY e.vector <=> :query_vec
        LIMIT :top_k
    """)

    rows = db.execute(sql, {
        "doc_id": document_id,
        "query_vec": str(query_vector),
        "top_k": top_k,
    }).fetchall()

    return [
        {
            "id": str(row.id),
            "text": row.text,
            "page_number": row.page_number,
            "chunk_index": row.chunk_index,
            "document_id": str(row.document_id),
        }
        for row in rows
    ]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/test_retrieval.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/retrieval.py backend/tests/test_retrieval.py
git commit -m "feat: implement pgvector cosine similarity retrieval"
```

---

### Task 7: Implement GPT-4o Report Generation

**Files:**
- Modify: `backend/app/services/reporting.py`
- Modify: `backend/tests/test_report_generation.py`

- [ ] **Step 1: Write the failing test**

Replace `backend/tests/test_report_generation.py`:

```python
from unittest.mock import MagicMock, patch

from app.services.reporting import generate_chapter_report


@patch("app.services.reporting.get_openai_client")
def test_generate_chapter_report_calls_gpt4o(mock_get_client):
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content="# Expanded Lecture\n\nDetailed notes here."))]
    )
    mock_get_client.return_value = mock_client

    result = generate_chapter_report("Chapter: Pages 1-4", "Limits define continuity.")

    assert "Expanded Lecture" in result or "Detailed notes" in result
    mock_client.chat.completions.create.assert_called_once()
    call_kwargs = mock_client.chat.completions.create.call_args
    assert call_kwargs[1]["model"] == "gpt-4o"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_report_generation.py -v`
Expected: FAIL because current `reporting.py` has no `generate_chapter_report` function.

- [ ] **Step 3: Write minimal implementation**

Rewrite `backend/app/services/reporting.py`:

```python
from __future__ import annotations

from typing import Any

from app.services.openai_client import get_openai_client
from app.services.prompts import CHAPTER_REPORT_PROMPT


def build_report_prompt(query: str, chunks: list[dict[str, Any]]) -> str:
    context_parts: list[str] = []
    for chunk in chunks:
        page = chunk.get("page_number", "?")
        text = chunk.get("text", "")
        context_parts.append(f"[Page {page}] {text}")
    context_block = "\n\n".join(context_parts)
    return (
        f"You are a teaching assistant. Using the following course material as context, "
        f"produce a clear, logically structured explanation.\n\n"
        f"## Context\n\n{context_block}\n\n"
        f"## Task\n\n{query}"
    )


def generate_chapter_report(chapter_title: str, context: str) -> str:
    client = get_openai_client()
    prompt = CHAPTER_REPORT_PROMPT.format(chapter_title=chapter_title, context=context)
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )
    return response.choices[0].message.content
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/test_report_generation.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/reporting.py backend/tests/test_report_generation.py
git commit -m "feat: implement GPT-4o chapter report generation"
```

---

### Task 8: Add Glossary Extraction Service and Route

**Files:**
- Create: `backend/app/services/glossary.py`
- Create: `backend/app/schemas/glossary.py`
- Create: `backend/app/api/routes/glossary.py`
- Create: `backend/tests/test_glossary.py`
- Modify: `backend/app/main.py`

- [ ] **Step 1: Write the failing test**

Create `backend/tests/test_glossary.py`:

```python
import json
from unittest.mock import MagicMock, patch

from app.services.glossary import extract_glossary


@patch("app.services.glossary.get_openai_client")
def test_extract_glossary_returns_structured_terms(mock_get_client):
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content=json.dumps([
            {"term": "Derivative", "definition": "Rate of change of a function.", "analogy": "Speed of a car."},
            {"term": "Integral", "definition": "Area under a curve."},
        ])))]
    )
    mock_get_client.return_value = mock_client

    result = extract_glossary("Derivatives measure change. Integrals compute area.")

    assert len(result) == 2
    assert result[0]["term"] == "Derivative"
    assert result[1]["term"] == "Integral"
    assert result[0]["analogy"] == "Speed of a car."
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_glossary.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'app.services.glossary'`

- [ ] **Step 3: Write minimal implementation**

Create `backend/app/services/glossary.py`:

```python
from __future__ import annotations

import json

from app.services.openai_client import get_openai_client
from app.services.prompts import GLOSSARY_EXTRACT_PROMPT


def extract_glossary(text: str) -> list[dict[str, str]]:
    client = get_openai_client()
    prompt = GLOSSARY_EXTRACT_PROMPT.format(text=text)
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
    )
    raw = response.choices[0].message.content.strip()
    # Strip markdown code fences if present
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1].rsplit("```", 1)[0]
    return json.loads(raw)
```

Create `backend/app/schemas/glossary.py`:

```python
from pydantic import BaseModel


class GlossaryEntryResponse(BaseModel):
    id: str
    term: str
    definition: str
    analogy: str | None = None
```

Create `backend/app/api/routes/glossary.py`:

```python
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
```

Add glossary router to `backend/app/main.py` (add import and `app.include_router`):

```python
from app.api.routes.glossary import router as glossary_router
# ... after existing includes:
app.include_router(glossary_router, prefix="/api")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/test_glossary.py -v`
Expected: PASS

Run all tests: `cd backend && python -m pytest -v`
Expected: All pass (fix any broken old tests as needed).

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/glossary.py backend/app/schemas/glossary.py backend/app/api/routes/glossary.py backend/app/main.py backend/tests/test_glossary.py
git commit -m "feat: add glossary extraction service and API route"
```

---

### Task 9: Rewrite Reports Route to Query DB

**Files:**
- Modify: `backend/app/api/routes/reports.py`
- Modify: `backend/app/schemas/report.py`

- [ ] **Step 1: Write the failing test**

Create `backend/tests/test_reports_api.py`:

```python
from unittest.mock import MagicMock
from uuid import uuid4

from fastapi.testclient import TestClient

from app.db.session import get_db
from app.main import app
from app.models.report import Report


def test_section_report_endpoint_calls_gpt4o():
    db = MagicMock()
    # Mock retrieve and generate
    app.dependency_overrides[get_db] = lambda: db
    client = TestClient(app)
    response = client.post(
        "/api/reports/section",
        json={"query": "Explain limits", "document_id": str(uuid4())},
    )
    # Should still return 200 with generated content
    assert response.status_code == 200
    data = response.json()
    assert "title" in data
    assert "body" in data
    app.dependency_overrides.clear()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_reports_api.py -v`
Expected: FAIL because the route still uses in-memory chunk store.

- [ ] **Step 3: Write minimal implementation**

Rewrite `backend/app/api/routes/reports.py`:

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.report import SectionReportRequest, SectionReportResponse
from app.services.reporting import build_report_prompt, generate_chapter_report
from app.services.retrieval import retrieve_top_chunks

router = APIRouter()


@router.post("/reports/section", response_model=SectionReportResponse)
def create_section_report(
    req: SectionReportRequest,
    db: Session = Depends(get_db),
) -> SectionReportResponse:
    chunks = retrieve_top_chunks(db, req.query, req.document_id)
    context = "\n\n".join(c["text"] for c in chunks)
    body = generate_chapter_report(req.query, context)
    return SectionReportResponse(title=req.query, body=body)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/test_reports_api.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/api/routes/reports.py backend/tests/test_reports_api.py
git commit -m "feat: rewrite reports route to use DB retrieval and GPT-4o"
```

---

### Task 10: Set Up shadcn/ui in Frontend

**Files:**
- Modify: `frontend/package.json`
- Create: `frontend/components/ui/*` (via shadcn CLI)
- Create: `frontend/lib/utils.ts`
- Modify: `frontend/app/globals.css`
- Modify: `frontend/tsconfig.json`

- [ ] **Step 1: Install shadcn/ui**

Run these commands from the `frontend/` directory:

```bash
npm install class-variance-authority clsx tailwind-merge lucide-react next-themes
npx shadcn@latest init --defaults
```

When the CLI asks questions, accept defaults (New York style, zinc color).

This will:
- Create `components/ui/` directory
- Create `lib/utils.ts` with the `cn()` helper
- Update `globals.css` with CSS variables
- Update `tailwind.config.ts`

- [ ] **Step 2: Add required shadcn/ui components**

```bash
npx shadcn@latest add card button accordion badge sheet progress toast skeleton separator dropdown-menu
```

- [ ] **Step 3: Verify the build**

Run: `cd frontend && npx next build`
Expected: Build succeeds with no errors.

- [ ] **Step 4: Commit**

```bash
git add frontend/
git commit -m "feat: set up shadcn/ui component library"
```

---

### Task 11: Rebuild Frontend Upload Page

**Files:**
- Modify: `frontend/app/page.tsx`
- Modify: `frontend/components/upload-form.tsx`
- Create: `frontend/components/document-list.tsx`
- Modify: `frontend/lib/api.ts`
- Modify: `frontend/components/job-status.tsx`

- [ ] **Step 1: Write the failing test**

Update `frontend/tests/upload-form.test.tsx`:

```tsx
import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom";

import { UploadForm } from "../components/upload-form";

test("renders upload dropzone with button", () => {
  render(<UploadForm />);
  expect(screen.getByText(/drop your pdf here/i)).toBeInTheDocument();
  expect(screen.getByRole("button", { name: /upload/i })).toBeInTheDocument();
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && npx jest tests/upload-form.test.tsx --no-cache`
Expected: FAIL because current component doesn't have "drop your pdf here" text.

- [ ] **Step 3: Write minimal implementation**

Add to `frontend/lib/api.ts`:

```ts
const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export async function uploadDocument(file: File) {
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch(`${API_BASE}/api/documents/upload`, {
    method: "POST",
    body: formData,
  });
  return res.json();
}

export async function getJobStatus(jobId: string) {
  const res = await fetch(`${API_BASE}/api/jobs/${jobId}`);
  return res.json();
}

export async function listDocuments() {
  const res = await fetch(`${API_BASE}/api/documents`);
  return res.json();
}

export async function getDocument(id: string) {
  const res = await fetch(`${API_BASE}/api/documents/${id}`);
  return res.json();
}

export async function getGlossary(documentId: string) {
  const res = await fetch(`${API_BASE}/api/documents/${documentId}/glossary`);
  return res.json();
}

export async function uploadAssignment(file: File) {
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch(`${API_BASE}/api/assignments/upload`, {
    method: "POST",
    body: formData,
  });
  return res.json();
}
```

Rewrite `frontend/components/upload-form.tsx`:

```tsx
"use client";

import { useRef, useState, useCallback } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { uploadDocument } from "@/lib/api";

interface UploadFormProps {
  onUploaded?: (data: { document_id: string; job_id: string }) => void;
}

export function UploadForm({ onUploaded }: UploadFormProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [uploading, setUploading] = useState(false);
  const [dragOver, setDragOver] = useState(false);

  const handleFile = useCallback(async (file: File) => {
    setUploading(true);
    try {
      const data = await uploadDocument(file);
      onUploaded?.(data);
    } finally {
      setUploading(false);
    }
  }, [onUploaded]);

  return (
    <Card
      className={`border-2 border-dashed transition-colors ${dragOver ? "border-primary bg-muted" : "border-muted-foreground/25"}`}
      onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
      onDragLeave={() => setDragOver(false)}
      onDrop={(e) => {
        e.preventDefault();
        setDragOver(false);
        const file = e.dataTransfer.files[0];
        if (file) handleFile(file);
      }}
    >
      <CardContent className="flex flex-col items-center justify-center py-10 gap-4">
        <p className="text-muted-foreground text-sm">Drop your PDF here, or click to browse</p>
        <input
          ref={inputRef}
          type="file"
          accept=".pdf"
          className="hidden"
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) handleFile(file);
          }}
        />
        <Button
          variant="outline"
          disabled={uploading}
          onClick={() => inputRef.current?.click()}
        >
          {uploading ? "Uploading..." : "Upload"}
        </Button>
      </CardContent>
    </Card>
  );
}
```

Create `frontend/components/document-list.tsx`:

```tsx
"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { listDocuments } from "@/lib/api";

interface Doc {
  id: string;
  filename: string;
  mime_type: string;
  created_at: string;
}

export function DocumentList() {
  const [docs, setDocs] = useState<Doc[]>([]);

  useEffect(() => {
    listDocuments().then(setDocs).catch(() => {});
  }, []);

  if (docs.length === 0) return null;

  return (
    <div className="space-y-3">
      <h2 className="text-lg font-semibold">Your Documents</h2>
      {docs.map((doc) => (
        <Link key={doc.id} href={`/documents/${doc.id}`}>
          <Card className="hover:bg-muted/50 transition-colors cursor-pointer">
            <CardContent className="flex items-center justify-between py-3">
              <span className="font-medium">{doc.filename}</span>
              <Badge variant="secondary">{doc.mime_type.split("/")[1]?.toUpperCase()}</Badge>
            </CardContent>
          </Card>
        </Link>
      ))}
    </div>
  );
}
```

Rewrite `frontend/app/page.tsx`:

```tsx
"use client";

import { useState } from "react";
import { UploadForm } from "@/components/upload-form";
import { JobStatus } from "@/components/job-status";
import { DocumentList } from "@/components/document-list";

export default function HomePage() {
  const [jobId, setJobId] = useState<string | null>(null);
  const [docId, setDocId] = useState<string | null>(null);

  return (
    <main className="max-w-2xl mx-auto py-12 px-4 space-y-8">
      <div>
        <h1 className="text-3xl font-bold mb-2">CoursePulse AI</h1>
        <p className="text-muted-foreground">Upload your course slides to generate a structured teaching report.</p>
      </div>

      <UploadForm
        onUploaded={(data) => {
          setDocId(data.document_id);
          setJobId(data.job_id);
        }}
      />

      {jobId && (
        <JobStatus jobId={jobId} onComplete={() => {
          if (docId) window.location.href = `/documents/${docId}`;
        }} />
      )}

      <DocumentList />
    </main>
  );
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd frontend && npx jest tests/upload-form.test.tsx --no-cache`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/app/page.tsx frontend/components/upload-form.tsx frontend/components/document-list.tsx frontend/components/job-status.tsx frontend/lib/api.ts frontend/tests/upload-form.test.tsx
git commit -m "feat: rebuild upload page with shadcn/ui and document list"
```

---

### Task 12: Rebuild Report Viewer and Glossary Panel

**Files:**
- Modify: `frontend/app/documents/[id]/page.tsx`
- Modify: `frontend/components/report-viewer.tsx`
- Modify: `frontend/components/glossary-panel.tsx`
- Modify: `frontend/tests/report-viewer.test.tsx`

- [ ] **Step 1: Write the failing test**

Update `frontend/tests/report-viewer.test.tsx`:

```tsx
import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom";

import { ReportViewer } from "../components/report-viewer";

test("renders chapter titles in accordion", () => {
  const reports = [
    { id: "1", title: "Chapter: Pages 1-4", body: "Expanded lecture content." },
  ];
  render(<ReportViewer reports={reports} />);
  expect(screen.getByText("Chapter: Pages 1-4")).toBeInTheDocument();
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && npx jest tests/report-viewer.test.tsx --no-cache`
Expected: FAIL because current `ReportViewer` has `title`/`body` props, not `reports` array.

- [ ] **Step 3: Write minimal implementation**

Rewrite `frontend/components/report-viewer.tsx`:

```tsx
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";

interface Report {
  id: string;
  title: string;
  body: string;
}

interface ReportViewerProps {
  reports: Report[];
}

export function ReportViewer({ reports }: ReportViewerProps) {
  if (reports.length === 0) {
    return <p className="text-muted-foreground">No reports generated yet.</p>;
  }

  return (
    <Accordion type="multiple" defaultValue={[reports[0]?.id]} className="space-y-2">
      {reports.map((report) => (
        <AccordionItem key={report.id} value={report.id}>
          <AccordionTrigger className="text-lg font-semibold">
            {report.title}
          </AccordionTrigger>
          <AccordionContent>
            <div className="prose dark:prose-invert max-w-none whitespace-pre-wrap">
              {report.body}
            </div>
          </AccordionContent>
        </AccordionItem>
      ))}
    </Accordion>
  );
}
```

Rewrite `frontend/components/glossary-panel.tsx`:

```tsx
"use client";

import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";

interface GlossaryEntry {
  id: string;
  term: string;
  definition: string;
  analogy?: string | null;
}

interface GlossaryPanelProps {
  entries: GlossaryEntry[];
}

export function GlossaryPanel({ entries }: GlossaryPanelProps) {
  if (entries.length === 0) return null;

  return (
    <Sheet>
      <SheetTrigger asChild>
        <Button variant="outline" size="sm">
          Glossary ({entries.length})
        </Button>
      </SheetTrigger>
      <SheetContent className="overflow-y-auto">
        <SheetHeader>
          <SheetTitle>Glossary</SheetTitle>
        </SheetHeader>
        <div className="mt-4 space-y-4">
          {entries.map((entry) => (
            <div key={entry.id}>
              <Badge variant="secondary" className="mb-1">{entry.term}</Badge>
              <p className="text-sm text-muted-foreground">{entry.definition}</p>
              {entry.analogy && (
                <p className="text-sm italic text-muted-foreground/70 mt-1">{entry.analogy}</p>
              )}
              <Separator className="mt-3" />
            </div>
          ))}
        </div>
      </SheetContent>
    </Sheet>
  );
}
```

Rewrite `frontend/app/documents/[id]/page.tsx`:

```tsx
"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { ReportViewer } from "@/components/report-viewer";
import { GlossaryPanel } from "@/components/glossary-panel";
import { Skeleton } from "@/components/ui/skeleton";
import { getDocument, getGlossary } from "@/lib/api";

export default function DocumentDetailPage() {
  const params = useParams();
  const id = params.id as string;
  const [doc, setDoc] = useState<any>(null);
  const [glossary, setGlossary] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([getDocument(id), getGlossary(id)])
      .then(([d, g]) => { setDoc(d); setGlossary(g); })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) {
    return (
      <main className="max-w-4xl mx-auto py-12 px-4 space-y-4">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-4 w-3/4" />
      </main>
    );
  }

  if (!doc) {
    return <main className="max-w-4xl mx-auto py-12 px-4"><p>Document not found.</p></main>;
  }

  return (
    <main className="max-w-4xl mx-auto py-12 px-4">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold">{doc.filename}</h1>
          <p className="text-sm text-muted-foreground">Uploaded {new Date(doc.created_at).toLocaleDateString()}</p>
        </div>
        <GlossaryPanel entries={glossary} />
      </div>
      <ReportViewer reports={doc.reports ?? []} />
    </main>
  );
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd frontend && npx jest --no-cache`
Expected: All frontend tests pass.

- [ ] **Step 5: Commit**

```bash
git add frontend/app/documents/[id]/page.tsx frontend/components/report-viewer.tsx frontend/components/glossary-panel.tsx frontend/tests/report-viewer.test.tsx
git commit -m "feat: rebuild report viewer with Accordion and glossary Sheet"
```

---

### Task 13: Update Docker Compose and Run Full Integration

**Files:**
- Modify: `docker-compose.yml` — add health check for db
- Modify: `backend/Dockerfile` — ensure alembic runs on startup
- Modify: `.env.example` — update docs

- [ ] **Step 1: Update backend Dockerfile to run migrations**

Rewrite `backend/Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY backend/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY backend /app/backend

WORKDIR /app/backend

CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"]
```

- [ ] **Step 2: Add db health check to docker-compose.yml**

Update the `db` service in `docker-compose.yml` to add a health check, and the `backend` to wait for it:

```yaml
services:
  db:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_DB: ${POSTGRES_DB:-coursepulse}
      POSTGRES_USER: ${POSTGRES_USER:-coursepulse}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-coursepulse}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U coursepulse"]
      interval: 5s
      timeout: 5s
      retries: 5

  backend:
    build:
      context: .
      dockerfile: backend/Dockerfile
    environment:
      DATABASE_URL: ${DATABASE_URL:-postgresql+psycopg://coursepulse:coursepulse@db:5432/coursepulse}
      FILE_STORAGE_ROOT: ${FILE_STORAGE_ROOT:-/app/storage}
      OPENAI_API_KEY: ${OPENAI_API_KEY:-replace-me}
    volumes:
      - ./backend:/app/backend
      - ./storage:/app/storage
    ports:
      - "8000:8000"
    depends_on:
      db:
        condition: service_healthy

  frontend:
    build:
      context: .
      dockerfile: frontend/Dockerfile
    environment:
      NEXT_PUBLIC_API_BASE_URL: ${NEXT_PUBLIC_API_BASE_URL:-http://localhost:8000}
    volumes:
      - ./frontend:/app/frontend
    ports:
      - "3000:3000"
    depends_on:
      - backend

volumes:
  postgres_data:
```

- [ ] **Step 3: Update .env.example**

```
DATABASE_URL=postgresql+psycopg://coursepulse:coursepulse@db:5432/coursepulse
POSTGRES_DB=coursepulse
POSTGRES_USER=coursepulse
POSTGRES_PASSWORD=coursepulse
OPENAI_API_KEY=sk-your-key-here
FILE_STORAGE_ROOT=/app/storage
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
# Optional: YouTube Data API v3 key for video recommendations
# YOUTUBE_API_KEY=
```

- [ ] **Step 4: Test the full stack**

```bash
cp .env.example .env
# Edit .env to add a real OPENAI_API_KEY
docker compose up --build
```

Verify:
- http://localhost:3000 loads the upload page
- http://localhost:8000/api/health returns `{"status": "ok"}`
- http://localhost:8000/docs shows the API docs
- Upload a PDF and wait for the report to generate

- [ ] **Step 5: Commit**

```bash
git add docker-compose.yml backend/Dockerfile .env.example
git commit -m "feat: update Docker Compose for full Slice 1 integration"
```

---

### Task 14: Fix Remaining Tests and Run Full Suite

**Files:**
- Modify: various test files as needed
- Modify: `backend/tests/test_ingestion_to_report_flow.py`

- [ ] **Step 1: Run all backend tests**

Run: `cd backend && python -m pytest -v`

Fix any failures. Common issues:
- `test_ingestion_to_report_flow.py` needs mock DB overrides
- `test_health.py` should still pass (no DB needed)
- `test_models.py` should still pass (no DB needed)

- [ ] **Step 2: Update integration test with mocks**

Rewrite `backend/tests/test_ingestion_to_report_flow.py`:

```python
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.db.session import get_db
from app.main import app
from app.services.chunking import build_chunks

FIXTURES = Path(__file__).parent / "fixtures"


def test_chunking_to_retrieval_integration():
    pages = json.loads((FIXTURES / "sample_course_page.json").read_text())
    chunks = build_chunks(pages)
    assert len(chunks) == 3
    assert all("text" in c for c in chunks)


@patch("app.api.routes.documents.run_ingestion_pipeline")
def test_upload_and_job_tracking_integration(mock_pipeline, tmp_path, monkeypatch):
    monkeypatch.setenv("FILE_STORAGE_ROOT", str(tmp_path))
    db = MagicMock()

    # Mock course lookup
    mock_course = MagicMock()
    mock_course.id = __import__("uuid").uuid4()
    db.query.return_value.filter.return_value.first.return_value = mock_course

    app.dependency_overrides[get_db] = lambda: db
    client = TestClient(app)

    upload_res = client.post(
        "/api/documents/upload",
        files={"file": ("test.pdf", b"%PDF-1.4 fake", "application/pdf")},
    )
    assert upload_res.status_code == 202
    body = upload_res.json()
    assert "document_id" in body
    assert "job_id" in body
    app.dependency_overrides.clear()
```

- [ ] **Step 3: Run all tests**

Run: `cd backend && python -m pytest -v`
Expected: ALL PASS

Run: `cd frontend && npx jest --no-cache`
Expected: ALL PASS

- [ ] **Step 4: Commit**

```bash
git add backend/tests/ frontend/tests/
git commit -m "test: update all tests for Slice 1 DB integration"
```
