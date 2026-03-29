CREATE TABLE IF NOT EXISTS video_clusters (
    cluster_id INTEGER PRIMARY KEY AUTOINCREMENT,
    slug TEXT UNIQUE NOT NULL,
    centroid BLOB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

ALTER TABLE videos ADD COLUMN cluster_id INTEGER REFERENCES video_clusters(cluster_id);

INSERT INTO schema_version (version) VALUES (5);
