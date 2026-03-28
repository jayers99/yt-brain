Feature: Manual Video Ingestion
  Add videos by URL using yt-dlp for metadata.

  Scenario: Extract video ID from standard URL
    Given a YouTube URL "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    When I extract the video ID
    Then the ID is "dQw4w9WgXcQ"

  Scenario: Extract video ID from short URL
    Given a YouTube URL "https://youtu.be/dQw4w9WgXcQ"
    When I extract the video ID
    Then the ID is "dQw4w9WgXcQ"

  Scenario: Parse yt-dlp metadata JSON
    Given yt-dlp metadata JSON for video "abc123"
    When I parse the metadata
    Then the video title is "Test Title"
    And the video duration is 300
    And the video channel_id is "UCtest"
