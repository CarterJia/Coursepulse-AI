# Report Rendering Polish Design

**Date:** 2026-04-14
**Status:** Design approved, pending implementation plan
**Related:** Follow-up to `2026-04-14-coursepulse-report-redesign-design.md` (addresses rendering issues surfaced during Task 16 smoke test)

---

## 1. Goal

Fix four concrete rendering / formatting issues that surfaced when the first real PDF (`Lecture17_MCTS.pdf`, 108 pages) went through the new two-pass report pipeline:

1. **Mermaid syntax errors** — LLM-generated Mermaid blocks fail to parse, rendering multiple prominent "Syntax error in text / mermaid version 11.14.0" bomb graphics.
2. **Hallucinated image paths** — LLM references image files (e.g. `page_7_img_0.png`) that were never extracted, causing broken-image `?` placeholders in the rendered report.
3. **Inline numbered enumerations** — LLM writes `"1. xx 2. yy 3. zz"` inside a single paragraph instead of using Markdown list syntax, producing dense unreadable prose.
4. **LaTeX block formulas lack visual prominence** — Block math renders at body-text size with no containing frame, so important formulas (e.g. the UCT and AlphaGo PUCT equations) fail to stand out.

Every fix uses a two-layer defense: **upstream prompt constraints** to lower failure rate, **downstream fallback / styling** to handle the rest.

---

## 2. Non-goals

- Regenerating existing reports in the DB. The one test document will be cleared and re-ingested as part of smoke verification.
- Adding new Mermaid features. We keep Mermaid as-is structurally; we just tighten what the LLM emits and hide failures gracefully.
- Migrating to a different LaTeX renderer. KaTeX stays; only its display-block CSS changes.
- Building a fallback for `$...$` inline math. Only `$$...$$` display blocks get the new styling.

---

## 3. Solution Overview

| Issue | Upstream (prompt) | Downstream (runtime) |
|---|---|---|
| Mermaid errors | Strict label/syntax rules in `TOPIC_WRITE_PROMPT` | `MermaidBlock` catches render errors, shows `（图示加载失败）` in small italic muted text |
| Image hallucination | Strict "only use listed paths" rule in `TOPIC_WRITE_PROMPT` | `_strip_missing_images()` scans every topic body before DB insert, deletes refs to nonexistent files |
| Inline enumerations | List-format rules in `TOPIC_WRITE_PROMPT` (use `1.` for sequential, `-` for parallel, never inline) | — |
| Formula prominence | — | CSS rule on `.katex-display`: 1.4em font, amber left border, light amber background |

---

## 4. Detailed Design

### 4.1 Prompt additions (`TOPIC_WRITE_PROMPT`)

Append three new rule blocks inside the existing instructions section. These sit alongside the current "Image usage rules" and "Formatting rules" already in the prompt. The exact text:

```
## Mermaid diagram rules (strict)
- If a Mermaid block is beneficial, use `graph LR` or `graph TD`.
- Node labels MUST only contain: ASCII letters, digits, spaces, Chinese characters.
- Node labels MUST NOT contain any of: ( ) [ ] { } , ; : " ' / \
- If a label needs symbols or formulas, wrap the entire label in double quotes,
  e.g. A["Q(s,a) 回传"] --> B["UCB1 选择"].
- When in doubt, skip Mermaid and rely on extracted images instead.

## Image reference rules (strict)
- ONLY use image paths from the "Available images for this topic" list.
- NEVER invent, guess, or modify image paths.
- If no suitable image is available, DO NOT include any image reference — just write prose.

## List formatting rules
- When enumerating ≥2 items, use proper Markdown list syntax (one item per line).
- Use `1. 2. 3.` for ordered / sequential content (e.g. 算法步骤).
- Use `-` for parallel / non-sequential items (e.g. 考点清单).
- NEVER inline multiple items in one paragraph such as "1. xx 2. yy 3. zz".
- NEVER use inline markers such as (1), ①, or 1).
```

The existing "Image usage rules" block remains but becomes secondary to the new strict block; wording is reconciled so they don't contradict each other — the strict rule is authoritative.

### 4.2 Backend image validation

New helper in `backend/app/services/reporting.py`:

```python
import os
import re

_IMG_PATTERN = re.compile(r"!\[([^\]]*)\]\(/api/files/([^/]+)/([^)]+)\)")


def _strip_missing_images(body: str, document_id: str, derived_root: str) -> str:
    """Remove markdown image refs whose files don't exist on disk."""
    def replace(match: re.Match[str]) -> str:
        ref_doc_id, filename = match.group(2), match.group(3)
        if ref_doc_id != document_id:
            return ""  # wrong doc id → hallucinated
        full_path = os.path.join(derived_root, "derived", ref_doc_id, filename)
        if not os.path.isfile(full_path):
            return ""  # file missing → hallucinated
        return match.group(0)
    return _IMG_PATTERN.sub(replace, body)
```

Wired into `run_report_pipeline` just before each `db.add(Report(...))` for `section_type="topic"`:

```python
from app.core.config import settings
derived_root = settings.file_storage_root

for topic_body in topic_bodies:
    cleaned = _strip_missing_images(topic_body, str(document_id), derived_root)
    db.add(Report(..., body=cleaned, ...))
```

Other section types (`overview`, `tldr`, `exam_summary`, `quick_review`) also get filtered for consistency, even though the LLM is unlikely to emit image refs there.

**Why regex over a Markdown AST:** The pattern we emit is narrow and well-formed (we control the prompt). A 3-group regex is simpler and faster than running the body through `mistune`/`markdown-it` just to filter one element type.

### 4.3 Frontend Mermaid fallback

In `frontend/components/markdown-renderer.tsx`, the current `MermaidBlock.catch` writes a `<pre>Mermaid error: …</pre>` into the ref. Replace with a muted one-liner:

```tsx
.catch(() => {
  if (ref.current) {
    ref.current.innerHTML = '';
    ref.current.className = 'mermaid-fallback text-xs text-muted-foreground italic my-2';
    ref.current.textContent = '（图示加载失败）';
  }
});
```

The component still renders something, so React doesn't care about the unmounted-ref race. No new state needed.

### 4.4 Frontend formula styling

Append to `frontend/app/globals.css` (after the existing `@import "katex/dist/katex.min.css"`):

```css
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

`.katex-display` is KaTeX's auto-applied class for `$$...$$` blocks only; `.katex` (no `-display` suffix) on inline `$...$` is not affected, so inline math keeps its body-text sizing.

---

## 5. Data Model Changes

None. No schema changes. No migrations.

---

## 6. Testing

### 6.1 Backend

- New file `backend/tests/test_reporting_image_validation.py`, three cases for `_strip_missing_images`:
  - Valid path to an existing file → kept intact
  - Path whose filename doesn't exist on disk → entire `![](...)` removed
  - Path whose doc_id doesn't match the current document → entire `![](...)` removed
- Tests use `tmp_path` as the `derived_root`, create real empty files for the "exists" case.

### 6.2 Frontend

- `frontend/tests/markdown-renderer.test.tsx` gets one new test:
  - Make the mocked `mermaid.render` reject with an error
  - Render a `mermaid` code block
  - Assert the rendered node contains the fallback text `(图示加载失败)` (use the simple-paren version so the assertion doesn't depend on full-width glyphs)
  - Assert the element has class `mermaid-fallback`

### 6.3 CSS

No automated test. Verified visually during smoke test.

### 6.4 Smoke test (manual)

After implementation:
1. Clear DB rows for the test document, delete `storage/derived/<old_doc_id>/`
2. Re-upload `Lecture17_MCTS.pdf`
3. Open the detail page and confirm:
   - No bomb graphics anywhere
   - No broken-image `?` placeholders
   - Enumerations like the "MCTS 四步" appear as proper numbered lists
   - UCT / PUCT formulas render large with an amber left border

---

## 7. File Change Summary

| File | Type | Purpose |
|---|---|---|
| `backend/app/services/prompts.py` | Modify | Add 3 new rule blocks to `TOPIC_WRITE_PROMPT` |
| `backend/app/services/reporting.py` | Modify | Add `_strip_missing_images` helper; call it from `run_report_pipeline` before each `db.add(Report)` |
| `backend/tests/test_reporting_image_validation.py` | Create | Unit tests for the image validator |
| `frontend/components/markdown-renderer.tsx` | Modify | Replace Mermaid error render with muted fallback |
| `frontend/tests/markdown-renderer.test.tsx` | Modify | Add fallback test |
| `frontend/app/globals.css` | Modify | Add `.katex-display` styling |

---

## 8. Risks & Mitigations

| Risk | Mitigation |
|---|---|
| LLM still hallucinates image paths despite strict prompt | `_strip_missing_images` backend filter is the safety net — guarantees no broken images reach the browser |
| LLM still produces invalid Mermaid despite strict prompt | Frontend `.catch` shows muted one-liner instead of bomb — no worse than a missing sentence |
| Amber formula boxes clash with existing tldr/exam_summary highlights (also amber) | Accept — the visual language is intentional: both are "pay attention here" cues. Distinct shapes (card vs left-border) keep them readable |
| `_strip_missing_images` regex misses alternative image ref syntaxes (HTML `<img>`, reference-style) | Prompt only asks for `![](...)` syntax; backend check matches our emitted pattern. If failures surface later, extend the regex |
| New CSS breaks inline `$...$` rendering | Selector is specifically `.katex-display`, not `.katex` — inline math is unaffected by construction |

---

## 9. Open / Deferred

- A Mermaid syntax validator that runs *before* insertion and strips invalid blocks (stronger than relying on frontend catch). Deferred because (a) frontend fallback is adequate, (b) no simple Python Mermaid parser is available — we'd need to shell out to `mmdc`, adding a Node.js dependency to the backend container.
- Automatic re-prompting when image refs get stripped (so the LLM gets a chance to write prose-only text in place of the removed image). Deferred: in practice the surrounding prose already stands alone.
- Visual design polish on the muted-fallback text (icon, subtle hover tooltip explaining "this would have been a diagram"). Deferred as YAGNI.

---

**Design approved:** 2026-04-14 by user. Implementation plan pending.
