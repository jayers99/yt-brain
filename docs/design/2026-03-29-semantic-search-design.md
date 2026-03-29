# Semantic Search Design

**Date**: 2026-03-29
**Status**: Complete
**Slug**: `semantic-search`

## Problem

With 12,500+ videos in history, the current substring search on title/channel is too literal. You remember watching "something about RAG pipelines" but the video title is "Building Production LLM Apps" — substring search won't find it. We need search by meaning.

## Solution

Two-part feature:

1. **`backfill-descriptions`** — Fetch video descriptions for existing history via yt-dlp
2. **Semantic search** — Embed title+description, store in sqlite-vec, expose via dashboard search bar

## Part 1: Backfill Descriptions

### CLI

```
yt-brain backfill-descriptions              # Fetch all missing descriptions
yt-brain backfill-descriptions --limit 500  # Cap per run
```

### Implementation

Follows the existing backfill pattern (`backfill-channels`, `backfill-categories`):

- Query videos where `description = ''`
- Call `yt-dlp --dump-json --no-download` per video to fetch metadata
- Extract `description` field, update the row
- Rate-limit to avoid throttling (~1 req/sec)
- Report progress: "Backfilled 342/12500 descriptions"

### Key files

- `src/yt_brain/application/backfill.py` — Add `backfill_descriptions()` function
- `src/yt_brain/infrastructure/database.py` — Add `get_videos_missing_description()` and `update_description()` helpers
- `src/yt_brain/cli.py` — Add `backfill-descriptions` command

## Part 2: Semantic Search

### Dependencies

- `sentence-transformers` — Local embedding model
- `sqlite-vec` — SQLite extension for vector search

### Embedding Model

`all-MiniLM-L6-v2` — 384-dimensional embeddings, ~50MB download, fast on CPU. Good balance of quality and speed for this scale.

### Schema

New sqlite-vec virtual table (new migration):

```sql
CREATE VIRTUAL TABLE IF NOT EXISTS video_embeddings USING vec0(
    youtube_id TEXT PRIMARY KEY,
    embedding FLOAT[384]
);
```

### CLI

```
yt-brain embed              # Generate embeddings for all videos without one
yt-brain embed --rebuild    # Regenerate all embeddings
```

### Embedding logic

- Concatenate `title + "\n" + description` as the text to embed
- Use sentence-transformers to encode in batches (~256 at a time)
- Insert/replace into `video_embeddings` virtual table
- Only process videos not already in the table (unless `--rebuild`)

### Key files

- `src/yt_brain/application/embed.py` — Embedding service
- `src/yt_brain/infrastructure/database.py` — Vector table helpers (insert, kNN query)
- `src/yt_brain/cli.py` — Add `embed` command
- `migrations/004_video_embeddings.sql` — sqlite-vec virtual table

### Search API

New Flask endpoint:

```
GET /api/search?q=<query>&limit=20
```

- Embeds the query string using the same model
- Runs kNN search via sqlite-vec
- Returns ranked list of `{youtube_id, title, channel, score}`

### Dashboard UX

- Replace the two search inputs (title + channel) with a single search bar
- Placeholder: "Search by topic, concept, or keyword..."
- Debounced (300ms) fetch to `/api/search?q=...`
- Results intersect with active genre/year/starred filters client-side
- Falls back to showing all videos when search bar is empty (current behavior)

### Key files

- `src/yt_brain/web/dashboard.py` — Add `/api/search` endpoint, update HTML template

## Data Flow

```
[Takeout/yt-dlp ingest] → videos table (title, empty description)
         ↓
[backfill-descriptions]  → videos table (title, description filled)
         ↓
[yt-brain embed]         → video_embeddings table (384-dim vectors)
         ↓
[dashboard search]       → embed query → sqlite-vec kNN → ranked results
```

## Future: Auto-embed on Sync

Once this ships, `yt-brain sync` can auto-embed new videos as they're added. Deferred — keep sync and embed separate for now.

## Verification

1. `yt-brain backfill-descriptions --limit 10` — confirm descriptions populate
2. `yt-brain embed` — confirm embeddings generate without errors
3. `yt-brain dashboard` → search for a topic you know you watched → confirm relevant results appear even when title doesn't match the search term
4. Combine semantic search with genre/year filters → confirm they intersect correctly
