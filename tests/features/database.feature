Feature: Database Storage
  SQLite persistence for yt-brain.

  Scenario: Initialize database creates tables
    Given a fresh database
    Then the videos table exists
    And the channels table exists
    And the playlists table exists
    And the playlist_videos table exists
    And the schema_version is 1

  Scenario: Save and retrieve a video
    Given a fresh database
    And a video "abc123" titled "Test Video" from channel "ch1"
    When I save the video
    And I retrieve video "abc123"
    Then the retrieved video title is "Test Video"

  Scenario: Save duplicate video updates it
    Given a fresh database
    And a video "abc123" titled "Original" from channel "ch1"
    When I save the video
    And I save a video "abc123" titled "Updated" from channel "ch1"
    And I retrieve video "abc123"
    Then the retrieved video title is "Updated"

  Scenario: List videos by engagement level
    Given a fresh database
    And a saved video "v1" with engagement "BOUNCED"
    And a saved video "v2" with engagement "LIKED"
    And a saved video "v3" with engagement "LIKED"
    When I list videos with engagement "LIKED"
    Then I get 2 videos
