# Public Release UX Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make yt-brain easy to install from PyPI with a `yt-brain surgeon` command for prerequisite verification, then rewrite docs so README is a landing page and INSTALL.md is the single setup guide.

**Architecture:** Three phases executed sequentially — (1) `yt-brain surgeon` CLI command in application layer, (2) PyPI publishing via GitHub Actions with soft dependency handling, (3) README/INSTALL.md rewrite. Each phase is a separate PR.

**Tech Stack:** Typer CLI, Rich console output, GitHub Actions (trusted publishing), hatchling build backend

---

## File Map

| File | Action | Purpose |
|------|--------|---------|
| `src/yt_brain/application/surgeon.py` | Create | Prerequisite check logic |
| `tests/test_surgeon.py` | Create | Tests for surgeon command |
| `src/yt_brain/cli.py` | Modify | Register `surgeon` command |
| `pyproject.toml` | Modify | Add classifiers, project URLs, version bump |
| `.github/workflows/publish.yml` | Create | PyPI publish on release |
| `README.md` | Rewrite | Landing page only |
| `INSTALL.md` | Create | Full setup guide |
| `CONTRIBUTING.md` | Modify | Add Makefile table from README |

---

## Phase 1: `yt-brain surgeon`

### Task 1: Surgeon check infrastructure

**Files:**
- Create: `src/yt_brain/application/surgeon.py`
- Create: `tests/test_surgeon.py`

- [ ] **Step 1: Write the failing test for CheckResult model and `check_sqlite_vec`**

```python
# tests/test_surgeon.py
"""Tests for yt-brain surgeon prerequisite checks."""

from __future__ import annotations

from unittest.mock import patch

from yt_brain.application.surgeon import CheckResult, CheckStatus, check_sqlite_vec


class TestCheckResult:
    def test_ok_result(self):
        r = CheckResult(name="test", status=CheckStatus.OK, detail="works")
        assert r.name == "test"
        assert r.status == CheckStatus.OK
        assert r.detail == "works"

    def test_fail_result(self):
        r = CheckResult(name="test", status=CheckStatus.FAIL, detail="broken")
        assert r.status == CheckStatus.FAIL


class TestCheckSqliteVec:
    def test_available(self):
        with patch("yt_brain.application.surgeon.SQLITE_VEC_AVAILABLE", True):
            result = check_sqlite_vec()
        assert result.status == CheckStatus.OK
        assert result.name == "sqlite-vec"

    def test_unavailable(self):
        with patch("yt_brain.application.surgeon.SQLITE_VEC_AVAILABLE", False):
            result = check_sqlite_vec()
        assert result.status == CheckStatus.FAIL
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_surgeon.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'yt_brain.application.surgeon'`

- [ ] **Step 3: Implement CheckResult model and `check_sqlite_vec`**

```python
# src/yt_brain/application/surgeon.py
"""Prerequisite checks for yt-brain surgeon command."""

from __future__ import annotations

import enum
from dataclasses import dataclass

from yt_brain.infrastructure.database import SQLITE_VEC_AVAILABLE


class CheckStatus(enum.Enum):
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
    if SQLITE_VEC_AVAILABLE:
        return CheckResult(name="sqlite-vec", status=CheckStatus.OK, detail="loadable")
    return CheckResult(
        name="sqlite-vec",
        status=CheckStatus.FAIL,
        detail="not available (semantic search disabled)",
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_surgeon.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/yt_brain/application/surgeon.py tests/test_surgeon.py
git commit -m "Add surgeon check infrastructure with sqlite-vec check"
```

### Task 2: yt-dlp check

**Files:**
- Modify: `src/yt_brain/application/surgeon.py`
- Modify: `tests/test_surgeon.py`

- [ ] **Step 1: Write the failing test for `check_ytdlp`**

```python
# append to tests/test_surgeon.py
import subprocess

from yt_brain.application.surgeon import check_ytdlp


class TestCheckYtdlp:
    def test_installed(self):
        with patch(
            "yt_brain.application.surgeon.subprocess.run",
            return_value=subprocess.CompletedProcess(args=[], returncode=0, stdout="2024.12.1"),
        ):
            result = check_ytdlp()
        assert result.status == CheckStatus.OK
        assert "2024.12.1" in result.detail

    def test_not_installed(self):
        with patch(
            "yt_brain.application.surgeon.subprocess.run",
            side_effect=FileNotFoundError,
        ):
            result = check_ytdlp()
        assert result.status == CheckStatus.FAIL
        assert "not found" in result.detail
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_surgeon.py::TestCheckYtdlp -v`
Expected: FAIL — `ImportError: cannot import name 'check_ytdlp'`

- [ ] **Step 3: Implement `check_ytdlp`**

```python
# add to src/yt_brain/application/surgeon.py
import subprocess


def check_ytdlp() -> CheckResult:
    try:
        result = subprocess.run(
            ["yt-dlp", "--version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        version = result.stdout.strip()
        return CheckResult(name="yt-dlp", status=CheckStatus.OK, detail=f"installed ({version})")
    except FileNotFoundError:
        return CheckResult(name="yt-dlp", status=CheckStatus.FAIL, detail="not found on PATH")
    except subprocess.TimeoutExpired:
        return CheckResult(name="yt-dlp", status=CheckStatus.WARN, detail="found but timed out")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_surgeon.py::TestCheckYtdlp -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/yt_brain/application/surgeon.py tests/test_surgeon.py
git commit -m "Add yt-dlp check to surgeon"
```

### Task 3: YouTube API key check

**Files:**
- Modify: `src/yt_brain/application/surgeon.py`
- Modify: `tests/test_surgeon.py`

- [ ] **Step 1: Write the failing test for `check_youtube_api_key`**

```python
# append to tests/test_surgeon.py
import json
from unittest.mock import MagicMock

from yt_brain.application.surgeon import check_youtube_api_key


class TestCheckYoutubeApiKey:
    def test_not_configured(self):
        result = check_youtube_api_key(api_key="")
        assert result.status == CheckStatus.FAIL
        assert "not configured" in result.detail

    def test_configured_and_valid(self):
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({"items": [{"id": "dQw4w9WgXcQ"}]}).encode()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        with patch("yt_brain.application.surgeon.urllib.request.urlopen", return_value=mock_resp):
            result = check_youtube_api_key(api_key="fake-key")
        assert result.status == CheckStatus.OK
        assert "valid" in result.detail

    def test_configured_but_invalid(self):
        with patch(
            "yt_brain.application.surgeon.urllib.request.urlopen",
            side_effect=Exception("403 Forbidden"),
        ):
            result = check_youtube_api_key(api_key="bad-key")
        assert result.status == CheckStatus.FAIL
        assert "invalid" in result.detail.lower() or "error" in result.detail.lower()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_surgeon.py::TestCheckYoutubeApiKey -v`
Expected: FAIL — `ImportError: cannot import name 'check_youtube_api_key'`

- [ ] **Step 3: Implement `check_youtube_api_key`**

```python
# add to src/yt_brain/application/surgeon.py
import json
import urllib.request
from urllib.error import URLError


def check_youtube_api_key(api_key: str) -> CheckResult:
    if not api_key:
        return CheckResult(
            name="YouTube API key",
            status=CheckStatus.FAIL,
            detail="not configured",
        )
    try:
        url = (
            "https://www.googleapis.com/youtube/v3/videos"
            f"?part=id&id=dQw4w9WgXcQ&key={api_key}"
        )
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.loads(resp.read())
        if data.get("items"):
            return CheckResult(name="YouTube API key", status=CheckStatus.OK, detail="configured + valid")
        return CheckResult(name="YouTube API key", status=CheckStatus.FAIL, detail="configured but returned no data")
    except (URLError, json.JSONDecodeError, TimeoutError, Exception) as e:
        return CheckResult(name="YouTube API key", status=CheckStatus.FAIL, detail=f"configured but error: {e}")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_surgeon.py::TestCheckYoutubeApiKey -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/yt_brain/application/surgeon.py tests/test_surgeon.py
git commit -m "Add YouTube API key check to surgeon"
```

### Task 4: Anthropic API key check

**Files:**
- Modify: `src/yt_brain/application/surgeon.py`
- Modify: `tests/test_surgeon.py`

- [ ] **Step 1: Write the failing test for `check_anthropic_api_key`**

```python
# append to tests/test_surgeon.py
from yt_brain.application.surgeon import check_anthropic_api_key


class TestCheckAnthropicApiKey:
    def test_not_configured(self):
        result = check_anthropic_api_key(api_key="")
        assert result.status == CheckStatus.WARN
        assert "not configured" in result.detail

    def test_configured(self):
        # Anthropic check just validates key is set (non-empty), doesn't call API
        # to avoid burning tokens on a health check
        result = check_anthropic_api_key(api_key="sk-ant-fake")
        assert result.status == CheckStatus.OK
        assert "configured" in result.detail
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_surgeon.py::TestCheckAnthropicApiKey -v`
Expected: FAIL — `ImportError: cannot import name 'check_anthropic_api_key'`

- [ ] **Step 3: Implement `check_anthropic_api_key`**

Note: Unlike YouTube API, we don't make a test call — Anthropic API calls cost money and this is a diagnostic command. Just verify the key is present.

```python
# add to src/yt_brain/application/surgeon.py
def check_anthropic_api_key(api_key: str) -> CheckResult:
    if not api_key:
        return CheckResult(
            name="Anthropic API key",
            status=CheckStatus.WARN,
            detail="not configured (cluster naming will use numeric IDs)",
        )
    return CheckResult(
        name="Anthropic API key",
        status=CheckStatus.OK,
        detail="configured",
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_surgeon.py::TestCheckAnthropicApiKey -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/yt_brain/application/surgeon.py tests/test_surgeon.py
git commit -m "Add Anthropic API key check to surgeon"
```

### Task 5: Browser cookies and database status checks

**Files:**
- Modify: `src/yt_brain/application/surgeon.py`
- Modify: `tests/test_surgeon.py`

- [ ] **Step 1: Write the failing tests for `check_browser_cookies` and `check_database`**

```python
# append to tests/test_surgeon.py
from yt_brain.application.surgeon import check_browser_cookies, check_database


class TestCheckBrowserCookies:
    def test_reports_untested(self):
        result = check_browser_cookies()
        assert result.status == CheckStatus.INFO
        assert "untested" in result.detail.lower()


class TestCheckDatabase:
    def test_empty_db(self, temp_db):
        result = check_database(temp_db)
        assert result.status == CheckStatus.INFO
        assert "0 videos" in result.detail

    def test_db_with_videos(self, temp_db):
        from yt_brain.domain.models import EngagementLevel, Source, Video
        from yt_brain.infrastructure.database import save_video

        video = Video(
            youtube_id="test1",
            title="Test",
            description="",
            channel_id="ch1",
            duration_seconds=100,
            watched_seconds=50,
            watched_at=None,
            engagement_level=EngagementLevel.UNKNOWN,
            transcript="",
            tags=[],
            source=Source.MANUAL,
        )
        save_video(temp_db, video)
        result = check_database(temp_db)
        assert result.status == CheckStatus.INFO
        assert "1 video" in result.detail
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_surgeon.py::TestCheckBrowserCookies tests/test_surgeon.py::TestCheckDatabase -v`
Expected: FAIL — `ImportError`

- [ ] **Step 3: Implement both checks**

```python
# add to src/yt_brain/application/surgeon.py
import sqlite3
from pathlib import Path


def check_browser_cookies() -> CheckResult:
    return CheckResult(
        name="Browser cookies",
        status=CheckStatus.INFO,
        detail="untested (run 'yt-brain sync' to verify)",
    )


def check_database(db_path: Path) -> CheckResult:
    if not db_path.exists():
        return CheckResult(name="Database", status=CheckStatus.INFO, detail="no database yet")
    try:
        conn = sqlite3.connect(db_path)
        video_count = conn.execute("SELECT COUNT(*) FROM videos").fetchone()[0]

        # Check for embeddings table (may not exist if vec migrations skipped)
        embedding_count = 0
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        if "video_embeddings" in tables:
            embedding_count = conn.execute("SELECT COUNT(*) FROM video_embeddings").fetchone()[0]

        cluster_count = 0
        if "video_clusters" in tables:
            cluster_count = conn.execute("SELECT COUNT(*) FROM video_clusters").fetchone()[0]

        conn.close()

        parts = [f"{video_count} video{'s' if video_count != 1 else ''}"]
        if embedding_count:
            parts.append(f"{embedding_count} embeddings")
        if cluster_count:
            parts.append(f"{cluster_count} clusters")

        return CheckResult(name="Database", status=CheckStatus.INFO, detail=" | ".join(parts))
    except Exception as e:
        return CheckResult(name="Database", status=CheckStatus.WARN, detail=f"error reading: {e}")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_surgeon.py::TestCheckBrowserCookies tests/test_surgeon.py::TestCheckDatabase -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/yt_brain/application/surgeon.py tests/test_surgeon.py
git commit -m "Add browser cookies and database checks to surgeon"
```

### Task 6: `run_surgeon` orchestrator and CLI command

**Files:**
- Modify: `src/yt_brain/application/surgeon.py`
- Modify: `src/yt_brain/cli.py`
- Modify: `tests/test_surgeon.py`

- [ ] **Step 1: Write the failing test for `run_surgeon`**

```python
# append to tests/test_surgeon.py
from yt_brain.application.surgeon import run_surgeon


class TestRunSurgeon:
    def test_returns_all_checks(self, temp_db):
        with (
            patch("yt_brain.application.surgeon.SQLITE_VEC_AVAILABLE", True),
            patch(
                "yt_brain.application.surgeon.subprocess.run",
                return_value=subprocess.CompletedProcess(args=[], returncode=0, stdout="2024.12.1"),
            ),
        ):
            results = run_surgeon(
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
        assert "Browser cookies" in names
        assert "Database" in names

    def test_has_failures_returns_true_when_fail(self, temp_db):
        with (
            patch("yt_brain.application.surgeon.SQLITE_VEC_AVAILABLE", False),
            patch(
                "yt_brain.application.surgeon.subprocess.run",
                side_effect=FileNotFoundError,
            ),
        ):
            results = run_surgeon(
                youtube_api_key="",
                anthropic_api_key="",
                db_path=temp_db,
            )
        failures = [r for r in results if r.status == CheckStatus.FAIL]
        assert len(failures) >= 2  # sqlite-vec + yt-dlp + youtube key
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_surgeon.py::TestRunSurgeon -v`
Expected: FAIL — `ImportError: cannot import name 'run_surgeon'`

- [ ] **Step 3: Implement `run_surgeon`**

```python
# add to src/yt_brain/application/surgeon.py
def run_surgeon(
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_surgeon.py::TestRunSurgeon -v`
Expected: PASS

- [ ] **Step 5: Register the CLI command**

Add to `src/yt_brain/cli.py`, after the `config` command (around line 510):

```python
@app.command()
def surgeon() -> None:
    """Check that all prerequisites are installed and configured."""
    from yt_brain.application.surgeon import CheckStatus, run_surgeon
    from yt_brain.infrastructure.config import load_config

    config = load_config()
    db_path = config.db_path

    results = run_surgeon(
        youtube_api_key=config.youtube_api_key,
        anthropic_api_key=config.anthropic_api_key,
        db_path=db_path,
    )

    console.print()
    console.print("[bold]yt-brain prerequisites check[/bold]")
    console.print("─" * 34)

    status_icons = {
        CheckStatus.OK: "[green]✅[/green]",
        CheckStatus.FAIL: "[red]❌[/red]",
        CheckStatus.WARN: "[yellow]⚠️[/yellow] ",
        CheckStatus.INFO: "[blue]ℹ️[/blue] ",
    }

    for r in results:
        icon = status_icons[r.status]
        console.print(f" {icon} {r.name:<20s} {r.detail}")

    failures = [r for r in results if r.status == CheckStatus.FAIL]
    warnings = [r for r in results if r.status == CheckStatus.WARN]

    console.print()
    if failures:
        console.print(f"[red]❌ {len(failures)} issue(s) found. See INSTALL.md for setup instructions.[/red]")
        raise typer.Exit(1)
    elif warnings:
        console.print(f"[yellow]⚠️  {len(warnings)} warning(s). Everything critical is OK.[/yellow]")
    else:
        console.print("[green]All prerequisites OK.[/green]")
```

- [ ] **Step 6: Write CLI integration test**

```python
# append to tests/test_surgeon.py
class TestSurgeonCli:
    def test_surgeon_runs(self, temp_config_dir):
        from typer.testing import CliRunner

        from yt_brain.cli import app

        runner = CliRunner()
        with (
            patch("yt_brain.application.surgeon.SQLITE_VEC_AVAILABLE", True),
            patch(
                "yt_brain.application.surgeon.subprocess.run",
                return_value=subprocess.CompletedProcess(args=[], returncode=0, stdout="2024.12.1"),
            ),
            patch("yt_brain.application.surgeon.urllib.request.urlopen") as mock_url,
        ):
            mock_resp = MagicMock()
            mock_resp.read.return_value = json.dumps({"items": []}).encode()
            mock_resp.__enter__ = lambda s: s
            mock_resp.__exit__ = MagicMock(return_value=False)
            mock_url.return_value = mock_resp
            result = runner.invoke(app, ["surgeon"])

        assert "prerequisites check" in result.output
        assert "sqlite-vec" in result.output
        assert "yt-dlp" in result.output

    def test_surgeon_exit_code_1_on_failure(self, temp_config_dir):
        from typer.testing import CliRunner

        from yt_brain.cli import app

        runner = CliRunner()
        with (
            patch("yt_brain.application.surgeon.SQLITE_VEC_AVAILABLE", False),
            patch(
                "yt_brain.application.surgeon.subprocess.run",
                side_effect=FileNotFoundError,
            ),
        ):
            result = runner.invoke(app, ["surgeon"])

        assert result.exit_code == 1
        assert "issue(s) found" in result.output
```

- [ ] **Step 7: Run full test suite**

Run: `uv run pytest tests/test_surgeon.py -v`
Expected: All PASS

- [ ] **Step 8: Run lint and type check**

Run: `uv run ruff check src/yt_brain/application/surgeon.py tests/test_surgeon.py && uv run mypy src/yt_brain/application/surgeon.py`
Expected: Clean

- [ ] **Step 9: Commit**

```bash
git add src/yt_brain/application/surgeon.py tests/test_surgeon.py src/yt_brain/cli.py
git commit -m "Add yt-brain surgeon CLI command for prerequisite checking"
```

---

## Phase 2: PyPI Publishing

### Task 7: Package metadata for PyPI

**Files:**
- Modify: `pyproject.toml`

- [ ] **Step 1: Add PyPI metadata to `pyproject.toml`**

Add `[project.urls]` section and classifiers. Update the existing `[project]` section:

```toml
# Add after the existing license line in [project]
classifiers = [
    "Development Status :: 4 - Beta",
    "Environment :: Console",
    "Intended Audience :: End Users/Desktop",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.12",
    "Topic :: Multimedia :: Video",
]

[project.urls]
Homepage = "https://github.com/jayers99/yt-brain"
Repository = "https://github.com/jayers99/yt-brain"
"Bug Tracker" = "https://github.com/jayers99/yt-brain/issues"
```

- [ ] **Step 2: Verify the package builds**

Run: `uv run python -m build`
Expected: Creates `dist/yt_brain-0.1.0-py3-none-any.whl` and `dist/yt-brain-0.1.0.tar.gz`

Note: If `build` is not available, install it first: `uv run pip install build`. Alternatively: `uvx --from build pyproject-build`

- [ ] **Step 3: Verify the wheel installs and `yt-brain` entry point works**

Run: `uv run pip install dist/yt_brain-0.1.0-py3-none-any.whl --force-reinstall && uv run yt-brain --help`
Expected: Help text shows all commands including `surgeon`

- [ ] **Step 4: Commit**

```bash
git add pyproject.toml
git commit -m "Add PyPI classifiers and project URLs"
```

### Task 8: GitHub Actions publish workflow

**Files:**
- Create: `.github/workflows/publish.yml`

- [ ] **Step 1: Create the publish workflow**

```yaml
# .github/workflows/publish.yml
name: Publish to PyPI

on:
  release:
    types: [published]

permissions:
  id-token: write  # Required for trusted publishing

jobs:
  publish:
    runs-on: ubuntu-latest
    environment: pypi

    steps:
      - uses: actions/checkout@v4

      - name: Set up uv
        uses: astral-sh/setup-uv@v5
        with:
          enable-cache: true

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install build tools
        run: uv tool install build

      - name: Build package
        run: uvx --from build pyproject-build

      - name: Publish to PyPI
        uses: pypa/gh-action-pypi-publish@release/v1
```

- [ ] **Step 2: Commit**

```bash
git add .github/workflows/publish.yml
git commit -m "Add GitHub Actions workflow for PyPI publishing"
```

- [ ] **Step 3: Note — manual PyPI trusted publisher setup required**

Before the first release, configure trusted publishing on PyPI:
1. Go to https://pypi.org/manage/account/publishing/
2. Add new pending publisher:
   - PyPI project name: `yt-brain`
   - Owner: `jayers99`
   - Repository: `yt-brain`
   - Workflow name: `publish.yml`
   - Environment name: `pypi`

Also create the `pypi` environment in GitHub repo settings:
1. Go to repo Settings > Environments
2. Create environment named `pypi`

---

## Phase 3: README + INSTALL.md Rewrite

### Task 9: Create INSTALL.md

**Files:**
- Create: `INSTALL.md`

- [ ] **Step 1: Write INSTALL.md**

```markdown
# Installation & Setup Guide

> **Important:** yt-brain requires external tools and API keys to function. Installing the Python package alone is not enough. Follow this guide completely before using the application.

## 1. Install yt-brain

Choose one:

```bash
# Recommended: permanent global install
uv tool install yt-brain

# Or: install into an existing Python environment
pip install yt-brain

# Or: one-off run without installing
uvx yt-brain

# Or: install from source (for development)
git clone https://github.com/jayers99/yt-brain.git
cd yt-brain
uv sync
# Commands use: uv run yt-brain <command>
```

## 2. Prerequisites

### a. yt-dlp

Required for syncing new watch history and fetching transcripts.

**Install:**

```bash
# Recommended
uv tool install yt-dlp

# Or via Homebrew (macOS)
brew install yt-dlp
```

**Browser cookie access:** yt-dlp reads your YouTube login cookies to access watch history. You must be logged into YouTube in your browser.

- **macOS:** Grant Full Disk Access to your terminal app (System Settings > Privacy & Security > Full Disk Access)
- **Supported browsers:** Chrome, Firefox, Edge, Safari, Opera, Brave

### b. YouTube Data API key

Required for enriching video metadata (upload dates, categories, descriptions).

1. Create a project in [Google Cloud Console](https://console.cloud.google.com)
2. Enable **YouTube Data API v3**
3. Create an API key under **Credentials**
4. Configure it:

```bash
# Option 1: Environment variable
export YOUTUBE_API_KEY="your-key-here"

# Option 2: Config file (~/.config/yt-brain/config.yaml)
youtube_api_key: your-key-here
```

### c. Anthropic API key (optional)

Used for AI-powered cluster naming. Without it, clusters get numeric IDs instead of descriptive names.

```bash
# Option 1: Environment variable
export ANTHROPIC_API_KEY="your-key-here"

# Option 2: Config file (~/.config/yt-brain/config.yaml)
anthropic_api_key: your-key-here
```

## 3. Import Your Data

### Google Takeout (recommended starting point)

Google Takeout is the only way to get your full watch history. This is a one-time bulk import.

1. Go to [takeout.google.com](https://takeout.google.com)
2. Deselect all, then select only **YouTube and YouTube Music** > **history**
3. Choose **JSON** format (not HTML)
4. Export and download the zip
5. Import:

```bash
yt-brain ingest takeout ~/Downloads/takeout-*.zip
```

You should see: `Ingested <N> videos from Takeout.` where N is typically hundreds to thousands.

## 4. Verify Setup

Run the surgeon command to check everything is configured:

```bash
yt-brain surgeon
```

All critical checks should show ✅. Fix any ❌ items using the instructions above.

## 5. Quick Start

After setup, here's the typical workflow:

```bash
# Enrich your imported data with metadata
yt-brain backfill-channels       # Fill channel names (no API key needed)
yt-brain backfill-categories     # Fill video categories (needs YouTube API key)
yt-brain backfill-dates          # Fill upload dates (needs YouTube API key)
yt-brain backfill-descriptions   # Fill descriptions (needs YouTube API key)

# Generate semantic embeddings for search
yt-brain embed
# This downloads the all-MiniLM-L6-v2 model (~80MB) on first run
# and processes all videos. Takes 1-2 minutes for ~1000 videos.

# Launch the dashboard
yt-brain dashboard
# Opens http://localhost:5555 in your browser

# Keep data current (run periodically)
yt-brain sync
```

## 6. Troubleshooting

### sqlite-vec installation issues

sqlite-vec is a native SQLite extension for semantic search. If it fails to install:

- **macOS (Apple Silicon):** Usually works with `uv sync`. If not: `brew install sqlite` first
- **macOS (Intel):** `brew install sqlite && uv sync`
- **Linux (x86_64):** Install `libsqlite3-dev` (`apt install libsqlite3-dev`), then reinstall
- **Linux (ARM):** Build from source: `pip install sqlite-vec --no-binary sqlite-vec`

When sqlite-vec is unavailable, dashboard search falls back to text matching. All other features work normally.

### "Could not extract cookies" / sync fails

- Ensure you're logged into YouTube in your browser
- macOS: grant Full Disk Access to your terminal (System Settings > Privacy & Security)
- Try a different browser: `yt-brain sync --browser firefox`

### "Missing youtube_api_key"

Set your API key via environment variable or config file. See [Prerequisites](#b-youtube-data-api-key) above.

### "Not enough videos to cluster"

You need at least 10 videos with embeddings. Run `yt-brain embed` first, then `yt-brain cluster --rebuild`.

### Config location

All data is stored in `~/.config/yt-brain/`:
- `config.yaml` — API keys, thresholds
- `yt-brain.db` — SQLite database with all video data

Override with: `export YT_BRAIN_CONFIG_DIR=/path/to/dir`
```

- [ ] **Step 2: Commit**

```bash
git add INSTALL.md
git commit -m "Add comprehensive INSTALL.md setup guide"
```

### Task 10: Rewrite README.md

**Files:**
- Rewrite: `README.md`

- [ ] **Step 1: Rewrite README.md as a landing page**

```markdown
[![CI](https://github.com/jayers99/yt-brain/actions/workflows/ci.yml/badge.svg)](https://github.com/jayers99/yt-brain/actions/workflows/ci.yml)

# yt-brain

Turn passive YouTube watching into active knowledge.

yt-brain ingests your YouTube watch history, classifies videos by genre and channel, and provides an interactive dashboard to explore your viewing patterns.

![yt-brain Dashboard](docs/app_screen_shot.png)

## Features

- **Semantic search** — find videos by meaning, not just keywords (powered by sentence-transformers + sqlite-vec)
- **Genre classification** — automatic categorization using YouTube categories and keyword analysis
- **Interactive dashboard** — filter by genre, channel, time range, and starred channels simultaneously
- **Incremental sync** — stay current with new watches via yt-dlp browser cookie integration
- **AI-powered clustering** — discover viewing patterns with HDBSCAN + Claude-generated topic names
- **Google Takeout import** — bulk import your full watch history

## Install

```bash
pip install yt-brain
```

**[Installation & Setup Guide](INSTALL.md)** — yt-brain requires external tools and API keys. Follow the setup guide before first use.

## Commands

| Command | Description |
|---------|-------------|
| `ingest takeout <path>` | Import from Google Takeout (zip or directory) |
| `ingest video <url>` | Add a single video by URL |
| `sync [--browser chrome]` | Fetch and add new videos since last sync |
| `embed [--rebuild]` | Generate semantic embeddings for search |
| `cluster [--rebuild]` | Run topic clustering on embedded videos |
| `dashboard [--port 5555]` | Launch web dashboard |
| `surgeon` | Check that prerequisites are installed and configured |
| `status` | Show video counts by engagement tier |
| `classify` | Run engagement classification |
| `backfill-channels` | Fill missing channel names |
| `backfill-categories` | Fill missing categories (needs API key) |
| `backfill-dates` | Fill missing dates (needs API key) |
| `backfill-descriptions` | Fill missing descriptions (needs API key) |
| `transcript <video_id>` | Fetch transcript via yt-dlp |
| `config` | Show current configuration |

## Dashboard

The web dashboard provides:

- **Genre Breakdown** with checkboxes to filter by genre
- **Channel Breakdown** with clickable links to YouTube
- **Semantic Search** — find videos by topic or concept, not just exact words
- **Time filter** dropdown (1 day, 1 week, 1 month, 6 months, 1-5 years, all)
- **Date range** display based on actual watch dates

### Search Syntax

| Query | Behavior |
|-------|----------|
| `machine learning` | Semantic search — finds related videos by meaning |
| `"kubernetes"` | Semantic + exact match on "kubernetes" in title or description |
| `title:"Claude"` | Exact match in title only (case-insensitive) |
| `desc:"tutorial"` | Exact match in description only |
| `channel:"3Blue1Brown"` | Exact match in channel name |
| `AI agents title:"python"` | Semantic search for "AI agents", filtered to titles containing "python" |

## Architecture

Hexagonal architecture with swappable infrastructure adapters:

```
src/yt_brain/
├── cli.py                  # Typer CLI entry point
├── domain/                 # Pure models, classification logic
├── application/            # Service orchestration
├── infrastructure/         # SQLite, YouTube API, Takeout parser, yt-dlp
└── web/                    # Flask dashboard, genre classifier
```

Data stored in SQLite at `~/.config/yt-brain/yt-brain.db`.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup and guidelines.

## License

MIT
```

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "Rewrite README as landing page, link to INSTALL.md"
```

### Task 11: Move Makefile docs to CONTRIBUTING.md

**Files:**
- Modify: `CONTRIBUTING.md`

- [ ] **Step 1: Read current CONTRIBUTING.md**

Read `CONTRIBUTING.md` to see current content.

- [ ] **Step 2: Add Makefile section to CONTRIBUTING.md**

Add after the existing setup section:

```markdown
### Makefile

A `Makefile` is included for common dev tasks:

| Target | Command |
|--------|---------|
| `make install` | `uv sync` — install core dependencies |
| `make dev` | `uv sync --dev --extra ai` — install all dev + optional deps |
| `make test` | `uv run pytest -v` |
| `make lint` | `uv run ruff check src/ tests/` |
| `make typecheck` | `uv run mypy` |
| `make run` | `uv run yt-brain dashboard` |
| `make clean` | Remove `__pycache__`, caches, build artifacts |

Run `make` with no arguments to see available targets.
```

- [ ] **Step 3: Commit**

```bash
git add CONTRIBUTING.md
git commit -m "Move Makefile docs from README to CONTRIBUTING.md"
```

### Task 12: Final verification

- [ ] **Step 1: Run full test suite**

Run: `uv run pytest -x -q`
Expected: All tests pass

- [ ] **Step 2: Run lint and type check**

Run: `uv run ruff check src/ tests/ && uv run mypy`
Expected: Clean

- [ ] **Step 3: Verify `yt-brain surgeon` works end-to-end**

Run: `uv run yt-brain surgeon`
Expected: See formatted output with status of all 6 checks

- [ ] **Step 4: Verify `yt-brain --help` shows surgeon command**

Run: `uv run yt-brain --help`
Expected: `surgeon` appears in command list
