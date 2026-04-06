# Installation & Setup Guide

> **Important:** yt-brain requires external tools and API keys to function. Installing the Python package alone is not enough. Follow this guide completely before using the application.

## 1. Install yt-brain

Choose one:

```bash
# Recommended: permanent global install
uv tool install yt-brain

# Or: install into an existing Python environment
pip install yt-brain

# Or: one-off run without installing
uvx yt-brain

# Or: install from source (for development)
git clone https://github.com/jayers99/yt-brain.git
cd yt-brain
uv sync
# Commands use: uv run yt-brain <command>
```

## 2. Prerequisites

### a. yt-dlp

Required for syncing new watch history and fetching transcripts.

**Install:**

```bash
# Recommended
uv tool install yt-dlp

# Or via Homebrew (macOS)
brew install yt-dlp
```

**Browser cookie access:** yt-dlp reads your YouTube login cookies to access watch history. You must be logged into YouTube in your browser.

- **macOS:** Grant Full Disk Access to your terminal app (System Settings > Privacy & Security > Full Disk Access)
- **Supported browsers:** Chrome, Firefox, Edge, Safari, Opera, Brave

### b. YouTube Data API key

Required for enriching video metadata (upload dates, categories, descriptions).

1. Create a project in [Google Cloud Console](https://console.cloud.google.com)
2. Enable **YouTube Data API v3**
3. Create an API key under **Credentials**
4. Configure it:

```bash
# Option 1: Environment variable
export YOUTUBE_API_KEY="your-key-here"

# Option 2: Config file (~/.config/yt-brain/config.yaml)
youtube_api_key: your-key-here
```

### c. Anthropic API key (optional)

Used for AI-powered cluster naming. Without it, clusters get numeric IDs instead of descriptive names.

```bash
# Option 1: Environment variable
export ANTHROPIC_API_KEY="your-key-here"

# Option 2: Config file (~/.config/yt-brain/config.yaml)
anthropic_api_key: your-key-here
```

## 3. Import Your Data

### Google Takeout (recommended starting point)

Google Takeout is the only way to get your full watch history. This is a one-time bulk import.

1. Go to [takeout.google.com](https://takeout.google.com)
2. Deselect all, then select only **YouTube and YouTube Music** > **history**
3. Choose **JSON** format (not HTML)
4. Export and download the zip
5. Import:

```bash
yt-brain ingest takeout ~/Downloads/takeout-*.zip
```

You should see: `Ingested <N> videos from Takeout.` where N is typically hundreds to thousands.

## 4. Verify Setup

Run the doctor command to check everything is configured:

```bash
yt-brain doctor
```

All critical checks should show ✅. Fix any ❌ items using the instructions above.

## 5. Quick Start

After setup, here's the typical workflow:

```bash
# Enrich your imported data with metadata
yt-brain backfill-channels       # Fill channel names (no API key needed)
yt-brain backfill-categories     # Fill video categories (needs YouTube API key)
yt-brain backfill-dates          # Fill upload dates (needs YouTube API key)
yt-brain backfill-descriptions   # Fill descriptions (needs YouTube API key)

# Generate semantic embeddings for search
yt-brain embed
# This downloads the all-MiniLM-L6-v2 model (~80MB) on first run
# and processes all videos. Takes 1-2 minutes for ~1000 videos.

# Launch the dashboard
yt-brain dashboard
# Opens http://localhost:5555 in your browser

# Keep data current (run periodically)
yt-brain sync
```

## 6. Troubleshooting

### sqlite-vec installation issues

sqlite-vec is a native SQLite extension for semantic search. If it fails to install:

- **macOS (Apple Silicon):** Usually works with `uv sync`. If not: `brew install sqlite` first
- **macOS (Intel):** `brew install sqlite && uv sync`
- **Linux (x86_64):** Install `libsqlite3-dev` (`apt install libsqlite3-dev`), then reinstall
- **Linux (ARM):** Build from source: `pip install sqlite-vec --no-binary sqlite-vec`

When sqlite-vec is unavailable, dashboard search falls back to text matching. All other features work normally.

### "Could not extract cookies" / sync fails

- Ensure you're logged into YouTube in your browser
- macOS: grant Full Disk Access to your terminal (System Settings > Privacy & Security)
- Try a different browser: `yt-brain sync --browser firefox`

### "Missing youtube_api_key"

Set your API key via environment variable or config file. See [Prerequisites](#b-youtube-data-api-key) above.

### "Not enough videos to cluster"

You need at least 10 videos with embeddings. Run `yt-brain embed` first, then `yt-brain cluster --rebuild`.

### Config location

All data is stored in `~/.config/yt-brain/`:
- `config.yaml` — API keys, thresholds
- `yt-brain.db` — SQLite database with all video data

Override with: `export YT_BRAIN_CONFIG_DIR=/path/to/dir`
