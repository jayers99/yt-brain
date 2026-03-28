import json
from pathlib import Path

from pytest_bdd import given, parsers, scenarios, then, when

from yt_brain.infrastructure.takeout_parser import parse_liked_videos, parse_watch_history

scenarios("../features/ingest_takeout.feature")


def _make_watch_entry(video_id: str, title: str = "Test", channel: str = "Test Channel", watched_sec: int | None = None, duration_sec: int | None = None) -> dict:
    entry = {
        "header": "YouTube",
        "title": f"Watched {title}",
        "titleUrl": f"https://www.youtube.com/watch?v={video_id}",
        "subtitles": [{"name": channel, "url": f"https://www.youtube.com/channel/UC{video_id}"}],
        "time": "2026-03-20T10:00:00.000Z",
    }
    if duration_sec is not None and watched_sec is not None:
        entry["details"] = [{"name": f"Watched {watched_sec} of {duration_sec} seconds"}]
    return entry


def _make_ad_entry() -> dict:
    return {
        "header": "YouTube",
        "title": "Visited YouTube Music",
        "time": "2026-03-20T09:00:00.000Z",
    }


@given(parsers.parse("a Takeout watch-history.json with {count:d} entries"), target_fixture="takeout_file")
def create_watch_history(tmp_path: Path, count: int) -> Path:
    entries = [_make_watch_entry(f"vid{i}", f"Video {i}") for i in range(count)]
    filepath = tmp_path / "watch-history.json"
    filepath.write_text(json.dumps(entries))
    return filepath


@given(parsers.parse('a Takeout entry for video "{vid}" watched for {watched:d} of {duration:d} seconds'), target_fixture="takeout_file")
def create_entry_with_duration(tmp_path: Path, vid: str, watched: int, duration: int) -> Path:
    entries = [_make_watch_entry(vid, watched_sec=watched, duration_sec=duration)]
    filepath = tmp_path / "watch-history.json"
    filepath.write_text(json.dumps(entries))
    return filepath


@given(parsers.parse("a Takeout watch-history.json with {video_count:d} videos and {ad_count:d} ad"), target_fixture="takeout_file")
def create_mixed_history(tmp_path: Path, video_count: int, ad_count: int) -> Path:
    entries = [_make_watch_entry(f"vid{i}") for i in range(video_count)]
    entries += [_make_ad_entry() for _ in range(ad_count)]
    filepath = tmp_path / "watch-history.json"
    filepath.write_text(json.dumps(entries))
    return filepath


@given(parsers.parse("a Takeout like list with {count:d} entries"), target_fixture="takeout_file")
def create_liked_list(tmp_path: Path, count: int) -> Path:
    entries = [
        {"contentDetails": {"videoId": f"liked{i}"}, "snippet": {"title": f"Liked {i}"}}
        for i in range(count)
    ]
    filepath = tmp_path / "liked-videos.json"
    filepath.write_text(json.dumps(entries))
    return filepath


@when("I parse the takeout file", target_fixture="parsed_videos")
def do_parse(takeout_file: Path):
    return parse_watch_history(takeout_file)


@when("I parse the liked videos file", target_fixture="liked_ids")
def do_parse_liked(takeout_file: Path):
    return parse_liked_videos(takeout_file)


@then(parsers.parse("I get {count:d} videos"))
def check_count(parsed_videos, count: int) -> None:
    assert len(parsed_videos) == count


@then("each video has a youtube_id")
def check_has_id(parsed_videos) -> None:
    for v in parsed_videos:
        assert v.youtube_id


@then(parsers.parse('each video has source "{source}"'))
def check_source(parsed_videos, source: str) -> None:
    from yt_brain.domain.models import Source
    for v in parsed_videos:
        assert v.source == Source(source)


@then(parsers.parse("the video has watched_seconds {seconds:d}"))
def check_watched(parsed_videos, seconds: int) -> None:
    assert parsed_videos[0].watched_seconds == seconds


@then(parsers.parse("the video has duration_seconds {seconds:d}"))
def check_duration(parsed_videos, seconds: int) -> None:
    assert parsed_videos[0].duration_seconds == seconds


@then(parsers.parse("I get {count:d} liked video IDs"))
def check_liked_count(liked_ids, count: int) -> None:
    assert len(liked_ids) == count
