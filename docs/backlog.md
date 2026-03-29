# yt-brain Feature Backlog

| # | Slug | Description | Status |
|---|------|-------------|--------|
| 1 | `semantic-search` | Backfill descriptions + embed title/description with sentence-transformers + sqlite-vec search in dashboard | **Complete** |
| 2 | `embed-and-cluster` | Auto-cluster videos by topic using embeddings (Phase 2 vision) | **Complete** |
| 3 | `video-ratings` | Thumbs up/down column in All Videos table; toggle ratings in dashboard and sync back to YouTube via OAuth | Backlog |
| 4 | `channel-scoring` | Score channels 0-10 from engagement signals (stars, watch frequency, completion) | Backlog |
| 5 | `playlist-awareness` | Detect when liked/starred videos belong to a playlist; recommend full sequences | Backlog |
| 6 | `transcript-bulk-fetch` | Bulk-fetch transcripts for starred channels or high-engagement tiers | Backlog |
| 7 | `channel-graduation` | Promote top channels into a "graduated" tier for RAG/NotebookLM export | Backlog |
| 8 | `notebooklm-export` | Bundle graduated channel transcripts for NotebookLM ingestion | Backlog |
| 9 | `obsidian-export` | Generate markdown notes with backlinks, tags, and cluster MOCs | Backlog |
| 10 | `queue-engine` | Curated learning queue synced to a YouTube playlist for cross-device playback | Backlog |
| 11 | `semantic-discovery` | Surface related creators/topics via embedding similarity | Backlog |
| 12 | `scheduled-sync` | Cron/launchd wrapper for daily `yt-brain sync` | Backlog |
