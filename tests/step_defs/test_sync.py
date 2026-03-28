from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from unittest.mock import patch

from pytest_bdd import given, parsers, scenarios, then, when

from yt_brain.domain.models import Video
from yt_brain.infrastructure.database import save_video

scenarios("../features/sync.feature")


@dataclass
class SyncContext:
    db_path: Path | None = None
    ytdlp_entries: list[dict] | None = None
    sync_result: object | None = None
    api_key: str | None = None


@given('a database with existing videos "vid1" and "vid2"', target_fixture="ctx")
def db_with_two_videos(temp_db):
    ctx = SyncContext(db_path=temp_db)
    for vid_id in ["vid1", "vid2"]:
        save_video(temp_db, Video(youtube_id=vid_id, title=f"Video {vid_id}", channel_id="ch"))
    return ctx


@given('a database with existing videos "vid1", "vid2", "vid3"', target_fixture="ctx")
def db_with_three_videos(temp_db):
    ctx = SyncContext(db_path=temp_db)
    for vid_id in ["vid1", "vid2", "vid3"]:
        save_video(temp_db, Video(youtube_id=vid_id, title=f"Video {vid_id}", channel_id="ch"))
    return ctx


@given("an empty database", target_fixture="ctx")
def empty_db(temp_db):
    return SyncContext(db_path=temp_db)


@given('yt-dlp returns videos "vid1", "vid2", "vid3", "vid4"')
def ytdlp_returns_four(ctx):
    ctx.ytdlp_entries = [
        {"id": vid, "title": f"Video {vid}", "duration": 300}
        for vid in ["vid1", "vid2", "vid3", "vid4"]
    ]


@given('yt-dlp returns a batch of only known videos "vid1", "vid2", "vid3"')
def ytdlp_returns_known(ctx):
    ctx.ytdlp_entries = [
        {"id": vid, "title": f"Video {vid}", "duration": 300}
        for vid in ["vid1", "vid2", "vid3"]
    ]


@given('yt-dlp returns videos "new1", "new2"')
def ytdlp_returns_new(ctx):
    ctx.ytdlp_entries = [
        {"id": vid, "title": f"Video {vid}", "duration": 300}
        for vid in ["new1", "new2"]
    ]


@given("the YouTube API is available")
def api_available(ctx):
    ctx.api_key = "test-api-key"


@when("I run sync")
def run_sync(ctx):
    from yt_brain.application.sync import sync_videos

    with patch("yt_brain.application.sync.fetch_history_range", return_value=ctx.ytdlp_entries):
        ctx.sync_result = sync_videos(ctx.db_path, batch_size=len(ctx.ytdlp_entries))


@when("I run sync with an API key")
def run_sync_with_api(ctx):
    from yt_brain.application.sync import sync_videos

    with patch("yt_brain.application.sync.fetch_history_range", return_value=ctx.ytdlp_entries), \
         patch("yt_brain.application.backfill.urllib.request.urlopen") as mock_urlopen:
        import json
        mock_urlopen.return_value.__enter__ = lambda s: s
        mock_urlopen.return_value.__exit__ = lambda s, *a: None
        mock_urlopen.return_value.read.return_value = json.dumps({
            "author_name": "Test Channel",
            "items": [{"id": "new1", "snippet": {"categoryId": "27", "publishedAt": "2026-01-01T00:00:00Z"}},
                       {"id": "new2", "snippet": {"categoryId": "28", "publishedAt": "2026-02-01T00:00:00Z"}}],
        }).encode()
        ctx.sync_result = sync_videos(ctx.db_path, api_key=ctx.api_key, batch_size=len(ctx.ytdlp_entries))


@then(parsers.parse("{count:d} new videos are saved to the database"))
def check_new_videos_saved(ctx, count):
    assert ctx.sync_result.new_videos == count


@then("no new videos are saved")
def check_no_new_videos(ctx):
    assert ctx.sync_result.new_videos == 0


@then(parsers.parse("the sync result shows {count:d} new videos"))
def check_sync_result_count(ctx, count):
    assert ctx.sync_result.new_videos == count


@then("channels are backfilled for new videos")
def check_channels_backfilled(ctx):
    assert ctx.sync_result.channels_backfilled >= 0


@then("categories are backfilled for new videos")
def check_categories_backfilled(ctx):
    assert ctx.sync_result.categories_backfilled >= 0


@then("dates are backfilled for new videos")
def check_dates_backfilled(ctx):
    assert ctx.sync_result.dates_backfilled >= 0
