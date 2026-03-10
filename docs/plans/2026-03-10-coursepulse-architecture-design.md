# CoursePulse Architecture Design

**Date:** 2026-03-10

**Project:** CoursePulse AI

**Status:** Approved

## 1. Confirmed Constraints

- Single-user tool for personal use only
- Local-first deployment on the user's machine
- Local web app UX, not a desktop wrapper
- `Next.js` frontend with a separate `FastAPI` backend
- Mixed AI execution model
- `Postgres + pgvector` as the unified data layer
- `Docker Compose` for local orchestration

## 2. Architecture Decision

The approved baseline is a modular monolith:

- `frontend`: `Next.js` application for uploads, report reading, navigation, and review views
- `api`: `FastAPI` service as the only business backend
- `db`: `Postgres 16 + pgvector` for metadata, generated artifacts, and semantic retrieval

The backend remains one deployable service, but its code is split into explicit modules:

- `ingestion`
- `retrieval`
- `reporting`
- `diagnosis`
- `video_search`

This keeps the local MVP simple while preserving a clean path to split out workers later if heavy jobs become a bottleneck.

## 3. Service Boundaries

### Frontend

Responsibilities:

- Upload slides and assignment images
- Show processing state and job progress
- Render generated teaching reports
- Surface glossary definitions and related video recommendations
- Jump from mistakes to related slide pages and review items

### Backend API

Responsibilities:

- Receive files and persist metadata
- Parse slides, PDFs, and images
- Run OCR and formula extraction
- Chunk and embed course content
- Call cloud LLM APIs for explanation, diagnosis, and summary generation
- Return synchronous results for light interactions
- Manage asynchronous jobs for heavy workflows

### Database

Responsibilities:

- Store course and document metadata
- Store page-level extraction output
- Store semantic chunks and embeddings
- Store generated reports, diagnoses, and review priorities
- Track job status for asynchronous workflows

## 4. Storage Design

Files are stored on local disk, not inside the database.

Recommended directories:

- `storage/slides/`
- `storage/assignments/`
- `storage/derived/`

The database stores paths and metadata only.

Core tables:

- `courses`
- `documents`
- `document_pages`
- `knowledge_chunks`
- `embeddings`
- `reports`
- `glossary_entries`
- `assignments`
- `mistake_diagnoses`
- `review_priorities`
- `jobs`

`pgvector` is used only for semantically searchable teaching content and diagnosis support, not for every object in the system.

## 5. Core Processing Flows

### Slide Ingestion

Flow:

1. User uploads `PPTX`, `PDF`, or image files
2. Backend saves the original file locally
3. `ingestion` extracts text, page structure, OCR text, formulas, and visual descriptions
4. `retrieval` creates normalized chunks and embeddings
5. Results are persisted to `Postgres + pgvector`

Execution mode: asynchronous

### Report Generation

Flow:

1. User requests a page, section, or full-document explanation
2. Backend retrieves relevant chunks
3. `reporting` constructs a context package
4. Cloud LLM generates structured teaching output
5. Output is persisted and returned to the client

Execution mode:

- synchronous for page-level and small-section summaries
- asynchronous for chapter-level or full-document reports

### Mistake Diagnosis

Flow:

1. User uploads a marked assignment or quiz image
2. Backend OCR extracts question and feedback cues
3. `diagnosis` identifies likely mistake type
4. `retrieval` maps the mistake to relevant slide pages and chunks
5. Backend returns remediation guidance and targeted review links

Execution mode: asynchronous

### Glossary and Video Support

Flow:

1. User clicks a term or concept
2. Backend retrieves local context and concept signals
3. Glossary explanation is generated
4. `video_search` returns short supporting video recommendations

Execution mode: synchronous

## 6. AI Strategy

The project uses a mixed local-plus-cloud AI model:

- Local responsibilities:
  - file parsing
  - OCR
  - formula extraction
  - chunking
  - caching
  - embedding persistence
- Cloud responsibilities:
  - logic completion
  - pedagogical report writing
  - error diagnosis
  - explanation quality

This balances quality, privacy, and local resource constraints.

## 7. Technical Stack

- Frontend: `Next.js`, `Tailwind CSS`
- Backend: `FastAPI`
- Database: `Postgres 16`, `pgvector`
- Orchestration: `Docker Compose`
- ORM and migrations: `SQLAlchemy`, `Alembic`
- Document parsing: `PyMuPDF`
- OCR: `Tesseract` or `PaddleOCR`
- LLM provider: `OpenAI` or `Claude`
- Video API: `YouTube Data API`

## 8. Recommended Repository Layout

```text
coursepulse/
  frontend/
    app/
    components/
    lib/
    styles/
  backend/
    app/
      api/
      core/
      db/
      models/
      schemas/
      services/
      tasks/
    alembic/
  storage/
    slides/
    assignments/
    derived/
  infra/
    docker/
  docs/
    plans/
  docker-compose.yml
  .env.example
```

## 9. Error Handling

The MVP must distinguish these failure modes:

- file processing failures
- model/API failures
- retrieval or mapping failures

Principles:

- keep the original file
- persist partial progress
- expose job status clearly
- never fabricate mappings when retrieval confidence is weak

## 10. Testing Strategy

Three layers are required:

- unit tests for chunking, task state transitions, diagnosis rules, and prompt assembly
- integration tests for upload -> parse -> index -> retrieve -> summarize
- manual acceptance checks using real course materials and real mistakes

## 11. MVP Boundary

Phase 1 MVP includes:

- upload a single slide deck or PDF
- extract text and generate structured chunks
- generate expanded section summaries
- support glossary explanations
- recommend short supporting videos
- upload mistake images and link them back to relevant slides
- generate simple review priority output

Not included in MVP:

- multi-user accounts
- study groups or shared error banks
- lecture audio fusion
- Bilibili integration
- advanced permissions
- production-grade printable cheat sheet layout

## 12. Why This Design Won

Alternative designs were considered:

- backend-heavy monolith with a minimal frontend
- early split into API plus worker services

The chosen modular monolith was approved because it gives:

- faster local delivery
- clear module boundaries
- low operational overhead
- a clean migration path if async workloads later need dedicated workers
