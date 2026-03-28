Feature: Status Dashboard
  Show counts and summary of video library.

  Scenario: Status with empty database
    Given an empty database
    When I get the status summary
    Then total videos is 0
    And all tier counts are 0

  Scenario: Status with classified videos
    Given a database with these videos:
      | youtube_id | engagement |
      | v1         | BOUNCED    |
      | v2         | WATCHED    |
      | v3         | LIKED      |
      | v4         | LIKED      |
      | v5         | CURATED    |
    When I get the status summary
    Then total videos is 5
    And BOUNCED count is 1
    And WATCHED count is 1
    And LIKED count is 2
    And CURATED count is 1
