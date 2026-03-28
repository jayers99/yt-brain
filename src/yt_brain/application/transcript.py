from __future__ import annotations

from pathlib import Path

from yt_brain.domain.errors import VideoNotFoundError
from yt_brain.domain.models import EngagementLevel
from yt_brain.infrastructure.database import get_video, get_videos_by_engagement, save_video
from yt_brain.infrastructure.ytdlp_adapter import fetch_transcript


def fetch_video_transcript(db_path: Path, video_id: str, language: str = "en") -> str | None:
    video = get_video(db_path, video_id)
    if video is None:
        raise VideoNotFoundError(f"Video not found: {video_id}")

    if video.transcript:
        return video.transcript

    transcript = fetch_transcript(video_id, language)
    if transcript:
        video.transcript = transcript
        save_video(db_path, video)

    return transcript


def fetch_transcripts_by_level(
    db_path: Path,
    level: EngagementLevel,
    language: str = "en",
) -> dict[str, bool]:
    videos = get_videos_by_engagement(db_path, level)
    results: dict[str, bool] = {}

    for video in videos:
        if video.transcript:
            results[video.youtube_id] = True
            continue

        transcript = fetch_transcript(video.youtube_id, language)
        if transcript:
            video.transcript = transcript
            save_video(db_path, video)
            results[video.youtube_id] = True
        else:
            results[video.youtube_id] = False

    return results
