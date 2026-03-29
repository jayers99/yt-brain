# Dev Journal: Semantic Search

**Date**: 2026-03-29
**Feature**: `semantic-search`
**Design**: [2026-03-29-semantic-search-design.md](2026-03-29-semantic-search-design.md)

## What Was Built

Semantic search across 12,749 YouTube videos using local embeddings and sqlite-vec, replacing the old substring title/channel search in the dashboard.

## Stack

| Component | Choice | Why |
|-----------|--------|-----|
| Embeddings | `sentence-transformers` / `all-MiniLM-L6-v2` | Local, no API costs, 384-dim, fast on CPU, ~50MB model |
| Vector store | `sqlite-vec` | Stays in existing SQLite DB, no new infrastructure |
| Description source | YouTube Data API v3 | Batches of 50 — original yt-dlp approach was ~2-3 sec/video (would take 8+ hours for full history) |

## Key Implementation Details

### Description Backfill (`backfill_descriptions`)

- Uses YouTube Data API `videos?part=snippet` in batches of 50
- Originally used yt-dlp `fetch_metadata()` per video (subprocess per call) — way too slow
- API approach: ~250 requests for 12.5k videos, completes in 1-2 minutes
- Requires `youtube_api_key` in config

### Embedding Generation (`embed`)

- Concatenates `title + "\n" + description` as input text
- Encodes in batches of 256 via `SentenceTransformer.encode()`
- Serializes float arrays to bytes via `struct.pack()` for sqlite-vec
- Incremental: only embeds videos not already in `video_embeddings` table
- `--rebuild` flag regenerates all

### sqlite-vec Integration

- Virtual table: `CREATE VIRTUAL TABLE video_embeddings USING vec0(youtube_id TEXT PRIMARY KEY, embedding FLOAT[384])`
- Migration 004 requires extension loaded before `executescript` — handled by `_VEC_MIGRATIONS` set in `init_db()`
- kNN query: `SELECT youtube_id, distance FROM video_embeddings WHERE embedding MATCH ? ORDER BY distance LIMIT ?`
- Extension loaded via `sqlite_vec.load(conn)` with `enable_load_extension(True)`

### Search API (`/api/search`)

- Model preloaded at dashboard startup (eliminates cold-start on first search)
- 150ms debounce on frontend
- Supports field-specific filters parsed server-side:
  - `title:"x"` — case-insensitive match in title
  - `desc:"x"` — case-insensitive match in description
  - `channel:"x"` — case-insensitive match in channel name
  - `"x"` (bare quotes) — match in title or description
- Filter terms are stripped from the query before semantic embedding
- When filters are active, fetches 5x results from sqlite-vec then post-filters against actual DB rows

### Dashboard Changes

- Replaced two inputs (title search + channel search) with single semantic search bar
- Search bar disabled with hint when no embeddings exist
- `semanticMatchIds` JS state: `null` = no search active, `Set` = matched video IDs
- Intersects with existing genre/year/starred filters client-side
- Browser opens only after server is ready (background thread polls localhost)

## DB Impact

- Before: 24 MB
- After embeddings: ~43 MB (384 floats × 4 bytes × 12,749 rows ≈ 19 MB)
- SQLite limit: 281 TB — no concern

## Gotchas Encountered

1. **yt-dlp too slow for bulk backfill** — 1 subprocess per video, ~2-3 sec each. Switched to YouTube Data API batches of 50.
2. **`channelOk` reference error** — removed the old title/channel search variables but left a reference in `applyFilters()`. Silently broke all filtering.
3. **sqlite-vec migrations** — can't run via `executescript` without loading the extension first. Added `_VEC_MIGRATIONS` set to handle this.
4. **Flask Ctrl+C** — dev server swallows SIGINT. Added explicit `signal.signal(SIGINT, handler)` and `use_reloader=False`.
5. **Semaphore leak on kill** — torch threads leave leaked semaphores. Clean SIGINT handler prevents this.
