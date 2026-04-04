# Filter Removed Videos from Dashboard

**Date:** 2026-04-04
**Status:** Approved

## Problem

454 of 12,825 videos in the database are no longer viewable on YouTube (removed or made private). These appear in the dashboard's All Videos table with the raw YouTube URL as their title, cluttering the interface with unclickable entries.

## Detection Rule

A video is considered "removed" when its title starts with `https://www.youtube.com/watch?v=`. This occurs because the Takeout import captures the URL as the title when YouTube can't resolve the video's actual title — a reliable indicator that the video was already unavailable at import time.

- 454 videos match this pattern
- 3 of those have partial backfilled metadata (channel/category) but are still unviewable
- 0 false negatives: no videos with real titles lack all metadata

## Design

### Approach: Dashboard-only filter

Filter removed videos in the dashboard route before building the video data list. CLI commands (`status`, `classify`, etc.) remain unaffected and continue to see the full dataset.

### Change Location

Single change in `src/yt_brain/web/dashboard.py`, in the index route handler. After fetching videos from the database but before enrichment and serialization, filter out removed videos:

```python
videos = [v for v in videos if not v.title.startswith("https://www.youtube.com/watch?v=")]
```

### Effects

- All Videos table excludes removed videos
- Dashboard stats (engagement counts, genre breakdown, total count) reflect only viewable videos
- No DB schema changes
- No new fields or migrations
- No UI toggle — removed videos are simply excluded

### Future Considerations

- A "show removed" toggle could be added later if the user wants visibility into removed videos from the GUI
- A `yt-brain check-availability` command could actively verify videos against YouTube, but is out of scope here
