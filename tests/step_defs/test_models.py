from pytest_bdd import given, parsers, scenarios, then, when

scenarios("../features/models.feature")


@given(parsers.parse('a video with youtube_id "{youtube_id}" and duration {duration:d}'), target_fixture="video")
def create_video(youtube_id: str, duration: int):
    from yt_brain.domain.models import EngagementLevel, Source, Video

    return Video(
        youtube_id=youtube_id,
        title="Test Video",
        channel_id="ch1",
        duration_seconds=duration,
        engagement_level=EngagementLevel.UNKNOWN,
        source=Source.MANUAL,
    )


@when(parsers.parse("the video watched_seconds is {seconds:d}"))
def set_watched(video, seconds: int):
    video.watched_seconds = seconds


@then(parsers.parse('the video engagement_level is "{level}"'))
def check_engagement(video, level: str):
    from yt_brain.domain.models import EngagementLevel

    assert video.engagement_level == EngagementLevel(level)


@then(parsers.parse('the video source is "{source}"'))
def check_source(video, source: str):
    from yt_brain.domain.models import Source

    assert video.source == Source(source)


@then(parsers.parse("{higher} is higher than {lower}"))
def check_ordering(higher: str, lower: str):
    from yt_brain.domain.models import EngagementLevel

    level_order = [EngagementLevel.UNKNOWN, EngagementLevel.BOUNCED, EngagementLevel.WATCHED, EngagementLevel.LIKED, EngagementLevel.CURATED]
    higher_idx = level_order.index(EngagementLevel(higher))
    lower_idx = level_order.index(EngagementLevel(lower))
    assert higher_idx > lower_idx
