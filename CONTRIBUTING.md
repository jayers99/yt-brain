# Contributing to yt-brain

## Development Setup

```bash
git clone https://github.com/jayers99/yt-brain.git
cd yt-brain
uv sync --dev --extra ai
```

## Running Tests

```bash
uv run pytest -v
```

## Code Quality

```bash
uv run ruff check src/ tests/
uv run mypy
```

Pre-commit hooks run automatically if you install them:

```bash
uv run pre-commit install
```

## Architecture

yt-brain uses hexagonal architecture:

- **domain/** — Pure models and business logic. No external dependencies.
- **application/** — Service orchestration. Depends on domain, calls infrastructure.
- **infrastructure/** — SQLite, yt-dlp, YouTube API, config. Implements domain interfaces.
- **web/** — Flask dashboard. Depends on infrastructure for data access.

## Pull Requests

- Keep PRs focused on a single change
- Include tests for new functionality
- Run `ruff check` and `mypy` before submitting
