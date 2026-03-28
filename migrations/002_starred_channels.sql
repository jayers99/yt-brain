CREATE TABLE IF NOT EXISTS starred_channels (
    channel_name TEXT PRIMARY KEY,
    starred_at TEXT NOT NULL DEFAULT (datetime('now'))
);

INSERT OR IGNORE INTO schema_version (version) VALUES (2);
