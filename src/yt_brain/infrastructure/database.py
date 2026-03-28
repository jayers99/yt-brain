from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path

from yt_brain.domain.errors import DatabaseError
from yt_brain.domain.models import EngagementLevel, Source, Video


def init_db(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    try:
        migration_file = Path(__file__).parent.parent.parent.parent / "migrations" / "001_initial_schema.sql"
        if not migration_file.exists():
            raise DatabaseError(f"Migration file not found: {migration_file}")

        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='schema_version'")
        if cursor.fetchone() is not None:
            return

        sql = migration_file.read_text()
        conn.executescript(sql)
    finally:
        conn.close()


def save_video(db_path: Path, video: Video) -> None:
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            """INSERT INTO videos (youtube_id, title, description, channel_id, duration_seconds,
                watched_seconds, watched_at, engagement_level, engagement_override,
                transcript, tags, source, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
            ON CONFLICT(youtube_id) DO UPDATE SET
                title=excluded.title, description=excluded.description,
                channel_id=excluded.channel_id, duration_seconds=excluded.duration_seconds,
                watched_seconds=excluded.watched_seconds, watched_at=excluded.watched_at,
                engagement_level=excluded.engagement_level,
                engagement_override=excluded.engagement_override,
                transcript=excluded.transcript, tags=excluded.tags,
                source=excluded.source, updated_at=datetime('now')""",
            (
                video.youtube_id,
                video.title,
                video.description,
                video.channel_id,
                video.duration_seconds,
                video.watched_seconds,
                video.watched_at.isoformat() if video.watched_at else None,
                video.engagement_level.value,
                video.engagement_override.value if video.engagement_override else None,
                video.transcript,
                json.dumps(video.tags),
                video.source.value,
            ),
        )
        conn.commit()
    finally:
        conn.close()


def get_video(db_path: Path, youtube_id: str) -> Video | None:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        cursor = conn.execute("SELECT * FROM videos WHERE youtube_id = ?", (youtube_id,))
        row = cursor.fetchone()
        if row is None:
            return None
        return _row_to_video(row)
    finally:
        conn.close()


def get_videos_by_engagement(db_path: Path, level: EngagementLevel) -> list[Video]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        cursor = conn.execute("SELECT * FROM videos WHERE engagement_level = ?", (level.value,))
        return [_row_to_video(row) for row in cursor.fetchall()]
    finally:
        conn.close()


def get_all_videos(db_path: Path) -> list[Video]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        cursor = conn.execute("SELECT * FROM videos ORDER BY watched_at DESC")
        return [_row_to_video(row) for row in cursor.fetchall()]
    finally:
        conn.close()


def get_video_count_by_engagement(db_path: Path) -> dict[str, int]:
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.execute("SELECT engagement_level, COUNT(*) FROM videos GROUP BY engagement_level")
        return dict(cursor.fetchall())
    finally:
        conn.close()


def update_engagement(db_path: Path, youtube_id: str, level: EngagementLevel, is_override: bool = False) -> None:
    conn = sqlite3.connect(db_path)
    try:
        if is_override:
            conn.execute(
                "UPDATE videos SET engagement_override = ?, updated_at = datetime('now') WHERE youtube_id = ?",
                (level.value, youtube_id),
            )
        else:
            conn.execute(
                "UPDATE videos SET engagement_level = ?, updated_at = datetime('now') WHERE youtube_id = ?",
                (level.value, youtube_id),
            )
        conn.commit()
    finally:
        conn.close()


def save_channel(db_path: Path, channel_id: str, name: str, url: str = "", subscribed: bool = False) -> None:
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            """INSERT INTO channels (youtube_id, name, url, subscription_status)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(youtube_id) DO UPDATE SET
                name=excluded.name, url=excluded.url,
                subscription_status=excluded.subscription_status""",
            (channel_id, name, url, int(subscribed)),
        )
        conn.commit()
    finally:
        conn.close()


def is_video_in_playlist(db_path: Path, youtube_id: str) -> bool:
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.execute(
            "SELECT 1 FROM playlist_videos pv JOIN playlists p ON pv.playlist_id = p.youtube_id "
            "WHERE pv.video_id = ? AND p.is_user_created = 1",
            (youtube_id,),
        )
        return cursor.fetchone() is not None
    finally:
        conn.close()


def is_video_liked(db_path: Path, youtube_id: str) -> bool:
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.execute("SELECT 1 FROM videos WHERE youtube_id = ? AND engagement_level = 'LIKED'", (youtube_id,))
        return cursor.fetchone() is not None
    finally:
        conn.close()


def _row_to_video(row: sqlite3.Row) -> Video:
    return Video(
        youtube_id=row["youtube_id"],
        title=row["title"],
        description=row["description"],
        channel_id=row["channel_id"],
        duration_seconds=row["duration_seconds"],
        watched_seconds=row["watched_seconds"],
        watched_at=datetime.fromisoformat(row["watched_at"]) if row["watched_at"] else None,
        engagement_level=EngagementLevel(row["engagement_level"]),
        engagement_override=EngagementLevel(row["engagement_override"]) if row["engagement_override"] else None,
        transcript=row["transcript"],
        tags=json.loads(row["tags"]),
        source=Source(row["source"]),
    )
