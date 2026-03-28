# yt-brain — YouTube Knowledge Brain

**Date**: 2026-03-26
**Status**: Approved
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
│   ├── cli.py                  # Typer entry point
│   ├── domain/
│   │   ├── models.py           # Video, Channel, Playlist, EngagementLevel
│   │   ├── classifier.py       # Engagement pyramid logic
│   │   └── services.py         # Domain services (pure)
│   ├── application/
│   │   ├── ingest.py           # Orchestrates ingestion from sources
│   │   ├── classify.py         # Runs classification pipeline
│   │   └── review.py           # Review/curation workflows
│   └── infrastructure/
│       ├── youtube_api.py      # YouTube Data API v3 adapter
│       ├── takeout_parser.py   # Google Takeout JSON/HTML parser
│       ├── ytdlp_adapter.py    # yt-dlp for transcripts & metadata
│       ├── database.py         # SQLite repository
│       └── config.py           # Auth, paths, settings
├── tests/
│   └── features/               # BDD scenarios
└── migrations/                 # SQLite schema versioning
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
yt-brain ingest takeout <path>     # Import Google Takeout export
yt-brain ingest api                # Sync via YouTube Data API (likes, playlists, subs)
yt-brain ingest video <url>        # Add a single video manually

yt-brain classify                  # Run engagement classification on unclassified videos
yt-brain classify --reclassify     # Re-run on everything

yt-brain review                    # Interactive review: videos by engagement tier
yt-brain review --level curated    # Review specific tier
yt-brain review --channel <name>   # Review by channel

yt-brain status                    # Dashboard: counts by tier, unclassified, channels
yt-brain transcript <video_id>     # Fetch transcript via yt-dlp
yt-brain transcript --level liked  # Bulk fetch transcripts for a tier

yt-brain config                    # Show/set API keys, thresholds, paths
```

**Review UX**: Rich terminal output (via Rich library). Videos displayed in a table grouped by engagement tier showing channel, title, watch %, and current classification. Arrow keys to navigate, enter to select, and a simple prompt to reclassify (e.g., `[b]ounce [w]atched [l]iked [c]urated [s]kip`). Overrides are stored as `engagement_override` on the video record.

**Key workflows:**
1. **Initial backfill**: `yt-brain ingest takeout <path>` → `yt-brain classify` → `yt-brain review`
2. **Ongoing sync**: `yt-brain ingest api` → `yt-brain classify`
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

**Primary: YouTube Data API v3** for ongoing sync (likes, playlists, subscriptions).

**Backfill: Google Takeout** for historical data — critically, Takeout includes watch duration which the API does not expose. This is the only source for the bounced/watched classification of historical videos.

**Enrichment: yt-dlp** for transcripts and extended metadata on demand.

### Design Decisions

- **SQLite over Postgres/Firestore**: Personal tool, own your data, no server. sqlite-vss upgrade path for Phase 2.
- **Transcripts on demand, not at ingest**: yt-dlp is slow; only fetch for videos worth keeping.
- **Engagement tiers drive downstream phases**: Only WATCHED+ gets embedded in Phase 2. BOUNCED is data you can query but won't invest compute in.
- **Hexagonal architecture**: Matches existing Praxis extensions. Infrastructure adapters (API, Takeout, yt-dlp) are swappable.

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
