from unittest.mock import patch, MagicMock

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
