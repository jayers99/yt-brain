#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

if ! command -v uv &>/dev/null; then
    echo "Error: uv is not installed. Install with: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

if [ ! -d .venv ]; then
    echo "Setting up environment..."
    uv sync
else
    uv sync --quiet
fi

echo "=== Syncing new videos ==="
uv run yt-brain sync

echo ""
echo "=== Backfilling metadata ==="
uv run yt-brain backfill-channels
uv run yt-brain backfill-dates
uv run yt-brain backfill-categories
uv run yt-brain backfill-descriptions

echo ""
echo "=== Classifying engagement ==="
uv run yt-brain classify

echo ""
echo "=== Generating embeddings ==="
uv run yt-brain embed

echo ""
echo "=== Clustering ==="
uv run yt-brain cluster

echo ""
echo "=== Status ==="
uv run yt-brain status

echo ""
echo "=== Launching dashboard ==="
uv run yt-brain dashboard
