import pytest

from app.services.report_planner import PlanValidationError, validate_plan


VALID_PLAN = {
    "overview": "本讲讲线代",
    "tldr": ["要点 1", "要点 2", "要点 3", "要点 4", "要点 5"],
    "topics": [
        {
            "title": "矩阵乘法",
            "source_pages": [1, 2],
            "uses_images_from_pages": [],
            "key_points": ["a"],
            "exam_tips": ["b"],
            "common_mistakes": ["c"],
        }
    ],
    "exam_summary": {"must_know": ["x"], "common_pitfalls": ["y"]},
    "quick_review": ["一", "二", "三"],
}


def test_valid_plan_passes():
    validate_plan(VALID_PLAN, max_page=3)


def test_missing_topics_raises():
    bad = dict(VALID_PLAN)
    bad.pop("topics")
    with pytest.raises(PlanValidationError, match="topics"):
        validate_plan(bad, max_page=3)


def test_topics_not_list_raises():
    bad = {**VALID_PLAN, "topics": "oops"}
    with pytest.raises(PlanValidationError):
        validate_plan(bad, max_page=3)


def test_source_page_out_of_range_raises():
    bad = {**VALID_PLAN, "topics": [{**VALID_PLAN["topics"][0], "source_pages": [99]}]}
    with pytest.raises(PlanValidationError, match="source_pages"):
        validate_plan(bad, max_page=3)


def test_missing_overview_raises():
    bad = dict(VALID_PLAN)
    bad.pop("overview")
    with pytest.raises(PlanValidationError, match="overview"):
        validate_plan(bad, max_page=3)


def test_exam_summary_missing_keys_raises():
    bad = {**VALID_PLAN, "exam_summary": {"must_know": ["x"]}}  # missing common_pitfalls
    with pytest.raises(PlanValidationError, match="common_pitfalls"):
        validate_plan(bad, max_page=3)


def test_search_keywords_defaults_to_empty_when_missing():
    plan = {**VALID_PLAN, "topics": [{**VALID_PLAN["topics"][0]}]}
    validate_plan(plan, max_page=3)
    assert plan["topics"][0]["search_keywords"] == []


def test_search_keywords_invalid_type_raises():
    topic = {**VALID_PLAN["topics"][0], "search_keywords": "not a list"}
    bad = {**VALID_PLAN, "topics": [topic]}
    with pytest.raises(PlanValidationError, match="search_keywords"):
        validate_plan(bad, max_page=3)


def test_search_keywords_non_string_items_raises():
    topic = {**VALID_PLAN["topics"][0], "search_keywords": [123]}
    bad = {**VALID_PLAN, "topics": [topic]}
    with pytest.raises(PlanValidationError, match="search_keywords"):
        validate_plan(bad, max_page=3)
