# Contributing to yt-brain

## Development Setup

```bash
git clone https://github.com/jayers99/yt-brain.git
cd yt-brain
uv sync --dev --extra ai
```

### Makefile

A `Makefile` is included for common dev tasks:

| Target | Command |
|--------|---------|
| `make install` | `uv sync` — install core dependencies |
| `make dev` | `uv sync --dev --extra ai` — install all dev + optional deps |
| `make test` | `uv run pytest -v` |
| `make lint` | `uv run ruff check src/ tests/` |
| `make typecheck` | `uv run mypy` |
| `make run` | `uv run yt-brain dashboard` |
| `make clean` | Remove `__pycache__`, caches, build artifacts |

Run `make` with no arguments to see available targets.

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
