# yt-brain

YouTube Knowledge Brain — ingest, classify, and curate YouTube activity into a personal knowledge base.

## Purpose

- Ingest YouTube watch history (Takeout export, API sync, manual URL)
- Classify videos by engagement level (bounced, watched, liked, curated)
- Review and override classifications
- Fetch transcripts on demand via yt-dlp
- Phase 1 of 4: foundation for semantic clustering, NotebookLM export, and Obsidian integration
- Learning project: hands-on with vector databases, embeddings, semantic similarity

## CLI Commands

```bash
yt-brain ingest takeout <path>     # Import Google Takeout export
yt-brain ingest api                # Sync via YouTube Data API
yt-brain ingest video <url>        # Add a single video manually
yt-brain classify                  # Run engagement classification
yt-brain review                    # Interactive review by tier
yt-brain status                    # Dashboard counts
yt-brain transcript <video_id>     # Fetch transcript via yt-dlp
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
