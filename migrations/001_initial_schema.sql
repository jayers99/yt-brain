CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS channels (
    youtube_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    url TEXT NOT NULL DEFAULT '',
    subscription_status INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS videos (
    youtube_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    channel_id TEXT NOT NULL,
    duration_seconds INTEGER NOT NULL DEFAULT 0,
    watched_seconds INTEGER,
    watched_at TEXT,
    engagement_level TEXT NOT NULL DEFAULT 'UNKNOWN',
    engagement_override TEXT,
    transcript TEXT,
    tags TEXT NOT NULL DEFAULT '[]',
    source TEXT NOT NULL DEFAULT 'manual',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (channel_id) REFERENCES channels(youtube_id)
);

CREATE TABLE IF NOT EXISTS playlists (
    youtube_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    is_user_created INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS playlist_videos (
    playlist_id TEXT NOT NULL,
    video_id TEXT NOT NULL,
    position INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (playlist_id, video_id),
    FOREIGN KEY (playlist_id) REFERENCES playlists(youtube_id),
    FOREIGN KEY (video_id) REFERENCES videos(youtube_id)
);

INSERT INTO schema_version (version) VALUES (1);
