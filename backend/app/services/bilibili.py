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
