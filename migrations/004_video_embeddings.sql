-- This migration requires sqlite-vec extension to be loaded first.
-- It is applied specially by init_db, not via executescript.

CREATE VIRTUAL TABLE IF NOT EXISTS video_embeddings USING vec0(
    youtube_id TEXT PRIMARY KEY,
    embedding FLOAT[384]
);

INSERT INTO schema_version (version) VALUES (4);
