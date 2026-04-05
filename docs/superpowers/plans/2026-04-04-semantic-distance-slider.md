# Semantic Search Distance Slider Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a range slider next to the All Videos search box that controls semantic search `max_distance` in real-time.

**Architecture:** Pure frontend change in `dashboard.py`. Restructure the search header into a flex layout containing the existing search input + a new slider group. Wire the slider's `input` event into the existing `scheduleSemanticSearch` debounce flow, appending `max_distance` to the API fetch URL.

**Tech Stack:** HTML/CSS/JS inline in Flask template (`dashboard.py`)

**Spec:** `docs/superpowers/specs/2026-04-04-semantic-distance-slider-design.md`

---

### Task 1: Add slider HTML and CSS

**Files:**
- Modify: `src/yt_brain/web/dashboard.py:508-529` (CSS section)
- Modify: `src/yt_brain/web/dashboard.py:690-691` (search header HTML)

- [ ] **Step 1: Add CSS for the slider group**

In the CSS section (after the `.search-wrap` styles around line 529), add:

```css
.search-row { display: flex; align-items: center; gap: 12px; width: 100%; }
.search-row .search-wrap { flex: 1; min-width: 0; }
.slider-group { display: flex; align-items: center; gap: 6px; flex-shrink: 0; }
.slider-group input[type="range"] { width: 120px; accent-color: var(--accent); cursor: pointer; }
.slider-value { font-family: var(--font-mono); font-size: 12px; color: var(--text-muted); min-width: 35px; text-align: right; }
```

- [ ] **Step 2: Restructure the search header HTML**

Replace the `<th>` on line 691:

```html
<th colspan="7" style="padding-bottom:12px"><div class="search-wrap"><input type="text" id="semanticSearch" placeholder="{{ 'Search by topic, concept, or keyword...' if has_embeddings else 'Run yt-brain embed to enable semantic search' }}" {{ '' if has_embeddings else 'disabled' }} oninput="scheduleSemanticSearch()" class="search-input" style="width:100%"><span class="clear-btn" onclick="clearSearch()">&times;</span></div></th>
```

With:

```html
<th colspan="7" style="padding-bottom:12px">
  <div class="search-row">
    <div class="search-wrap"><input type="text" id="semanticSearch" placeholder="{{ 'Search by topic, concept, or keyword...' if has_embeddings else 'Run yt-brain embed to enable semantic search' }}" {{ '' if has_embeddings else 'disabled' }} oninput="scheduleSemanticSearch()" class="search-input" style="width:100%"><span class="clear-btn" onclick="clearSearch()">&times;</span></div>
    <div class="slider-group">
      <input type="range" id="distanceSlider" min="0.1" max="1.2" step="0.05" value="0.6" oninput="onDistanceSliderInput()">
      <span id="distanceValue" class="slider-value">0.60</span>
    </div>
  </div>
</th>
```

- [ ] **Step 3: Verify visually**

Run: `cd /Users/jayers/code/praxis-workspace/projects/learn/yt-brain && uv run yt-brain dashboard`

Open `http://localhost:5555`. Confirm:
- Search box and slider appear side-by-side
- Slider shows `0.60` readout
- Slider thumb is styled with accent color
- Layout doesn't break on narrow viewports

- [ ] **Step 4: Commit**

```bash
git add src/yt_brain/web/dashboard.py
git commit -m "Add distance slider HTML/CSS next to search box"
```

---

### Task 2: Wire slider to semantic search

**Files:**
- Modify: `src/yt_brain/web/dashboard.py:1055-1100` (JS `scheduleSemanticSearch` and new handler)
- Modify: `src/yt_brain/web/dashboard.py:960-968` (JS `clearSearch`)

- [ ] **Step 1: Add the `onDistanceSliderInput` function**

In the `<script>` section, right before the `scheduleSemanticSearch` function (around line 1055), add:

```javascript
function onDistanceSliderInput() {
    document.getElementById('distanceValue').textContent =
        parseFloat(document.getElementById('distanceSlider').value).toFixed(2);
    scheduleSemanticSearch();
}
```

- [ ] **Step 2: Update the fetch URL in `scheduleSemanticSearch`**

In `scheduleSemanticSearch`, change the fetch call (line 1083) from:

```javascript
fetch('/api/search?q=' + encodeURIComponent(q) + '&limit=200')
```

To:

```javascript
fetch('/api/search?q=' + encodeURIComponent(q) + '&limit=200&max_distance=' + document.getElementById('distanceSlider').value)
```

- [ ] **Step 3: Reset slider in `clearSearch`**

In the `clearSearch` function (line 960), add two lines after `semanticSearchEl.value = '';`:

```javascript
document.getElementById('distanceSlider').value = 0.6;
document.getElementById('distanceValue').textContent = '0.60';
```

- [ ] **Step 4: Verify behavior**

Run the dashboard and test:
1. Type a search query → results appear
2. Drag slider left (toward 0.1) → fewer, more relevant results
3. Drag slider right (toward 1.2) → more results, looser matches
4. Click the clear button → slider resets to 0.60
5. Adjust slider with no query → no error, no effect

- [ ] **Step 5: Commit**

```bash
git add src/yt_brain/web/dashboard.py
git commit -m "Wire distance slider to semantic search with real-time updates"
```
