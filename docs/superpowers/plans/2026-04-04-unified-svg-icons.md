# Unified SVG Icons Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace all Unicode/emoji icons (stars and thumbs) with inline SVG icons using thin strokes matching the dark theme.

**Architecture:** Single-file change to `dashboard.py`. Define SVG path constants as JS variables for reuse across static HTML and dynamic JS templates. Update CSS to style SVGs via `currentColor` inheritance. Replace all 8 icon locations (3 star, 5 thumb) with SVG markup.

**Tech Stack:** Inline SVG, CSS `currentColor`, Flask/Jinja template

**Spec:** `docs/superpowers/specs/2026-04-04-unified-svg-icons-design.md`

---

### Task 1: Add CSS variables, icon base class, and SVG JS constants

**Files:**
- Modify: `src/yt_brain/web/dashboard.py:84-93` (CSS variables)
- Modify: `src/yt_brain/web/dashboard.py:366-386` (liked-icon/liked-btn styles)
- Modify: `src/yt_brain/web/dashboard.py:509-511` (star-btn styles)

- [ ] **Step 1: Add CSS variables for liked/disliked colors**

In the `:root` block (around line 88, after `--star-color`), add:

```css
--liked-color: #22c55e;
--disliked-color: #ef4444;
```

- [ ] **Step 2: Add `.icon-svg` base class and update star/liked styles**

Replace the existing star-btn styles (lines 509-511):

```css
.star-btn { cursor: pointer; font-size: 16px; color: var(--text-muted); transition: color 0.2s ease, transform 0.15s ease; }
.star-btn:hover { color: var(--star-color); transform: scale(1.15); }
.star-btn.starred { color: var(--star-color); }
```

With:

```css
.icon-svg { width: 16px; height: 16px; stroke: currentColor; fill: none; stroke-width: 1.5; stroke-linecap: round; stroke-linejoin: round; vertical-align: middle; transition: color 0.2s ease, fill 0.2s ease, transform 0.15s ease; }
.star-btn { cursor: pointer; color: var(--text-muted); display: inline-flex; align-items: center; transition: color 0.2s ease, transform 0.15s ease; }
.star-btn:hover { color: var(--star-color); transform: scale(1.15); }
.star-btn.starred { color: var(--star-color); }
.star-btn.starred .icon-svg { fill: var(--star-color); fill-opacity: 0.9; }
```

Replace the existing liked-icon/liked-btn styles (lines 366-386):

```css
.liked-icon {
    opacity: 0.3;
}
.liked-icon.liked {
    opacity: 1;
}
.liked-icon.disliked {
    opacity: 1;
}
.liked-btn {
    cursor: pointer;
    opacity: 0.3;
    font-size: 14px;
    user-select: none;
}
.liked-btn.filter-like {
    opacity: 1;
}
.liked-btn.filter-dislike {
    opacity: 1;
}
```

With:

```css
.liked-icon {
    color: var(--text-muted);
    display: inline-flex;
    align-items: center;
}
.liked-icon.liked {
    color: var(--liked-color);
}
.liked-icon.liked .icon-svg {
    fill: var(--liked-color);
    fill-opacity: 0.9;
}
.liked-icon.disliked {
    color: var(--disliked-color);
}
.liked-icon.disliked .icon-svg {
    fill: var(--disliked-color);
    fill-opacity: 0.5;
}
.liked-btn {
    cursor: pointer;
    color: var(--text-muted);
    display: inline-flex;
    align-items: center;
    user-select: none;
    transition: color 0.2s ease, transform 0.15s ease;
}
.liked-btn:hover {
    color: var(--text-secondary);
    transform: scale(1.15);
}
.liked-btn.filter-like {
    color: var(--liked-color);
}
.liked-btn.filter-like .icon-svg {
    fill: var(--liked-color);
    fill-opacity: 0.9;
}
.liked-btn.filter-dislike {
    color: var(--disliked-color);
}
.liked-btn.filter-dislike .icon-svg {
    fill: var(--disliked-color);
    fill-opacity: 0.5;
}
```

- [ ] **Step 3: Add SVG constants in the `<script>` section**

At the top of the `<script>` block (right after `<script>`, before any existing JS), add:

```javascript
const SVG_STAR = '<svg class="icon-svg" viewBox="0 0 24 24"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87L18.18 22 12 18.56 5.82 22 7 14.14l-5-4.87 6.91-1.01L12 2z"/></svg>';
const SVG_THUMB_UP = '<svg class="icon-svg" viewBox="0 0 24 24"><path d="M7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3m7-2V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3H14z"/></svg>';
const SVG_THUMB_DOWN = '<svg class="icon-svg" viewBox="0 0 24 24" style="transform:scaleY(-1)"><path d="M7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3m7-2V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3H14z"/></svg>';
```

- [ ] **Step 4: Commit**

```bash
git add src/yt_brain/web/dashboard.py
git commit -m "Add SVG icon CSS and JS constants"
```

---

### Task 2: Replace star icons in channel breakdown

**Files:**
- Modify: `src/yt_brain/web/dashboard.py:662` (channel table header — star filter)
- Modify: `src/yt_brain/web/dashboard.py:666` (channel table rows — star toggle, Jinja)
- Modify: `src/yt_brain/web/dashboard.py:1305` (channel table rows — star toggle, JS template)

- [ ] **Step 1: Replace star filter header icon**

On line 662, find:

```html
<span id="starFilter" class="star-btn" onclick="toggleStarFilter()" title="Show starred only">&#9733;</span>
```

Replace `&#9733;` with the SVG. The full span becomes:

```html
<span id="starFilter" class="star-btn" onclick="toggleStarFilter()" title="Show starred only"><svg class="icon-svg" viewBox="0 0 24 24"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87L18.18 22 12 18.56 5.82 22 7 14.14l-5-4.87 6.91-1.01L12 2z"/></svg></span>
```

- [ ] **Step 2: Replace star icons in Jinja-rendered channel rows**

On line 666, find:

```html
<span class="star-btn{% if c.starred %} starred{% endif %}" onclick="toggleStar(this, '{{ c.name | e }}')" title="Star channel">&#9733;</span>
```

Replace `&#9733;` with the SVG:

```html
<span class="star-btn{% if c.starred %} starred{% endif %}" onclick="toggleStar(this, '{{ c.name | e }}')" title="Star channel"><svg class="icon-svg" viewBox="0 0 24 24"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87L18.18 22 12 18.56 5.82 22 7 14.14l-5-4.87 6.91-1.01L12 2z"/></svg></span>
```

- [ ] **Step 3: Replace star icons in JS dynamic channel rows**

On line 1305, in the template literal, find:

```javascript
<span class="star-btn${starred}" onclick="toggleStar(this, '${eName}')" title="Star channel">&#9733;</span>
```

Replace `&#9733;` with `${SVG_STAR}`:

```javascript
<span class="star-btn${starred}" onclick="toggleStar(this, '${eName}')" title="Star channel">${SVG_STAR}</span>
```

- [ ] **Step 4: Verify visually**

Run: `cd /Users/jayers/code/praxis-workspace/projects/learn/yt-brain && uv run yt-brain dashboard`

Open `http://localhost:5555`. Confirm:
- Channel breakdown stars render as outlined SVGs in muted color
- Starred channels show filled amber stars
- Star filter header icon matches
- Hovering any star shows amber color + scale

- [ ] **Step 5: Commit**

```bash
git add src/yt_brain/web/dashboard.py
git commit -m "Replace Unicode stars with SVG icons in channel breakdown"
```

---

### Task 3: Replace thumb icons in All Videos table

**Files:**
- Modify: `src/yt_brain/web/dashboard.py:733` (liked filter header)
- Modify: `src/yt_brain/web/dashboard.py:745` (liked/disliked icons in video rows, Jinja)
- Modify: `src/yt_brain/web/dashboard.py:1076-1094` (toggleLikedFilter JS function)

- [ ] **Step 1: Replace liked filter header icon**

On line 733, find:

```html
<span id="likedFilter" class="liked-btn" onclick="toggleLikedFilter()" title="Filter by liked status">&#x1F44D;</span>
```

Replace `&#x1F44D;` with the SVG:

```html
<span id="likedFilter" class="liked-btn" onclick="toggleLikedFilter()" title="Filter by liked status"><svg class="icon-svg" viewBox="0 0 24 24"><path d="M7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3m7-2V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3H14z"/></svg></span>
```

- [ ] **Step 2: Replace liked/disliked icons in Jinja video rows**

On line 745, find:

```html
<td class="liked-cell">{% if v.liked == 'like' %}<span class="liked-icon liked">&#x1F44D;</span>{% elif v.liked == 'dislike' %}<span class="liked-icon disliked">&#x1F44E;</span>{% endif %}</td>
```

Replace with:

```html
<td class="liked-cell">{% if v.liked == 'like' %}<span class="liked-icon liked"><svg class="icon-svg" viewBox="0 0 24 24"><path d="M7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3m7-2V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3H14z"/></svg></span>{% elif v.liked == 'dislike' %}<span class="liked-icon disliked"><svg class="icon-svg" viewBox="0 0 24 24" style="transform:scaleY(-1)"><path d="M7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3m7-2V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3H14z"/></svg></span>{% endif %}</td>
```

- [ ] **Step 3: Update `toggleLikedFilter` JS function**

Replace the entire function (lines 1076-1094):

```javascript
function toggleLikedFilter() {
    const btn = document.getElementById('likedFilter');
    if (likedFilterState === null) {
        likedFilterState = 'like';
        btn.classList.add('filter-like');
        btn.classList.remove('filter-dislike');
        btn.innerHTML = '&#x1F44D;';
    } else if (likedFilterState === 'like') {
        likedFilterState = 'dislike';
        btn.classList.remove('filter-like');
        btn.classList.add('filter-dislike');
        btn.innerHTML = '&#x1F44E;';
    } else {
        likedFilterState = null;
        btn.classList.remove('filter-like', 'filter-dislike');
        btn.innerHTML = '&#x1F44D;';
    }
    applyFilters();
}
```

With:

```javascript
function toggleLikedFilter() {
    const btn = document.getElementById('likedFilter');
    if (likedFilterState === null) {
        likedFilterState = 'like';
        btn.classList.add('filter-like');
        btn.classList.remove('filter-dislike');
        btn.innerHTML = SVG_THUMB_UP;
    } else if (likedFilterState === 'like') {
        likedFilterState = 'dislike';
        btn.classList.remove('filter-like');
        btn.classList.add('filter-dislike');
        btn.innerHTML = SVG_THUMB_DOWN;
    } else {
        likedFilterState = null;
        btn.classList.remove('filter-like', 'filter-dislike');
        btn.innerHTML = SVG_THUMB_UP;
    }
    applyFilters();
}
```

- [ ] **Step 4: Verify visually**

Run the dashboard and check:
1. Liked filter header shows outlined thumb-up SVG in muted color
2. Click once → green filled thumb-up (filter-like state)
3. Click again → red filled thumb-down (filter-dislike state)
4. Click again → back to muted outlined thumb-up
5. Video rows show green filled thumb-up for liked, muted red filled thumb-down for disliked
6. Hover on filter header shows scale + brighter color

- [ ] **Step 5: Commit**

```bash
git add src/yt_brain/web/dashboard.py
git commit -m "Replace emoji thumbs with SVG icons in All Videos table"
```
