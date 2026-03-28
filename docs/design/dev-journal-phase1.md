# Phase 1 Development Journal

**Date**: 2026-03-27 — 2026-03-28
**Scope**: MVP dashboard with YouTube history ingestion, genre classification, and interactive filtering

---

## What We Built

A Flask web dashboard backed by SQLite that ingests YouTube watch history from Google Takeout, classifies videos by YouTube's own category system, and provides interactive filtering by genre, channel, year range, and text search. Channels can be starred/favorited with persistence.

## What Worked

### Google Takeout as primary data source
Takeout provides the richest data: actual watch timestamps, channel names, and channel URLs. This is the only source for real "when did I watch this" dates. The watch-history.json format is clean and well-structured.

### YouTube Data API for metadata enrichment
Free tier API key (no OAuth needed) handles two critical backfills:
- **Video categories** via `videos.list?part=snippet` — YouTube assigns categories like "Education", "Science & Technology", "Music". Batches of 50 IDs per call makes it fast (~250 calls for 12K videos).
- **Upload dates** via the same endpoint — `publishedAt` field. Not as useful as watch dates from Takeout but was our only option before Takeout.

### YouTube oEmbed API for channel names
`https://www.youtube.com/oembed?url=...` returns `author_name` with no auth required. Fast way to resolve channel names when yt-dlp flat-playlist mode doesn't provide them.

### Client-side filtering in the dashboard
All filtering (year range, genre checkboxes, title/channel search, star filter) runs in JavaScript by showing/hiding table rows and recalculating stats. No server round-trips. This keeps the Flask app trivially simple — one route renders the page, one API endpoint toggles stars.

### Incremental migration system
Simple numbered SQL files in `migrations/`. `init_db` checks `schema_version` and runs any pending files. No ORM, no framework — just raw SQL. Easy to add new tables/columns without breaking existing databases.

## What Didn't Work

### Watch percentage / engagement classification
The original spec designed an engagement pyramid (BOUNCED → WATCHED → LIKED → CURATED) based on watch percentage. This turned out to be impossible:
- **YouTube Data API** does not expose watch progress for a user's own videos
- **yt-dlp** can fetch video metadata but not personal watch state
- **Google Takeout** exports watch history timestamps but NOT how much of each video was watched (despite the spec assuming it would)
- The red progress bar under YouTube thumbnails is client-side only

All 12K+ videos ended up as UNKNOWN engagement. We removed engagement from the dashboard entirely rather than show useless data. The engagement model needs rethinking for Phase 2 — likely based on signals we CAN get (liked, playlisted, subscribed, rewatch count).

### yt-dlp flat-playlist mode for history
`yt-dlp --flat-playlist --dump-json` on the history feed is fast but returns minimal data: video ID, title, duration. No channel name, no channel ID, no watch date, no category. Every missing field required a separate backfill step. Full metadata mode (`--dump-json` without `--flat-playlist`) returns everything but takes ~4 seconds per video — unusable at scale.

### Keyword-based genre classification
The initial keyword regex classifier put 67% of videos into "Other". YouTube titles are too varied and context-dependent for pattern matching. Replaced with YouTube's own `categoryId` from the Data API, which dropped unclassified to ~4% (deleted/private videos only).

### The `fetch` command for time-based history
Built a `fetch 2yr` command that was supposed to crawl yt-dlp history until hitting a date cutoff. Two problems:
1. yt-dlp doesn't return dates, so we couldn't check the cutoff during fetch — only after backfilling dates via API
2. YouTube history can have 10K+ entries with no natural stopping point
3. The user's history went back far enough that it tried to fetch everything

Takeout turned out to be the right answer for bulk historical data. The `fetch` command exists but is less useful than `ingest takeout`.

### Upload date as a proxy for watch date
Before Takeout, we used `publishedAt` (when the video was uploaded to YouTube) as the date range. This was misleading — a video published in 2008 could have been watched yesterday. Once Takeout provided real watch timestamps, this became irrelevant.

## Key Architecture Decisions

### Channel name stored in `channel_id` field
The Video model has `channel_id` but we store the human-readable channel name there (e.g., "Linus Tech Tips" not "UCXuqSBlHAE6Xw-yeJA0Tunw"). This is because the dashboard displays it directly and all our lookups are by name. The actual YouTube channel ID is stored in the `channels` table URL field. Slightly confusing naming but pragmatic.

### Dashboard is a single HTML template with inline JS
The entire dashboard is one `render_template_string` call with ~300 lines of HTML/CSS/JS. No build step, no npm, no framework. This keeps iteration fast (edit Python, restart Flask, refresh browser) but will need restructuring if the dashboard grows much more.

### Stars use a separate table, not a column on channels
`starred_channels` table with just `channel_name` as primary key. Simple, avoids coupling to the channels table (which may not have entries for all channels), and easy to query.

## Current State (as of 2026-03-28)

- **12,735 videos** in the database from Takeout (Nov 2023 — Mar 2026)
- **12,278 categorized** via YouTube Data API
- **5,446 channels** with real YouTube URLs
- Dashboard with genre checkboxes, channel stars, year filter, search
- YouTube API key configured for metadata enrichment
- All tests from Phase 1 plan exist but some may need updating to match current schema

## What's Next

The original spec outlines Phase 2 (embeddings + semantic clustering) but the engagement model needs revisiting first. Possible directions:

1. **YouTube API OAuth** — access liked videos, playlists, subscriptions for real engagement signals
2. **Semantic clustering** — embed video titles/descriptions, cluster by topic rather than YouTube's coarse categories
3. **Transcript fetching** — bulk fetch transcripts for high-value videos, enable full-text search
4. **Dashboard improvements** — sorting columns, pagination, export functionality
5. **Engagement v2** — model based on available signals (starred channels, liked videos, playlist membership, rewatch detection from duplicate Takeout entries)
