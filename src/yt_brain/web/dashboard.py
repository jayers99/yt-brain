"""Flask dashboard for yt-brain."""

from __future__ import annotations

import json
from collections import Counter

from flask import Flask, jsonify, render_template_string, request

import sqlite3

from yt_brain.infrastructure.config import load_config
from yt_brain.infrastructure.database import get_all_videos, get_channel_urls, get_starred_channels, init_db, toggle_starred_channel

from .classifier import classify_genre, genre_stats

TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>yt-brain Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
            background: #0f0f0f;
            color: #e0e0e0;
            padding: 24px;
        }
        h1 {
            font-size: 28px;
            font-weight: 700;
            margin-bottom: 8px;
            color: #fff;
        }
        .subtitle { color: #888; margin-bottom: 32px; font-size: 14px; }
        .grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 24px;
            margin-bottom: 32px;
            align-items: stretch;
        }
        .card {
            background: #1a1a1a;
            border-radius: 12px;
            padding: 24px;
            border: 1px solid #2a2a2a;
            display: flex;
            flex-direction: column;
            max-height: 500px;
        }
        .card h2 {
            font-size: 16px;
            font-weight: 600;
            margin-bottom: 16px;
            color: #ccc;
        }
        .stat-row {
            display: flex;
            gap: 24px;
            margin-bottom: 32px;
        }
        .stat-box {
            background: #1a1a1a;
            border-radius: 12px;
            padding: 20px 28px;
            border: 1px solid #2a2a2a;
            text-align: center;
        }
        .stat-box .number {
            font-size: 36px;
            font-weight: 700;
            color: #fff;
        }
        .stat-box .label {
            font-size: 12px;
            color: #888;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-top: 4px;
        }
        .chart-container {
            position: relative;
            height: 350px;
        }
        .full-width { grid-column: 1 / -1; }
        table {
            width: 100%;
            border-collapse: collapse;
            font-size: 13px;
        }
        th {
            text-align: left;
            padding: 8px 12px;
            border-bottom: 1px solid #333;
            color: #888;
            font-weight: 500;
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        td {
            padding: 8px 12px;
            border-bottom: 1px solid #1f1f1f;
        }
        tr:hover td { background: #222; }
        .genre-badge {
            display: inline-block;
            padding: 2px 10px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: 500;
        }
        .bar-cell {
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .bar {
            height: 8px;
            border-radius: 4px;
            background: #6366f1;
        }
        .bar-label { font-size: 12px; color: #888; min-width: 45px; text-align: right; }
        .engagement-grid {
            display: grid;
            grid-template-columns: repeat(5, 1fr);
            gap: 12px;
        }
        .eng-box {
            text-align: center;
            padding: 16px 8px;
            border-radius: 8px;
            background: #222;
        }
        .eng-box .num { font-size: 24px; font-weight: 700; }
        .eng-box .lbl { font-size: 10px; color: #888; text-transform: uppercase; margin-top: 4px; }
        .eng-UNKNOWN .num { color: #6b7280; }
        .eng-BOUNCED .num { color: #ef4444; }
        .eng-WATCHED .num { color: #f59e0b; }
        .eng-LIKED .num { color: #22c55e; }
        .eng-CURATED .num { color: #6366f1; }
        .video-list { max-height: 1000px; overflow-y: auto; }
        #videoTable thead th { position: sticky; top: 0; background: #1a1a1a; z-index: 1; }
        #genreTable thead th { position: sticky; top: 0; background: #1a1a1a; z-index: 1; }
        #channelTable thead th { position: sticky; top: 0; background: #1a1a1a; z-index: 1; }
        .duration { color: #888; font-variant-numeric: tabular-nums; }
        .channel { color: #6b7280; }
        .filter-bar {
            display: flex;
            gap: 8px;
            margin-bottom: 16px;
            flex-wrap: wrap;
        }
        .filter-btn {
            padding: 4px 14px;
            border-radius: 16px;
            border: 1px solid #333;
            background: transparent;
            color: #ccc;
            cursor: pointer;
            font-size: 12px;
            transition: all 0.15s;
        }
        input[type="checkbox"] { accent-color: #6366f1; cursor: pointer; }
        .star-btn { cursor: pointer; font-size: 16px; color: #444; transition: color 0.15s; }
        .star-btn:hover { color: #f59e0b; }
        .star-btn.starred { color: #f59e0b; }
        ::-webkit-scrollbar { width: 8px; height: 8px; }
        ::-webkit-scrollbar-track { background: #1a1a1a; }
        ::-webkit-scrollbar-thumb { background: #333; border-radius: 4px; }
        ::-webkit-scrollbar-thumb:hover { background: #555; }
        * { scrollbar-width: thin; scrollbar-color: #333 #1a1a1a; }
    </style>
</head>
<body>
    <h1>yt-brain Dashboard</h1>
    <p class="subtitle">
        <span id="filteredCount">{{ total_videos }}</span> videos from your YouTube history &middot; <span id="dateRangeLabel">{{ date_range }}</span>
        &nbsp;
        <select id="yearFilter" onchange="applyFilters()" style="background:#222;color:#ccc;border:1px solid #444;border-radius:6px;padding:4px 8px;font-size:13px;cursor:pointer;">
            <option value="all">All time</option>
            <option value="1">Last 1 day</option>
            <option value="7">Last 1 week</option>
            <option value="30">Last 1 month</option>
            <option value="182">Last 6 months</option>
            <option value="365">Last 1 year</option>
            <option value="730">Last 2 years</option>
            <option value="1095">Last 3 years</option>
            <option value="1825">Last 5 years</option>
        </select>
    </p>

    <div class="stat-row">
        <div class="stat-box">
            <div class="number">{{ total_videos }}</div>
            <div class="label">Total Videos</div>
        </div>
        <div class="stat-box">
            <div class="number">{{ num_channels }}</div>
            <div class="label">Channels</div>
        </div>
        <div class="stat-box">
            <div class="number">{{ num_genres }}</div>
            <div class="label">Genres</div>
        </div>
        <div class="stat-box">
            <div class="number">{{ top_genre }}</div>
            <div class="label">Top Genre</div>
        </div>
    </div>

    <div class="grid">
        <div class="card">
            <h2>Genre Breakdown</h2>
            <div style="overflow-y:auto;flex:1">
            <table id="genreTable">
                <thead><tr>
                    <th style="width:28px"><input type="checkbox" id="genreSelectAll" checked onchange="toggleAllGenres(this.checked)" title="Select all / none"></th>
                    <th>Genre</th><th>Count</th><th></th>
                </tr></thead>
                <tbody>
                {% for s in stats %}
                <tr>
                    <td><input type="checkbox" class="genre-cb" value="{{ s.genre }}" checked onchange="applyFilters()"></td>
                    <td>{{ s.genre }}</td>
                    <td>{{ s.count }}</td>
                    <td>
                        <div class="bar-cell">
                            <div class="bar" style="width: {{ s.pct * 2 }}px"></div>
                            <span class="bar-label">{{ s.pct }}%</span>
                        </div>
                    </td>
                </tr>
                {% endfor %}
                </tbody>
            </table>
            </div>
        </div>

        <div class="card">
            <h2>Channel Breakdown</h2>
            <div style="overflow-y:auto;flex:1">
            <table id="channelTable">
                <thead><tr><th style="width:28px"><span id="starFilter" class="star-btn" onclick="toggleStarFilter()" title="Show starred only">&#9733;</span></th><th>Channel</th><th>Count</th><th></th></tr></thead>
                <tbody>
                {% for c in channel_stats %}
                <tr>
                    <td><span class="star-btn{% if c.starred %} starred{% endif %}" onclick="toggleStar(this, '{{ c.name | e }}')" title="Star channel">&#9733;</span></td>
                    <td><a href="{{ c.url or 'https://www.youtube.com/results?search_query=' + c.name|urlencode }}" target="_blank" style="color:#8b8bf5;text-decoration:none">{{ c.name }}</a></td>
                    <td>{{ c.count }}</td>
                    <td>
                        <div class="bar-cell">
                            <div class="bar" style="width: {{ c.pct * 2 }}px"></div>
                            <span class="bar-label">{{ c.pct }}%</span>
                        </div>
                    </td>
                </tr>
                {% endfor %}
                </tbody>
            </table>
            </div>
        </div>

        <div class="card full-width">
            <h2>All Videos</h2>
            <div style="display:flex;gap:12px;margin-bottom:12px">
                <input type="text" id="titleSearch" placeholder="Search titles..." oninput="applyFilters()" style="flex:1;padding:8px 12px;background:#222;color:#ccc;border:1px solid #333;border-radius:8px;font-size:13px;outline:none;" onfocus="this.style.borderColor='#6366f1'" onblur="this.style.borderColor='#333'">
                <input type="text" id="channelSearch" placeholder="Search channels..." oninput="applyFilters()" style="flex:1;padding:8px 12px;background:#222;color:#ccc;border:1px solid #333;border-radius:8px;font-size:13px;outline:none;" onfocus="this.style.borderColor='#6366f1'" onblur="this.style.borderColor='#333'">
            </div>
            <div class="video-list">
                <table id="videoTable">
                    <thead><tr><th>Title</th><th>Channel</th><th>Genre</th></tr></thead>
                    <tbody>
                    {% for v in videos %}
                    <tr data-genre="{{ v.genre }}" data-watched="{{ v.watched_at }}">
                        <td><a href="https://www.youtube.com/watch?v={{ v.id }}" target="_blank" style="color:#8b8bf5;text-decoration:none">{{ v.title[:65] }}</a></td>
                        <td class="channel"><a href="{{ v.channel_url or 'https://www.youtube.com/results?search_query=' + v.channel|urlencode }}" target="_blank" style="color:#6b7280;text-decoration:none">{{ v.channel[:20] }}</a></td>
                        <td><span class="genre-badge" style="background:{{ genre_colors.get(v.genre, '#333') }}22;color:{{ genre_colors.get(v.genre, '#888') }}">{{ v.genre }}</span></td>
                    </tr>
                    {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <script>
        const starredChannels = new Set({{ starred_json | safe }});
        const channelUrls = {{ channel_urls_json | safe }};

        let starFilterActive = false;

        function toggleStarFilter() {
            starFilterActive = !starFilterActive;
            document.getElementById('starFilter').classList.toggle('starred', starFilterActive);
            applyFilters();
        }

        function toggleStar(el, channelName) {
            fetch('/api/star', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({channel: channelName})
            }).then(r => r.json()).then(data => {
                el.classList.toggle('starred', data.starred);
                if (data.starred) starredChannels.add(channelName);
                else starredChannels.delete(channelName);
            });
        }

        function toggleAllGenres(checked) {
            document.querySelectorAll('.genre-cb').forEach(cb => cb.checked = checked);
            applyFilters();
        }

        function getSelectedGenres() {
            const cbs = document.querySelectorAll('.genre-cb:checked');
            return new Set(Array.from(cbs).map(cb => cb.value));
        }

        function applyFilters() {
            const days = document.getElementById('yearFilter').value;
            const now = new Date();
            let cutoff = null;
            if (days !== 'all') {
                cutoff = new Date(now.getTime() - parseInt(days) * 24 * 60 * 60 * 1000);
            }

            const searchTerm = (document.getElementById('titleSearch').value || '').toLowerCase();
            const selectedGenres = getSelectedGenres();
            const allCbs = document.querySelectorAll('.genre-cb');
            const selectAllCb = document.getElementById('genreSelectAll');
            selectAllCb.checked = selectedGenres.size === allCbs.length;
            selectAllCb.indeterminate = selectedGenres.size > 0 && selectedGenres.size < allCbs.length;

            const rows = document.querySelectorAll('#videoTable tbody tr');
            const genreCounts = {};
            const channelCounts = {};
            let visibleCount = 0;
            let minDate = null, maxDate = null;

            rows.forEach(row => {
                const watched = row.dataset.watched;
                const genre = row.dataset.genre;
                const channel = row.children[1]?.textContent || '';

                let dateOk = true;
                if (cutoff && watched) {
                    dateOk = new Date(watched) >= cutoff;
                } else if (cutoff && !watched) {
                    dateOk = false;
                }

                const genreOk = selectedGenres.has(genre);
                const title = (row.children[0]?.textContent || '').toLowerCase();
                const channelTerm = (document.getElementById('channelSearch').value || '').toLowerCase();
                const searchOk = !searchTerm || title.includes(searchTerm);
                const channelOk = !channelTerm || channel.toLowerCase().includes(channelTerm);
                const starOk = !starFilterActive || starredChannels.has(channel);
                const visible = dateOk && genreOk && searchOk && channelOk && starOk;
                row.style.display = visible ? '' : 'none';

                if (dateOk) {
                    genreCounts[genre] = (genreCounts[genre] || 0) + 1;
                    if (genreOk) {
                        visibleCount++;
                        if (channel) channelCounts[channel] = (channelCounts[channel] || 0) + 1;
                        if (watched) {
                            const d = new Date(watched);
                            if (!minDate || d < minDate) minDate = d;
                            if (!maxDate || d > maxDate) maxDate = d;
                        }
                    }
                }
            });

            // Update genre counts and re-sort by count desc, Other last
            const genreRows = Array.from(document.querySelectorAll('#genreTable tbody tr'));
            const totalForPct = Object.values(genreCounts).reduce((a,b)=>a+b, 0);
            genreRows.forEach(tr => {
                const genre = tr.children[1]?.textContent;
                const count = genreCounts[genre] || 0;
                tr.children[2].textContent = count;
                const pct = totalForPct ? (count/totalForPct*100).toFixed(1) : 0;
                const barCell = tr.children[3]?.querySelector('.bar-cell');
                if (barCell) {
                    barCell.querySelector('.bar').style.width = pct*2+'px';
                    barCell.querySelector('.bar-label').textContent = pct+'%';
                }
            });
            genreRows.sort((a, b) => {
                const aGenre = a.children[1]?.textContent;
                const bGenre = b.children[1]?.textContent;
                if (aGenre === 'Other') return 1;
                if (bGenre === 'Other') return -1;
                return (genreCounts[bGenre] || 0) - (genreCounts[aGenre] || 0);
            });
            const genreTbody = document.querySelector('#genreTable tbody');
            genreRows.forEach(tr => genreTbody.appendChild(tr));

            // Update stats
            document.getElementById('filteredCount').textContent = visibleCount;

            const statBoxes = document.querySelectorAll('.stat-box .number');
            statBoxes[0].textContent = visibleCount; // Total Videos
            statBoxes[1].textContent = Object.keys(channelCounts).length; // Channels
            statBoxes[2].textContent = Object.keys(genreCounts).length; // Genres

            // Top genre
            let topGenre = '-';
            let topCount = 0;
            for (const [g, c] of Object.entries(genreCounts)) {
                if (c > topCount) { topCount = c; topGenre = g; }
            }
            statBoxes[3].textContent = topGenre;

            // Date range
            const fmt = d => d.toLocaleDateString('en-US', {month:'short', day:'numeric', year:'numeric'});
            const rangeEl = document.getElementById('dateRangeLabel');
            if (minDate && maxDate) {
                rangeEl.textContent = minDate.toDateString() === maxDate.toDateString()
                    ? fmt(minDate) : fmt(minDate) + ' — ' + fmt(maxDate);
            } else {
                rangeEl.textContent = '-';
            }

            // Update channel breakdown table
            const chBody = document.getElementById('channelTable')?.querySelector('tbody');
            if (chBody) {
                const filtered = starFilterActive
                    ? Object.entries(channelCounts).filter(([name]) => starredChannels.has(name))
                    : Object.entries(channelCounts);
                const sorted = filtered.sort((a,b) => b[1]-a[1]);
                chBody.innerHTML = sorted.map(([name, count]) => {
                    const pct = visibleCount ? (count / visibleCount * 100).toFixed(1) : 0;
                    const url = channelUrls[name] || `https://www.youtube.com/results?search_query=${encodeURIComponent(name)}`;
                    const starred = starredChannels.has(name) ? ' starred' : '';
                    const eName = name.replace(/'/g, "\\'").replace(/"/g, '&quot;');
                    return `<tr><td><span class="star-btn${starred}" onclick="toggleStar(this, '${eName}')" title="Star channel">&#9733;</span></td><td><a href="${url}" target="_blank" style="color:#8b8bf5;text-decoration:none">${name}</a></td><td>${count}</td><td><div class="bar-cell"><div class="bar" style="width:${pct*2}px"></div><span class="bar-label">${pct}%</span></div></td></tr>`;
                }).join('');
            }
        }
    </script>
</body>
</html>
"""

GENRE_COLORS = {
    "AI/ML & LLMs": "#6366f1",
    "Programming & Dev Tools": "#22c55e",
    "Tech News & Industry": "#06b6d4",
    "Science & Education": "#f59e0b",
    "History & Documentary": "#ef4444",
    "Philosophy & Self-Improvement": "#8b5cf6",
    "Film, TV & Pop Culture": "#ec4899",
    "Music": "#f97316",
    "Gaming": "#14b8a6",
    "Finance & Business": "#0ea5e9",
    "Design & Creative": "#d946ef",
    "Food & Cooking": "#fbbf24",
    "Fitness & Health": "#84cc16",
    "Politics & Current Events": "#e11d48",
    "DIY & How-To": "#a855f7",
    "Other": "#6b7280",
}


def create_app() -> Flask:
    app = Flask(__name__)

    @app.route("/")
    def index():
        config = load_config()
        init_db(config.db_path)
        videos_raw = get_all_videos(config.db_path)
        channel_urls = get_channel_urls(config.db_path)

        videos = []
        for v in videos_raw:
            dur = v.duration_seconds
            if dur:
                m, s = divmod(dur, 60)
                dur_fmt = f"{m}:{s:02d}"
            else:
                dur_fmt = "-"

            videos.append({
                "id": v.youtube_id,
                "title": v.title,
                "channel": v.channel_id,
                "genre": v.category or classify_genre(v.title),
                "duration": v.duration_seconds,
                "duration_fmt": dur_fmt,
                "engagement": v.effective_engagement.value,
                "watched_at": v.watched_at.isoformat() if v.watched_at else "",
                "channel_url": channel_urls.get(v.channel_id, ""),
            })

        stats = genre_stats(videos)
        total = len(videos)
        total_hours = round(sum(v["duration"] or 0 for v in videos) / 3600, 1)
        top_genre = stats[0]["genre"] if stats else "-"

        # Date range
        conn = sqlite3.connect(config.db_path)
        try:
            row = conn.execute(
                "SELECT MIN(COALESCE(watched_at, updated_at)), MAX(COALESCE(watched_at, updated_at)) FROM videos"
            ).fetchone()
            if row and row[0] and row[1]:
                from datetime import datetime
                d_min = datetime.fromisoformat(row[0])
                d_max = datetime.fromisoformat(row[1])
                if d_min.date() == d_max.date():
                    date_range = d_min.strftime("%b %d, %Y")
                else:
                    date_range = f"{d_min.strftime('%b %d, %Y')} — {d_max.strftime('%b %d, %Y')}"
            else:
                date_range = "-"
        finally:
            conn.close()

        # Channel stats
        starred = get_starred_channels(config.db_path)
        channel_counts = Counter(v["channel"] for v in videos if v["channel"])
        channel_stats = []
        for name, count in channel_counts.most_common():
            channel_stats.append({
                "name": name,
                "count": count,
                "pct": round(count / total * 100, 1) if total else 0,
                "starred": name in starred,
                "url": channel_urls.get(name, ""),
            })

        engagement = {}
        for level in ["UNKNOWN", "BOUNCED", "WATCHED", "LIKED", "CURATED"]:
            engagement[level] = sum(1 for v in videos if v["engagement"] == level)

        # Duration buckets
        buckets = [
            ("< 2m", 0, 120),
            ("2-5m", 120, 300),
            ("5-10m", 300, 600),
            ("10-20m", 600, 1200),
            ("20-40m", 1200, 2400),
            ("40m-1h", 2400, 3600),
            ("> 1h", 3600, 999999),
        ]
        duration_buckets = []
        for label, lo, hi in buckets:
            count = sum(1 for v in videos if lo <= (v["duration"] or 0) < hi)
            duration_buckets.append({"label": label, "count": count})

        return render_template_string(
            TEMPLATE,
            videos=videos,
            stats=stats,
            stats_json=json.dumps(stats),
            total_videos=total,
            num_genres=len(stats),
            top_genre=top_genre,
            total_hours=total_hours,
            engagement=engagement,
            duration_buckets_json=json.dumps(duration_buckets),
            genre_colors=GENRE_COLORS,
            channel_stats=channel_stats,
            num_channels=len(channel_stats),
            date_range=date_range,
            starred_json=json.dumps(list(starred)),
            channel_urls_json=json.dumps(channel_urls),
        )

    @app.route("/api/star", methods=["POST"])
    def api_star():
        config = load_config()
        init_db(config.db_path)
        data = request.get_json()
        channel_name = data.get("channel", "")
        if not channel_name:
            return jsonify({"error": "missing channel"}), 400
        is_starred = toggle_starred_channel(config.db_path, channel_name)
        return jsonify({"starred": is_starred, "channel": channel_name})

    return app


def run_dashboard(port: int = 5555) -> None:
    app = create_app()
    app.run(host="127.0.0.1", port=port, debug=False)
