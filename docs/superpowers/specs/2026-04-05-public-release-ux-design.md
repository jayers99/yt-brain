# Public Release UX Design

**Date:** 2026-04-05
**Status:** Draft

## Problem

yt-brain has compelling features (semantic search, genre classification, interactive dashboard) but the onboarding experience is hostile to new users. Commands appear before installation, `uv run` is never explained, API-dependent commands sit in Quick Start without prereq context, and there's no way to verify your setup works.

The goal: make yt-brain installable from PyPI (`pip install yt-brain` / `uvx yt-brain`) and provide a clear, honest installation guide that acknowledges the complexity and walks users through it.

## Design Decisions

- **All four external dependencies are required** for the full experience: Google Takeout (bulk history), yt-dlp + browser cookies (incremental sync/transcripts), YouTube Data API key (metadata enrichment), Anthropic API key (AI cluster naming — optional but included).
- **Dependencies stay in core** — sentence-transformers, sqlite-vec, hdbscan remain in `dependencies`. Semantic search is the killer feature; splitting it out defeats the purpose.
- **sqlite-vec is soft at runtime** — if the native extension fails to load, features degrade gracefully (already partially implemented in dashboard). This prevents install failures on unsupported platforms from blocking the entire app.
- **README is a landing page**, not a setup guide. INSTALL.md is the single source of truth for getting the app working.
- **Sequencing: code first, then docs** — ship `yt-brain doctor` and PyPI publishing before rewriting docs, so docs describe reality.

## Phase 1: `yt-brain doctor`

New CLI command that checks each prerequisite and reports status.

### Checks (in order)

| # | Check | Method | Status values |
|---|-------|--------|---------------|
| 1 | sqlite-vec | Try loading the extension | loadable / not available |
| 2 | yt-dlp | Check if callable on PATH | installed (version) / not found |
| 3 | YouTube Data API key | Check config/env var; make a lightweight test API call (single video metadata) | configured + valid / configured + invalid / not configured |
| 4 | Anthropic API key | Check config/env var; make a test API call | configured + valid / configured + invalid / not configured |
| 5 | Browser cookies | Cannot test without side effects | report as "untested" with guidance |
| 6 | Database status | Count videos, check for embeddings, check for clusters | informational (not pass/fail) |

### Output format

```
$ yt-brain doctor

yt-brain prerequisites check
------------------------------
 sqlite-vec        loadable
 yt-dlp            installed (2024.12.1)
 YouTube API key   not configured
 Anthropic API key configured + valid
 Browser cookies   untested (run 'yt-brain sync' to verify)
 Database          1,247 videos | 1,200 embeddings | 15 clusters

 1 issue found. See INSTALL.md for setup instructions.
```

- Uses Rich for formatting (checkmarks, colors, table alignment)
- Exit code 0 if all critical checks pass, exit code 1 if any fail
- Anthropic API key is non-critical (warning, not failure)
- Browser cookies are untestable without side effects (reported as informational)
- Critical checks: sqlite-vec, yt-dlp, YouTube Data API key

### Implementation location

- New file: `src/yt_brain/application/doctor.py` — check logic
- CLI command registered in `src/yt_brain/cli.py`

## Phase 2: PyPI Publishing

### Package metadata changes

- Add `[project.urls]` — Homepage, Repository, Bug Tracker, Documentation
- Add PyPI classifiers (Development Status, License, Python version, Topic)
- Verify `[project.scripts]` entry works for installed package: `yt-brain = "yt_brain.cli:app"`

### Soft dependency handling

Make native extension imports graceful so `pip install yt-brain` succeeds even when sqlite-vec or other native deps fail to build:

- sqlite-vec: try-import at runtime, disable semantic search features if unavailable (partially done already)
- sentence-transformers: try-import when `embed` command runs, clear error if missing
- hdbscan: try-import when `cluster` command runs, clear error if missing

These remain in `dependencies` (pip will attempt to install them) but the app doesn't crash if they're absent.

### Publishing workflow

- GitHub Actions workflow: `.github/workflows/publish.yml`
- Trigger: on GitHub release (tagged `v*`)
- Build: `python -m build`
- Publish: trusted publishing (OIDC) — GitHub Actions authenticates directly with PyPI, no API tokens
- Requires one-time PyPI trusted publisher setup (link GitHub repo to PyPI project)

### Supported install paths

| Method | Command | Result |
|--------|---------|--------|
| pip | `pip install yt-brain` | Into any Python environment |
| uvx | `uvx yt-brain` | Ephemeral run |
| uv tool | `uv tool install yt-brain` | Permanent global install |

## Phase 3: README.md + INSTALL.md Rewrite

### README.md — Landing page

Structure:
1. CI badge
2. Title + one-liner: "Turn passive YouTube watching into active knowledge."
3. Screenshot
4. Feature highlights (bullet list):
   - Semantic search — find videos by meaning, not just keywords
   - Genre classification — automatic categorization of your watch history
   - Interactive dashboard — filter by genre, channel, time, with combined search
   - Incremental sync — stay current with new watches via yt-dlp
   - AI-powered clustering — discover viewing patterns automatically
5. Install one-liner: `pip install yt-brain`
6. Prominent link: **[Installation & Setup Guide](INSTALL.md) — required before first use**
7. Brief architecture section (hexagonal arch diagram — useful for repo visitors)
8. Links: CONTRIBUTING.md, License

Everything else removed from README.

### INSTALL.md — Setup guide

Structure:
```
WARNING HEADER: yt-brain requires external services and API keys.
`pip install` alone is not enough. Follow this guide completely.

1. Install yt-brain
   - pip install yt-brain
   - OR: uvx yt-brain (ephemeral)
   - OR: uv tool install yt-brain (permanent)
   - OR: clone + uv sync (development)

2. Prerequisites
   a. yt-dlp
      - Install methods (uv tool install, brew, pip)
      - Browser cookie access setup
      - OS-specific notes (macOS Full Disk Access)
   b. YouTube Data API key
      - Google Cloud Console walkthrough
      - Setting the key (env var or config file)
   c. Anthropic API key (optional)
      - For AI-powered cluster naming
      - Falls back to numeric names without it

3. Import your data
   a. Google Takeout walkthrough
      - Step-by-step with expected output
      - JSON format reminder

4. Verify setup
   yt-brain doctor
   - Explain what each check means
   - Link to Troubleshooting for failures

5. Quick Start
   - Commands in correct order, with expected output
   - API-dependent commands clearly marked
   - "You should see..." notes after key steps

6. Troubleshooting
   - sqlite-vec issues (moved from current README)
   - Cookie access issues
   - Missing API key
   - Clustering issues
   - Config location
```

### Content migration

| Current location | New location |
|-----------------|--------------|
| README Setup section | INSTALL.md sections 1-2 |
| README Quick Start | INSTALL.md section 5 |
| README Troubleshooting | INSTALL.md section 6 |
| README Makefile table | CONTRIBUTING.md |
| README Commands table | INSTALL.md section 5 or stays in README (brief) |
| README Dashboard/Search docs | Stay in README (feature highlights) |
| README Data Sources | INSTALL.md section 2 (context for why each dep exists) |
| README Architecture | Stays in README |

## Phasing

| Phase | Scope | PR |
|-------|-------|----|
| 1 | `yt-brain doctor` command | Separate PR |
| 2 | PyPI publishing (package metadata, soft deps, GH Actions workflow) | Separate PR |
| 3 | README.md rewrite + INSTALL.md creation | Separate PR |

Each phase is independently shippable. Phase 3 depends on phases 1 and 2 being merged so docs can reference `yt-brain doctor` and `pip install yt-brain` accurately.
