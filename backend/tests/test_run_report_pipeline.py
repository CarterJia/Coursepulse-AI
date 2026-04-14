import uuid
from unittest.mock import MagicMock, patch

from app.services.reporting import run_report_pipeline


PAGES = [
    {"page_number": 1, "text": "intro to matrices"},
    {"page_number": 2, "text": "matrix multiplication"},
]

PLAN = {
    "overview": "本讲介绍矩阵",
    "tldr": ["矩阵是变换", "乘法不交换", "可逆与行列式", "秩", "初等行变换"],
    "topics": [
        {
            "title": "矩阵的定义",
            "source_pages": [1],
            "uses_images_from_pages": [],
            "key_points": ["a"], "exam_tips": ["b"], "common_mistakes": ["c"],
        },
        {
            "title": "矩阵乘法",
            "source_pages": [2],
            "uses_images_from_pages": [],
            "key_points": ["x"], "exam_tips": ["y"], "common_mistakes": ["z"],
        },
    ],
    "exam_summary": {"must_know": ["求逆"], "common_pitfalls": ["AB ≠ BA"]},
    "quick_review": ["一", "二"],
}


@patch("app.services.reporting.generate_all_topic_cards")
@patch("app.services.reporting.generate_plan")
def test_run_report_pipeline_writes_all_section_types(mock_plan, mock_cards):
    mock_plan.return_value = PLAN
    mock_cards.return_value = ["card A body", "card B body"]

    db = MagicMock()
    added_reports: list = []
    db.add.side_effect = lambda obj: added_reports.append(obj)

    document_id = uuid.uuid4()
    run_report_pipeline(db, document_id, PAGES, image_manifest={})

    # should add 5 rows: overview + tldr + 2 topics + exam_summary + quick_review = 6
    section_types = sorted(r.section_type for r in added_reports)
    assert section_types == [
        "exam_summary", "overview", "quick_review", "tldr", "topic", "topic"
    ]
    # topics have the LLM-generated bodies
    topic_rows = [r for r in added_reports if r.section_type == "topic"]
    assert any("card A body" in r.body for r in topic_rows)
    assert any("card B body" in r.body for r in topic_rows)
    # overview row has the overview text
    overview_row = next(r for r in added_reports if r.section_type == "overview")
    assert "矩阵" in overview_row.body


@patch("app.services.reporting.build_fallback_plan")
@patch("app.services.reporting.generate_all_topic_cards")
@patch("app.services.reporting.generate_plan")
def test_run_report_pipeline_uses_fallback_on_pass1_failure(mock_plan, mock_cards, mock_fallback):
    from app.services.report_planner import PlanValidationError
    mock_plan.side_effect = PlanValidationError("total failure")
    mock_fallback.return_value = PLAN
    mock_cards.return_value = ["A", "B"]

    db = MagicMock()
    run_report_pipeline(db, uuid.uuid4(), PAGES, image_manifest={})

    mock_fallback.assert_called_once()
    mock_cards.assert_called_once()
