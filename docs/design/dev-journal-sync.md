# Sync Feature Development Journal

**Date**: 2026-03-28
**Scope**: Auto-sync command to keep local database current with YouTube watch history

---

## What We Built

A `yt-brain sync` command that fetches recent YouTube watch history via yt-dlp (browser cookies), identifies new videos not already in the database, saves them, and backfills metadata (channel names, categories, dates) in one step. Also added shorter time ranges to the dashboard filter and a `run.sh` wrapper script.

## Changes Made

### New Files
- `src/yt_brain/application/sync.py` — Sync service with `sync_videos()` and `SyncResult` dataclass
- `src/yt_brain/application/backfill.py` — Extracted backfill functions (channels via oEmbed, categories via YouTube Data API, dates via YouTube Data API) from inline CLI code into reusable module
- `tests/features/sync.feature` — 3 BDD scenarios (adds new, stops on known, backfills metadata)
- `tests/step_defs/test_sync.py` — Step definitions with mocked yt-dlp and API calls
- `tests/step_defs/test_backfill.py` — Unit tests for backfill extraction
- `docs/design/2026-03-28-sync-design.md` — Feature design spec
- `docs/design/2026-03-28-sync-plan.md` — Implementation plan (8 tasks)
- `run.sh` — Wrapper script: checks uv, syncs, launches dashboard

### Modified Files
- `src/yt_brain/infrastructure/database.py` — Added `get_existing_video_ids()` for batch existence check
- `src/yt_brain/infrastructure/ytdlp_adapter.py` — Made `_fetch_history_range` public as `fetch_history_range`
- `src/yt_brain/cli.py` — Added `sync` command, refactored `backfill-channels/categories/dates` commands to use `backfill.py`, added error handling
- `src/yt_brain/web/dashboard.py` — Time filter dropdown: added 1 day, 1 week, 1 month, 6 months options; filter logic changed from years to days
- `CLAUDE.md`, `README.md`, `docs/design/spec.md` — Updated docs

## Key Design Decisions

### Stop-on-known-batch algorithm
Sync fetches history in batches of 200 via `fetch_history_range()`. For each batch, it checks which video IDs already exist in the database using a single `IN (...)` query (`get_existing_video_ids`). New videos are saved; if an entire batch is already known, sync stops. This avoids fetching the entire history every time while handling slight ordering variations in the feed.

### Backfill extraction
Backfill logic was duplicated across 3 CLI commands + inline in `history --save` and `fetch`. Extracted the core logic into `application/backfill.py` with an optional `video_ids` parameter — when provided, only those videos are backfilled (used by sync); when `None`, all videos missing that field are backfilled (preserving existing CLI behavior). The `YOUTUBE_CATEGORIES` dict moved from `cli.py` to `backfill.py`.

### Partial refactoring scope
The `history --save` and `fetch` CLI commands still have inline backfill code. These were intentionally left for a future cleanup — refactoring them wasn't needed for sync to work and would have increased the scope.

## What Worked

### Subagent-driven development
Used the superpowers:subagent-driven-development workflow with fresh subagents per task. 8 tasks executed sequentially with spec compliance reviews. Sonnet model was sufficient for all implementation tasks (mechanical, well-specified). Total: ~10 commits on a feature branch, fast-forward merged to main.

### Existing infrastructure reuse
The codebase already had `fetch_history`, `parse_ytdlp_metadata`, `save_video` (with upsert), and all the backfill API patterns. Sync was mostly orchestration of existing pieces.

### First manual test
First sync run picked up 11 new videos with full metadata backfill. Second run immediately returned "Already up to date." Stop-on-known logic worked correctly.

## Known Limitations

1. **Weak backfill integration test** — The sync BDD test for backfill uses a single mock for all 3 API endpoints (oEmbed + YouTube Data API), so assertions only check `>= 0`. Individual backfill functions are tested separately in `test_backfill.py`.

2. **No progress indicator during sync** — The `fetch` command prints batch progress but sync is silent during multi-batch fetches. Fine for typical use (small incremental syncs) but could be improved for large initial syncs.

3. **Pre-existing test failures** — 2 tests fail unrelated to sync work: `test_initialize_database_creates_tables` (schema version expects 1, is 3 due to migrations) and `test_parse_ytdlp_metadata_json` (channel field mapping changed from `channel_id` to `channel` preference in `parse_ytdlp_metadata`).

## Current State (as of 2026-03-28)

- 12,746 videos in database (12,735 from Takeout + 11 from first sync)
- Sync command works end-to-end with Chrome cookies
- Dashboard time filter has 8 options (1 day through all time)
- `run.sh` provides one-command setup + sync + dashboard launch
- All new sync tests pass (29/31 total, 2 pre-existing failures)

## What's Next

Potential follow-ups from code review:
1. Refactor `history --save` and `fetch` commands to use `backfill.py` (eliminate remaining inline backfill code)
2. Fix the 2 pre-existing test failures
3. Add progress indicator for multi-batch sync
4. Strengthen backfill integration test with proper per-endpoint mocks
