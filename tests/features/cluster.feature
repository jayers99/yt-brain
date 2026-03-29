Feature: Video clustering
  As a user
  I want videos grouped into topic clusters
  So I can browse related content together

  Scenario: Cluster list shows clusters after rebuild
    Given a database with embedded videos
    When I run clustering with rebuild
    Then I see clusters with video counts

  Scenario: Incremental assign adds new videos to clusters
    Given a database with existing clusters
    And a new embedded video similar to an existing cluster
    When I run incremental clustering
    Then the new video is assigned to the nearest cluster

  Scenario: Unrelated video stays unassigned
    Given a database with existing clusters
    And a new embedded video far from all clusters
    When I run incremental clustering
    Then the new video has no cluster
