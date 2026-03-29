# yt-brain

Turn passive YouTube watching into active knowledge.

yt-brain ingests your YouTube watch history, classifies videos by genre and channel, and provides an interactive dashboard to explore your viewing patterns. Built as a foundation for semantic clustering, NotebookLM export, and Obsidian integration.

## Install

```bash
uv sync
```

## Quick Start

```bash
# Import watch history from Google Takeout (zip or directory)
yt-brain ingest takeout ~/Downloads/takeout-*.zip

# Backfill metadata (channel names, categories, dates, descriptions)
yt-brain backfill-channels
yt-brain backfill-categories
yt-brain backfill-dates
yt-brain backfill-descriptions

# Generate semantic embeddings for search
yt-brain embed

# Launch the interactive dashboard
yt-brain dashboard

# Keep data current (fetches new videos from YouTube history)
yt-brain sync
```

## Commands

| Command | Description |
|---------|-------------|
| `ingest takeout <path>` | Import from Google Takeout (zip or directory) |
| `ingest video <url>` | Add a single video by URL |
| `history [-n 50] [--save]` | Browse recent watch history via yt-dlp |
| `fetch <period>` | Fetch history for a time period (e.g. `1yr`, `2yr`) |
| `sync [--browser chrome]` | Fetch and add new videos since last sync |
| `classify [--reclassify]` | Run engagement classification |
| `review [--level <tier>]` | Interactive review by engagement tier |
| `status` | Show video counts by engagement tier |
| `transcript <video_id>` | Fetch transcript via yt-dlp |
| `backfill-channels` | Fill missing channel names via oEmbed |
| `backfill-dates` | Fill missing dates via YouTube Data API |
| `backfill-categories` | Fill missing categories via YouTube Data API |
| `backfill-descriptions` | Fill missing descriptions via YouTube Data API |
| `embed [--rebuild]` | Generate semantic embeddings for search |
| `dashboard [--port 5555]` | Launch web dashboard |
| `config` | Show current configuration |

## Dashboard

The web dashboard provides:

- **Genre Breakdown** with checkboxes to filter by genre
- **Channel Breakdown** with clickable links to YouTube
- **Semantic Search** — find videos by topic or concept, not just exact words
- **Time filter** dropdown (1 day, 1 week, 1 month, 6 months, 1-5 years, all)
- **Date range** display based on actual watch dates

All filters combine — search by topic, select a year range, check specific genres, and filter by starred channels simultaneously.

### Search Syntax

| Query | Behavior |
|-------|----------|
| `machine learning` | Semantic search — finds related videos by meaning |
| `"kubernetes"` | Semantic + exact match on "kubernetes" in title or description |
| `title:"Claude"` | Exact match in title only (case-insensitive) |
| `desc:"tutorial"` | Exact match in description only |
| `channel:"3Blue1Brown"` | Exact match in channel name |
| `AI agents title:"python"` | Semantic search for "AI agents", filtered to titles containing "python" |

Filters are combinable: `machine learning title:"python" channel:"sentdex"`

## Data Sources

| Source | What it provides |
|--------|-----------------|
| **Google Takeout** | Watch history with timestamps, channel names |
| **YouTube Data API** | Video upload dates (via `backfill-dates`) |
| **YouTube oEmbed** | Channel names (via `backfill-channels`) |
| **yt-dlp** | Recent history, video metadata, transcripts |
| **sentence-transformers** | Local semantic embeddings (all-MiniLM-L6-v2) |
| **sqlite-vec** | Vector search for semantic similarity |

## Setup

### Google Takeout (recommended)

1. Go to [takeout.google.com](https://takeout.google.com)
2. Select only **YouTube and YouTube Music** > **history**
3. Export and download the zip
4. `yt-brain ingest takeout ~/Downloads/takeout-*.zip`

### YouTube Data API Key (optional)

Required for `backfill-dates`, `backfill-categories`, `backfill-descriptions`, `fetch`, and `sync`.

1. Create a project in [Google Cloud Console](https://console.cloud.google.com)
2. Enable the YouTube Data API v3
3. Create an API key under Credentials
4. The key is stored in `~/.config/yt-brain/config.yaml`

## Architecture

Hexagonal architecture with swappable infrastructure adapters:

```
src/yt_brain/
├── cli.py                  # Typer CLI entry point
├── domain/                 # Pure models, classification logic
├── application/            # Service orchestration
├── infrastructure/         # SQLite, YouTube API, Takeout parser, yt-dlp
└── web/                    # Flask dashboard, genre classifier
```

Data stored in SQLite at `~/.config/yt-brain/yt-brain.db`.

## License

MIT
