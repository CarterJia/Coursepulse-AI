from app.services.prompts import (
    REPORT_PLAN_PROMPT,
    TOPIC_WRITE_PROMPT,
    build_retry_prompt,
)


def test_report_plan_prompt_has_placeholders():
    assert "{pages_block}" in REPORT_PLAN_PROMPT
    assert "{image_manifest_block}" in REPORT_PLAN_PROMPT
    assert "overview" in REPORT_PLAN_PROMPT
    assert "topics" in REPORT_PLAN_PROMPT
    assert "exam_summary" in REPORT_PLAN_PROMPT
    assert "quick_review" in REPORT_PLAN_PROMPT


def test_topic_write_prompt_has_placeholders():
    for key in (
        "{topic_title}",
        "{source_pages}",
        "{image_paths_block}",
        "{key_points}",
        "{exam_tips}",
        "{common_mistakes}",
        "{pages_block}",
    ):
        assert key in TOPIC_WRITE_PROMPT, key


def test_build_retry_prompt_includes_previous_response_and_error():
    original = "ORIG PROMPT {pages_block} END"
    prev = '{"topics": "oops not an array"}'
    err = "topics must be a list"
    retry = build_retry_prompt(original, prev, err)
    assert "ORIG PROMPT" in retry
    assert prev in retry
    assert err in retry
    assert "修正" in retry or "fix" in retry.lower()


def test_topic_write_prompt_has_mermaid_strict_rules():
    # Strict Mermaid rules must be present so the LLM stops emitting
    # labels with parens/brackets that break the renderer.
    assert "Mermaid" in TOPIC_WRITE_PROMPT
    assert "graph LR" in TOPIC_WRITE_PROMPT or "graph TD" in TOPIC_WRITE_PROMPT
    assert '( ) [ ] {{ }}' in TOPIC_WRITE_PROMPT
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


def test_topic_write_prompt_formats_cleanly():
    """Regression: all literal braces in TOPIC_WRITE_PROMPT must be
    either format placeholders or escaped ({{ }}). Otherwise .format()
    raises KeyError at runtime in generate_topic_card."""
    TOPIC_WRITE_PROMPT.format(
        topic_title="t",
        source_pages="[1]",
        image_paths_block="-",
        key_points="-",
        exam_tips="-",
        common_mistakes="-",
        pages_block="...",
    )
