# CoursePulse AI

Transform course slides into structured teaching reports, connect knowledge gaps, and drive targeted revision through mistake diagnosis.

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Node.js 22+
- Python 3.11+

### Environment Setup

```bash
cp .env.example .env
# Edit .env and set your OPENAI_API_KEY
```

### Run with Docker Compose

```bash
docker compose up --build
```

- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **API docs:** http://localhost:8000/docs

### Local Development (without Docker)

**Backend:**

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

**Frontend:**

```bash
cd frontend
npm install
npm run dev
```

### Run Tests

```bash
# Backend
cd backend && python -m pytest -v

# Frontend
cd frontend && npx jest
```

## Required Environment Variables

| Variable | Description |
|---|---|
| `DATABASE_URL` | Postgres connection string |
| `OPENAI_API_KEY` | OpenAI API key for embeddings |
| `FILE_STORAGE_ROOT` | Local path for uploaded files |

## Data Storage

Uploaded files are stored on disk, not in the database:

- `storage/slides/` — course slide files (PDF, PPTX)
- `storage/assignments/` — assignment / quiz images
- `storage/derived/` — generated artifacts

## MVP Scope

### Included

- Upload single course slides (PDF)
- Parse and chunk slide content
- Generate section-level teaching reports
- Provide term definitions (glossary)
- Recommend related short videos
- Upload mistake images and link back to relevant slides
- Generate simple review priorities

### Not Included (deferred)

- Multi-user accounts and authentication
- Study groups and shared mistake pools
- Classroom audio transcription and fusion
- Deep Bilibili integration
- Complex permission systems
- High-quality printable cheat sheet layout engine
