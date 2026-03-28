Feature: Engagement Classification
  Classify videos by engagement signals.

  Scenario: Video watched less than 15% is bounced
    Given a video with duration 600 and watched 60
    When I classify the video
    Then the engagement level is "BOUNCED"

  Scenario: Video watched more than 85% is watched
    Given a video with duration 600 and watched 540
    When I classify the video
    Then the engagement level is "WATCHED"

  Scenario: Video between thresholds stays unknown
    Given a video with duration 600 and watched 300
    When I classify the video
    Then the engagement level is "UNKNOWN"

  Scenario: Liked video overrides watch time
    Given a video with duration 600 and watched 60
    And the video is liked
    When I classify the video
    Then the engagement level is "LIKED"

  Scenario: Curated video is highest tier
    Given a video with duration 600 and watched 60
    And the video is liked
    And the video is in a user playlist
    When I classify the video
    Then the engagement level is "CURATED"

  Scenario: No watch data stays unknown
    Given a video with no watch data
    When I classify the video
    Then the engagement level is "UNKNOWN"

  Scenario: Custom thresholds are respected
    Given a video with duration 600 and watched 180
    And the bounce threshold is 0.25
    When I classify the video
    Then the engagement level is "UNKNOWN"
