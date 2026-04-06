from __future__ import annotations

import json
import sqlite3
import subprocess
import urllib.error
import urllib.request
from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class CheckStatus(Enum):
    OK = "ok"
    FAIL = "fail"
    WARN = "warn"
    INFO = "info"


@dataclass
class CheckResult:
    name: str
    status: CheckStatus
    detail: str


def check_sqlite_vec() -> CheckResult:
    from yt_brain.infrastructure.database import SQLITE_VEC_AVAILABLE

    if SQLITE_VEC_AVAILABLE:
        return CheckResult("sqlite-vec", CheckStatus.OK, "loaded")
    return CheckResult("sqlite-vec", CheckStatus.FAIL, "not available — reinstall with: pip install sqlite-vec")


def check_ytdlp() -> CheckResult:
    try:
        result = subprocess.run(
            ["yt-dlp", "--version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        version = result.stdout.strip()
        if result.returncode == 0 and version:
            return CheckResult("yt-dlp", CheckStatus.OK, version)
        error = result.stderr.strip()
        detail = error or version or f"yt-dlp exited with status {result.returncode}"
        return CheckResult("yt-dlp", CheckStatus.FAIL, detail)
    except FileNotFoundError:
        return CheckResult("yt-dlp", CheckStatus.FAIL, "not found — install yt-dlp")
    except Exception as exc:  # noqa: BLE001
        return CheckResult("yt-dlp", CheckStatus.FAIL, str(exc))


def check_youtube_api_key(api_key: str) -> CheckResult:
    if not api_key:
        return CheckResult("YouTube API key", CheckStatus.FAIL, "not configured")
    url = f"https://www.googleapis.com/youtube/v3/videos?part=id&id=dQw4w9WgXcQ&key={api_key}"
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.loads(resp.read())
        if data.get("items"):
            return CheckResult("YouTube API key", CheckStatus.OK, "valid")
        return CheckResult("YouTube API key", CheckStatus.FAIL, "key accepted but no items returned")
    except urllib.error.HTTPError as exc:
        return CheckResult("YouTube API key", CheckStatus.FAIL, f"HTTP {exc.code}: {exc.reason}")
    except Exception:  # noqa: BLE001
        return CheckResult("YouTube API key", CheckStatus.FAIL, "configured but validation failed")


def check_anthropic_api_key(api_key: str) -> CheckResult:
    if not api_key:
        return CheckResult(
            "Anthropic API key",
            CheckStatus.WARN,
            "not configured (optional — needed for cluster naming)",
        )
    return CheckResult("Anthropic API key", CheckStatus.OK, "configured")


def check_browser_cookies() -> CheckResult:
    return CheckResult(
        "browser cookies",
        CheckStatus.INFO,
        "untested (run 'yt-brain sync' to verify)",
    )


def check_database(db_path: Path) -> CheckResult:
    if not db_path.exists():
        return CheckResult("database", CheckStatus.INFO, "no database yet")

    conn = sqlite3.connect(db_path)
    try:
        (video_count,) = conn.execute("SELECT COUNT(*) FROM videos").fetchone()

        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }

        parts = [f"{video_count:,} videos"]

        if "video_embeddings" in tables:
            parts.append("embeddings table present")

        if "video_clusters" in tables:
            (cluster_count,) = conn.execute("SELECT COUNT(*) FROM video_clusters").fetchone()
            parts.append(f"{cluster_count:,} clusters")

        return CheckResult("database", CheckStatus.INFO, " | ".join(parts))
    except sqlite3.OperationalError:
        return CheckResult("database", CheckStatus.WARN, "database exists but schema is missing or corrupt")
    finally:
        conn.close()


def run_doctor(
    youtube_api_key: str,
    anthropic_api_key: str,
    db_path: Path,
) -> list[CheckResult]:
    """Run all prerequisite checks and return results."""
    return [
        check_sqlite_vec(),
        check_ytdlp(),
        check_youtube_api_key(youtube_api_key),
        check_anthropic_api_key(anthropic_api_key),
        check_browser_cookies(),
        check_database(db_path),
    ]
