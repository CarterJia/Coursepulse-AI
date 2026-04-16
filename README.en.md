# CoursePulse AI

Turn sleepy lecture slides into a personal TA report.
Upload a PDF, get a structured study report: topic-organized notes, glossary, and relevant Bilibili teaching videos.

**[Live Demo](https://coursepulse-ai.railway.app)** · [中文](README.md)

---

## What it does

CoursePulse AI turns a lecture-slide PDF into a structured study report: organized by topic, surfacing exam points and common mistakes, with formulas, diagrams, and relevant teaching videos pulled from Bilibili. Built for students drowning in slides.

## Status

✅ PDF parsing + two-pass LLM note generation
✅ Semantic embeddings + Bilibili video recommendations
🚧 Homework diagnosis — Vision identifies mistakes and links back to slides
🚧 Pre-exam review report — weighted topic map + cheat sheet

## Architecture

Three tiers: Next.js frontend, FastAPI backend, Postgres + pgvector. Core pipeline is six steps: parse → chunk → embed → Pass-1 planning → Pass-2 writing → video recommendation.

Visual explainer: [`/architecture`](https://coursepulse-ai.railway.app/architecture).

## Run locally in 5 minutes

Prereqs: Docker Desktop, a DeepSeek API key.

```bash
git clone https://github.com/CarterJia/Coursepulse-AI.git
cd coursepulse-ai
cp .env.example .env   # edit .env and set DEEPSEEK_API_KEY
docker compose up
```

Open http://localhost:3000.

## Bring your own key

The Live Demo allows 3 free uploads per IP per day. To run more, click "Use my own API key" at the bottom of the upload area and paste your DeepSeek key. The key lives in your browser's localStorage only — it never hits our server logs.

## Stack

- Next.js 15 / TypeScript / Tailwind / shadcn/ui
- FastAPI / SQLAlchemy / Alembic
- Postgres 16 / pgvector
- DeepSeek Chat / BAAI/bge-small-zh-v1.5
- Docker Compose / Railway

## Design docs

All design specs live in [`docs/superpowers/specs/`](docs/superpowers/specs/). Start with [`2026-04-13-coursepulse-full-product-design.md`](docs/superpowers/specs/2026-04-13-coursepulse-full-product-design.md).

## License

MIT
