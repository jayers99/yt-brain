from unittest.mock import MagicMock, patch

from yt_brain.domain.models import Video
from yt_brain.infrastructure.database import save_video


def test_backfill_channels_fills_missing(temp_db):
    from yt_brain.application.backfill import backfill_channels

    v = Video(youtube_id="abc123", title="Test Video", channel_id="")
    save_video(temp_db, v)

    mock_resp = MagicMock()
    mock_resp.read.return_value = b'{"author_name": "Test Channel"}'
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = lambda s, *a: None
    with patch("yt_brain.application.backfill.urllib.request.urlopen", return_value=mock_resp):
        result = backfill_channels(temp_db)

    assert result == 1


def test_backfill_channels_scoped_to_video_ids(temp_db):
    from yt_brain.application.backfill import backfill_channels

    v1 = Video(youtube_id="aaa", title="V1", channel_id="")
    v2 = Video(youtube_id="bbb", title="V2", channel_id="")
    save_video(temp_db, v1)
    save_video(temp_db, v2)

    mock_resp = MagicMock()
    mock_resp.read.return_value = b'{"author_name": "Channel"}'
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = lambda s, *a: None
    with patch("yt_brain.application.backfill.urllib.request.urlopen", return_value=mock_resp):
        result = backfill_channels(temp_db, video_ids=["aaa"])

    assert result == 1


def test_fetch_liked_ids(temp_db):
    from unittest.mock import MagicMock, patch

    from yt_brain.infrastructure.ytdlp_adapter import fetch_liked_ids

    fake_output = "abc123\ndef456\nghi789\n"
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = fake_output

    with patch("yt_brain.infrastructure.ytdlp_adapter.subprocess.run", return_value=mock_result):
        ids = fetch_liked_ids(browser="chrome")

    assert ids == ["abc123", "def456", "ghi789"]


def test_backfill_likes_marks_liked_videos(temp_db):
    from yt_brain.application.backfill import backfill_likes
    from yt_brain.infrastructure.database import save_video

    # Create 3 videos in DB
    for vid_id in ["vid1", "vid2", "vid3"]:
        save_video(temp_db, Video(youtube_id=vid_id, title=f"V {vid_id}", channel_id="ch"))

    # yt-dlp says vid1 and vid3 are liked
    with patch("yt_brain.application.backfill.fetch_liked_ids", return_value=["vid1", "vid3", "vid_not_in_db"]):
        count = backfill_likes(temp_db, browser="chrome")

    assert count == 2

    import sqlite3
    conn = sqlite3.connect(temp_db)
    rows = {r[0]: r[1] for r in conn.execute("SELECT youtube_id, liked FROM videos WHERE youtube_id IN ('vid1','vid2','vid3')").fetchall()}
    conn.close()
    assert rows["vid1"] == "like"
    assert rows["vid2"] is None
    assert rows["vid3"] == "like"


def test_backfill_dates_populates_published_at(temp_db):
    from yt_brain.application.backfill import backfill_dates
    from yt_brain.infrastructure.database import save_video

    v = Video(youtube_id="pub1", title="Pub Video", channel_id="ch")
    save_video(temp_db, v)

    import json
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps({
        "items": [{"id": "pub1", "snippet": {"publishedAt": "2024-03-15T12:00:00Z"}}]
    }).encode()
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = lambda s, *a: None

    with patch("yt_brain.application.backfill.urllib.request.urlopen", return_value=mock_resp):
        backfill_dates(temp_db, "test-key")

    import sqlite3
    conn = sqlite3.connect(temp_db)
    row = conn.execute("SELECT published_at FROM videos WHERE youtube_id = 'pub1'").fetchone()
    conn.close()
    assert row[0] == "2024-03-15T12:00:00Z"
