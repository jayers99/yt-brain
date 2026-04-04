from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

from yt_brain.application.backfill import backfill_categories, backfill_channels, backfill_dates, backfill_likes
from yt_brain.infrastructure.database import get_existing_video_ids, get_existing_video_watched_at, save_video, update_watched_at
from yt_brain.infrastructure.ytdlp_adapter import fetch_history_range, parse_ytdlp_metadata


@dataclass
class SyncResult:
    new_videos: int
    rewatched_videos: int
    channels_backfilled: int
    categories_backfilled: int
    dates_backfilled: int
    likes_synced: int


def sync_videos(
    db_path: Path,
    browser: str = "chrome",
    batch_size: int = 200,
    api_key: str | None = None,
) -> SyncResult:
    """Fetch recent YouTube history and add new videos to the database.

    Fetches in batches. Stops when an entire batch consists of videos
    already in the database with no position change (i.e. no re-watches).
    Updates watched_at for re-watched videos that appear near the top
    of the history feed.
    """
    all_new_ids: list[str] = []
    rewatched_ids: list[str] = []
    start = 1
    now = datetime.now(timezone.utc)

    while True:
        end = start + batch_size - 1
        entries = fetch_history_range(start, end, browser)

        if not entries:
            break

        # Check which videos are new
        batch_ids = [e.get("id", "") for e in entries if e.get("id")]
        existing = get_existing_video_ids(db_path, batch_ids)
        new_ids = [vid for vid in batch_ids if vid not in existing]

        # Update watched_at only for videos genuinely re-watched since
        # the last sync.  A video counts as re-watched if its stored
        # watched_at is more than 24 hours old — recent timestamps are
        # just artifacts of the previous sync run.
        if start == 1:
            existing_timestamps = get_existing_video_watched_at(db_path, batch_ids)
            cutoff = (now - timedelta(hours=24)).isoformat()
            for i, vid_id in enumerate(batch_ids):
                if vid_id in existing_timestamps:
                    old_ts = existing_timestamps[vid_id]
                    if old_ts is None or old_ts < cutoff:
                        ts = (now - timedelta(seconds=i)).isoformat()
                        update_watched_at(db_path, vid_id, ts)
                        rewatched_ids.append(vid_id)

        if not new_ids:
            # Entire batch already known — stop
            break

        # Save new videos
        entries_by_id = {e["id"]: e for e in entries if e.get("id")}
        for vid_id in new_ids:
            video = parse_ytdlp_metadata(entries_by_id[vid_id])
            save_video(db_path, video)
            all_new_ids.append(vid_id)

        # If batch had some new, keep fetching
        if len(entries) < batch_size:
            break

        start += batch_size

    # Backfill metadata for new videos only
    channels_filled = backfill_channels(db_path, video_ids=all_new_ids) if all_new_ids else 0
    categories_filled = backfill_categories(db_path, api_key, video_ids=all_new_ids) if all_new_ids and api_key else 0
    dates_filled = backfill_dates(db_path, api_key, video_ids=all_new_ids) if all_new_ids and api_key else 0
    likes_filled = backfill_likes(db_path, browser=browser)

    return SyncResult(
        new_videos=len(all_new_ids),
        rewatched_videos=len(rewatched_ids),
        channels_backfilled=channels_filled,
        categories_backfilled=categories_filled,
        dates_backfilled=dates_filled,
        likes_synced=likes_filled,
    )
