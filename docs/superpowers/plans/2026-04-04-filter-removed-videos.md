# Filter Removed Videos Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Hide videos with URL-as-title (removed/private YouTube videos) from the dashboard while keeping them in the database.

**Architecture:** Single list comprehension filter in the dashboard index route, applied after DB fetch but before enrichment. One helper function to encapsulate the detection rule.

**Tech Stack:** Python, Flask, pytest

---

## File Map

- **Modify:** `src/yt_brain/web/dashboard.py:1320` — add filter before video list construction
- **Create:** `tests/web/test_filter_removed_videos.py` — unit tests for the filter logic

---

### Task 1: Write failing test for removed video filtering

**Files:**
- Create: `tests/web/test_filter_removed_videos.py`

- [ ] **Step 1: Write the failing test**

```python
"""Test that removed/private videos are filtered from dashboard data."""

from datetime import datetime
from yt_brain.domain.models import Video


def _make_video(youtube_id: str, title: str) -> Video:
    return Video(
        youtube_id=youtube_id,
        title=title,
        channel_id="",
        description="",
        duration_seconds=0,
        watched_at=datetime(2025, 1, 1),
        engagement_level="UNKNOWN",
        source="takeout",
    )


def test_removed_videos_excluded():
    """Videos whose title is a YouTube URL should be filtered out."""
    from yt_brain.web.dashboard import is_removed_video

    removed = _make_video("abc123", "https://www.youtube.com/watch?v=abc123")
    normal = _make_video("def456", "How to Cook Pasta")

    assert is_removed_video(removed) is True
    assert is_removed_video(normal) is False


def test_normal_titles_not_excluded():
    """Titles containing YouTube URLs but not starting with one pass through."""
    from yt_brain.web.dashboard import is_removed_video

    v = _make_video("ghi789", "Check out https://www.youtube.com/watch?v=xyz")
    assert is_removed_video(v) is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/web/test_filter_removed_videos.py -v`
Expected: FAIL with `ImportError: cannot import name 'is_removed_video'`

---

### Task 2: Implement the filter

**Files:**
- Modify: `src/yt_brain/web/dashboard.py:1320`

- [ ] **Step 1: Add the `is_removed_video` helper**

Add this function near the top of `dashboard.py`, after the existing imports and before `classify_genre`:

```python
def is_removed_video(video) -> bool:
    """Return True if the video was removed/private on YouTube.

    Detected by Takeout storing the raw URL as the title when YouTube
    can't resolve the actual video title.
    """
    return video.title.startswith("https://www.youtube.com/watch?v=")
```

- [ ] **Step 2: Add the filter in the index route**

At line 1320 (just before `videos = []`), add the filter to `videos_raw`:

```python
        # Exclude removed/private videos (title is the raw YouTube URL)
        videos_raw = [v for v in videos_raw if not is_removed_video(v)]
```

- [ ] **Step 3: Run tests to verify they pass**

Run: `uv run pytest tests/web/test_filter_removed_videos.py -v`
Expected: PASS (both tests)

- [ ] **Step 4: Commit**

```bash
git add src/yt_brain/web/dashboard.py tests/web/test_filter_removed_videos.py
git commit -m "Filter removed/private videos from dashboard"
```

---

### Task 3: Manual verification

- [ ] **Step 1: Run the dashboard**

Run: `uv run yt-brain dashboard`

- [ ] **Step 2: Verify in browser**

Open the dashboard and confirm:
- No videos with YouTube URL titles appear in the All Videos table
- Total video count in the stats header is ~454 less than before
- Genre breakdown, engagement counts reflect only viewable videos
- Sorting and filtering still work correctly
