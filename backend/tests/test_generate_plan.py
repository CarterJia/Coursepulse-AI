import json
from unittest.mock import MagicMock, patch

import pytest

from app.services.report_planner import generate_plan


GOOD_PLAN = {
    "overview": "本讲讲线代",
    "tldr": ["A", "B", "C", "D", "E"],
    "topics": [
        {
            "title": "矩阵",
            "source_pages": [1, 2],
            "uses_images_from_pages": [],
            "key_points": ["a"],
            "exam_tips": ["b"],
            "common_mistakes": ["c"],
        }
    ],
    "exam_summary": {"must_know": ["x"], "common_pitfalls": ["y"]},
    "quick_review": ["q"],
}


def _mk_response(content: str):
    resp = MagicMock()
    resp.choices = [MagicMock()]
    resp.choices[0].message.content = content
    return resp


@patch("app.services.report_planner.get_openai_client")
def test_generate_plan_succeeds_first_try(mock_client_factory):
    client = MagicMock()
    client.chat.completions.create.return_value = _mk_response(json.dumps(GOOD_PLAN))
    mock_client_factory.return_value = client

    pages = [{"page_number": i, "text": f"page {i}"} for i in (1, 2)]
    plan = generate_plan(pages, image_manifest={}, max_retries=5)

    assert plan["overview"] == "本讲讲线代"
    assert client.chat.completions.create.call_count == 1
    # JSON mode must be requested
    call_kwargs = client.chat.completions.create.call_args.kwargs
    assert call_kwargs["response_format"] == {"type": "json_object"}


@patch("app.services.report_planner.get_openai_client")
def test_generate_plan_retries_on_malformed_json(mock_client_factory):
    client = MagicMock()
    client.chat.completions.create.side_effect = [
        _mk_response("not json"),
        _mk_response('{"overview": "bad but valid json, missing fields"}'),
        _mk_response(json.dumps(GOOD_PLAN)),
    ]
    mock_client_factory.return_value = client

    pages = [{"page_number": 1, "text": "p1"}, {"page_number": 2, "text": "p2"}]
    plan = generate_plan(pages, image_manifest={}, max_retries=5)

    assert plan["overview"] == "本讲讲线代"
    assert client.chat.completions.create.call_count == 3
    # retry prompts must include previous response
    second_prompt = client.chat.completions.create.call_args_list[1].kwargs["messages"][0]["content"]
    assert "not json" in second_prompt
