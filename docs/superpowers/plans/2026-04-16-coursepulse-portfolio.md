# CoursePulse Portfolio Packaging Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn CoursePulse AI into a public GitHub portfolio piece — minimal visual polish, a new `/architecture` explainer page, IP-based quota + BYOK, bilingual README, and a Railway live demo.

**Architecture:** Pure additive changes. New frontend pages are static React/Tailwind. New backend pieces are a `middleware/` package (quota) and one new route (`/api/documents/sample`). The `openai_client` accepts an optional per-request API key so BYOK can flow through without touching business logic. Sample document is populated via a one-time operator upload rather than an Alembic data migration (simpler and matches demo constraints — see Task 7 notes).

**Tech Stack:** Next.js 15, Tailwind CSS, shadcn/ui, FastAPI, Starlette middleware, SQLAlchemy, Alembic, Docker, Railway.

**Spec:** [`docs/superpowers/specs/2026-04-16-coursepulse-portfolio-design.md`](../specs/2026-04-16-coursepulse-portfolio-design.md)

---

## File Structure

### New files

- `frontend/app/architecture/page.tsx` — static `/architecture` page
- `frontend/components/site-header.tsx` — shared top nav (home + architecture links)
- `frontend/components/byok-input.tsx` — collapsible API key input, persists to localStorage
- `frontend/components/quota-indicator.tsx` — shows "Today N/3" or "Using your key"
- `frontend/lib/byok.ts` — localStorage helpers + header injection
- `backend/app/middleware/__init__.py` — empty package marker
- `backend/app/middleware/quota.py` — per-IP daily quota middleware
- `backend/app/middleware/byok.py` — extracts `X-User-API-Key` → `request.state.user_api_key`
- `backend/tests/test_quota_middleware.py` — unit tests for quota
- `backend/tests/test_byok_middleware.py` — unit tests for byok
- `backend/tests/test_documents_sample.py` — test for `/api/documents/sample`
- `scripts/cleanup_storage.sh` — startup cleanup of old files
- `docs/deployment.md` — Railway deployment guide
- `README.md` — new bilingual-ready Chinese README (replaces whatever exists)
- `README.en.md` — English translation

### Modified files

- `frontend/app/layout.tsx` — adds `<SiteHeader />` and Inter font
- `frontend/app/page.tsx` — new Hero + feature strip + sample button
- `frontend/components/upload-form.tsx` — uses BYOK header and shows quota
- `frontend/components/topic-card.tsx` — visual polish (spacing, dividers)
- `frontend/components/video-card.tsx` — polish (uniform border/radius) — already has `referrerPolicy="no-referrer"` from Slice 2 hotfix
- `frontend/lib/api.ts` — upload + sample calls accept/forward BYOK header
- `backend/app/main.py` — register BYOK + quota middleware
- `backend/app/core/config.py` — add quota/sample env var settings
- `backend/app/services/openai_client.py` — `get_openai_client(api_key: str | None = None)`
- `backend/app/services/reporting.py` — pass `api_key` from call sites through to client
- `backend/app/services/glossary.py` — same
- `backend/app/services/report_planner.py` — same
- `backend/app/services/ingestion.py` — thread `api_key` through the pipeline entrypoint
- `backend/app/api/routes/documents.py` — `/api/documents/sample` route + read BYOK from request.state
- `backend/Dockerfile` — run `cleanup_storage.sh` before uvicorn
- `backend/requirements.txt` — no changes expected (fastapi already has middleware support)

---

## Task 1: Minimal Design System + Site Header

Set up the design-system primitives (Inter font, Tailwind tokens) and a shared site header with home + architecture links. This unblocks every subsequent frontend task.

**Files:**
- Modify: `frontend/app/layout.tsx`
- Create: `frontend/components/site-header.tsx`

- [ ] **Step 1: Install Inter font via next/font**

Edit `frontend/app/layout.tsx`. Full new content:

```tsx
import "./globals.css";
import { Inter } from "next/font/google";
import { SiteHeader } from "@/components/site-header";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });

export const metadata = {
  title: "CoursePulse AI",
  description: "Turn sleepy lecture slides into a personal TA report",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={inter.variable}>
      <body className="min-h-screen bg-white text-gray-900 font-sans antialiased">
        <SiteHeader />
        {children}
      </body>
    </html>
  );
}
```

- [ ] **Step 2: Create site header component**

Create `frontend/components/site-header.tsx`:

```tsx
import Link from "next/link";

export function SiteHeader() {
  return (
    <header className="border-b border-gray-200">
      <div className="max-w-6xl mx-auto h-14 px-4 flex items-center justify-between">
        <Link href="/" className="font-semibold text-gray-900 tracking-tight">
          CoursePulse AI
        </Link>
        <nav className="flex items-center gap-6 text-sm text-gray-600">
          <Link href="/architecture" className="hover:text-gray-900 transition-colors">
            Architecture
          </Link>
          <a
            href="https://github.com/CarterJia/Coursepulse-AI"
            className="hover:text-gray-900 transition-colors"
            target="_blank"
            rel="noreferrer"
          >
            GitHub
          </a>
        </nav>
      </div>
    </header>
  );
}
```

Note: the GitHub URL is a placeholder — the user can edit it when they actually publish the repo. The rest is fine as-is.

- [ ] **Step 3: Update globals.css to wire up Inter as the font-sans default**

Open `frontend/app/globals.css` and add inside the `@layer base` block (create the block if missing):

```css
@layer base {
  :root {
    --font-sans: var(--font-inter), "PingFang SC", system-ui, sans-serif;
  }
  body {
    font-family: var(--font-sans);
  }
}
```

If `globals.css` already has `:root` variables, append `--font-sans` at the end of the existing block rather than duplicating.

- [ ] **Step 4: Run dev server and verify**

Run from `/frontend`: `npm run dev`. Open http://localhost:3000. Expected: header bar is visible at top with "CoursePulse AI" on the left and "Architecture" / "GitHub" on the right. Font looks like Inter (not Times/default serif).

- [ ] **Step 5: Commit**

```bash
git add frontend/app/layout.tsx frontend/components/site-header.tsx frontend/app/globals.css
git commit -m "feat(frontend): site header + Inter font"
```

---

## Task 2: Architecture Page

Static explainer page. Three sections: pipeline (6 cards), design decisions (3 items), stack badges.

**Files:**
- Create: `frontend/app/architecture/page.tsx`

- [ ] **Step 1: Create the page**

Create `frontend/app/architecture/page.tsx`:

```tsx
export const metadata = {
  title: "Architecture — CoursePulse AI",
  description: "How the pipeline works and why it was designed this way",
};

type PipelineStep = {
  id: string;
  phase: string;
  tech: string;
  blurb: string;
  tone: "gray" | "blue" | "yellow" | "green";
};

const STEPS: PipelineStep[] = [
  { id: "1", phase: "解析", tech: "PyMuPDF", blurb: "PDF → 每页文本 + 图像", tone: "gray" },
  { id: "2", phase: "切片", tech: "按章节分块", blurb: "104 页 → 104 knowledge chunks", tone: "gray" },
  { id: "3", phase: "向量化", tech: "bge-small-zh", blurb: "pgvector 存储，支持语义检索", tone: "blue" },
  { id: "4", phase: "Pass-1 LLM", tech: "DeepSeek 规划", blurb: "定主题 + 考点 + 关键词", tone: "yellow" },
  { id: "5", phase: "Pass-2 LLM", tech: "逐主题撰写", blurb: "Markdown 讲义 + 公式", tone: "yellow" },
  { id: "6", phase: "视频推荐", tech: "B 站检索 + 余弦相似度", blurb: "阈值 0.62 过滤噪声", tone: "green" },
];

const TONE_STYLES: Record<PipelineStep["tone"], string> = {
  gray: "bg-gray-50 border-gray-200",
  blue: "bg-indigo-50 border-indigo-200",
  yellow: "bg-amber-50 border-amber-200",
  green: "bg-emerald-50 border-emerald-200",
};

export default function ArchitecturePage() {
  return (
    <main className="max-w-6xl mx-auto px-4 py-16 space-y-16">
      <header>
        <p className="text-xs uppercase tracking-widest text-gray-500 font-semibold">How it works</p>
        <h1 className="mt-2 text-3xl font-bold tracking-tight">从 PDF 到结构化讲义的 6 步流水线</h1>
        <p className="mt-3 text-gray-600 max-w-2xl">
          上传一份课件需要协同 5 个 AI 调用、2 种模型、1 个向量库。下面是每一步在做什么。
        </p>
      </header>

      <section aria-label="Pipeline">
        <div className="grid grid-cols-2 md:grid-cols-6 gap-3">
          {STEPS.map((step) => (
            <div key={step.id} className={`rounded-lg border p-3 ${TONE_STYLES[step.tone]}`}>
              <div className="text-[10px] font-bold text-indigo-600">① {step.phase}</div>
              <div className="mt-1 text-sm font-semibold text-gray-900">{step.tech}</div>
              <div className="mt-1 text-xs text-gray-600">{step.blurb}</div>
            </div>
          ))}
        </div>
      </section>

      <section aria-label="Design decisions">
        <p className="text-xs uppercase tracking-widest text-gray-500 font-semibold">Design decisions</p>
        <div className="mt-4 grid md:grid-cols-3 gap-6">
          <article className="space-y-2">
            <h3 className="text-sm font-semibold text-gray-900">为什么分两个 LLM Pass？</h3>
            <p className="text-sm text-gray-600 leading-relaxed">
              Pass-1 只输出结构化 JSON 规划（主题、考点、关键词），便宜快。Pass-2 按主题并发撰写详细 Markdown。
              比单次大提示 token 省约 40%，且失败可局部重试。
            </p>
          </article>
          <article className="space-y-2">
            <h3 className="text-sm font-semibold text-gray-900">为什么相似度阈值是 0.62？</h3>
            <p className="text-sm text-gray-600 leading-relaxed">
              实测 <code className="font-mono text-xs bg-gray-100 px-1 py-0.5 rounded">bge-small-zh</code> 对无关
              中文文本基线分数在 0.3–0.5，噪声带 0.5–0.6，真正相关 ≥0.65。选 0.62 是召回率和噪声的折中。
              曾经因为阈值 0.55 出现过 "Excel IF 函数" 被推给 Q-learning 主题的假阳性案例。
            </p>
          </article>
          <article className="space-y-2">
            <h3 className="text-sm font-semibold text-gray-900">为什么给 Bilibili 加 session warmup？</h3>
            <p className="text-sm text-gray-600 leading-relaxed">
              直接 <code className="font-mono text-xs bg-gray-100 px-1 py-0.5 rounded">requests.get</code> 会被
              反爬：10 次请求 9 次空响应。解决方案：复用 Session、首次 GET <code className="font-mono text-xs bg-gray-100 px-1 py-0.5 rounded">bilibili.com</code>
              拿 <code className="font-mono text-xs bg-gray-100 px-1 py-0.5 rounded">buvid3</code> cookie、带浏览器 header、请求间 0.8s 间隔。
            </p>
          </article>
        </div>
      </section>

      <section aria-label="Stack" className="bg-gray-900 text-white rounded-lg p-6">
        <p className="text-xs uppercase tracking-widest text-gray-400 font-semibold">Stack</p>
        <div className="mt-3 flex flex-wrap gap-2">
          {[
            "Next.js 15",
            "FastAPI",
            "Postgres + pgvector",
            "DeepSeek",
            "sentence-transformers",
            "Docker Compose",
            "Railway",
          ].map((s) => (
            <span key={s} className="bg-gray-800 px-3 py-1 rounded text-xs">
              {s}
            </span>
          ))}
        </div>
      </section>
    </main>
  );
}
```

- [ ] **Step 2: Verify in browser**

Run `npm run dev` from `frontend/`. Navigate to http://localhost:3000/architecture.

Expected:
- Six pipeline cards arranged in a single row on desktop, 2 cols on mobile
- Three design-decision blocks in a 3-col grid on desktop
- Stack card at the bottom with dark background and 7 badges

- [ ] **Step 3: Commit**

```bash
git add frontend/app/architecture/page.tsx
git commit -m "feat(frontend): add /architecture explainer page"
```

---

## Task 3: Homepage Hero Redesign

Replace the current minimal homepage with a Hero section, feature strip showing shipped/in-dev, and a refactored upload block. Sample button is present but only stubbed (wired up in Task 11).

**Files:**
- Modify: `frontend/app/page.tsx`

- [ ] **Step 1: Rewrite page.tsx**

Full new content of `frontend/app/page.tsx`:

```tsx
"use client";

import { useState } from "react";
import { UploadForm } from "@/components/upload-form";
import { JobStatus } from "@/components/job-status";
import { DocumentList } from "@/components/document-list";

const FEATURES: { status: "shipped" | "wip"; title: string; blurb: string }[] = [
  { status: "shipped", title: "PDF 解析 + 两阶段 LLM 讲义生成", blurb: "上传课件，自动生成主题分明的教学报告。" },
  { status: "shipped", title: "语义向量 + B 站视频推荐", blurb: "bge-small-zh 相似度打分，只留真正相关的视频。" },
  { status: "wip", title: "错题诊断", blurb: "Vision 识别作业错误并回链到课件知识点。" },
  { status: "wip", title: "考前复习报告", blurb: "权重地图 + Cheat Sheet 生成。" },
];

export default function HomePage() {
  const [jobId, setJobId] = useState<string | null>(null);
  const [docId, setDocId] = useState<string | null>(null);

  return (
    <main className="max-w-5xl mx-auto py-16 px-4 space-y-16">
      <section>
        <h1 className="text-4xl md:text-5xl font-bold tracking-tight">CoursePulse AI</h1>
        <p className="mt-4 text-lg text-gray-600 max-w-2xl">
          Turn sleepy lecture slides into a personal TA report.
          上传 PDF，自动产出结构化讲义、术语百科、相关教学视频。
        </p>
        <div className="mt-6 flex gap-3">
          <a
            href="#upload"
            className="inline-flex items-center rounded-md bg-indigo-600 text-white px-4 py-2 text-sm font-medium hover:bg-indigo-500 transition-colors"
          >
            Upload your slides
          </a>
          <button
            type="button"
            disabled
            className="inline-flex items-center rounded-md border border-gray-300 bg-white text-gray-500 px-4 py-2 text-sm font-medium cursor-not-allowed"
            title="Wired up in the sample-route task"
          >
            Try the sample
          </button>
        </div>
      </section>

      <section aria-label="Features" className="grid md:grid-cols-2 gap-4">
        {FEATURES.map((f) => (
          <div
            key={f.title}
            className={`rounded-lg border p-4 ${
              f.status === "shipped" ? "border-gray-200 bg-white" : "border-dashed border-gray-300 bg-gray-50"
            }`}
          >
            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold">
                {f.status === "shipped" ? (
                  <span className="text-emerald-600">✅ 已上线</span>
                ) : (
                  <span className="text-gray-500">🚧 研发中</span>
                )}
              </span>
            </div>
            <h3 className="mt-2 font-semibold text-gray-900">{f.title}</h3>
            <p className="mt-1 text-sm text-gray-600">{f.blurb}</p>
          </div>
        ))}
      </section>

      <section id="upload" className="space-y-6">
        <div>
          <h2 className="text-2xl font-semibold tracking-tight">Upload</h2>
          <p className="mt-1 text-sm text-gray-600">PDF only. Default quota: 3 uploads per IP per day.</p>
        </div>

        <UploadForm
          onUploaded={(data) => {
            setDocId(data.document_id);
            setJobId(data.job_id);
          }}
        />

        {jobId && (
          <JobStatus
            jobId={jobId}
            onComplete={() => {
              if (docId) window.location.href = `/documents/${docId}`;
            }}
          />
        )}
      </section>

      <section aria-label="Recent documents">
        <h2 className="text-2xl font-semibold tracking-tight mb-4">Recent documents</h2>
        <DocumentList />
      </section>
    </main>
  );
}
```

- [ ] **Step 2: Verify in browser**

Run `npm run dev`. Open http://localhost:3000. Expected:
- Hero with large bilingual title, indigo "Upload your slides" CTA, disabled "Try the sample" button
- 2×2 feature grid: two shipped (✅ solid border), two WIP (🚧 dashed border)
- Upload section anchored at `#upload`
- DocumentList at the bottom

- [ ] **Step 3: Commit**

```bash
git add frontend/app/page.tsx
git commit -m "feat(frontend): hero + feature strip + structured homepage"
```

---

## Task 4: Report Page + Component Polish

Tighten the visual layers on `topic-card.tsx` and `video-card.tsx` to match the new aesthetic.

**Files:**
- Modify: `frontend/components/topic-card.tsx`
- Modify: `frontend/components/video-card.tsx`

- [ ] **Step 1: Read current topic-card.tsx**

Read `frontend/components/topic-card.tsx` and identify the title element and card container. Keep all existing behavior (collapse, videos, etc.). The only changes are:

- Title from `text-xl` (or whatever it is) → `text-2xl`, add `tracking-tight`
- Card root: add `border-gray-200` if not present, `rounded-lg`, `shadow-none`

- [ ] **Step 2: Apply the tweaks**

Use Edit tool to change only the specific class strings. Do not rewrite the file wholesale. After the edit, the title element should look like:

```tsx
<h2 className="text-2xl font-semibold tracking-tight text-gray-900">{title}</h2>
```

And the outermost card element's className should include `border border-gray-200 rounded-lg`.

- [ ] **Step 3: Read current video-card.tsx**

Read `frontend/components/video-card.tsx`. The cover `<img>` already has `referrerPolicy="no-referrer"` from the Slice 2 hotfix — do not change that. The only change: ensure cover img has `rounded border border-gray-200` and the outer card uses `border-gray-200 rounded-lg`.

- [ ] **Step 4: Apply the video-card tweaks**

Use Edit for minimal classname changes only.

- [ ] **Step 5: Verify visually**

Open an existing report at http://localhost:3000/documents/<any-existing-id>. Expected: cards look cleaner (thin gray borders, consistent 8px radius, no heavy shadow).

- [ ] **Step 6: Commit**

```bash
git add frontend/components/topic-card.tsx frontend/components/video-card.tsx
git commit -m "feat(frontend): tighten card visuals on report page"
```

---

## Task 5: OpenAI Client Accepts Per-Request API Key

Support BYOK by allowing callers to pass an override key. Default path unchanged (reads env).

**Files:**
- Modify: `backend/app/services/openai_client.py`
- Modify: `backend/tests/test_openai_client.py`

- [ ] **Step 1: Write failing test**

Open `backend/tests/test_openai_client.py`. Append:

```python
def test_get_openai_client_uses_override_key(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "env-key")
    reset_openai_client()
    client = get_openai_client(api_key="user-key")
    assert client.api_key == "user-key"


def test_get_openai_client_override_does_not_cache(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "env-key")
    reset_openai_client()
    _ = get_openai_client(api_key="user-key")
    default_client = get_openai_client()
    assert default_client.api_key == "env-key"
```

You will need these imports at the top of the test file (add only if missing):

```python
from app.services.openai_client import get_openai_client, reset_openai_client
```

- [ ] **Step 2: Run tests — expect failure**

```bash
cd backend && pytest tests/test_openai_client.py -v
```

Expected: the two new tests fail (`get_openai_client()` takes no args).

- [ ] **Step 3: Implement override**

Replace contents of `backend/app/services/openai_client.py`:

```python
from __future__ import annotations

import os

from openai import OpenAI

_client: OpenAI | None = None

DEEPSEEK_BASE_URL = "https://api.deepseek.com"


def get_openai_client(api_key: str | None = None) -> OpenAI:
    """Return an OpenAI-compatible client pointed at DeepSeek.

    When ``api_key`` is provided, a one-shot client is returned without touching
    the module-level cache — this is the BYOK path. When omitted, the cached
    client (created from ``DEEPSEEK_API_KEY``) is used.
    """
    if api_key:
        return OpenAI(api_key=api_key, base_url=DEEPSEEK_BASE_URL)

    global _client
    if _client is None:
        _client = OpenAI(
            api_key=os.getenv("DEEPSEEK_API_KEY", ""),
            base_url=DEEPSEEK_BASE_URL,
        )
    return _client


def reset_openai_client() -> None:
    """Reset the cached client (used in tests)."""
    global _client
    _client = None
```

- [ ] **Step 4: Run tests — expect pass**

```bash
cd backend && pytest tests/test_openai_client.py -v
```

Expected: all tests in the file pass.

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/openai_client.py backend/tests/test_openai_client.py
git commit -m "feat(backend): openai_client accepts per-request api_key override"
```

---

## Task 6: Thread api_key Through Services

Every service that calls `get_openai_client()` needs to forward the caller's api_key. Callers at the top of the pipeline will come from Task 8.

**Files:**
- Modify: `backend/app/services/reporting.py`
- Modify: `backend/app/services/glossary.py`
- Modify: `backend/app/services/report_planner.py`
- Modify: `backend/app/services/ingestion.py`

- [ ] **Step 1: Update `glossary.py`**

Change the signature:

```python
def extract_glossary(text: str, api_key: str | None = None) -> list[dict[str, str]]:
    client = get_openai_client(api_key=api_key)
    # ... rest unchanged
```

- [ ] **Step 2: Update `report_planner.py`**

Find the function at line 132 that calls `get_openai_client()`. Add `api_key: str | None = None` to its signature, and pass it through:

```python
def generate_plan(
    pages: list[tuple[int, str]],
    image_manifest: dict[int, list[str]],
    api_key: str | None = None,
) -> dict[str, Any]:
    client = get_openai_client(api_key=api_key)
    # ... rest unchanged
```

If there's also a `build_fallback_plan` caller that doesn't hit the LLM, leave it alone.

- [ ] **Step 3: Update `reporting.py`**

Both call sites (around lines 158 and 203) need forwarding. Add `api_key: str | None = None` to each containing function's signature. Example for `generate_topic_card`:

```python
def generate_topic_card(
    topic: dict[str, Any],
    pages: list[tuple[int, str]],
    image_paths: list[str],
    api_key: str | None = None,
) -> str:
    client = get_openai_client(api_key=api_key)
    # ... rest unchanged
```

And for `generate_all_topic_cards`, forward `api_key` down to each `generate_topic_card` call inside the ThreadPoolExecutor.

Also add `api_key` to `generate_chapter_report` if it calls the client.

- [ ] **Step 4: Update `ingestion.py`**

Find `run_ingestion_pipeline` and extend its signature with `api_key: str | None = None` at the end. Forward it to every service call: `generate_plan`, `generate_all_topic_cards`, `extract_glossary`, and any other LLM call inside.

Read `ingestion.py` first to see the exact call chain — keep changes minimal, just add the parameter and pass it through.

- [ ] **Step 5: Run existing tests to make sure nothing broke**

```bash
cd backend && pytest tests/ -v -x
```

Expected: all previously-passing tests still pass. Any test that calls these functions positionally is unaffected since `api_key` is a keyword-only new arg with a default.

- [ ] **Step 6: Commit**

```bash
git add backend/app/services/reporting.py backend/app/services/glossary.py \
  backend/app/services/report_planner.py backend/app/services/ingestion.py
git commit -m "feat(backend): thread api_key through reporting pipeline services"
```

---

## Task 7: BYOK Middleware

Small middleware that reads `X-User-API-Key` and sticks it on `request.state.user_api_key` (or None).

**Files:**
- Create: `backend/app/middleware/__init__.py` (empty)
- Create: `backend/app/middleware/byok.py`
- Create: `backend/tests/test_byok_middleware.py`
- Modify: `backend/app/main.py`

- [ ] **Step 1: Write failing test**

Create `backend/tests/test_byok_middleware.py`:

```python
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from app.middleware.byok import BYOKMiddleware


def _build_app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(BYOKMiddleware)

    @app.get("/echo")
    def echo(request: Request):
        return {"key": request.state.user_api_key}

    return app


def test_byok_header_populates_request_state():
    client = TestClient(_build_app())
    resp = client.get("/echo", headers={"X-User-API-Key": "sk-user"})
    assert resp.status_code == 200
    assert resp.json() == {"key": "sk-user"}


def test_byok_header_absent_sets_none():
    client = TestClient(_build_app())
    resp = client.get("/echo")
    assert resp.status_code == 200
    assert resp.json() == {"key": None}


def test_byok_header_empty_string_is_none():
    client = TestClient(_build_app())
    resp = client.get("/echo", headers={"X-User-API-Key": ""})
    assert resp.status_code == 200
    assert resp.json() == {"key": None}
```

- [ ] **Step 2: Run tests — expect failure**

```bash
cd backend && pytest tests/test_byok_middleware.py -v
```

Expected: ModuleNotFoundError on `app.middleware.byok`.

- [ ] **Step 3: Create middleware package + module**

Create `backend/app/middleware/__init__.py` (empty file — just establishes the package).

Create `backend/app/middleware/byok.py`:

```python
from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class BYOKMiddleware(BaseHTTPMiddleware):
    """Read X-User-API-Key and store it on request.state.user_api_key.

    Empty strings are treated as absent. Value is never logged.
    """

    async def dispatch(self, request: Request, call_next) -> Response:  # type: ignore[override]
        raw = request.headers.get("X-User-API-Key")
        request.state.user_api_key = raw or None
        return await call_next(request)
```

- [ ] **Step 4: Run tests — expect pass**

```bash
cd backend && pytest tests/test_byok_middleware.py -v
```

Expected: 3 tests pass.

- [ ] **Step 5: Register middleware in main.py**

Edit `backend/app/main.py`. After the CORS middleware block, add:

```python
from app.middleware.byok import BYOKMiddleware
app.add_middleware(BYOKMiddleware)
```

Place the import at the top with the other `from app.middleware...` imports (creating a new import line).

- [ ] **Step 6: Run full test suite to confirm nothing broke**

```bash
cd backend && pytest tests/ -v -x
```

Expected: all pass.

- [ ] **Step 7: Commit**

```bash
git add backend/app/middleware/__init__.py backend/app/middleware/byok.py \
  backend/tests/test_byok_middleware.py backend/app/main.py
git commit -m "feat(backend): BYOK middleware reads X-User-API-Key"
```

---

## Task 8: Quota Middleware

Per-IP daily quota with UTC reset. In-memory dict. If BYOK is set on `request.state.user_api_key`, the quota is skipped.

**Files:**
- Create: `backend/app/middleware/quota.py`
- Create: `backend/tests/test_quota_middleware.py`
- Modify: `backend/app/core/config.py`
- Modify: `backend/app/main.py`

- [ ] **Step 1: Add setting**

In `backend/app/core/config.py`, extend the `Settings` model:

```python
class Settings(BaseModel):
    app_name: str = "CoursePulse API"
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://coursepulse:coursepulse@db:5432/coursepulse",
    )
    file_storage_root: str = os.getenv("FILE_STORAGE_ROOT", "/app/storage")
    deepseek_api_key: str = os.getenv("DEEPSEEK_API_KEY", "")
    upload_quota_per_ip: int = int(os.getenv("UPLOAD_QUOTA_PER_IP", "3"))
    sample_document_id: str = os.getenv("SAMPLE_DOCUMENT_ID", "")
```

- [ ] **Step 2: Write failing tests**

Create `backend/tests/test_quota_middleware.py`:

```python
from datetime import datetime, timezone

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from app.middleware.quota import QuotaMiddleware, _reset_counter_for_tests


@pytest.fixture(autouse=True)
def _reset():
    _reset_counter_for_tests()
    yield
    _reset_counter_for_tests()


def _build_app(limit: int = 2) -> FastAPI:
    app = FastAPI()
    app.add_middleware(QuotaMiddleware, limit=limit, guarded_path="/api/documents/upload")

    @app.post("/api/documents/upload")
    def upload(request: Request):
        return {"ok": True}

    @app.get("/api/other")
    def other():
        return {"ok": True}

    return app


def test_quota_allows_first_n_requests():
    client = TestClient(_build_app(limit=2))
    assert client.post("/api/documents/upload").status_code == 200
    assert client.post("/api/documents/upload").status_code == 200


def test_quota_blocks_after_limit():
    client = TestClient(_build_app(limit=2))
    client.post("/api/documents/upload")
    client.post("/api/documents/upload")
    resp = client.post("/api/documents/upload")
    assert resp.status_code == 429
    body = resp.json()
    assert body["detail"] == "Daily quota exhausted"
    assert body["use_byok"] is True


def test_quota_only_applies_to_guarded_path():
    client = TestClient(_build_app(limit=0))
    resp = client.get("/api/other")
    assert resp.status_code == 200


def test_quota_skipped_when_byok_present():
    app = FastAPI()
    app.add_middleware(QuotaMiddleware, limit=0, guarded_path="/api/documents/upload")

    @app.middleware("http")
    async def fake_byok(request, call_next):
        request.state.user_api_key = "sk-user"
        return await call_next(request)

    @app.post("/api/documents/upload")
    def upload():
        return {"ok": True}

    client = TestClient(app)
    assert client.post("/api/documents/upload").status_code == 200


def test_quota_response_header_exposes_remaining():
    client = TestClient(_build_app(limit=3))
    resp = client.post("/api/documents/upload")
    assert resp.status_code == 200
    assert resp.headers.get("X-Quota-Remaining") == "2"
```

- [ ] **Step 3: Run tests — expect failure**

```bash
cd backend && pytest tests/test_quota_middleware.py -v
```

Expected: ModuleNotFoundError on `app.middleware.quota`.

- [ ] **Step 4: Implement middleware**

Create `backend/app/middleware/quota.py`:

```python
from __future__ import annotations

import threading
from datetime import datetime, timezone

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

_counter: dict[str, tuple[int, str]] = {}
_lock = threading.Lock()


def _today_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _reset_counter_for_tests() -> None:
    with _lock:
        _counter.clear()


def _client_ip(request: Request) -> str:
    fwd = request.headers.get("x-forwarded-for")
    if fwd:
        return fwd.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


class QuotaMiddleware(BaseHTTPMiddleware):
    """Limit POSTs to a guarded path to N per IP per UTC day.

    BYOK bypass: when ``request.state.user_api_key`` is truthy (set by BYOKMiddleware),
    the quota check is skipped. Register BYOKMiddleware BEFORE QuotaMiddleware so the
    attribute is populated in time.
    """

    def __init__(self, app, *, limit: int, guarded_path: str):
        super().__init__(app)
        self.limit = limit
        self.guarded_path = guarded_path

    async def dispatch(self, request: Request, call_next) -> Response:  # type: ignore[override]
        if request.method != "POST" or request.url.path != self.guarded_path:
            return await call_next(request)

        if getattr(request.state, "user_api_key", None):
            return await call_next(request)

        ip = _client_ip(request)
        today = _today_utc()

        with _lock:
            count, day = _counter.get(ip, (0, today))
            if day != today:
                count = 0
                day = today
            if count >= self.limit:
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Daily quota exhausted", "use_byok": True},
                )
            count += 1
            _counter[ip] = (count, day)
            remaining = max(self.limit - count, 0)

        response = await call_next(request)
        response.headers["X-Quota-Remaining"] = str(remaining)
        return response
```

- [ ] **Step 5: Run tests — expect pass**

```bash
cd backend && pytest tests/test_quota_middleware.py -v
```

Expected: 5 tests pass.

- [ ] **Step 6: Register in main.py (in correct order)**

Starlette applies middleware in reverse registration order, so **BYOK must be added AFTER Quota** to execute first. Edit `backend/app/main.py`:

```python
from app.core.config import settings
from app.middleware.byok import BYOKMiddleware
from app.middleware.quota import QuotaMiddleware

# ... existing code ...

app.add_middleware(
    QuotaMiddleware,
    limit=settings.upload_quota_per_ip,
    guarded_path="/api/documents/upload",
)
app.add_middleware(BYOKMiddleware)
```

Ordering rationale (worth a one-line comment above the two registrations):

```python
# Middleware runs in reverse of registration — BYOK registered last so it
# runs first, setting request.state.user_api_key before Quota checks it.
```

- [ ] **Step 7: Run full test suite**

```bash
cd backend && pytest tests/ -v -x
```

Expected: all pass.

- [ ] **Step 8: Commit**

```bash
git add backend/app/middleware/quota.py backend/tests/test_quota_middleware.py \
  backend/app/core/config.py backend/app/main.py
git commit -m "feat(backend): per-IP daily quota middleware with BYOK bypass"
```

---

## Task 9: Upload Route Reads BYOK From request.state

The upload route already exists. It needs to pull the BYOK key out of `request.state` and hand it to the ingestion pipeline (added in Task 6).

**Files:**
- Modify: `backend/app/api/routes/documents.py`

- [ ] **Step 1: Update the upload handler**

Replace the existing `upload_document` function in `backend/app/api/routes/documents.py`:

```python
@router.post("/documents/upload", response_model=DocumentUploadResponse, status_code=202)
async def upload_document(
    request: Request,
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
    user_api_key = getattr(request.state, "user_api_key", None)
    background_tasks.add_task(run_ingestion_pipeline, doc.id, job.id, api_key=user_api_key)
    return JSONResponse(
        status_code=202,
        content={"document_id": str(doc.id), "job_id": str(job.id), "status": "queued"},
    )
```

And add `from fastapi import Request` to the import at the top (extending the existing `from fastapi import ...` line).

- [ ] **Step 2: Smoke-test manually**

Use any small PDF you have locally (the repo does not ship a sample PDF fixture). Set `PDF=/path/to/any.pdf` first:

```bash
docker compose up -d --build backend
curl -i -X POST -F "file=@$PDF" http://localhost:8000/api/documents/upload
```

Expected: 202 response with header `X-Quota-Remaining: 2`. Pipeline runs against env `DEEPSEEK_API_KEY` (no BYOK key).

Then try with a bogus BYOK key:

```bash
curl -i -X POST -H 'X-User-API-Key: sk-fake' -F "file=@$PDF" http://localhost:8000/api/documents/upload
```

Expected: 202. Job eventually fails (fake key) — that's fine, the point is that BYOK path is taken (no quota decrement). Header `X-Quota-Remaining` should NOT be present on this response because the quota middleware early-returns.

- [ ] **Step 3: Commit**

```bash
git add backend/app/api/routes/documents.py
git commit -m "feat(backend): upload route forwards BYOK key to pipeline"
```

---

## Task 10: Sample Document Route

`GET /api/documents/sample` returns the preloaded document's ID from `settings.sample_document_id`. If unset, 404.

**Note on scope deviation from spec:** The spec mentioned an Alembic seed migration. In practice, the sample is populated by one operator-run upload in the deployed environment (documented in `docs/deployment.md` in Task 14). This keeps migrations schema-only and avoids bundling pre-generated report JSON inside a migration file. The env var `SAMPLE_DOCUMENT_ID` points to whatever UUID that upload produces.

**Files:**
- Modify: `backend/app/api/routes/documents.py`
- Create: `backend/tests/test_documents_sample.py`

- [ ] **Step 1: Write failing test**

Create `backend/tests/test_documents_sample.py`:

```python
import uuid

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_sample_returns_configured_id(monkeypatch, client):
    sample_id = str(uuid.uuid4())
    monkeypatch.setattr(settings, "sample_document_id", sample_id)
    resp = client.get("/api/documents/sample")
    assert resp.status_code == 200
    assert resp.json() == {"document_id": sample_id}


def test_sample_returns_404_when_unconfigured(monkeypatch, client):
    monkeypatch.setattr(settings, "sample_document_id", "")
    resp = client.get("/api/documents/sample")
    assert resp.status_code == 404
```

- [ ] **Step 2: Run test — expect failure**

```bash
cd backend && pytest tests/test_documents_sample.py -v
```

Expected: 404 on both (no route exists).

- [ ] **Step 3: Add the route**

In `backend/app/api/routes/documents.py`, add at the end of the file:

```python
@router.get("/documents/sample")
def get_sample_document_id():
    from fastapi import HTTPException
    from app.core.config import settings
    if not settings.sample_document_id:
        raise HTTPException(status_code=404, detail="Sample document not configured")
    return {"document_id": settings.sample_document_id}
```

- [ ] **Step 4: Run tests — expect pass**

```bash
cd backend && pytest tests/test_documents_sample.py -v
```

Expected: 2 tests pass.

- [ ] **Step 5: Commit**

```bash
git add backend/app/api/routes/documents.py backend/tests/test_documents_sample.py
git commit -m "feat(backend): GET /api/documents/sample route"
```

---

## Task 11: Frontend BYOK + Quota + Sample Button Wiring

All three pieces land together because the upload form uses all of them.

**Files:**
- Create: `frontend/lib/byok.ts`
- Create: `frontend/components/byok-input.tsx`
- Create: `frontend/components/quota-indicator.tsx`
- Modify: `frontend/components/upload-form.tsx`
- Modify: `frontend/lib/api.ts`
- Modify: `frontend/app/page.tsx`

- [ ] **Step 1: Create BYOK helper**

Create `frontend/lib/byok.ts`:

```ts
const STORAGE_KEY = "cp_deepseek_api_key";

export function getStoredKey(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(STORAGE_KEY);
}

export function setStoredKey(key: string) {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(STORAGE_KEY, key);
}

export function clearStoredKey() {
  if (typeof window === "undefined") return;
  window.localStorage.removeItem(STORAGE_KEY);
}

export function withBYOKHeaders(headers: HeadersInit = {}): HeadersInit {
  const key = getStoredKey();
  if (!key) return headers;
  return { ...headers, "X-User-API-Key": key };
}
```

- [ ] **Step 2: Update api.ts to forward BYOK and expose quota + sample**

Replace content of `frontend/lib/api.ts`:

```ts
import { withBYOKHeaders } from "@/lib/byok";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export type SectionType =
  | "overview"
  | "tldr"
  | "topic"
  | "exam_summary"
  | "quick_review";

export interface Report {
  id: string;
  title: string;
  body: string;
  section_type: SectionType;
}

export interface UploadResult {
  document_id: string;
  job_id: string;
  status: string;
  quota_remaining: number | null;
}

export async function uploadDocument(file: File): Promise<UploadResult> {
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch(`${API_BASE}/api/documents/upload`, {
    method: "POST",
    headers: withBYOKHeaders(),
    body: formData,
  });
  if (res.status === 429) {
    const body = await res.json();
    throw new Error(body.detail || "Daily quota exhausted");
  }
  const data = await res.json();
  const remaining = res.headers.get("X-Quota-Remaining");
  return { ...data, quota_remaining: remaining === null ? null : Number(remaining) };
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

export interface Video {
  bvid: string;
  title: string;
  bilibili_url: string;
  cover_url: string;
  up_name: string;
  duration_seconds: number;
  play_count: number;
  similarity_score: number;
}

export interface TopicVideos {
  topic_title: string;
  videos: Video[];
}

export async function getVideos(documentId: string): Promise<TopicVideos[]> {
  const res = await fetch(`${API_BASE}/api/documents/${documentId}/videos`);
  if (!res.ok) return [];
  return res.json();
}

export async function getSampleDocumentId(): Promise<string | null> {
  const res = await fetch(`${API_BASE}/api/documents/sample`);
  if (!res.ok) return null;
  const body = await res.json();
  return body.document_id;
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

- [ ] **Step 3: Create BYOK input component**

Create `frontend/components/byok-input.tsx`:

```tsx
"use client";

import { useEffect, useState } from "react";
import { clearStoredKey, getStoredKey, setStoredKey } from "@/lib/byok";

export function BYOKInput() {
  const [expanded, setExpanded] = useState(false);
  const [value, setValue] = useState("");
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    const existing = getStoredKey();
    if (existing) {
      setSaved(true);
    }
  }, []);

  return (
    <div className="text-sm">
      {!expanded ? (
        <button
          type="button"
          onClick={() => setExpanded(true)}
          className="text-indigo-600 hover:underline"
        >
          {saved ? "Using your API key — change" : "Use my own API key (unlock unlimited)"}
        </button>
      ) : (
        <div className="flex gap-2 items-center">
          <input
            type="password"
            value={value}
            onChange={(e) => setValue(e.target.value)}
            placeholder="sk-..."
            className="flex-1 rounded border border-gray-300 px-3 py-1.5 text-sm"
          />
          <button
            type="button"
            onClick={() => {
              if (value.trim()) {
                setStoredKey(value.trim());
                setSaved(true);
              } else {
                clearStoredKey();
                setSaved(false);
              }
              setExpanded(false);
              setValue("");
            }}
            className="rounded bg-gray-900 text-white px-3 py-1.5 text-sm hover:bg-gray-700"
          >
            Save
          </button>
          <button
            type="button"
            onClick={() => {
              clearStoredKey();
              setSaved(false);
              setExpanded(false);
              setValue("");
            }}
            className="text-gray-500 hover:text-gray-900 text-xs"
          >
            Clear
          </button>
        </div>
      )}
      <p className="mt-1 text-xs text-gray-500">
        Stored only in your browser's localStorage. Never sent to our server's logs.
      </p>
    </div>
  );
}
```

- [ ] **Step 4: Create quota indicator component**

Create `frontend/components/quota-indicator.tsx`:

```tsx
"use client";

import { useEffect, useState } from "react";
import { getStoredKey } from "@/lib/byok";

interface Props {
  remaining: number | null;
}

export function QuotaIndicator({ remaining }: Props) {
  const [hasKey, setHasKey] = useState(false);

  useEffect(() => {
    setHasKey(!!getStoredKey());
  }, [remaining]);

  if (hasKey) {
    return <span className="text-xs text-gray-500">Using your API key · unlimited</span>;
  }
  if (remaining === null) {
    return <span className="text-xs text-gray-500">Daily quota: 3 uploads</span>;
  }
  return <span className="text-xs text-gray-500">Today: {remaining}/3 remaining</span>;
}
```

- [ ] **Step 5: Update upload-form to use both**

Replace `frontend/components/upload-form.tsx`:

```tsx
"use client";

import { useRef, useState, useCallback } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { uploadDocument } from "@/lib/api";
import { BYOKInput } from "@/components/byok-input";
import { QuotaIndicator } from "@/components/quota-indicator";

interface UploadFormProps {
  onUploaded?: (data: { document_id: string; job_id: string }) => void;
}

export function UploadForm({ onUploaded }: UploadFormProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [uploading, setUploading] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const [remaining, setRemaining] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleFile = useCallback(
    async (file: File) => {
      setUploading(true);
      setError(null);
      try {
        const data = await uploadDocument(file);
        setRemaining(data.quota_remaining);
        onUploaded?.(data);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Upload failed");
      } finally {
        setUploading(false);
      }
    },
    [onUploaded]
  );

  return (
    <div className="space-y-3">
      <Card
        className={`border-2 border-dashed transition-colors ${
          dragOver ? "border-indigo-500 bg-indigo-50" : "border-gray-300"
        }`}
        onDragOver={(e) => {
          e.preventDefault();
          setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragOver(false);
          const file = e.dataTransfer.files[0];
          if (file) handleFile(file);
        }}
      >
        <CardContent className="flex flex-col items-center justify-center py-10 gap-4">
          <p className="text-gray-500 text-sm">Drop your PDF here, or click to browse</p>
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
          <Button variant="outline" disabled={uploading} onClick={() => inputRef.current?.click()}>
            {uploading ? "Uploading..." : "Upload"}
          </Button>
        </CardContent>
      </Card>

      <div className="flex items-center justify-between">
        <QuotaIndicator remaining={remaining} />
        <BYOKInput />
      </div>

      {error && <p className="text-sm text-red-600">{error}</p>}
    </div>
  );
}
```

- [ ] **Step 6: Wire the sample button on the homepage**

Open `frontend/app/page.tsx` (the file from Task 3). Replace the `disabled` sample button with:

```tsx
<button
  type="button"
  onClick={async () => {
    const { getSampleDocumentId } = await import("@/lib/api");
    const id = await getSampleDocumentId();
    if (id) {
      window.location.href = `/documents/${id}`;
    } else {
      alert("Sample document is not configured yet. Check back later!");
    }
  }}
  className="inline-flex items-center rounded-md border border-gray-300 bg-white text-gray-900 px-4 py-2 text-sm font-medium hover:bg-gray-50 transition-colors"
>
  Try the sample
</button>
```

- [ ] **Step 7: Manual verification**

With backend running:

1. Open http://localhost:3000 — verify the BYOK link and "Daily quota: 3 uploads" appear under the upload card.
2. Upload a small PDF — verify it changes to "Today: 2/3 remaining".
3. Click "Use my own API key", paste a dummy key like `sk-test`, save. Verify label changes to "Using your API key · unlimited".
4. Upload again — quota label stays "Using your API key". In browser devtools Network tab, confirm `X-User-API-Key: sk-test` header appears.
5. Click "change" → "Clear". Verify link resets.
6. Click "Try the sample" — if backend has no `SAMPLE_DOCUMENT_ID` set, expect the alert. If it does, expect navigation to that document's page.

- [ ] **Step 8: Commit**

```bash
git add frontend/lib/byok.ts frontend/lib/api.ts \
  frontend/components/byok-input.tsx frontend/components/quota-indicator.tsx \
  frontend/components/upload-form.tsx frontend/app/page.tsx
git commit -m "feat(frontend): BYOK input + quota indicator + sample button wiring"
```

---

## Task 12: Storage Cleanup Script

Cleans files older than 7 days from `storage/slides/` and `storage/assignments/` on container startup. The `storage/samples/` directory (if present) is not touched.

**Files:**
- Create: `scripts/cleanup_storage.sh`
- Modify: `backend/Dockerfile`

- [ ] **Step 1: Create the cleanup script**

Create `scripts/cleanup_storage.sh`:

```sh
#!/bin/sh
set -eu

ROOT="${FILE_STORAGE_ROOT:-/app/storage}"

for sub in slides assignments derived; do
  dir="$ROOT/$sub"
  if [ -d "$dir" ]; then
    find "$dir" -type f -mtime +7 -delete 2>/dev/null || true
    find "$dir" -type d -empty -delete 2>/dev/null || true
  fi
done

echo "[cleanup] Storage cleanup complete. Root: $ROOT"
```

- [ ] **Step 2: Make it executable and add to Dockerfile**

Make executable locally (matters for Linux):

```bash
chmod +x scripts/cleanup_storage.sh
```

Edit `backend/Dockerfile`. Replace current content with:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY backend/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY backend /app/backend
COPY scripts/cleanup_storage.sh /app/scripts/cleanup_storage.sh
RUN chmod +x /app/scripts/cleanup_storage.sh

WORKDIR /app/backend

ENV PYTHONPATH=/app/backend

CMD ["sh", "-c", "/app/scripts/cleanup_storage.sh && alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
```

Note: `--reload` is dropped from CMD because production Railway doesn't need it. Local dev already uses `docker-compose.yml` which can override the command — check that file to confirm (it typically does for dev).

- [ ] **Step 3: Verify locally**

```bash
docker compose up -d --build backend
docker compose logs backend | head -20
```

Expected: "[cleanup] Storage cleanup complete. Root: /app/storage" appears before uvicorn starts.

- [ ] **Step 4: Commit**

```bash
git add scripts/cleanup_storage.sh backend/Dockerfile
git commit -m "chore(deploy): cleanup old uploads on container startup"
```

---

## Task 13: README (Chinese)

Rewrite `README.md` with the bilingual-entry-point + structured section layout from the spec. Sparse emoji.

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Replace README.md content**

Full new content:

```markdown
# CoursePulse AI

Turn sleepy lecture slides into a personal TA report.
上传 PDF，自动产出结构化讲义、术语百科、相关教学视频。

**[Live Demo](https://coursepulse-ai.railway.app)** · [English](README.en.md)

---

## 做什么

CoursePulse AI 把课件 PDF 转成一份结构化的学习报告：按主题分段、抽取考点与易错点、配套公式与示意图、并从 B 站挑出相关教学视频。面向课业重、错过直播的大学生。

## 功能状态

✅ PDF 解析 + 两阶段 LLM 讲义生成
✅ 语义向量 + B 站视频推荐
🚧 错题诊断 — Vision 识别错误并回链课件
🚧 考前复习报告 — 权重地图 + Cheat Sheet

## 架构

三层：Next.js 前端、FastAPI 后端、Postgres + pgvector 数据库。核心流水线是 6 步：解析 → 切片 → 向量化 → Pass-1 规划 → Pass-2 撰写 → 视频推荐。

可视化讲解：访问 [`/architecture`](https://coursepulse-ai.railway.app/architecture) 页。

## 5 分钟本地跑通

前置：Docker Desktop、一个 DeepSeek API key。

```bash
git clone https://github.com/CarterJia/Coursepulse-AI.git
cd coursepulse-ai
cp .env.example .env   # 编辑 .env 填入 DEEPSEEK_API_KEY
docker compose up
```

打开 http://localhost:3000 即可使用。

## Bring your own key

Live Demo 默认每个 IP 每天 3 次免费上传。想跑更多：在首页右下点 "Use my own API key"，填入自己的 DeepSeek API key 即可解锁无限次。

key 只存在你浏览器的 localStorage，不会写入我们的数据库或日志。

## 技术栈

- Next.js 15 / TypeScript / Tailwind / shadcn/ui
- FastAPI / SQLAlchemy / Alembic
- Postgres 16 / pgvector
- DeepSeek Chat / BAAI/bge-small-zh-v1.5
- Docker Compose / Railway

## 设计文档

所有设计 spec 在 [`docs/superpowers/specs/`](docs/superpowers/specs/)。入门建议从 [`2026-04-13-coursepulse-full-product-design.md`](docs/superpowers/specs/2026-04-13-coursepulse-full-product-design.md) 开始。

## License

MIT
```

- [ ] **Step 2: Verify links**

Render the README on GitHub (or via a Markdown preview) and click each link. The `/architecture` link and Live Demo URL will 404 until actually deployed — that's fine, they're meant for the final published state.

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "docs: rewrite README as the portfolio landing page"
```

---

## Task 14: README (English) + Deployment Guide

**Files:**
- Create: `README.en.md`
- Create: `docs/deployment.md`

- [ ] **Step 1: Create English README**

Full content of `README.en.md`:

```markdown
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
```

- [ ] **Step 2: Create deployment guide**

Full content of `docs/deployment.md`:

```markdown
# Railway Deployment Guide

This project is deployed on Railway as three services: `frontend`, `backend`, and a managed Postgres plugin.

## One-time setup

### 1. Provision Railway project

- Create a new Railway project.
- Add the **Postgres** plugin to the project. Railway will set `DATABASE_URL` automatically on the backend service once linked.

### 2. Backend service

- Deploy from the `backend/Dockerfile` in this repo (set the Root directory to `/`, Dockerfile path to `backend/Dockerfile`).
- Environment variables:
  - `DEEPSEEK_API_KEY` — your DeepSeek API key (used for default-quota requests)
  - `UPLOAD_QUOTA_PER_IP` — default `3`
  - `FILE_STORAGE_ROOT` — `/app/storage`
  - `SAMPLE_DOCUMENT_ID` — leave empty for now; populate after step 4

### 3. Frontend service

- Deploy from `frontend/Dockerfile`.
- Environment variables:
  - `NEXT_PUBLIC_API_BASE_URL` — the public URL of the backend service (e.g. `https://backend-production.up.railway.app`)

### 4. Populate the sample document

- Once both services are live, upload the sample PDF ONCE using your own API key so it bypasses quota:

```bash
curl -i -X POST \
  -H 'X-User-API-Key: YOUR_DEEPSEEK_KEY' \
  -F 'file=@path/to/sample.pdf' \
  https://backend-production.up.railway.app/api/documents/upload
```

- Copy the `document_id` from the response.
- Set `SAMPLE_DOCUMENT_ID` on the backend service to that UUID.
- Redeploy the backend. "Try the sample" on the homepage now routes to this document.

## Operational notes

- **Storage is ephemeral.** `scripts/cleanup_storage.sh` runs on container startup and deletes files older than 7 days from `storage/slides/`, `storage/assignments/`, and `storage/derived/`. This is intentional — the demo doesn't retain user uploads long term. Generated reports and glossary entries live in Postgres and persist across restarts.
- **Quota counter resets on restart.** The counter is in-memory. When the container is redeployed or restarted by Railway, all IPs get a fresh quota. Acceptable for a demo.
- **BYOK keys are never persisted.** They live only in the browser's localStorage and appear only on the single HTTP request they travel with. The backend never writes them to disk or logs.

## Costs

- Railway Hobby plan: $5/month (keeps containers warm, no cold start)
- DeepSeek API: estimated $5–30/month depending on traffic; capped by the per-IP quota
```

- [ ] **Step 3: Commit**

```bash
git add README.en.md docs/deployment.md
git commit -m "docs: English README and Railway deployment guide"
```

---

## Task 15: End-to-End Verification

A final smoke test to confirm nothing regressed and all pieces work together.

- [ ] **Step 1: Fresh rebuild**

```bash
cd "<repo root>"
docker compose down
docker compose up -d --build
docker compose logs -f backend
```

Wait for "Application startup complete" in logs. Confirm "[cleanup] Storage cleanup complete" also appears.

- [ ] **Step 2: Walk the full demo path**

1. Visit http://localhost:3000. Verify: Hero, 2×2 feature grid, "Try the sample" button (will show alert until SAMPLE_DOCUMENT_ID is set — expected locally).
2. Visit http://localhost:3000/architecture. Verify: 6 pipeline cards, 3 design decisions, stack card.
3. Go back to `/`, upload any small PDF. Verify: quota indicator updates from "Daily quota: 3 uploads" to "Today: 2/3 remaining".
4. Click "Use my own API key", save a dummy value. Upload again. Verify: indicator says "Using your API key · unlimited"; devtools Network tab shows `X-User-API-Key` header on the POST.
5. Open the resulting document page. Verify: topic cards look polished (thin gray border, larger titles), video cards (if any) render with uniform cover radius.
6. Exhaust quota locally by setting `UPLOAD_QUOTA_PER_IP=1` in `.env`, restarting backend, clearing localStorage, and uploading twice. Second upload returns 429 with a user-facing error.

- [ ] **Step 3: Run full backend test suite**

```bash
cd backend && pytest tests/ -v
```

Expected: all tests pass.

- [ ] **Step 4: Commit (if anything cosmetic changed during verification)**

If verification surfaced any small fixes, commit them with a clear message. Otherwise skip this step.

---

## Out-of-plan follow-ups (do NOT do as part of this plan)

- Railway deploy itself (requires account + push). The user will execute the steps in `docs/deployment.md` when ready.
- Custom domain configuration.
- Any Slice 2 hotfixes that are still uncommitted in the working tree at the time this plan starts (bilibili hardening, threshold, glossary fault tolerance, referrerPolicy) — those should be committed as a separate PR before or after this plan, not mixed in.
