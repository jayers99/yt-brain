from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path

from yt_brain.domain.errors import DatabaseError
from yt_brain.domain.models import EngagementLevel, Source, Video


def _load_sqlite_vec(conn: sqlite3.Connection) -> None:
    """Load the sqlite-vec extension into a connection."""
    import sqlite_vec

    conn.enable_load_extension(True)
    sqlite_vec.load(conn)
    conn.enable_load_extension(False)


# Migrations that require sqlite-vec loaded before they can run.
_VEC_MIGRATIONS = {4}


def init_db(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    try:
        migrations_dir = Path(__file__).parent.parent.parent.parent / "migrations"

        # Check if schema_version exists
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='schema_version'")
        if cursor.fetchone() is None:
            # Fresh DB — run initial migration
            sql = (migrations_dir / "001_initial_schema.sql").read_text()
            conn.executescript(sql)

        # Run any pending migrations
        cursor = conn.execute("SELECT MAX(version) FROM schema_version")
        current_version = cursor.fetchone()[0] or 0

        for mig_file in sorted(migrations_dir.glob("*.sql")):
            # Extract version number from filename (e.g., 002_starred_channels.sql -> 2)
            version = int(mig_file.name.split("_")[0])
            if version > current_version:
                if version in _VEC_MIGRATIONS:
                    _load_sqlite_vec(conn)
                conn.executescript(mig_file.read_text())
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


def get_videos_missing_channel(db_path: Path) -> list[tuple[str, str]]:
    """Return (youtube_id, title) for videos with empty channel_id."""
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.execute(
            "SELECT youtube_id, title FROM videos WHERE channel_id = '' OR channel_id IS NULL"
        )
        return cursor.fetchall()
    finally:
        conn.close()


def update_channel_id(db_path: Path, youtube_id: str, channel_id: str) -> None:
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            "UPDATE videos SET channel_id = ?, updated_at = datetime('now') WHERE youtube_id = ?",
            (channel_id, youtube_id),
        )
        conn.commit()
    finally:
        conn.close()


def get_videos_missing_watched_at(db_path: Path) -> list[str]:
    """Return youtube_ids for videos with no watched_at date."""
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.execute("SELECT youtube_id FROM videos WHERE watched_at IS NULL")
        return [row[0] for row in cursor.fetchall()]
    finally:
        conn.close()


def update_watched_at(db_path: Path, youtube_id: str, watched_at: str) -> None:
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            "UPDATE videos SET watched_at = ?, updated_at = datetime('now') WHERE youtube_id = ?",
            (watched_at, youtube_id),
        )
        conn.commit()
    finally:
        conn.close()


def get_videos_missing_category(db_path: Path) -> list[str]:
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.execute("SELECT youtube_id FROM videos WHERE category = ''")
        return [row[0] for row in cursor.fetchall()]
    finally:
        conn.close()


def update_category(db_path: Path, youtube_id: str, category: str) -> None:
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("UPDATE videos SET category = ? WHERE youtube_id = ?", (category, youtube_id))
        conn.commit()
    finally:
        conn.close()


def get_existing_video_ids(db_path: Path, youtube_ids: list[str]) -> set[str]:
    """Return the subset of youtube_ids that already exist in the database."""
    if not youtube_ids:
        return set()
    conn = sqlite3.connect(db_path)
    try:
        placeholders = ",".join("?" * len(youtube_ids))
        cursor = conn.execute(
            f"SELECT youtube_id FROM videos WHERE youtube_id IN ({placeholders})",
            youtube_ids,
        )
        return {row[0] for row in cursor.fetchall()}
    finally:
        conn.close()


def get_channel_urls(db_path: Path) -> dict[str, str]:
    """Return {channel_name: youtube_url} for channels with URLs."""
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.execute("SELECT youtube_id, url FROM channels WHERE url != ''")
        return {row[0]: row[1] for row in cursor.fetchall()}
    finally:
        conn.close()


def get_starred_channels(db_path: Path) -> set[str]:
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.execute("SELECT channel_name FROM starred_channels")
        return {row[0] for row in cursor.fetchall()}
    finally:
        conn.close()


def toggle_starred_channel(db_path: Path, channel_name: str) -> bool:
    """Toggle star status. Returns True if now starred, False if unstarred."""
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.execute("SELECT 1 FROM starred_channels WHERE channel_name = ?", (channel_name,))
        if cursor.fetchone():
            conn.execute("DELETE FROM starred_channels WHERE channel_name = ?", (channel_name,))
            conn.commit()
            return False
        else:
            conn.execute("INSERT INTO starred_channels (channel_name) VALUES (?)", (channel_name,))
            conn.commit()
            return True
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


def get_videos_missing_description(db_path: Path) -> list[str]:
    """Return youtube_ids for videos with empty descriptions."""
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.execute("SELECT youtube_id FROM videos WHERE description = '' OR description IS NULL")
        return [row[0] for row in cursor.fetchall()]
    finally:
        conn.close()


def update_description(db_path: Path, youtube_id: str, description: str) -> None:
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            "UPDATE videos SET description = ?, updated_at = datetime('now') WHERE youtube_id = ?",
            (description, youtube_id),
        )
        conn.commit()
    finally:
        conn.close()


def is_video_liked(db_path: Path, youtube_id: str) -> bool:
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.execute("SELECT 1 FROM videos WHERE youtube_id = ? AND engagement_level = 'LIKED'", (youtube_id,))
        return cursor.fetchone() is not None
    finally:
        conn.close()


def get_videos_for_embedding(db_path: Path, rebuild: bool = False) -> list[tuple[str, str, str]]:
    """Return (youtube_id, title, description) for videos needing embeddings.

    If rebuild=True, returns all videos. Otherwise only those not in video_embeddings.
    """
    conn = sqlite3.connect(db_path)
    _load_sqlite_vec(conn)
    try:
        if rebuild:
            cursor = conn.execute("SELECT youtube_id, title, description FROM videos")
        else:
            cursor = conn.execute(
                "SELECT v.youtube_id, v.title, v.description FROM videos v "
                "WHERE v.youtube_id NOT IN (SELECT youtube_id FROM video_embeddings)"
            )
        return cursor.fetchall()
    finally:
        conn.close()


def insert_embeddings(db_path: Path, rows: list[tuple[str, bytes]]) -> None:
    """Insert (youtube_id, embedding_bytes) into video_embeddings."""
    conn = sqlite3.connect(db_path)
    _load_sqlite_vec(conn)
    try:
        conn.executemany(
            "INSERT OR REPLACE INTO video_embeddings (youtube_id, embedding) VALUES (?, ?)",
            rows,
        )
        conn.commit()
    finally:
        conn.close()


def search_similar(db_path: Path, query_embedding: bytes, limit: int = 20) -> list[tuple[str, float]]:
    """Return (youtube_id, distance) for nearest neighbors."""
    conn = sqlite3.connect(db_path)
    _load_sqlite_vec(conn)
    try:
        cursor = conn.execute(
            "SELECT youtube_id, distance FROM video_embeddings "
            "WHERE embedding MATCH ? ORDER BY distance LIMIT ?",
            (query_embedding, limit),
        )
        return cursor.fetchall()
    finally:
        conn.close()


def get_embedding_count(db_path: Path) -> int:
    conn = sqlite3.connect(db_path)
    _load_sqlite_vec(conn)
    try:
        cursor = conn.execute("SELECT COUNT(*) FROM video_embeddings")
        return cursor.fetchone()[0]
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
        category=row["category"] if "category" in row.keys() else "",
    )
