# Slice 2: Bilibili Video Recommendations — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** After report generation, automatically search Bilibili for short educational videos matching each topic, rank by embedding similarity, and display them in the frontend.

**Architecture:** Extend Pass-1 plan JSON with `search_keywords` per topic. After report rows are written, a new pipeline step calls the Bilibili public search API for each topic, filters by duration/play count, scores candidates via `bge-small-zh` embedding cosine similarity against topic key_points, and writes results to a new `video_recommendations` table. A new API route serves videos grouped by topic, and the frontend renders video cards at the bottom of each TopicCard accordion.

**Tech Stack:** Bilibili public search API (no key required), `sentence-transformers` (existing `bge-small-zh` model), Alembic migration, FastAPI route, React video card component.

---

## File Map

| File | Action | Responsibility |
|------|--------|----------------|
| `backend/app/models/video_recommendation.py` | Create | SQLAlchemy model for `video_recommendations` table |
| `backend/alembic/versions/0004_video_recommendations.py` | Create | Alembic migration to create the table |
| `backend/app/services/bilibili.py` | Create | Bilibili search API wrapper + rule filtering (duration, play count) |
| `backend/app/services/video_recommender.py` | Create | Embedding similarity scoring + DB writes |
| `backend/app/services/prompts.py` | Modify | Add `search_keywords` to Pass-1 plan schema |
| `backend/app/services/report_planner.py` | Modify | Validate `search_keywords` field |
| `backend/app/services/reporting.py` | Modify | Call video recommender at pipeline tail |
| `backend/app/schemas/video.py` | Create | Pydantic response schema |
| `backend/app/api/routes/videos.py` | Create | `GET /api/documents/{id}/videos` |
| `backend/app/main.py` | Modify | Register videos router |
| `backend/tests/test_bilibili.py` | Create | Tests for Bilibili API wrapper |
| `backend/tests/test_video_recommender.py` | Create | Tests for similarity scoring + DB writes |
| `backend/tests/test_plan_validator.py` | Modify | Add `search_keywords` to test fixtures |
| `backend/tests/test_prompts.py` | Modify | Assert `search_keywords` in plan prompt |
| `backend/tests/test_run_report_pipeline.py` | Modify | Mock video recommender in pipeline tests |
| `frontend/lib/api.ts` | Modify | Add `getVideos()` fetch function + types |
| `frontend/components/video-card.tsx` | Create | Video card component (cover + title + UP + duration) |
| `frontend/components/topic-card.tsx` | Modify | Render video cards at bottom when available |
| `frontend/app/documents/[id]/page.tsx` | Modify | Fetch videos and pass to ReportViewer |
| `frontend/components/report-viewer.tsx` | Modify | Pass videos to TopicCard |

---

### Task 1: Video Recommendation Model + Migration

**Files:**
- Create: `backend/app/models/video_recommendation.py`
- Create: `backend/alembic/versions/0004_video_recommendations.py`
- Test: `backend/tests/test_models.py` (append)

- [ ] **Step 1: Write the failing test**

Append to `backend/tests/test_models.py`:

```python
def test_video_recommendation_model_importable():
    from app.models.video_recommendation import VideoRecommendation
    assert VideoRecommendation.__tablename__ == "video_recommendations"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && PYTHONPATH=. ../.venv/bin/pytest tests/test_models.py::test_video_recommendation_model_importable -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Create the model**

Create `backend/app/models/video_recommendation.py`:

```python
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class VideoRecommendation(Base):
    __tablename__ = "video_recommendations"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("documents.id"))
    topic_title: Mapped[str] = mapped_column(String(512))
    bilibili_url: Mapped[str] = mapped_column(String(512))
    bvid: Mapped[str] = mapped_column(String(64))
    title: Mapped[str] = mapped_column(String(512))
    description: Mapped[str] = mapped_column(Text, default="")
    cover_url: Mapped[str] = mapped_column(String(512))
    up_name: Mapped[str] = mapped_column(String(256))
    duration_seconds: Mapped[int] = mapped_column(Integer)
    play_count: Mapped[int] = mapped_column(Integer)
    similarity_score: Mapped[float] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && PYTHONPATH=. ../.venv/bin/pytest tests/test_models.py::test_video_recommendation_model_importable -v`
Expected: PASS

- [ ] **Step 5: Create the Alembic migration**

Create `backend/alembic/versions/0004_video_recommendations.py`:

```python
"""Add video_recommendations table

Revision ID: 0004
Revises: 0003_add_reports_section_type
"""
from alembic import op
import sqlalchemy as sa

revision = "0004"
down_revision = "0003_add_reports_section_type"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "video_recommendations",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("document_id", sa.Uuid(), sa.ForeignKey("documents.id"), nullable=False),
        sa.Column("topic_title", sa.String(512), nullable=False),
        sa.Column("bilibili_url", sa.String(512), nullable=False),
        sa.Column("bvid", sa.String(64), nullable=False),
        sa.Column("title", sa.String(512), nullable=False),
        sa.Column("description", sa.Text(), server_default=""),
        sa.Column("cover_url", sa.String(512), nullable=False),
        sa.Column("up_name", sa.String(256), nullable=False),
        sa.Column("duration_seconds", sa.Integer(), nullable=False),
        sa.Column("play_count", sa.Integer(), nullable=False),
        sa.Column("similarity_score", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("video_recommendations")
```

- [ ] **Step 6: Commit**

```bash
git add backend/app/models/video_recommendation.py backend/alembic/versions/0004_video_recommendations.py backend/tests/test_models.py
git commit -m "feat: add VideoRecommendation model and migration"
```

---

### Task 2: Bilibili Search API Wrapper

**Files:**
- Create: `backend/app/services/bilibili.py`
- Create: `backend/tests/test_bilibili.py`

- [ ] **Step 1: Write the failing tests**

Create `backend/tests/test_bilibili.py`:

```python
import json
from unittest.mock import patch, MagicMock

from app.services.bilibili import search_videos, BilibiliVideo


def _mock_response(results: list[dict], code: int = 0) -> MagicMock:
    resp = MagicMock()
    resp.status_code = 200
    resp.json.return_value = {
        "code": code,
        "data": {"result": results},
    }
    return resp


def _make_result(
    bvid: str = "BV1test",
    title: str = "测试视频",
    description: str = "这是一个测试",
    duration: str = "5:30",
    play: int = 50000,
    author: str = "TestUP",
    pic: str = "//cover.jpg",
) -> dict:
    return {
        "bvid": bvid,
        "title": title,
        "description": description,
        "duration": duration,
        "play": play,
        "author": author,
        "pic": pic,
    }


@patch("app.services.bilibili.requests.get")
def test_search_videos_returns_filtered_results(mock_get):
    mock_get.return_value = _mock_response([
        _make_result(bvid="BV1", duration="5:30", play=50000),
        _make_result(bvid="BV2", duration="15:00", play=80000),  # too long
        _make_result(bvid="BV3", duration="3:00", play=500),     # too few plays
        _make_result(bvid="BV4", duration="8:00", play=20000),
    ])
    results = search_videos("蒙特卡洛树搜索 讲解")
    bvids = [v.bvid for v in results]
    assert "BV1" in bvids
    assert "BV4" in bvids
    assert "BV2" not in bvids  # >10 min
    assert "BV3" not in bvids  # <10000 plays


@patch("app.services.bilibili.requests.get")
def test_search_videos_parses_duration_correctly(mock_get):
    mock_get.return_value = _mock_response([
        _make_result(bvid="BV1", duration="9:59", play=20000),   # 599s, OK
        _make_result(bvid="BV2", duration="10:00", play=20000),  # 600s, exactly 10 min — excluded
        _make_result(bvid="BV3", duration="1:02:00", play=20000),  # 3720s, too long
    ])
    results = search_videos("test")
    assert len(results) == 1
    assert results[0].bvid == "BV1"
    assert results[0].duration_seconds == 599


@patch("app.services.bilibili.requests.get")
def test_search_videos_returns_empty_on_api_error(mock_get):
    mock_get.side_effect = Exception("network error")
    results = search_videos("test")
    assert results == []


@patch("app.services.bilibili.requests.get")
def test_search_videos_returns_empty_on_bad_code(mock_get):
    mock_get.return_value = _mock_response([], code=-1)
    results = search_videos("test")
    assert results == []


@patch("app.services.bilibili.requests.get")
def test_search_videos_strips_html_from_title(mock_get):
    mock_get.return_value = _mock_response([
        _make_result(
            bvid="BV1",
            title='<em class="keyword">蒙特卡洛</em>树搜索讲解',
            play=50000,
            duration="5:00",
        ),
    ])
    results = search_videos("蒙特卡洛")
    assert results[0].title == "蒙特卡洛树搜索讲解"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && PYTHONPATH=. ../.venv/bin/pytest tests/test_bilibili.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Implement the Bilibili wrapper**

Create `backend/app/services/bilibili.py`:

```python
"""Bilibili public search API wrapper with rule-based filtering."""
from __future__ import annotations

import logging
import random
import re
from dataclasses import dataclass

import requests

logger = logging.getLogger(__name__)

SEARCH_URL = "https://api.bilibili.com/x/web-interface/search/type"

MAX_DURATION_SECONDS = 600  # 10 minutes
MIN_PLAY_COUNT = 10_000

SEARCH_SUFFIXES = ["讲解", "教程", "详解", "入门"]

_HTML_TAG_RE = re.compile(r"<[^>]+>")


@dataclass
class BilibiliVideo:
    bvid: str
    title: str
    description: str
    cover_url: str
    up_name: str
    duration_seconds: int
    play_count: int


def _parse_duration(duration_str: str) -> int:
    """Parse Bilibili duration string like '5:30' or '1:02:00' into seconds."""
    parts = duration_str.split(":")
    parts = [int(p) for p in parts]
    if len(parts) == 3:
        return parts[0] * 3600 + parts[1] * 60 + parts[2]
    if len(parts) == 2:
        return parts[0] * 60 + parts[1]
    return parts[0]


def build_search_query(keyword: str) -> str:
    """Append a random educational suffix to the keyword."""
    suffix = random.choice(SEARCH_SUFFIXES)
    return f"{keyword} {suffix}"


def search_videos(query: str, max_results: int = 10) -> list[BilibiliVideo]:
    """Search Bilibili and return rule-filtered results.

    Returns an empty list on any error (network, parse, bad API code).
    """
    try:
        resp = requests.get(
            SEARCH_URL,
            params={
                "search_type": "video",
                "keyword": query,
                "order": "click",
                "page": 1,
                "pagesize": max_results,
            },
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=10,
        )
        data = resp.json()
        if data.get("code") != 0:
            logger.warning("Bilibili API returned code %s for query '%s'", data.get("code"), query)
            return []

        raw_results = data.get("data", {}).get("result") or []
    except Exception:
        logger.exception("Bilibili search failed for query '%s'", query)
        return []

    videos: list[BilibiliVideo] = []
    for item in raw_results:
        try:
            duration_s = _parse_duration(item.get("duration", "0:00"))
        except (ValueError, IndexError):
            continue

        if duration_s >= MAX_DURATION_SECONDS:
            continue

        play = item.get("play", 0)
        if isinstance(play, str):
            play = int(play) if play.isdigit() else 0
        if play < MIN_PLAY_COUNT:
            continue

        title = _HTML_TAG_RE.sub("", item.get("title", ""))

        pic = item.get("pic", "")
        if pic.startswith("//"):
            pic = f"https:{pic}"

        videos.append(BilibiliVideo(
            bvid=item.get("bvid", ""),
            title=title,
            description=item.get("description", ""),
            cover_url=pic,
            up_name=item.get("author", ""),
            duration_seconds=duration_s,
            play_count=play,
        ))

    return videos
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && PYTHONPATH=. ../.venv/bin/pytest tests/test_bilibili.py -v`
Expected: all 5 PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/bilibili.py backend/tests/test_bilibili.py
git commit -m "feat: add Bilibili search API wrapper with rule filtering"
```

---

### Task 3: Video Recommender (Embedding Similarity + DB Writes)

**Files:**
- Create: `backend/app/services/video_recommender.py`
- Create: `backend/tests/test_video_recommender.py`

- [ ] **Step 1: Write the failing tests**

Create `backend/tests/test_video_recommender.py`:

```python
import uuid
from unittest.mock import MagicMock, patch

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


@patch("app.services.video_recommender.search_videos")
def test_recommend_videos_for_topic_deduplicates(mock_search):
    mock_search.return_value = [
        _make_video(bvid="BV1", title="MCTS讲解"),
        _make_video(bvid="BV1", title="MCTS讲解"),  # duplicate
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
    # BV1 appears in both topics but should only be written once (highest similarity)
    assert db.add.call_count == 1
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && PYTHONPATH=. ../.venv/bin/pytest tests/test_video_recommender.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Implement the video recommender**

Create `backend/app/services/video_recommender.py`:

```python
"""Video recommender: embedding similarity scoring + DB writes."""
from __future__ import annotations

import logging
import uuid as _uuid
from typing import Any

from sqlalchemy.orm import Session

from app.models.video_recommendation import VideoRecommendation
from app.services.bilibili import BilibiliVideo, build_search_query, search_videos
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
    all_candidates: list[BilibiliVideo] = []

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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && PYTHONPATH=. ../.venv/bin/pytest tests/test_video_recommender.py -v`
Expected: all 6 PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/video_recommender.py backend/tests/test_video_recommender.py
git commit -m "feat: add video recommender with embedding similarity scoring"
```

---

### Task 4: Extend Pass-1 Plan with `search_keywords`

**Files:**
- Modify: `backend/app/services/prompts.py` (REPORT_PLAN_PROMPT)
- Modify: `backend/app/services/report_planner.py` (validate_plan, build_fallback_plan)
- Modify: `backend/tests/test_plan_validator.py`
- Modify: `backend/tests/test_prompts.py`

- [ ] **Step 1: Write the failing tests**

Add to `backend/tests/test_plan_validator.py` — find the valid plan fixture used in existing tests and add `search_keywords` to each topic, then add a test for missing `search_keywords`:

```python
def test_validate_plan_rejects_missing_search_keywords(valid_plan, max_page):
    """search_keywords is required on each topic."""
    del valid_plan["topics"][0]["search_keywords"]
    with pytest.raises(PlanValidationError, match="search_keywords"):
        validate_plan(valid_plan, max_page=max_page)
```

Add to `backend/tests/test_prompts.py`:

```python
def test_report_plan_prompt_has_search_keywords():
    assert "search_keywords" in REPORT_PLAN_PROMPT
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && PYTHONPATH=. ../.venv/bin/pytest tests/test_plan_validator.py::test_validate_plan_rejects_missing_search_keywords tests/test_prompts.py::test_report_plan_prompt_has_search_keywords -v`
Expected: FAIL

- [ ] **Step 3: Update REPORT_PLAN_PROMPT**

In `backend/app/services/prompts.py`, add `"search_keywords"` to the topic schema inside `REPORT_PLAN_PROMPT`. In the JSON example block, add after `"common_mistakes"`:

```
"search_keywords": ["搜索用关键词1", "搜索用关键词2"]
```

Also add to the "其他要求" section:

```
- search_keywords: 每个主题 2-3 个关键词, 用于在视频网站搜索相关教学视频。应该是课程领域内的专业术语或概念名, 不要太泛 (如"数学") 也不要太窄 (如完整的公式)
```

- [ ] **Step 4: Update validate_plan**

In `backend/app/services/report_planner.py`, inside the topic validation loop (after the `common_mistakes` check), add:

```python
search_kw = t.get("search_keywords")
if search_kw is None:
    search_kw = []
    t["search_keywords"] = search_kw
else:
    _require_list(search_kw, f"topics[{i}].search_keywords")
    for kw in search_kw:
        if not isinstance(kw, str):
            raise PlanValidationError(f"topics[{i}].search_keywords items must be strings")
```

Note: `search_keywords` defaults to `[]` if missing (backward compat with LLM that doesn't emit it on retry). Only validates type if present.

- [ ] **Step 5: Update build_fallback_plan**

In `build_fallback_plan`, add `"search_keywords": []` to each fallback topic dict.

- [ ] **Step 6: Update test fixtures**

In `backend/tests/test_plan_validator.py`, add `"search_keywords": ["关键词"]` to every topic in the valid plan fixture. In `backend/tests/test_run_report_pipeline.py`, add `"search_keywords": ["矩阵"]` to each topic in the `PLAN` dict. In `backend/tests/test_fallback_plan.py`, assert that fallback topics have `"search_keywords"`.

- [ ] **Step 7: Run all affected tests**

Run: `cd backend && PYTHONPATH=. ../.venv/bin/pytest tests/test_plan_validator.py tests/test_prompts.py tests/test_run_report_pipeline.py tests/test_fallback_plan.py -v`
Expected: all PASS

- [ ] **Step 8: Commit**

```bash
git add backend/app/services/prompts.py backend/app/services/report_planner.py backend/tests/test_plan_validator.py backend/tests/test_prompts.py backend/tests/test_run_report_pipeline.py backend/tests/test_fallback_plan.py
git commit -m "feat: add search_keywords to Pass-1 plan schema for video search"
```

---

### Task 5: Integrate Video Recommender into Pipeline

**Files:**
- Modify: `backend/app/services/reporting.py` (run_report_pipeline)
- Modify: `backend/tests/test_run_report_pipeline.py`

- [ ] **Step 1: Write the failing test**

Add to `backend/tests/test_run_report_pipeline.py`:

```python
@patch("app.services.reporting.recommend_videos_for_document")
@patch("app.services.reporting.generate_all_topic_cards")
@patch("app.services.reporting.generate_plan")
def test_run_report_pipeline_calls_video_recommender(mock_plan, mock_cards, mock_videos):
    mock_plan.return_value = PLAN
    mock_cards.return_value = ["card A", "card B"]

    db = MagicMock()
    document_id = uuid.uuid4()
    run_report_pipeline(db, document_id, PAGES, image_manifest={})

    mock_videos.assert_called_once()
    call_args = mock_videos.call_args
    assert call_args[0][0] is db
    assert call_args[0][1] == document_id
    assert call_args[0][2] == PLAN["topics"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && PYTHONPATH=. ../.venv/bin/pytest tests/test_run_report_pipeline.py::test_run_report_pipeline_calls_video_recommender -v`
Expected: FAIL (no `recommend_videos_for_document` import)

- [ ] **Step 3: Add video recommender call to pipeline**

In `backend/app/services/reporting.py`, add import:

```python
from app.services.video_recommender import recommend_videos_for_document
```

At the end of `run_report_pipeline`, after the last `db.add(Report(...))` block and before the function returns, add:

```python
    # Video recommendations (non-blocking: failure here does not affect reports)
    try:
        recommend_videos_for_document(db, document_id, plan["topics"])
    except Exception:
        logger.exception("Video recommendation failed for document %s", document_id)
```

- [ ] **Step 4: Run all pipeline tests**

Run: `cd backend && PYTHONPATH=. ../.venv/bin/pytest tests/test_run_report_pipeline.py -v`
Expected: all PASS

- [ ] **Step 5: Update existing pipeline tests to mock video recommender**

The existing tests in `test_run_report_pipeline.py` that patch `generate_plan` and `generate_all_topic_cards` now also need to patch `recommend_videos_for_document` to avoid calling the real embedding model. Add `@patch("app.services.reporting.recommend_videos_for_document")` to each existing test, adding the mock parameter.

- [ ] **Step 6: Run all pipeline tests again**

Run: `cd backend && PYTHONPATH=. ../.venv/bin/pytest tests/test_run_report_pipeline.py -v`
Expected: all PASS

- [ ] **Step 7: Commit**

```bash
git add backend/app/services/reporting.py backend/tests/test_run_report_pipeline.py
git commit -m "feat: integrate video recommender into report pipeline"
```

---

### Task 6: Videos API Route

**Files:**
- Create: `backend/app/schemas/video.py`
- Create: `backend/app/api/routes/videos.py`
- Modify: `backend/app/main.py`

- [ ] **Step 1: Create the Pydantic schema**

Create `backend/app/schemas/video.py`:

```python
from pydantic import BaseModel


class VideoResponse(BaseModel):
    bvid: str
    title: str
    bilibili_url: str
    cover_url: str
    up_name: str
    duration_seconds: int
    play_count: int
    similarity_score: float


class TopicVideosResponse(BaseModel):
    topic_title: str
    videos: list[VideoResponse]
```

- [ ] **Step 2: Create the route**

Create `backend/app/api/routes/videos.py`:

```python
import uuid
from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.video_recommendation import VideoRecommendation
from app.schemas.video import TopicVideosResponse, VideoResponse

router = APIRouter()


@router.get(
    "/documents/{document_id}/videos",
    response_model=list[TopicVideosResponse],
)
def get_document_videos(document_id: str, db: Session = Depends(get_db)):
    doc_uuid = uuid.UUID(document_id)
    rows = (
        db.query(VideoRecommendation)
        .filter(VideoRecommendation.document_id == doc_uuid)
        .order_by(VideoRecommendation.similarity_score.desc())
        .all()
    )
    grouped: dict[str, list[VideoResponse]] = defaultdict(list)
    for r in rows:
        grouped[r.topic_title].append(VideoResponse(
            bvid=r.bvid,
            title=r.title,
            bilibili_url=r.bilibili_url,
            cover_url=r.cover_url,
            up_name=r.up_name,
            duration_seconds=r.duration_seconds,
            play_count=r.play_count,
            similarity_score=r.similarity_score,
        ))
    return [
        TopicVideosResponse(topic_title=title, videos=vids)
        for title, vids in grouped.items()
    ]
```

- [ ] **Step 3: Register the router in main.py**

In `backend/app/main.py`, add:

```python
from app.api.routes.videos import router as videos_router
```

And at the bottom with the other `app.include_router` calls:

```python
app.include_router(videos_router, prefix="/api")
```

- [ ] **Step 4: Run the full backend test suite**

Run: `cd backend && PYTHONPATH=. ../.venv/bin/pytest -x --tb=short`
Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/schemas/video.py backend/app/api/routes/videos.py backend/app/main.py
git commit -m "feat: add GET /api/documents/{id}/videos endpoint"
```

---

### Task 7: Frontend — API Function + Video Card Component

**Files:**
- Modify: `frontend/lib/api.ts`
- Create: `frontend/components/video-card.tsx`

- [ ] **Step 1: Add types and fetch function to api.ts**

Append to `frontend/lib/api.ts`:

```typescript
export interface Video {
  bvid: string;
  title: string;
  bilibili_url: string;
  cover_url: string;
  up_name: string;
  duration_seconds: number;
  play_count: number;
  similarity_score: number;
}

export interface TopicVideos {
  topic_title: string;
  videos: Video[];
}

export async function getVideos(documentId: string): Promise<TopicVideos[]> {
  const res = await fetch(`${API_BASE}/api/documents/${documentId}/videos`);
  if (!res.ok) return [];
  return res.json();
}
```

- [ ] **Step 2: Create the VideoCard component**

Create `frontend/components/video-card.tsx`:

```tsx
import type { Video } from "@/lib/api";

function formatDuration(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m}:${s.toString().padStart(2, "0")}`;
}

function formatPlayCount(count: number): string {
  if (count >= 10000) {
    return `${(count / 10000).toFixed(1)}万`;
  }
  return count.toLocaleString();
}

interface VideoCardProps {
  video: Video;
}

export function VideoCard({ video }: VideoCardProps) {
  return (
    <a
      href={video.bilibili_url}
      target="_blank"
      rel="noopener noreferrer"
      className="flex gap-3 rounded-lg border p-3 hover:bg-accent transition-colors"
    >
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        src={video.cover_url}
        alt={video.title}
        className="w-36 h-20 object-cover rounded shrink-0"
      />
      <div className="flex flex-col justify-between min-w-0 flex-1">
        <p className="font-medium text-sm line-clamp-2">{video.title}</p>
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <span>{video.up_name}</span>
          <span>·</span>
          <span>{formatDuration(video.duration_seconds)}</span>
          <span>·</span>
          <span>{formatPlayCount(video.play_count)}播放</span>
        </div>
      </div>
    </a>
  );
}
```

- [ ] **Step 3: Commit**

```bash
git add frontend/lib/api.ts frontend/components/video-card.tsx
git commit -m "feat: add video API client and VideoCard component"
```

---

### Task 8: Frontend — Wire Videos into TopicCard and Report Page

**Files:**
- Modify: `frontend/app/documents/[id]/page.tsx`
- Modify: `frontend/components/report-viewer.tsx`
- Modify: `frontend/components/topic-card.tsx`

- [ ] **Step 1: Update document page to fetch videos**

In `frontend/app/documents/[id]/page.tsx`, add `getVideos` to the import from `@/lib/api`, add `TopicVideos` to the type import. Add state:

```tsx
const [videos, setVideos] = useState<TopicVideos[]>([]);
```

Update the `Promise.all` to include `getVideos(id)`:

```tsx
Promise.all([getDocument(id), getGlossary(id), getVideos(id)])
  .then(([d, g, v]) => { setDoc(d); setGlossary(g); setVideos(v); })
```

Pass videos to ReportViewer:

```tsx
<ReportViewer reports={doc.reports ?? []} videos={videos} />
```

- [ ] **Step 2: Update ReportViewer to accept and pass videos**

In `frontend/components/report-viewer.tsx`, add `TopicVideos` to the import. Update the interface:

```tsx
interface ReportViewerProps {
  reports: Report[];
  videos?: TopicVideos[];
}
```

Update the function signature and pass videos to TopicCard:

```tsx
export function ReportViewer({ reports, videos = [] }: ReportViewerProps) {
```

Inside the topics mapping, look up videos for each topic:

```tsx
{topics.map((r) => {
  const topicVideos = videos.find((v) => v.topic_title === r.title)?.videos ?? [];
  return (
    <TopicCard key={r.id} id={r.id} title={r.title} body={r.body} videos={topicVideos} />
  );
})}
```

- [ ] **Step 3: Update TopicCard to render videos**

In `frontend/components/topic-card.tsx`, add import:

```tsx
import { VideoCard } from "@/components/video-card";
import type { Video } from "@/lib/api";
```

Update the interface:

```tsx
interface TopicCardProps {
  id: string;
  title: string;
  body: string;
  videos?: Video[];
}
```

Update the component to render videos at the bottom of AccordionContent, after the MarkdownRenderer:

```tsx
export function TopicCard({ id, title, body, videos = [] }: TopicCardProps) {
  return (
    <AccordionItem value={id}>
      <AccordionTrigger className="text-lg font-semibold">{title}</AccordionTrigger>
      <AccordionContent>
        <MarkdownRenderer content={body} />
        {videos.length > 0 && (
          <div className="mt-6 pt-4 border-t space-y-3">
            <p className="text-sm font-medium text-muted-foreground">相关视频推荐</p>
            {videos.map((v) => (
              <VideoCard key={v.bvid} video={v} />
            ))}
          </div>
        )}
      </AccordionContent>
    </AccordionItem>
  );
}
```

- [ ] **Step 4: Verify frontend compiles**

Run: `cd frontend && npx next build 2>&1 | tail -20` (or check dev server for errors)

- [ ] **Step 5: Commit**

```bash
git add frontend/app/documents/\[id\]/page.tsx frontend/components/report-viewer.tsx frontend/components/topic-card.tsx
git commit -m "feat: display video recommendations in topic cards"
```

---

### Task 9: Run Migration + End-to-End Verification

- [ ] **Step 1: Run the Alembic migration in Docker**

```bash
cd /Users/uw/Desktop/Exam\ Hero/.worktrees/mvp-foundation
docker compose exec backend alembic upgrade head
```

Expected: migration `0004` applied successfully.

- [ ] **Step 2: Rebuild and restart containers**

```bash
docker compose up --build -d
```

- [ ] **Step 3: Run full backend test suite**

```bash
cd backend && PYTHONPATH=. ../.venv/bin/pytest -x --tb=short
```

Expected: all PASS

- [ ] **Step 4: Wipe old data and re-upload a test PDF**

```bash
docker compose exec -T db psql -U coursepulse -d coursepulse -c "TRUNCATE reports, video_recommendations, knowledge_chunks, embeddings, document_pages, documents CASCADE;"
rm -rf storage/derived/* storage/slides/*
```

Open http://localhost:3000, upload a PDF, wait for pipeline to complete.

- [ ] **Step 5: Verify videos in DB**

```bash
docker compose exec -T db psql -U coursepulse -d coursepulse -c "SELECT topic_title, title, similarity_score, play_count FROM video_recommendations ORDER BY similarity_score DESC;"
```

Check that videos are present with reasonable similarity scores.

- [ ] **Step 6: Verify frontend**

Open the document report page. Expand topic cards. Verify that topics with videos show the "相关视频推荐" section with clickable video cards (cover + title + UP + duration + play count). Click a card to confirm it opens Bilibili in a new tab. Verify topics without videos show no video section.

- [ ] **Step 7: Commit any final adjustments**

```bash
git add -A
git commit -m "chore: final adjustments for Slice 2 video recommendations"
```
