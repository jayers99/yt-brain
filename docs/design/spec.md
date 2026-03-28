# yt-brain — YouTube Knowledge Brain

**Date**: 2026-03-26 (updated 2026-03-27)
**Status**: MVP Complete
**Phase**: 1 of 4 (Ingestion + Engagement Classification)

## Vision

Turn passive YouTube watching into active knowledge. yt-brain captures your YouTube activity, classifies engagement signals, and builds a curated knowledge base that feeds into NotebookLM for deep dives and Obsidian for cross-domain idea generation.

The tool is both the product and the classroom — building it teaches vector databases, embeddings, semantic similarity, and clustering algorithms using your own data.

## Full Pipeline

```
Watch → Classify → Curate → Export to NotebookLM → Generate insights → Connect in Obsidian
```

## Phase 1 Scope: Ingestion + Engagement Classification

### Project Structure

Standalone learning project.

```
yt-brain/
├── pyproject.toml              # uv, Python 3.12+
├── CLAUDE.md
├── src/yt_brain/
│   ├── cli.py                  # Typer entry point (all commands)
│   ├── domain/
│   │   ├── models.py           # Video, Channel, Playlist, EngagementLevel
│   │   ├── classifier.py       # Engagement classification logic
│   │   └── errors.py           # Domain exceptions
│   ├── application/
│   │   ├── ingest.py           # Orchestrates ingestion (Takeout zip/dir, manual)
│   │   ├── classify.py         # Runs classification pipeline
│   │   ├── review.py           # Review/curation workflows
│   │   ├── status.py           # Status dashboard service
│   │   └── transcript.py       # Transcript fetch service
│   ├── infrastructure/
│   │   ├── takeout_parser.py   # Google Takeout JSON parser (zip support)
│   │   ├── ytdlp_adapter.py    # yt-dlp for history, transcripts & metadata
│   │   ├── database.py         # SQLite repository
│   │   └── config.py           # Auth, paths, settings
│   └── web/
│       ├── classifier.py       # Keyword-based genre classifier
│       └── dashboard.py        # Flask web dashboard
├── tests/
│   ├── features/               # BDD scenarios
│   └── step_defs/              # Step definitions
├── migrations/                 # SQLite schema versioning
└── docs/design/                # Specs and plans
```

Follows hexagonal architecture pattern. Infrastructure adapters (API, Takeout, yt-dlp) are swappable.

### Domain Models

**Video**
- youtube_id (str)
- title, description, channel_id
- duration_seconds (int)
- watched_seconds (int, nullable)
- watched_at (datetime)
- engagement_level (EngagementLevel)
- engagement_override (nullable) — manual reclassification
- transcript (text, nullable) — populated on demand via yt-dlp
- tags (list[str]) — YouTube's tags + custom
- source (enum: api | takeout | manual)

**Channel**
- youtube_id, name, url
- subscription_status (bool)

**Playlist**
- youtube_id, title
- is_user_created (bool)
- videos (list[video_id])

### Engagement Classification

| Level | Signal | Rule |
|-------|--------|------|
| `BOUNCED` | Barely watched | watched < 15% of duration |
| `WATCHED` | Finished it | watched >= 85% of duration |
| `LIKED` | Thumbs up | in YouTube liked videos |
| `CURATED` | Playlist'd | added to any user playlist |
| `UNKNOWN` | No watch data | API-sourced without duration info |

Highest signal wins. Thresholds (15%, 85%) are configurable. Users can override any classification manually during review.

### CLI Commands

```
yt-brain ingest takeout <path>     # Import Google Takeout export (zip or directory)
yt-brain ingest video <url>        # Add a single video manually
yt-brain history [-n 50] [--save]  # Browse/save recent history via yt-dlp
yt-brain fetch <period>            # Fetch history for a time period (1yr, 2yr, etc.)

yt-brain classify                  # Run engagement classification on unclassified videos
yt-brain classify --reclassify     # Re-run on everything

yt-brain review                    # Interactive review: videos by engagement tier
yt-brain review --level curated    # Review specific tier

yt-brain status                    # CLI dashboard: counts by tier
yt-brain dashboard [--port 5555]   # Web dashboard with interactive filters
yt-brain transcript <video_id>     # Fetch transcript via yt-dlp
yt-brain transcript --level liked  # Bulk fetch transcripts for a tier

yt-brain backfill-channels         # Fill missing channel names via oEmbed
yt-brain backfill-dates            # Fill missing dates via YouTube Data API
yt-brain config                    # Show/set API keys, thresholds, paths
```

**Review UX**: Rich terminal output (via Rich library). Videos displayed in a table grouped by engagement tier showing channel, title, watch %, and current classification. Simple prompt to reclassify (e.g., `[b]ounce [w]atched [l]iked [c]urated [s]kip`). Overrides are stored as `engagement_override` on the video record.

**Web Dashboard**: Flask-based dark-theme dashboard with:
- Genre breakdown with checkbox filters (select all/none)
- Channel breakdown with clickable YouTube links
- All Videos table with title and channel search
- Year filter dropdown (1yr, 2yr, 3yr, 5yr, all time)
- Date range display from actual watch dates
- All filters combine and recalculate stats dynamically

**Key workflows:**
1. **Initial backfill**: `yt-brain ingest takeout <path>` → `yt-brain backfill-channels` → `yt-brain dashboard`
2. **Quick history**: `yt-brain history --save -n 200` (auto-backfills channel names)
3. **Deep dive prep**: `yt-brain transcript --level curated`

### Data Storage

**SQLite database**: `~/.config/yt-brain/yt-brain.db`

Tables:
- `videos` — core video records with engagement data
- `channels` — channel metadata and subscription status
- `playlists` — playlist metadata
- `playlist_videos` — many-to-many join (playlist_id, video_id, position)

SQLite chosen because:
- Zero infrastructure, single file, portable
- Phase 2 can add vector search via `sqlite-vss` without changing the stack
- Easy to query, back up, inspect, reset

**Transcript storage**: Text column on video record, fetched on demand only (yt-dlp calls are slow; only worth it for videos you're keeping).

**Schema migrations**: Numbered SQL files in `migrations/`. A `schema_version` table tracks applied migrations. No ORM — raw SQL with a thin repository layer.

**Config**: `~/.config/yt-brain/config.yaml`
```yaml
youtube_api_key: ...
oauth_credentials: ~/.config/yt-brain/oauth.json
thresholds:
  bounced_below: 0.15
  watched_above: 0.85
transcript_language: en
```

### Data Source Strategy

**Primary: Google Takeout** for historical data — Takeout provides watch timestamps and channel names. This is the richest data source for building the history.

**Metadata enrichment: YouTube Data API v3** for video upload dates (used by `backfill-dates`). Requires an API key (free tier).

**Channel names: YouTube oEmbed API** for resolving channel names when not available from Takeout (used by `backfill-channels`). No auth required.

**Live history + transcripts: yt-dlp** for browsing recent watch history via browser cookies and fetching transcripts on demand.

**Deferred: YouTube Data API OAuth** for syncing likes, playlists, and subscriptions. Planned for Phase 1.5.

### Design Decisions

- **SQLite over Postgres/Firestore**: Personal tool, own your data, no server. sqlite-vss upgrade path for Phase 2.
- **Transcripts on demand, not at ingest**: yt-dlp is slow; only fetch for videos worth keeping.
- **Keyword-based genre classification**: Simple regex rules classify videos by title into ~15 genres. Good enough for exploration; ML classification deferred to Phase 2.
- **Watch percentage not available externally**: YouTube does not expose watch duration through any API. Engagement classification (BOUNCED/WATCHED) requires Takeout data with watch details, which is rare. Current MVP focuses on genre and channel analysis.
- **Hexagonal architecture**: Infrastructure adapters (API, Takeout, yt-dlp) are swappable.
- **Client-side dashboard filtering**: All filter logic runs in the browser via JS for instant responsiveness without server round-trips.

## Future Phases (Vision Only)

### Phase 2: Embeddings + Semantic Clustering
- Embed metadata + transcripts using an embedding model
- Vector storage via sqlite-vss
- Automatic topic clustering
- `yt-brain explore` for semantic similarity and discovery
- Hands-on learning: embeddings, distance metrics, clustering algorithms

### Phase 3: Curation + NotebookLM Export
- `yt-brain curate` — review/name/merge clusters, add cross-connections
- `yt-brain export notebooklm --cluster <name>` — bundle for NotebookLM ingestion
- Deep-dive podcast generation per topic cluster
- Manual "oddball connections" across clusters

### Phase 4: Obsidian Integration
- `yt-brain export obsidian` — markdown notes with backlinks, tags, cluster membership
- Video notes + cluster MOCs (Maps of Content)
- Cross-reference with existing vault
- Surface research gaps and new topic ideas
