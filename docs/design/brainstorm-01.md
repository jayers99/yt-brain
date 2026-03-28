# YT-Brain (YouTube Second Brain)

## Overview

YT-Brain is an agentic system designed to transform YouTube into a structured, high-signal learning platform.

It captures, scores, curates, and integrates YouTube content into a broader knowledge ecosystem, such as NotebookLM and Obsidian, enabling:

- Continuous learning optimization
- High-quality content filtering
- Semantic discovery of new knowledge
- Durable knowledge retention and synthesis

## Core Objectives

### 1. Data Collection First (MVP Priority)

- Establish robust ingestion of YouTube activity
- Capture watch history, likes, playlists, and engagement signals

### 2. Content Quality Filtering

- Identify high-value creators
- Suppress low-value or noisy content
- Build a personalized signal-to-noise optimization engine

### 3. Queue Optimization

- Replace ad hoc browsing with a curated learning queue
- Continuously prioritize relevant, high-quality content

### 4. RAG Integration

- Promote high-value creators into NotebookLM
- Maintain up-to-date transcript ingestion for queryable knowledge

### 5. Holistic Learning System

- Integrate across mediums: video, notes, and articles
- Connect with Obsidian and the Praxis ecosystem

## Key System Concepts

### 1. Intelligent Queue Engine

A continuously optimized YouTube queue that:

- Prioritizes high-value content
- Reorders dynamically based on:
  - User preferences
  - Learning goals
  - Engagement signals
- Syncs with YouTube playlists for cross-device access, including Apple TV and iPad

### 2. Channel Scoring System

#### Scoring Model

- Range: 0-10
- Inputs:
  - Explicit feedback: upvote/downvote
  - Implicit signals:
    - Watch completion
    - Rewatch frequency
    - Likes
    - Time spent

#### Behavior

- High score: promoted
- Low score: suppressed
- Threshold-based filtering

#### Pattern Inspiration

- Digg-style voting system

### 3. Graduation Pipeline (Channel to RAG)

A controlled promotion mechanism:

1. Discover channel
2. Watch and evaluate
3. Accumulate score
4. Manual "Graduate" action
5. Trigger ingestion into NotebookLM

#### Outcome

- Entire channel becomes:
  - Searchable
  - Queryable via AI
  - Part of the active knowledge base

### 4. Continuous RAG Sync

- Monitor graduated channels
- Detect new uploads
- Automatically ingest transcripts into NotebookLM

#### Implementation Options

- Scheduled polling
- Event-driven ingestion

### 5. Semantic Discovery Engine

#### Goal

Surface new creators and content based on conceptual similarity.

#### Mechanism

- Embeddings plus vector similarity
- Cluster:
  - Videos
  - Channels
  - Topics

#### Example

If studying RAG, surface:

- Adjacent creators
- Related topics such as agents, embeddings, and retrieval systems
- High-quality educators in the same semantic space

### 6. Playlist Awareness

- Detect when liked videos belong to a playlist
- Recommend the entire playlist as a structured learning path

#### Example

"You liked 4 videos from this playlist - explore the full sequence"

### 7. Discovery Enhancements

#### Features

- Emerging creator detection
- Topic expansion via semantic proximity
- Cross-channel influence mapping

### 8. Learning Tracks (Separate Project)

A modular system defining structured learning domains.

#### Examples

- Agentic Programming
- RAG Systems
- AI Infrastructure

#### Integration

YT-Brain:

- Feeds into tracks
- Pulls recommendations from tracks

### 9. Librarian System (Praxis Integration)

A curated archive of high-value artifacts.

#### Responsibilities

- Identify resharing-worthy content
- Store:
  - Key videos
  - Insights
  - References
- Tag for:
  - Retrieval
  - Publishing
  - Knowledge synthesis

### 10. Cognitive Learning Optimization

Designed for long-term retention and fluid thinking.

#### Techniques

- Spaced repetition
- Reflection prompts
- Concept linking
- Periodic resurfacing of prior content

#### Goal

Convert passive watching into:

- Durable knowledge
- Generative thinking capability

### 11. Taste and Preference Modeling

A system to understand why content is preferred.

#### Dimensions

- Topic
- Depth
- Teaching style
- Pacing
- Format

#### Outcome

- Improved recommendations
- Personalized learning optimization

### 12. Multi-Modal Knowledge Integration

#### Systems

- YouTube (video)
- NotebookLM (RAG)
- Obsidian (notes)
- Articles

#### Goal

Unified knowledge graph across all media.

### 13. Agentic Architecture

#### Characteristics

- Always-on system
- Background agents performing:
  - Ingestion
  - Scoring
  - Sync
  - Discovery
  - Optimization

#### Human Role

- Strategic oversight
- Manual promotion (graduation)
- Governance decisions

### 14. Governance Model (Praxis-Aligned)

#### Define

- When agents act autonomously
- When escalation is required

#### Example

- Auto-ingest: allowed
- Channel graduation: manual approval

## Data Collection Strategy (MVP Focus)

### Sources

- YouTube API
- Watch history
- Likes
- Playlists
- Subscriptions

### Engagement Signals

- Watch duration
- Completion rate
- Rewatch frequency
- Interaction events

### Processing Layers

1. Raw ingestion
2. Feature extraction
3. Scoring
4. Storage

## Integration with YouTube Ecosystem

Leverage native features:

- Watch Later
- Likes
- Playlists
- Subscriptions

### Strategy

- Reinforce YouTube's recommendation system
- Use playlists as a control surface for the queue

## Research / Spike Backlog

### 1. YouTube Engagement Metrics

- Available API fields
- Watch duration granularity
- Limitations and gaps

### 2. Classification Models

- Content scoring systems
- Recommendation algorithms
- Hybrid rule plus ML approaches

### 3. Prior Art (External Tools)

- Learning analytics platforms
- Content recommendation engines
- Knowledge management tools

### 4. Cognitive Learning Research

- Retention strategies for older adults
- Techniques for:
  - Recall
  - Concept transfer
  - Creative synthesis

### 5. Semantic Video Mapping

- Existing datasets of video embeddings
- Precomputed knowledge graphs
- Opportunities to reuse external models

## Future Considerations

- Self-improving agent heuristics
- Cross-user knowledge sharing (optional)
- Publishing pipeline: content to output
- Integration with Praxis Workshop workflows

## Summary

YT-Brain is not just a recommendation system. It is a learning optimization engine that transforms YouTube into a structured, evolving, AI-augmented knowledge system.

It combines:

- Signal filtering
- Semantic discovery
- Agentic automation
- Cognitive science
- Multi-modal integration

All governed under Praxis.

## Next Step

If you want the next logical follow-on, convert this into a Praxis SOD, then derive epics and tickets for implementation.
