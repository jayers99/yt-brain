ALTER TABLE videos ADD COLUMN category TEXT NOT NULL DEFAULT '';

INSERT OR IGNORE INTO schema_version (version) VALUES (3);
