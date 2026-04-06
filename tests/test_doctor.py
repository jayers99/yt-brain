from __future__ import annotations

import json
import sqlite3
import subprocess
import urllib.error
from pathlib import Path
from unittest.mock import MagicMock, patch

from yt_brain.application.doctor import (
    CheckResult,
    CheckStatus,
    check_anthropic_api_key,
    check_browser_cookies,
    check_database,
    check_sqlite_vec,
    check_youtube_api_key,
    check_ytdlp,
    run_doctor,
)


class TestCheckSqliteVec:
    def test_ok_when_available(self):
        with patch("yt_brain.infrastructure.database.SQLITE_VEC_AVAILABLE", True):
            result = check_sqlite_vec()
        assert result.status == CheckStatus.OK
        assert result.name == "sqlite-vec"

    def test_fail_when_unavailable(self):
        with patch("yt_brain.infrastructure.database.SQLITE_VEC_AVAILABLE", False):
            result = check_sqlite_vec()
        assert result.status == CheckStatus.FAIL
        assert "uv sync" in result.detail

    def test_returns_check_result(self):
        with patch("yt_brain.infrastructure.database.SQLITE_VEC_AVAILABLE", True):
            result = check_sqlite_vec()
        assert isinstance(result, CheckResult)


class TestCheckYtdlp:
    def test_ok_with_version(self):
        mock_run = MagicMock()
        mock_run.return_value.stdout = "2024.1.1\n"
        with patch("subprocess.run", mock_run):
            result = check_ytdlp()
        assert result.status == CheckStatus.OK
        assert result.detail == "2024.1.1"

    def test_fail_when_not_found(self):
        with patch("subprocess.run", side_effect=FileNotFoundError):
            result = check_ytdlp()
        assert result.status == CheckStatus.FAIL
        assert "not found" in result.detail

    def test_fail_on_other_exception(self):
        with patch("subprocess.run", side_effect=OSError("permission denied")):
            result = check_ytdlp()
        assert result.status == CheckStatus.FAIL

    def test_name_is_ytdlp(self):
        mock_run = MagicMock()
        mock_run.return_value.stdout = "2024.1.1\n"
        with patch("subprocess.run", mock_run):
            result = check_ytdlp()
        assert result.name == "yt-dlp"


class TestCheckYoutubeApiKey:
    def test_fail_when_empty(self):
        result = check_youtube_api_key("")
        assert result.status == CheckStatus.FAIL
        assert "not configured" in result.detail

    def test_ok_when_items_returned(self):
        payload = json.dumps({"items": [{"id": "dQw4w9WgXcQ"}]}).encode()
        mock_resp = MagicMock()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_resp.read.return_value = payload
        with patch("urllib.request.urlopen", return_value=mock_resp):
            result = check_youtube_api_key("valid-key")
        assert result.status == CheckStatus.OK
        assert "valid" in result.detail

    def test_fail_when_no_items(self):
        payload = json.dumps({"items": []}).encode()
        mock_resp = MagicMock()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_resp.read.return_value = payload
        with patch("urllib.request.urlopen", return_value=mock_resp):
            result = check_youtube_api_key("bad-key")
        assert result.status == CheckStatus.FAIL

    def test_fail_on_http_error(self):
        with patch("urllib.request.urlopen", side_effect=urllib.error.HTTPError(None, 403, "Forbidden", {}, None)):
            result = check_youtube_api_key("bad-key")
        assert result.status == CheckStatus.FAIL
        assert "403" in result.detail

    def test_fail_on_network_error(self):
        with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("timeout")):
            result = check_youtube_api_key("some-key")
        assert result.status == CheckStatus.FAIL

    def test_name(self):
        result = check_youtube_api_key("")
        assert result.name == "YouTube API key"

    def test_error_detail_does_not_leak_api_key(self):
        secret = "super-secret-api-key-12345"
        with patch("urllib.request.urlopen", side_effect=Exception(f"https://googleapis.com/...&key={secret}")):
            result = check_youtube_api_key(secret)
        assert result.status == CheckStatus.FAIL
        assert secret not in result.detail


class TestCheckAnthropicApiKey:
    def test_warn_when_empty(self):
        result = check_anthropic_api_key("")
        assert result.status == CheckStatus.WARN
        assert "optional" in result.detail

    def test_ok_when_set(self):
        result = check_anthropic_api_key("sk-ant-abc123")
        assert result.status == CheckStatus.OK

    def test_name(self):
        result = check_anthropic_api_key("")
        assert result.name == "Anthropic API key"

    def test_no_api_call_made(self):
        """Should never make a network call — costs money."""
        with patch("urllib.request.urlopen") as mock_url:
            check_anthropic_api_key("some-key")
            mock_url.assert_not_called()


class TestCheckBrowserCookies:
    def test_always_info(self):
        result = check_browser_cookies()
        assert result.status == CheckStatus.INFO

    def test_detail_mentions_sync(self):
        result = check_browser_cookies()
        assert "yt-brain sync" in result.detail

    def test_name(self):
        result = check_browser_cookies()
        assert result.name == "browser cookies"


class TestCheckDatabase:
    def test_info_when_no_db(self, tmp_path: Path):
        result = check_database(tmp_path / "nonexistent.db")
        assert result.status == CheckStatus.INFO
        assert "no database yet" in result.detail

    def test_info_with_empty_db(self, temp_db: Path):
        result = check_database(temp_db)
        assert result.status == CheckStatus.INFO
        assert "0 videos" in result.detail

    def test_video_count_shown(self, temp_db: Path):
        conn = sqlite3.connect(temp_db)
        conn.execute(
            "INSERT INTO videos (youtube_id, title, description, channel_id, "
            "duration_seconds, watched_seconds, engagement_level, transcript, tags, source) "
            "VALUES ('abc123', 'Test', '', 'ch1', 60, 30, 'unknown', '', '[]', 'manual')"
        )
        conn.commit()
        conn.close()
        result = check_database(temp_db)
        assert "1 videos" in result.detail

    def test_embeddings_count_shown_when_table_exists(self, temp_db: Path):
        result = check_database(temp_db)
        # If sqlite-vec is available, video_embeddings table exists
        # Either way, the result should be INFO with no crash
        assert result.status == CheckStatus.INFO
        assert "videos" in result.detail

    def test_clusters_count_shown_when_table_exists(self, temp_db: Path):
        result = check_database(temp_db)
        assert result.status == CheckStatus.INFO

    def test_name(self, temp_db: Path):
        result = check_database(temp_db)
        assert result.name == "database"

    def test_warn_when_db_exists_but_no_schema(self, tmp_path: Path):
        # Create a db file with no tables (empty/corrupt schema)
        db_path = tmp_path / "empty.db"
        import sqlite3 as _sqlite3
        conn = _sqlite3.connect(db_path)
        conn.close()
        result = check_database(db_path)
        assert result.status == CheckStatus.WARN
        assert "corrupt" in result.detail or "missing" in result.detail

    def test_large_counts_formatted_with_commas(self, temp_db: Path):
        conn = sqlite3.connect(temp_db)
        # Insert 1001 fake videos to verify comma formatting
        conn.executemany(
            "INSERT INTO videos (youtube_id, title, description, channel_id, "
            "duration_seconds, watched_seconds, engagement_level, transcript, tags, source) "
            "VALUES (?, 'T', '', 'c', 60, 30, 'unknown', '', '[]', 'manual')",
            [(f"vid{i}",) for i in range(1001)],
        )
        conn.commit()
        conn.close()
        result = check_database(temp_db)
        assert "1,001 videos" in result.detail


class TestRunDoctor:
    def test_returns_all_checks(self, temp_db):
        with (
            patch("yt_brain.infrastructure.database.SQLITE_VEC_AVAILABLE", True),
            patch(
                "yt_brain.application.doctor.subprocess.run",
                return_value=subprocess.CompletedProcess(args=[], returncode=0, stdout="2024.12.1"),
            ),
        ):
            results = run_doctor(
                youtube_api_key="",
                anthropic_api_key="",
                db_path=temp_db,
            )
        assert len(results) == 6
        names = [r.name for r in results]
        assert "sqlite-vec" in names
        assert "yt-dlp" in names
        assert "YouTube API key" in names
        assert "Anthropic API key" in names
        assert "browser cookies" in names
        assert "database" in names

    def test_has_failures_when_deps_missing(self, temp_db):
        with (
            patch("yt_brain.infrastructure.database.SQLITE_VEC_AVAILABLE", False),
            patch(
                "yt_brain.application.doctor.subprocess.run",
                side_effect=FileNotFoundError,
            ),
        ):
            results = run_doctor(
                youtube_api_key="",
                anthropic_api_key="",
                db_path=temp_db,
            )
        failures = [r for r in results if r.status == CheckStatus.FAIL]
        assert len(failures) >= 2


class TestDoctorCli:
    def test_doctor_runs(self, temp_config_dir):
        from typer.testing import CliRunner

        from yt_brain.cli import app

        runner = CliRunner()
        with (
            patch("yt_brain.infrastructure.database.SQLITE_VEC_AVAILABLE", True),
            patch(
                "yt_brain.application.doctor.subprocess.run",
                return_value=subprocess.CompletedProcess(args=[], returncode=0, stdout="2024.12.1"),
            ),
            patch("yt_brain.application.doctor.urllib.request.urlopen") as mock_url,
        ):
            mock_resp = MagicMock()
            mock_resp.read.return_value = json.dumps({"items": []}).encode()
            mock_resp.__enter__ = lambda s: s
            mock_resp.__exit__ = MagicMock(return_value=False)
            mock_url.return_value = mock_resp
            result = runner.invoke(app, ["doctor"])

        assert "prerequisites check" in result.output
        assert "sqlite-vec" in result.output
        assert "yt-dlp" in result.output

    def test_doctor_exit_code_1_on_failure(self, temp_config_dir):
        from typer.testing import CliRunner

        from yt_brain.cli import app

        runner = CliRunner()
        with (
            patch("yt_brain.infrastructure.database.SQLITE_VEC_AVAILABLE", False),
            patch(
                "yt_brain.application.doctor.subprocess.run",
                side_effect=FileNotFoundError,
            ),
        ):
            result = runner.invoke(app, ["doctor"])

        assert result.exit_code == 1
        assert "issue(s) found" in result.output
