Feature: Review Workflow
  Review and override video classifications.

  Scenario: List videos for review by tier
    Given a database with classified videos:
      | youtube_id | title       | engagement |
      | v1         | Video One   | LIKED      |
      | v2         | Video Two   | LIKED      |
      | v3         | Video Three | WATCHED    |
    When I get review list for tier "LIKED"
    Then I get 2 videos for review

  Scenario: Override a video classification
    Given a database with a video "v1" classified as "WATCHED"
    When I override "v1" to "CURATED"
    And I retrieve video "v1" for review
    Then the effective engagement is "CURATED"
