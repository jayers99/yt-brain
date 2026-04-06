"""Test that removed/private videos are filtered from dashboard data."""

from datetime import datetime

from yt_brain.domain.models import Video


def _make_video(youtube_id: str, title: str) -> Video:
    return Video(
        youtube_id=youtube_id,
        title=title,
        channel_id="",
        description="",
        duration_seconds=0,
        watched_at=datetime(2025, 1, 1),
        engagement_level="UNKNOWN",
        source="takeout",
    )


def test_removed_videos_excluded():
    """Videos whose title is a YouTube URL should be filtered out."""
    from yt_brain.web.dashboard import is_removed_video

    removed = _make_video("abc123", "https://www.youtube.com/watch?v=abc123")
    normal = _make_video("def456", "How to Cook Pasta")

    assert is_removed_video(removed) is True
    assert is_removed_video(normal) is False


def test_normal_titles_not_excluded():
    """Titles containing YouTube URLs but not starting with one pass through."""
    from yt_brain.web.dashboard import is_removed_video

    v = _make_video("ghi789", "Check out https://www.youtube.com/watch?v=xyz")
    assert is_removed_video(v) is False
