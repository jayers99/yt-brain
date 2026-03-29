# Semantic Video Clustering Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Auto-cluster videos by topic using HDBSCAN on existing embeddings, with Claude API-generated slugs and a clickable cluster column in the dashboard.

**Architecture:** New `video_clusters` table + `cluster_id` FK on `videos`. Clustering pipeline in `application/cluster.py` orchestrates HDBSCAN + slug generation. Dashboard gets a new column and `cluster:<slug>` search filter.

**Tech Stack:** hdbscan, anthropic (Claude API), numpy, sqlite-vec (existing), sentence-transformers (existing)

**Spec:** `docs/superpowers/specs/2026-03-29-semantic-video-clustering-design.md`

---

## File Map

| File | Action | Responsibility |
|------|--------|---------------|
| `migrations/005_video_clusters.sql` | Create | Cluster table + videos.cluster_id column |
| `src/yt_brain/domain/models.py` | Modify | Add Cluster model |
| `src/yt_brain/infrastructure/database.py` | Modify | Cluster CRUD functions |
| `src/yt_brain/application/cluster.py` | Create | HDBSCAN pipeline, slug generation, incremental assign |
| `src/yt_brain/cli.py` | Modify | `cluster`, `cluster list`, `cluster rename` commands |
| `src/yt_brain/web/dashboard.py` | Modify | Cluster column, `cluster:` filter, data plumbing |
| `tests/step_defs/test_cluster.py` | Create | Unit + integration tests |
| `tests/features/cluster.feature` | Create | BDD scenarios |
| `pyproject.toml` | Modify | Add hdbscan, anthropic, numpy dependencies |

---

### Task 1: Add Dependencies

**Files:**
- Modify: `pyproject.toml:9-17`

- [ ] **Step 1: Add hdbscan, anthropic, and numpy to dependencies**

In `pyproject.toml`, add to the `dependencies` array:

```toml
dependencies = [
    "typer>=0.15.1",
    "rich>=13.9.4",
    "pydantic>=2.10.4",
    "pyyaml>=6.0.2",
    "flask>=3.1.3",
    "sentence-transformers>=3.4.1",
    "sqlite-vec>=0.1.6",
    "hdbscan>=0.8.40",
    "anthropic>=0.42.0",
    "numpy>=1.26.0",
]
```

- [ ] **Step 2: Install dependencies**

Run: `uv sync`
Expected: Dependencies installed successfully

- [ ] **Step 3: Commit**

```bash
git add pyproject.toml uv.lock
git commit -m "Add hdbscan, anthropic, numpy dependencies for clustering"
```

---

### Task 2: Database Migration and Cluster CRUD

**Files:**
- Create: `migrations/005_video_clusters.sql`
- Modify: `src/yt_brain/infrastructure/database.py:22` (add 5 to `_VEC_MIGRATIONS`)
- Modify: `src/yt_brain/infrastructure/database.py:382+` (new functions)
- Modify: `src/yt_brain/domain/models.py:56+` (Cluster model)
- Create: `tests/step_defs/test_cluster.py`

- [ ] **Step 1: Write the failing test for cluster storage**

Create `tests/step_defs/test_cluster.py`:

```python
import struct
from pathlib import Path

import pytest

from yt_brain.infrastructure.database import (
    init_db,
    save_video,
    save_cluster,
    get_cluster_by_slug,
    assign_video_to_cluster,
    get_clusters_with_counts,
    get_video_cluster_slug,
)
from yt_brain.domain.models import Cluster, EngagementLevel, Source, Video


def _make_video(youtube_id: str, title: str = "Test", channel: str = "ch") -> Video:
    return Video(
        youtube_id=youtube_id,
        title=title,
        channel_id=channel,
        engagement_level=EngagementLevel.UNKNOWN,
        source=Source.MANUAL,
    )


def _fake_centroid() -> bytes:
    return struct.pack("384f", *([0.0] * 384))


def test_save_and_get_cluster(temp_db: Path) -> None:
    cluster = Cluster(slug="agentic-dev", centroid=_fake_centroid())
    cluster_id = save_cluster(temp_db, cluster)
    assert cluster_id > 0

    fetched = get_cluster_by_slug(temp_db, "agentic-dev")
    assert fetched is not None
    assert fetched.slug == "agentic-dev"
    assert fetched.cluster_id == cluster_id


def test_assign_video_to_cluster(temp_db: Path) -> None:
    save_video(temp_db, _make_video("vid1", title="Building agents"))
    cluster = Cluster(slug="agentic-dev", centroid=_fake_centroid())
    cluster_id = save_cluster(temp_db, cluster)

    assign_video_to_cluster(temp_db, "vid1", cluster_id)

    slug = get_video_cluster_slug(temp_db, "vid1")
    assert slug == "agentic-dev"


def test_get_clusters_with_counts(temp_db: Path) -> None:
    cluster = Cluster(slug="agentic-dev", centroid=_fake_centroid())
    cluster_id = save_cluster(temp_db, cluster)

    for i in range(3):
        save_video(temp_db, _make_video(f"vid{i}", title=f"Agent video {i}"))
        assign_video_to_cluster(temp_db, f"vid{i}", cluster_id)

    clusters = get_clusters_with_counts(temp_db)
    assert len(clusters) == 1
    assert clusters[0]["slug"] == "agentic-dev"
    assert clusters[0]["count"] == 3


def test_video_with_no_cluster_returns_none(temp_db: Path) -> None:
    save_video(temp_db, _make_video("vid1"))
    slug = get_video_cluster_slug(temp_db, "vid1")
    assert slug is None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/step_defs/test_cluster.py -v`
Expected: FAIL — `ImportError: cannot import name 'save_cluster'`

- [ ] **Step 3: Create the migration**

Create `migrations/005_video_clusters.sql`:

```sql
CREATE TABLE IF NOT EXISTS video_clusters (
    cluster_id INTEGER PRIMARY KEY AUTOINCREMENT,
    slug TEXT UNIQUE NOT NULL,
    centroid BLOB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

ALTER TABLE videos ADD COLUMN cluster_id INTEGER REFERENCES video_clusters(cluster_id);

INSERT INTO schema_version (version) VALUES (5);
```

- [ ] **Step 4: Add Cluster model**

In `src/yt_brain/domain/models.py`, after the `Video` class (after line 56), add:

```python
class Cluster(BaseModel):
    cluster_id: int | None = None
    slug: str
    centroid: bytes
```

- [ ] **Step 5: Implement cluster database functions**

In `src/yt_brain/infrastructure/database.py`:

Update `_VEC_MIGRATIONS` on line 22:

```python
_VEC_MIGRATIONS = {4, 5}
```

Add these imports to the existing import of `Cluster` from models (update the import on line 9):

```python
from yt_brain.domain.models import Cluster, EngagementLevel, Source, Video
```

After `get_embedding_count` (after line 381), add:

```python
def save_cluster(db_path: Path, cluster: Cluster) -> int:
    """Insert a cluster and return its cluster_id."""
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.execute(
            "INSERT INTO video_clusters (slug, centroid) VALUES (?, ?)",
            (cluster.slug, cluster.centroid),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def get_cluster_by_slug(db_path: Path, slug: str) -> Cluster | None:
    conn = sqlite3.connect(db_path)
    try:
        row = conn.execute(
            "SELECT cluster_id, slug, centroid FROM video_clusters WHERE slug = ?",
            (slug,),
        ).fetchone()
        if row is None:
            return None
        return Cluster(cluster_id=row[0], slug=row[1], centroid=row[2])
    finally:
        conn.close()


def assign_video_to_cluster(db_path: Path, youtube_id: str, cluster_id: int) -> None:
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            "UPDATE videos SET cluster_id = ? WHERE youtube_id = ?",
            (cluster_id, youtube_id),
        )
        conn.commit()
    finally:
        conn.close()


def get_video_cluster_slug(db_path: Path, youtube_id: str) -> str | None:
    conn = sqlite3.connect(db_path)
    try:
        row = conn.execute(
            "SELECT vc.slug FROM videos v "
            "JOIN video_clusters vc ON v.cluster_id = vc.cluster_id "
            "WHERE v.youtube_id = ?",
            (youtube_id,),
        ).fetchone()
        return row[0] if row else None
    finally:
        conn.close()


def get_clusters_with_counts(db_path: Path) -> list[dict]:
    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute(
            "SELECT vc.slug, COUNT(v.youtube_id) as count "
            "FROM video_clusters vc "
            "LEFT JOIN videos v ON v.cluster_id = vc.cluster_id "
            "GROUP BY vc.cluster_id ORDER BY count DESC"
        ).fetchall()
        return [{"slug": row[0], "count": row[1]} for row in rows]
    finally:
        conn.close()


def rename_cluster(db_path: Path, old_slug: str, new_slug: str) -> bool:
    """Rename a cluster slug. Returns True if found and renamed."""
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.execute(
            "UPDATE video_clusters SET slug = ? WHERE slug = ?",
            (new_slug, old_slug),
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def delete_all_clusters(db_path: Path) -> None:
    """Remove all clusters and assignments (for rebuild)."""
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("UPDATE videos SET cluster_id = NULL")
        conn.execute("DELETE FROM video_clusters")
        conn.commit()
    finally:
        conn.close()


def get_all_embeddings(db_path: Path) -> list[tuple[str, bytes]]:
    """Return all (youtube_id, embedding) from video_embeddings."""
    conn = sqlite3.connect(db_path)
    _load_sqlite_vec(conn)
    try:
        rows = conn.execute(
            "SELECT youtube_id, embedding FROM video_embeddings"
        ).fetchall()
        return rows
    finally:
        conn.close()


def get_unassigned_video_ids(db_path: Path) -> list[str]:
    """Return youtube_ids of videos that have embeddings but no cluster."""
    conn = sqlite3.connect(db_path)
    _load_sqlite_vec(conn)
    try:
        rows = conn.execute(
            "SELECT ve.youtube_id FROM video_embeddings ve "
            "JOIN videos v ON v.youtube_id = ve.youtube_id "
            "WHERE v.cluster_id IS NULL"
        ).fetchall()
        return [r[0] for r in rows]
    finally:
        conn.close()


def get_embeddings_for_ids(db_path: Path, youtube_ids: list[str]) -> list[tuple[str, bytes]]:
    """Return (youtube_id, embedding) for specific video IDs."""
    if not youtube_ids:
        return []
    conn = sqlite3.connect(db_path)
    _load_sqlite_vec(conn)
    try:
        placeholders = ",".join("?" * len(youtube_ids))
        rows = conn.execute(
            f"SELECT youtube_id, embedding FROM video_embeddings WHERE youtube_id IN ({placeholders})",
            youtube_ids,
        ).fetchall()
        return rows
    finally:
        conn.close()


def bulk_assign_clusters(db_path: Path, assignments: list[tuple[str, int]]) -> None:
    """Bulk assign videos to clusters. assignments = [(youtube_id, cluster_id), ...]."""
    conn = sqlite3.connect(db_path)
    try:
        conn.executemany(
            "UPDATE videos SET cluster_id = ? WHERE youtube_id = ?",
            [(cid, vid) for vid, cid in assignments],
        )
        conn.commit()
    finally:
        conn.close()
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `uv run pytest tests/step_defs/test_cluster.py -v`
Expected: All 4 tests PASS

- [ ] **Step 7: Commit**

```bash
git add migrations/005_video_clusters.sql src/yt_brain/domain/models.py src/yt_brain/infrastructure/database.py tests/step_defs/test_cluster.py
git commit -m "Add video_clusters table, Cluster model, and CRUD functions"
```

---

### Task 3: Clustering Application Service (HDBSCAN + Slug Generation)

**Files:**
- Create: `src/yt_brain/application/cluster.py`
- Create: `tests/step_defs/test_cluster_service.py`

- [ ] **Step 1: Write failing tests for the clustering service**

Create `tests/step_defs/test_cluster_service.py`:

```python
import struct
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from yt_brain.application.cluster import (
    ASSIGNMENT_THRESHOLD,
    _blob_to_array,
    _compute_centroid,
    _generate_slug,
    _slugify,
    cluster_videos,
    assign_new_videos,
)
from yt_brain.domain.models import EngagementLevel, Source, Video
from yt_brain.infrastructure.database import (
    get_clusters_with_counts,
    get_video_cluster_slug,
    init_db,
    insert_embeddings,
    save_video,
)


def _to_blob(vec: list[float]) -> bytes:
    return struct.pack(f"{len(vec)}f", *vec)


def _make_video(db_path: Path, youtube_id: str, title: str, embedding: list[float]) -> None:
    save_video(db_path, Video(
        youtube_id=youtube_id,
        title=title,
        channel_id="ch",
        engagement_level=EngagementLevel.UNKNOWN,
        source=Source.MANUAL,
    ))
    insert_embeddings(db_path, [(youtube_id, _to_blob(embedding))])


def test_slugify() -> None:
    assert _slugify("Agentic Software Development") == "agentic-software-development"
    assert _slugify("Police Body Cam / Footage!") == "police-body-cam-footage"
    assert _slugify("  hello   world  ") == "hello-world"


def test_blob_to_array() -> None:
    vec = [1.0, 2.0, 3.0]
    blob = _to_blob(vec)
    result = _blob_to_array(blob, dim=3)
    np.testing.assert_array_almost_equal(result, vec)


def test_compute_centroid() -> None:
    vecs = np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]])
    centroid = _compute_centroid(vecs)
    np.testing.assert_array_almost_equal(centroid, [0.5, 0.5, 0.0])


@patch("yt_brain.application.cluster._call_claude_for_label")
def test_generate_slug_calls_claude(mock_claude: MagicMock) -> None:
    mock_claude.return_value = "Agentic Development"
    titles = ["Building AI agents", "LangChain tutorial", "Claude tool use"]
    slug = _generate_slug(titles, existing_slugs=set(), api_key="test-key")
    assert slug == "agentic-development"
    mock_claude.assert_called_once()


@patch("yt_brain.application.cluster._call_claude_for_label")
def test_generate_slug_deduplicates(mock_claude: MagicMock) -> None:
    mock_claude.return_value = "Agentic Development"
    titles = ["Building AI agents"]
    slug = _generate_slug(titles, existing_slugs={"agentic-development"}, api_key="test-key")
    assert slug == "agentic-development-2"


@patch("yt_brain.application.cluster._call_claude_for_label")
def test_generate_slug_fallback_on_api_error(mock_claude: MagicMock) -> None:
    mock_claude.side_effect = Exception("API error")
    titles = ["Building AI agents"]
    slug = _generate_slug(titles, existing_slugs=set(), api_key="test-key", fallback_index=3)
    assert slug == "cluster-03"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/step_defs/test_cluster_service.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'yt_brain.application.cluster'`

- [ ] **Step 3: Implement the clustering service**

Create `src/yt_brain/application/cluster.py`:

```python
from __future__ import annotations

import re
import struct
from pathlib import Path

import numpy as np

from yt_brain.application.embed import EMBEDDING_DIM
from yt_brain.infrastructure.database import (
    bulk_assign_clusters,
    delete_all_clusters,
    get_all_embeddings,
    get_clusters_with_counts,
    get_cluster_by_slug,
    get_embeddings_for_ids,
    get_unassigned_video_ids,
    save_cluster,
)
from yt_brain.domain.models import Cluster

ASSIGNMENT_THRESHOLD = 0.5  # Max cosine distance for incremental assignment
DEFAULT_MIN_CLUSTER_SIZE = 5


def _blob_to_array(blob: bytes, dim: int = EMBEDDING_DIM) -> np.ndarray:
    """Deserialize a sqlite-vec blob to a numpy array."""
    return np.array(struct.unpack(f"{dim}f", blob), dtype=np.float32)


def _array_to_blob(arr: np.ndarray) -> bytes:
    """Serialize a numpy array to a sqlite-vec blob."""
    return struct.pack(f"{len(arr)}f", *arr.tolist())


def _compute_centroid(vectors: np.ndarray) -> np.ndarray:
    """Compute the mean of a set of vectors."""
    return vectors.mean(axis=0)


def _cosine_distance(a: np.ndarray, b: np.ndarray) -> float:
    """Compute cosine distance between two vectors."""
    dot = np.dot(a, b)
    norm = np.linalg.norm(a) * np.linalg.norm(b)
    if norm == 0:
        return 1.0
    return 1.0 - dot / norm


def _slugify(text: str) -> str:
    """Convert a label to a kebab-case slug."""
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"[\s-]+", "-", text)
    return text.strip("-")


def _call_claude_for_label(titles: list[str], api_key: str) -> str:
    """Call Claude API to generate a short cluster label from video titles."""
    import anthropic

    client = anthropic.Anthropic(api_key=api_key)
    titles_text = "\n".join(f"- {t}" for t in titles[:10])
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=30,
        messages=[{
            "role": "user",
            "content": (
                f"These video titles belong to the same topic cluster:\n\n{titles_text}\n\n"
                "Reply with ONLY a short label (2-4 words) describing the topic. No punctuation, no explanation."
            ),
        }],
    )
    return message.content[0].text.strip()


def _generate_slug(
    titles: list[str],
    existing_slugs: set[str],
    api_key: str,
    fallback_index: int = 0,
) -> str:
    """Generate a unique slug for a cluster using Claude API with fallback."""
    try:
        label = _call_claude_for_label(titles, api_key)
        slug = _slugify(label)
    except Exception:
        slug = f"cluster-{fallback_index:02d}"

    if slug not in existing_slugs:
        return slug

    # Deduplicate
    i = 2
    while f"{slug}-{i}" in existing_slugs:
        i += 1
    return f"{slug}-{i}"


def cluster_videos(
    db_path: Path,
    api_key: str,
    min_cluster_size: int = DEFAULT_MIN_CLUSTER_SIZE,
    on_progress: callable | None = None,
) -> int:
    """Full rebuild: cluster all embedded videos with HDBSCAN.

    Returns the number of clusters created.
    """
    import hdbscan

    raw = get_all_embeddings(db_path)
    if len(raw) < 10:
        return 0

    ids = [r[0] for r in raw]
    vectors = np.array([_blob_to_array(r[1]) for r in raw])

    clusterer = hdbscan.HDBSCAN(min_cluster_size=min_cluster_size, metric="euclidean")
    labels = clusterer.fit_predict(vectors)

    delete_all_clusters(db_path)

    unique_labels = set(labels)
    unique_labels.discard(-1)  # Remove noise label

    existing_slugs: set[str] = set()
    label_to_cluster_id: dict[int, int] = {}

    for i, label in enumerate(sorted(unique_labels)):
        mask = labels == label
        cluster_vectors = vectors[mask]
        cluster_ids = [ids[j] for j in range(len(ids)) if labels[j] == label]

        centroid = _compute_centroid(cluster_vectors)

        # Get titles for slug generation
        from yt_brain.infrastructure.database import get_video

        # Get titles of videos closest to centroid
        distances = [_cosine_distance(vectors[j], centroid) for j in range(len(ids)) if labels[j] == label]
        sorted_indices = sorted(range(len(cluster_ids)), key=lambda k: distances[k])
        top_ids = [cluster_ids[k] for k in sorted_indices[:10]]
        top_titles = []
        for vid_id in top_ids:
            vid = get_video(db_path, vid_id)
            if vid:
                top_titles.append(vid.title)

        slug = _generate_slug(top_titles, existing_slugs, api_key, fallback_index=i + 1)
        existing_slugs.add(slug)

        cluster = Cluster(slug=slug, centroid=_array_to_blob(centroid))
        cluster_id = save_cluster(db_path, cluster)
        label_to_cluster_id[label] = cluster_id

        if on_progress:
            on_progress(i + 1, len(unique_labels))

    # Assign videos to clusters
    assignments = []
    for j, vid_id in enumerate(ids):
        if labels[j] != -1:
            assignments.append((vid_id, label_to_cluster_id[labels[j]]))
    bulk_assign_clusters(db_path, assignments)

    return len(unique_labels)


def assign_new_videos(db_path: Path) -> int:
    """Incremental: assign unassigned videos to nearest existing cluster.

    Returns the number of videos assigned.
    """
    clusters = get_clusters_with_counts(db_path)
    if not clusters:
        return 0

    unassigned_ids = get_unassigned_video_ids(db_path)
    if not unassigned_ids:
        return 0

    # Load cluster centroids
    cluster_data = []
    for c in clusters:
        cluster_obj = get_cluster_by_slug(db_path, c["slug"])
        if cluster_obj and cluster_obj.cluster_id is not None:
            centroid = _blob_to_array(cluster_obj.centroid)
            cluster_data.append((cluster_obj.cluster_id, centroid))

    if not cluster_data:
        return 0

    # Load embeddings for unassigned videos
    unassigned_embs = get_embeddings_for_ids(db_path, unassigned_ids)

    assignments = []
    for vid_id, emb_blob in unassigned_embs:
        vec = _blob_to_array(emb_blob)
        best_id = None
        best_dist = float("inf")
        for cluster_id, centroid in cluster_data:
            dist = _cosine_distance(vec, centroid)
            if dist < best_dist:
                best_dist = dist
                best_id = cluster_id
        if best_dist <= ASSIGNMENT_THRESHOLD and best_id is not None:
            assignments.append((vid_id, best_id))

    if assignments:
        bulk_assign_clusters(db_path, assignments)

    return len(assignments)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/step_defs/test_cluster_service.py -v`
Expected: All 6 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/yt_brain/application/cluster.py tests/step_defs/test_cluster_service.py
git commit -m "Add clustering service with HDBSCAN pipeline and Claude slug generation"
```

---

### Task 4: CLI Commands

**Files:**
- Modify: `src/yt_brain/cli.py:562+`

- [ ] **Step 1: Write failing test for CLI cluster command**

Add to `tests/step_defs/test_cluster.py`:

```python
from typer.testing import CliRunner
from yt_brain.cli import app as cli_app

runner = CliRunner()


def test_cluster_list_empty(temp_db: Path) -> None:
    result = runner.invoke(cli_app, ["cluster", "list"])
    assert result.exit_code == 0
    assert "No clusters" in result.stdout


def test_cluster_rename_not_found(temp_db: Path) -> None:
    result = runner.invoke(cli_app, ["cluster", "rename", "nonexistent", "new-name"])
    assert result.exit_code == 0
    assert "not found" in result.stdout.lower()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/step_defs/test_cluster.py::test_cluster_list_empty -v`
Expected: FAIL — no `cluster` command

- [ ] **Step 3: Implement CLI commands**

In `src/yt_brain/cli.py`, after the `embed` command (after line 562), add:

```python
# --- Cluster commands ---
cluster_app = typer.Typer(help="Manage video topic clusters.")
app.add_typer(cluster_app, name="cluster")


@cluster_app.callback(invoke_without_command=True)
def cluster_default(
    ctx: typer.Context,
    rebuild: Annotated[bool, typer.Option("--rebuild", help="Full recluster from scratch")] = False,
    min_cluster_size: Annotated[int, typer.Option("--min-cluster-size", help="Minimum videos per cluster")] = 5,
) -> None:
    """Run video clustering (incremental by default, --rebuild for full)."""
    if ctx.invoked_subcommand is not None:
        return

    from yt_brain.infrastructure.config import load_config
    from yt_brain.infrastructure.database import get_embedding_count

    db_path = _get_db_path()
    _ensure_db(db_path)

    emb_count = get_embedding_count(db_path)
    if emb_count == 0:
        console.print("[red]No embeddings found. Run: yt-brain embed[/red]")
        raise typer.Exit(1)

    if emb_count < 10:
        console.print("[red]Not enough videos to cluster (need at least 10 embeddings).[/red]")
        raise typer.Exit(1)

    config = load_config()
    api_key = config.data.get("anthropic_api_key", "")

    if rebuild:
        if not api_key:
            console.print("[yellow]No anthropic_api_key in config. Slugs will be numeric.[/yellow]")
            api_key = ""

        console.print(f"[dim]Clustering {emb_count} videos (min_cluster_size={min_cluster_size})...[/dim]")

        def on_progress(done: int, total: int) -> None:
            console.print(f"  [dim]Named {done}/{total} clusters[/dim]")

        from yt_brain.application.cluster import cluster_videos

        n = cluster_videos(db_path, api_key=api_key, min_cluster_size=min_cluster_size, on_progress=on_progress)
        console.print(f"[green]Created {n} clusters.[/green]")
    else:
        from yt_brain.application.cluster import assign_new_videos
        from yt_brain.infrastructure.database import get_clusters_with_counts

        clusters = get_clusters_with_counts(db_path)
        if not clusters:
            console.print("[yellow]No clusters exist yet. Run with --rebuild first.[/yellow]")
            raise typer.Exit(1)

        n = assign_new_videos(db_path)
        console.print(f"[green]Assigned {n} new videos to existing clusters.[/green]")


@cluster_app.command("list")
def cluster_list() -> None:
    """Show all clusters with video counts."""
    from yt_brain.infrastructure.database import get_clusters_with_counts

    db_path = _get_db_path()
    _ensure_db(db_path)

    clusters = get_clusters_with_counts(db_path)
    if not clusters:
        console.print("[dim]No clusters yet. Run: yt-brain cluster --rebuild[/dim]")
        return

    from rich.table import Table

    table = Table(title="Video Clusters")
    table.add_column("Slug", style="cyan")
    table.add_column("Videos", justify="right")
    for c in clusters:
        table.add_row(c["slug"], str(c["count"]))
    console.print(table)


@cluster_app.command("rename")
def cluster_rename(
    old_slug: Annotated[str, typer.Argument(help="Current cluster slug")],
    new_slug: Annotated[str, typer.Argument(help="New cluster slug")],
) -> None:
    """Rename a cluster slug."""
    from yt_brain.infrastructure.database import rename_cluster

    db_path = _get_db_path()
    _ensure_db(db_path)

    if rename_cluster(db_path, old_slug, new_slug):
        console.print(f"[green]Renamed '{old_slug}' → '{new_slug}'[/green]")
    else:
        console.print(f"[red]Cluster '{old_slug}' not found.[/red]")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/step_defs/test_cluster.py -v`
Expected: All 6 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/yt_brain/cli.py tests/step_defs/test_cluster.py
git commit -m "Add cluster CLI commands: cluster, cluster list, cluster rename"
```

---

### Task 5: Dashboard — Cluster Column and Search Filter

**Files:**
- Modify: `src/yt_brain/web/dashboard.py:508` (table headers)
- Modify: `src/yt_brain/web/dashboard.py:511-516` (table rows)
- Modify: `src/yt_brain/web/dashboard.py:499-502` (colgroup)
- Modify: `src/yt_brain/web/dashboard.py:540-548` (videoData JS)
- Modify: `src/yt_brain/web/dashboard.py:629-677` (applyFilters)
- Modify: `src/yt_brain/web/dashboard.py:778-797` (video dict)
- Modify: `src/yt_brain/web/dashboard.py:857-874` (render_template_string)
- Modify: `src/yt_brain/web/dashboard.py:903-974` (search endpoint)

- [ ] **Step 1: Add cluster data to the video dict in the index route**

In `src/yt_brain/web/dashboard.py`, in the `index()` route, after `channel_urls = get_channel_urls(config.db_path)` (line 776), add:

```python
        # Load cluster slugs for all videos
        cluster_slugs = get_all_video_cluster_slugs(config.db_path)
```

Add `get_all_video_cluster_slugs` to the imports from database at the top of `create_app` or in the function.

In the video dict construction (line 787-797), add the cluster slug:

```python
            videos.append({
                "id": v.youtube_id,
                "title": v.title,
                "channel": v.channel_id,
                "genre": v.category or classify_genre(v.title),
                "duration": v.duration_seconds,
                "duration_fmt": dur_fmt,
                "engagement": v.effective_engagement.value,
                "watched_at": v.watched_at.isoformat() if v.watched_at else "",
                "channel_url": channel_urls.get(v.channel_id, ""),
                "cluster": cluster_slugs.get(v.youtube_id, ""),
            })
```

- [ ] **Step 2: Add the `get_all_video_cluster_slugs` database function**

In `src/yt_brain/infrastructure/database.py`, add after `bulk_assign_clusters`:

```python
def get_all_video_cluster_slugs(db_path: Path) -> dict[str, str]:
    """Return {youtube_id: cluster_slug} for all videos with a cluster."""
    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute(
            "SELECT v.youtube_id, vc.slug FROM videos v "
            "JOIN video_clusters vc ON v.cluster_id = vc.cluster_id "
            "WHERE v.cluster_id IS NOT NULL"
        ).fetchall()
        return {r[0]: r[1] for r in rows}
    finally:
        conn.close()
```

- [ ] **Step 3: Update the table HTML — colgroup, headers, rows**

In `dashboard.py`, update the colgroup (lines 499-502):

```html
                    <colgroup>
                        <col style="width:45%">
                        <col style="width:20%">
                        <col style="width:20%">
                        <col style="width:15%">
                    </colgroup>
```

Update the header row (line 508):

```html
                        <tr><th>Title</th><th>Channel</th><th>Genre</th><th>Cluster</th></tr>
```

Update the video row template (lines 512-516):

```html
                    {% for v in videos %}
                    <tr data-genre="{{ v.genre }}" data-watched="{{ v.watched_at }}" data-id="{{ v.id }}" data-cluster="{{ v.cluster }}">
                        <td><a href="https://www.youtube.com/watch?v={{ v.id }}" target="_blank" class="link-title">{{ v.title }}</a></td>
                        <td class="channel"><a href="{{ v.channel_url or 'https://www.youtube.com/results?search_query=' + v.channel|urlencode }}" target="_blank" class="link-channel">{{ v.channel[:20] }}</a></td>
                        <td><span class="genre-badge" style="background:{{ genre_colors.get(v.genre, '#333') }}22;color:{{ genre_colors.get(v.genre, '#888') }}">{{ v.genre }}</span></td>
                        <td>{% if v.cluster %}<a href="#" class="link-cluster" onclick="filterByCluster('{{ v.cluster }}'); return false;">{{ v.cluster }}</a>{% endif %}</td>
                    </tr>
                    {% endfor %}
```

- [ ] **Step 4: Update the videoData JS cache**

In the `<script>` section (lines 540-548), update the videoData map to include cluster:

```javascript
        const videoData = Array.from(videoRows).map(row => ({
            row,
            id: row.dataset.id,
            genre: row.dataset.genre,
            cluster: row.dataset.cluster || '',
            watchedTs: row.dataset.watched ? new Date(row.dataset.watched).getTime() : null,
            title: (row.children[0]?.textContent || '').toLowerCase(),
            channel: row.children[1]?.textContent || '',
            channelLower: (row.children[1]?.textContent || '').toLowerCase(),
        }));
```

- [ ] **Step 5: Add `filterByCluster` JS function and cluster filter in `applyFilters`**

After the `clearSearch()` function (after line 570), add:

```javascript
        function filterByCluster(slug) {
            semanticSearchEl.value = 'cluster:' + slug;
            // Set cluster filter directly instead of semantic search
            activeClusterFilter = slug;
            semanticMatchIds = null;
            applyFilters();
        }
```

Add a variable declaration near the other state variables (after `let semanticTimer = null;` on line 563):

```javascript
        let activeClusterFilter = null;
```

Update `scheduleSemanticSearch()` (lines 572-597) to detect `cluster:` prefix:

```javascript
        function scheduleSemanticSearch() {
            if (semanticTimer) clearTimeout(semanticTimer);
            const q = semanticSearchEl.value.trim();
            if (!q) {
                semanticMatchIds = null;
                activeClusterFilter = null;
                applyFilters();
                return;
            }
            // Check for cluster: filter
            const clusterMatch = q.match(/^cluster:(\S+)$/);
            if (clusterMatch) {
                activeClusterFilter = clusterMatch[1];
                semanticMatchIds = null;
                applyFilters();
                return;
            }
            activeClusterFilter = null;
            // Debounce 150ms for API call (model is preloaded)
            semanticTimer = setTimeout(() => {
                fetch('/api/search?q=' + encodeURIComponent(q) + '&limit=200')
                    .then(r => r.json())
                    .then(data => {
                        if (data.results && data.results.length > 0) {
                            semanticMatchIds = new Set(data.results.map(r => r.youtube_id));
                        } else {
                            semanticMatchIds = new Set();  // empty = nothing matches
                        }
                        applyFilters();
                    })
                    .catch(() => {
                        semanticMatchIds = null;
                        applyFilters();
                    });
            }, 300);
        }
```

Update `clearSearch()` to also clear the cluster filter:

```javascript
        function clearSearch() {
            semanticSearchEl.value = '';
            semanticSearchEl.focus();
            semanticMatchIds = null;
            activeClusterFilter = null;
            applyFilters();
        }
```

Update `applyFilters()` — in the filter loop (line 657), add the cluster check:

```javascript
                const searchOk = activeClusterFilter
                    ? v.cluster === activeClusterFilter
                    : (semanticMatchIds === null || semanticMatchIds.has(v.id));
```

This replaces the existing line 657:
```javascript
                const searchOk = semanticMatchIds === null || semanticMatchIds.has(v.id);
```

- [ ] **Step 6: Run the dashboard manually and verify**

Run: `uv run yt-brain dashboard`
Expected: Dashboard loads. All Videos table has a "Cluster" column. Column is empty (no clusters assigned yet). Search bar accepts `cluster:` prefix without triggering semantic search.

- [ ] **Step 7: Commit**

```bash
git add src/yt_brain/web/dashboard.py src/yt_brain/infrastructure/database.py
git commit -m "Add cluster column to dashboard with cluster: search filter"
```

---

### Task 6: BDD Scenario

**Files:**
- Create: `tests/features/cluster.feature`

- [ ] **Step 1: Write BDD feature file**

Create `tests/features/cluster.feature`:

```gherkin
Feature: Video clustering
  As a user
  I want videos grouped into topic clusters
  So I can browse related content together

  Scenario: Cluster list shows clusters after rebuild
    Given a database with embedded videos
    When I run clustering with rebuild
    Then I see clusters with video counts

  Scenario: Incremental assign adds new videos to clusters
    Given a database with existing clusters
    And a new embedded video similar to an existing cluster
    When I run incremental clustering
    Then the new video is assigned to the nearest cluster

  Scenario: Unrelated video stays unassigned
    Given a database with existing clusters
    And a new embedded video far from all clusters
    When I run incremental clustering
    Then the new video has no cluster
```

- [ ] **Step 2: Commit**

```bash
git add tests/features/cluster.feature
git commit -m "Add BDD scenarios for video clustering"
```

---

### Task 7: Update Backlog and CLAUDE.md

**Files:**
- Modify: `docs/backlog.md:6`
- Modify: `CLAUDE.md`

- [ ] **Step 1: Update backlog status**

In `docs/backlog.md`, change line 6:

```
| 2 | `embed-and-cluster` | Auto-cluster videos by topic using embeddings (Phase 2 vision) | **Complete** |
```

- [ ] **Step 2: Update CLAUDE.md with new commands**

In `CLAUDE.md`, add to the CLI Commands section:

```
yt-brain cluster [--rebuild] [--min-cluster-size 5]  # Run video clustering
yt-brain cluster list              # Show clusters with counts
yt-brain cluster rename <old> <new>  # Rename a cluster slug
```

Add to Key Files table:

```
| `src/yt_brain/application/cluster.py` | HDBSCAN clustering + Claude slug generation |
```

Add to Data section:

```
- Anthropic API key stored in config (for cluster slug generation)
- Cluster assignments in `video_clusters` table + `videos.cluster_id` FK
```

- [ ] **Step 3: Commit**

```bash
git add docs/backlog.md CLAUDE.md
git commit -m "Mark embed-and-cluster complete, update docs with clustering commands"
```
