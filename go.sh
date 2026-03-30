#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

if ! command -v uv &>/dev/null; then
    echo "Error: uv is not installed. Install with: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

uv sync --quiet
uv run yt-brain dashboard
