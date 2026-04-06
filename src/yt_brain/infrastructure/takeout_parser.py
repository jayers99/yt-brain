from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from yt_brain.domain.errors import IngestError
from yt_brain.domain.models import Source, Video


def parse_watch_history(filepath: Path) -> list[Video]:
    if not filepath.exists():
        raise IngestError(f"Watch history file not found: {filepath}")

    with open(filepath) as f:
        entries = json.load(f)

    videos = []
    for entry in entries:
        video = _parse_watch_entry(entry)
        if video is not None:
            videos.append(video)

    return videos


def parse_liked_videos(filepath: Path) -> list[str]:
    if not filepath.exists():
        raise IngestError(f"Liked videos file not found: {filepath}")

    with open(filepath) as f:
        entries = json.load(f)

    video_ids = []
    for entry in entries:
        content = entry.get("contentDetails", {})
        video_id = content.get("videoId")
        if video_id:
            video_ids.append(video_id)

    return video_ids


def _parse_watch_entry(entry: dict[str, Any]) -> Video | None:
    title_url = entry.get("titleUrl", "")
    if not title_url or "watch?v=" not in title_url:
        return None

    video_id = _extract_video_id(title_url)
    if not video_id:
        return None

    raw_title = entry.get("title", "")
    title = raw_title.removeprefix("Watched ")

    channel_id = ""
    channel_name = ""
    subtitles = entry.get("subtitles", [])
    if subtitles:
        sub = subtitles[0]
        channel_name = sub.get("name", "")
        channel_url = sub.get("url", "")
        if "/channel/" in channel_url:
            channel_id = channel_url.split("/channel/")[-1]

    watched_at = None
    time_str = entry.get("time")
    if time_str:
        watched_at = datetime.fromisoformat(time_str.replace("Z", "+00:00"))

    watched_seconds = None
    duration_seconds = 0
    details = entry.get("details", [])
    for detail in details:
        name = detail.get("name", "")
        match = re.match(r"Watched (\d+) of (\d+) seconds", name)
        if match:
            watched_seconds = int(match.group(1))
            duration_seconds = int(match.group(2))

    return Video(
        youtube_id=video_id,
        title=title,
        channel_id=channel_name or channel_id,
        duration_seconds=duration_seconds,
        watched_seconds=watched_seconds,
        watched_at=watched_at,
        source=Source.TAKEOUT,
    )


def _extract_video_id(url: str) -> str | None:
    parsed = urlparse(url)
    params = parse_qs(parsed.query)
    ids = params.get("v")
    if ids:
        return ids[0]
    return None
