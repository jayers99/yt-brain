from pytest_bdd import given, parsers, scenarios, then, when

from yt_brain.domain.classifier import ClassificationContext, classify_video
from yt_brain.domain.models import EngagementLevel, Source, Video

scenarios("../features/classify.feature")


@given(parsers.parse("a video with duration {duration:d} and watched {watched:d}"), target_fixture="context")
def video_with_watch_data(duration: int, watched: int) -> ClassificationContext:
    video = Video(
        youtube_id="test1",
        title="Test",
        channel_id="ch1",
        duration_seconds=duration,
        watched_seconds=watched,
        source=Source.TAKEOUT,
    )
    return ClassificationContext(video=video, is_liked=False, is_in_playlist=False)


@given("a video with no watch data", target_fixture="context")
def video_no_watch_data() -> ClassificationContext:
    video = Video(
        youtube_id="test1",
        title="Test",
        channel_id="ch1",
        duration_seconds=600,
        source=Source.API,
    )
    return ClassificationContext(video=video, is_liked=False, is_in_playlist=False)


@given("the video is liked")
def mark_liked(context: ClassificationContext) -> None:
    context.is_liked = True


@given("the video is in a user playlist")
def mark_in_playlist(context: ClassificationContext) -> None:
    context.is_in_playlist = True


@given(parsers.parse("the bounce threshold is {threshold:f}"))
def set_bounce_threshold(context: ClassificationContext, threshold: float) -> None:
    context.bounce_threshold = threshold


@when("I classify the video", target_fixture="result")
def do_classify(context: ClassificationContext) -> EngagementLevel:
    return classify_video(
        video=context.video,
        is_liked=context.is_liked,
        is_in_playlist=context.is_in_playlist,
        bounce_threshold=context.bounce_threshold,
        watched_threshold=context.watched_threshold,
    )


@then(parsers.parse('the engagement level is "{level}"'))
def check_level(result: EngagementLevel, level: str) -> None:
    assert result == EngagementLevel(level)
