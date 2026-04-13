# CoursePulse AI — Full Product Design Spec

> Turn course slides into structured teaching reports, diagnose mistakes, and generate exam review strategies.

## Goal

Transform the existing MVP skeleton into a portfolio-ready, fully functional product that anyone can clone from GitHub, run `docker compose up`, set an OpenAI API key, and start using immediately.

## Constraints & Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| LLM + Embedding | OpenAI GPT-4o + text-embedding-3-small | Single API key covers all AI features |
| Image recognition | GPT-4o Vision | Handles handwriting, formulas, and grading marks better than traditional OCR |
| Deployment | Docker Compose (frontend + backend + postgres) | One command startup, no external services needed |
| Async tasks | FastAPI BackgroundTasks | Single-user scenario, avoids Celery/Redis complexity |
| UI framework | shadcn/ui + Tailwind CSS + next-themes | Product-grade visuals with dark mode |
| YouTube integration | Optional — degrades gracefully without API key | Core experience only requires OpenAI key |
| Vector search | pgvector cosine similarity | Already in schema, no additional infrastructure |

## Architecture

```
Browser
  │
  ▼
┌──────────────────┐
│  Next.js Frontend │  shadcn/ui + Tailwind + next-themes
│  (port 3000)      │
└────────┬─────────┘
         │ REST API
         ▼
┌──────────────────┐
│  FastAPI Backend  │
│  (port 8000)      │
│                   │
│  Sync routes:     │  uploads, queries, glossary, video search
│  BackgroundTasks: │  PDF parsing, report gen, diagnosis
└────────┬─────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌────────┐  ┌──────────┐
│Postgres │  │ OpenAI   │
│pgvector │  │ GPT-4o   │
│ (5432)  │  │ Embedding│
└────────┘  └──────────┘
              ┌──────────┐
              │ YouTube  │ (optional)
              │ Data API │
              └──────────┘
```

All three containers (frontend, backend, db) managed by Docker Compose. OpenAI API called from backend only. YouTube API is optional.

## Implementation Strategy: Vertical Slices

Each slice delivers an end-to-end user-facing feature. The product is usable after each slice.

### Slice 1: Course Report Pipeline (core)

Upload a PDF and receive a structured teaching report with glossary.

**Course management:** For MVP simplicity, a "Default Course" is auto-created on first document upload. Users can optionally name their course via the upload form. All documents and assignments are associated to a course, which is the unit for review priority generation in Slice 4.

**Data flow:**

1. User uploads PDF via frontend
2. File saved to `storage/slides/`, document record written to DB, job created (status=queued)
3. BackgroundTask pipeline:
   - PyMuPDF extracts per-page text → `document_pages`
   - Pages chunked → `knowledge_chunks`
   - Each chunk embedded via `text-embedding-3-small` → `embeddings` (pgvector)
   - Chapters grouped (3-5 pages each), GPT-4o generates expanded lecture notes → `reports`
   - Same GPT-4o call extracts technical terms with definitions and analogies → `glossary_entries`
   - Job marked as succeeded
4. Frontend polls job status, redirects to report page on completion

**Backend changes (existing files):**

| File | Change |
|------|--------|
| `services/ingestion.py` | Replace placeholder UUIDs with real DB writes, launch BackgroundTask |
| `services/embedding.py` | Replace zero vector with OpenAI `text-embedding-3-small` call |
| `services/retrieval.py` | Replace "first N" with pgvector cosine similarity query |
| `services/reporting.py` | Replace prompt return with actual GPT-4o call, structured output |
| `db/session.py` | Connect to real Postgres |
| `api/routes/documents.py` | Inject DB session, write real records |
| `api/routes/reports.py` | Query DB by document_id, return generated reports |

**Backend new files:**

| File | Purpose |
|------|---------|
| `services/glossary.py` | Term extraction + GPT-4o explanation generation |
| `services/prompts.py` | Centralized prompt templates for all GPT-4o calls |
| `api/routes/glossary.py` | `GET /api/documents/{id}/glossary` |

**GPT-4o call strategy:**
- Lecture expansion: batch by chapter (3-5 pages), use JSON mode structured output to get both the expanded notes and extracted terms in a single call
- Prompt templates centralized in `services/prompts.py`

**Frontend pages:**

| Route | Content |
|-------|---------|
| `/` | Upload dropzone + list of processed documents |
| `/documents/[id]` | Report body (left) + glossary panel (right sidebar/sheet) + job progress |

### Slice 2: Video Recommendations

Add related YouTube video suggestions per chapter in the report page.

**Logic:**
- After report generation completes, extract 2-3 core concept keywords per chapter
- Call YouTube Data API v3: query "{keyword} explained", filter duration < 10 min, take top 2
- Store in `video_recommendations` table

**New files:**

| File | Purpose |
|------|---------|
| `models/video_recommendation.py` | document_id, chapter, title, youtube_url, thumbnail, duration |
| `services/video_search.py` | YouTube API wrapper: keyword extraction + search + filtering |
| `api/routes/videos.py` | `GET /api/documents/{id}/videos` |
| `alembic/versions/0002_video_recommendations.py` | New table migration |

**Graceful degradation:**
- No `YOUTUBE_API_KEY` configured → `video_search.py` returns empty list
- Frontend shows info card: "Configure YouTube API Key to enable video recommendations"

**Frontend:**
- "Related Videos" section below each chapter in report page
- Video card component: thumbnail + title + channel + duration badge
- Click opens YouTube in new tab

### Slice 3: Mistake Diagnosis

Upload graded assignment screenshots, get error analysis linked back to course material.

**Data flow:**

1. User uploads assignment image (PNG/JPG)
2. File saved to `storage/assignments/`, assignment record + job created
3. BackgroundTask pipeline:
   - Base64 encode image, send to GPT-4o Vision
   - Prompt: identify all questions, mark which are wrong, extract question content and incorrect answers
   - Returns structured JSON: `[{question, student_answer, correct_answer, error_description}]`
   - For each mistake: extract keywords → embed → pgvector search for most relevant knowledge_chunks → locate slide page numbers
   - Second GPT-4o call: given the mistake and corresponding course material, classify error type and generate remediation
   - Write to `mistake_diagnoses` table
   - Job marked as succeeded

**Error type taxonomy:**

| Type | Key | Description |
|------|-----|-------------|
| Calculation error | `calculation_error` | Right method, arithmetic mistake |
| Logic error | `logic_error` | Flawed reasoning steps |
| Concept gap | `concept_gap` | Fundamental misunderstanding |

**Backend changes:**

| File | Change |
|------|--------|
| `services/diagnosis.py` | Replace placeholder with Vision call + retrieval + error analysis |
| `api/routes/assignments.py` | Inject DB, real writes, launch BackgroundTask |

**New routes:**
- `GET /api/assignments/{id}` — return diagnosis results

**Frontend pages:**

| Route | Content |
|-------|---------|
| `/assignments` | Upload area + list of analyzed assignments |
| `/assignments/[id]` | Diagnosis cards: error type badge (red=concept_gap, orange=logic_error, yellow=calculation_error), slide page link, remediation, practice problem |

**Key interaction:** Clicking the slide page number in a diagnosis card navigates to `/documents/[id]?page=N` and highlights the relevant knowledge point.

### Slice 4: Review Priority System

Aggregate course data and mistake history into an exam preparation strategy.

**Scoring algorithm:**

```
score = 0.4 × content_weight + 0.4 × error_frequency + 0.2 × error_severity
```

Where:
- `content_weight`: chunk text length / total course text length (how much lecture time this topic gets)
- `error_frequency`: number of times this chunk is linked to mistakes / total mistakes
- `error_severity`: weighted by error type (concept_gap=1.0, logic_error=0.6, calculation_error=0.3)

**Priority tiers:**
- `must_know`: top 30% by score
- `high_frequency`: 30%-70%
- `nice_to_know`: bottom 30%

Written to `review_priorities` table.

**Cheat sheet generation:**
- Collect all `must_know` and `high_frequency` chunks
- GPT-4o call: "Generate a concise review outline with core formulas, key conclusions, and common pitfalls"
- Output as Markdown text (no PDF layout engine per CLAUDE.md scope)

**New files:**

| File | Purpose |
|------|---------|
| `services/review.py` | Scoring algorithm + tier assignment + cheat sheet generation |
| `api/routes/review.py` | `POST /api/courses/{id}/review` (trigger), `GET /api/courses/{id}/review` (results) |

**Frontend page:**

| Route | Content |
|-------|---------|
| `/courses/[id]/review` | Review dashboard |

**Dashboard layout:**
- Top: three stat cards (must_know count, high_frequency count, nice_to_know count) with color coding
- Middle: priority list sorted by score, each item shows: topic summary, source page, error type tags
- Bottom: cheat sheet preview (rendered Markdown) with "Copy to clipboard" and "Export Markdown" buttons

### Slice 5: UI Polish & Developer Experience

Final pass to bring the product to portfolio quality.

**shadcn/ui component usage:**

| Purpose | Components |
|---------|-----------|
| File upload | Card + custom Dropzone (drag & drop) |
| Report display | Card, Accordion (chapter collapse), Badge |
| Glossary | Sheet (side drawer) |
| Video cards | Card + AspectRatio (thumbnail) |
| Diagnosis | Card + Badge (colored error type) |
| Review dashboard | Card + Progress + Table |
| Global | Navbar, Sidebar, Skeleton (loading states), Toast (notifications), Dark Mode toggle |

**Navigation:**
- Left sidebar with three sections: Slides, Assignments, Review
- Top navbar with app title + dark mode toggle
- Responsive: sidebar collapses on mobile

**Loading experience:**
- Upload → Skeleton + step-by-step progress text ("Parsing PDF...", "Generating report...")
- Toast notifications on completion/failure
- Long tasks show multi-step progress indicator

**Dark mode:**
- next-themes integration, default follows system preference
- Manual toggle in top-right corner

**Developer experience:**

| Item | Detail |
|------|--------|
| README.md | Rewrite with: project screenshots/GIF, feature list, one-command startup guide, env var table, architecture diagram |
| .env.example | All keys documented (OPENAI_API_KEY required, YOUTUBE_API_KEY optional) |
| Demo data | Bundle a sample PDF + sample assignment screenshot so `docker compose up` immediately has content to show |
| LICENSE | MIT |
| .github/ | Optional: issue templates, contributing guide |

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | Yes | GPT-4o + embedding |
| `DATABASE_URL` | Yes (has default) | Postgres connection string |
| `FILE_STORAGE_ROOT` | Yes (has default) | Local file storage path |
| `YOUTUBE_API_KEY` | No | YouTube Data API v3 for video recommendations |

## Database Tables

Existing (from skeleton):
- `courses`, `documents`, `document_pages`, `knowledge_chunks`, `embeddings`
- `reports`, `glossary_entries`
- `assignments`, `mistake_diagnoses`, `review_priorities`
- `jobs`

New:
- `video_recommendations` (document_id, chapter, title, youtube_url, thumbnail_url, duration_seconds, channel_name)

## API Endpoints Summary

| Method | Path | Slice | Purpose |
|--------|------|-------|---------|
| POST | `/api/documents/upload` | 1 | Upload course slides |
| GET | `/api/documents` | 1 | List all documents |
| GET | `/api/documents/{id}` | 1 | Document detail + reports |
| GET | `/api/documents/{id}/glossary` | 1 | Glossary entries |
| GET | `/api/jobs/{job_id}` | 1 | Job status polling |
| GET | `/api/documents/{id}/videos` | 2 | Video recommendations |
| POST | `/api/assignments/upload` | 3 | Upload assignment screenshot |
| GET | `/api/assignments` | 3 | List assignments |
| GET | `/api/assignments/{id}` | 3 | Diagnosis results |
| POST | `/api/courses/{id}/review` | 4 | Generate review priorities |
| GET | `/api/courses/{id}/review` | 4 | Get review results + cheat sheet |
| POST | `/api/reports/section` | 1 | On-demand section summary |
| GET | `/api/health` | — | Health check |

## Non-Goals (explicitly excluded)

- Multi-user authentication
- Study groups and shared mistake pools
- Classroom audio transcription
- Bilibili integration
- Complex permission systems
- Printable PDF cheat sheet layout engine
- Deployment to cloud (local Docker only for MVP)
