# All Videos Table: Sorting & New Columns — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add liked/watched/published columns to the All Videos table, client-side column sorting, and a liked-status filter — backed by a new migration and yt-dlp-based liked-video sync.

**Architecture:** New DB columns via migration 007, a new `fetch_liked_ids()` in the yt-dlp adapter, a `backfill_likes()` service + CLI command, dashboard HTML/JS/CSS updates for 7-column table with sort and filter. All sorting is client-side DOM reordering using the existing `videoData` cache.

**Tech Stack:** Python 3.12, SQLite, Flask/Jinja2, yt-dlp, vanilla JavaScript

---

## File Structure

| File | Responsibility |
|------|---------------|
| `migrations/007_video_liked_published.sql` | Add `liked` TEXT and `published_at` TEXT columns |
| `src/yt_brain/infrastructure/database.py` | New DB functions: `update_video_liked()`, `update_published_at()`, `get_all_video_ids()` |
| `src/yt_brain/infrastructure/ytdlp_adapter.py` | New `fetch_liked_ids()` — fetches LL playlist via yt-dlp |
| `src/yt_brain/application/backfill.py` | New `backfill_likes()`, update `backfill_dates()` to also populate `published_at` |
| `src/yt_brain/application/sync.py` | Add liked refresh to sync pipeline |
| `src/yt_brain/cli.py` | New `backfill-likes` command |
| `src/yt_brain/web/dashboard.py` | 7-column table HTML, sort JS, liked filter JS, CSS |
| `tests/step_defs/test_backfill.py` | Tests for `backfill_likes()` |
| `tests/step_defs/test_database.py` | Tests for new DB functions |

---

### Task 1: Database Migration

**Files:**
- Create: `migrations/007_video_liked_published.sql`

- [ ] **Step 1: Write the migration SQL**

```sql
ALTER TABLE videos ADD COLUMN liked TEXT DEFAULT NULL;
ALTER TABLE videos ADD COLUMN published_at TEXT DEFAULT NULL;

INSERT INTO schema_version (version) VALUES (7);
```

Create the file at `migrations/007_video_liked_published.sql`.

- [ ] **Step 2: Verify migration applies**

Run:
```bash
cd /Users/jayers/code/praxis-workspace/projects/learn/yt-brain
uv run python -c "
from pathlib import Path
from yt_brain.infrastructure.database import init_db
import sqlite3, tempfile, os
with tempfile.TemporaryDirectory() as d:
    db = Path(d) / 'test.db'
    init_db(db)
    conn = sqlite3.connect(db)
    cols = [r[1] for r in conn.execute('PRAGMA table_info(videos)').fetchall()]
    assert 'liked' in cols, f'liked not in {cols}'
    assert 'published_at' in cols, f'published_at not in {cols}'
    ver = conn.execute('SELECT MAX(version) FROM schema_version').fetchone()[0]
    assert ver == 7, f'version is {ver}'
    print('Migration OK: liked, published_at columns added, version=7')
    conn.close()
"
```
Expected: `Migration OK: liked, published_at columns added, version=7`

- [ ] **Step 3: Commit**

```bash
git add migrations/007_video_liked_published.sql
git commit -m "Add liked and published_at columns to videos table"
```

---

### Task 2: Database Functions

**Files:**
- Modify: `src/yt_brain/infrastructure/database.py`
- Test: `tests/step_defs/test_database.py`

- [ ] **Step 1: Write failing tests for new DB functions**

Add to `tests/step_defs/test_database.py`:

```python
def test_update_video_liked(temp_db):
    from yt_brain.infrastructure.database import update_video_liked

    v = Video(youtube_id="lik1", title="Liked Video", channel_id="ch1")
    save_video(temp_db, v)
    update_video_liked(temp_db, "lik1", "like")

    conn = sqlite3.connect(temp_db)
    row = conn.execute("SELECT liked FROM videos WHERE youtube_id = 'lik1'").fetchone()
    conn.close()
    assert row[0] == "like"


def test_update_video_liked_null(temp_db):
    from yt_brain.infrastructure.database import update_video_liked

    v = Video(youtube_id="lik2", title="Unliked Video", channel_id="ch1")
    save_video(temp_db, v)
    update_video_liked(temp_db, "lik2", None)

    conn = sqlite3.connect(temp_db)
    row = conn.execute("SELECT liked FROM videos WHERE youtube_id = 'lik2'").fetchone()
    conn.close()
    assert row[0] is None


def test_bulk_update_liked(temp_db):
    from yt_brain.infrastructure.database import bulk_update_liked

    for vid_id in ["a1", "a2", "a3"]:
        save_video(temp_db, Video(youtube_id=vid_id, title=f"V {vid_id}", channel_id="ch"))
    bulk_update_liked(temp_db, {"a1": "like", "a2": "dislike", "a3": None})

    conn = sqlite3.connect(temp_db)
    rows = {r[0]: r[1] for r in conn.execute("SELECT youtube_id, liked FROM videos WHERE youtube_id IN ('a1','a2','a3')").fetchall()}
    conn.close()
    assert rows == {"a1": "like", "a2": "dislike", "a3": None}


def test_update_published_at(temp_db):
    from yt_brain.infrastructure.database import update_published_at

    v = Video(youtube_id="pub1", title="Published Video", channel_id="ch1")
    save_video(temp_db, v)
    update_published_at(temp_db, "pub1", "2024-06-15T10:00:00Z")

    conn = sqlite3.connect(temp_db)
    row = conn.execute("SELECT published_at FROM videos WHERE youtube_id = 'pub1'").fetchone()
    conn.close()
    assert row[0] == "2024-06-15T10:00:00Z"


def test_get_all_video_ids(temp_db):
    from yt_brain.infrastructure.database import get_all_video_ids

    for vid_id in ["x1", "x2"]:
        save_video(temp_db, Video(youtube_id=vid_id, title=f"V {vid_id}", channel_id="ch"))
    result = get_all_video_ids(temp_db)
    assert result == {"x1", "x2"}
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/step_defs/test_database.py::test_update_video_liked tests/step_defs/test_database.py::test_update_video_liked_null tests/step_defs/test_database.py::test_bulk_update_liked tests/step_defs/test_database.py::test_update_published_at tests/step_defs/test_database.py::test_get_all_video_ids -v`
Expected: FAIL with `ImportError: cannot import name 'update_video_liked'`

- [ ] **Step 3: Implement the DB functions**

Add to `src/yt_brain/infrastructure/database.py` after the `update_description` function (after line 329):

```python
def update_video_liked(db_path: Path, youtube_id: str, liked: str | None) -> None:
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            "UPDATE videos SET liked = ?, updated_at = datetime('now') WHERE youtube_id = ?",
            (liked, youtube_id),
        )
        conn.commit()
    finally:
        conn.close()


def bulk_update_liked(db_path: Path, liked_map: dict[str, str | None]) -> None:
    """Update liked status for multiple videos. liked_map = {youtube_id: 'like'|'dislike'|None}."""
    conn = sqlite3.connect(db_path)
    try:
        conn.executemany(
            "UPDATE videos SET liked = ?, updated_at = datetime('now') WHERE youtube_id = ?",
            [(status, vid) for vid, status in liked_map.items()],
        )
        conn.commit()
    finally:
        conn.close()


def update_published_at(db_path: Path, youtube_id: str, published_at: str) -> None:
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            "UPDATE videos SET published_at = ?, updated_at = datetime('now') WHERE youtube_id = ?",
            (published_at, youtube_id),
        )
        conn.commit()
    finally:
        conn.close()


def get_all_video_ids(db_path: Path) -> set[str]:
    """Return all youtube_ids in the database."""
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.execute("SELECT youtube_id FROM videos")
        return {row[0] for row in cursor.fetchall()}
    finally:
        conn.close()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/step_defs/test_database.py::test_update_video_liked tests/step_defs/test_database.py::test_update_video_liked_null tests/step_defs/test_database.py::test_bulk_update_liked tests/step_defs/test_database.py::test_update_published_at tests/step_defs/test_database.py::test_get_all_video_ids -v`
Expected: 5 PASSED

- [ ] **Step 5: Commit**

```bash
git add src/yt_brain/infrastructure/database.py tests/step_defs/test_database.py
git commit -m "Add DB functions for liked status and published_at"
```

---

### Task 3: yt-dlp Liked Videos Fetcher

**Files:**
- Modify: `src/yt_brain/infrastructure/ytdlp_adapter.py`
- Test: `tests/step_defs/test_backfill.py`

- [ ] **Step 1: Write the failing test**

Add to `tests/step_defs/test_backfill.py`:

```python
def test_fetch_liked_ids(temp_db):
    from unittest.mock import patch
    from yt_brain.infrastructure.ytdlp_adapter import fetch_liked_ids

    fake_output = "abc123\ndef456\nghi789\n"
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = fake_output

    with patch("yt_brain.infrastructure.ytdlp_adapter.subprocess.run", return_value=mock_result):
        ids = fetch_liked_ids(browser="chrome")

    assert ids == ["abc123", "def456", "ghi789"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/step_defs/test_backfill.py::test_fetch_liked_ids -v`
Expected: FAIL with `ImportError: cannot import name 'fetch_liked_ids'`

- [ ] **Step 3: Implement `fetch_liked_ids`**

Add to `src/yt_brain/infrastructure/ytdlp_adapter.py` after the `fetch_history_range` function (after line 131):

```python
def fetch_liked_ids(browser: str = "chrome") -> list[str]:
    """Fetch video IDs from the user's Liked Videos playlist via yt-dlp."""
    try:
        result = subprocess.run(
            [
                "yt-dlp",
                "--cookies-from-browser", browser,
                "--flat-playlist",
                "--print", "id",
                "https://www.youtube.com/playlist?list=LL",
            ],
            capture_output=True,
            text=True,
            timeout=120,
        )
    except FileNotFoundError as err:
        raise IngestError("yt-dlp is not installed. Install with: brew install yt-dlp") from err

    if result.returncode != 0:
        raise IngestError(f"Failed to fetch liked videos: {result.stderr.strip()}")

    return [line.strip() for line in result.stdout.strip().splitlines() if line.strip()]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/step_defs/test_backfill.py::test_fetch_liked_ids -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/yt_brain/infrastructure/ytdlp_adapter.py tests/step_defs/test_backfill.py
git commit -m "Add fetch_liked_ids to yt-dlp adapter"
```

---

### Task 4: Backfill Likes Service

**Files:**
- Modify: `src/yt_brain/application/backfill.py`
- Test: `tests/step_defs/test_backfill.py`

- [ ] **Step 1: Write the failing test**

Add to `tests/step_defs/test_backfill.py`:

```python
def test_backfill_likes_marks_liked_videos(temp_db):
    from yt_brain.application.backfill import backfill_likes
    from yt_brain.infrastructure.database import save_video

    # Create 3 videos in DB
    for vid_id in ["vid1", "vid2", "vid3"]:
        save_video(temp_db, Video(youtube_id=vid_id, title=f"V {vid_id}", channel_id="ch"))

    # yt-dlp says vid1 and vid3 are liked
    with patch("yt_brain.application.backfill.fetch_liked_ids", return_value=["vid1", "vid3", "vid_not_in_db"]):
        count = backfill_likes(temp_db, browser="chrome")

    assert count == 2

    import sqlite3
    conn = sqlite3.connect(temp_db)
    rows = {r[0]: r[1] for r in conn.execute("SELECT youtube_id, liked FROM videos WHERE youtube_id IN ('vid1','vid2','vid3')").fetchall()}
    conn.close()
    assert rows["vid1"] == "like"
    assert rows["vid2"] is None
    assert rows["vid3"] == "like"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/step_defs/test_backfill.py::test_backfill_likes_marks_liked_videos -v`
Expected: FAIL with `ImportError: cannot import name 'backfill_likes'`

- [ ] **Step 3: Implement `backfill_likes`**

Add to `src/yt_brain/application/backfill.py`:

First, update the imports at the top of the file (line 8) to add the new database functions:

```python
from yt_brain.infrastructure.database import (
    bulk_update_liked,
    get_all_video_ids,
    get_videos_missing_category,
    get_videos_missing_channel,
    get_videos_missing_description,
    get_videos_missing_watched_at,
    update_category,
    update_channel_id,
    update_description,
    update_watched_at,
)
```

Then add the function after `backfill_dates` (after line 156):

```python
def backfill_likes(db_path: Path, browser: str = "chrome") -> int:
    """Fetch liked video IDs via yt-dlp and mark them in the database.

    Returns the number of videos marked as liked.
    """
    from yt_brain.infrastructure.ytdlp_adapter import fetch_liked_ids

    liked_ids = set(fetch_liked_ids(browser=browser))
    all_ids = get_all_video_ids(db_path)
    matched = liked_ids & all_ids

    if matched:
        liked_map = {vid: "like" for vid in matched}
        bulk_update_liked(db_path, liked_map)

    return len(matched)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/step_defs/test_backfill.py::test_backfill_likes_marks_liked_videos -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/yt_brain/application/backfill.py tests/step_defs/test_backfill.py
git commit -m "Add backfill_likes service for syncing YouTube liked status"
```

---

### Task 5: Update `backfill_dates` to Populate `published_at`

**Files:**
- Modify: `src/yt_brain/application/backfill.py`
- Test: `tests/step_defs/test_backfill.py`

- [ ] **Step 1: Write the failing test**

Add to `tests/step_defs/test_backfill.py`:

```python
def test_backfill_dates_populates_published_at(temp_db):
    from yt_brain.application.backfill import backfill_dates
    from yt_brain.infrastructure.database import save_video

    v = Video(youtube_id="pub1", title="Pub Video", channel_id="ch")
    save_video(temp_db, v)

    import json
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps({
        "items": [{"id": "pub1", "snippet": {"publishedAt": "2024-03-15T12:00:00Z"}}]
    }).encode()
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = lambda s, *a: None

    with patch("yt_brain.application.backfill.urllib.request.urlopen", return_value=mock_resp):
        backfill_dates(temp_db, "test-key")

    import sqlite3
    conn = sqlite3.connect(temp_db)
    row = conn.execute("SELECT published_at FROM videos WHERE youtube_id = 'pub1'").fetchone()
    conn.close()
    assert row[0] == "2024-03-15T12:00:00Z"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/step_defs/test_backfill.py::test_backfill_dates_populates_published_at -v`
Expected: FAIL — `published_at` is `None` because `backfill_dates` doesn't write to it yet.

- [ ] **Step 3: Update `backfill_dates` to also set `published_at`**

In `src/yt_brain/application/backfill.py`, update the import block to include `update_published_at`:

```python
from yt_brain.infrastructure.database import (
    bulk_update_liked,
    get_all_video_ids,
    get_videos_missing_category,
    get_videos_missing_channel,
    get_videos_missing_description,
    get_videos_missing_watched_at,
    update_category,
    update_channel_id,
    update_description,
    update_published_at,
    update_watched_at,
)
```

Then in the `backfill_dates` function, after line 152 (`update_watched_at(db_path, item["id"], published)`), add:

```python
                    update_published_at(db_path, item["id"], published)
```

So lines 150-153 become:

```python
                published = item["snippet"].get("publishedAt", "")
                if published:
                    update_watched_at(db_path, item["id"], published)
                    update_published_at(db_path, item["id"], published)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/step_defs/test_backfill.py::test_backfill_dates_populates_published_at -v`
Expected: PASS

- [ ] **Step 5: Run all backfill tests to avoid regressions**

Run: `uv run pytest tests/step_defs/test_backfill.py -v`
Expected: All PASS

- [ ] **Step 6: Commit**

```bash
git add src/yt_brain/application/backfill.py tests/step_defs/test_backfill.py
git commit -m "Populate published_at alongside watched_at in backfill_dates"
```

---

### Task 6: CLI `backfill-likes` Command

**Files:**
- Modify: `src/yt_brain/cli.py`

- [ ] **Step 1: Add the CLI command**

Add after the `backfill_channels` command (after line 712) in `src/yt_brain/cli.py`:

```python
@app.command("backfill-likes")
def backfill_likes_cmd(
    browser: Annotated[str, typer.Option("--browser", "-b", help="Browser to read cookies from")] = "chrome",
) -> None:
    """Backfill liked video status from YouTube."""
    from yt_brain.application.backfill import backfill_likes

    db_path = _get_db_path()
    _ensure_db(db_path)

    console.print(f"[dim]Fetching liked videos from YouTube ({browser} cookies)...[/dim]")
    try:
        count = backfill_likes(db_path, browser=browser)
    except Exception as e:
        err_console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1) from None
    console.print(f"[green]Marked {count} videos as liked.[/green]")
```

- [ ] **Step 2: Verify the command shows in help**

Run: `uv run yt-brain --help`
Expected: `backfill-likes` appears in the command list.

- [ ] **Step 3: Commit**

```bash
git add src/yt_brain/cli.py
git commit -m "Add backfill-likes CLI command"
```

---

### Task 7: Add Liked Refresh to Sync Pipeline

**Files:**
- Modify: `src/yt_brain/application/sync.py`
- Test: `tests/step_defs/test_sync.py`

- [ ] **Step 1: Write the failing test**

Add to `tests/step_defs/test_sync.py` at the bottom:

```python
def test_sync_refreshes_liked_status(temp_db):
    from yt_brain.application.sync import sync_videos

    # Pre-populate a video
    save_video(temp_db, Video(youtube_id="vid1", title="V1", channel_id="ch"))

    entries = [{"id": "new1", "title": "New Video", "duration": 300}]

    with patch("yt_brain.application.sync.fetch_history_range", return_value=entries), \
         patch("yt_brain.application.sync.backfill_likes", return_value=1) as mock_likes:
        result = sync_videos(temp_db, batch_size=10)
        mock_likes.assert_called_once_with(temp_db, browser="chrome")

    assert result.likes_synced == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/step_defs/test_sync.py::test_sync_refreshes_liked_status -v`
Expected: FAIL — `backfill_likes` not imported in sync, `likes_synced` doesn't exist on `SyncResult`.

- [ ] **Step 3: Update `sync.py`**

In `src/yt_brain/application/sync.py`:

Update the import (line 7):

```python
from yt_brain.application.backfill import backfill_categories, backfill_channels, backfill_dates, backfill_likes
```

Add `likes_synced` to `SyncResult` (line 18, after `dates_backfilled`):

```python
@dataclass
class SyncResult:
    new_videos: int
    rewatched_videos: int
    channels_backfilled: int
    categories_backfilled: int
    dates_backfilled: int
    likes_synced: int
```

Add the liked refresh call after the existing backfill calls (after line 86), and add `browser` parameter passthrough:

```python
    likes_filled = backfill_likes(db_path, browser=browser)
```

Update the return statement (line 88-93) to include `likes_synced`:

```python
    return SyncResult(
        new_videos=len(all_new_ids),
        rewatched_videos=len(rewatched_ids),
        channels_backfilled=channels_filled,
        categories_backfilled=categories_filled,
        dates_backfilled=dates_filled,
        likes_synced=likes_filled,
    )
```

- [ ] **Step 4: Update CLI sync output to show likes**

In `src/yt_brain/cli.py`, in the `sync` command (around line 202), add after the dates backfilled line:

```python
        if result.likes_synced:
            console.print(f"  Likes synced: {result.likes_synced}")
```

- [ ] **Step 5: Run test to verify it passes**

Run: `uv run pytest tests/step_defs/test_sync.py::test_sync_refreshes_liked_status -v`
Expected: PASS

- [ ] **Step 6: Run all sync tests to avoid regressions**

Run: `uv run pytest tests/step_defs/test_sync.py -v`
Expected: All PASS (existing tests may need `likes_synced` added to assertions — check and fix if needed)

- [ ] **Step 7: Commit**

```bash
git add src/yt_brain/application/sync.py src/yt_brain/cli.py tests/step_defs/test_sync.py
git commit -m "Include liked-video refresh in sync pipeline"
```

---

### Task 8: Dashboard — Server-Side Data (Flask Route)

**Files:**
- Modify: `src/yt_brain/web/dashboard.py` (lines 1091-1223, the `index()` route)

- [ ] **Step 1: Add `liked` and `published_at` to the video dict**

In `src/yt_brain/web/dashboard.py`, in the `index()` route, update the video dict construction (around line 1126-1137). Each video dict currently builds from `videos_raw`. After `"cluster": cluster_slugs.get(v.youtube_id, ""),` add:

```python
                "liked": getattr(v, 'liked', None) or "",
                "published_at": getattr(v, 'published_at', None) or "",
```

Note: The `Video` model doesn't have `liked` or `published_at` fields yet, but `_row_to_video` uses `sqlite3.Row` which only reads defined fields. We need to read these directly from the raw query. The simplest approach is to read them from the DB alongside the existing query.

Actually, the cleanest approach: query liked/published_at separately as a dict lookup, similar to how `cluster_slugs` works.

Add after the `cluster_slugs` line (around line 1099):

```python
        # Load liked status and published dates for all videos
        import sqlite3 as _sqlite3
        _conn = _sqlite3.connect(config.db_path)
        try:
            _liked_map = {r[0]: r[1] for r in _conn.execute("SELECT youtube_id, liked FROM videos WHERE liked IS NOT NULL").fetchall()}
            _published_map = {r[0]: r[1] for r in _conn.execute("SELECT youtube_id, published_at FROM videos WHERE published_at IS NOT NULL").fetchall()}
        finally:
            _conn.close()
```

Then in the video dict (line 1136-1137 area), add:

```python
                "liked": _liked_map.get(v.youtube_id, ""),
                "published_at": _published_map.get(v.youtube_id, ""),
```

- [ ] **Step 2: Verify the dashboard still loads**

Run: `uv run yt-brain dashboard --port 5556 &` and open `http://127.0.0.1:5556` in a browser. Verify no errors. Kill the process.

- [ ] **Step 3: Commit**

```bash
git add src/yt_brain/web/dashboard.py
git commit -m "Pass liked and published_at data to dashboard template"
```

---

### Task 9: Dashboard — Table HTML (7 Columns)

**Files:**
- Modify: `src/yt_brain/web/dashboard.py` (lines 601-627, the table HTML in `TEMPLATE`)

- [ ] **Step 1: Update the colgroup and headers**

Replace the table HTML (lines 604-615) with:

```html
                <table id="videoTable">
                    <colgroup>
                        <col style="width:4%">
                        <col style="width:33%">
                        <col style="width:16%">
                        <col style="width:14%">
                        <col style="width:13%">
                        <col style="width:10%">
                        <col style="width:10%">
                    </colgroup>
                    <thead>
                        <tr>
                            <th colspan="7" style="padding-bottom:12px"><div class="search-wrap"><input type="text" id="semanticSearch" placeholder="{{ 'Search by topic, concept, or keyword...' if has_embeddings else 'Run yt-brain embed to enable semantic search' }}" {{ '' if has_embeddings else 'disabled' }} oninput="scheduleSemanticSearch()" class="search-input" style="width:100%"><span class="clear-btn" onclick="clearSearch()">&times;</span></div></th>
                        </tr>
                        <tr>
                            <th><span id="likedFilter" class="liked-btn" onclick="toggleLikedFilter()" title="Filter by liked status">&#x1F44D;</span></th>
                            <th class="sortable" data-sort="title" onclick="toggleSort('title')">Title</th>
                            <th class="sortable" data-sort="channel" onclick="toggleSort('channel')">Channel</th>
                            <th class="sortable" data-sort="genre" onclick="toggleSort('genre')">Genre</th>
                            <th class="sortable" data-sort="cluster" onclick="toggleSort('cluster')">Cluster</th>
                            <th class="sortable" data-sort="watched" onclick="toggleSort('watched')">Watched</th>
                            <th class="sortable" data-sort="published" onclick="toggleSort('published')">Published</th>
                        </tr>
                    </thead>
```

- [ ] **Step 2: Update the table body rows**

Replace the `<tr>` template (lines 618-624) with:

```html
                    {% for v in videos %}
                    <tr data-genre="{{ v.genre }}" data-watched="{{ v.watched_at }}" data-id="{{ v.id }}" data-cluster="{{ v.cluster }}" data-liked="{{ v.liked }}" data-published="{{ v.published_at }}">
                        <td class="liked-cell">{% if v.liked == 'like' %}<span class="liked-icon liked">&#x1F44D;</span>{% elif v.liked == 'dislike' %}<span class="liked-icon disliked">&#x1F44E;</span>{% endif %}</td>
                        <td><a href="https://www.youtube.com/watch?v={{ v.id }}" target="_blank" class="link-title">{{ v.title }}</a></td>
                        <td class="channel"><a href="{{ v.channel_url or 'https://www.youtube.com/results?search_query=' + v.channel|urlencode }}" target="_blank" class="link-channel">{{ v.channel[:20] }}</a></td>
                        <td><span class="genre-badge" style="background:{{ genre_colors.get(v.genre, '#333') }}22;color:{{ genre_colors.get(v.genre, '#888') }}">{{ v.genre }}</span></td>
                        <td>{% if v.cluster %}<a href="#" class="link-cluster" onclick="filterByCluster('{{ v.cluster }}'); return false;">{{ v.cluster }}</a>{% endif %}</td>
                        <td class="date-cell">{{ v.watched_at[:10] if v.watched_at else '' }}</td>
                        <td class="date-cell">{{ v.published_at[:10] if v.published_at else '' }}</td>
                    </tr>
                    {% endfor %}
```

- [ ] **Step 3: Verify the dashboard renders the new columns**

Run: `uv run yt-brain dashboard --port 5556 &` and check the table has 7 columns. Kill the process.

- [ ] **Step 4: Commit**

```bash
git add src/yt_brain/web/dashboard.py
git commit -m "Expand All Videos table to 7 columns with liked/dates"
```

---

### Task 10: Dashboard — CSS for New Columns and Sort Indicators

**Files:**
- Modify: `src/yt_brain/web/dashboard.py` (CSS section in `TEMPLATE`, around lines 42-480)

- [ ] **Step 1: Add CSS rules**

Add these CSS rules inside the `<style>` block, after the existing `#videoTable` styles (around line 320):

```css
        /* Sortable headers */
        .sortable {
            cursor: pointer;
            user-select: none;
            position: relative;
        }
        .sortable:hover {
            color: var(--text-primary);
        }
        .sortable::after {
            content: '';
            margin-left: 4px;
            color: var(--text-muted);
            font-size: 10px;
        }
        .sortable.sort-asc::after {
            content: '▲';
            color: var(--accent);
        }
        .sortable.sort-desc::after {
            content: '▼';
            color: var(--accent);
        }

        /* Liked column */
        .liked-cell {
            text-align: center;
            font-size: 14px;
        }
        .liked-icon {
            opacity: 0.3;
        }
        .liked-icon.liked {
            opacity: 1;
        }
        .liked-icon.disliked {
            opacity: 1;
        }
        .liked-btn {
            cursor: pointer;
            opacity: 0.3;
            font-size: 14px;
            user-select: none;
        }
        .liked-btn.filter-like {
            opacity: 1;
        }
        .liked-btn.filter-dislike {
            opacity: 1;
        }

        /* Date columns */
        .date-cell {
            font-variant-numeric: tabular-nums;
            font-size: 12px;
            color: var(--text-tertiary);
        }
```

- [ ] **Step 2: Update the sticky header top offset**

The second header row (with column names) has `top: 45px` for sticky positioning. Since we haven't changed the search row height, this should remain the same. Verify visually.

- [ ] **Step 3: Commit**

```bash
git add src/yt_brain/web/dashboard.py
git commit -m "Add CSS for sort indicators, liked icons, and date columns"
```

---

### Task 11: Dashboard — JavaScript Sort Logic

**Files:**
- Modify: `src/yt_brain/web/dashboard.py` (JS section in `TEMPLATE`)

- [ ] **Step 1: Update the videoData cache**

In the `videoData` construction (lines 648-657), update to include new fields:

```javascript
        const videoData = Array.from(videoRows).map((row, idx) => ({
            row,
            originalIndex: idx,
            id: row.dataset.id,
            genre: row.dataset.genre,
            cluster: row.dataset.cluster || '',
            liked: row.dataset.liked || '',
            watchedTs: row.dataset.watched ? new Date(row.dataset.watched).getTime() : null,
            watched: row.dataset.watched || '',
            published: row.dataset.published || '',
            publishedTs: row.dataset.published ? new Date(row.dataset.published).getTime() : null,
            title: (row.children[1]?.textContent || '').toLowerCase(),
            channel: row.children[2]?.textContent || '',
            channelLower: (row.children[2]?.textContent || '').toLowerCase(),
        }));
```

Note the index shift: `children[0]` is now the liked cell, `children[1]` is title, `children[2]` is channel.

- [ ] **Step 2: Add sort state and toggle function**

Add after the `let starFilterActive = false;` line (line 644):

```javascript
        let sortColumn = null;
        let sortDirection = null;
        let likedFilterState = null;

        function toggleSort(column) {
            if (sortColumn === column) {
                if (sortDirection === 'asc') sortDirection = 'desc';
                else if (sortDirection === 'desc') { sortDirection = null; sortColumn = null; }
            } else {
                sortColumn = column;
                sortDirection = 'asc';
            }

            // Update header indicators
            document.querySelectorAll('.sortable').forEach(th => {
                th.classList.remove('sort-asc', 'sort-desc');
            });
            if (sortColumn && sortDirection) {
                const activeTh = document.querySelector(`.sortable[data-sort="${sortColumn}"]`);
                if (activeTh) activeTh.classList.add('sort-' + sortDirection);
            }

            applySortAndFilters();
        }

        function applySortAndFilters() {
            const tbody = document.querySelector('#videoTable tbody');

            if (sortColumn && sortDirection) {
                const dir = sortDirection === 'asc' ? 1 : -1;
                videoData.sort((a, b) => {
                    let va, vb;
                    if (sortColumn === 'title') { va = a.title; vb = b.title; }
                    else if (sortColumn === 'channel') { va = a.channelLower; vb = b.channelLower; }
                    else if (sortColumn === 'genre') { va = a.genre.toLowerCase(); vb = b.genre.toLowerCase(); }
                    else if (sortColumn === 'cluster') { va = a.cluster.toLowerCase(); vb = b.cluster.toLowerCase(); }
                    else if (sortColumn === 'watched') { va = a.watched; vb = b.watched; }
                    else if (sortColumn === 'published') { va = a.published; vb = b.published; }
                    else return 0;

                    // Empty values sort last regardless of direction
                    if (!va && !vb) return 0;
                    if (!va) return 1;
                    if (!vb) return -1;
                    if (va < vb) return -dir;
                    if (va > vb) return dir;
                    return 0;
                });
            } else {
                videoData.sort((a, b) => a.originalIndex - b.originalIndex);
            }

            const frag = document.createDocumentFragment();
            for (const v of videoData) frag.appendChild(v.row);
            tbody.appendChild(frag);

            applyFilters();
        }

        function toggleLikedFilter() {
            const btn = document.getElementById('likedFilter');
            if (likedFilterState === null) {
                likedFilterState = 'like';
                btn.classList.add('filter-like');
                btn.classList.remove('filter-dislike');
                btn.innerHTML = '&#x1F44D;';
            } else if (likedFilterState === 'like') {
                likedFilterState = 'dislike';
                btn.classList.remove('filter-like');
                btn.classList.add('filter-dislike');
                btn.innerHTML = '&#x1F44E;';
            } else {
                likedFilterState = null;
                btn.classList.remove('filter-like', 'filter-dislike');
                btn.innerHTML = '&#x1F44D;';
            }
            applyFilters();
        }
```

- [ ] **Step 3: Add liked filter condition to `applyFilters()`**

In the `applyFilters()` function (around line 938), after the `starOk` line, add:

```javascript
                const likedOk = likedFilterState === null || v.liked === likedFilterState;
```

And update the `passesNonGenre` line to include it:

```javascript
                const passesNonGenre = dateOk && searchOk && starOk && likedOk;
```

- [ ] **Step 4: Verify sort and filter work in browser**

Run: `uv run yt-brain dashboard --port 5556 &`
- Click "Title" header — rows sort A-Z, arrow shows ▲
- Click "Title" again — rows sort Z-A, arrow shows ▼
- Click "Title" again — sort clears, original order restored
- Click "Watched" — sorts by date ascending
- Click the 👍 filter — only liked videos show
- Click again — only disliked videos show
- Click again — filter off

Kill the process.

- [ ] **Step 5: Commit**

```bash
git add src/yt_brain/web/dashboard.py
git commit -m "Add client-side column sorting and liked filter to All Videos table"
```

---

### Task 12: Run Backfill on Live Database

This task populates the live database with liked and published_at data.

- [ ] **Step 1: Apply migration to live DB**

Run: `uv run yt-brain status`
This triggers `init_db` which auto-applies migration 007.

- [ ] **Step 2: Backfill liked status**

Run: `uv run yt-brain backfill-likes`
Expected: `Marked N videos as liked.`

- [ ] **Step 3: Backfill published dates** (for videos missing published_at)

Run: `uv run yt-brain backfill-dates`
This will now populate `published_at` alongside `watched_at` for videos missing dates.

For videos that already have `watched_at` but not `published_at`, we need a one-time script. Run:

```bash
uv run python -c "
from yt_brain.infrastructure.config import load_config
from yt_brain.infrastructure.database import init_db
import sqlite3, json, urllib.request

config = load_config()
init_db(config.db_path)
conn = sqlite3.connect(config.db_path)
ids = [r[0] for r in conn.execute('SELECT youtube_id FROM videos WHERE published_at IS NULL').fetchall()]
print(f'{len(ids)} videos missing published_at')

filled = 0
for i in range(0, len(ids), 50):
    batch = ids[i:i+50]
    try:
        url = f'https://www.googleapis.com/youtube/v3/videos?part=snippet&id={\",\".join(batch)}&key={config.youtube_api_key}'
        resp = urllib.request.urlopen(url, timeout=15)
        data = json.loads(resp.read())
        for item in data.get('items', []):
            pub = item['snippet'].get('publishedAt', '')
            if pub:
                conn.execute('UPDATE videos SET published_at = ? WHERE youtube_id = ?', (pub, item['id']))
                filled += 1
    except Exception as e:
        print(f'  Error: {e}')
    if (i + 50) % 500 == 0:
        print(f'  {i+50}/{len(ids)}')
conn.commit()
conn.close()
print(f'Backfilled {filled} published dates')
"
```

- [ ] **Step 4: Verify in dashboard**

Run: `uv run yt-brain dashboard --port 5556 &`
Verify:
- Liked videos show 👍 icons
- Watched and Published date columns are populated
- Sorting works on all columns
- Liked filter works

Kill the process.

- [ ] **Step 5: Commit (no code changes, just verification)**

No commit needed for this task.

---

### Task 13: Run Full Test Suite

- [ ] **Step 1: Run all tests**

Run: `uv run pytest tests/ -v --ignore=tests/web`
Expected: All PASS

- [ ] **Step 2: Run web layout tests if available**

Run: `uv run pytest tests/web/ -v` (requires Playwright — skip if not set up)
Expected: All PASS or skip gracefully

- [ ] **Step 3: Final commit if any fixups were needed**

```bash
git add -A
git commit -m "Fix test regressions from table sorting feature"
```
(Only if there were changes to commit.)
