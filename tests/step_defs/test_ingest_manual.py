from pytest_bdd import given, parsers, scenarios, then, when

from yt_brain.infrastructure.ytdlp_adapter import extract_video_id, parse_ytdlp_metadata

scenarios("../features/ingest_manual.feature")


@given(parsers.parse('a YouTube URL "{url}"'), target_fixture="url")
def youtube_url(url: str) -> str:
    return url


@given(parsers.parse('yt-dlp metadata JSON for video "{vid}"'), target_fixture="metadata_json")
def metadata_json(vid: str) -> dict:
    return {
        "id": vid,
        "title": "Test Title",
        "description": "Test description",
        "duration": 300,
        "channel_id": "UCtest",
        "channel": "Test Channel",
        "uploader_url": "https://www.youtube.com/channel/UCtest",
        "tags": ["test", "example"],
    }


@when("I extract the video ID", target_fixture="extracted_id")
def do_extract(url: str) -> str:
    return extract_video_id(url)


@when("I parse the metadata", target_fixture="parsed_video")
def do_parse(metadata_json: dict):
    return parse_ytdlp_metadata(metadata_json)


@then(parsers.parse('the ID is "{vid}"'))
def check_id(extracted_id: str, vid: str) -> None:
    assert extracted_id == vid


@then(parsers.parse('the video title is "{title}"'))
def check_title(parsed_video, title: str) -> None:
    assert parsed_video.title == title


@then(parsers.parse("the video duration is {duration:d}"))
def check_duration(parsed_video, duration: int) -> None:
    assert parsed_video.duration_seconds == duration


@then(parsers.parse('the video channel_id is "{channel_id}"'))
def check_channel(parsed_video, channel_id: str) -> None:
    assert parsed_video.channel_id == channel_id
