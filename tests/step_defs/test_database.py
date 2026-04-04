import sqlite3

from pytest_bdd import given, parsers, scenarios, then, when

from yt_brain.domain.models import EngagementLevel, Source, Video
from yt_brain.infrastructure.database import (
    get_existing_video_ids,
    get_video,
    get_videos_by_engagement,
    init_db,
    save_video,
)

scenarios("../features/database.feature")


@given("a fresh database", target_fixture="db_path")
def fresh_database(temp_config_dir):
    db_path = temp_config_dir / "yt-brain.db"
    init_db(db_path)
    return db_path


@given(parsers.parse('a video "{vid}" titled "{title}" from channel "{channel}"'), target_fixture="video")
def create_video(vid: str, title: str, channel: str) -> Video:
    return Video(youtube_id=vid, title=title, channel_id=channel, source=Source.MANUAL)


@given(parsers.parse('a saved video "{vid}" with engagement "{level}"'))
def save_video_with_engagement(db_path, vid: str, level: str) -> None:
    video = Video(
        youtube_id=vid,
        title=f"Video {vid}",
        channel_id="ch1",
        engagement_level=EngagementLevel(level),
        source=Source.MANUAL,
    )
    save_video(db_path, video)


@when("I save the video")
def do_save(db_path, video) -> None:
    save_video(db_path, video)


@when(parsers.parse('I save a video "{vid}" titled "{title}" from channel "{channel}"'))
def save_another(db_path, vid: str, title: str, channel: str) -> None:
    video = Video(youtube_id=vid, title=title, channel_id=channel, source=Source.MANUAL)
    save_video(db_path, video)


@when(parsers.parse('I retrieve video "{vid}"'), target_fixture="retrieved")
def do_retrieve(db_path, vid: str):
    return get_video(db_path, vid)


@when(parsers.parse('I list videos with engagement "{level}"'), target_fixture="video_list")
def do_list_by_engagement(db_path, level: str):
    return get_videos_by_engagement(db_path, EngagementLevel(level))


@then(parsers.parse('the retrieved video title is "{title}"'))
def check_title(retrieved, title: str) -> None:
    assert retrieved is not None
    assert retrieved.title == title


@then(parsers.parse("the {table} table exists"))
def check_table_exists(db_path, table: str) -> None:
    conn = sqlite3.connect(db_path)
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
    assert cursor.fetchone() is not None
    conn.close()


@then(parsers.parse("the schema_version is {version:d}"))
def check_schema_version(db_path, version: int) -> None:
    conn = sqlite3.connect(db_path)
    cursor = conn.execute("SELECT version FROM schema_version ORDER BY version DESC LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    assert row is not None
    assert row[0] == version


@then(parsers.parse("I get {count:d} videos"))
def check_video_count(video_list, count: int) -> None:
    assert len(video_list) == count


def test_get_existing_video_ids(temp_db):
    v1 = Video(youtube_id="aaa", title="Video A", channel_id="ch1")
    v2 = Video(youtube_id="bbb", title="Video B", channel_id="ch2")
    save_video(temp_db, v1)
    save_video(temp_db, v2)

    result = get_existing_video_ids(temp_db, ["aaa", "bbb", "ccc", "ddd"])
    assert result == {"aaa", "bbb"}


def test_get_existing_video_ids_empty(temp_db):
    result = get_existing_video_ids(temp_db, [])
    assert result == set()


def test_update_video_liked(temp_db):
    from yt_brain.infrastructure.database import update_video_liked

    v = Video(youtube_id="lik1", title="Liked Video", channel_id="ch1")
    save_video(temp_db, v)
    update_video_liked(temp_db, "lik1", "like")

    conn = sqlite3.connect(temp_db)
    row = conn.execute("SELECT liked FROM videos WHERE youtube_id = 'lik1'").fetchone()
    conn.close()
    assert row[0] == "like"


def test_update_video_liked_null(temp_db):
    from yt_brain.infrastructure.database import update_video_liked

    v = Video(youtube_id="lik2", title="Unliked Video", channel_id="ch1")
    save_video(temp_db, v)
    update_video_liked(temp_db, "lik2", None)

    conn = sqlite3.connect(temp_db)
    row = conn.execute("SELECT liked FROM videos WHERE youtube_id = 'lik2'").fetchone()
    conn.close()
    assert row[0] is None


def test_bulk_update_liked(temp_db):
    from yt_brain.infrastructure.database import bulk_update_liked

    for vid_id in ["a1", "a2", "a3"]:
        save_video(temp_db, Video(youtube_id=vid_id, title=f"V {vid_id}", channel_id="ch"))
    bulk_update_liked(temp_db, {"a1": "like", "a2": "dislike", "a3": None})

    conn = sqlite3.connect(temp_db)
    rows = {r[0]: r[1] for r in conn.execute("SELECT youtube_id, liked FROM videos WHERE youtube_id IN ('a1','a2','a3')").fetchall()}
    conn.close()
    assert rows == {"a1": "like", "a2": "dislike", "a3": None}


def test_update_published_at(temp_db):
    from yt_brain.infrastructure.database import update_published_at

    v = Video(youtube_id="pub1", title="Published Video", channel_id="ch1")
    save_video(temp_db, v)
    update_published_at(temp_db, "pub1", "2024-06-15T10:00:00Z")

    conn = sqlite3.connect(temp_db)
    row = conn.execute("SELECT published_at FROM videos WHERE youtube_id = 'pub1'").fetchone()
    conn.close()
    assert row[0] == "2024-06-15T10:00:00Z"


def test_get_all_video_ids(temp_db):
    from yt_brain.infrastructure.database import get_all_video_ids

    for vid_id in ["x1", "x2"]:
        save_video(temp_db, Video(youtube_id=vid_id, title=f"V {vid_id}", channel_id="ch"))
    result = get_all_video_ids(temp_db)
    assert result == {"x1", "x2"}
