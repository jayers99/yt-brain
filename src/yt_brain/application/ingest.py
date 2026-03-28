from __future__ import annotations

from pathlib import Path

from yt_brain.domain.models import EngagementLevel, Video
from yt_brain.infrastructure.database import get_video, save_channel, save_video, update_engagement
from yt_brain.infrastructure.takeout_parser import parse_liked_videos, parse_watch_history
from yt_brain.infrastructure.ytdlp_adapter import extract_video_id, fetch_metadata


def ingest_takeout(db_path: Path, takeout_path: Path) -> int:
    if takeout_path.suffix == ".zip":
        return _ingest_takeout_zip(db_path, takeout_path)

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


def _ingest_takeout_zip(db_path: Path, zip_path: Path) -> int:
    import json
    import zipfile

    from yt_brain.infrastructure.takeout_parser import _parse_watch_entry

    with zipfile.ZipFile(zip_path) as zf:
        # Find watch-history.json in the zip
        watch_file = None
        for name in zf.namelist():
            if name.endswith("watch-history.json"):
                watch_file = name
                break

        if not watch_file:
            raise FileNotFoundError(f"No watch-history.json found in {zip_path}")

        with zf.open(watch_file) as f:
            entries = json.load(f)

    count = 0
    for entry in entries:
        video = _parse_watch_entry(entry)
        if video is not None:
            save_video(db_path, video)
            if video.channel_id:
                # Extract channel URL from raw entry
                channel_url = ""
                subtitles = entry.get("subtitles", [])
                if subtitles:
                    channel_url = subtitles[0].get("url", "")
                save_channel(db_path, video.channel_id, video.channel_id, channel_url)
            count += 1

    return count


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
