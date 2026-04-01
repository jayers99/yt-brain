# Brain Drain — Brainstorm Notes

**Date:** 2026-03-30
**Status:** In progress — brainstorming
**Slug:** `brain-drain`

## Concept

Detect and surface "brain rot" viewing patterns — binge spirals of low-quality content consumption. Find the trash, face the truth, understand the patterns.

## Decisions Made

### Feature name: `brain-drain`
- Where your IQ points went

### Detection signals

**Binge velocity**
- 5+ videos on the same topic/cluster in a short time window
- Measures how fast you fell down the hole

**Binge length**
- Total duration of a brain drain session
- How long the spiral lasted before you snapped out of it (or didn't)

**Late night flag**
- Tag sessions that happen late at night — prime brain rot hours

**Drinking detection (impairment inference)**
Multiple approaches, likely combined:
- **Time heuristic** — Friday/Saturday after 10pm = "probably drinking" territory, user-configurable threshold
- **Content quality decay** — track if video quality degrades over an evening session (started with a lecture, ended on fail compilations = sus)
- **Self-report** — retroactive "I was drunk" tag during review
- **Combo confidence score** — late night + weekend + binge velocity + content quality nosedive = "likely impaired" rating
- **User-defined drinking hours** — configurable window in config, everything in that window gets flagged

## Open Questions

- How to visualize brain drain sessions in the dashboard?
- Scoring/ranking: worst brain drain sessions of all time?
- Alerts or just retrospective analysis?
- Should brain drain feed into engagement classification?

---

# Watch Next Agent — Brainstorm Notes

**Date:** 2026-03-30
**Status:** In progress — brainstorming
**Slug:** TBD

## Concept

A persistent agent that acts as a personal video recommendation engine. Replaces YouTube's algorithm with one that actually knows you. Runs 24/7, continuously builds and maintains a "watch next" playlist ranked by probability you'll enjoy each video.

## Key Ideas

- **Recommendation source:** Based on previous search queries, viewing history, engagement patterns, starred channels, cluster preferences
- **Playlist management:** Keeps a playlist full — as you watch videos, it backfills with new suggestions
- **Probability ranking:** Each suggestion scored by likelihood you'll like it, sorted best-first
- **Always-on agent:** Runs continuously, not just on-demand — proactively discovers and queues content
- **YouTube playlist sync:** Ideally pushes recommendations to an actual YouTube playlist for cross-device playback

## Constraints

**Duration sweet spot**
- Analyze watch history to find the user's preferred video length range
- Only recommend videos in that medium time range — no 30-second clips, no 3-hour deep dives
- "I don't have time to watch lengthy videos anymore"

## Open Questions

- Discovery source: only videos from channels you already watch, or discover new channels/creators?
- How to score "probability you'll like it" — embedding similarity? Engagement history? Claude reasoning?
- Agent runtime: background daemon? Scheduled cron? Claude agent with tool access?
- YouTube API OAuth needed for playlist write access?
- How does brain-drain detection interact — should the agent avoid recommending brain rot, or have a "guilty pleasure" mode?
- Should the duration sweet spot be auto-calculated from history or user-configurable?

---

# Engagement Scoring — Brainstorm Notes

**Date:** 2026-03-30
**Status:** In progress — brainstorming
**Slug:** TBD

## Concept

Replace the coarse 5-tier engagement classification (UNKNOWN/BOUNCED/WATCHED/LIKED/CURATED) with a continuous engagement metric. Score both individual videos AND channels based on real behavioral signals.

## Current State

- Already tracking: `watched_seconds`, `duration_seconds`, `watch_percentage`, `engagement_level`
- Current classifier is simple threshold-based (watch % → tier)
- No channel-level aggregation exists

## Key Signals

**Per-video engagement:**
- Watch percentage (30 seconds on a 20-min video = bounce = low score)
- Completion rate
- Whether you came back to rewatch
- Engagement override (manual signal)

**Per-channel engagement (aggregated):**
- Average watch percentage across all videos from that channel
- Bounce rate — what % of their videos do you bail on?
- Return frequency — how often do you watch this channel?
- Starred status (strong positive signal)
- Trend — is engagement going up or down over time?

## Key Insight

"If I only watch 30 seconds, I don't like that channel" — bounce rate is a negative signal that should propagate from video to channel. Channels with high bounce rates get deprioritized in recommendations.

## Open Questions

- Numeric score (0-100) or keep tiers but make them smarter?
- How does this feed into the watch-next agent's probability ranking?
- Should the score decay over time (recent behavior weighted more)?
- How does this interact with brain-drain detection?

---

# Shame Score — Brainstorm Notes

**Date:** 2026-03-30
**Status:** Idea captured
**Slug:** `shame-score`

## Concept

A weekly report card that aggregates brain-drain sessions into a trend line. "This week you spent 4.2 hours watching people fall off things. Your brain drain index is up 340% from last week. Your mom would be disappointed." Gamification in reverse — the goal is to make the number go DOWN.

## Key Ideas

- Weekly summary with brain rot hours, trend vs previous week, worst session
- Tone: brutally honest, funny, slightly judgmental
- Streak tracking — "3 weeks without a taser video binge"
- Could use Claude to generate personalized roasts based on the actual content

---

# Sober Queue / Drunk Queue — Brainstorm Notes

**Date:** 2026-03-30
**Status:** Idea captured
**Slug:** `sober-queue` / `drunk-queue`

## Concept

The watch-next agent has a split personality. During "drinking hours" it builds one playlist, during sober hours another. The feature is the confrontation between who you think you are and who you are at 1am on a Saturday.

## Key Ideas

- Two parallel queues maintained by the watch-next agent
- Dashboard view: side-by-side comparison columns
- Engagement stats per queue — drunk-you has a 94% completion rate on trash while sober-you abandons MIT lectures at 8 minutes
- Feeds from brain-drain's drinking detection (time heuristics, content decay, self-report)
- The data doesn't lie

---

# Channel Autopsy — Brainstorm Notes

**Date:** 2026-03-30
**Status:** Idea captured
**Slug:** `channel-autopsy`

## Concept

When engagement scoring detects a channel is dying (your watch % declining over months), generate a eulogy. "You and Linus Tech Tips had a good run. 47 videos watched in 2024, down to 3 in 2025. Cause of death: you stopped caring about PC builds." Helps consciously prune subscriptions.

## Key Ideas

- Requires engagement scoring with time-series trend data
- Claude-generated eulogies based on actual viewing history
- Could surface in dashboard as a "departures" section
- Actionable: unstar/unsubscribe prompt after the eulogy

---

# Taste Drift — Brainstorm Notes

**Date:** 2026-03-30
**Status:** Idea captured
**Slug:** `taste-drift`

## Concept

Monthly visualization of how your interests are shifting. "You're 23% more into woodworking than 3 months ago. Your programming content is down 15%. At this rate you'll be a carpenter by October." Uses cluster embeddings over time windows.

## Key Ideas

- Compare cluster distributions across monthly windows
- Detect emerging interests (new clusters appearing) and dying ones (clusters shrinking)
- Extrapolate trends for comedic effect — "At this rate..."
- Could feed into watch-next agent to lean into emerging interests

---

# Guilty Pleasure Budget — Brainstorm Notes

**Date:** 2026-03-30
**Status:** Idea captured
**Slug:** `guilty-pleasure-budget`

## Concept

Set a weekly brain rot allowance. "I'm allowed 2 hours of trash per week." The watch-next agent tracks your balance and either cuts you off or starts mixing in quality content to dilute the rot. Like a financial budget but for your neurons.

## Key Ideas

- User-configurable weekly budget (e.g., 2 hours)
- Real-time balance tracking — "You have 47 minutes of guilt left this week"
- When budget runs low, watch-next agent starts diluting recommendations with quality content
- "Overdraft" mode — you can go over budget but shame-score penalizes it harder
- Resets weekly (or configurable)
- Interacts with brain-drain detection to classify what counts as "guilty"

---

# Public Release — Brainstorm Notes

**Date:** 2026-03-30
**Status:** Idea captured — large effort, needs decomposition
**Slug:** `public-release`

## Concept

Package yt-brain for John Q Public. Currently a developer's personal tool with hardcoded API keys and manual setup. Needs to become something a non-technical user can install and run.

## Known Challenges

**API key problem:**
- Currently uses a personal Anthropic API key for Claude-powered clustering/labeling
- Users shouldn't need their own Anthropic account — need a hosted option, local model fallback, or remove the Claude dependency entirely for core features

**YouTube/Google API problem:**
- YouTube Data API requires a Google Cloud project, API key, OAuth consent screen
- John Q Public is NOT going to set up a GCP project and enable APIs
- Options: hosted proxy, OAuth flow that just works, or lean harder on yt-dlp (no API key needed) and browser cookies

**Other packaging concerns:**
- Installation: pip/pipx/brew? Desktop app? Docker?
- Database setup: currently assumes `~/.config/yt-brain/` — needs to just work
- Takeout import UX: non-technical users need guidance through Google Takeout
- Dashboard hosting: localhost is fine for devs, not for normies
- sqlite-vec native extension: cross-platform compilation
- Sentence-transformers model download: ~90MB on first run, needs to be transparent

## Open Questions

- Target audience: power users who can run a CLI, or truly mainstream?
- Monetization: free/open source, freemium with hosted API, donation-ware?
- Hosted vs self-hosted vs hybrid?
- Which features require API keys and which can work without them?
- How much of the YouTube API can be replaced by yt-dlp to reduce the auth burden?
