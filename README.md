[![CI](https://github.com/jayers99/yt-brain/actions/workflows/ci.yml/badge.svg)](https://github.com/jayers99/yt-brain/actions/workflows/ci.yml)

# yt-brain

Turn passive YouTube watching into active knowledge.

yt-brain ingests your YouTube watch history, classifies videos by genre and channel, and provides an interactive dashboard to explore your viewing patterns.

![yt-brain Dashboard](docs/app_screen_shot.png)

## Features

- **Semantic search** — find videos by meaning, not just keywords (powered by sentence-transformers + sqlite-vec)
- **Genre classification** — automatic categorization using YouTube categories and keyword analysis
- **Interactive dashboard** — filter by genre, channel, time range, and starred channels simultaneously
- **Incremental sync** — stay current with new watches via yt-dlp browser cookie integration
- **AI-powered clustering** — discover viewing patterns with HDBSCAN + Claude-generated topic names
- **Google Takeout import** — bulk import your full watch history

## Install

```bash
pip install yt-brain
```

**[Installation & Setup Guide](INSTALL.md)** — yt-brain requires external tools and API keys. Follow the setup guide before first use.

## Commands

| Command | Description |
|---------|-------------|
| `ingest takeout <path>` | Import from Google Takeout (zip or directory) |
| `ingest video <url>` | Add a single video by URL |
| `sync [--browser chrome]` | Fetch and add new videos since last sync |
| `embed [--rebuild]` | Generate semantic embeddings for search |
| `cluster [--rebuild]` | Run topic clustering on embedded videos |
| `dashboard [--port 5555]` | Launch web dashboard |
| `doctor` | Check that prerequisites are installed and configured |
| `status` | Show video counts by engagement tier |
| `classify` | Run engagement classification |
| `backfill-channels` | Fill missing channel names |
| `backfill-categories` | Fill missing categories (needs API key) |
| `backfill-dates` | Fill missing dates (needs API key) |
| `backfill-descriptions` | Fill missing descriptions (needs API key) |
| `transcript <video_id>` | Fetch transcript via yt-dlp |
| `config` | Show current configuration |

## Dashboard

The web dashboard provides:

- **Genre Breakdown** with checkboxes to filter by genre
- **Channel Breakdown** with clickable links to YouTube
- **Semantic Search** — find videos by topic or concept, not just exact words
- **Time filter** dropdown (1 day, 1 week, 1 month, 6 months, 1-5 years, all)
- **Date range** display based on actual watch dates

### Search Syntax

| Query | Behavior |
|-------|----------|
| `machine learning` | Semantic search — finds related videos by meaning |
| `"kubernetes"` | Semantic + exact match on "kubernetes" in title or description |
| `title:"Claude"` | Exact match in title only (case-insensitive) |
| `desc:"tutorial"` | Exact match in description only |
| `channel:"3Blue1Brown"` | Exact match in channel name |
| `AI agents title:"python"` | Semantic search for "AI agents", filtered to titles containing "python" |

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

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup and guidelines.

## License

MIT
