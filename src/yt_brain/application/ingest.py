from __future__ import annotations

from pathlib import Path

from yt_brain.domain.models import EngagementLevel, Video
from yt_brain.infrastructure.database import get_video, save_channel, save_video, update_engagement
from yt_brain.infrastructure.takeout_parser import parse_liked_videos, parse_watch_history
from yt_brain.infrastructure.ytdlp_adapter import extract_video_id, fetch_metadata


def ingest_takeout(db_path: Path, takeout_path: Path) -> int:
    watch_history_file = _find_watch_history(takeout_path)
    videos = parse_watch_history(watch_history_file)

    count = 0
    for video in videos:
        save_video(db_path, video)
        if video.channel_id:
            save_channel(db_path, video.channel_id, video.channel_id)
        count += 1

    liked_file = takeout_path / "YouTube and YouTube Music" / "playlists" / "Liked videos.json"
    if not liked_file.exists():
        liked_file = takeout_path / "liked-videos.json"
    if liked_file.exists():
        liked_ids = parse_liked_videos(liked_file)
        for vid_id in liked_ids:
            existing = get_video(db_path, vid_id)
            if existing is not None:
                update_engagement(db_path, vid_id, EngagementLevel.LIKED)

    return count


def ingest_video(db_path: Path, url: str) -> Video:
    video_id = extract_video_id(url)

    existing = get_video(db_path, video_id)
    if existing is not None:
        return existing

    video = fetch_metadata(video_id)
    save_video(db_path, video)

    if video.channel_id:
        save_channel(db_path, video.channel_id, video.title)

    return video


def _find_watch_history(takeout_path: Path) -> Path:
    candidates = [
        takeout_path / "YouTube and YouTube Music" / "history" / "watch-history.json",
        takeout_path / "watch-history.json",
        takeout_path,
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(f"Could not find watch-history.json in {takeout_path}")
