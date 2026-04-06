# yt-brain Feature Backlog

| # | Slug | Description | Status |
|---|------|-------------|--------|
| 1 | `semantic-search` | Backfill descriptions + embed title/description with sentence-transformers + sqlite-vec search in dashboard | **Complete** |
| 2 | `embed-and-cluster` | Auto-cluster videos by topic using embeddings (Phase 2 vision) | **Complete** |
| 3 | `brain-drain` | Detect binge spirals of low-quality content: velocity, duration, late-night flag, drinking detection | Backlog |
| 4 | `engagement-scoring` | Replace coarse 5-tier classification with continuous engagement metric for videos and channels | Backlog |
| 5 | `taste-drift` | Monthly visualization of shifting interests using cluster embeddings over time windows | Backlog |
| 6 | `shame-score` | Weekly report card aggregating brain-drain sessions with trends and Claude-generated roasts | Backlog |
| 7 | `transcript-bulk-fetch` | Bulk-fetch transcripts for starred channels or high-engagement tiers | Backlog |
| 8 | `channel-autopsy` | Claude-generated eulogies for channels with declining engagement over time | Backlog |
| 9 | `clear-all-filters` | Single button in dashboard to reset all active filters (genre, date, star, search) at once | Backlog |
| 10 | `scheduled-sync` | Cron/launchd wrapper for daily `yt-brain sync` | Backlog |
| 11 | `channel-scoring` | Score channels 0-10 from engagement signals (stars, watch frequency, completion) | Backlog |
| 12 | `channel-graduation` | Promote top channels into a "graduated" tier for RAG/NotebookLM export | Backlog |
| 13 | `notebooklm-export` | Bundle graduated channel transcripts for NotebookLM ingestion | Backlog |
| 14 | `obsidian-export` | Generate markdown notes with backlinks, tags, and cluster MOCs | Backlog |
| 15 | `semantic-discovery` | Surface related creators/topics via embedding similarity | Backlog |
| 16 | `sober-queue` / `drunk-queue` | Split watch-next playlists by time-of-day; confront daytime-you with 1am-you | Backlog |
| 17 | `watch-next-agent` | Always-on recommendation agent that maintains a curated playlist ranked by predicted enjoyment | Backlog |
| 18 | `playlist-awareness` | Detect when liked/starred videos belong to a playlist; recommend full sequences | Backlog |
| 19 | `video-ratings` | Thumbs up/down column in All Videos table; toggle ratings in dashboard and sync back to YouTube via OAuth | Backlog |
| 20 | `queue-engine` | Curated learning queue synced to a YouTube playlist for cross-device playback | Backlog |
| 21 | `guilty-pleasure-budget` | Weekly brain rot allowance with real-time balance tracking and overdraft penalties | Backlog |
| 22 | `public-release` | Package yt-brain for non-technical users: installation, API key problem, hosted options | Backlog |
| 23 | `watch-timeline` | Bar chart of videos watched over time; x-axis adapts to active date filter (day/week/month/all-time) with appropriate bucket widths | Backlog |
| 24 | `genre-timeline` | Multi-line time series layered on watch-timeline with one line per genre; visualize binge patterns across categories (entertainment vs education vs etc.) | Backlog |
| 25 | `favicon-optimize` | Redesign favicons for legibility at small sizes (16x16, 32x32); simplify detail for browser tabs | Backlog |
| 26 | `short-query-search` | Improve search for short queries (2-3 chars like "4K"); explore hybrid approach — substring/LIKE match for short input, semantic for longer; longer debounce on short queries to avoid wasted API calls | Backlog |
| 27 | `public-repo-cleanup` | Clean up repo artifacts before public release. **Delete:** `docs/superpowers/` (implementation scaffolding, redundant with merged code), `images/filter-expand-outside-bounds*.png` (debug screenshots), `images/favicon_io.zip` (extracted files already present), `.DS_Store`. **Gitignore:** `docs/superpowers/`, `.DS_Store`, `praxis.yaml`. **Keep:** `docs/design/` (dev journals with design rationale — learning value), `go.sh`/`update.sh` (convenience scripts, document in README), `images/favicon_io/` + `images/yt-brain-toon*.png` (branding). **Decide later:** `praxis.yaml` — personal workspace metadata, remove or gitignore. `docs/backlog.md` — personal task list, consider removing for public. Need a more central solution for superpowers planning docs across projects. | Backlog |
