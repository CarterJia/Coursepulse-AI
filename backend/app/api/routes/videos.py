import uuid
from collections import defaultdict

from fastapi import APIRouter, Depends
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
