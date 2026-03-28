from __future__ import annotations

import json
import subprocess
from urllib.parse import parse_qs, urlparse

from yt_brain.domain.errors import IngestError
from yt_brain.domain.models import Source, Video


def extract_video_id(url: str) -> str:
    parsed = urlparse(url)

    if parsed.hostname in ("youtu.be",):
        return parsed.path.lstrip("/")

    if parsed.hostname in ("www.youtube.com", "youtube.com", "m.youtube.com"):
        params = parse_qs(parsed.query)
        ids = params.get("v")
        if ids:
            return ids[0]

    raise IngestError(f"Cannot extract video ID from URL: {url}")


def fetch_metadata(video_id: str) -> Video:
    try:
        result = subprocess.run(
            ["yt-dlp", "--dump-json", "--no-download", f"https://www.youtube.com/watch?v={video_id}"],
            capture_output=True,
            text=True,
            timeout=30,
        )
    except FileNotFoundError as err:
        raise IngestError("yt-dlp is not installed. Install with: brew install yt-dlp") from err

    if result.returncode != 0:
        raise IngestError(f"yt-dlp failed for {video_id}: {result.stderr.strip()}")

    metadata = json.loads(result.stdout)
    return parse_ytdlp_metadata(metadata)


def fetch_transcript(video_id: str, language: str = "en") -> str | None:
    try:
        result = subprocess.run(
            [
                "yt-dlp",
                "--write-auto-subs",
                "--sub-lang", language,
                "--skip-download",
                "--print-to-file", "%(subtitles)j", "/dev/stdout",
                f"https://www.youtube.com/watch?v={video_id}",
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode == 0 and result.stdout.strip():
            subs = json.loads(result.stdout)
            if language in subs:
                return _extract_text_from_subs(subs[language])
    except (FileNotFoundError, json.JSONDecodeError, KeyError, subprocess.TimeoutExpired):
        pass

    return None


def fetch_history(
    limit: int = 20,
    browser: str = "chrome",
) -> list[dict]:
    """Fetch YouTube watch history via yt-dlp using browser cookies."""
    try:
        result = subprocess.run(
            [
                "yt-dlp",
                "--cookies-from-browser", browser,
                "--flat-playlist",
                "--dump-json",
                "-I", f"1:{limit}",
                "https://www.youtube.com/feed/history",
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )
    except FileNotFoundError as err:
        raise IngestError("yt-dlp is not installed. Install with: brew install yt-dlp") from err

    if result.returncode != 0:
        raise IngestError(f"Failed to fetch history: {result.stderr.strip()}")

    entries = []
    for line in result.stdout.strip().splitlines():
        if line.strip():
            entries.append(json.loads(line))
    return entries


def _fetch_history_range(
    start: int,
    end: int,
    browser: str = "chrome",
) -> list[dict]:
    """Fetch a specific range of YouTube watch history entries."""
    try:
        result = subprocess.run(
            [
                "yt-dlp",
                "--cookies-from-browser", browser,
                "--flat-playlist",
                "--dump-json",
                "-I", f"{start}:{end}",
                "https://www.youtube.com/feed/history",
            ],
            capture_output=True,
            text=True,
            timeout=120,
        )
    except FileNotFoundError as err:
        raise IngestError("yt-dlp is not installed. Install with: brew install yt-dlp") from err

    if result.returncode != 0:
        raise IngestError(f"Failed to fetch history: {result.stderr.strip()}")

    entries = []
    for line in result.stdout.strip().splitlines():
        if line.strip():
            entries.append(json.loads(line))
    return entries


def parse_ytdlp_metadata(metadata: dict) -> Video:
    return Video(
        youtube_id=metadata.get("id", ""),
        title=metadata.get("title") or "",
        description=metadata.get("description") or "",
        channel_id=metadata.get("channel", "") or metadata.get("uploader", "") or metadata.get("channel_id", ""),
        duration_seconds=int(metadata.get("duration") or 0),
        tags=metadata.get("tags", []) or [],
        source=Source.MANUAL,
    )


def _extract_text_from_subs(sub_data: list[dict]) -> str:
    lines = []
    for event in sub_data:
        text = event.get("text", "").strip()
        if text and text not in lines[-1:]:
            lines.append(text)
    return " ".join(lines)
