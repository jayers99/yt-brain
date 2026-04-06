import struct
from pathlib import Path

from typer.testing import CliRunner

from yt_brain.cli import app as cli_app
from yt_brain.domain.models import Cluster, EngagementLevel, Source, Video
from yt_brain.infrastructure.database import (
    assign_video_to_cluster,
    get_cluster_by_slug,
    get_clusters_with_counts,
    get_video_cluster_slug,
    save_cluster,
    save_video,
)


def _make_video(youtube_id: str, title: str = "Test", channel: str = "ch") -> Video:
    return Video(
        youtube_id=youtube_id,
        title=title,
        channel_id=channel,
        engagement_level=EngagementLevel.UNKNOWN,
        source=Source.MANUAL,
    )


def _fake_centroid() -> bytes:
    return struct.pack("384f", *([0.0] * 384))


def test_save_and_get_cluster(temp_db: Path) -> None:
    cluster = Cluster(slug="agentic-dev", centroid=_fake_centroid())
    cluster_id = save_cluster(temp_db, cluster)
    assert cluster_id > 0

    fetched = get_cluster_by_slug(temp_db, "agentic-dev")
    assert fetched is not None
    assert fetched.slug == "agentic-dev"
    assert fetched.cluster_id == cluster_id


def test_assign_video_to_cluster(temp_db: Path) -> None:
    save_video(temp_db, _make_video("vid1", title="Building agents"))
    cluster = Cluster(slug="agentic-dev", centroid=_fake_centroid())
    cluster_id = save_cluster(temp_db, cluster)

    assign_video_to_cluster(temp_db, "vid1", cluster_id)

    slug = get_video_cluster_slug(temp_db, "vid1")
    assert slug == "agentic-dev"


def test_get_clusters_with_counts(temp_db: Path) -> None:
    cluster = Cluster(slug="agentic-dev", centroid=_fake_centroid())
    cluster_id = save_cluster(temp_db, cluster)

    for i in range(3):
        save_video(temp_db, _make_video(f"vid{i}", title=f"Agent video {i}"))
        assign_video_to_cluster(temp_db, f"vid{i}", cluster_id)

    clusters = get_clusters_with_counts(temp_db)
    assert len(clusters) == 1
    assert clusters[0]["slug"] == "agentic-dev"
    assert clusters[0]["count"] == 3


def test_video_with_no_cluster_returns_none(temp_db: Path) -> None:
    save_video(temp_db, _make_video("vid1"))
    slug = get_video_cluster_slug(temp_db, "vid1")
    assert slug is None


runner = CliRunner()


def test_cluster_list_empty(temp_db: Path) -> None:
    result = runner.invoke(cli_app, ["cluster", "list"])
    assert result.exit_code == 0
    assert "No clusters" in result.stdout


def test_cluster_rename_not_found(temp_db: Path) -> None:
    result = runner.invoke(cli_app, ["cluster", "rename", "nonexistent", "new-name"])
    assert result.exit_code == 0
    assert "not found" in result.stdout.lower()
