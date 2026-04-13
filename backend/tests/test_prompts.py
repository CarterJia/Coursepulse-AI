from app.services.prompts import CHAPTER_REPORT_PROMPT, GLOSSARY_EXTRACT_PROMPT


def test_chapter_report_prompt_has_placeholders():
    assert "{context}" in CHAPTER_REPORT_PROMPT
    assert "{chapter_title}" in CHAPTER_REPORT_PROMPT


def test_glossary_extract_prompt_has_placeholders():
    assert "{text}" in GLOSSARY_EXTRACT_PROMPT
