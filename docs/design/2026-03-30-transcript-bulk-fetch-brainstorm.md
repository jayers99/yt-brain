# Transcript Bulk Fetch — Brainstorm Notes

**Date:** 2026-03-30
**Status:** In progress — paused for further thought
**Backlog item:** #6 `transcript-bulk-fetch`

## Decisions Made

### Scope: Fetch all transcripts
- Fetch transcripts for all videos, not just starred/high-engagement
- Database can handle the volume (~100-200MB for a large library)
- Transcript fetch runs once (or rarely) during database build, not real-time

### Separate transcript database
- Move transcripts out of the main `videos` table into a **separate SQLite database**
- Main DB stays lean — dashboard queries never touch transcript text
- Use SQLite `ATTACH DATABASE` to join across when needed
- Transcript DB can grow independently without affecting core dashboard performance

### Keep current embeddings clean
- Title + description embeddings stay as-is (high signal density, 256-token model window)
- Transcripts would dilute embeddings — intros, tangents, sponsor reads are noise for topic matching
- Current clustering and semantic search quality is better with concise metadata

### Progressive disclosure for search
- **Default search:** title + description embeddings (current behavior, fast)
- **Deep search option:** also queries transcript DB for content-level matches
- Future possibility: chunk-level transcript embeddings as a separate feature (split transcripts into passages, embed each, search within videos)

## Open Questions

- **CLI design:** Standalone command vs. pipeline step in `update.sh` vs. both
- **Rate limiting / batching:** How to handle large initial fetch (thousands of yt-dlp calls)
- **Transcript metadata:** Store language, word count, fetch timestamp?
- **Deep search UX:** Toggle in dashboard? Separate search mode? Auto-fallback?
