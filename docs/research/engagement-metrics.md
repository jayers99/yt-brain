# Technical Briefing: Personal YouTube Engagement Scoring System

This briefing establishes the architectural framework for a personal engagement scoring system. Ground truth for this document is derived from the **SocialBee 2026 Guide**, **Openbridge** technical documentation, and **InfluenceFlow** auditing standards.

## 1. YouTube Native Metrics: API and Internal Signals

YouTube utilizes a layered data architecture involving public endpoints, owner-restricted analytics, and internal satisfaction signals to rank content and predict viewer behavior.

| Metric Name | Definition/Formula | Availability Tier | Takeout Availability |
| :--- | :--- | :--- | :--- |
| **Watch Time** | Total accumulated time spent watching a video. | Owner-only Analytics API | **No** (Records video ID only) |
| **Average View Duration (AVD)** | Total Watch Time ÷ Total Views. | Owner-only Analytics API | **No** (Duration not recorded) |
| **Click-Through Rate (CTR)** | (Clicks ÷ Impressions) × 100. | Owner-only Analytics API | **No** |
| **Return Viewers** | Count of unique viewers with prior session history. | Owner-only Analytics API | **Partial** (Inferred from history) |
| **Subscribers Gained/Lost** | Net transaction log of sub-state per video. | Owner-only Analytics API | **No** (Subscriptions folder only lists *current* subs) |
| **Sentiment (Likes/Dislikes)** | Binary approval/disapproval signals. | Public Data API v3 | **Yes** (Interactions folder) |
| **Comments** | User-generated text strings. | Public Data API v3 | **Yes** (Now exported as **CSV**) |
| **Post-watch Surveys** | Direct "satisfaction" feedback prompts. | Internal Signal | **No** |
| **Session Patterns** | Analysis of viewer movement between videos. | Internal Signal | **No** |
| **Topic Durability** | Long-term relevance/decay rate of a topic. | Internal Signal | **No** |

**Architectural Note:** Per the source context, Google Takeout watch history records *that* a video was watched (event occurrence) but does *not* record the specific duration watched for each entry. A 10-second "bounce" and a full-length completion are indistinguishable in the raw Takeout logs.

## 2. Ecosystem Tool Analysis: Third-Party Composite Scores

Third-party tools utilize YouTube’s Public APIs to create proprietary benchmarks. As an architect, note that many of these rely on the 10-video rolling average as a primary baseline.

### vidIQ
*   **Overall Score (Keyword Score):** A proprietary balance of Search Volume vs. Competition. 
*   **Color-Coded Brackets:** Red (0-19: Very Low), Orange (20-39: Low), Yellow (40-59: Medium), Lime Green (60-79: High), and Green (80-100: Very High).

### TubeBuddy
*   **Retention Analysis:** Identifies drop-off points via API hooks.
*   **A/B Testing Engine:** Allows for comparative testing of **Thumbnails, Titles, and Descriptions** to isolate the highest CTR Attribution Signals.
*   **Click Magnet:** Aggregates content preferences to forecast high-performance topics.

### Social Blade
*   **Social Blade Rank:** A-C grading system based on reach and influence.
*   **Estimated Earnings:** Calculated via CPT (Cost Per Thousand) ranges ($0.25 to $4.00). **Warning:** These are rough estimates only; actual CPT is known only to the channel operator (IONOS/Social Blade).

### Morningfame
*   **Traction Benchmarking:** Compares Views, AVD, Likes, Comments, and Subs Gained against the channel’s specific **10-video average**.
*   **Velocity Indicators:** Determines if a video is "Speeding Up" or "Slowing Down" relative to the channel's historical baseline.

### Tubular Labs & InfluenceFlow
*   **Tubular Labs:** Measures "Engagements per Video" as the primary metric for fan loyalty, prioritizing "Culturally Relevant Content" (e.g., cuisine, music) over raw gaming/news highlights.
*   **InfluenceFlow (AER):** Establishes the **Authentic Engagement Rate (AER)**. This audits "bought" followers and bot activity by analyzing comment relevance/quality (SocialBee 2026 standards).

## 3. Cross-Cutting Engagement Taxonomy

Metrics are categorized into functional groups to weight their value within a scoring algorithm.

*   **Consumption Depth:** Includes AVD, total minutes watched, and the **Retention Curve**. (Source: SocialBee)
*   **Completion:** Includes Shorts "Completion Rate" and the **"Viewed vs. Swiped Away"** ratio. A 70% Viewed threshold is the industry benchmark for viral potential (Source: ReelRise).
*   **Virality:** High-weight signals including Views Velocity, Shares, and **"Sends"** (The latter being a top-three priority for modern unconnected reach).
*   **Recurrence:** Includes Return Viewers and Subscriber Gained status (at the channel level).
*   **Sentiment:** Evaluation of Like/Dislike ratios and comment-based sentiment analysis.
*   **Save-Intent:** The highest-intent category, including manual "Saves" and Playlist additions (e.g., "Watch Later").

## 4. Per-Viewer Derivability Matrix

For developers building a scoring engine using **Google Takeout (JSON)** and **Public Data API v3**, use the following matrix:

| Data Point | Derivability Status | Technical Note |
| :--- | :--- | :--- |
| **Watched Duration** | **Not Derivable** | Takeout only logs the timestamp of the "Watched" event. |
| **Bounce Signal** | **Partially Derivable** | Inferred via high view counts in Takeout with 0 corresponding likes, comments, or saves. |
| **Re-watch Count** | **Fully Derivable** | `COUNT(watch-history.json WHERE video_id == X)` |
| **Playlist Membership** | **Fully Derivable** | Extracted from the Takeout "Playlists" folder. |
| **Like Status** | **Fully Derivable** | Found in Takeout "Interactions" or via Data API `list.likedVideos`. |
| **Comment Status** | **Fully Derivable** | Exported as **CSV** files in the Takeout export. |

### Implementation Warning (Localization)
Parsing the `watch-history.json` requires **Regex or localized string mapping**. In German accounts, the file is `Wiedergabeverlauf.json` and the action string is `"Wiedergabeverlauf"` instead of `"Watched"`. Failure to map these strings will result in null returns during JSON traversal.

**Data Schema Reference:**
The `watch-history.json` object typically contains: `header` (Platform), `title` (Video Title), `titleUrl` (Video ID/URL), and `time` (ISO 8601).

## 5. Recommended Starter Metric Set for MVP Scoring

To build an MVP personal score, utilize these 7 specific signals.

1.  **Re-watch Frequency (Recurrence)**
    *   **Logic:** Signals high personal utility or educational value.
    *   **Formula:** `COUNT(watch-history.json WHERE video_id == X)`
    *   **Validation:** Morningfame (Traction).

2.  **Intent-to-Save Ratio (Save-Intent)**
    *   **Logic:** Adding to "Watch Later" or a personal playlist indicates high value.
    *   **Formula:** `(Video_ID in Playlists) / (Unique Video_ID Count in History)`
    *   **Validation:** Tubular Labs (Fan Loyalty).

3.  **Shorts Algorithmic Fit (Completion)**
    *   **Logic:** Uses public benchmarks to weight the "Viewed vs. Swiped Away" status.
    *   **Formula:** `(Public API Views) vs. (ReelRise 70% Viral Benchmark)`
    *   **Validation:** ReelRise (Algorithm Heartbeat).

4.  **Interaction Breadth (Sentiment)**
    *   **Logic:** Measures active participation vs. passive consumption.
    *   **Formula:** `IF(Like_Status == True, 1, 0) + COUNT(Personal_Comments WHERE video_id == X)`
    *   **Validation:** InfluenceFlow (Standard Engagement).

5.  **Authentic Engagement Check (Quality)**
    *   **Logic:** Filters generic engagement from genuine interest.
    *   **Formula:** `NLP_RELEVANCE(Personal_Comment_String, Video_Description_Keywords)`
    *   **Validation:** InfluenceFlow (AER).

6.  **Subscription Latency (Temporal Signal)**
    *   **Logic:** Analyzes the speed of "Return Viewing" after a new upload.
    *   **Formula:** `(First_Watch_Timestamp in Takeout) - (API_Published_At)`
    *   **Validation:** SocialBee (Velocity).

7.  **Creator Affinity (Trust)**
    *   **Logic:** Measures the density of consumption for a specific creator.
    *   **Formula:** `COUNT(History WHERE channel_id == Y) / COUNT(Total_History)`
    *   **Validation:** Social Blade (Rank).

**Noise and Bias Mitigation:** "Total Views" is a vanity metric susceptible to algorithmic spikes. For a robust personal score, prioritize **Recurrence (Re-watch)** and **Manual Saves** over "Spiky" one-off views.