# Semantic Video Clustering Design

**Date:** 2026-03-29
**Backlog item:** #2 `embed-and-cluster`
**Status:** Approved

## Purpose

Auto-cluster videos by topic using existing 384-dim embeddings (all-MiniLM-L6-v2, sqlite-vec). Adds a clickable cluster label to the All Videos dashboard table for content organization and browsing.

## Data Model

### New table: `video_clusters`

| Column       | Type          | Purpose                                  |
|--------------|---------------|------------------------------------------|
| `cluster_id` | INTEGER PK    | Auto-increment                           |
| `slug`       | TEXT UNIQUE   | LLM-generated kebab-case label           |
| `centroid`   | BLOB          | 384-dim mean embedding for incremental assign |
| `created_at` | TIMESTAMP     | When cluster was created                 |

### Schema change: `videos` table

Add nullable column:
- `cluster_id` INTEGER, FK → `video_clusters.cluster_id`

New migration file (e.g., `005_video_clusters.sql`).

## Clustering Pipeline

### Algorithm: HDBSCAN

- Density-based clustering on existing embeddings from `video_embeddings`
- Configurable `min_cluster_size` parameter (default 5)
- Videos classified as noise (label -1) remain unassigned (`cluster_id = NULL`)

### Slug Generation: Claude API

For each cluster:
1. Collect top ~10 video titles (closest to centroid)
2. Send to Claude API with prompt to generate a short, descriptive label
3. Slugify the label to kebab-case
4. On slug collision, append `-2`, `-3`, etc.
5. On API failure, fall back to `cluster-01`, `cluster-02` numeric slugs

Anthropic API key stored in `config.yaml` alongside existing YouTube API key.

### Modes

**Incremental (default):**
- Assigns new/unassigned videos to nearest existing cluster by cosine distance to centroid
- If cosine distance to nearest centroid exceeds 0.5, video remains unassigned (tunable constant)
- No re-clustering, no new slug generation

**Full rebuild (`--rebuild`):**
- Reclusters all embedded videos from scratch
- Recomputes centroids, regenerates slugs via Claude API
- Replaces all cluster assignments

### Pipeline steps (full rebuild)

1. Load all embeddings from `video_embeddings`
2. Run HDBSCAN with `min_cluster_size`
3. Compute centroid (mean embedding) per cluster
4. Generate slugs via Claude API
5. Write `video_clusters` rows and update `videos.cluster_id`

## CLI Commands

```
yt-brain cluster [--rebuild] [--min-cluster-size 5]   # Run clustering
yt-brain cluster list                                   # Show clusters with video counts
yt-brain cluster rename <old-slug> <new-slug>          # Manual rename
```

### Behavior

- `yt-brain cluster` with no flags: incremental assign only
- `--rebuild`: full recluster from scratch
- `--min-cluster-size N`: HDBSCAN parameter, only applies with `--rebuild`
- Exits with message if no embeddings exist ("Run `yt-brain embed` first")
- Exits with message if fewer than 10 embedded videos

## Dashboard Changes

### All Videos table

- New "Cluster" column showing the cluster slug as a clickable text link
- Videos with no cluster show an empty cell
- Click behavior: populates the search bar with `cluster:<slug>` and filters the table

### Search filter

- Extend existing search parser to handle `cluster:<slug>` syntax
- Filters All Videos table to videos matching that cluster slug
- Works alongside existing filters (`title:`, `desc:`, `channel:`)

## Error Handling

| Scenario | Behavior |
|----------|----------|
| No embeddings | Exit with "Run `yt-brain embed` first" |
| <10 embedded videos | Exit with "Not enough videos to cluster" |
| Claude API failure | Fall back to numeric slugs (`cluster-01`, etc.) |
| Slug collision | Append `-2`, `-3` suffix |
| Noise videos (HDBSCAN) | `cluster_id = NULL`, empty column in dashboard |

## Dependencies

| Package | Purpose |
|---------|---------|
| `hdbscan` | Density-based clustering algorithm |
| `anthropic` | Claude API for slug generation |

## Architecture Placement

Following existing hexagonal architecture:

- `domain/` — Cluster model, assignment logic
- `application/cluster.py` — Clustering service (pipeline orchestration)
- `infrastructure/database.py` — Cluster table queries, migration
- `web/dashboard.py` — Cluster column, `cluster:` search filter
- `cli.py` — `cluster`, `cluster list`, `cluster rename` commands

## Testing

- **Unit tests:** centroid computation, incremental assignment, slug generation/collision, cosine distance threshold
- **BDD scenario:** "Given embedded videos, when I run cluster, then videos are grouped and slugs appear in dashboard"
- **Integration test:** `cluster:<slug>` search filter returns correct video set
