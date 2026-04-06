"""Tests for graceful degradation when sqlite-vec is unavailable."""

from __future__ import annotations

import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest


@pytest.fixture
def db_no_vec() -> Path:
    """Create a DB with init_db, but with sqlite-vec flag disabled."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        import yt_brain.infrastructure.database as db_mod

        original = db_mod.SQLITE_VEC_AVAILABLE
        db_mod.SQLITE_VEC_AVAILABLE = False
        try:
            db_mod.init_db(db_path)
        finally:
            db_mod.SQLITE_VEC_AVAILABLE = original
        yield db_path


class TestModuleLevelFlag:
    def test_flag_exists(self):
        from yt_brain.infrastructure.database import SQLITE_VEC_AVAILABLE

        assert isinstance(SQLITE_VEC_AVAILABLE, bool)


class TestInitDbWithoutVec:
    def test_init_db_skips_vec_migrations(self, db_no_vec: Path):
        """init_db should succeed, creating non-vec tables, skipping vec ones."""
        conn = sqlite3.connect(db_no_vec)
        try:
            # Non-vec tables should exist
            tables = {
                row[0]
                for row in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()
            }
            assert "videos" in tables
            assert "channels" in tables
            assert "starred_channels" in tables
            # vec virtual table should NOT exist
            assert "video_embeddings" not in tables
        finally:
            conn.close()

    def test_non_vec_migrations_applied(self, db_no_vec: Path):
        """Non-vec migrations should still be applied."""
        conn = sqlite3.connect(db_no_vec)
        try:
            versions = {
                row[0]
                for row in conn.execute("SELECT version FROM schema_version").fetchall()
            }
            # Non-vec migrations should be present
            assert 1 in versions
            assert 2 in versions
            assert 3 in versions
            assert 5 in versions  # video_clusters (regular SQL, not vec)
            assert 6 in versions
            assert 7 in versions
            # Vec migrations (4, 8) should be skipped
            assert 4 not in versions
            assert 8 not in versions
        finally:
            conn.close()


class TestVecFunctionsRaiseWithoutVec:
    """Vec-dependent functions should raise DatabaseError with a clear message."""

    def test_get_videos_for_embedding_raises(self, db_no_vec: Path):
        from yt_brain.domain.errors import DatabaseError
        from yt_brain.infrastructure.database import get_videos_for_embedding

        with patch("yt_brain.infrastructure.database.SQLITE_VEC_AVAILABLE", False), pytest.raises(DatabaseError, match="sqlite-vec"):
            get_videos_for_embedding(db_no_vec)

    def test_insert_embeddings_raises(self, db_no_vec: Path):
        from yt_brain.domain.errors import DatabaseError
        from yt_brain.infrastructure.database import insert_embeddings

        with patch("yt_brain.infrastructure.database.SQLITE_VEC_AVAILABLE", False), pytest.raises(DatabaseError, match="sqlite-vec"):
            insert_embeddings(db_no_vec, [])

    def test_search_similar_raises(self, db_no_vec: Path):
        from yt_brain.domain.errors import DatabaseError
        from yt_brain.infrastructure.database import search_similar

        with patch("yt_brain.infrastructure.database.SQLITE_VEC_AVAILABLE", False), pytest.raises(DatabaseError, match="sqlite-vec"):
            search_similar(db_no_vec, b"\x00" * 384, limit=10)

    def test_get_embedding_count_raises(self, db_no_vec: Path):
        from yt_brain.domain.errors import DatabaseError
        from yt_brain.infrastructure.database import get_embedding_count

        with patch("yt_brain.infrastructure.database.SQLITE_VEC_AVAILABLE", False), pytest.raises(DatabaseError, match="sqlite-vec"):
            get_embedding_count(db_no_vec)

    def test_get_all_embeddings_raises(self, db_no_vec: Path):
        from yt_brain.domain.errors import DatabaseError
        from yt_brain.infrastructure.database import get_all_embeddings

        with patch("yt_brain.infrastructure.database.SQLITE_VEC_AVAILABLE", False), pytest.raises(DatabaseError, match="sqlite-vec"):
            get_all_embeddings(db_no_vec)

    def test_get_unassigned_video_ids_raises(self, db_no_vec: Path):
        from yt_brain.domain.errors import DatabaseError
        from yt_brain.infrastructure.database import get_unassigned_video_ids

        with patch("yt_brain.infrastructure.database.SQLITE_VEC_AVAILABLE", False), pytest.raises(DatabaseError, match="sqlite-vec"):
            get_unassigned_video_ids(db_no_vec)

    def test_get_embeddings_for_ids_raises(self, db_no_vec: Path):
        from yt_brain.domain.errors import DatabaseError
        from yt_brain.infrastructure.database import get_embeddings_for_ids

        with patch("yt_brain.infrastructure.database.SQLITE_VEC_AVAILABLE", False), pytest.raises(DatabaseError, match="sqlite-vec"):
            get_embeddings_for_ids(db_no_vec, ["abc"])


class TestDashboardSearchFallback:
    """Dashboard search should fall back to LIKE queries without sqlite-vec."""

    def test_search_fallback_to_like(self, temp_db: Path):
        """When embed_model not loaded, search should use text fallback."""
        from yt_brain.domain.models import EngagementLevel, Source, Video
        from yt_brain.infrastructure.database import save_video

        # Insert a test video
        video = Video(
            youtube_id="test123",
            title="Python Machine Learning Tutorial",
            description="Learn ML with Python",
            channel_id="test_channel",
            duration_seconds=600,
            watched_seconds=300,
            watched_at=None,
            engagement_level=EngagementLevel.UNKNOWN,
            transcript="",
            tags=[],
            source=Source.MANUAL,
        )
        save_video(temp_db, video)

        from yt_brain.web.dashboard import create_app

        with patch("yt_brain.infrastructure.database.SQLITE_VEC_AVAILABLE", False):
            app = create_app()
            with app.test_client() as client:
                resp = client.get("/api/search?q=Python")
                data = resp.get_json()
                assert resp.status_code == 200
                assert "results" in data
                # Should find our video via text search
                ids = [r["youtube_id"] for r in data["results"]]
                assert "test123" in ids

    def test_search_fallback_no_match(self, temp_db: Path):
        """Text fallback should return empty for non-matching query."""
        from yt_brain.web.dashboard import create_app

        with patch("yt_brain.infrastructure.database.SQLITE_VEC_AVAILABLE", False):
            app = create_app()
            with app.test_client() as client:
                resp = client.get("/api/search?q=zzzznotfound")
                data = resp.get_json()
                assert resp.status_code == 200
                assert data["results"] == []


class TestCliEarlyGuards:
    """CLI embed and cluster commands should exit cleanly when sqlite-vec is unavailable."""

    def test_embed_exits_without_sqlite_vec(self):
        from typer.testing import CliRunner

        from yt_brain.cli import app

        runner = CliRunner()
        with patch("yt_brain.infrastructure.database.SQLITE_VEC_AVAILABLE", False):
            result = runner.invoke(app, ["embed"])
        assert result.exit_code == 1
        assert "sqlite-vec is not installed" in result.output

    def test_cluster_exits_without_sqlite_vec(self):
        from typer.testing import CliRunner

        from yt_brain.cli import app

        runner = CliRunner()
        with patch("yt_brain.infrastructure.database.SQLITE_VEC_AVAILABLE", False):
            result = runner.invoke(app, ["cluster"])
        assert result.exit_code == 1
        assert "sqlite-vec is not installed" in result.output
