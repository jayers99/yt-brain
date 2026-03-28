Feature: Google Takeout Ingestion
  Parse YouTube history from Google Takeout exports.

  Scenario: Parse watch history JSON
    Given a Takeout watch-history.json with 3 entries
    When I parse the takeout file
    Then I get 3 videos
    And each video has a youtube_id
    And each video has source "takeout"

  Scenario: Parse watch history with duration data
    Given a Takeout entry for video "dQw4w9WgXcQ" watched for 180 of 212 seconds
    When I parse the takeout file
    Then the video has watched_seconds 180
    And the video has duration_seconds 212

  Scenario: Skip ads and non-video entries
    Given a Takeout watch-history.json with 2 videos and 1 ad
    When I parse the takeout file
    Then I get 2 videos

  Scenario: Parse liked videos JSON
    Given a Takeout like list with 2 entries
    When I parse the liked videos file
    Then I get 2 liked video IDs
