from unittest.mock import MagicMock, patch

from app.services.reporting import generate_topic_card, generate_all_topic_cards


def _mk_response(content: str):
    resp = MagicMock()
    resp.choices = [MagicMock()]
    resp.choices[0].message.content = content
    return resp


TOPIC = {
    "title": "矩阵乘法",
    "source_pages": [1, 2],
    "uses_images_from_pages": [2],
    "key_points": ["kp"],
    "exam_tips": ["et"],
    "common_mistakes": ["cm"],
}

PAGES = [
    {"page_number": 1, "text": "page one content"},
    {"page_number": 2, "text": "page two content"},
    {"page_number": 3, "text": "unrelated"},
]

IMAGE_MANIFEST = {2: ["page_2_img_0.png"]}


@patch("app.services.reporting.get_openai_client")
def test_generate_topic_card_builds_prompt_and_calls_llm(mock_client_factory):
    client = MagicMock()
    client.chat.completions.create.return_value = _mk_response(
        "### 主题: 矩阵乘法\n\n内容..."
    )
    mock_client_factory.return_value = client

    card = generate_topic_card(
        TOPIC, PAGES, IMAGE_MANIFEST, document_id="doc-123"
    )

    assert "矩阵乘法" in card
    # call received prompt with the right topic title
    call_prompt = client.chat.completions.create.call_args.kwargs["messages"][0]["content"]
    assert "矩阵乘法" in call_prompt
    # only source_pages should appear in the pages_block
    assert "page one content" in call_prompt
    assert "page two content" in call_prompt
    assert "unrelated" not in call_prompt
    # image path must include the files route pattern
    assert "/api/files/doc-123/page_2_img_0.png" in call_prompt


@patch("app.services.reporting.generate_topic_card")
def test_generate_all_topic_cards_runs_concurrently(mock_single):
    mock_single.side_effect = lambda t, *a, **kw: f"card for {t['title']}"
    topics = [
        {"title": "A", "source_pages": [1], "uses_images_from_pages": [],
         "key_points": [], "exam_tips": [], "common_mistakes": []},
        {"title": "B", "source_pages": [2], "uses_images_from_pages": [],
         "key_points": [], "exam_tips": [], "common_mistakes": []},
        {"title": "C", "source_pages": [3], "uses_images_from_pages": [],
         "key_points": [], "exam_tips": [], "common_mistakes": []},
    ]
    cards = generate_all_topic_cards(topics, PAGES, {}, document_id="doc-xyz", max_workers=2)

    # results align with input order
    assert cards == ["card for A", "card for B", "card for C"]
