from pytest_bdd import given, parsers, scenarios, then, when

from yt_brain.application.review import get_review_list, override_engagement
from yt_brain.domain.models import EngagementLevel, Source, Video
from yt_brain.infrastructure.database import get_video, init_db, save_video

scenarios("../features/review.feature")


@given("a database with classified videos:", target_fixture="db_path")
def db_with_classified(temp_config_dir, datatable):
    db_path = temp_config_dir / "yt-brain.db"
    init_db(db_path)
    # datatable is a list of lists; first row is headers
    rows_raw = list(datatable)
    headers = rows_raw[0]
    rows = [dict(zip(headers, row, strict=True)) for row in rows_raw[1:]]
    for row in rows:
        video = Video(
            youtube_id=row["youtube_id"],
            title=row["title"],
            channel_id="ch1",
            engagement_level=EngagementLevel(row["engagement"]),
            source=Source.MANUAL,
        )
        save_video(db_path, video)
    return db_path


@given(parsers.parse('a database with a video "{vid}" classified as "{level}"'), target_fixture="db_path")
def db_with_one_video(temp_config_dir, vid: str, level: str):
    db_path = temp_config_dir / "yt-brain.db"
    init_db(db_path)
    video = Video(
        youtube_id=vid,
        title=f"Video {vid}",
        channel_id="ch1",
        engagement_level=EngagementLevel(level),
        source=Source.MANUAL,
    )
    save_video(db_path, video)
    return db_path


@when(parsers.parse('I get review list for tier "{level}"'), target_fixture="review_list")
def do_get_review_list(db_path, level: str):
    return get_review_list(db_path, EngagementLevel(level))


@when(parsers.parse('I override "{vid}" to "{level}"'))
def do_override(db_path, vid: str, level: str) -> None:
    override_engagement(db_path, vid, EngagementLevel(level))


@when(parsers.parse('I retrieve video "{vid}" for review'), target_fixture="reviewed_video")
def do_retrieve(db_path, vid: str):
    return get_video(db_path, vid)


@then(parsers.parse("I get {count:d} videos for review"))
def check_review_count(review_list, count: int) -> None:
    assert len(review_list) == count


@then(parsers.parse('the effective engagement is "{level}"'))
def check_effective(reviewed_video, level: str) -> None:
    assert reviewed_video.effective_engagement == EngagementLevel(level)
