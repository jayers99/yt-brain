from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from yt_brain.infrastructure.database import get_all_videos, get_video_count_by_engagement


@dataclass
class StatusSummary:
    total: int = 0
    by_engagement: dict[str, int] = field(default_factory=dict)
    channels: int = 0
    with_transcripts: int = 0


def get_status_summary(db_path: Path) -> StatusSummary:
    counts = get_video_count_by_engagement(db_path)
    total = sum(counts.values())

    videos = get_all_videos(db_path)
    with_transcripts = sum(1 for v in videos if v.transcript)

    return StatusSummary(
        total=total,
        by_engagement=counts,
        with_transcripts=with_transcripts,
    )
