from __future__ import annotations

from pathlib import Path

from yt_brain.domain.models import EngagementLevel, Video
from yt_brain.infrastructure.database import get_all_videos, get_videos_by_engagement, update_engagement


def get_review_list(
    db_path: Path,
    level: EngagementLevel | None = None,
) -> list[Video]:
    if level is not None:
        return get_videos_by_engagement(db_path, level)
    return get_all_videos(db_path)


def override_engagement(db_path: Path, youtube_id: str, level: EngagementLevel) -> None:
    update_engagement(db_path, youtube_id, level, is_override=True)
