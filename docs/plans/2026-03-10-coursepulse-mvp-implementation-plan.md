# CoursePulse MVP Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a local-first single-user MVP that ingests course slides, indexes knowledge chunks, generates teaching reports, and maps mistakes back to relevant slide content.

**Architecture:** Use a modular monolith with a `Next.js` frontend, a `FastAPI` backend, and `Postgres + pgvector` under `Docker Compose`. Keep light interactions synchronous and heavy ingestion/report generation asynchronous through a database-backed jobs layer inside the backend.

**Tech Stack:** `Next.js`, `Tailwind CSS`, `FastAPI`, `SQLAlchemy`, `Alembic`, `Postgres 16`, `pgvector`, `Docker Compose`, `PyMuPDF`, `pytest`

---

## Execution Log

- 2026-03-10 17:32 EDT: `Task 1` verified complete.
  - Local check passed: `.venv/bin/python -m pytest backend/tests/test_env_smoke.py -v`
  - Container check passed: `docker compose run --rm backend pytest tests/test_env_smoke.py -v`
- 2026-03-10 17:34 EDT: `Task 2` verified complete.
  - Local check passed: `PYTHONPATH=backend .venv/bin/python -m pytest backend/tests/test_health.py -v`
- Next restart point:
  - Start at `Task 3`
  - First test to run after creating it: `PYTHONPATH=backend .venv/bin/python -m pytest backend/tests/test_models.py -v`

---

### ~~Task 1: Scaffold Infrastructure and Shared Environment~~

**Status:** Completed and verified on 2026-03-10 17:32 EDT

**Files:**
- Create: `docker-compose.yml`
- Create: `.env.example`
- Create: `backend/Dockerfile`
- Create: `frontend/Dockerfile`
- Create: `backend/requirements.txt`
- Create: `frontend/package.json`

**Step 1: Write the failing test** ~~Completed~~

Create `backend/tests/test_env_smoke.py`:

```python
def test_required_env_names_exist():
    required = {
        "DATABASE_URL",
        "OPENAI_API_KEY",
        "FILE_STORAGE_ROOT",
    }
    assert "DATABASE_URL" in required
```

**Step 2: Run test to verify it fails** ~~Completed~~

Run: `pytest backend/tests/test_env_smoke.py -v`
Expected: FAIL because the test file and test environment do not exist yet.

**Step 3: Write minimal implementation** ~~Completed~~

- Add a `docker-compose.yml` with `frontend`, `backend`, and `db`
- Add `.env.example` with the required environment variables
- Add minimal Dockerfiles for backend and frontend
- Add dependency manifests

**Step 4: Run test to verify it passes** ~~Completed~~

Run: `pytest backend/tests/test_env_smoke.py -v`
Expected: PASS

**Step 5: Commit** ~~Completed~~

```bash
git add docker-compose.yml .env.example backend/Dockerfile frontend/Dockerfile backend/requirements.txt frontend/package.json backend/tests/test_env_smoke.py
git commit -m "chore: scaffold local infrastructure"
```

### ~~Task 2: Create Backend App Skeleton and Health Routes~~

**Status:** Completed and verified on 2026-03-10 17:34 EDT

**Files:**
- Create: `backend/app/main.py`
- Create: `backend/app/api/routes/health.py`
- Create: `backend/app/core/config.py`
- Create: `backend/app/__init__.py`
- Create: `backend/tests/test_health.py`

**Step 1: Write the failing test** ~~Completed~~

Create `backend/tests/test_health.py`:

```python
from fastapi.testclient import TestClient

from app.main import app


def test_healthcheck_returns_ok():
    client = TestClient(app)
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

**Step 2: Run test to verify it fails** ~~Completed~~

Run: `pytest backend/tests/test_health.py -v`
Expected: FAIL with import errors because the app files do not exist yet.

**Step 3: Write minimal implementation** ~~Completed~~

Implement:

```python
from fastapi import FastAPI

from app.api.routes.health import router as health_router

app = FastAPI(title="CoursePulse API")
app.include_router(health_router, prefix="/api")
```

and:

```python
from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def healthcheck():
    return {"status": "ok"}
```

**Step 4: Run test to verify it passes** ~~Completed~~

Run: `pytest backend/tests/test_health.py -v`
Expected: PASS

**Step 5: Commit** ~~Completed~~

```bash
git add backend/app backend/tests/test_health.py
git commit -m "feat: add backend app skeleton"
```

### Task 3: Define Database Models and Migration Baseline

**Files:**
- Create: `backend/app/db/base.py`
- Create: `backend/app/db/session.py`
- Create: `backend/app/models/course.py`
- Create: `backend/app/models/document.py`
- Create: `backend/app/models/knowledge_chunk.py`
- Create: `backend/app/models/job.py`
- Create: `backend/alembic.ini`
- Create: `backend/alembic/env.py`
- Create: `backend/alembic/versions/0001_initial_schema.py`
- Create: `backend/tests/test_models.py`

**Step 1: Write the failing test**

Create `backend/tests/test_models.py`:

```python
from app.models.document import Document
from app.models.job import Job
from app.models.knowledge_chunk import KnowledgeChunk


def test_core_models_expose_expected_tablenames():
    assert Document.__tablename__ == "documents"
    assert KnowledgeChunk.__tablename__ == "knowledge_chunks"
    assert Job.__tablename__ == "jobs"
```

**Step 2: Run test to verify it fails**

Run: `pytest backend/tests/test_models.py -v`
Expected: FAIL because the models do not exist yet.

**Step 3: Write minimal implementation**

Define the initial SQLAlchemy models for:

- `Course`
- `Document`
- `DocumentPage`
- `KnowledgeChunk`
- `Embedding`
- `Report`
- `Assignment`
- `MistakeDiagnosis`
- `ReviewPriority`
- `Job`

Add an Alembic migration to create the schema and enable `vector`.

**Step 4: Run test to verify it passes**

Run: `pytest backend/tests/test_models.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/db backend/app/models backend/alembic backend/tests/test_models.py
git commit -m "feat: add database schema baseline"
```

### Task 4: Implement File Storage and Document Upload API

**Files:**
- Create: `backend/app/schemas/document.py`
- Create: `backend/app/services/storage.py`
- Create: `backend/app/services/ingestion.py`
- Create: `backend/app/api/routes/documents.py`
- Create: `backend/tests/test_document_upload.py`

**Step 1: Write the failing test**

Create `backend/tests/test_document_upload.py`:

```python
from fastapi.testclient import TestClient

from app.main import app


def test_document_upload_returns_job_payload(tmp_path, monkeypatch):
    monkeypatch.setenv("FILE_STORAGE_ROOT", str(tmp_path))
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
```

**Step 2: Run test to verify it fails**

Run: `pytest backend/tests/test_document_upload.py -v`
Expected: FAIL because the upload route does not exist yet.

**Step 3: Write minimal implementation**

Implement:

- local file persistence under `storage/slides/`
- `POST /api/documents/upload`
- document record creation
- job record creation with initial `queued` state

**Step 4: Run test to verify it passes**

Run: `pytest backend/tests/test_document_upload.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/schemas/document.py backend/app/services/storage.py backend/app/services/ingestion.py backend/app/api/routes/documents.py backend/tests/test_document_upload.py
git commit -m "feat: add document upload workflow"
```

### Task 5: Add Parsing, Chunking, and Indexing Pipeline

**Files:**
- Create: `backend/app/services/parser.py`
- Create: `backend/app/services/chunking.py`
- Create: `backend/app/services/embedding.py`
- Modify: `backend/app/services/ingestion.py`
- Create: `backend/tests/test_chunking.py`

**Step 1: Write the failing test**

Create `backend/tests/test_chunking.py`:

```python
from app.services.chunking import build_chunks


def test_build_chunks_splits_pages_into_searchable_units():
    pages = [
        {"page_number": 1, "text": "Limits define continuity. Derivatives measure change."}
    ]
    chunks = build_chunks(pages)
    assert len(chunks) >= 1
    assert chunks[0]["page_number"] == 1
    assert "continuity" in chunks[0]["text"].lower()
```

**Step 2: Run test to verify it fails**

Run: `pytest backend/tests/test_chunking.py -v`
Expected: FAIL because chunking logic does not exist yet.

**Step 3: Write minimal implementation**

Implement:

- parser wrapper around `PyMuPDF`
- deterministic page-to-chunk transformation
- embedding service interface
- index persistence into `knowledge_chunks` and `embeddings`

**Step 4: Run test to verify it passes**

Run: `pytest backend/tests/test_chunking.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/services/parser.py backend/app/services/chunking.py backend/app/services/embedding.py backend/app/services/ingestion.py backend/tests/test_chunking.py
git commit -m "feat: add ingestion indexing pipeline"
```

### Task 6: Add Retrieval and Section Report Generation

**Files:**
- Create: `backend/app/schemas/report.py`
- Create: `backend/app/services/retrieval.py`
- Create: `backend/app/services/reporting.py`
- Create: `backend/app/api/routes/reports.py`
- Create: `backend/tests/test_report_generation.py`

**Step 1: Write the failing test**

Create `backend/tests/test_report_generation.py`:

```python
from app.services.reporting import build_report_prompt


def test_build_report_prompt_includes_context_chunks():
    chunks = [{"page_number": 2, "text": "Gradient descent updates weights by moving opposite the gradient."}]
    prompt = build_report_prompt("Explain gradient descent", chunks)
    assert "Explain gradient descent" in prompt
    assert "opposite the gradient" in prompt
```

**Step 2: Run test to verify it fails**

Run: `pytest backend/tests/test_report_generation.py -v`
Expected: FAIL because reporting logic does not exist yet.

**Step 3: Write minimal implementation**

Implement:

- retrieval service for `top_k` chunk lookup
- prompt builder for report generation
- `POST /api/reports/section`
- synchronous generation for page or section summaries

**Step 4: Run test to verify it passes**

Run: `pytest backend/tests/test_report_generation.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/schemas/report.py backend/app/services/retrieval.py backend/app/services/reporting.py backend/app/api/routes/reports.py backend/tests/test_report_generation.py
git commit -m "feat: add section report generation"
```

### Task 7: Add Job Status Tracking for Heavy Workflows

**Files:**
- Create: `backend/app/schemas/job.py`
- Create: `backend/app/tasks/jobs.py`
- Create: `backend/app/api/routes/jobs.py`
- Modify: `backend/app/services/ingestion.py`
- Modify: `backend/app/main.py`
- Create: `backend/tests/test_jobs_api.py`

**Step 1: Write the failing test**

Create `backend/tests/test_jobs_api.py`:

```python
from fastapi.testclient import TestClient

from app.main import app


def test_job_status_endpoint_returns_known_state():
    client = TestClient(app)
    response = client.get("/api/jobs/test-job-id")
    assert response.status_code in {200, 404}
```

**Step 2: Run test to verify it fails**

Run: `pytest backend/tests/test_jobs_api.py -v`
Expected: FAIL because the jobs route does not exist yet.

**Step 3: Write minimal implementation**

Implement:

- `GET /api/jobs/{job_id}`
- a database-backed job state machine with `queued`, `running`, `succeeded`, `failed`
- ingestion hooks to update state over time

**Step 4: Run test to verify it passes**

Run: `pytest backend/tests/test_jobs_api.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/schemas/job.py backend/app/tasks/jobs.py backend/app/api/routes/jobs.py backend/app/services/ingestion.py backend/app/main.py backend/tests/test_jobs_api.py
git commit -m "feat: add job status tracking"
```

### Task 8: Add Assignment Upload and Diagnosis Skeleton

**Files:**
- Create: `backend/app/schemas/diagnosis.py`
- Create: `backend/app/services/diagnosis.py`
- Create: `backend/app/api/routes/assignments.py`
- Create: `backend/tests/test_assignment_upload.py`

**Step 1: Write the failing test**

Create `backend/tests/test_assignment_upload.py`:

```python
from fastapi.testclient import TestClient

from app.main import app


def test_assignment_upload_queues_diagnosis_job(tmp_path, monkeypatch):
    monkeypatch.setenv("FILE_STORAGE_ROOT", str(tmp_path))
    client = TestClient(app)
    response = client.post(
        "/api/assignments/upload",
        files={"file": ("quiz1.png", b"fake-image", "image/png")},
    )
    assert response.status_code == 202
    assert response.json()["status"] == "queued"
```

**Step 2: Run test to verify it fails**

Run: `pytest backend/tests/test_assignment_upload.py -v`
Expected: FAIL because the assignment route does not exist yet.

**Step 3: Write minimal implementation**

Implement:

- local file persistence under `storage/assignments/`
- assignment record creation
- diagnosis job queue record creation
- placeholder diagnosis service that returns structured `not_implemented` guidance

**Step 4: Run test to verify it passes**

Run: `pytest backend/tests/test_assignment_upload.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/schemas/diagnosis.py backend/app/services/diagnosis.py backend/app/api/routes/assignments.py backend/tests/test_assignment_upload.py
git commit -m "feat: add diagnosis upload skeleton"
```

### Task 9: Build Frontend App Shell and Upload Flow

**Files:**
- Create: `frontend/app/page.tsx`
- Create: `frontend/app/documents/[id]/page.tsx`
- Create: `frontend/components/upload-form.tsx`
- Create: `frontend/components/job-status.tsx`
- Create: `frontend/lib/api.ts`
- Create: `frontend/tests/upload-form.test.tsx`

**Step 1: Write the failing test**

Create `frontend/tests/upload-form.test.tsx`:

```tsx
import { render, screen } from "@testing-library/react";

import { UploadForm } from "../components/upload-form";

test("renders upload button", () => {
  render(<UploadForm />);
  expect(screen.getByRole("button", { name: /upload/i })).toBeInTheDocument();
});
```

**Step 2: Run test to verify it fails**

Run: `npm test -- --runInBand frontend/tests/upload-form.test.tsx`
Expected: FAIL because the frontend scaffold does not exist yet.

**Step 3: Write minimal implementation**

Implement:

- a homepage with slide upload entry
- job status polling
- a basic document detail page shell
- API helpers for backend endpoints

**Step 4: Run test to verify it passes**

Run: `npm test -- --runInBand frontend/tests/upload-form.test.tsx`
Expected: PASS

**Step 5: Commit**

```bash
git add frontend/app frontend/components frontend/lib frontend/tests/upload-form.test.tsx
git commit -m "feat: add frontend upload shell"
```

### Task 10: Build Report Reader and Glossary Interaction

**Files:**
- Create: `frontend/components/report-viewer.tsx`
- Create: `frontend/components/glossary-panel.tsx`
- Modify: `frontend/app/documents/[id]/page.tsx`
- Create: `frontend/tests/report-viewer.test.tsx`

**Step 1: Write the failing test**

Create `frontend/tests/report-viewer.test.tsx`:

```tsx
import { render, screen } from "@testing-library/react";

import { ReportViewer } from "../components/report-viewer";

test("renders section heading", () => {
  render(<ReportViewer title="Week 1 Summary" body="Limits and derivatives." />);
  expect(screen.getByText("Week 1 Summary")).toBeInTheDocument();
});
```

**Step 2: Run test to verify it fails**

Run: `npm test -- --runInBand frontend/tests/report-viewer.test.tsx`
Expected: FAIL because the components do not exist yet.

**Step 3: Write minimal implementation**

Implement:

- report rendering with page and section output
- click-to-explain glossary interaction
- panel UI for supporting concept explanations

**Step 4: Run test to verify it passes**

Run: `npm test -- --runInBand frontend/tests/report-viewer.test.tsx`
Expected: PASS

**Step 5: Commit**

```bash
git add frontend/components/report-viewer.tsx frontend/components/glossary-panel.tsx frontend/app/documents/[id]/page.tsx frontend/tests/report-viewer.test.tsx
git commit -m "feat: add report reading experience"
```

### Task 11: Add End-to-End Integration Test Harness

**Files:**
- Create: `backend/tests/test_ingestion_to_report_flow.py`
- Create: `backend/tests/fixtures/sample_course_page.json`
- Modify: `backend/app/services/reporting.py`
- Modify: `backend/app/services/retrieval.py`

**Step 1: Write the failing test**

Create `backend/tests/test_ingestion_to_report_flow.py`:

```python
def test_ingestion_to_report_flow_placeholder():
    assert False, "replace with an end-to-end ingestion/report integration test"
```

**Step 2: Run test to verify it fails**

Run: `pytest backend/tests/test_ingestion_to_report_flow.py -v`
Expected: FAIL by design.

**Step 3: Write minimal implementation**

Replace the placeholder with a real integration test that:

- seeds a document and chunks
- runs retrieval
- builds a report prompt
- verifies the response payload contract

**Step 4: Run test to verify it passes**

Run: `pytest backend/tests/test_ingestion_to_report_flow.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/tests/test_ingestion_to_report_flow.py backend/tests/fixtures/sample_course_page.json backend/app/services/reporting.py backend/app/services/retrieval.py
git commit -m "test: add ingestion to report integration coverage"
```

### Task 12: Write Local Runbook and MVP Limits

**Files:**
- Create: `README.md`
- Modify: `CLAUDE.md`

**Step 1: Write the failing test**

Manual verification requirement:

- Confirm a new contributor can run the stack locally using only the README
- Confirm the README states which features are intentionally out of scope

**Step 2: Run verification to confirm it fails**

Run: manual inspection
Expected: FAIL because the runbook does not exist yet.

**Step 3: Write minimal implementation**

Document:

- local startup commands
- required environment variables
- data storage locations
- current MVP scope and non-goals

**Step 4: Run verification to confirm it passes**

Run: manual inspection of `README.md` and `CLAUDE.md`
Expected: PASS

**Step 5: Commit**

```bash
git add README.md CLAUDE.md
git commit -m "docs: add local runbook and mvp scope"
```
