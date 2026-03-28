from pytest_bdd import given, parsers, scenarios, then, when

from yt_brain.application.status import StatusSummary, get_status_summary
from yt_brain.domain.models import EngagementLevel, Source, Video
from yt_brain.infrastructure.database import init_db, save_video

scenarios("../features/status.feature")


@given("an empty database", target_fixture="db_path")
def empty_db(temp_config_dir):
    db_path = temp_config_dir / "yt-brain.db"
    init_db(db_path)
    return db_path


@given("a database with these videos:", target_fixture="db_path")
def db_with_videos(temp_config_dir, datatable):
    db_path = temp_config_dir / "yt-brain.db"
    init_db(db_path)
    # datatable is a list of lists; first row is headers
    rows_raw = list(datatable)
    headers = rows_raw[0]
    rows = [dict(zip(headers, row, strict=True)) for row in rows_raw[1:]]
    for row in rows:
        video = Video(
            youtube_id=row["youtube_id"],
            title=f"Video {row['youtube_id']}",
            channel_id="ch1",
            engagement_level=EngagementLevel(row["engagement"]),
            source=Source.MANUAL,
        )
        save_video(db_path, video)
    return db_path


@when("I get the status summary", target_fixture="summary")
def do_get_summary(db_path) -> StatusSummary:
    return get_status_summary(db_path)


@then(parsers.parse("total videos is {count:d}"))
def check_total(summary: StatusSummary, count: int) -> None:
    assert summary.total == count


@then("all tier counts are 0")
def check_all_zero(summary: StatusSummary) -> None:
    for level in EngagementLevel:
        assert summary.by_engagement.get(level.value, 0) == 0


@then(parsers.parse("{level} count is {count:d}"))
def check_tier_count(summary: StatusSummary, level: str, count: int) -> None:
    assert summary.by_engagement.get(level, 0) == count
