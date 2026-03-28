# yt-brain

Turn passive YouTube watching into active knowledge.

yt-brain captures your YouTube activity, classifies engagement signals, and builds a curated knowledge base that feeds into NotebookLM for deep dives and Obsidian for cross-domain idea generation.

## Install

```bash
uv sync
```

## Usage

```bash
# Import watch history from Google Takeout
yt-brain ingest takeout ~/Downloads/Takeout/

# Classify videos by engagement level
yt-brain classify

# Review and override classifications
yt-brain review

# Check dashboard
yt-brain status
```

## License

MIT
