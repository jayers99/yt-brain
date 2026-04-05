# Unified SVG Icon System for Stars and Thumbs

## Summary

Replace all Unicode/emoji icons (stars `★` and thumbs `👍👎`) with inline SVG icons using thin strokes that match the dashboard's monochrome/indigo dark theme. Stroke-to-fill transitions communicate active state.

## Icons

Three SVG icons, all with `1.5px` stroke, `round` line-cap/join:

- **Star** — 5-point star, 16×16 viewBox
- **Thumb up** — minimal hand outline, 16×16 viewBox (scaled to ~14px via CSS)
- **Thumb down** — same hand path, vertically flipped via `transform: scaleY(-1)`, 16×16 viewBox

All icons use `currentColor` for stroke and fill so they inherit color from CSS.

## States and Colors

| State | Stroke color | Fill | Scale |
|-------|-------------|------|-------|
| Inactive | `--text-muted` (#50505e) | `none` | 1.0 |
| Hover | `--text-secondary` (#a0a0b0) | `none` | 1.15 |
| Active star | `--star-color` (#f59e0b) | `--star-color` at 90% opacity | 1.0 |
| Active thumb-up | `--liked-color` (#22c55e) | `--liked-color` at 90% opacity | 1.0 |
| Active thumb-down | `--disliked-color` (#ef4444) | `--disliked-color` at 50% opacity | 1.0 |

New CSS variables added to `:root`:
- `--liked-color: #22c55e`
- `--disliked-color: #ef4444`

## Transitions

All icons: `color 0.2s ease, transform 0.15s ease` (matches existing star pattern).

## Locations

### Channel Breakdown Table
- **Header:** Star filter toggle (`#starFilter`) — `&#9733;` → star SVG
- **Rows (server-rendered):** Star toggle per channel — `&#9733;` → star SVG
- **Rows (JS-rendered in `applyFilters`):** Star toggle in dynamic HTML template string — `&#9733;` → star SVG

### All Videos Table
- **Header:** Liked filter toggle (`#likedFilter`) — `&#x1F44D;` → thumb-up SVG
- **Rows (server-rendered):** Liked/disliked indicators — `&#x1F44D;`/`&#x1F44E;` → thumb-up/thumb-down SVG
- **JS (`toggleLikedFilter`):** Filter state cycles set `innerHTML` to `&#x1F44D;`/`&#x1F44E;` — replace with SVG strings

## CSS Changes

- Update `.star-btn` styles: remove `font-size`, add `display: inline-flex; align-items: center;`
- Update `.liked-icon`, `.liked-btn` styles: remove opacity-based approach, use color-based approach matching star pattern
- Add `.icon-svg` base class: `width: 16px; height: 16px; stroke: currentColor; fill: none; stroke-width: 1.5; stroke-linecap: round; stroke-linejoin: round; transition: color 0.2s ease, fill 0.2s ease, transform 0.15s ease;`
- Active states set both `color` and `fill` on the SVG via parent class

## File Changed

| File | Change |
|------|--------|
| `src/yt_brain/web/dashboard.py` | CSS: new variables, `.icon-svg` class, updated star/liked styles. HTML: replace all `&#9733;`/`&#x1F44D;`/`&#x1F44E;` with inline SVGs. JS: update `toggleLikedFilter` innerHTML and channel row template string. |

## Out of Scope

- Adding new icon types beyond star, thumb-up, thumb-down
- Animating the stroke-to-fill transition (CSS transition on fill opacity is sufficient)
- External icon libraries or fonts
