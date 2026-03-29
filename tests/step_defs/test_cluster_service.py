import struct
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from yt_brain.application.cluster import (
    ASSIGNMENT_THRESHOLD,
    _blob_to_array,
    _compute_centroid,
    _generate_slug,
    _slugify,
    cluster_videos,
    assign_new_videos,
)
from yt_brain.domain.models import EngagementLevel, Source, Video
from yt_brain.infrastructure.database import (
    get_clusters_with_counts,
    get_video_cluster_slug,
    init_db,
    insert_embeddings,
    save_video,
)


def _to_blob(vec: list[float]) -> bytes:
    return struct.pack(f"{len(vec)}f", *vec)


def _make_video(db_path: Path, youtube_id: str, title: str, embedding: list[float]) -> None:
    save_video(db_path, Video(
        youtube_id=youtube_id,
        title=title,
        channel_id="ch",
        engagement_level=EngagementLevel.UNKNOWN,
        source=Source.MANUAL,
    ))
    insert_embeddings(db_path, [(youtube_id, _to_blob(embedding))])


def test_slugify() -> None:
    assert _slugify("Agentic Software Development") == "agentic-software-development"
    assert _slugify("Police Body Cam / Footage!") == "police-body-cam-footage"
    assert _slugify("  hello   world  ") == "hello-world"


def test_blob_to_array() -> None:
    vec = [1.0, 2.0, 3.0]
    blob = _to_blob(vec)
    result = _blob_to_array(blob, dim=3)
    np.testing.assert_array_almost_equal(result, vec)


def test_compute_centroid() -> None:
    vecs = np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]])
    centroid = _compute_centroid(vecs)
    np.testing.assert_array_almost_equal(centroid, [0.5, 0.5, 0.0])


@patch("yt_brain.application.cluster._call_claude_for_label")
def test_generate_slug_calls_claude(mock_claude: MagicMock) -> None:
    mock_claude.return_value = "Agentic Development"
    titles = ["Building AI agents", "LangChain tutorial", "Claude tool use"]
    slug = _generate_slug(titles, existing_slugs=set(), api_key="test-key")
    assert slug == "agentic-development"
    mock_claude.assert_called_once()


@patch("yt_brain.application.cluster._call_claude_for_label")
def test_generate_slug_deduplicates(mock_claude: MagicMock) -> None:
    mock_claude.return_value = "Agentic Development"
    titles = ["Building AI agents"]
    slug = _generate_slug(titles, existing_slugs={"agentic-development"}, api_key="test-key")
    assert slug == "agentic-development-2"


@patch("yt_brain.application.cluster._call_claude_for_label")
def test_generate_slug_fallback_on_api_error(mock_claude: MagicMock) -> None:
    mock_claude.side_effect = Exception("API error")
    titles = ["Building AI agents"]
    slug = _generate_slug(titles, existing_slugs=set(), api_key="test-key", fallback_index=3)
    assert slug == "cluster-03"
