# Semantic Search Distance Slider

## Summary

Add a range slider directly to the right of the All Videos search box that controls the `max_distance` threshold for semantic search. Results update in real-time as the user adjusts the slider.

## Layout

The existing `<th colspan="7">` containing the search input gets restructured:

- Outer flex container with `gap: 12px`, `align-items: center`
- Search input takes `flex: 1` (majority of width)
- Slider group sits to the right: `<input type="range">` (~120px) + numeric readout (~35px)

```
[__Search by topic, concept, or keyword...___x] [====O=====] 0.60
```

## Slider Spec

| Property  | Value  |
|-----------|--------|
| Min       | 0.1    |
| Max       | 1.2    |
| Step      | 0.05   |
| Default   | 0.6    |
| Width     | ~120px |

- Numeric readout: monospace, `font-size: 12px`, shows two decimal places (e.g. `0.60`)
- Always visible and active, styled to match existing dark theme (`--bg-elevated`, `--accent`)
- Custom range styling for webkit/moz to match dark theme

## Behavior

1. **On slider `input` event**: update the numeric readout immediately, then trigger a debounced re-fetch (same 300ms debounce as the search box)
2. **Fetch URL**: append `&max_distance={value}` to the existing `/api/search?q=...&limit=200` call
3. **When no search query is active**: slider is visible but has no effect (no API call to modify)
4. **`clearSearch()`**: resets slider value back to `0.6` and updates the readout
5. **Shared debounce**: slider adjustments and search text changes share the same 300ms debounce timer (`semanticTimer`) — whichever fires last wins

## Files Changed

| File | Change |
|------|--------|
| `src/yt_brain/web/dashboard.py` | HTML: restructure search header into flex layout with slider. CSS: slider styling. JS: wire slider to search fetch, reset on clear. |

## Backend

No changes needed. `/api/search` already accepts `max_distance` as a query parameter (line 1546 of `dashboard.py`).

## Out of Scope

- Persisting slider position across page reloads
- Labels like "Exact" / "Broad" on slider ends
- Hiding/disabling slider when embeddings are unavailable (keep simple — it just has no effect)
