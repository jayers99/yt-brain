ALTER TABLE video_clusters ADD COLUMN parent_category TEXT DEFAULT '';

INSERT INTO schema_version (version) VALUES (6);
