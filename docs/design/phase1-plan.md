# yt-brain Phase 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Praxis extension that ingests YouTube history (Takeout + API + manual), classifies videos by engagement level, and provides a review/status CLI.

**Architecture:** Hexagonal architecture matching existing Praxis extensions (steward, render-run). Domain layer holds pure models and classification logic. Infrastructure adapters handle SQLite, YouTube API, Takeout parsing, and yt-dlp. Application layer orchestrates workflows. Typer CLI delegates to application services.

**Tech Stack:** Python 3.12+, Poetry, Typer, Rich, Pydantic, SQLite3 (stdlib), yt-dlp, google-api-python-client, google-auth-oauthlib, PyYAML, pytest, pytest-bdd

---

## Deferred to Phase 1.5

- **YouTube Data API adapter** (`youtube_api.py`, `yt-brain ingest api`): Requires OAuth2 setup and Google Cloud project. Takeout + manual ingestion cover the initial workflow. API sync will be added as a follow-up once the core is solid.

---

## File Map

| File | Responsibility |
|------|---------------|
| `pyproject.toml` | Poetry config, deps, entry point |
| `CLAUDE.md` | Extension docs for AI assistants |
| `bin/yt-brain` | Workspace wrapper script |
| `src/yt_brain/__init__.py` | Package init |
| `src/yt_brain/cli.py` | Typer app, all commands |
| `src/yt_brain/domain/__init__.py` | Domain package |
| `src/yt_brain/domain/models.py` | Video, Channel, Playlist, EngagementLevel, Source enums |
| `src/yt_brain/domain/classifier.py` | Engagement classification logic (pure) |
| `src/yt_brain/domain/errors.py` | Domain exceptions |
| `src/yt_brain/application/__init__.py` | Application package |
| `src/yt_brain/application/ingest.py` | Ingest orchestration service |
| `src/yt_brain/application/classify.py` | Classification orchestration service |
| `src/yt_brain/application/review.py` | Review workflow service |
| `src/yt_brain/application/status.py` | Status dashboard service |
| `src/yt_brain/application/transcript.py` | Transcript fetch service |
| `src/yt_brain/infrastructure/__init__.py` | Infrastructure package |
| `src/yt_brain/infrastructure/config.py` | Config loading (YAML + env vars) |
| `src/yt_brain/infrastructure/database.py` | SQLite repository (init, migrations, CRUD) |
| `src/yt_brain/infrastructure/takeout_parser.py` | Google Takeout JSON/HTML parser |
| `src/yt_brain/infrastructure/youtube_api.py` | YouTube Data API v3 adapter |
| `src/yt_brain/infrastructure/ytdlp_adapter.py` | yt-dlp wrapper for transcripts + metadata |
| `migrations/001_initial_schema.sql` | Initial SQLite schema |
| `tests/conftest.py` | Shared fixtures (temp DB, temp config) |
| `tests/features/classify.feature` | Classification BDD scenarios |
| `tests/features/ingest_takeout.feature` | Takeout ingestion BDD scenarios |
| `tests/features/ingest_manual.feature` | Manual video ingestion BDD scenarios |
| `tests/features/review.feature` | Review BDD scenarios |
| `tests/features/status.feature` | Status dashboard BDD scenarios |
| `tests/step_defs/test_classify.py` | Classification step definitions |
| `tests/step_defs/test_ingest_takeout.py` | Takeout ingestion step definitions |
| `tests/step_defs/test_ingest_manual.py` | Manual ingestion step definitions |
| `tests/step_defs/test_review.py` | Review step definitions |
| `tests/step_defs/test_status.py` | Status dashboard step definitions |

All paths below are relative to `` unless otherwise noted.

---

### Task 1: Project Scaffold

**Files:**
- Create: `pyproject.toml`
- Create: `CLAUDE.md`
- Create: `src/yt_brain/__init__.py`
- Create: `src/yt_brain/cli.py`
- Create: `src/yt_brain/domain/__init__.py`
- Create: `src/yt_brain/application/__init__.py`
- Create: `src/yt_brain/infrastructure/__init__.py`
- Create: `bin/yt-brain` (workspace root)

- [ ] **Step 1: Create pyproject.toml**

```toml
[tool.poetry]
name = "yt-brain"
version = "0.1.0"
description = "YouTube knowledge brain — ingest, classify, and curate your YouTube activity"
authors = ["jayers99"]
readme = "README.md"
license = "MIT"

packages = [{ include = "yt-brain", from = "src" }]

[tool.poetry.scripts]
yt-brain = "yt_brain.cli:app"

[tool.poetry.dependencies]
python = "^3.12"
typer = "^0.15.1"
rich = "^13.9.4"
pydantic = "^2.10.4"
pyyaml = "^6.0.2"

[tool.poetry.group.dev.dependencies]
pytest = "^8.3.4"
pytest-bdd = "^8.1.0"
ruff = "^0.8.4"
mypy = "^1.14.1"
types-pyyaml = "^6.0.12"
pre-commit = "^4.5.1"

[tool.ruff]
line-length = 120
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B", "SIM"]

[tool.ruff.lint.per-file-ignores]
"tests/*" = ["E501"]

[tool.mypy]
python_version = "3.12"
strict = true
warn_return_any = true
warn_unused_ignores = true
files = ["src"]
exclude = ["tests/"]

[[tool.mypy.overrides]]
module = ["tests.*"]
ignore_errors = true

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
```

- [ ] **Step 2: Create minimal cli.py**

```python
import typer

app = typer.Typer(
    name="yt-brain",
    help="YouTube knowledge brain — ingest, classify, and curate your YouTube activity.",
    no_args_is_help=True,
)


@app.callback()
def main() -> None:
    """yt-brain - YouTube Knowledge Brain."""
    pass


if __name__ == "__main__":
    app()
```

- [ ] **Step 3: Create package __init__.py files**

`src/yt_brain/__init__.py`:
```python
"""yt-brain — YouTube knowledge brain."""
```

`src/yt_brain/domain/__init__.py`, `src/yt_brain/application/__init__.py`, `src/yt_brain/infrastructure/__init__.py`:
```python
```
(empty files)

- [ ] **Step 4: Create CLAUDE.md**

```markdown
# yt-brain

YouTube Knowledge Brain — a Praxis extension for ingesting, classifying, and curating YouTube activity.

## Purpose

- Ingest YouTube watch history (Takeout export, API sync, manual URL)
- Classify videos by engagement level (bounced, watched, liked, curated)
- Review and override classifications
- Fetch transcripts on demand via yt-dlp
- Phase 1 of 4: foundation for semantic clustering, NotebookLM export, and Obsidian integration

## CLI Commands

```bash
yt-brain ingest takeout <path>     # Import Google Takeout export
yt-brain ingest api                # Sync via YouTube Data API
yt-brain ingest video <url>        # Add a single video manually
yt-brain classify                  # Run engagement classification
yt-brain review                    # Interactive review by tier
yt-brain status                    # Dashboard counts
yt-brain transcript <video_id>    # Fetch transcript via yt-dlp
yt-brain config                    # Show/set configuration
```

## Architecture

Hexagonal architecture:
- `domain/` — Pure models, classification logic, errors
- `application/` — Service orchestration (ingest, classify, review, status, transcript)
- `infrastructure/` — SQLite, YouTube API, Takeout parser, yt-dlp, config

## Key Files

| File | Purpose |
|------|---------|
| `src/yt_brain/cli.py` | Typer entry point |
| `src/yt_brain/domain/models.py` | Video, Channel, Playlist, EngagementLevel |
| `src/yt_brain/domain/classifier.py` | Engagement classification logic |
| `src/yt_brain/infrastructure/database.py` | SQLite repository |
| `src/yt_brain/infrastructure/takeout_parser.py` | Google Takeout parser |
| `tests/features/` | BDD scenarios |

## Data

- SQLite DB: `~/.config/yt-brain/yt-brain.db`
- Config: `~/.config/yt-brain/config.yaml`
```

- [ ] **Step 5: Create bin/yt-brain wrapper**

File: `bin/yt-brain` (at workspace root `/Users/jayers/code/praxis-workspace/bin/yt-brain`)

```bash
#!/bin/bash
exec poetry -C "$PRAXIS_HOME/extensions/yt-brain" run yt-brain "$@"
```

- [ ] **Step 6: Make wrapper executable and install deps**

```bash
chmod +x bin/yt-brain
cd extensions/yt-brain && poetry install
```

- [ ] **Step 7: Verify CLI boots**

Run: `cd extensions/yt-brain && poetry run yt-brain --help`
Expected: Help text showing "YouTube knowledge brain" and no commands yet (just `--help`)

- [ ] **Step 8: Commit**

```bash
git add  bin/yt-brain
git commit -m "scaffold yt-brain extension with Poetry, Typer, and bin wrapper"
```

---

### Task 2: Domain Models & Errors

**Files:**
- Create: `src/yt_brain/domain/models.py`
- Create: `src/yt_brain/domain/errors.py`
- Create: `tests/features/models.feature`
- Create: `tests/step_defs/test_models.py`
- Create: `tests/conftest.py`

- [ ] **Step 1: Write BDD feature for domain models**

File: `tests/features/models.feature`
```gherkin
Feature: Domain Models
  Core data models for yt-brain.

  Scenario: Create a video with engagement level
    Given a video with youtube_id "abc123" and duration 600
    When the video watched_seconds is 540
    Then the video engagement_level is "UNKNOWN"
    And the video source is "manual"

  Scenario: EngagementLevel ordering
    Then CURATED is higher than LIKED
    And LIKED is higher than WATCHED
    And WATCHED is higher than BOUNCED
    And BOUNCED is higher than UNKNOWN
```

- [ ] **Step 2: Write step definitions**

File: `tests/step_defs/test_models.py`
```python
from pytest_bdd import given, scenarios, then, when, parsers

scenarios("../features/models.feature")


@given(parsers.parse('a video with youtube_id "{youtube_id}" and duration {duration:d}'), target_fixture="video")
def create_video(youtube_id: str, duration: int):
    from yt_brain.domain.models import Video, EngagementLevel, Source

    return Video(
        youtube_id=youtube_id,
        title="Test Video",
        channel_id="ch1",
        duration_seconds=duration,
        engagement_level=EngagementLevel.UNKNOWN,
        source=Source.MANUAL,
    )


@when(parsers.parse("the video watched_seconds is {seconds:d}"))
def set_watched(video, seconds: int):
    video.watched_seconds = seconds


@then(parsers.parse('the video engagement_level is "{level}"'))
def check_engagement(video, level: str):
    from yt_brain.domain.models import EngagementLevel

    assert video.engagement_level == EngagementLevel(level)


@then(parsers.parse('the video source is "{source}"'))
def check_source(video, source: str):
    from yt_brain.domain.models import Source

    assert video.source == Source(source)


@then(parsers.parse("{higher} is higher than {lower}"))
def check_ordering(higher: str, lower: str):
    from yt_brain.domain.models import EngagementLevel

    level_order = [EngagementLevel.UNKNOWN, EngagementLevel.BOUNCED, EngagementLevel.WATCHED, EngagementLevel.LIKED, EngagementLevel.CURATED]
    higher_idx = level_order.index(EngagementLevel(higher))
    lower_idx = level_order.index(EngagementLevel(lower))
    assert higher_idx > lower_idx
```

- [ ] **Step 3: Create conftest.py**

File: `tests/conftest.py`
```python
import os
import tempfile
from collections.abc import Generator
from pathlib import Path

import pytest


@pytest.fixture
def temp_config_dir() -> Generator[Path, None, None]:
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir)
        old_env = os.environ.get("YT_BRAIN_CONFIG_DIR")
        os.environ["YT_BRAIN_CONFIG_DIR"] = str(path)
        try:
            yield path
        finally:
            if old_env is None:
                os.environ.pop("YT_BRAIN_CONFIG_DIR", None)
            else:
                os.environ["YT_BRAIN_CONFIG_DIR"] = old_env


@pytest.fixture
def temp_db(temp_config_dir: Path) -> Path:
    from yt_brain.infrastructure.database import init_db

    db_path = temp_config_dir / "yt-brain.db"
    init_db(db_path)
    return db_path
```

- [ ] **Step 4: Run tests to verify they fail**

Run: `cd extensions/yt-brain && poetry run pytest tests/step_defs/test_models.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'yt-brain.domain.models'`

- [ ] **Step 5: Implement domain models**

File: `src/yt_brain/domain/models.py`
```python
from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class EngagementLevel(str, Enum):
    UNKNOWN = "UNKNOWN"
    BOUNCED = "BOUNCED"
    WATCHED = "WATCHED"
    LIKED = "LIKED"
    CURATED = "CURATED"


ENGAGEMENT_ORDER = [
    EngagementLevel.UNKNOWN,
    EngagementLevel.BOUNCED,
    EngagementLevel.WATCHED,
    EngagementLevel.LIKED,
    EngagementLevel.CURATED,
]


class Source(str, Enum):
    API = "api"
    TAKEOUT = "takeout"
    MANUAL = "manual"


class Video(BaseModel):
    youtube_id: str
    title: str
    description: str = ""
    channel_id: str
    duration_seconds: int = 0
    watched_seconds: int | None = None
    watched_at: datetime | None = None
    engagement_level: EngagementLevel = EngagementLevel.UNKNOWN
    engagement_override: EngagementLevel | None = None
    transcript: str | None = None
    tags: list[str] = Field(default_factory=list)
    source: Source = Source.MANUAL

    @property
    def effective_engagement(self) -> EngagementLevel:
        return self.engagement_override if self.engagement_override is not None else self.engagement_level

    @property
    def watch_percentage(self) -> float | None:
        if self.watched_seconds is None or self.duration_seconds == 0:
            return None
        return self.watched_seconds / self.duration_seconds


class Channel(BaseModel):
    youtube_id: str
    name: str
    url: str = ""
    subscription_status: bool = False


class Playlist(BaseModel):
    youtube_id: str
    title: str
    is_user_created: bool = True
    video_ids: list[str] = Field(default_factory=list)
```

- [ ] **Step 6: Implement domain errors**

File: `src/yt_brain/domain/errors.py`
```python
class YtbrainError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class VideoNotFoundError(YtbrainError):
    pass


class ConfigError(YtbrainError):
    pass


class IngestError(YtbrainError):
    pass


class DatabaseError(YtbrainError):
    pass
```

- [ ] **Step 7: Run tests to verify they pass**

Run: `cd extensions/yt-brain && poetry run pytest tests/step_defs/test_models.py -v`
Expected: 2 passed

- [ ] **Step 8: Commit**

```bash
git add src/yt_brain/domain/ tests/
git commit -m "add domain models, errors, and BDD tests for Video, Channel, Playlist"
```

---

### Task 3: Engagement Classifier (Pure Domain Logic)

**Files:**
- Create: `src/yt_brain/domain/classifier.py`
- Create: `tests/features/classify.feature`
- Create: `tests/step_defs/test_classify.py`

- [ ] **Step 1: Write BDD feature for classification**

File: `tests/features/classify.feature`
```gherkin
Feature: Engagement Classification
  Classify videos by engagement signals.

  Scenario: Video watched less than 15% is bounced
    Given a video with duration 600 and watched 60
    When I classify the video
    Then the engagement level is "BOUNCED"

  Scenario: Video watched more than 85% is watched
    Given a video with duration 600 and watched 540
    When I classify the video
    Then the engagement level is "WATCHED"

  Scenario: Video between thresholds stays unknown
    Given a video with duration 600 and watched 300
    When I classify the video
    Then the engagement level is "UNKNOWN"

  Scenario: Liked video overrides watch time
    Given a video with duration 600 and watched 60
    And the video is liked
    When I classify the video
    Then the engagement level is "LIKED"

  Scenario: Curated video is highest tier
    Given a video with duration 600 and watched 60
    And the video is liked
    And the video is in a user playlist
    When I classify the video
    Then the engagement level is "CURATED"

  Scenario: No watch data stays unknown
    Given a video with no watch data
    When I classify the video
    Then the engagement level is "UNKNOWN"

  Scenario: Custom thresholds are respected
    Given a video with duration 600 and watched 120
    And the bounce threshold is 0.25
    When I classify the video
    Then the engagement level is "UNKNOWN"
```

- [ ] **Step 2: Write step definitions**

File: `tests/step_defs/test_classify.py`
```python
from pytest_bdd import given, parsers, scenarios, then, when

from yt_brain.domain.classifier import ClassificationContext, classify_video
from yt_brain.domain.models import EngagementLevel, Source, Video

scenarios("../features/classify.feature")


@given(parsers.parse("a video with duration {duration:d} and watched {watched:d}"), target_fixture="context")
def video_with_watch_data(duration: int, watched: int) -> ClassificationContext:
    video = Video(
        youtube_id="test1",
        title="Test",
        channel_id="ch1",
        duration_seconds=duration,
        watched_seconds=watched,
        source=Source.TAKEOUT,
    )
    return ClassificationContext(video=video, is_liked=False, is_in_playlist=False)


@given("a video with no watch data", target_fixture="context")
def video_no_watch_data() -> ClassificationContext:
    video = Video(
        youtube_id="test1",
        title="Test",
        channel_id="ch1",
        duration_seconds=600,
        source=Source.API,
    )
    return ClassificationContext(video=video, is_liked=False, is_in_playlist=False)


@given("the video is liked")
def mark_liked(context: ClassificationContext) -> None:
    context.is_liked = True


@given("the video is in a user playlist")
def mark_in_playlist(context: ClassificationContext) -> None:
    context.is_in_playlist = True


@given(parsers.parse("the bounce threshold is {threshold:f}"))
def set_bounce_threshold(context: ClassificationContext, threshold: float) -> None:
    context.bounce_threshold = threshold


@when("I classify the video", target_fixture="result")
def do_classify(context: ClassificationContext) -> EngagementLevel:
    return classify_video(
        video=context.video,
        is_liked=context.is_liked,
        is_in_playlist=context.is_in_playlist,
        bounce_threshold=context.bounce_threshold,
        watched_threshold=context.watched_threshold,
    )


@then(parsers.parse('the engagement level is "{level}"'))
def check_level(result: EngagementLevel, level: str) -> None:
    assert result == EngagementLevel(level)
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `cd extensions/yt-brain && poetry run pytest tests/step_defs/test_classify.py -v`
Expected: FAIL — `ImportError: cannot import name 'ClassificationContext' from 'yt-brain.domain.classifier'`

- [ ] **Step 4: Implement classifier**

File: `src/yt_brain/domain/classifier.py`
```python
from __future__ import annotations

from dataclasses import dataclass, field

from yt_brain.domain.models import EngagementLevel, Video

DEFAULT_BOUNCE_THRESHOLD = 0.15
DEFAULT_WATCHED_THRESHOLD = 0.85


@dataclass
class ClassificationContext:
    video: Video
    is_liked: bool = False
    is_in_playlist: bool = False
    bounce_threshold: float = DEFAULT_BOUNCE_THRESHOLD
    watched_threshold: float = DEFAULT_WATCHED_THRESHOLD


def classify_video(
    video: Video,
    is_liked: bool = False,
    is_in_playlist: bool = False,
    bounce_threshold: float = DEFAULT_BOUNCE_THRESHOLD,
    watched_threshold: float = DEFAULT_WATCHED_THRESHOLD,
) -> EngagementLevel:
    """Classify a video's engagement level. Highest signal wins."""
    if is_in_playlist:
        return EngagementLevel.CURATED

    if is_liked:
        return EngagementLevel.LIKED

    watch_pct = video.watch_percentage
    if watch_pct is None:
        return EngagementLevel.UNKNOWN

    if watch_pct >= watched_threshold:
        return EngagementLevel.WATCHED

    if watch_pct < bounce_threshold:
        return EngagementLevel.BOUNCED

    return EngagementLevel.UNKNOWN
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd extensions/yt-brain && poetry run pytest tests/step_defs/test_classify.py -v`
Expected: 7 passed

- [ ] **Step 6: Commit**

```bash
git add src/yt_brain/domain/classifier.py tests/features/classify.feature tests/step_defs/test_classify.py
git commit -m "add engagement classifier with BDD tests — bounced/watched/liked/curated pyramid"
```

---

### Task 4: Config & Database Infrastructure

**Files:**
- Create: `src/yt_brain/infrastructure/config.py`
- Create: `src/yt_brain/infrastructure/database.py`
- Create: `migrations/001_initial_schema.sql`
- Create: `tests/features/database.feature`
- Create: `tests/step_defs/test_database.py`

- [ ] **Step 1: Write BDD feature for database**

File: `tests/features/database.feature`
```gherkin
Feature: Database Storage
  SQLite persistence for yt-brain.

  Scenario: Initialize database creates tables
    Given a fresh database
    Then the videos table exists
    And the channels table exists
    And the playlists table exists
    And the playlist_videos table exists
    And the schema_version is 1

  Scenario: Save and retrieve a video
    Given a fresh database
    And a video "abc123" titled "Test Video" from channel "ch1"
    When I save the video
    And I retrieve video "abc123"
    Then the retrieved video title is "Test Video"

  Scenario: Save duplicate video updates it
    Given a fresh database
    And a video "abc123" titled "Original" from channel "ch1"
    When I save the video
    And I save a video "abc123" titled "Updated" from channel "ch1"
    And I retrieve video "abc123"
    Then the retrieved video title is "Updated"

  Scenario: List videos by engagement level
    Given a fresh database
    And a saved video "v1" with engagement "BOUNCED"
    And a saved video "v2" with engagement "LIKED"
    And a saved video "v3" with engagement "LIKED"
    When I list videos with engagement "LIKED"
    Then I get 2 videos
```

- [ ] **Step 2: Write step definitions**

File: `tests/step_defs/test_database.py`
```python
import sqlite3

from pytest_bdd import given, parsers, scenarios, then, when

from yt_brain.domain.models import EngagementLevel, Source, Video
from yt_brain.infrastructure.database import (
    get_videos_by_engagement,
    get_video,
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
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `cd extensions/yt-brain && poetry run pytest tests/step_defs/test_database.py -v`
Expected: FAIL — `ImportError: cannot import name 'init_db' from 'yt-brain.infrastructure.database'`

- [ ] **Step 4: Create migration SQL**

File: `migrations/001_initial_schema.sql`
```sql
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS channels (
    youtube_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    url TEXT NOT NULL DEFAULT '',
    subscription_status INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS videos (
    youtube_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    channel_id TEXT NOT NULL,
    duration_seconds INTEGER NOT NULL DEFAULT 0,
    watched_seconds INTEGER,
    watched_at TEXT,
    engagement_level TEXT NOT NULL DEFAULT 'UNKNOWN',
    engagement_override TEXT,
    transcript TEXT,
    tags TEXT NOT NULL DEFAULT '[]',
    source TEXT NOT NULL DEFAULT 'manual',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (channel_id) REFERENCES channels(youtube_id)
);

CREATE TABLE IF NOT EXISTS playlists (
    youtube_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    is_user_created INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS playlist_videos (
    playlist_id TEXT NOT NULL,
    video_id TEXT NOT NULL,
    position INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (playlist_id, video_id),
    FOREIGN KEY (playlist_id) REFERENCES playlists(youtube_id),
    FOREIGN KEY (video_id) REFERENCES videos(youtube_id)
);

INSERT INTO schema_version (version) VALUES (1);
```

- [ ] **Step 5: Implement config**

File: `src/yt_brain/infrastructure/config.py`
```python
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from yt_brain.domain.errors import ConfigError

DEFAULT_CONFIG_DIR = Path.home() / ".config" / "praxis" / "yt-brain"
CONFIG_DIR_ENV = "YT_BRAIN_CONFIG_DIR"


@dataclass
class YtbrainConfig:
    config_dir: Path = field(default_factory=lambda: DEFAULT_CONFIG_DIR)
    youtube_api_key: str = ""
    oauth_credentials: Path = field(default_factory=lambda: DEFAULT_CONFIG_DIR / "oauth.json")
    bounce_threshold: float = 0.15
    watched_threshold: float = 0.85
    transcript_language: str = "en"

    @property
    def db_path(self) -> Path:
        return self.config_dir / "yt-brain.db"

    @property
    def config_file(self) -> Path:
        return self.config_dir / "config.yaml"


def get_config_dir() -> Path:
    env_val = os.environ.get(CONFIG_DIR_ENV)
    if env_val:
        return Path(env_val)
    return DEFAULT_CONFIG_DIR


def load_config() -> YtbrainConfig:
    config_dir = get_config_dir()
    config_file = config_dir / "config.yaml"

    config = YtbrainConfig(config_dir=config_dir)

    if config_file.exists():
        with open(config_file) as f:
            data = yaml.safe_load(f) or {}

        if "youtube_api_key" in data:
            config.youtube_api_key = data["youtube_api_key"]
        if "oauth_credentials" in data:
            config.oauth_credentials = Path(data["oauth_credentials"])
        if "thresholds" in data:
            thresholds = data["thresholds"]
            if "bounced_below" in thresholds:
                config.bounce_threshold = float(thresholds["bounced_below"])
            if "watched_above" in thresholds:
                config.watched_threshold = float(thresholds["watched_above"])
        if "transcript_language" in data:
            config.transcript_language = data["transcript_language"]

    return config


def save_config(config: YtbrainConfig) -> None:
    config.config_dir.mkdir(parents=True, exist_ok=True)
    data = {
        "youtube_api_key": config.youtube_api_key,
        "oauth_credentials": str(config.oauth_credentials),
        "thresholds": {
            "bounced_below": config.bounce_threshold,
            "watched_above": config.watched_threshold,
        },
        "transcript_language": config.transcript_language,
    }
    with open(config.config_file, "w") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)
```

- [ ] **Step 6: Implement database**

File: `src/yt_brain/infrastructure/database.py`
```python
from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from importlib import resources
from pathlib import Path

from yt_brain.domain.errors import DatabaseError, VideoNotFoundError
from yt_brain.domain.models import EngagementLevel, Source, Video


def init_db(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    try:
        migration_file = Path(__file__).parent.parent.parent.parent / "migrations" / "001_initial_schema.sql"
        if not migration_file.exists():
            raise DatabaseError(f"Migration file not found: {migration_file}")

        # Check if already initialized
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='schema_version'")
        if cursor.fetchone() is not None:
            return

        sql = migration_file.read_text()
        conn.executescript(sql)
    finally:
        conn.close()


def save_video(db_path: Path, video: Video) -> None:
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            """INSERT INTO videos (youtube_id, title, description, channel_id, duration_seconds,
                watched_seconds, watched_at, engagement_level, engagement_override,
                transcript, tags, source, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
            ON CONFLICT(youtube_id) DO UPDATE SET
                title=excluded.title, description=excluded.description,
                channel_id=excluded.channel_id, duration_seconds=excluded.duration_seconds,
                watched_seconds=excluded.watched_seconds, watched_at=excluded.watched_at,
                engagement_level=excluded.engagement_level,
                engagement_override=excluded.engagement_override,
                transcript=excluded.transcript, tags=excluded.tags,
                source=excluded.source, updated_at=datetime('now')""",
            (
                video.youtube_id,
                video.title,
                video.description,
                video.channel_id,
                video.duration_seconds,
                video.watched_seconds,
                video.watched_at.isoformat() if video.watched_at else None,
                video.engagement_level.value,
                video.engagement_override.value if video.engagement_override else None,
                video.transcript,
                json.dumps(video.tags),
                video.source.value,
            ),
        )
        conn.commit()
    finally:
        conn.close()


def get_video(db_path: Path, youtube_id: str) -> Video | None:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        cursor = conn.execute("SELECT * FROM videos WHERE youtube_id = ?", (youtube_id,))
        row = cursor.fetchone()
        if row is None:
            return None
        return _row_to_video(row)
    finally:
        conn.close()


def get_videos_by_engagement(db_path: Path, level: EngagementLevel) -> list[Video]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        cursor = conn.execute("SELECT * FROM videos WHERE engagement_level = ?", (level.value,))
        return [_row_to_video(row) for row in cursor.fetchall()]
    finally:
        conn.close()


def get_all_videos(db_path: Path) -> list[Video]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        cursor = conn.execute("SELECT * FROM videos ORDER BY watched_at DESC")
        return [_row_to_video(row) for row in cursor.fetchall()]
    finally:
        conn.close()


def get_video_count_by_engagement(db_path: Path) -> dict[str, int]:
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.execute("SELECT engagement_level, COUNT(*) FROM videos GROUP BY engagement_level")
        return dict(cursor.fetchall())
    finally:
        conn.close()


def update_engagement(db_path: Path, youtube_id: str, level: EngagementLevel, is_override: bool = False) -> None:
    conn = sqlite3.connect(db_path)
    try:
        if is_override:
            conn.execute(
                "UPDATE videos SET engagement_override = ?, updated_at = datetime('now') WHERE youtube_id = ?",
                (level.value, youtube_id),
            )
        else:
            conn.execute(
                "UPDATE videos SET engagement_level = ?, updated_at = datetime('now') WHERE youtube_id = ?",
                (level.value, youtube_id),
            )
        conn.commit()
    finally:
        conn.close()


def save_channel(db_path: Path, channel_id: str, name: str, url: str = "", subscribed: bool = False) -> None:
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            """INSERT INTO channels (youtube_id, name, url, subscription_status)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(youtube_id) DO UPDATE SET
                name=excluded.name, url=excluded.url,
                subscription_status=excluded.subscription_status""",
            (channel_id, name, url, int(subscribed)),
        )
        conn.commit()
    finally:
        conn.close()


def is_video_in_playlist(db_path: Path, youtube_id: str) -> bool:
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.execute(
            "SELECT 1 FROM playlist_videos pv JOIN playlists p ON pv.playlist_id = p.youtube_id WHERE pv.video_id = ? AND p.is_user_created = 1",
            (youtube_id,),
        )
        return cursor.fetchone() is not None
    finally:
        conn.close()


def is_video_liked(db_path: Path, youtube_id: str) -> bool:
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.execute("SELECT 1 FROM videos WHERE youtube_id = ? AND engagement_level = 'LIKED'", (youtube_id,))
        return cursor.fetchone() is not None
    finally:
        conn.close()


def _row_to_video(row: sqlite3.Row) -> Video:
    return Video(
        youtube_id=row["youtube_id"],
        title=row["title"],
        description=row["description"],
        channel_id=row["channel_id"],
        duration_seconds=row["duration_seconds"],
        watched_seconds=row["watched_seconds"],
        watched_at=datetime.fromisoformat(row["watched_at"]) if row["watched_at"] else None,
        engagement_level=EngagementLevel(row["engagement_level"]),
        engagement_override=EngagementLevel(row["engagement_override"]) if row["engagement_override"] else None,
        transcript=row["transcript"],
        tags=json.loads(row["tags"]),
        source=Source(row["source"]),
    )
```

- [ ] **Step 7: Run tests to verify they pass**

Run: `cd extensions/yt-brain && poetry run pytest tests/step_defs/test_database.py -v`
Expected: 4 passed

- [ ] **Step 8: Commit**

```bash
git add src/yt_brain/infrastructure/ migrations/ tests/
git commit -m "add SQLite database, config, and migrations infrastructure"
```

---

### Task 5: Google Takeout Parser

**Files:**
- Create: `src/yt_brain/infrastructure/takeout_parser.py`
- Create: `tests/features/ingest_takeout.feature`
- Create: `tests/step_defs/test_ingest_takeout.py`

- [ ] **Step 1: Write BDD feature for Takeout parsing**

File: `tests/features/ingest_takeout.feature`
```gherkin
Feature: Google Takeout Ingestion
  Parse YouTube history from Google Takeout exports.

  Scenario: Parse watch history JSON
    Given a Takeout watch-history.json with 3 entries
    When I parse the takeout file
    Then I get 3 videos
    And each video has a youtube_id
    And each video has source "takeout"

  Scenario: Parse watch history with duration data
    Given a Takeout entry for video "dQw4w9WgXcQ" watched for 180 of 212 seconds
    When I parse the takeout file
    Then the video has watched_seconds 180
    And the video has duration_seconds 212

  Scenario: Skip ads and non-video entries
    Given a Takeout watch-history.json with 2 videos and 1 ad
    When I parse the takeout file
    Then I get 2 videos

  Scenario: Parse liked videos JSON
    Given a Takeout like list with 2 entries
    When I parse the liked videos file
    Then I get 2 liked video IDs
```

- [ ] **Step 2: Write step definitions**

File: `tests/step_defs/test_ingest_takeout.py`
```python
import json
from pathlib import Path

from pytest_bdd import given, parsers, scenarios, then, when

from yt_brain.infrastructure.takeout_parser import parse_watch_history, parse_liked_videos

scenarios("../features/ingest_takeout.feature")


def _make_watch_entry(video_id: str, title: str = "Test", channel: str = "Test Channel", watched_sec: int | None = None, duration_sec: int | None = None) -> dict:
    entry = {
        "header": "YouTube",
        "title": f"Watched {title}",
        "titleUrl": f"https://www.youtube.com/watch?v={video_id}",
        "subtitles": [{"name": channel, "url": f"https://www.youtube.com/channel/UC{video_id}"}],
        "time": "2026-03-20T10:00:00.000Z",
    }
    if watched_sec is not None:
        entry["activityControls"] = [f"duration:{duration_sec},watched:{watched_sec}"]
    # Takeout format includes details array for duration info
    if duration_sec is not None and watched_sec is not None:
        entry["details"] = [{"name": f"Watched {watched_sec} of {duration_sec} seconds"}]
    return entry


def _make_ad_entry() -> dict:
    return {
        "header": "YouTube",
        "title": "Visited YouTube Music",
        "time": "2026-03-20T09:00:00.000Z",
    }


@given(parsers.parse("a Takeout watch-history.json with {count:d} entries"), target_fixture="takeout_file")
def create_watch_history(tmp_path: Path, count: int) -> Path:
    entries = [_make_watch_entry(f"vid{i}", f"Video {i}") for i in range(count)]
    filepath = tmp_path / "watch-history.json"
    filepath.write_text(json.dumps(entries))
    return filepath


@given(parsers.parse('a Takeout entry for video "{vid}" watched for {watched:d} of {duration:d} seconds'), target_fixture="takeout_file")
def create_entry_with_duration(tmp_path: Path, vid: str, watched: int, duration: int) -> Path:
    entries = [_make_watch_entry(vid, watched_sec=watched, duration_sec=duration)]
    filepath = tmp_path / "watch-history.json"
    filepath.write_text(json.dumps(entries))
    return filepath


@given(parsers.parse("a Takeout watch-history.json with {video_count:d} videos and {ad_count:d} ad"), target_fixture="takeout_file")
def create_mixed_history(tmp_path: Path, video_count: int, ad_count: int) -> Path:
    entries = [_make_watch_entry(f"vid{i}") for i in range(video_count)]
    entries += [_make_ad_entry() for _ in range(ad_count)]
    filepath = tmp_path / "watch-history.json"
    filepath.write_text(json.dumps(entries))
    return filepath


@given(parsers.parse("a Takeout like list with {count:d} entries"), target_fixture="takeout_file")
def create_liked_list(tmp_path: Path, count: int) -> Path:
    entries = [
        {"contentDetails": {"videoId": f"liked{i}"}, "snippet": {"title": f"Liked {i}"}}
        for i in range(count)
    ]
    filepath = tmp_path / "liked-videos.json"
    filepath.write_text(json.dumps(entries))
    return filepath


@when("I parse the takeout file", target_fixture="parsed_videos")
def do_parse(takeout_file: Path):
    return parse_watch_history(takeout_file)


@when("I parse the liked videos file", target_fixture="liked_ids")
def do_parse_liked(takeout_file: Path):
    return parse_liked_videos(takeout_file)


@then(parsers.parse("I get {count:d} videos"))
def check_count(parsed_videos, count: int) -> None:
    assert len(parsed_videos) == count


@then("each video has a youtube_id")
def check_has_id(parsed_videos) -> None:
    for v in parsed_videos:
        assert v.youtube_id


@then(parsers.parse('each video has source "{source}"'))
def check_source(parsed_videos, source: str) -> None:
    from yt_brain.domain.models import Source
    for v in parsed_videos:
        assert v.source == Source(source)


@then(parsers.parse("the video has watched_seconds {seconds:d}"))
def check_watched(parsed_videos, seconds: int) -> None:
    assert parsed_videos[0].watched_seconds == seconds


@then(parsers.parse("the video has duration_seconds {seconds:d}"))
def check_duration(parsed_videos, seconds: int) -> None:
    assert parsed_videos[0].duration_seconds == seconds


@then(parsers.parse("I get {count:d} liked video IDs"))
def check_liked_count(liked_ids, count: int) -> None:
    assert len(liked_ids) == count
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `cd extensions/yt-brain && poetry run pytest tests/step_defs/test_ingest_takeout.py -v`
Expected: FAIL — `ImportError: cannot import name 'parse_watch_history'`

- [ ] **Step 4: Implement Takeout parser**

File: `src/yt_brain/infrastructure/takeout_parser.py`
```python
from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from yt_brain.domain.errors import IngestError
from yt_brain.domain.models import Source, Video


def parse_watch_history(filepath: Path) -> list[Video]:
    if not filepath.exists():
        raise IngestError(f"Watch history file not found: {filepath}")

    with open(filepath) as f:
        entries = json.load(f)

    videos = []
    for entry in entries:
        video = _parse_watch_entry(entry)
        if video is not None:
            videos.append(video)

    return videos


def parse_liked_videos(filepath: Path) -> list[str]:
    if not filepath.exists():
        raise IngestError(f"Liked videos file not found: {filepath}")

    with open(filepath) as f:
        entries = json.load(f)

    video_ids = []
    for entry in entries:
        content = entry.get("contentDetails", {})
        video_id = content.get("videoId")
        if video_id:
            video_ids.append(video_id)

    return video_ids


def _parse_watch_entry(entry: dict) -> Video | None:
    title_url = entry.get("titleUrl", "")
    if not title_url or "watch?v=" not in title_url:
        return None

    video_id = _extract_video_id(title_url)
    if not video_id:
        return None

    raw_title = entry.get("title", "")
    title = raw_title.removeprefix("Watched ")

    channel_id = ""
    channel_name = ""
    subtitles = entry.get("subtitles", [])
    if subtitles:
        sub = subtitles[0]
        channel_name = sub.get("name", "")
        channel_url = sub.get("url", "")
        if "/channel/" in channel_url:
            channel_id = channel_url.split("/channel/")[-1]

    watched_at = None
    time_str = entry.get("time")
    if time_str:
        watched_at = datetime.fromisoformat(time_str.replace("Z", "+00:00"))

    watched_seconds = None
    duration_seconds = 0
    details = entry.get("details", [])
    for detail in details:
        name = detail.get("name", "")
        match = re.match(r"Watched (\d+) of (\d+) seconds", name)
        if match:
            watched_seconds = int(match.group(1))
            duration_seconds = int(match.group(2))

    return Video(
        youtube_id=video_id,
        title=title,
        channel_id=channel_id or channel_name,
        duration_seconds=duration_seconds,
        watched_seconds=watched_seconds,
        watched_at=watched_at,
        source=Source.TAKEOUT,
    )


def _extract_video_id(url: str) -> str | None:
    parsed = urlparse(url)
    params = parse_qs(parsed.query)
    ids = params.get("v")
    if ids:
        return ids[0]
    return None
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd extensions/yt-brain && poetry run pytest tests/step_defs/test_ingest_takeout.py -v`
Expected: 4 passed

- [ ] **Step 6: Commit**

```bash
git add src/yt_brain/infrastructure/takeout_parser.py tests/features/ingest_takeout.feature tests/step_defs/test_ingest_takeout.py
git commit -m "add Google Takeout parser for watch history and liked videos"
```

---

### Task 6: yt-dlp Adapter (Transcripts & Metadata)

**Files:**
- Create: `src/yt_brain/infrastructure/ytdlp_adapter.py`
- Create: `tests/features/ingest_manual.feature`
- Create: `tests/step_defs/test_ingest_manual.py`

- [ ] **Step 1: Write BDD feature for manual ingestion and yt-dlp**

File: `tests/features/ingest_manual.feature`
```gherkin
Feature: Manual Video Ingestion
  Add videos by URL using yt-dlp for metadata.

  Scenario: Extract video ID from standard URL
    Given a YouTube URL "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    When I extract the video ID
    Then the ID is "dQw4w9WgXcQ"

  Scenario: Extract video ID from short URL
    Given a YouTube URL "https://youtu.be/dQw4w9WgXcQ"
    When I extract the video ID
    Then the ID is "dQw4w9WgXcQ"

  Scenario: Parse yt-dlp metadata JSON
    Given yt-dlp metadata JSON for video "abc123"
    When I parse the metadata
    Then the video title is "Test Title"
    And the video duration is 300
    And the video channel_id is "UCtest"
```

- [ ] **Step 2: Write step definitions**

File: `tests/step_defs/test_ingest_manual.py`
```python
from pytest_bdd import given, parsers, scenarios, then, when

from yt_brain.infrastructure.ytdlp_adapter import extract_video_id, parse_ytdlp_metadata

scenarios("../features/ingest_manual.feature")


@given(parsers.parse('a YouTube URL "{url}"'), target_fixture="url")
def youtube_url(url: str) -> str:
    return url


@given(parsers.parse('yt-dlp metadata JSON for video "{vid}"'), target_fixture="metadata_json")
def metadata_json(vid: str) -> dict:
    return {
        "id": vid,
        "title": "Test Title",
        "description": "Test description",
        "duration": 300,
        "channel_id": "UCtest",
        "channel": "Test Channel",
        "uploader_url": "https://www.youtube.com/channel/UCtest",
        "tags": ["test", "example"],
    }


@when("I extract the video ID", target_fixture="extracted_id")
def do_extract(url: str) -> str:
    return extract_video_id(url)


@when("I parse the metadata", target_fixture="parsed_video")
def do_parse(metadata_json: dict):
    return parse_ytdlp_metadata(metadata_json)


@then(parsers.parse('the ID is "{vid}"'))
def check_id(extracted_id: str, vid: str) -> None:
    assert extracted_id == vid


@then(parsers.parse('the video title is "{title}"'))
def check_title(parsed_video, title: str) -> None:
    assert parsed_video.title == title


@then(parsers.parse("the video duration is {duration:d}"))
def check_duration(parsed_video, duration: int) -> None:
    assert parsed_video.duration_seconds == duration


@then(parsers.parse('the video channel_id is "{channel_id}"'))
def check_channel(parsed_video, channel_id: str) -> None:
    assert parsed_video.channel_id == channel_id
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `cd extensions/yt-brain && poetry run pytest tests/step_defs/test_ingest_manual.py -v`
Expected: FAIL — `ImportError: cannot import name 'extract_video_id'`

- [ ] **Step 4: Implement yt-dlp adapter**

File: `src/yt_brain/infrastructure/ytdlp_adapter.py`
```python
from __future__ import annotations

import json
import subprocess
from pathlib import Path
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
    except FileNotFoundError:
        raise IngestError("yt-dlp is not installed. Install with: brew install yt-dlp")

    if result.returncode != 0:
        raise IngestError(f"yt-dlp failed for {video_id}: {result.stderr.strip()}")

    metadata = json.loads(result.stdout)
    return parse_ytdlp_metadata(metadata)


def fetch_transcript(video_id: str, language: str = "en") -> str | None:
    try:
        result = subprocess.run(
            [
                "yt-dlp",
                "--write-subs",
                "--write-auto-subs",
                "--sub-lang", language,
                "--sub-format", "json3",
                "--skip-download",
                "--print", "%(requested_subtitles)j",
                f"https://www.youtube.com/watch?v={video_id}",
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )
    except FileNotFoundError:
        raise IngestError("yt-dlp is not installed. Install with: brew install yt-dlp")

    if result.returncode != 0:
        return None

    # Use a simpler approach: get auto-generated subtitles as text
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
    except (json.JSONDecodeError, KeyError, subprocess.TimeoutExpired):
        pass

    return None


def parse_ytdlp_metadata(metadata: dict) -> Video:
    return Video(
        youtube_id=metadata.get("id", ""),
        title=metadata.get("title", ""),
        description=metadata.get("description", ""),
        channel_id=metadata.get("channel_id", ""),
        duration_seconds=int(metadata.get("duration", 0)),
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
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd extensions/yt-brain && poetry run pytest tests/step_defs/test_ingest_manual.py -v`
Expected: 3 passed

- [ ] **Step 6: Commit**

```bash
git add src/yt_brain/infrastructure/ytdlp_adapter.py tests/features/ingest_manual.feature tests/step_defs/test_ingest_manual.py
git commit -m "add yt-dlp adapter for video metadata and transcript fetching"
```

---

### Task 7: Application Services (Ingest, Classify, Status)

**Files:**
- Create: `src/yt_brain/application/ingest.py`
- Create: `src/yt_brain/application/classify.py`
- Create: `src/yt_brain/application/status.py`
- Create: `src/yt_brain/application/transcript.py`
- Create: `tests/features/status.feature`
- Create: `tests/step_defs/test_status.py`

- [ ] **Step 1: Write BDD feature for status**

File: `tests/features/status.feature`
```gherkin
Feature: Status Dashboard
  Show counts and summary of video library.

  Scenario: Status with empty database
    Given an empty database
    When I get the status summary
    Then total videos is 0
    And all tier counts are 0

  Scenario: Status with classified videos
    Given a database with these videos:
      | youtube_id | engagement |
      | v1         | BOUNCED    |
      | v2         | WATCHED    |
      | v3         | LIKED      |
      | v4         | LIKED      |
      | v5         | CURATED    |
    When I get the status summary
    Then total videos is 5
    And BOUNCED count is 1
    And WATCHED count is 1
    And LIKED count is 2
    And CURATED count is 1
```

- [ ] **Step 2: Write step definitions**

File: `tests/step_defs/test_status.py`
```python
from pytest_bdd import given, parsers, scenarios, then, when
from pytest_bdd.parsers import DataTable

from yt_brain.application.status import get_status_summary, StatusSummary
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
    for row in datatable:
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
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `cd extensions/yt-brain && poetry run pytest tests/step_defs/test_status.py -v`
Expected: FAIL — `ImportError: cannot import name 'get_status_summary'`

- [ ] **Step 4: Implement status service**

File: `src/yt_brain/application/status.py`
```python
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from yt_brain.infrastructure.database import get_video_count_by_engagement, get_all_videos


@dataclass
class StatusSummary:
    total: int = 0
    by_engagement: dict[str, int] = field(default_factory=dict)
    channels: int = 0
    with_transcripts: int = 0


def get_status_summary(db_path: Path) -> StatusSummary:
    counts = get_video_count_by_engagement(db_path)
    total = sum(counts.values())

    videos = get_all_videos(db_path)
    with_transcripts = sum(1 for v in videos if v.transcript)

    return StatusSummary(
        total=total,
        by_engagement=counts,
        with_transcripts=with_transcripts,
    )
```

- [ ] **Step 5: Implement ingest service**

File: `src/yt_brain/application/ingest.py`
```python
from __future__ import annotations

from pathlib import Path

from yt_brain.domain.models import EngagementLevel, Video
from yt_brain.infrastructure.database import get_video, save_video, save_channel
from yt_brain.infrastructure.takeout_parser import parse_watch_history, parse_liked_videos
from yt_brain.infrastructure.ytdlp_adapter import extract_video_id, fetch_metadata


def ingest_takeout(db_path: Path, takeout_path: Path) -> int:
    watch_history_file = _find_watch_history(takeout_path)
    videos = parse_watch_history(watch_history_file)

    count = 0
    for video in videos:
        save_video(db_path, video)
        if video.channel_id:
            save_channel(db_path, video.channel_id, video.channel_id)
        count += 1

    # Try to find and apply liked videos
    liked_file = takeout_path / "YouTube and YouTube Music" / "playlists" / "Liked videos.json"
    if not liked_file.exists():
        liked_file = takeout_path / "liked-videos.json"
    if liked_file.exists():
        liked_ids = parse_liked_videos(liked_file)
        for vid_id in liked_ids:
            existing = get_video(db_path, vid_id)
            if existing is not None:
                from yt_brain.infrastructure.database import update_engagement
                update_engagement(db_path, vid_id, EngagementLevel.LIKED)

    return count


def ingest_video(db_path: Path, url: str) -> Video:
    video_id = extract_video_id(url)

    existing = get_video(db_path, video_id)
    if existing is not None:
        return existing

    video = fetch_metadata(video_id)
    save_video(db_path, video)

    if video.channel_id:
        save_channel(db_path, video.channel_id, video.title)

    return video


def _find_watch_history(takeout_path: Path) -> Path:
    candidates = [
        takeout_path / "YouTube and YouTube Music" / "history" / "watch-history.json",
        takeout_path / "watch-history.json",
        takeout_path,
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(f"Could not find watch-history.json in {takeout_path}")
```

- [ ] **Step 6: Implement classify service**

File: `src/yt_brain/application/classify.py`
```python
from __future__ import annotations

from pathlib import Path

from yt_brain.domain.classifier import classify_video
from yt_brain.domain.models import EngagementLevel
from yt_brain.infrastructure.database import (
    get_all_videos,
    is_video_in_playlist,
    is_video_liked,
    update_engagement,
)


def classify_all(
    db_path: Path,
    reclassify: bool = False,
    bounce_threshold: float = 0.15,
    watched_threshold: float = 0.85,
) -> dict[str, int]:
    videos = get_all_videos(db_path)
    counts: dict[str, int] = {}

    for video in videos:
        if not reclassify and video.engagement_level != EngagementLevel.UNKNOWN:
            continue

        is_liked = is_video_liked(db_path, video.youtube_id)
        in_playlist = is_video_in_playlist(db_path, video.youtube_id)

        level = classify_video(
            video=video,
            is_liked=is_liked,
            is_in_playlist=in_playlist,
            bounce_threshold=bounce_threshold,
            watched_threshold=watched_threshold,
        )

        update_engagement(db_path, video.youtube_id, level)
        counts[level.value] = counts.get(level.value, 0) + 1

    return counts
```

- [ ] **Step 7: Implement transcript service**

File: `src/yt_brain/application/transcript.py`
```python
from __future__ import annotations

from pathlib import Path

from yt_brain.domain.errors import VideoNotFoundError
from yt_brain.domain.models import EngagementLevel
from yt_brain.infrastructure.database import get_video, get_videos_by_engagement, save_video
from yt_brain.infrastructure.ytdlp_adapter import fetch_transcript


def fetch_video_transcript(db_path: Path, video_id: str, language: str = "en") -> str | None:
    video = get_video(db_path, video_id)
    if video is None:
        raise VideoNotFoundError(f"Video not found: {video_id}")

    if video.transcript:
        return video.transcript

    transcript = fetch_transcript(video_id, language)
    if transcript:
        video.transcript = transcript
        save_video(db_path, video)

    return transcript


def fetch_transcripts_by_level(
    db_path: Path,
    level: EngagementLevel,
    language: str = "en",
) -> dict[str, bool]:
    videos = get_videos_by_engagement(db_path, level)
    results: dict[str, bool] = {}

    for video in videos:
        if video.transcript:
            results[video.youtube_id] = True
            continue

        transcript = fetch_transcript(video.youtube_id, language)
        if transcript:
            video.transcript = transcript
            save_video(db_path, video)
            results[video.youtube_id] = True
        else:
            results[video.youtube_id] = False

    return results
```

- [ ] **Step 8: Run tests to verify they pass**

Run: `cd extensions/yt-brain && poetry run pytest tests/ -v`
Expected: All tests pass (models, classify, database, takeout, manual, status)

- [ ] **Step 9: Commit**

```bash
git add src/yt_brain/application/
git commit -m "add application services for ingest, classify, status, and transcript"
```

---

### Task 8: Review Workflow (Application + Rich UI)

**Files:**
- Create: `src/yt_brain/application/review.py`
- Create: `tests/features/review.feature`
- Create: `tests/step_defs/test_review.py`

- [ ] **Step 1: Write BDD feature for review**

File: `tests/features/review.feature`
```gherkin
Feature: Review Workflow
  Review and override video classifications.

  Scenario: List videos for review by tier
    Given a database with classified videos:
      | youtube_id | title       | engagement |
      | v1         | Video One   | LIKED      |
      | v2         | Video Two   | LIKED      |
      | v3         | Video Three | WATCHED    |
    When I get review list for tier "LIKED"
    Then I get 2 videos for review

  Scenario: Override a video classification
    Given a database with a video "v1" classified as "WATCHED"
    When I override "v1" to "CURATED"
    And I retrieve video "v1" for review
    Then the effective engagement is "CURATED"
```

- [ ] **Step 2: Write step definitions**

File: `tests/step_defs/test_review.py`
```python
from pytest_bdd import given, parsers, scenarios, then, when

from yt_brain.application.review import get_review_list, override_engagement
from yt_brain.domain.models import EngagementLevel, Source, Video
from yt_brain.infrastructure.database import get_video, init_db, save_video

scenarios("../features/review.feature")


@given("a database with classified videos:", target_fixture="db_path")
def db_with_classified(temp_config_dir, datatable):
    db_path = temp_config_dir / "yt-brain.db"
    init_db(db_path)
    for row in datatable:
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
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `cd extensions/yt-brain && poetry run pytest tests/step_defs/test_review.py -v`
Expected: FAIL — `ImportError: cannot import name 'get_review_list'`

- [ ] **Step 4: Implement review service**

File: `src/yt_brain/application/review.py`
```python
from __future__ import annotations

from pathlib import Path

from yt_brain.domain.models import EngagementLevel, Video
from yt_brain.infrastructure.database import get_videos_by_engagement, update_engagement


def get_review_list(
    db_path: Path,
    level: EngagementLevel | None = None,
) -> list[Video]:
    if level is not None:
        return get_videos_by_engagement(db_path, level)

    from yt_brain.infrastructure.database import get_all_videos
    return get_all_videos(db_path)


def override_engagement(db_path: Path, youtube_id: str, level: EngagementLevel) -> None:
    update_engagement(db_path, youtube_id, level, is_override=True)
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd extensions/yt-brain && poetry run pytest tests/step_defs/test_review.py -v`
Expected: 2 passed

- [ ] **Step 6: Commit**

```bash
git add src/yt_brain/application/review.py tests/features/review.feature tests/step_defs/test_review.py
git commit -m "add review workflow service with override support"
```

---

### Task 9: CLI Commands (Wire Everything Together)

**Files:**
- Modify: `src/yt_brain/cli.py`

- [ ] **Step 1: Implement full CLI**

File: `src/yt_brain/cli.py`
```python
from __future__ import annotations

from pathlib import Path
from typing import Annotated, Optional

import typer
from rich.console import Console
from rich.table import Table

from yt_brain.domain.models import EngagementLevel

app = typer.Typer(
    name="yt-brain",
    help="YouTube knowledge brain — ingest, classify, and curate your YouTube activity.",
    no_args_is_help=True,
)

ingest_app = typer.Typer(help="Ingest YouTube data from various sources.")
app.add_typer(ingest_app, name="ingest")

console = Console()
err_console = Console(stderr=True)


def _get_db_path() -> Path:
    from yt_brain.infrastructure.config import load_config

    config = load_config()
    config.config_dir.mkdir(parents=True, exist_ok=True)
    return config.db_path


def _ensure_db(db_path: Path) -> None:
    from yt_brain.infrastructure.database import init_db

    init_db(db_path)


@app.callback()
def main() -> None:
    """yt-brain - YouTube Knowledge Brain."""
    pass


@ingest_app.command("takeout")
def ingest_takeout(
    path: Annotated[Path, typer.Argument(help="Path to Google Takeout export directory or watch-history.json")],
) -> None:
    """Import YouTube history from a Google Takeout export."""
    from yt_brain.application.ingest import ingest_takeout as do_ingest

    db_path = _get_db_path()
    _ensure_db(db_path)

    try:
        count = do_ingest(db_path, path)
        console.print(f"[green]Ingested {count} videos from Takeout.[/green]")
    except Exception as e:
        err_console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1) from None


@ingest_app.command("video")
def ingest_video(
    url: Annotated[str, typer.Argument(help="YouTube video URL")],
) -> None:
    """Add a single video by URL."""
    from yt_brain.application.ingest import ingest_video as do_ingest

    db_path = _get_db_path()
    _ensure_db(db_path)

    try:
        video = do_ingest(db_path, url)
        console.print(f"[green]Added:[/green] {video.title} ({video.youtube_id})")
    except Exception as e:
        err_console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1) from None


@app.command()
def classify(
    reclassify: Annotated[bool, typer.Option("--reclassify", help="Re-classify all videos")] = False,
) -> None:
    """Run engagement classification on videos."""
    from yt_brain.application.classify import classify_all
    from yt_brain.infrastructure.config import load_config

    config = load_config()
    db_path = config.db_path
    _ensure_db(db_path)

    counts = classify_all(
        db_path,
        reclassify=reclassify,
        bounce_threshold=config.bounce_threshold,
        watched_threshold=config.watched_threshold,
    )

    total = sum(counts.values())
    console.print(f"[green]Classified {total} videos:[/green]")
    for level, count in sorted(counts.items()):
        console.print(f"  {level}: {count}")


@app.command()
def review(
    level: Annotated[Optional[str], typer.Option("--level", "-l", help="Filter by engagement level")] = None,
) -> None:
    """Review videos by engagement tier."""
    from yt_brain.application.review import get_review_list, override_engagement

    db_path = _get_db_path()
    _ensure_db(db_path)

    filter_level = EngagementLevel(level) if level else None
    videos = get_review_list(db_path, filter_level)

    if not videos:
        console.print("[yellow]No videos to review.[/yellow]")
        return

    table = Table(title="Video Review")
    table.add_column("ID", style="dim", max_width=12)
    table.add_column("Title", max_width=50)
    table.add_column("Channel", max_width=20)
    table.add_column("Watch %", justify="right")
    table.add_column("Engagement", style="bold")
    table.add_column("Override", style="italic")

    for video in videos:
        pct = f"{video.watch_percentage:.0%}" if video.watch_percentage is not None else "-"
        override = video.engagement_override.value if video.engagement_override else ""
        table.add_row(
            video.youtube_id,
            video.title[:50],
            video.channel_id[:20],
            pct,
            video.engagement_level.value,
            override,
        )

    console.print(table)
    console.print(f"\nTotal: {len(videos)} videos")
    console.print("\nTo reclassify a video: [bold]yt-brain review[/bold] then use override prompt")

    # Simple override loop
    while True:
        response = console.input("\n[bold]Override a video? Enter video ID (or 'q' to quit):[/bold] ").strip()
        if response.lower() in ("q", "quit", ""):
            break

        video_id = response
        level_input = console.input("[b]ounce [w]atched [l]iked [c]urated [s]kip: ").strip().lower()
        level_map = {"b": "BOUNCED", "w": "WATCHED", "l": "LIKED", "c": "CURATED"}
        if level_input in level_map:
            override_engagement(db_path, video_id, EngagementLevel(level_map[level_input]))
            console.print(f"[green]Overridden {video_id} → {level_map[level_input]}[/green]")
        elif level_input != "s":
            console.print("[yellow]Skipped.[/yellow]")


@app.command()
def status() -> None:
    """Show dashboard with video counts by engagement tier."""
    from yt_brain.application.status import get_status_summary

    db_path = _get_db_path()
    _ensure_db(db_path)

    summary = get_status_summary(db_path)

    table = Table(title="yt-brain Status")
    table.add_column("Tier", style="bold")
    table.add_column("Count", justify="right")

    for level in EngagementLevel:
        count = summary.by_engagement.get(level.value, 0)
        table.add_row(level.value, str(count))

    table.add_section()
    table.add_row("TOTAL", str(summary.total), style="bold")
    table.add_row("With transcripts", str(summary.with_transcripts))

    console.print(table)


@app.command()
def transcript(
    video_id: Annotated[Optional[str], typer.Argument(help="YouTube video ID")] = None,
    level: Annotated[Optional[str], typer.Option("--level", "-l", help="Fetch transcripts for all videos at this engagement level")] = None,
) -> None:
    """Fetch video transcript(s) via yt-dlp."""
    from yt_brain.application.transcript import fetch_video_transcript, fetch_transcripts_by_level
    from yt_brain.infrastructure.config import load_config

    config = load_config()
    db_path = config.db_path
    _ensure_db(db_path)

    if video_id:
        result = fetch_video_transcript(db_path, video_id, config.transcript_language)
        if result:
            console.print(f"[green]Transcript fetched for {video_id}[/green] ({len(result)} chars)")
        else:
            console.print(f"[yellow]No transcript available for {video_id}[/yellow]")
    elif level:
        results = fetch_transcripts_by_level(db_path, EngagementLevel(level), config.transcript_language)
        success = sum(1 for v in results.values() if v)
        console.print(f"[green]Fetched {success}/{len(results)} transcripts for {level} videos[/green]")
    else:
        err_console.print("[red]Provide a video ID or --level flag[/red]")
        raise typer.Exit(1)


@app.command()
def config() -> None:
    """Show current configuration."""
    from yt_brain.infrastructure.config import load_config

    cfg = load_config()

    table = Table(title="yt-brain Config")
    table.add_column("Setting", style="bold")
    table.add_column("Value")

    table.add_row("Config dir", str(cfg.config_dir))
    table.add_row("Database", str(cfg.db_path))
    table.add_row("API key", "***" if cfg.youtube_api_key else "(not set)")
    table.add_row("OAuth credentials", str(cfg.oauth_credentials))
    table.add_row("Bounce threshold", f"{cfg.bounce_threshold:.0%}")
    table.add_row("Watched threshold", f"{cfg.watched_threshold:.0%}")
    table.add_row("Transcript language", cfg.transcript_language)

    console.print(table)


if __name__ == "__main__":
    app()
```

- [ ] **Step 2: Verify CLI boots with all commands**

Run: `cd extensions/yt-brain && poetry run yt-brain --help`
Expected: Shows commands: `classify`, `config`, `ingest`, `review`, `status`, `transcript`

- [ ] **Step 3: Run full test suite**

Run: `cd extensions/yt-brain && poetry run pytest tests/ -v`
Expected: All tests pass

- [ ] **Step 4: Commit**

```bash
git add src/yt_brain/cli.py
git commit -m "wire up CLI commands for ingest, classify, review, status, transcript, config"
```

---

### Task 10: Integration Test & Final Polish

**Files:**
- Modify: `workspace-config.yaml` (workspace root)

- [ ] **Step 1: Add yt-brain to workspace config**

In `/Users/jayers/code/praxis-workspace/workspace-config.yaml`, add `yt-brain` to `installed_extensions`:

```yaml
installed_extensions:
  - render-run
  - template-python-cli
  - yt-brain
```

- [ ] **Step 2: Run full test suite from workspace root**

Run: `cd /Users/jayers/code/praxis-workspace/extensions/yt-brain && poetry run pytest tests/ -v --tb=short`
Expected: All tests pass (models, classify, database, takeout, manual, review, status)

- [ ] **Step 3: Smoke test the CLI end-to-end**

```bash
cd /Users/jayers/code/praxis-workspace/extensions/yt-brain
poetry run yt-brain config
poetry run yt-brain status
```
Expected: Config shows defaults, status shows 0 videos

- [ ] **Step 4: Run linting**

```bash
cd /Users/jayers/code/praxis-workspace/extensions/yt-brain && poetry run ruff check src/ tests/
```
Expected: No errors

- [ ] **Step 5: Commit final changes**

```bash
git add workspace-config.yaml
git commit -m "register yt-brain extension in workspace config"
```

- [ ] **Step 6: Run all tests one final time**

Run: `cd /Users/jayers/code/praxis-workspace/extensions/yt-brain && poetry run pytest tests/ -v`
Expected: All tests pass. Phase 1 complete.
