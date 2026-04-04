# All Videos Table: Sorting & New Columns

**Date:** 2026-04-04
**Status:** Approved

## Overview

Expand the All Videos table with three new columns (Liked, Watched Date, Published Date), add click-to-sort on all non-filter columns, and add a liked filter matching the existing starred channels pattern.

## Database Changes

### New Migration: `007_video_liked_published.sql`

Add two columns to the `videos` table:

- `liked` (TEXT, DEFAULT NULL) — values: `'like'`, `'dislike'`, or `NULL` (no rating)
- `published_at` (TEXT, DEFAULT NULL) — ISO 8601 date string from YouTube

No backfill in the migration itself — data comes from sync/backfill commands.

## Data Sync

### Liked Status

**Source:** yt-dlp `--flat-playlist --print id` on the `LL` (Liked Videos) playlist using `--cookies-from-browser`.

**Approach:**
1. Fetch all liked video IDs from the LL playlist via yt-dlp
2. For each video in the DB: set `liked = 'like'` if its ID is in the LL list
3. yt-dlp does not expose a "disliked" playlist — dislike data requires YouTube Data API `videos.getRating` with OAuth 2.0. Initial implementation uses yt-dlp for likes only; dislike support is a follow-up requiring OAuth setup.

**Commands:**
- `yt-brain backfill-likes` — one-time bulk fetch of liked video IDs, updates DB
- `yt-brain sync` — refreshes liked status alongside other metadata

**Limitations:** YouTube caps the LL playlist at ~5,000 entries. Current user has 335 liked videos, well within range.

### Published Date

**Source:** YouTube Data API v3 `snippet.publishedAt` — already fetched by `backfill-dates`.

**Change:** Store `publishedAt` in the new `published_at` column. The existing `backfill-dates` command currently stores this in `watched_at` as a fallback; update it to also populate `published_at`.

## Table Layout

Seven columns with fixed widths:

| Column | Width | Behavior | Content |
|--------|-------|----------|---------|
| Liked | 4% | Filter (3-state toggle) | 👍 / 👎 / blank |
| Title | 33% | Sort (asc/desc/clear) | Clickable YouTube link |
| Channel | 16% | Sort (asc/desc/clear) | Channel name link |
| Genre | 14% | Sort (asc/desc/clear) | Genre badge |
| Cluster | 13% | Sort (asc/desc/clear) | Cluster slug link |
| Watched | 10% | Sort (asc/desc/clear) | YYYY-MM-DD |
| Published | 10% | Sort (asc/desc/clear) | YYYY-MM-DD |

## Sort Behavior

**Interaction:** Click a sortable column header to cycle: none → ascending → descending → none.

**State:**
- `sortColumn` — `null` or column key (`'title'`, `'channel'`, `'genre'`, `'cluster'`, `'watched'`, `'published'`)
- `sortDirection` — `null`, `'asc'`, or `'desc'`

**Visual indicator:** Arrow glyph appended to active header: ▲ (ascending), ▼ (descending). No glyph when sort is cleared.

**Implementation (client-side, pure DOM sort):**
1. Store each row's original index in the `videoData` cache during initial DOM parse
2. On sort: sort the `videoData` array by the selected column value
3. Re-append `<tr>` elements to `<tbody>` in sorted order (DOM move, no clone/recreate)
4. On clear: re-append rows in original index order
5. Active filters are respected — hidden rows stay hidden but maintain sort position
6. Sorting a new column clears the previous sort first

**Sort types:**
- Title, Channel, Genre, Cluster: case-insensitive alphabetical; empty values sort last
- Watched, Published: chronological using full ISO timestamp for sort comparison; display truncated to `YYYY-MM-DD`; null dates sort last

## Liked Filter

**Pattern:** Matches the existing starred channels filter (★ toggle in the channel pane header).

**Interaction:** Click the Liked column header icon to cycle through filter states:
- **Off:** Header shows dimmed 👍 (no filter active)
- **Liked only:** Header shows highlighted 👍 (only liked videos visible)
- **Disliked only:** Header shows highlighted 👎 (only disliked videos visible)
- Next click returns to **Off**

**State:** `likedFilterState` — `null`, `'like'`, or `'dislike'`

**Integration:** Added as a new condition in the existing `applyFilters()` function:
```
const likedOk = likedFilterState === null || v.liked === likedFilterState;
```

Combined with existing filters via AND: `dateOk && searchOk && starOk && genreOk && likedOk`.

## Data Flow

### Server → Template

The Flask `index()` route adds to each video dict:
- `liked`: `'like'`, `'dislike'`, or `''`
- `watched_at`: existing (already present)
- `published_at`: new ISO date string or `''`

### Template → DOM

New data attributes on each `<tr>`:
- `data-liked="{{ v.liked }}"` 
- `data-published="{{ v.published_at }}"`
- `data-watched` already exists

### DOM → videoData Cache

During initial DOM parse, extract and cache:
- `liked`: from `data-liked`
- `watched`: from `data-watched` (already cached)
- `published`: from `data-published`
- `originalIndex`: row's position in initial DOM order

## CSS

- Sortable headers: `cursor: pointer` with hover effect
- Sort glyph: `::after` pseudo-element or inline span, styled with `var(--text-muted)`
- 👍/👎 icons: use Unicode thumbs-up (U+1F44D) and thumbs-down (U+1F44E), or SVG for consistency
- Liked icon states: highlighted (colored) vs dimmed (`opacity: 0.3`)
- Header filter icon: same highlight treatment as the existing star filter
- Date columns: `font-variant-numeric: tabular-nums` for alignment

## Files Modified

| File | Changes |
|------|---------|
| `migrations/007_video_liked_published.sql` | New migration |
| `src/yt_brain/infrastructure/database.py` | Add `liked` and `published_at` to queries, new `get_liked_video_ids()` and `update_video_liked()` functions |
| `src/yt_brain/infrastructure/ytdlp_adapter.py` | New `fetch_liked_ids()` function |
| `src/yt_brain/application/backfill.py` | New `backfill_likes()` function; update `backfill_dates()` to populate `published_at` |
| `src/yt_brain/application/sync.py` | Include liked refresh in sync pipeline |
| `src/yt_brain/cli.py` | New `backfill-likes` command |
| `src/yt_brain/web/dashboard.py` | Table HTML (new columns, sort headers, liked filter), JS (sort logic, liked filter), CSS (sort indicators, liked styling) |

## Out of Scope

- Dislike data via YouTube Data API (requires OAuth 2.0 setup — follow-up)
- Pagination / virtual scrolling
- Multi-column sort
- Server-side sorting
