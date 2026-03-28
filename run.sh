#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

# Ensure uv is installed
if ! command -v uv &>/dev/null; then
    echo "Error: uv is not installed. Install with: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# Ensure venv and dependencies are set up
if [ ! -d .venv ]; then
    echo "Setting up environment..."
    uv sync
else
    # Quick check that deps are current
    uv sync --quiet
fi

echo "Syncing YouTube history..."
uv run yt-brain sync

echo ""
echo "Launching dashboard..."
uv run yt-brain dashboard
