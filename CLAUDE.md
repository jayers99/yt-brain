# yt-brain

YouTube Knowledge Brain — ingest, classify, and curate YouTube activity into a personal knowledge base.

## Purpose

- Ingest YouTube watch history (Takeout export, yt-dlp history, manual URL)
- Classify videos by genre (YouTube categories via API, keyword fallback) and engagement level
- Interactive web dashboard for exploring viewing patterns
- Fetch transcripts on demand via yt-dlp
- Phase 1 of 4: foundation for semantic clustering, NotebookLM export, and Obsidian integration
- Learning project: hands-on with vector databases, embeddings, semantic similarity

## CLI Commands

```bash
yt-brain ingest takeout <path>     # Import Google Takeout export (zip or dir)
yt-brain ingest video <url>        # Add a single video manually
yt-brain history [-n 50] [--save]  # Browse/save recent history via yt-dlp
yt-brain fetch <period>            # Fetch history for time period (1yr, 2yr)
yt-brain sync                      # Fetch and add new videos since last sync
yt-brain classify                  # Run engagement classification
yt-brain review                    # Interactive review by tier
yt-brain status                    # CLI dashboard counts
yt-brain dashboard [--port 5555]   # Web dashboard
yt-brain transcript <video_id>     # Fetch transcript via yt-dlp
yt-brain backfill-channels         # Fill channel names via oEmbed
yt-brain backfill-dates            # Fill dates via YouTube Data API
yt-brain backfill-categories       # Fill YouTube categories via Data API
yt-brain config                    # Show/set configuration
```

## Architecture

Hexagonal architecture:
- `domain/` — Pure models, classification logic, errors
- `application/` — Service orchestration (ingest, classify, review, status, transcript)
- `infrastructure/` — SQLite, Takeout parser, yt-dlp, config
- `web/` — Flask dashboard, genre classifier

## Key Files

| File | Purpose |
|------|---------|
| `src/yt_brain/cli.py` | Typer entry point, all commands |
| `src/yt_brain/domain/models.py` | Video, Channel, Playlist, EngagementLevel |
| `src/yt_brain/domain/classifier.py` | Engagement classification logic |
| `src/yt_brain/infrastructure/database.py` | SQLite repository |
| `src/yt_brain/infrastructure/takeout_parser.py` | Google Takeout parser (zip support) |
| `src/yt_brain/infrastructure/ytdlp_adapter.py` | yt-dlp for history, metadata, transcripts |
| `src/yt_brain/web/dashboard.py` | Flask web dashboard |
| `src/yt_brain/web/classifier.py` | Keyword-based genre classifier (fallback) |
| `tests/features/` | BDD scenarios |

## Data

- SQLite DB: `~/.config/yt-brain/yt-brain.db`
- Config: `~/.config/yt-brain/config.yaml`
- YouTube API key stored in config (not in repo)
- Migrations in `migrations/` — auto-applied by `init_db` on startup
- Starred channels persisted in `starred_channels` table
