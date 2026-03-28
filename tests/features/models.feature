Feature: Domain Models
  Core data models for yt-brain.

  Scenario: Create a video with engagement level
    Given a video with youtube_id "abc123" and duration 600
    When the video watched_seconds is 540
    Then the video engagement_level is "UNKNOWN"
    And the video source is "manual"

  Scenario: EngagementLevel ordering
    Then CURATED is higher than LIKED
    And LIKED is higher than WATCHED
    And WATCHED is higher than BOUNCED
    And BOUNCED is higher than UNKNOWN
