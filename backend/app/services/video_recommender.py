"""Video recommender: embedding similarity scoring + DB writes."""
from __future__ import annotations

import logging
import uuid as _uuid
from typing import Any

from sqlalchemy.orm import Session

from app.models.video_recommendation import VideoRecommendation
from app.services.bilibili import build_search_query, search_videos
from app.services.embedding import generate_embedding

logger = logging.getLogger(__name__)

MAX_VIDEOS_PER_TOPIC = 2


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(x * x for x in b) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def _compute_similarity(topic_text: str, video_text: str) -> float:
    """Compute cosine similarity between topic key_points and video title+description."""
    topic_vec = generate_embedding(topic_text)
    video_vec = generate_embedding(video_text)
    return _cosine_similarity(topic_vec, video_vec)


def recommend_videos_for_topic(topic: dict[str, Any]) -> list[dict[str, Any]]:
    """Search Bilibili for a single topic and return scored candidates.

    Returns a list of dicts with video info + similarity_score, sorted descending.
    """
    keywords = topic.get("search_keywords", [])
    if not keywords:
        return []

    seen_bvids: set[str] = set()
    all_candidates = []

    for keyword in keywords:
        query = build_search_query(keyword)
        results = search_videos(query)
        for v in results:
            if v.bvid not in seen_bvids:
                seen_bvids.add(v.bvid)
                all_candidates.append(v)

    if not all_candidates:
        return []

    topic_text = "; ".join(topic.get("key_points", [])) or topic["title"]

    scored: list[dict[str, Any]] = []
    for v in all_candidates:
        video_text = f"{v.title} {v.description}"
        score = _compute_similarity(topic_text, video_text)
        scored.append({
            "bvid": v.bvid,
            "title": v.title,
            "description": v.description,
            "cover_url": v.cover_url,
            "up_name": v.up_name,
            "duration_seconds": v.duration_seconds,
            "play_count": v.play_count,
            "similarity_score": score,
            "topic_title": topic["title"],
        })

    scored.sort(key=lambda x: x["similarity_score"], reverse=True)
    return scored[:MAX_VIDEOS_PER_TOPIC]


def recommend_videos_for_document(
    db: Session,
    document_id: _uuid.UUID,
    topics: list[dict[str, Any]],
) -> None:
    """Run video recommendation for all topics and write to DB.

    Cross-topic dedup: if the same bvid appears for multiple topics,
    only the occurrence with the highest similarity_score is kept.
    """
    best_by_bvid: dict[str, dict[str, Any]] = {}

    for topic in topics:
        try:
            candidates = recommend_videos_for_topic(topic)
        except Exception:
            logger.exception("Video recommendation failed for topic '%s'", topic.get("title"))
            continue

        for c in candidates:
            bvid = c["bvid"]
            if bvid not in best_by_bvid or c["similarity_score"] > best_by_bvid[bvid]["similarity_score"]:
                best_by_bvid[bvid] = c

    for rec in best_by_bvid.values():
        db.add(VideoRecommendation(
            id=_uuid.uuid4(),
            document_id=document_id,
            topic_title=rec["topic_title"],
            bilibili_url=f"https://www.bilibili.com/video/{rec['bvid']}",
            bvid=rec["bvid"],
            title=rec["title"],
            description=rec["description"],
            cover_url=rec["cover_url"],
            up_name=rec["up_name"],
            duration_seconds=rec["duration_seconds"],
            play_count=rec["play_count"],
            similarity_score=rec["similarity_score"],
        ))
