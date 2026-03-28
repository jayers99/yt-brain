Feature: Sync watch history
  Keep the local database current by fetching new videos from YouTube
  history via yt-dlp and backfilling metadata.

  Scenario: Sync adds new videos not yet in database
    Given a database with existing videos "vid1" and "vid2"
    And yt-dlp returns videos "vid1", "vid2", "vid3", "vid4"
    When I run sync
    Then 2 new videos are saved to the database
    And the sync result shows 2 new videos

  Scenario: Sync stops when entire batch is already known
    Given a database with existing videos "vid1", "vid2", "vid3"
    And yt-dlp returns a batch of only known videos "vid1", "vid2", "vid3"
    When I run sync
    Then no new videos are saved
    And the sync result shows 0 new videos

  Scenario: Sync backfills metadata for new videos
    Given an empty database
    And yt-dlp returns videos "new1", "new2"
    And the YouTube API is available
    When I run sync with an API key
    Then 2 new videos are saved to the database
    And channels are backfilled for new videos
    And categories are backfilled for new videos
    And dates are backfilled for new videos
