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
