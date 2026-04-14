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
