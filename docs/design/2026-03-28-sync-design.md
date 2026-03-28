# Sync Feature Design

**Date**: 2026-03-28
**Status**: Approved
**Scope**: Incremental sync of YouTube watch history via yt-dlp

## Problem

The database goes stale as soon as you watch new videos. The initial bulk load came from Google Takeout, but requesting new Takeout exports for every update is impractical. We need a single command that fetches recent watches and enriches them — no manual exports.

## Solution

A `yt-brain sync` command that uses yt-dlp with browser cookies to pull recent watch history, adds new videos to the database, and backfills metadata (channels, categories, dates) for new entries only.

## CLI Interface

```
yt-brain sync                      # Fetch new videos since last sync
yt-brain sync --browser firefox    # Use different browser for cookies
yt-brain sync --batch-size 100     # Control fetch batch size (default 200)
```

Default browser: `chrome`. Always prints a summary of what was added.

## Architecture

### Application Service (`application/sync.py`)

One public function:

```python
def sync_videos(
    db_path: Path,
    browser: str = "chrome",
    batch_size: int = 200,
    api_key: str | None = None,
) -> SyncResult
```

**SyncResult** dataclass:

```python
@dataclass
class SyncResult:
    new_videos: int
    channels_backfilled: int
    categories_backfilled: int
    dates_backfilled: int
```

### Algorithm

1. Fetch history from yt-dlp in batches of `batch_size`
2. For each video in batch, check if `youtube_id` exists in DB via `get_video()`
3. Save new videos via `save_video()`
4. If an entire batch is already known, stop fetching
5. Backfill channels (oEmbed), categories (YouTube Data API), dates (YouTube Data API) — only for newly added videos
6. Return `SyncResult`

The stop condition is **a full batch of duplicates**. This handles videos appearing slightly out of order in the feed without stopping too early.

### Backfill Extraction (`application/backfill.py`)

Backfill logic currently lives inline in CLI commands (`backfill-channels`, `backfill-categories`, `backfill-dates`). Extract into reusable functions:

```python
def backfill_channels(db_path: Path, video_ids: list[str] | None = None) -> int
def backfill_categories(db_path: Path, api_key: str, video_ids: list[str] | None = None) -> int
def backfill_dates(db_path: Path, api_key: str, video_ids: list[str] | None = None) -> int
```

When `video_ids` is provided, backfill only those videos. When `None`, backfill all videos missing that field (preserving existing CLI behavior).

Existing CLI backfill commands are refactored to call these functions.

### Infrastructure Reuse

One minor change: `ytdlp_adapter._fetch_history_range()` is currently private. Rename to `fetch_history_range()` (public) so the sync service can call it for batched fetching by position range (0-200, 200-400, etc.).

Otherwise, no new infrastructure code. Sync reuses:

- `ytdlp_adapter.fetch_history_range()` — fetch batches from history feed by position
- `database.save_video()` — upsert (already idempotent)
- `database.get_video()` — check existence for stop condition
- `database.get_videos_missing_channel()` + `update_channel_id()` — channel backfill
- `database.get_videos_missing_category()` + `update_category()` — category backfill
- `database.get_videos_missing_watched_at()` + `update_watched_at()` — date backfill

## Output

Always prints a summary:

```
Synced 12 new videos
  Channels backfilled: 12
  Categories backfilled: 12
  Dates backfilled: 10
```

When nothing is new:

```
Already up to date.
```

## Files Changed

| File | Change |
|------|--------|
| `src/yt_brain/application/sync.py` | **New** — sync service with `sync_videos()` and `SyncResult` |
| `src/yt_brain/application/backfill.py` | **New** — extracted backfill functions |
| `src/yt_brain/cli.py` | Add `sync` command, refactor backfill commands to use `backfill.py` |
| `tests/features/sync.feature` | **New** — BDD scenarios |
| `tests/step_defs/test_sync.py` | **New** — step definitions |

No changes to domain models, database layer, or yt-dlp adapter.

## Testing

```gherkin
Feature: Sync watch history

  Scenario: Sync adds new videos and backfills metadata
    Given a database with 3 existing videos
    And yt-dlp returns 5 videos including 3 already known
    When I run sync
    Then 2 new videos are saved
    And channel names are backfilled for new videos
    And categories are backfilled for new videos
    And the summary shows "Synced 2 new videos"

  Scenario: Sync stops when all videos are known
    Given a database with 10 existing videos
    And yt-dlp returns a batch of 10 already-known videos
    When I run sync
    Then no new videos are saved
    And the summary shows "Already up to date"
```

Unit tests with mocked infrastructure. Manual verification against real YouTube.
