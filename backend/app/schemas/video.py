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
