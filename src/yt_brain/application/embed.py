from __future__ import annotations

import struct
from pathlib import Path

from yt_brain.infrastructure.database import (
    get_videos_for_embedding,
    insert_embeddings,
)

MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDING_DIM = 384
BATCH_SIZE = 256


def _to_blob(embedding: list[float]) -> bytes:
    """Serialize a float list to bytes for sqlite-vec."""
    return struct.pack(f"{len(embedding)}f", *embedding)


def embed_videos(
    db_path: Path,
    rebuild: bool = False,
    on_progress: callable | None = None,
) -> int:
    """Generate embeddings for videos and store in sqlite-vec.

    Returns the number of videos embedded.
    """
    from sentence_transformers import SentenceTransformer

    videos = get_videos_for_embedding(db_path, rebuild=rebuild)
    if not videos:
        return 0

    model = SentenceTransformer(MODEL_NAME)

    total = len(videos)
    embedded = 0

    for i in range(0, total, BATCH_SIZE):
        batch = videos[i : i + BATCH_SIZE]
        texts = [f"{title}\n{desc}" for _, title, desc in batch]
        ids = [vid_id for vid_id, _, _ in batch]

        embeddings = model.encode(texts, show_progress_bar=False)

        rows = [(vid_id, _to_blob(emb.tolist())) for vid_id, emb in zip(ids, embeddings)]
        insert_embeddings(db_path, rows)

        embedded += len(batch)
        if on_progress:
            on_progress(embedded, total)

    return embedded
