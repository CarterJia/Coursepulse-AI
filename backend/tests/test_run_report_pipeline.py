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
            "search_keywords": ["矩阵定义"],
        },
        {
            "title": "矩阵乘法",
            "source_pages": [2],
            "uses_images_from_pages": [],
            "key_points": ["x"], "exam_tips": ["y"], "common_mistakes": ["z"],
            "search_keywords": ["矩阵乘法"],
        },
    ],
    "exam_summary": {"must_know": ["求逆"], "common_pitfalls": ["AB ≠ BA"]},
    "quick_review": ["一", "二"],
}


@patch("app.services.reporting.recommend_videos_for_document")
@patch("app.services.reporting.generate_all_topic_cards")
@patch("app.services.reporting.generate_plan")
def test_run_report_pipeline_writes_all_section_types(mock_plan, mock_cards, _mock_videos):
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


@patch("app.services.reporting.recommend_videos_for_document")
@patch("app.services.reporting.build_fallback_plan")
@patch("app.services.reporting.generate_all_topic_cards")
@patch("app.services.reporting.generate_plan")
def test_run_report_pipeline_uses_fallback_on_pass1_failure(mock_plan, mock_cards, mock_fallback, _mock_videos):
    from app.services.report_planner import PlanValidationError
    mock_plan.side_effect = PlanValidationError("total failure")
    mock_fallback.return_value = PLAN
    mock_cards.return_value = ["A", "B"]

    db = MagicMock()
    run_report_pipeline(db, uuid.uuid4(), PAGES, image_manifest={})

    mock_fallback.assert_called_once()
    mock_cards.assert_called_once()


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
         patch("app.services.reporting.generate_plan", return_value=PLAN), \
         patch("app.services.reporting.recommend_videos_for_document"):
        db = MagicMock()
        added: list = []
        db.add.side_effect = lambda obj: added.append(obj)

        run_report_pipeline(db, document_id, PAGES, image_manifest={})

    topic_rows = [r for r in added if r.section_type == "topic"]
    all_bodies = "\n".join(r.body for r in topic_rows)
    assert "real.png" in all_bodies  # real ref kept
    assert "ghost.png" not in all_bodies  # hallucinated refs stripped
