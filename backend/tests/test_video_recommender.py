import uuid
from unittest.mock import MagicMock, patch

import app.models.course  # noqa: F401 — ensure relationship mappers resolve
import app.models.document  # noqa: F401
from app.services.bilibili import BilibiliVideo
from app.services.video_recommender import (
    _compute_similarity,
    recommend_videos_for_topic,
    recommend_videos_for_document,
)


def _make_video(bvid: str = "BV1", title: str = "测试", description: str = "描述", play: int = 50000) -> BilibiliVideo:
    return BilibiliVideo(
        bvid=bvid, title=title, description=description,
        cover_url="https://cover.jpg", up_name="UP",
        duration_seconds=300, play_count=play,
    )


def test_compute_similarity_returns_float():
    score = _compute_similarity("蒙特卡洛树搜索是一种算法", "蒙特卡洛树搜索讲解 一种强化学习算法")
    assert isinstance(score, float)
    assert 0.0 <= score <= 1.0


def test_compute_similarity_related_higher_than_unrelated():
    related = _compute_similarity("蒙特卡洛树搜索算法", "MCTS 蒙特卡洛树搜索详解")
    unrelated = _compute_similarity("蒙特卡洛树搜索算法", "今天的天气真不错")
    assert related > unrelated


@patch("app.services.video_recommender._compute_similarity", lambda *_: 0.9)
@patch("app.services.video_recommender.search_videos")
def test_recommend_videos_for_topic_deduplicates(mock_search):
    mock_search.return_value = [
        _make_video(bvid="BV1", title="MCTS讲解"),
        _make_video(bvid="BV1", title="MCTS讲解"),
        _make_video(bvid="BV2", title="蒙特卡洛方法"),
    ]
    topic = {
        "title": "MCTS",
        "search_keywords": ["MCTS"],
        "key_points": ["蒙特卡洛树搜索"],
    }
    results = recommend_videos_for_topic(topic)
    bvids = [r["bvid"] for r in results]
    assert len(bvids) == len(set(bvids))


@patch("app.services.video_recommender._compute_similarity", lambda *_: 0.9)
@patch("app.services.video_recommender.search_videos")
def test_recommend_videos_for_topic_returns_max_2(mock_search):
    mock_search.return_value = [
        _make_video(bvid=f"BV{i}", title=f"视频{i}") for i in range(5)
    ]
    topic = {
        "title": "MCTS",
        "search_keywords": ["MCTS"],
        "key_points": ["蒙特卡洛树搜索"],
    }
    results = recommend_videos_for_topic(topic)
    assert len(results) <= 2


@patch("app.services.video_recommender.search_videos")
def test_recommend_videos_for_topic_filters_below_threshold(mock_search):
    mock_search.return_value = [
        _make_video(bvid="BV1", title="高相关"),
        _make_video(bvid="BV2", title="低相关"),
    ]
    topic = {
        "title": "MCTS",
        "search_keywords": ["MCTS"],
        "key_points": ["蒙特卡洛树搜索"],
    }
    scores = iter([0.8, 0.3])
    with patch("app.services.video_recommender._compute_similarity", lambda *_: next(scores)):
        results = recommend_videos_for_topic(topic)
    bvids = [r["bvid"] for r in results]
    assert bvids == ["BV1"]


@patch("app.services.video_recommender.recommend_videos_for_topic")
def test_recommend_videos_for_document_writes_to_db(mock_rec):
    mock_rec.return_value = [
        {
            "bvid": "BV1",
            "title": "MCTS讲解",
            "description": "描述",
            "cover_url": "https://cover.jpg",
            "up_name": "UP",
            "duration_seconds": 300,
            "play_count": 50000,
            "similarity_score": 0.85,
            "topic_title": "MCTS",
        }
    ]
    db = MagicMock()
    topics = [{"title": "MCTS", "search_keywords": ["MCTS"], "key_points": ["蒙特卡洛"]}]
    recommend_videos_for_document(db, uuid.uuid4(), topics)
    assert db.add.call_count == 1


@patch("app.services.video_recommender.recommend_videos_for_topic")
def test_recommend_videos_for_document_cross_topic_dedup(mock_rec):
    video = {
        "bvid": "BV1",
        "title": "MCTS讲解",
        "description": "描述",
        "cover_url": "https://cover.jpg",
        "up_name": "UP",
        "duration_seconds": 300,
        "play_count": 50000,
        "similarity_score": 0.85,
        "topic_title": "MCTS",
    }
    mock_rec.return_value = [video]
    db = MagicMock()
    topics = [
        {"title": "MCTS", "search_keywords": ["MCTS"], "key_points": ["蒙特卡洛"]},
        {"title": "树搜索", "search_keywords": ["树搜索"], "key_points": ["搜索"]},
    ]
    recommend_videos_for_document(db, uuid.uuid4(), topics)
    assert db.add.call_count == 1
