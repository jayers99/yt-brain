from __future__ import annotations

from pathlib import Path

from yt_brain.domain.classifier import classify_video
from yt_brain.domain.models import EngagementLevel
from yt_brain.infrastructure.database import (
    get_all_videos,
    is_video_in_playlist,
    is_video_liked,
    update_engagement,
)


def classify_all(
    db_path: Path,
    reclassify: bool = False,
    bounce_threshold: float = 0.15,
    watched_threshold: float = 0.85,
) -> dict[str, int]:
    videos = get_all_videos(db_path)
    counts: dict[str, int] = {}

    for video in videos:
        if not reclassify and video.engagement_level != EngagementLevel.UNKNOWN:
            continue

        is_liked = is_video_liked(db_path, video.youtube_id)
        in_playlist = is_video_in_playlist(db_path, video.youtube_id)

        level = classify_video(
            video=video,
            is_liked=is_liked,
            is_in_playlist=in_playlist,
            bounce_threshold=bounce_threshold,
            watched_threshold=watched_threshold,
        )

        update_engagement(db_path, video.youtube_id, level)
        counts[level.value] = counts.get(level.value, 0) + 1

    return counts
