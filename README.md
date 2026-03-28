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

# Backfill channel names (uses YouTube oEmbed API)
yt-brain backfill-channels

# Backfill video dates (requires YouTube Data API key)
yt-brain backfill-dates

# Launch the interactive dashboard
yt-brain dashboard
```

## Commands

| Command | Description |
|---------|-------------|
| `ingest takeout <path>` | Import from Google Takeout (zip or directory) |
| `ingest video <url>` | Add a single video by URL |
| `history [-n 50] [--save]` | Browse recent watch history via yt-dlp |
| `fetch <period>` | Fetch history for a time period (e.g. `1yr`, `2yr`) |
| `classify [--reclassify]` | Run engagement classification |
| `review [--level <tier>]` | Interactive review by engagement tier |
| `status` | Show video counts by engagement tier |
| `transcript <video_id>` | Fetch transcript via yt-dlp |
| `backfill-channels` | Fill missing channel names via oEmbed |
| `backfill-dates` | Fill missing dates via YouTube Data API |
| `dashboard [--port 5555]` | Launch web dashboard |
| `config` | Show current configuration |

## Dashboard

The web dashboard provides:

- **Genre Breakdown** with checkboxes to filter by genre
- **Channel Breakdown** with clickable links to YouTube
- **All Videos** table with title and channel search
- **Year filter** dropdown (1yr, 2yr, 3yr, 5yr, all)
- **Date range** display based on actual watch dates

All filters combine — select a year range, check specific genres, and search by title or channel simultaneously.

## Data Sources

| Source | What it provides |
|--------|-----------------|
| **Google Takeout** | Watch history with timestamps, channel names |
| **YouTube Data API** | Video upload dates (via `backfill-dates`) |
| **YouTube oEmbed** | Channel names (via `backfill-channels`) |
| **yt-dlp** | Recent history, video metadata, transcripts |

## Setup

### Google Takeout (recommended)

1. Go to [takeout.google.com](https://takeout.google.com)
2. Select only **YouTube and YouTube Music** > **history**
3. Export and download the zip
4. `yt-brain ingest takeout ~/Downloads/takeout-*.zip`

### YouTube Data API Key (optional)

Required for `backfill-dates` and `fetch` commands.

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
