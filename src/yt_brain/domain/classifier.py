from __future__ import annotations

from dataclasses import dataclass

from yt_brain.domain.models import EngagementLevel, Video

DEFAULT_BOUNCE_THRESHOLD = 0.15
DEFAULT_WATCHED_THRESHOLD = 0.85


@dataclass
class ClassificationContext:
    video: Video
    is_liked: bool = False
    is_in_playlist: bool = False
    bounce_threshold: float = DEFAULT_BOUNCE_THRESHOLD
    watched_threshold: float = DEFAULT_WATCHED_THRESHOLD


def classify_video(
    video: Video,
    is_liked: bool = False,
    is_in_playlist: bool = False,
    bounce_threshold: float = DEFAULT_BOUNCE_THRESHOLD,
    watched_threshold: float = DEFAULT_WATCHED_THRESHOLD,
) -> EngagementLevel:
    """Classify a video's engagement level. Highest signal wins."""
    if is_in_playlist:
        return EngagementLevel.CURATED

    if is_liked:
        return EngagementLevel.LIKED

    watch_pct = video.watch_percentage
    if watch_pct is None:
        return EngagementLevel.UNKNOWN

    if watch_pct >= watched_threshold:
        return EngagementLevel.WATCHED

    if watch_pct < bounce_threshold:
        return EngagementLevel.BOUNCED

    return EngagementLevel.UNKNOWN
