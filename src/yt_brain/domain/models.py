from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class EngagementLevel(StrEnum):
    UNKNOWN = "UNKNOWN"
    BOUNCED = "BOUNCED"
    WATCHED = "WATCHED"
    LIKED = "LIKED"
    CURATED = "CURATED"


ENGAGEMENT_ORDER = [
    EngagementLevel.UNKNOWN,
    EngagementLevel.BOUNCED,
    EngagementLevel.WATCHED,
    EngagementLevel.LIKED,
    EngagementLevel.CURATED,
]


class Source(StrEnum):
    API = "api"
    TAKEOUT = "takeout"
    MANUAL = "manual"


class Video(BaseModel):
    youtube_id: str
    title: str
    description: str = ""
    channel_id: str
    duration_seconds: int = 0
    watched_seconds: int | None = None
    watched_at: datetime | None = None
    engagement_level: EngagementLevel = EngagementLevel.UNKNOWN
    engagement_override: EngagementLevel | None = None
    transcript: str | None = None
    tags: list[str] = Field(default_factory=list)
    source: Source = Source.MANUAL
    category: str = ""

    @property
    def effective_engagement(self) -> EngagementLevel:
        return self.engagement_override if self.engagement_override is not None else self.engagement_level

    @property
    def watch_percentage(self) -> float | None:
        if self.watched_seconds is None or self.duration_seconds == 0:
            return None
        return self.watched_seconds / self.duration_seconds


class Channel(BaseModel):
    youtube_id: str
    name: str
    url: str = ""
    subscription_status: bool = False


class Playlist(BaseModel):
    youtube_id: str
    title: str
    is_user_created: bool = True
    video_ids: list[str] = Field(default_factory=list)
