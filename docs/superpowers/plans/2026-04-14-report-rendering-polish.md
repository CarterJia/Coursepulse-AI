# Report Rendering Polish Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix the four rendering issues surfaced in the Task-16 smoke test (invalid Mermaid, hallucinated images, inline enumerations, under-prominent formulas) using a two-layer defense (prompt constraint + runtime fallback/styling).

**Architecture:** Four independent, small changes — three in the backend (two prompt rule blocks + one regex-based image validator) and three in the frontend (Mermaid error fallback, block-math CSS, and their tests). Each fix pairs an upstream LLM-prompt rule with a downstream safety net so failures degrade gracefully.

**Tech Stack:** Python 3.11 / FastAPI / SQLAlchemy (backend), pytest, Next.js 15 / React 19 / Tailwind v4 (frontend), Jest + React Testing Library, KaTeX, Mermaid 11, regex.

**Spec:** `docs/superpowers/specs/2026-04-14-report-rendering-polish-design.md`

---

## File Structure

| File | Change | Responsibility |
|---|---|---|
| `backend/app/services/prompts.py` | Modify | Append three new rule blocks to `TOPIC_WRITE_PROMPT` (Mermaid / Image / List). |
| `backend/tests/test_prompts.py` | Modify | Assert the new rule strings appear in the prompt. |
| `backend/app/services/reporting.py` | Modify | Add `_strip_missing_images(body, document_id, derived_root)` helper; call it on every `section_type` body inside `run_report_pipeline` before `db.add(Report(...))`. |
| `backend/tests/test_reporting_image_validation.py` | Create | Unit tests for `_strip_missing_images` (keeps valid, drops missing file, drops wrong doc_id). |
| `backend/tests/test_run_report_pipeline.py` | Modify | Add one test that asserts broken image refs are stripped from report bodies end-to-end. |
| `frontend/components/markdown-renderer.tsx` | Modify | Replace `MermaidBlock` error handler: clear the div, set a muted italic class, and write `（图示加载失败）`. |
| `frontend/tests/markdown-renderer.test.tsx` | Modify | Add one test that mocks `mermaid.render` rejection and asserts the fallback text + class render. |
| `frontend/app/globals.css` | Modify | Append `.katex-display` and `.dark .katex-display` block rules after the existing `@import "katex/dist/katex.min.css"`. |

Scope stays inside already-existing files; only one new test file gets created. No schema changes, no new dependencies, no route changes.

---

## Task 1: Tighten `TOPIC_WRITE_PROMPT` with Mermaid / Image / List Rules

**Files:**
- Modify: `backend/app/services/prompts.py:61-106`
- Test: `backend/tests/test_prompts.py`

**Why TDD here:** The "test" is a structural assertion that specific rule strings made it into the prompt. That catches future drift (e.g. someone editing the prompt and dropping a rule silently) — exactly what tests are for.

- [ ] **Step 1: Read the current prompt**

Open `backend/app/services/prompts.py` and locate the `TOPIC_WRITE_PROMPT` string (lines 61-106). The last meaningful line before the final instruction is:

```
- 使用与原课件相同的语言
```

followed by a blank line and then:

```
**只输出上面格式定义的 Markdown, 不要加开场白或结语。**
```

The three new rule blocks go **between** those two — i.e. after the existing "格式规则" list and before the "只输出…" closer.

- [ ] **Step 2: Write the failing tests**

Open `backend/tests/test_prompts.py` and append:

```python
def test_topic_write_prompt_has_mermaid_strict_rules():
    # Strict Mermaid rules must be present so the LLM stops emitting
    # labels with parens/brackets that break the renderer.
    assert "Mermaid" in TOPIC_WRITE_PROMPT
    assert "graph LR" in TOPIC_WRITE_PROMPT or "graph TD" in TOPIC_WRITE_PROMPT
    assert '( ) [ ] { }' in TOPIC_WRITE_PROMPT
    assert '双引号' in TOPIC_WRITE_PROMPT


def test_topic_write_prompt_has_strict_image_rule():
    # Hard rule: only use paths from the provided list.
    assert "只使用" in TOPIC_WRITE_PROMPT
    assert "可用图片" in TOPIC_WRITE_PROMPT
    assert "不要编造" in TOPIC_WRITE_PROMPT


def test_topic_write_prompt_has_list_format_rule():
    # Forbid "1. xx 2. yy 3. zz" inline paragraphs.
    assert "1. 2. 3." in TOPIC_WRITE_PROMPT
    assert "- " in TOPIC_WRITE_PROMPT
    assert "不要在同一段" in TOPIC_WRITE_PROMPT
```

- [ ] **Step 3: Run the new tests to verify they fail**

Run: `cd backend && docker compose exec backend pytest tests/test_prompts.py -v`
Expected: three new tests FAIL (assertions fail — the strings aren't in the prompt yet).

- [ ] **Step 4: Add the three rule blocks to `TOPIC_WRITE_PROMPT`**

In `backend/app/services/prompts.py`, replace the existing `## 格式规则` section through the final instruction with:

```python
TOPIC_WRITE_PROMPT = """你正在为一份学习报告撰写**一个主题**的 Markdown 卡片。

## 主题元信息

- 标题: {topic_title}
- 涵盖页面: {source_pages}
- 可用图片: {image_paths_block}
- 已确定的核心要点: {key_points}
- 已确定的考点提示: {exam_tips}
- 已确定的易错点: {common_mistakes}

## 该主题相关的原始课件内容

{pages_block}

## 输出格式 (严格遵守)

```
### 主题: <标题>

> **💡 一句话：** <一句话抓住本质>

**展开：**

<2-5 段完整讲解, 把抽象变直觉>

(如需: **📐 关键公式：** $$<LaTeX>$$)
(如需: Markdown 表格对比)
(如需: 嵌入图片 ![](<图片路径>) — 仅使用上面"可用图片"里列出的路径)
(如需: ```mermaid 代码块 — 仅在上面没有合适图片时使用)

> **⚠️ 考点提示：** <根据已确定的 exam_tips 扩写>

> **🧠 易错点：** <根据已确定的 common_mistakes 扩写>
```

## 格式规则

- 数学公式: 行内用 $...$, 块级用 $$...$$
- 重点术语用 **加粗**
- 提示、警告用 > blockquote
- 尽量用直观类比帮助理解
- 使用与原课件相同的语言

## Mermaid 图示规则 (严格)

- 如要画图, 只使用 `graph LR` 或 `graph TD`。
- 节点标签**只允许**: ASCII 字母、数字、空格、汉字。
- 节点标签**不允许**出现: ( ) [ ] { } , ; : " ' / \\
- 如果标签需要符号或公式, 必须把整个标签用双引号包起来, 例如 `A["Q(s,a) 回传"] --> B["UCB1 选择"]`。
- 不确定能否画对时, 跳过 Mermaid, 改用上面提供的图片。

## 图片引用规则 (严格)

- 只使用"可用图片"里列出的路径, 一字不改。
- 不要编造、猜测或修改图片路径。
- 如果没有合适的图片, 就不要写任何图片引用, 直接用文字讲清楚。

## 列表格式规则

- 枚举≥2 个条目时, 必须用 Markdown 列表 (每条独占一行)。
- 有顺序/步骤用 `1. 2. 3.` (例如算法步骤)。
- 并列/无顺序用 `- ` (例如考点清单)。
- **不要**在同一段里写成 "1. xx 2. yy 3. zz"。
- **不要**使用 (1)、①、1) 这类内联编号。

**只输出上面格式定义的 Markdown, 不要加开场白或结语。**
"""
```

- [ ] **Step 5: Run tests to verify they now pass**

Run: `cd backend && docker compose exec backend pytest tests/test_prompts.py -v`
Expected: all prompt tests PASS (including the 3 existing ones + 3 new ones = 6 total).

- [ ] **Step 6: Commit**

```bash
git add backend/app/services/prompts.py backend/tests/test_prompts.py
git commit -m "feat(backend): tighten TOPIC_WRITE_PROMPT with Mermaid/image/list rules"
```

---

## Task 2: `_strip_missing_images` helper in `reporting.py`

**Files:**
- Modify: `backend/app/services/reporting.py:14-32` (imports) and `:164-223` (`run_report_pipeline`)
- Create: `backend/tests/test_reporting_image_validation.py`

This task is split into sub-tasks: first add the pure helper behind TDD, then wire it into the pipeline.

### Task 2a: Pure helper function

- [ ] **Step 1: Write the failing test file**

Create `backend/tests/test_reporting_image_validation.py`:

```python
import os

from app.services.reporting import _strip_missing_images


DOC_ID = "d6e5a8f4-0000-0000-0000-000000000001"


def _url(doc_id: str, filename: str) -> str:
    return f"/api/files/{doc_id}/{filename}"


def test_keeps_image_that_exists_on_disk(tmp_path):
    derived_dir = tmp_path / "derived" / DOC_ID
    derived_dir.mkdir(parents=True)
    (derived_dir / "page_3_img_0.png").write_bytes(b"\x89PNG")
    body = f"Look: ![caption]({_url(DOC_ID, 'page_3_img_0.png')}) end."

    result = _strip_missing_images(body, DOC_ID, str(tmp_path))

    assert result == body  # unchanged


def test_strips_image_whose_file_is_missing(tmp_path):
    (tmp_path / "derived" / DOC_ID).mkdir(parents=True)  # dir exists, file doesn't
    body = f"Before ![x]({_url(DOC_ID, 'page_7_img_0.png')}) after."

    result = _strip_missing_images(body, DOC_ID, str(tmp_path))

    assert "page_7_img_0.png" not in result
    assert "Before  after." in result  # image ref removed, surrounding text kept


def test_strips_image_referencing_a_different_document(tmp_path):
    other_doc = "00000000-0000-0000-0000-00000000aaaa"
    other_dir = tmp_path / "derived" / other_doc
    other_dir.mkdir(parents=True)
    (other_dir / "page_1_img_0.png").write_bytes(b"")
    body = f"Cross ![]({_url(other_doc, 'page_1_img_0.png')}) doc."

    result = _strip_missing_images(body, DOC_ID, str(tmp_path))

    # the file physically exists, but not under OUR doc_id → strip anyway
    assert "page_1_img_0.png" not in result


def test_passes_through_body_with_no_image_refs(tmp_path):
    body = "# 纯文字段落\n\n一些解释, 没有图片。"

    result = _strip_missing_images(body, DOC_ID, str(tmp_path))

    assert result == body


def test_handles_multiple_refs_independently(tmp_path):
    derived_dir = tmp_path / "derived" / DOC_ID
    derived_dir.mkdir(parents=True)
    (derived_dir / "real.png").write_bytes(b"")
    body = (
        f"A ![]({_url(DOC_ID, 'real.png')}) "
        f"B ![]({_url(DOC_ID, 'ghost.png')}) C"
    )

    result = _strip_missing_images(body, DOC_ID, str(tmp_path))

    assert "real.png" in result
    assert "ghost.png" not in result
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && docker compose exec backend pytest tests/test_reporting_image_validation.py -v`
Expected: all 5 tests FAIL with `ImportError: cannot import name '_strip_missing_images'`.

- [ ] **Step 3: Add the helper to `reporting.py`**

In `backend/app/services/reporting.py`, add these imports at the top (after the existing `import logging`):

```python
import os
import re
```

Then, immediately after the `MAX_PASS2_WORKERS = 4` constant (around line 34), add:

```python
_IMG_PATTERN = re.compile(r"!\[([^\]]*)\]\(/api/files/([^/]+)/([^)]+)\)")


def _strip_missing_images(body: str, document_id: str, derived_root: str) -> str:
    """Remove markdown image refs whose files don't exist under derived_root.

    Hallucinated-path defense: the LLM sometimes references image files it
    imagines (e.g. ``page_7_img_0.png``) that PyMuPDF never extracted.
    Rather than showing a broken-image placeholder, we strip the entire
    ``![](...)`` ref before insert. Refs that exist pass through unchanged.
    """

    def replace(match: "re.Match[str]") -> str:
        ref_doc_id, filename = match.group(2), match.group(3)
        if ref_doc_id != document_id:
            return ""  # wrong doc id → hallucinated
        full_path = os.path.join(derived_root, "derived", ref_doc_id, filename)
        if not os.path.isfile(full_path):
            return ""  # file not on disk → hallucinated
        return match.group(0)

    return _IMG_PATTERN.sub(replace, body)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && docker compose exec backend pytest tests/test_reporting_image_validation.py -v`
Expected: all 5 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/reporting.py backend/tests/test_reporting_image_validation.py
git commit -m "feat(backend): add _strip_missing_images helper with regex-based scrub"
```

### Task 2b: Wire helper into `run_report_pipeline`

- [ ] **Step 1: Write the failing integration test**

Open `backend/tests/test_run_report_pipeline.py` and append (at the end of the file):

```python
def test_run_report_pipeline_strips_hallucinated_image_refs(tmp_path, monkeypatch):
    """The pipeline must scrub image refs to files that don't exist on disk."""
    from app.core import config
    from app.services.reporting import run_report_pipeline

    monkeypatch.setattr(config.settings, "file_storage_root", str(tmp_path))

    document_id = uuid.uuid4()
    # Create derived dir with ONE real file, so one ref should survive.
    derived_dir = tmp_path / "derived" / str(document_id)
    derived_dir.mkdir(parents=True)
    (derived_dir / "real.png").write_bytes(b"")

    real_url = f"/api/files/{document_id}/real.png"
    ghost_url = f"/api/files/{document_id}/ghost.png"
    topic_bodies = [
        f"card A with ![]({real_url}) and ![]({ghost_url})",
        f"card B with only ![]({ghost_url})",
    ]

    with patch("app.services.reporting.generate_all_topic_cards", return_value=topic_bodies), \
         patch("app.services.reporting.generate_plan", return_value=PLAN):
        db = MagicMock()
        added: list = []
        db.add.side_effect = lambda obj: added.append(obj)

        run_report_pipeline(db, document_id, PAGES, image_manifest={})

    topic_rows = [r for r in added if r.section_type == "topic"]
    all_bodies = "\n".join(r.body for r in topic_rows)
    assert "real.png" in all_bodies  # real ref kept
    assert "ghost.png" not in all_bodies  # hallucinated refs stripped
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && docker compose exec backend pytest tests/test_run_report_pipeline.py::test_run_report_pipeline_strips_hallucinated_image_refs -v`
Expected: FAIL — `ghost.png` still appears in the written bodies because scrubbing isn't wired yet.

- [ ] **Step 3: Wire `_strip_missing_images` into the pipeline**

In `backend/app/services/reporting.py`, modify `run_report_pipeline` (around lines 164-223). Import `settings` at the top of the file (alongside the existing imports):

```python
from app.core.config import settings
```

Then rewrite the "Write rows" block of `run_report_pipeline` to funnel every body through the scrubber. The function body becomes:

```python
def run_report_pipeline(
    db: Session,
    document_id: _uuid.UUID,
    pages: list[dict],
    image_manifest: dict[int, list[str]],
) -> None:
    """Two-pass pipeline: Pass-1 plan -> Pass-2 topic cards -> write all rows to `reports`.

    Caller commits. On Pass-1 total failure, falls back to page-based plan.
    Every section body is scrubbed of hallucinated image refs before insert.
    """
    # Pass 1
    try:
        plan = generate_plan(pages, image_manifest, max_retries=5)
        logger.info("Pass-1 plan generated for document %s", document_id)
    except PlanValidationError as e:
        logger.warning("Pass-1 failed for %s (%s); using fallback plan", document_id, e)
        plan = build_fallback_plan(pages)

    # Pass 2 (concurrent)
    topic_cards = generate_all_topic_cards(
        plan["topics"], pages, image_manifest, document_id=str(document_id)
    )

    doc_id_str = str(document_id)
    derived_root = settings.file_storage_root

    def _clean(body: str) -> str:
        return _strip_missing_images(body, doc_id_str, derived_root)

    # Write rows
    db.add(Report(
        id=_uuid.uuid4(),
        document_id=document_id,
        title="课件概览",
        body=_clean(plan["overview"]),
        section_type="overview",
    ))
    db.add(Report(
        id=_uuid.uuid4(),
        document_id=document_id,
        title="核心要点速览",
        body=_clean(_render_tldr_body(plan["tldr"])),
        section_type="tldr",
    ))
    for topic, card_body in zip(plan["topics"], topic_cards):
        db.add(Report(
            id=_uuid.uuid4(),
            document_id=document_id,
            title=topic["title"],
            body=_clean(card_body),
            section_type="topic",
        ))
    db.add(Report(
        id=_uuid.uuid4(),
        document_id=document_id,
        title="考点与易错点汇总",
        body=_clean(_render_exam_summary_body(plan["exam_summary"])),
        section_type="exam_summary",
    ))
    db.add(Report(
        id=_uuid.uuid4(),
        document_id=document_id,
        title="30 分钟急救包",
        body=_clean(_render_quick_review_body(plan["quick_review"])),
        section_type="quick_review",
    ))
```

- [ ] **Step 4: Run the full reporting test suite**

Run: `cd backend && docker compose exec backend pytest tests/test_run_report_pipeline.py tests/test_reporting_image_validation.py -v`
Expected: all tests PASS (the 2 existing pipeline tests + 1 new one + 5 helper tests = 8 total).

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/reporting.py backend/tests/test_run_report_pipeline.py
git commit -m "feat(backend): scrub hallucinated image refs in run_report_pipeline"
```

---

## Task 3: Frontend Mermaid fallback message

**Files:**
- Modify: `frontend/components/markdown-renderer.tsx:22-41` (`MermaidBlock` component)
- Test: `frontend/tests/markdown-renderer.test.tsx`

- [ ] **Step 1: Write the failing test**

Open `frontend/tests/markdown-renderer.test.tsx`. The existing tests already import `MarkdownRenderer` and render Mermaid blocks, so we can reuse that setup. Add **above** the existing tests, right below the `import` block, a `jest.mock` stub for mermaid that lets individual tests override `.render`:

```tsx
jest.mock("mermaid", () => ({
  __esModule: true,
  default: {
    initialize: jest.fn(),
    render: jest.fn(() => Promise.resolve({ svg: "<svg></svg>" })),
  },
}));

// eslint-disable-next-line @typescript-eslint/no-require-imports
const mermaid = require("mermaid").default as { render: jest.Mock };
```

Then append a new test at the end of the file:

```tsx
test("renders muted fallback when Mermaid render fails", async () => {
  mermaid.render.mockRejectedValueOnce(new Error("syntax boom"));
  const md = "```mermaid\nthis is not valid mermaid syntax\n```";

  const { container } = render(<MarkdownRenderer content={md} />);

  // Wait for the effect to flush the rejected promise.
  await screen.findByText("（图示加载失败）");

  const fallback = container.querySelector(".mermaid-fallback");
  expect(fallback).not.toBeNull();
  expect(fallback?.textContent).toBe("（图示加载失败）");
  expect(fallback?.className).toContain("italic");
});
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd frontend && docker compose exec frontend npm test -- markdown-renderer.test.tsx`
Expected: new test FAILS — existing `.catch` writes `<pre>Mermaid error: …</pre>`, no `.mermaid-fallback` element.

The other Mermaid test (`renders Mermaid code block as a div with mermaid class`) should still pass because the default `render` mock resolves with a stub svg.

- [ ] **Step 3: Rewrite the `MermaidBlock` error handler**

In `frontend/components/markdown-renderer.tsx`, replace the `.catch(...)` block (lines 34-36) so the whole `MermaidBlock` component becomes:

```tsx
function MermaidBlock({ code }: { code: string }) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    ensureMermaidInitialized();
    if (ref.current) {
      const id = `mermaid-${Math.random().toString(36).slice(2)}`;
      mermaid
        .render(id, code)
        .then(({ svg }) => {
          if (ref.current) ref.current.innerHTML = svg;
        })
        .catch(() => {
          if (ref.current) {
            ref.current.innerHTML = "";
            ref.current.className =
              "mermaid-fallback text-xs text-muted-foreground italic my-2";
            ref.current.textContent = "（图示加载失败）";
          }
        });
    }
  }, [code]);

  return <div ref={ref} className="mermaid-block my-4" />;
}
```

Notes:
- We drop the error details from the UI on purpose — they're noise to the student and `mermaid.render` already logs to the console.
- Overwriting `className` is intentional: we want `.mermaid-block my-4` replaced so styling is only "fallback", not both.

- [ ] **Step 4: Run frontend tests**

Run: `cd frontend && docker compose exec frontend npm test -- markdown-renderer.test.tsx`
Expected: all tests PASS (5 existing + 1 new = 6 total). The pre-existing "renders Mermaid code block as a div with mermaid class" must still pass.

- [ ] **Step 5: Commit**

```bash
git add frontend/components/markdown-renderer.tsx frontend/tests/markdown-renderer.test.tsx
git commit -m "feat(frontend): muted fallback on Mermaid render failure"
```

---

## Task 4: Prominent styling for block-math (`.katex-display`)

**Files:**
- Modify: `frontend/app/globals.css:1-2` (adjacent to the existing KaTeX import)

No automated test — visual only. We'll cover it manually in Task 5.

- [ ] **Step 1: Append the rules**

Open `frontend/app/globals.css`. After the closing `}` of the `.dark { ... }` block (the one ending around line 75), before the `@layer base` block, insert:

```css
/* Block-math emphasis: $$...$$ blocks get a card-like amber frame so key
   formulas (e.g. UCT, PUCT) stand out from body text. Inline .katex is
   untouched by design. */
.katex-display {
  font-size: 1.4em;
  padding: 1rem 1.5rem;
  margin: 1rem 0;
  border-left: 4px solid #f59e0b;   /* amber-500 */
  border-radius: 0.375rem;
  background: #fffbeb;               /* amber-50 */
  overflow-x: auto;
}

.dark .katex-display {
  background: rgba(251, 191, 36, 0.08);
  border-left-color: #fbbf24;        /* amber-400 */
}
```

- [ ] **Step 2: Verify the frontend still compiles**

Run: `cd frontend && docker compose exec frontend npm run build`
Expected: build succeeds. (If Next's CSS pipeline rejects the file, the error surfaces here rather than in the browser.)

If the build was too slow to run locally, the alternative is:

Run: `cd frontend && docker compose exec frontend npx next lint`
Expected: no new errors.

- [ ] **Step 3: Commit**

```bash
git add frontend/app/globals.css
git commit -m "style(frontend): prominent amber frame for KaTeX block math"
```

---

## Task 5: Manual smoke test (re-verifies Task 16)

This task has no code changes. It re-runs the original smoke test against the fixed pipeline.

- [ ] **Step 1: Rebuild backend + frontend containers**

Run: `docker compose build backend frontend && docker compose up -d`
Expected: both containers come up healthy (`docker compose ps`).

- [ ] **Step 2: Wipe the prior test document**

This is a destructive DB op; before running, confirm the test doc is the only one (or the user confirms wiping is OK).

Run: `docker compose exec db psql -U coursepulse -d coursepulse -c "DELETE FROM documents WHERE filename LIKE 'Lecture17%';"`
Expected: `DELETE N` where N ≥ 1. Cascades will drop pages, chunks, embeddings, reports, glossary entries.

Then delete the derived images directory for that doc:

Run: `docker compose exec backend sh -c 'rm -rf /app/storage/derived/*'`
Expected: no output.

- [ ] **Step 3: Re-upload the test PDF**

Via the browser at http://localhost:3000, upload `Lecture17_MCTS.pdf`. Wait for ingestion to complete (check `/api/jobs` or the UI progress indicator).

- [ ] **Step 4: Open the document detail page and verify each fix**

Open the document detail page and step through every topic card. Confirm:

- [ ] No red "Syntax error in text / mermaid version 11.14.0" bomb graphics anywhere. Any Mermaid block that fails now shows small muted italic `（图示加载失败）` instead.
- [ ] No broken-image `?` placeholders. If the LLM wrote a bad path, its `![](...)` is gone entirely — the surrounding prose reads naturally.
- [ ] Enumerations (e.g. MCTS 四步, AlphaGo 的 rollout 流程) render as proper numbered or bulleted lists, not inline `"1. xx 2. yy 3. zz"` paragraphs.
- [ ] Block formulas (UCT, PUCT) render large (≈1.4× body text) with an amber left border and light amber background. Inline `$x$` keeps its body-text size.

- [ ] **Step 5: Record results**

If all four checks pass, mark the plan done.

If any check fails, do NOT edit the plan from inside this task. Instead, capture a screenshot + repro steps and circle back to the implementer for the failing fix. Re-run Task 5 after the follow-up lands.

---

## Self-Review Notes

**Spec coverage:**

| Spec section | Covered by task |
|---|---|
| §3 4-issue summary | Tasks 1–4 |
| §4.1 Prompt additions | Task 1 |
| §4.2 Backend image validation | Task 2a + 2b |
| §4.3 Frontend Mermaid fallback | Task 3 |
| §4.4 Frontend formula styling | Task 4 |
| §5 No data-model changes | n/a (confirmed — no migration tasks) |
| §6.1 Backend tests (3 cases) | Task 2a (5 cases, superset) |
| §6.2 Frontend fallback test | Task 3 |
| §6.3 No CSS automated test | Task 4 Step 2 = build-compile check, Task 5 = visual |
| §6.4 Manual smoke test | Task 5 |
| §7 File-change summary | Matches File Structure above |

No spec requirement is unclaimed.

**Placeholder scan:** No TBDs, no "implement later", no "similar to Task N", no unreferenced function names. Test code is concrete; CSS block is complete; prompt block is the full replacement.

**Type consistency:** Python helper signature `_strip_missing_images(body: str, document_id: str, derived_root: str) -> str` is used identically in the helper test (via call) and in the wiring (`_clean` closure). Frontend assertion `.mermaid-fallback` matches the class set in `MermaidBlock`. CSS selector `.katex-display` is KaTeX's standard auto-applied class — no app-side alias required.

---

**Plan complete and saved to `docs/superpowers/plans/2026-04-14-report-rendering-polish.md`. Two execution options:**

1. **Subagent-Driven (recommended)** — I dispatch a fresh subagent per task, review between tasks, fast iteration.
2. **Inline Execution** — Execute tasks in this session using executing-plans, batch execution with checkpoints.

Which approach?
