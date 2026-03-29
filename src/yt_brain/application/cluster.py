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
