from __future__ import annotations

import json
import urllib.request
from collections.abc import Callable
from pathlib import Path
from urllib.error import URLError

from yt_brain.infrastructure.database import (
    bulk_update_liked,
    get_all_video_ids,
    get_videos_missing_category,
    get_videos_missing_channel,
    get_videos_missing_description,
    get_videos_missing_watched_at,
    update_category,
    update_channel_id,
    update_description,
    update_published_at,
    update_watched_at,
)
from yt_brain.infrastructure.ytdlp_adapter import fetch_liked_ids

YOUTUBE_CATEGORIES = {
    "1": "Film & Animation", "2": "Autos & Vehicles", "10": "Music",
    "15": "Pets & Animals", "17": "Sports", "18": "Short Movies",
    "19": "Travel & Events", "20": "Gaming", "21": "Videoblogging",
    "22": "People & Blogs", "23": "Comedy", "24": "Entertainment",
    "25": "News & Politics", "26": "Howto & Style", "27": "Education",
    "28": "Science & Technology", "29": "Nonprofits & Activism",
    "30": "Movies", "35": "Documentary", "42": "Shorts", "43": "Shows",
    "44": "Trailers",
}


def backfill_channels(db_path: Path, video_ids: list[str] | None = None) -> int:
    """Backfill missing channel names via YouTube oEmbed API.

    If video_ids is provided, only backfill those videos.
    Returns the number of channels successfully backfilled.
    """
    missing = get_videos_missing_channel(db_path)
    if video_ids is not None:
        id_set = set(video_ids)
        missing = [(vid, title) for vid, title in missing if vid in id_set]

    filled = 0
    for vid_id, _title in missing:
        try:
            url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={vid_id}&format=json"
            resp = urllib.request.urlopen(url, timeout=10)
            data = json.loads(resp.read())
            name = data.get("author_name", "")
            if name:
                update_channel_id(db_path, vid_id, name)
                filled += 1
        except (URLError, json.JSONDecodeError, TimeoutError):
            pass
    return filled


def backfill_categories(db_path: Path, api_key: str, video_ids: list[str] | None = None) -> int:
    """Backfill missing categories via YouTube Data API.

    If video_ids is provided, only backfill those videos.
    Returns the number of categories successfully backfilled.
    """
    missing = get_videos_missing_category(db_path)
    if video_ids is not None:
        id_set = set(video_ids)
        missing = [vid for vid in missing if vid in id_set]

    filled = 0
    for i in range(0, len(missing), 50):
        batch = missing[i:i + 50]
        ids = ",".join(batch)
        try:
            api_url = (
                f"https://www.googleapis.com/youtube/v3/videos"
                f"?part=snippet&id={ids}&key={api_key}"
            )
            resp = urllib.request.urlopen(api_url, timeout=15)
            data = json.loads(resp.read())
            for item in data.get("items", []):
                cat_id = item["snippet"].get("categoryId", "")
                cat_name = YOUTUBE_CATEGORIES.get(cat_id, "Other")
                update_category(db_path, item["id"], cat_name)
                filled += 1
        except (URLError, json.JSONDecodeError, KeyError):
            pass
    return filled


def backfill_descriptions(
    db_path: Path,
    api_key: str,
    limit: int | None = None,
    on_progress: Callable[..., None] | None = None,
) -> int:
    """Backfill missing video descriptions via YouTube Data API (batches of 50).

    Returns the number of descriptions successfully backfilled.
    """
    missing = get_videos_missing_description(db_path)
    if limit is not None:
        missing = missing[:limit]

    filled = 0
    total = len(missing)
    for i in range(0, total, 50):
        batch = missing[i : i + 50]
        ids = ",".join(batch)
        try:
            api_url = (
                f"https://www.googleapis.com/youtube/v3/videos"
                f"?part=snippet&id={ids}&key={api_key}"
            )
            resp = urllib.request.urlopen(api_url, timeout=15)
            data = json.loads(resp.read())
            for item in data.get("items", []):
                desc = item["snippet"].get("description", "")
                if desc:
                    update_description(db_path, item["id"], desc)
                    filled += 1
        except (URLError, json.JSONDecodeError, KeyError):
            pass
        if on_progress:
            on_progress(min(i + 50, total), total)
    return filled


def backfill_likes(db_path: Path, browser: str = "chrome") -> int:
    """Fetch liked video IDs via yt-dlp and mark them in the database.

    Returns the number of videos marked as liked.
    """
    liked_ids = set(fetch_liked_ids(browser=browser))
    all_ids = get_all_video_ids(db_path)
    matched = liked_ids & all_ids

    if matched:
        liked_map: dict[str, str | None] = {vid: "like" for vid in matched}
        bulk_update_liked(db_path, liked_map)

    return len(matched)


def backfill_dates(db_path: Path, api_key: str, video_ids: list[str] | None = None) -> int:
    """Backfill missing watched_at dates via YouTube Data API.

    If video_ids is provided, only backfill those videos.
    Returns the number of dates successfully backfilled.
    """
    missing = get_videos_missing_watched_at(db_path)
    if video_ids is not None:
        id_set = set(video_ids)
        missing = [vid for vid in missing if vid in id_set]

    filled = 0
    for i in range(0, len(missing), 50):
        batch = missing[i:i + 50]
        ids = ",".join(batch)
        try:
            api_url = (
                f"https://www.googleapis.com/youtube/v3/videos"
                f"?part=snippet&id={ids}&key={api_key}"
            )
            resp = urllib.request.urlopen(api_url, timeout=15)
            data = json.loads(resp.read())
            for item in data.get("items", []):
                published = item["snippet"].get("publishedAt", "")
                if published:
                    update_watched_at(db_path, item["id"], published)
                    update_published_at(db_path, item["id"], published)
                    filled += 1
        except (URLError, json.JSONDecodeError, KeyError):
            pass
    return filled
