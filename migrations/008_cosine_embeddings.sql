-- Recreate video_embeddings with cosine distance metric.
-- Requires: yt-brain embed --rebuild after migration.

DROP TABLE IF EXISTS video_embeddings;

CREATE VIRTUAL TABLE IF NOT EXISTS video_embeddings USING vec0(
    youtube_id TEXT PRIMARY KEY,
    embedding FLOAT[384] distance_metric=cosine
);

INSERT INTO schema_version (version) VALUES (8);
