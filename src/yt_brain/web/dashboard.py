"""Flask dashboard for yt-brain."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from flask import Flask, render_template_string

from yt_brain.infrastructure.config import load_config
from yt_brain.infrastructure.database import get_all_videos, init_db

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
        }
        .card {
            background: #1a1a1a;
            border-radius: 12px;
            padding: 24px;
            border: 1px solid #2a2a2a;
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
        .video-list { max-height: 500px; overflow-y: auto; }
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
        .filter-btn:hover { border-color: #6366f1; color: #fff; }
        .filter-btn.active { background: #6366f1; border-color: #6366f1; color: #fff; }
    </style>
</head>
<body>
    <h1>yt-brain Dashboard</h1>
    <p class="subtitle">{{ total_videos }} videos analyzed from your YouTube history</p>

    <div class="stat-row">
        <div class="stat-box">
            <div class="number">{{ total_videos }}</div>
            <div class="label">Total Videos</div>
        </div>
        <div class="stat-box">
            <div class="number">{{ num_genres }}</div>
            <div class="label">Genres</div>
        </div>
        <div class="stat-box">
            <div class="number">{{ top_genre }}</div>
            <div class="label">Top Genre</div>
        </div>
        <div class="stat-box">
            <div class="number">{{ total_hours }}h</div>
            <div class="label">Watch Time</div>
        </div>
    </div>

    <div class="grid">
        <div class="card">
            <h2>Genre Distribution</h2>
            <div class="chart-container">
                <canvas id="genreDonut"></canvas>
            </div>
        </div>

        <div class="card">
            <h2>Genre Breakdown</h2>
            <table>
                <thead><tr><th>Genre</th><th>Count</th><th></th></tr></thead>
                <tbody>
                {% for s in stats %}
                <tr>
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

        <div class="card">
            <h2>Engagement Levels</h2>
            <div class="engagement-grid">
                {% for level, count in engagement.items() %}
                <div class="eng-box eng-{{ level }}">
                    <div class="num">{{ count }}</div>
                    <div class="lbl">{{ level }}</div>
                </div>
                {% endfor %}
            </div>
        </div>

        <div class="card">
            <h2>Duration Distribution</h2>
            <div class="chart-container">
                <canvas id="durationChart"></canvas>
            </div>
        </div>

        <div class="card full-width">
            <h2>All Videos</h2>
            <div class="filter-bar">
                <button class="filter-btn active" onclick="filterGenre('all')">All</button>
                {% for s in stats %}
                <button class="filter-btn" onclick="filterGenre('{{ s.genre }}')">{{ s.genre }} ({{ s.count }})</button>
                {% endfor %}
            </div>
            <div class="video-list">
                <table id="videoTable">
                    <thead><tr><th>Title</th><th>Channel</th><th>Genre</th><th>Duration</th><th>Engagement</th></tr></thead>
                    <tbody>
                    {% for v in videos %}
                    <tr data-genre="{{ v.genre }}">
                        <td><a href="https://www.youtube.com/watch?v={{ v.id }}" target="_blank" style="color:#8b8bf5;text-decoration:none">{{ v.title[:65] }}</a></td>
                        <td class="channel">{{ v.channel[:20] }}</td>
                        <td><span class="genre-badge" style="background:{{ genre_colors.get(v.genre, '#333') }}22;color:{{ genre_colors.get(v.genre, '#888') }}">{{ v.genre }}</span></td>
                        <td class="duration">{{ v.duration_fmt }}</td>
                        <td>{{ v.engagement }}</td>
                    </tr>
                    {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <script>
        const genreData = {{ stats_json | safe }};
        const colors = [
            '#6366f1','#22c55e','#f59e0b','#ef4444','#ec4899','#8b5cf6',
            '#06b6d4','#f97316','#14b8a6','#a855f7','#e11d48','#84cc16',
            '#0ea5e9','#d946ef','#fbbf24','#6b7280'
        ];

        new Chart(document.getElementById('genreDonut'), {
            type: 'doughnut',
            data: {
                labels: genreData.map(d => d.genre),
                datasets: [{
                    data: genreData.map(d => d.count),
                    backgroundColor: colors.slice(0, genreData.length),
                    borderWidth: 0,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '55%',
                plugins: {
                    legend: { position: 'right', labels: { color: '#ccc', font: { size: 11 }, padding: 12 } }
                }
            }
        });

        const durData = {{ duration_buckets_json | safe }};
        new Chart(document.getElementById('durationChart'), {
            type: 'bar',
            data: {
                labels: durData.map(d => d.label),
                datasets: [{
                    data: durData.map(d => d.count),
                    backgroundColor: '#6366f1',
                    borderRadius: 4,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    x: { ticks: { color: '#888' }, grid: { display: false } },
                    y: { ticks: { color: '#888' }, grid: { color: '#222' } }
                }
            }
        });

        function filterGenre(genre) {
            document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
            event.target.classList.add('active');
            document.querySelectorAll('#videoTable tbody tr').forEach(row => {
                row.style.display = (genre === 'all' || row.dataset.genre === genre) ? '' : 'none';
            });
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
                "genre": classify_genre(v.title),
                "duration": v.duration_seconds,
                "duration_fmt": dur_fmt,
                "engagement": v.effective_engagement.value,
            })

        stats = genre_stats(videos)
        total = len(videos)
        total_hours = round(sum(v["duration"] or 0 for v in videos) / 3600, 1)
        top_genre = stats[0]["genre"] if stats else "-"

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
        )

    return app


def run_dashboard(port: int = 5555) -> None:
    app = create_app()
    app.run(host="127.0.0.1", port=port, debug=False)
