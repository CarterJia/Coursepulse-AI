# CoursePulse Report Generation Redesign

**Date:** 2026-04-14
**Status:** Design approved, pending implementation plan
**Supersedes:** Report generation portion of `2026-04-13-coursepulse-full-product-design.md` (Slice 1)

---

## 1. Goal

Replace the current "per-4-page independent chapter" report format with a single **study-report-style** document that a student can read instead of the slides to prepare for an exam. The report is semantically structured (not page-mechanical), visually polished (LaTeX, diagrams, typography), and coherent end-to-end.

---

## 2. Non-goals

- Cross-lecture linking (e.g. "this lecture's position in the full course"). Requires a course syllabus, deferred to a later slice.
- Automatic test-question generation. Deferred.
- Re-rendering old reports generated under the current pipeline. They will be replaced on next upload.

---

## 3. Output Structure

Every PDF produces one logical report with these sections:

```
📍 课件概览          (overview)         — 2-3 段 TL;DR 描述全文主题与主线
🎯 核心要点速览       (tldr)             — 5-10 条 bullet, 考前 1 分钟刷
📖 知识点深度展开     (N × topic cards)  — 主体, 折叠 accordion
⚠️ 考点与易错点汇总   (exam_summary)     — 必考清单 + 易错点清单
⭐ 30 分钟急救包      (quick_review)     — 时间紧时读哪 3 件事
📚 术语表             (glossary)         — 已有, 侧边栏展示, 不变
```

### 3.1 Per-Topic Card Template

Each entry in `知识点深度展开` follows this internal structure:

```markdown
### 主题 N: <LLM-generated title>

> **💡 一句话：** <one-sentence essence>

**展开：**

<2-5 段完整讲解, 使用 LaTeX 公式, 嵌入图片/Mermaid, 加粗重点>

**📐 关键公式：**
$$<LaTeX block>$$

| 对比列 1 | 对比列 2 |
|---------|---------|
| ...     | ...     |

> **⚠️ 考点提示：** <LLM 根据启发式判断的考点>

> **🧠 易错点：** <LLM 标注的典型易错点>
```

### 3.2 Visual Elements

- **Bold** for emphasis on key terms
- LaTeX via `$...$` (inline) and `$$...$$` (block)
- Tables for comparisons and equivalence lists
- Blockquotes for tips/warnings/key points
- Emoji section markers (💡📐⚠️🧠🔥💣⭐) as visual anchors
- Diagrams: **prefer extracted images from original PDF**; fall back to Mermaid when no suitable original image exists

---

## 4. Generation Pipeline (Two-pass)

```
PDF
 │
 ├─(a)─> 解析文本 (PyMuPDF, existing)           ──> document_pages 表
 │
 ├─(b)─> 抽取嵌入图片 (PyMuPDF, NEW)             ──> storage/derived/<doc_id>/page_<n>_img_<k>.png
 │
 ├─(c)─> 切片 + embedding (existing, unchanged) ──> knowledge_chunks + embeddings
 │
 ├─(d)─> Pass 1: 全局规划 (1 × DeepSeek call)
 │         输入: 全文文本 (带页号) + 每页图片清单
 │         输出: JSON plan { overview, tldr, topics[], exam_summary, quick_review }
 │         失败处理: JSON mode + 5 次带反馈重试 + fallback
 │
 ├─(e)─> Pass 2: 每主题细写 (N × DeepSeek calls, 并发)
 │         输入: topic 标题 + 相关页文本 + 图片路径 + Pass 1 的 key_points/exam_tips
 │         输出: 该主题的完整 Markdown 卡片
 │
 ├─(f)─> 拼装 & 落库:
 │         - overview      → reports 表一行 (section_type='overview')
 │         - tldr          → reports 表一行 (section_type='tldr')
 │         - 每个 topic    → reports 表一行 (section_type='topic')
 │         - exam_summary  → reports 表一行 (section_type='exam_summary')
 │         - quick_review  → reports 表一行 (section_type='quick_review')
 │
 └─(g)─> 术语提取 (existing glossary pipeline, unchanged)
```

### 4.1 Pass 1 Prompt Outline (`REPORT_PLAN_PROMPT`)

```
You are an expert teaching assistant creating an exam-focused study report.

Read the entire course material below and produce a JSON plan.

## Course material
[PAGE 1]
<text of page 1>
[IMAGES ON PAGE 1]: 2 images available (ids: page_1_img_0, page_1_img_1)

[PAGE 2]
...

## Your task

Analyze the content and output a JSON object with this exact structure:

{
  "overview": "2-3 段中文, 说明本课件讲什么、主线是什么",
  "tldr": ["要点 1", "要点 2", ...],        // 5-10 条, 考前速览
  "topics": [
    {
      "title": "主题名 (语义化, 不要叫 'Pages 1-4')",
      "source_pages": [3, 4, 5],              // 该主题覆盖的页面
      "uses_images_from_pages": [4],          // 该主题相关的图片所在页, 可空
      "key_points": ["..."],                  // 该主题的核心要点
      "exam_tips": ["..."],                   // 考点提示
      "common_mistakes": ["..."]              // 易错点
    },
    ...
  ],
  "exam_summary": {
    "must_know": ["..."],                     // 必考清单
    "common_pitfalls": ["..."]                // 整体易错
  },
  "quick_review": ["..."]                     // 30 分钟急救包: 3-5 件事
}

## Heuristics for 考点/易错点
- 出现 "重点" / "考试" / "Example" / "注意" 等标记的内容
- 所有公式、定义、证明
- 反复出现的术语
- Slide 标题层级高的条目
- 作业题原题出现过的内容

Use Chinese. Match the language of the slides.
```

**Response format:** `response_format={"type": "json_object"}` is enabled.

### 4.2 Pass 2 Prompt Outline (`TOPIC_WRITE_PROMPT`)

```
You are writing one topic card in a study report.

## Topic
Title: <topic.title>
Source pages: <topic.source_pages>
Available images for this topic: [<list of image paths or "none">]
Pre-identified key points: <topic.key_points>
Pre-identified exam tips: <topic.exam_tips>
Pre-identified common mistakes: <topic.common_mistakes>

## Source material (verbatim from slides)
[PAGE <n>]
<text>
...

## Instructions

Write a Markdown topic card in the following structure:

### 主题: <title>

> **💡 一句话：** <one sentence>

**展开：**
<full explanation>

(optional: **📐 关键公式：** $$...$$)
(optional: table, image ![](<path>), or ```mermaid ... ```)

> **⚠️ 考点提示：** <...>

> **🧠 易错点：** <...>

## Image usage rules
- Prefer referencing images from `uses_images_from_pages` with `![](<image_path>)`.
- If no suitable image exists but a diagram would help, output a Mermaid code block.
- Do not fabricate image paths.

## Formatting rules
- LaTeX: `$...$` for inline math, `$$...$$` for blocks.
- Bold **key terms**. Use blockquotes for tips.
- Keep explanations intuitive — add real-world analogies where useful.
- Write in the same language as the source pages.
```

### 4.3 Retry & Fallback Logic

```python
MAX_RETRIES = 5

def generate_plan(pdf_text, image_manifest):
    last_error = None
    last_response = None
    for attempt in range(MAX_RETRIES):
        prompt = build_plan_prompt(pdf_text, image_manifest, last_response, last_error)
        response = call_deepseek(prompt, json_mode=True)
        try:
            plan = json.loads(response)
            validate_schema(plan)
            return plan
        except (JSONDecodeError, ValidationError) as e:
            last_error = str(e)
            last_response = response
            continue
    # all retries exhausted
    return fallback_page_based_plan(pdf_text)
```

**Fallback plan** simply groups every 4 consecutive pages into one `topic`, uses "Pages X-Y" as the title, empty `exam_tips` / `common_mistakes`, and generates a simple `overview` from the first page. Users always get a functional report.

### 4.4 Pass 2 Concurrency

Pass 2 calls (one per topic) are dispatched concurrently via `concurrent.futures.ThreadPoolExecutor` (the DeepSeek/OpenAI SDK is sync, so threads are simpler than asyncio here). Max 4 workers (configurable). Typical document has 4-6 topics, so concurrency cuts total latency roughly to "slowest topic" instead of "sum of all topics".

---

## 5. Data Model Changes

### 5.1 New column on `reports` table

```sql
ALTER TABLE reports ADD COLUMN section_type VARCHAR(32) NOT NULL DEFAULT 'topic';
```

Allowed values:
- `overview` — top-of-page summary
- `tldr` — bullet-point key takeaways
- `topic` — one per subject, renders as accordion
- `exam_summary` — consolidated must-know + pitfalls
- `quick_review` — 30-min cram list

Existing rows in the dev DB (from old pipeline) get `'topic'` by default but will render incorrectly with the new frontend (they lack the new card structure). Since the app is single-user local, we accept this: user can clear the dev DB before first new-pipeline upload, or ignore stale documents. Alembic migration: `0003_add_reports_section_type.py`.

### 5.2 No change to other tables

`document_pages`, `knowledge_chunks`, `embeddings`, `glossary_entries`, `jobs`, `courses`, `documents` remain unchanged.

### 5.3 Image storage

New directory convention: `storage/derived/<document_id>/page_<n>_img_<k>.<ext>`
- `<n>` is 1-indexed page number
- `<k>` is 0-indexed image index within the page
- Extension matches source (PNG, JPEG, etc.)

No new DB table for images — filesystem is source of truth; LLM references images by relative path.

---

## 6. New Backend Components

| File | Purpose |
|------|---------|
| `app/services/image_extraction.py` (new) | Extract embedded images from PDF using PyMuPDF; write to `storage/derived/`; return manifest |
| `app/services/reporting.py` (rewrite) | Two-pass orchestration: `generate_plan()` + `generate_topic_card()` + assembly |
| `app/services/prompts.py` (rewrite) | `REPORT_PLAN_PROMPT`, `TOPIC_WRITE_PROMPT`, error-feedback prompt builders |
| `app/services/ingestion.py` (modify) | Replace `generate_chapter_report` loop with two-pass call |
| `app/api/routes/files.py` (new) | `GET /api/files/{document_id}/{filename}` — serves images from `storage/derived/` with content-type detection |
| `app/main.py` (modify) | Register `files` router |
| `alembic/versions/0003_add_reports_section_type.py` (new) | Migration adding `section_type` column |

### 6.1 File-serving route security

`GET /api/files/{document_id}/{filename}`:
- Validate `document_id` is a valid UUID
- Reject `filename` containing `..`, `/`, or `\`
- Only serve files from `storage/derived/<document_id>/`
- Return 404 if not found

---

## 7. Frontend Changes

### 7.1 New dependencies

```
react-markdown
remark-gfm
remark-math
rehype-katex
katex  (CSS)
mermaid
```

### 7.2 Component changes

| Component | Change |
|-----------|--------|
| `report-viewer.tsx` (rewrite) | Three-zone layout: top (overview + tldr), middle (topic accordion), bottom (exam_summary + quick_review) |
| `topic-card.tsx` (new) | Renders a single `section_type='topic'` row with full Markdown pipeline |
| `report-summary.tsx` (new) | Renders overview / tldr / exam_summary / quick_review blocks |
| `markdown-renderer.tsx` (new) | Shared `react-markdown` + KaTeX + Mermaid component — used by all report sections |
| `app/documents/[id]/page.tsx` (modify) | Pass full `reports[]` list (with section_type) to `report-viewer` |

### 7.3 Mermaid rendering approach

Use a `<pre><code class="language-mermaid">...</code></pre>` to Mermaid SVG transformer inside `markdown-renderer.tsx`. Initialize Mermaid once with `mermaid.initialize({ startOnLoad: false })` and call `mermaid.run()` after render.

### 7.4 API response changes

`GET /api/documents/{id}` response `reports` array now includes `section_type`:

```json
{
  "reports": [
    {"id": "...", "section_type": "overview", "title": "课件概览", "body": "..."},
    {"id": "...", "section_type": "tldr", "title": "核心要点速览", "body": "..."},
    {"id": "...", "section_type": "topic", "title": "矩阵乘法的几何意义", "body": "..."},
    ...
  ]
}
```

`DocumentDetailResponse` / `ReportSummary` schemas get a new `section_type: str` field.

---

## 8. Testing

### 8.1 Backend

- **Unit: prompt builders** — verify placeholders fill correctly, error-feedback prompt includes prior response & error.
- **Unit: plan validator** — accept valid JSON, reject missing `topics`, reject `source_pages` containing non-ints, etc.
- **Unit: image extraction** — test on fixture PDF with 1 known embedded image; verify output file exists and has correct name.
- **Unit: file-serving route** — verify path traversal rejection, 404 on missing file, correct content-type.
- **Integration (mocked LLM): two-pass pipeline** — mock DeepSeek to return a known plan JSON + known topic markdowns; verify `reports` rows are inserted with correct `section_type`.
- **Integration: retry logic** — mock DeepSeek to return invalid JSON twice, then valid; verify correct plan is produced; separately verify fallback fires after 5 failures.

### 8.2 Frontend

- **Component: topic-card** — renders a fixture body containing LaTeX, Mermaid, image reference, and blockquotes; assert DOM has expected nodes.
- **Component: report-viewer** — given mixed-`section_type` reports array, assert overview appears at top, topics in accordion, exam_summary at bottom.
- **Markdown renderer** — smoke test that `$x^2$` renders KaTeX element; `graph LR` inside `mermaid` block produces an SVG.

---

## 9. Rollout

This is a destructive redesign. Since the product is single-user / local-first, we won't migrate old rows: each new PDF upload creates a new `documents` row and its own set of new-format `reports` rows, so old stale data simply coexists. Recommend clearing dev DB before first new-pipeline upload for a clean demo.

---

## 10. Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Pass 1 JSON consistently malformed | JSON mode + 5 retries with error feedback + page-based fallback |
| LLM assigns images to wrong topics | Observe first few runs; if bad, add validation that referenced images exist in `uses_images_from_pages` |
| Pass 2 concurrency overwhelms DeepSeek rate limit | Cap concurrent calls to 4 (configurable); add exponential backoff on rate-limit responses |
| Very long PDFs exceed Pass 1 context | For MVP, cap at ~100 pages (log + error if exceeded); a future slice can chunk Pass 1 |
| Mermaid/KaTeX bundle bloat | Only load on report pages; lazy-import via `next/dynamic` |
| Path traversal via filename in file route | Strict validation (reject `..`, `/`, `\`); resolved path must stay inside `storage/derived/<doc_id>/` |
| Image extraction fails on unusual PDFs | Catch exceptions; log; continue pipeline with empty image manifest (report degrades gracefully) |

---

## 11. Open / Deferred

- Cross-lecture linking (needs syllabus input)
- Automatic difficulty calibration ("this topic is harder than avg — spend more time")
- User-uploaded annotations ("教授说这章不考")
- Image *description* via vision model (currently images are referenced but LLM can't "see" them — we tell it where they are, not what they show)

---

**Design approved:** 2026-04-14 by user. Pending implementation plan (next skill invocation).
