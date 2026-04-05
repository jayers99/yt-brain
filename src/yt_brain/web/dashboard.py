"""Flask dashboard for yt-brain."""

from __future__ import annotations

import json
import sqlite3
from collections import Counter
from pathlib import Path

from flask import Flask, jsonify, render_template_string, request, send_from_directory

from yt_brain.infrastructure.config import load_config
from yt_brain.infrastructure.database import (
    get_all_videos,
    get_channel_urls,
    get_embedding_count,
    get_starred_channels,
    init_db,
    search_similar,
    toggle_starred_channel,
)

from .classifier import classify_genre, genre_stats


def is_removed_video(video: "Video") -> bool:
    """Return True if the video was removed/private on YouTube.

    Detected by Takeout storing the raw URL as the title when YouTube
    can't resolve the actual video title.
    """
    return video.title.startswith("https://www.youtube.com/watch?v=")


TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>yt-brain Dashboard</title>
    <link rel="apple-touch-icon" sizes="180x180" href="/images/apple-touch-icon.png">
    <link rel="icon" type="image/png" sizes="32x32" href="/images/favicon-32x32.png">
    <link rel="icon" type="image/png" sizes="16x16" href="/images/favicon-16x16.png">
    <link rel="icon" type="image/x-icon" href="/images/favicon.ico">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700;800&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
    <!-- chart.js removed — not used, saves ~200KB parse -->

    <style>
        :root {
            --bg-base: #0c0c0e;
            --bg-surface: #141418;
            --bg-elevated: #1a1a20;
            --bg-hover: #22222a;
            --border-subtle: #25252d;
            --border-default: #2e2e38;
            --text-primary: #f0f0f4;
            --text-secondary: #a0a0b0;
            --text-tertiary: #6a6a7a;
            --text-muted: #50505e;
            --accent: #6366f1;
            --accent-dim: #4f46e5;
            --accent-glow: rgba(99, 102, 241, 0.15);
            --accent-glow-strong: rgba(99, 102, 241, 0.25);
            --star-color: #f59e0b;
            --link-primary: #8b8bf5;
            --link-channel: #7a7a8e;
            --font-display: 'JetBrains Mono', 'SF Mono', 'Fira Code', monospace;
            --font-body: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
        }
        * { margin: 0; padding: 0; box-sizing: border-box; }
        html, body { overflow-x: hidden; width: 100%; max-width: 100vw; }
        body {
            font-family: var(--font-body);
            background: var(--bg-base);
            background-image:
                radial-gradient(ellipse 80% 50% at 50% -20%, rgba(99, 102, 241, 0.05), transparent),
                linear-gradient(180deg, #0c0c0e 0%, #0e0e12 100%);
            color: var(--text-secondary);
            padding: 32px 40px;
            min-height: 100vh;
        }
        .top-section {
            position: relative;
            overflow: hidden;
        }
        h1 {
            font-family: var(--font-display);
            font-size: 24px;
            font-weight: 700;
            margin-bottom: 8px;
            color: var(--text-primary);
            letter-spacing: -0.5px;
        }
        .subtitle {
            color: var(--text-tertiary);
            margin-bottom: 32px;
            font-size: 13px;
            letter-spacing: 0.2px;
        }
        .header-logo {
            position: absolute;
            top: 35%;
            right: 10px;
            transform: translateY(-50%);
            height: 180px;
            opacity: 0.85;
            filter: brightness(0.9) drop-shadow(0 4px 12px rgba(0,0,0,0.4));
            transition: transform 0.3s ease, filter 0.3s ease;
            z-index: 2;
        }
        .header-logo:hover {
            opacity: 0.8;
            transform: translateY(-50%) scale(1.04) rotate(-2deg);
            filter: brightness(0.9) drop-shadow(0 6px 20px rgba(99, 102, 241, 0.3));
        }
        .grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 24px;
            margin-bottom: 32px;
            align-items: stretch;
            overflow: hidden;
            width: calc(100vw - 80px);
            max-width: calc(100vw - 80px);
        }
        .card {
            background: var(--bg-surface);
            border-radius: 12px;
            padding: 24px;
            border: 1px solid var(--border-subtle);
            box-shadow: 0 2px 8px rgba(0,0,0,0.2), 0 1px 2px rgba(0,0,0,0.15);
            display: flex;
            flex-direction: column;
            max-height: 375px;
            overflow: hidden;
            min-width: 0;
            contain: layout style paint inline-size;
            will-change: transform;
            transition: box-shadow 0.2s ease, border-color 0.2s ease;
        }
        .card:hover {
            box-shadow: 0 4px 16px rgba(0,0,0,0.3), 0 2px 4px rgba(0,0,0,0.2);
            border-color: var(--border-default);
        }
        .card h2 {
            font-family: var(--font-display);
            font-size: 11px;
            font-weight: 500;
            margin-bottom: 16px;
            color: var(--text-tertiary);
            text-transform: uppercase;
            letter-spacing: 1.5px;
        }
        .stat-row {
            display: flex;
            gap: 20px;
            margin-bottom: 24px;
            padding-bottom: 28px;
            padding-right: 200px;
            border-bottom: 1px solid var(--border-subtle);
        }
        .stat-box {
            flex: 1;
            background: var(--bg-surface);
            border-radius: 10px;
            padding: 16px 20px;
            border: 1px solid var(--border-subtle);
            text-align: center;
            box-shadow:
                0 2px 8px rgba(0,0,0,0.2),
                inset 0 1px 0 rgba(255,255,255,0.03);
            background-image: linear-gradient(135deg, var(--bg-surface) 0%, var(--bg-elevated) 100%);
            position: relative;
            overflow: hidden;
            transition: box-shadow 0.25s ease, transform 0.2s ease;
        }
        .stat-box::before {
            content: '';
            position: absolute;
            inset: 0;
            border-radius: 12px;
            padding: 1px;
            background: linear-gradient(135deg, var(--accent-glow), transparent 60%);
            -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
            -webkit-mask-composite: xor;
            mask-composite: exclude;
            pointer-events: none;
        }
        .stat-box:hover {
            box-shadow:
                0 4px 16px rgba(0,0,0,0.3),
                0 0 20px var(--accent-glow);
            transform: translateY(-1px);
        }
        .stat-box .number {
            font-family: var(--font-display);
            font-size: 24px;
            font-weight: 800;
            color: var(--text-primary);
            letter-spacing: -1px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
            transition: color 0.3s ease;
        }
        .stat-box .label {
            font-size: 10px;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 1.5px;
            margin-top: 6px;
            font-weight: 500;
        }
        .chart-container {
            position: relative;
            height: 350px;
        }
        .full-width { grid-column: 1 / -1; }
        .card.card-primary {
            border-top: 2px solid var(--accent);
            background: linear-gradient(180deg, rgba(99, 102, 241, 0.03) 0%, var(--bg-surface) 80px);
        }
        table {
            width: 100%;
            border-collapse: collapse;
            font-size: 13px;
        }
        th {
            text-align: left;
            padding: 8px 12px;
            border-bottom: 1px solid var(--border-default);
            color: var(--text-muted);
            font-family: var(--font-display);
            font-weight: 500;
            font-size: 10px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        td {
            padding: 8px 12px;
            border-bottom: 1px solid rgba(255,255,255,0.03);
        }
        tr {
            transition: background 0.15s ease;
        }
        tr:hover td { background: var(--bg-hover); }
        #videoTable tbody tr {
            transition: opacity 0.2s ease, background 0.15s ease;
        }
        .genre-badge {
            display: inline-block;
            padding: 3px 12px;
            border-radius: 6px;
            font-size: 11px;
            font-weight: 600;
            letter-spacing: 0.3px;
        }
        .bar-cell {
            display: flex;
            align-items: center;
            gap: 6px;
            min-width: 0;
            overflow: hidden;
        }
        .bar-track {
            flex: 1;
            min-width: 0;
            height: 6px;
            border-radius: 3px;
            background: var(--bg-hover);
            overflow: hidden;
        }
        .bar {
            height: 100%;
            border-radius: 3px;
            background: var(--accent);
            transition: width 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        }
        .bar-label {
            flex-shrink: 0;
            min-width: 38px;
            font-family: var(--font-display);
            font-size: 11px;
            color: var(--text-muted);
            text-align: right;
        }
        .engagement-grid {
            display: grid;
            grid-template-columns: repeat(5, 1fr);
            gap: 12px;
        }
        .eng-box {
            text-align: center;
            padding: 16px 8px;
            border-radius: 8px;
            background: var(--bg-hover);
        }
        .eng-box .num { font-family: var(--font-display); font-size: 24px; font-weight: 700; }
        .eng-box .lbl { font-size: 10px; color: var(--text-muted); text-transform: uppercase; margin-top: 4px; }
        .eng-UNKNOWN .num { color: #6b7280; }
        .eng-BOUNCED .num { color: #ef4444; }
        .eng-WATCHED .num { color: #f59e0b; }
        .eng-LIKED .num { color: #22c55e; }
        .eng-CURATED .num { color: var(--accent); }
        .video-list { max-height: 700px; overflow-y: auto; overflow-x: hidden; width: 100%; min-width: 0; }
        .card.full-width { overflow: hidden; min-width: 0; width: 100%; max-width: calc(100vw - 80px); max-height: 750px; contain: inline-size; }
        .video-list table { table-layout: fixed; width: 100%; max-width: 100%; }
        /* Column widths set inline via colgroup */
        #videoTable td, #videoTable th { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 0; }
        #videoTable td a { display: block; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
        #videoTable thead tr:first-child th { position: sticky; top: 0; background: var(--bg-surface); z-index: 2; }
        #videoTable thead tr:last-child th { position: sticky; top: 45px; background: var(--bg-surface); z-index: 1; }
        /* Sortable headers */
        .sortable {
            cursor: pointer;
            user-select: none;
            position: relative;
        }
        .sortable:hover {
            color: var(--text-primary);
        }
        .sortable::after {
            content: '';
            margin-left: 4px;
            color: var(--text-muted);
            font-size: 10px;
        }
        .sortable.sort-asc::after {
            content: '▲';
            color: var(--accent);
        }
        .sortable.sort-desc::after {
            content: '▼';
            color: var(--accent);
        }
        /* Liked column */
        .liked-cell {
            text-align: center;
            font-size: 14px;
        }
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
        /* Date columns */
        .date-cell {
            font-variant-numeric: tabular-nums;
            font-size: 12px;
            color: var(--text-tertiary);
        }
        #genreTable td, #genreTable th { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
        #genreTable thead th { position: sticky; top: 0; background: var(--bg-surface); z-index: 1; }
        #channelTable td, #channelTable th { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
        #channelTable thead th { position: sticky; top: 0; background: var(--bg-surface); z-index: 1; }
        .duration { color: var(--text-muted); font-variant-numeric: tabular-nums; }
        .channel { color: var(--link-channel); }
        .link-title {
            color: var(--link-primary);
            text-decoration: none;
            transition: color 0.15s ease;
        }
        .link-title:hover { color: #a5a5ff; }
        .link-channel {
            color: var(--link-channel);
            text-decoration: none;
            transition: color 0.15s ease;
        }
        .link-channel:hover { color: var(--text-secondary); }
        .link-cluster {
            color: var(--text-tertiary);
            text-decoration: none;
            font-size: 11px;
            transition: color 0.15s ease;
        }
        .link-cluster:hover { color: var(--accent); }
        /* Topic Grid */
        .topic-breadcrumb {
            font-size: 13px;
            color: var(--text-tertiary);
            margin-bottom: 8px;
        }
        .topic-breadcrumb a {
            color: var(--accent);
            text-decoration: none;
        }
        .topic-breadcrumb a:hover { text-decoration: underline; }
        .topic-breadcrumb > span::before { content: '  \\203A  '; color: var(--text-tertiary); margin: 0 4px; }
        .topic-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
            gap: 12px;
        }
        .topic-card {
            background: var(--bg-elevated);
            border: 1px solid var(--border-default);
            border-radius: 8px;
            padding: 8px 14px;
            cursor: pointer;
            transition: border-color 0.15s, box-shadow 0.15s;
        }
        .topic-card:hover {
            border-color: var(--accent);
            box-shadow: 0 0 0 1px var(--accent);
        }
        .topic-card-name {
            font-weight: 600;
            font-size: 14px;
            color: var(--text-primary);
            margin-bottom: 5px;
        }
        .topic-card-meta {
            font-size: 11px;
            color: var(--text-tertiary);
        }
        .topic-card-preview {
            font-size: 11px;
            color: var(--text-secondary);
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        .topic-expanded-list {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-bottom: 12px;
        }
        .topic-expanded-list a {
            display: inline-block;
            padding: 6px 12px;
            background: var(--bg-elevated);
            border: 1px solid var(--border-default);
            border-radius: 16px;
            color: var(--text-secondary);
            text-decoration: none;
            font-size: 12px;
            transition: border-color 0.15s, color 0.15s;
        }
        .topic-expanded-list a:hover {
            border-color: var(--accent);
            color: var(--accent);
        }
        .topic-show-all {
            display: inline-block;
            font-size: 12px;
            color: var(--accent);
            text-decoration: none;
        }
        .topic-show-all:hover { text-decoration: underline; }
        .filter-bar {
            display: flex;
            gap: 8px;
            margin-bottom: 16px;
            flex-wrap: wrap;
        }
        .filter-btn {
            padding: 4px 14px;
            border-radius: 16px;
            border: 1px solid var(--border-default);
            background: transparent;
            color: var(--text-secondary);
            cursor: pointer;
            font-size: 12px;
            transition: all 0.15s;
        }
        input[type="checkbox"] { accent-color: var(--accent); cursor: pointer; }
        .star-btn { cursor: pointer; font-size: 16px; color: var(--text-muted); transition: color 0.2s ease, transform 0.15s ease; }
        .star-btn:hover { color: var(--star-color); transform: scale(1.15); }
        .star-btn.starred { color: var(--star-color); }
        .year-filter {
            background: var(--bg-elevated);
            color: var(--text-secondary);
            border: 1px solid var(--border-default);
            border-radius: 6px;
            padding: 4px 8px;
            font-size: 13px;
            font-family: var(--font-body);
            cursor: pointer;
            outline: none;
            transition: border-color 0.15s ease;
        }
        .year-filter:focus { border-color: var(--accent); }
        ::-webkit-scrollbar { width: 6px; height: 6px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: var(--border-default); border-radius: 3px; }
        ::-webkit-scrollbar-thumb:hover { background: var(--text-muted); }
        * { scrollbar-width: thin; scrollbar-color: var(--border-default) transparent; }
        .search-wrap { position: relative; overflow: hidden; max-width: 100%; width: 100%; min-width: 0; }
        .search-input {
            width: 100%;
            min-width: 0;
            max-width: 100%;
            padding: 8px 28px 8px 12px;
            background: var(--bg-elevated);
            color: var(--text-secondary);
            border: 1px solid var(--border-default);
            border-radius: 8px;
            font-size: 13px;
            font-family: var(--font-body);
            outline: none;
            transition: border-color 0.2s ease, box-shadow 0.2s ease;
        }
        .search-input:focus {
            border-color: var(--accent);
            box-shadow: 0 0 0 2px var(--accent-glow);
        }
        .clear-btn { position:absolute;right:8px;top:50%;transform:translateY(-50%);color:var(--text-muted);cursor:pointer;font-size:16px;line-height:1;display:none;transition:color 0.15s ease; }
        .clear-btn:hover { color:var(--text-secondary); }
        .search-wrap .search-input:not(:placeholder-shown) + .clear-btn { display:block; }
        .search-row { display: flex; align-items: center; gap: 12px; width: 100%; }
        .search-row .search-wrap { flex: 1; min-width: 0; }
        .slider-group { display: flex; align-items: center; gap: 6px; flex-shrink: 0; }
        .slider-group input[type="range"] { width: 120px; accent-color: var(--accent); cursor: pointer; }
        .slider-value { font-family: var(--font-mono); font-size: 12px; color: var(--text-muted); min-width: 35px; text-align: right; }
        #genreTable tbody tr {
            border-left: 3px solid transparent;
            transition: border-color 0.2s ease, background 0.15s ease;
        }
        #genreTable tbody tr:hover {
            border-left-color: var(--accent);
        }
        .card-scroll { overflow: hidden; flex: 1; }
        .card.scroll-active .card-scroll { overflow-y: auto; }
        .card.scroll-active { border-color: var(--accent-dim); box-shadow: 0 4px 16px rgba(0,0,0,0.3), 0 0 0 1px var(--accent-glow); }
        .card-scroll.has-overflow { position: relative; }
        .card-scroll.has-overflow::after {
            content: attr(data-more-hint);
            position: absolute; bottom: 0; left: 0; right: 0;
            height: 60px;
            background: linear-gradient(transparent, var(--bg-surface) 85%);
            display: flex; align-items: flex-end; justify-content: center;
            padding-bottom: 6px;
            font-size: 12px; color: var(--text-muted);
            pointer-events: none;
        }
        .card.scroll-active .card-scroll.has-overflow::after { display: none; }
        /* Virtual scroll handles off-screen rows — only ~50 in DOM at a time */
        /* Suppress ALL transitions during resize to avoid per-frame composite work */
        .resizing, .resizing * {
            transition: none !important;
        }
    </style>
</head>
<body>
    <div class="top-section">
        <img src="/images/yt-brain-toon-4.png" alt="yt-brain logo" class="header-logo">
        <h1>yt-brain Dashboard</h1>
        <p class="subtitle">
            <span id="filteredCount">{{ total_videos }}</span> videos from your YouTube history &middot; <span id="dateRangeLabel">{{ date_range }}</span>
            &nbsp;
            <select id="yearFilter" onchange="applyFilters()" class="year-filter">
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
            <div class="number">{{ top_genre }}</div>
            <div class="label">Top Genre</div>
        </div>
        <div class="stat-box">
            <div class="number">{{ num_genres }}</div>
            <div class="label">Genres</div>
        </div>
        <div class="stat-box">
            <div class="number">{{ num_channels }}</div>
            <div class="label">Channels</div>
        </div>
        <div class="stat-box">
            <div class="number">{{ total_videos }}</div>
            <div class="label">Total Videos</div>
        </div>
    </div>
    </div>

    <div class="grid">
        <div class="card">
            <h2>Genre Breakdown</h2>
            <div class="card-scroll">
            <table id="genreTable" style="table-layout:fixed;width:100%">
                <colgroup><col style="width:28px"><col style="width:35%"><col style="width:70px"><col></colgroup>
                <thead><tr>
                    <th><input type="checkbox" id="genreSelectAll" checked onchange="toggleAllGenres(this.checked)" title="Select all / none"></th>
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
                            <div class="bar-track"><div class="bar" style="width: {{ s.pct }}%"></div></div>
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
            <div class="card-scroll">
            <table id="channelTable" style="table-layout:fixed;width:100%">
                <colgroup><col style="width:28px"><col style="width:35%"><col style="width:70px"><col></colgroup>
                <thead><tr><th><span id="starFilter" class="star-btn" onclick="toggleStarFilter()" title="Show starred only">&#9733;</span></th><th>Channel</th><th>Count</th><th></th></tr></thead>
                <tbody>
                {% for c in channel_stats %}
                <tr>
                    <td><span class="star-btn{% if c.starred %} starred{% endif %}" onclick="toggleStar(this, '{{ c.name | e }}')" title="Star channel">&#9733;</span></td>
                    <td><a href="{{ c.url or 'https://www.youtube.com/results?search_query=' + c.name|urlencode }}" target="_blank" class="link-title">{{ c.name }}</a></td>
                    <td>{{ c.count }}</td>
                    <td>
                        <div class="bar-cell">
                            <div class="bar-track"><div class="bar" style="width: {{ c.pct }}%"></div></div>
                            <span class="bar-label">{{ c.pct }}%</span>
                        </div>
                    </td>
                </tr>
                {% endfor %}
                </tbody>
            </table>
            </div>
        </div>

        {% if topic_grid %}
        <div class="card card-primary full-width" id="topicGridCard">
            <div id="topicBreadcrumb" class="topic-breadcrumb" style="display:none">
                <a href="#" onclick="topicGridReset(); return false;">All</a>
                <span id="breadcrumbParent"></span>
                <span id="breadcrumbChild"></span>
            </div>
            <h2 id="topicGridTitle">Browse by Topic Clusters <span style="font-size:0.9em; font-weight:normal; opacity:0.7">({{ clustered_pct }}% of videos clustered)</span></h2>
            <div id="topicGrid" class="topic-grid">
                {% for cat, data in topic_grid %}
                <div class="topic-card" data-category="{{ cat }}">
                    <div class="topic-card-name">{{ cat }}</div>
                    <div class="topic-card-meta">{{ data.total }} videos &middot; {{ data.clusters|length }} clusters</div>
                </div>
                {% endfor %}
            </div>
            <div id="topicExpanded" class="topic-expanded" style="display:none">
                <div id="topicExpandedList" class="topic-expanded-list"></div>
                <a href="#" id="topicShowAll" class="topic-show-all" onclick="return false;">Show all videos</a>
            </div>
        </div>
        {% endif %}

        <div class="card card-primary full-width">
            <h2>All Videos</h2>
            <div class="video-list">
                <table id="videoTable">
                    <colgroup>
                        <col style="width:4%">
                        <col style="width:33%">
                        <col style="width:16%">
                        <col style="width:14%">
                        <col style="width:13%">
                        <col style="width:10%">
                        <col style="width:10%">
                    </colgroup>
                    <thead>
                        <tr>
                            <th colspan="7" style="padding-bottom:12px">
                              <div class="search-row">
                                <div class="search-wrap"><input type="text" id="semanticSearch" placeholder="{{ 'Search by topic, concept, or keyword...' if has_embeddings else 'Run yt-brain embed to enable semantic search' }}" {{ '' if has_embeddings else 'disabled' }} oninput="scheduleSemanticSearch()" class="search-input" style="width:100%"><span class="clear-btn" onclick="clearSearch()">&times;</span></div>
                                <div class="slider-group">
                                  <input type="range" id="distanceSlider" min="0.1" max="1.2" step="0.05" value="0.6" oninput="onDistanceSliderInput()">
                                  <span id="distanceValue" class="slider-value">0.60</span>
                                </div>
                              </div>
                            </th>
                        </tr>
                        <tr>
                            <th><span id="likedFilter" class="liked-btn" onclick="toggleLikedFilter()" title="Filter by liked status">&#x1F44D;</span></th>
                            <th class="sortable" data-sort="title" onclick="toggleSort('title')">Title</th>
                            <th class="sortable" data-sort="channel" onclick="toggleSort('channel')">Channel</th>
                            <th class="sortable" data-sort="genre" onclick="toggleSort('genre')">Genre</th>
                            <th class="sortable" data-sort="cluster" onclick="toggleSort('cluster')">Cluster</th>
                            <th class="sortable" data-sort="watched" onclick="toggleSort('watched')">Watched</th>
                            <th class="sortable" data-sort="published" onclick="toggleSort('published')">Published</th>
                        </tr>
                    </thead>
                    <tbody>
                    {% for v in videos %}
                    <tr data-genre="{{ v.genre }}" data-watched="{{ v.watched_at }}" data-id="{{ v.id }}" data-cluster="{{ v.cluster }}" data-liked="{{ v.liked }}" data-published="{{ v.published_at }}">
                        <td class="liked-cell">{% if v.liked == 'like' %}<span class="liked-icon liked">&#x1F44D;</span>{% elif v.liked == 'dislike' %}<span class="liked-icon disliked">&#x1F44E;</span>{% endif %}</td>
                        <td><a href="https://www.youtube.com/watch?v={{ v.id }}" target="_blank" class="link-title">{{ v.title }}</a></td>
                        <td class="channel"><a href="{{ v.channel_url or 'https://www.youtube.com/results?search_query=' + v.channel|urlencode }}" target="_blank" class="link-channel">{{ v.channel[:20] }}</a></td>
                        <td><span class="genre-badge" style="background:{{ genre_colors.get(v.genre, '#333') }}22;color:{{ genre_colors.get(v.genre, '#888') }}">{{ v.genre }}</span></td>
                        <td>{% if v.cluster %}<a href="#" class="link-cluster" onclick="filterByCluster('{{ v.cluster }}'); return false;">{{ v.cluster }}</a>{% endif %}</td>
                        <td class="date-cell">{{ v.watched_at[:10] if v.watched_at else '' }}</td>
                        <td class="date-cell">{{ v.published_at[:10] if v.published_at else '' }}</td>
                    </tr>
                    {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <script>
        // Suppress transitions during resize to avoid jank
        let resizeTimer;
        window.addEventListener('resize', () => {
            document.body.classList.add('resizing');
            clearTimeout(resizeTimer);
            resizeTimer = setTimeout(() => document.body.classList.remove('resizing'), 150);
        });

        const starredChannels = new Set({{ starred_json | safe }});
        const channelUrls = {{ channel_urls_json | safe }};

        let starFilterActive = false;
        let sortColumn = null;
        let sortDirection = null;
        let likedFilterState = null;

        // Pre-cache video data from DOM once, then remove rows for virtual scroll
        const videoRows = document.querySelectorAll('#videoTable tbody tr');
        const videoData = Array.from(videoRows).map((row, idx) => ({
            html: row.outerHTML,
            originalIndex: idx,
            id: row.dataset.id,
            genre: row.dataset.genre,
            cluster: row.dataset.cluster || '',
            liked: row.dataset.liked || '',
            watchedTs: row.dataset.watched ? new Date(row.dataset.watched).getTime() : null,
            watched: row.dataset.watched || '',
            published: row.dataset.published || '',
            title: (row.children[1]?.textContent || '').toLowerCase(),
            channel: row.children[2]?.textContent || '',
            channelLower: (row.children[2]?.textContent || '').toLowerCase(),
            visible: true,
        }));

        // Virtual scroll: only render rows in the viewport
        const ROW_HEIGHT = 37;
        const BUFFER_ROWS = 20;
        let filteredIndices = videoData.map((_, i) => i); // indices into videoData that pass filters
        const videoListEl = document.querySelector('.video-list');
        const tbody = document.querySelector('#videoTable tbody');

        // Clear server-rendered rows and set up virtual scroll spacer
        tbody.innerHTML = '';
        const spacerTop = document.createElement('tr');
        spacerTop.id = 'vScrollTop';
        spacerTop.innerHTML = '<td colspan="7" style="padding:0;border:0;height:0"></td>';
        const spacerBottom = document.createElement('tr');
        spacerBottom.id = 'vScrollBottom';
        spacerBottom.innerHTML = '<td colspan="7" style="padding:0;border:0;height:0"></td>';

        let lastRenderStart = -1;
        function renderVisibleRows() {
            const scrollTop = videoListEl.scrollTop;
            const viewportHeight = videoListEl.clientHeight;
            const totalRows = filteredIndices.length;
            const totalHeight = totalRows * ROW_HEIGHT;

            let startRow = Math.floor(scrollTop / ROW_HEIGHT) - BUFFER_ROWS;
            if (startRow < 0) startRow = 0;
            let endRow = Math.ceil((scrollTop + viewportHeight) / ROW_HEIGHT) + BUFFER_ROWS;
            if (endRow > totalRows) endRow = totalRows;

            // Skip re-render if window hasn't shifted
            if (startRow === lastRenderStart && tbody.children.length > 2) return;
            lastRenderStart = startRow;

            const topPad = startRow * ROW_HEIGHT;
            const bottomPad = (totalRows - endRow) * ROW_HEIGHT;

            const htmlParts = [];
            htmlParts.push('<tr id="vScrollTop"><td colspan="7" style="padding:0;border:0;height:' + topPad + 'px"></td></tr>');
            for (let i = startRow; i < endRow; i++) {
                htmlParts.push(videoData[filteredIndices[i]].html);
            }
            htmlParts.push('<tr id="vScrollBottom"><td colspan="7" style="padding:0;border:0;height:' + bottomPad + 'px"></td></tr>');
            tbody.innerHTML = htmlParts.join('');
        }

        videoListEl.addEventListener('scroll', renderVisibleRows);
        renderVisibleRows();

        // Cache DOM refs
        const yearFilterEl = document.getElementById('yearFilter');
        const semanticSearchEl = document.getElementById('semanticSearch');
        const selectAllCb = document.getElementById('genreSelectAll');
        const filteredCountEl = document.getElementById('filteredCount');
        const dateRangeEl = document.getElementById('dateRangeLabel');
        const statNumbers = document.querySelectorAll('.stat-box .number');
        const genreTbody = document.querySelector('#genreTable tbody');
        const channelTbody = document.getElementById('channelTable')?.querySelector('tbody');
        const genreCheckboxes = document.querySelectorAll('.genre-cb');

        // Semantic search state
        let semanticMatchIds = null;  // null = no search active, Set = matched IDs
        let semanticRankMap = null;   // null = no search, Map(id → rank) for relevance sort
        let semanticTimer = null;
        let activeClusterFilter = null;
        let activeParentFilter = null;
        let expandedCategory = null;  // currently expanded parent in topic grid

        // Topic Grid data and navigation
        const topicGridData = {{ topic_grid_json | safe }};

        // Reverse map: cluster slug → parent category
        const slugToCategory = {};
        for (const [cat, data] of Object.entries(topicGridData)) {
            for (const c of data.clusters) {
                slugToCategory[c.slug] = cat;
            }
        }

        // Cache topic card elements by category
        const topicCards = {};
        document.querySelectorAll('.topic-card[data-category]').forEach(card => {
            topicCards[card.dataset.category] = card;
        });

        // Event delegation for topic card clicks
        const topicGridEl = document.getElementById('topicGrid');
        if (topicGridEl) {
            topicGridEl.addEventListener('click', function(e) {
                const card = e.target.closest('.topic-card');
                if (card) expandCategory(card.dataset.category);
            });
        }

        function topicGridReset() {
            expandedCategory = null;
            document.getElementById('topicGrid').style.display = 'grid';
            document.getElementById('topicExpanded').style.display = 'none';
            document.getElementById('topicBreadcrumb').style.display = 'none';
            document.getElementById('topicGridTitle').style.display = '';
            document.getElementById('topicGridTitle').textContent = 'Browse by Topic Clusters';
            activeClusterFilter = null;
            activeParentFilter = null;
            semanticSearchEl.value = '';
            semanticMatchIds = null;
            applyFilters();
        }

        function _makeBreadcrumbParent(cat) {
            const a = document.createElement('a');
            a.href = '#';
            a.textContent = cat;
            a.addEventListener('click', function(e) { e.preventDefault(); expandCategory(cat); });
            const span = document.getElementById('breadcrumbParent');
            span.innerHTML = '';
            span.appendChild(a);
        }

        function _makeBreadcrumbParentForFilter(cat) {
            const a = document.createElement('a');
            a.href = '#';
            a.textContent = cat;
            a.addEventListener('click', function(e) { e.preventDefault(); expandCategory(cat); });
            const span = document.getElementById('breadcrumbParent');
            span.innerHTML = '';
            span.appendChild(a);
        }

        function expandCategory(cat) {
            const data = topicGridData[cat];
            if (!data) return;

            expandedCategory = cat;
            document.getElementById('topicGrid').style.display = 'none';
            document.getElementById('topicExpanded').style.display = 'block';
            document.getElementById('topicBreadcrumb').style.display = 'block';
            document.getElementById('topicGridTitle').style.display = 'none';
            _makeBreadcrumbParent(cat);
            document.getElementById('breadcrumbChild').innerHTML = '';

            // Don't filter yet - just show the expanded view
            activeClusterFilter = null;
            activeParentFilter = null;
            semanticSearchEl.value = '';
            semanticMatchIds = null;
            applyFilters();  // will call renderExpandedClusters via topic grid update
        }

        // Render child cluster pills using filtered counts
        function renderExpandedClusters(cat, clusterVideoCounts) {
            const data = topicGridData[cat];
            if (!data) return;

            const list = document.getElementById('topicExpandedList');
            list.innerHTML = '';
            let catTotal = 0;
            data.clusters.forEach(function(c) {
                const cnt = clusterVideoCounts[c.slug] || 0;
                if (cnt === 0) return;  // hide clusters with 0 matching videos
                catTotal += cnt;
                const a = document.createElement('a');
                a.href = '#';
                a.innerHTML = c.slug + ' <span style="color:var(--text-tertiary)">(' + cnt + ')</span>';
                a.addEventListener('click', function(e) { e.preventDefault(); selectChildCluster(cat, c.slug); });
                list.appendChild(a);
            });

            const showAll = document.getElementById('topicShowAll');
            showAll.textContent = 'Show all ' + catTotal + ' ' + cat + ' videos';
            showAll.onclick = function() { showParentVideos(cat); return false; };
        }

        function showParentVideos(cat) {
            const data = topicGridData[cat];
            if (!data) return;

            document.getElementById('topicBreadcrumb').style.display = 'block';
            _makeBreadcrumbParentForFilter(cat);
            document.getElementById('breadcrumbChild').innerHTML = '';

            // Filter to all clusters in this category
            const slugs = new Set(data.clusters.map(c => c.slug));
            activeParentFilter = slugs;
            activeClusterFilter = null;
            semanticSearchEl.value = 'category:' + cat;
            semanticMatchIds = null;
            applyFilters();
        }

        function selectChildCluster(cat, slug) {
            document.getElementById('topicBreadcrumb').style.display = 'block';
            _makeBreadcrumbParent(cat);
            const childSpan = document.getElementById('breadcrumbChild');
            childSpan.innerHTML = '';
            const s = document.createElement('span');
            s.style.color = 'var(--text-primary)';
            s.textContent = slug;
            childSpan.appendChild(s);

            activeClusterFilter = slug;
            activeParentFilter = null;
            semanticSearchEl.value = 'cluster:' + slug;
            semanticMatchIds = null;
            applyFilters();
        }

        function clearSearch() {
            semanticSearchEl.value = '';
            semanticSearchEl.focus();
            semanticMatchIds = null;
            semanticRankMap = null;
            activeClusterFilter = null;
            activeParentFilter = null;
            topicGridReset();
        }

        function filterByCluster(slug) {
            semanticSearchEl.value = 'cluster:' + slug;
            activeClusterFilter = slug;
            semanticMatchIds = null;
            applyFilters();
        }

        function toggleSort(column) {
            if (sortColumn === column) {
                if (sortDirection === 'asc') sortDirection = 'desc';
                else if (sortDirection === 'desc') { sortDirection = null; sortColumn = null; }
            } else {
                sortColumn = column;
                sortDirection = 'asc';
            }

            // Update header indicators
            document.querySelectorAll('.sortable').forEach(th => {
                th.classList.remove('sort-asc', 'sort-desc');
            });
            if (sortColumn && sortDirection) {
                const activeTh = document.querySelector(`.sortable[data-sort="${sortColumn}"]`);
                if (activeTh) activeTh.classList.add('sort-' + sortDirection);
            }

            applySortAndFilters();
        }

        function applySortAndFilters() {
            if (sortColumn && sortDirection) {
                const dir = sortDirection === 'asc' ? 1 : -1;
                videoData.sort((a, b) => {
                    let va, vb;
                    if (sortColumn === 'title') { va = a.title; vb = b.title; }
                    else if (sortColumn === 'channel') { va = a.channelLower; vb = b.channelLower; }
                    else if (sortColumn === 'genre') { va = a.genre.toLowerCase(); vb = b.genre.toLowerCase(); }
                    else if (sortColumn === 'cluster') { va = a.cluster.toLowerCase(); vb = b.cluster.toLowerCase(); }
                    else if (sortColumn === 'watched') { va = a.watched; vb = b.watched; }
                    else if (sortColumn === 'published') { va = a.published; vb = b.published; }
                    else return 0;

                    // Empty values sort last regardless of direction
                    if (!va && !vb) return 0;
                    if (!va) return 1;
                    if (!vb) return -1;
                    if (va < vb) return -dir;
                    if (va > vb) return dir;
                    return 0;
                });
            } else if (semanticRankMap && semanticRankMap.size > 0) {
                // Sort by search relevance when semantic search is active
                const maxRank = semanticRankMap.size;
                videoData.sort((a, b) => {
                    const ra = semanticRankMap.has(a.id) ? semanticRankMap.get(a.id) : maxRank;
                    const rb = semanticRankMap.has(b.id) ? semanticRankMap.get(b.id) : maxRank;
                    return ra - rb;
                });
            } else {
                videoData.sort((a, b) => a.originalIndex - b.originalIndex);
            }

            // Rebuild filtered indices after sort reorder
            applyFilters();
        }

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

        function scheduleSemanticSearch() {
            if (semanticTimer) clearTimeout(semanticTimer);
            const q = semanticSearchEl.value.trim();
            if (!q) {
                semanticMatchIds = null;
                semanticRankMap = null;
                activeClusterFilter = null;
                activeParentFilter = null;
                applySortAndFilters();
                return;
            }
            // Check for category: filter (from parent click)
            if (q.startsWith('category:')) {
                return; // Already handled by showParentVideos
            }
            // Check for cluster: filter
            const clusterMatch = q.match(/^cluster:([^ ]+)$/);
            if (clusterMatch) {
                activeClusterFilter = clusterMatch[1];
                activeParentFilter = null;
                semanticMatchIds = null;
                applyFilters();
                return;
            }
            activeClusterFilter = null;
            activeParentFilter = null;
            // Debounce 150ms for API call (model is preloaded)
            semanticTimer = setTimeout(() => {
                fetch('/api/search?q=' + encodeURIComponent(q) + '&limit=200')
                    .then(r => r.json())
                    .then(data => {
                        if (data.results && data.results.length > 0) {
                            semanticMatchIds = new Set(data.results.map(r => r.youtube_id));
                            semanticRankMap = new Map(data.results.map((r, i) => [r.youtube_id, i]));
                        } else {
                            semanticMatchIds = new Set();  // empty = nothing matches
                            semanticRankMap = new Map();
                        }
                        applySortAndFilters();
                    })
                    .catch(() => {
                        semanticMatchIds = null;
                        semanticRankMap = null;
                        applySortAndFilters();
                    });
            }, 300);
        }

        // Debounce for non-search filters
        let filterRafId = null;
        function scheduleFilter() {
            if (filterRafId) cancelAnimationFrame(filterRafId);
            filterRafId = requestAnimationFrame(applyFilters);
        }

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
            genreCheckboxes.forEach(cb => cb.checked = checked);
            applyFilters();
        }

        function applyFilters() {
            filterRafId = null;
            const days = yearFilterEl.value;
            let cutoffTs = null;
            if (days !== 'all') {
                cutoffTs = Date.now() - parseInt(days) * 86400000;
            }

            const selectedGenres = new Set();
            let checkedCount = 0;
            genreCheckboxes.forEach(cb => {
                if (cb.checked) { selectedGenres.add(cb.value); checkedCount++; }
            });
            selectAllCb.checked = checkedCount === genreCheckboxes.length;
            selectAllCb.indeterminate = checkedCount > 0 && checkedCount < genreCheckboxes.length;

            const genreCounts = {};
            const channelCounts = {};
            let visibleCount = 0;
            let minTs = Infinity, maxTs = -Infinity;

            filteredIndices = [];
            for (let i = 0, len = videoData.length; i < len; i++) {
                const v = videoData[i];

                const dateOk = cutoffTs === null
                    ? true
                    : (v.watchedTs !== null && v.watchedTs >= cutoffTs);

                const searchOk = activeClusterFilter
                    ? v.cluster === activeClusterFilter
                    : activeParentFilter
                        ? activeParentFilter.has(v.cluster)
                        : (semanticMatchIds === null || semanticMatchIds.has(v.id));
                const starOk = !starFilterActive || starredChannels.has(v.channel);
                const likedOk = likedFilterState === null || v.liked === likedFilterState;
                const genreOk = selectedGenres.has(v.genre);
                const passesNonGenre = dateOk && searchOk && starOk && likedOk;
                const visible = passesNonGenre && genreOk;

                if (visible) filteredIndices.push(i);

                if (passesNonGenre) {
                    genreCounts[v.genre] = (genreCounts[v.genre] || 0) + 1;
                }

                if (visible) {
                    visibleCount++;
                    if (v.channel) channelCounts[v.channel] = (channelCounts[v.channel] || 0) + 1;
                    if (v.watchedTs !== null) {
                        if (v.watchedTs < minTs) minTs = v.watchedTs;
                        if (v.watchedTs > maxTs) maxTs = v.watchedTs;
                    }
                }
            }
            lastRenderStart = -1; // force re-render
            renderVisibleRows();

            // Update genre counts and re-sort
            const genreRows = Array.from(genreTbody.children);
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
            const frag = document.createDocumentFragment();
            genreRows.forEach(tr => frag.appendChild(tr));
            genreTbody.appendChild(frag);

            // Update stats (order: Top Genre, Genres, Channels, Total Videos)
            filteredCountEl.textContent = visibleCount;

            let topGenre = '-';
            let topCount = 0;
            for (const g in genreCounts) {
                if (genreCounts[g] > topCount) { topCount = genreCounts[g]; topGenre = g; }
            }
            statNumbers[0].textContent = topGenre;
            statNumbers[1].textContent = Object.keys(genreCounts).length;
            statNumbers[2].textContent = Object.keys(channelCounts).length;
            statNumbers[3].textContent = visibleCount;

            // Date range
            if (minTs !== Infinity && maxTs !== -Infinity) {
                const fmt = d => d.toLocaleDateString('en-US', {month:'short', day:'numeric', year:'numeric'});
                const minD = new Date(minTs), maxD = new Date(maxTs);
                dateRangeEl.textContent = minD.toDateString() === maxD.toDateString()
                    ? fmt(minD) : fmt(minD) + ' — ' + fmt(maxD);
            } else {
                dateRangeEl.textContent = '-';
            }

            // Update channel breakdown table
            if (channelTbody) {
                const entries = Object.entries(channelCounts);
                const filtered = starFilterActive
                    ? entries.filter(([name]) => starredChannels.has(name))
                    : entries;
                filtered.sort((a,b) => b[1]-a[1]);
                channelTbody.innerHTML = filtered.map(([name, count]) => {
                    const pct = visibleCount ? (count / visibleCount * 100).toFixed(1) : 0;
                    const url = channelUrls[name] || `https://www.youtube.com/results?search_query=${encodeURIComponent(name)}`;
                    const starred = starredChannels.has(name) ? ' starred' : '';
                    const eName = name.replace(/'/g, "\\'").replace(/"/g, '&quot;');
                    return `<tr><td><span class="star-btn${starred}" onclick="toggleStar(this, '${eName}')" title="Star channel">&#9733;</span></td><td><a href="${url}" target="_blank" class="link-title">${name}</a></td><td>${count}</td><td><div class="bar-cell"><div class="bar-track"><div class="bar" style="width:${pct}%"></div></div><span class="bar-label">${pct}%</span></div></td></tr>`;
                }).join('');
            }

            // Update topic grid counts based on filtered videos
            if (topicGridEl) {
                // Count videos per cluster that pass non-cluster filters (genre + date + star + search)
                const clusterVideoCounts = {};
                for (let i = 0, len = videoData.length; i < len; i++) {
                    const v = videoData[i];
                    if (!v.cluster) continue;
                    const dateOk2 = cutoffTs === null || (v.watchedTs !== null && v.watchedTs >= cutoffTs);
                    const starOk2 = !starFilterActive || starredChannels.has(v.channel);
                    const genreOk2 = selectedGenres.has(v.genre);
                    if (dateOk2 && starOk2 && genreOk2) {
                        clusterVideoCounts[v.cluster] = (clusterVideoCounts[v.cluster] || 0) + 1;
                    }
                }

                // Aggregate by parent category
                for (const [cat, card] of Object.entries(topicCards)) {
                    const data = topicGridData[cat];
                    if (!data) continue;
                    let catTotal = 0;
                    let catClusters = 0;
                    for (const c of data.clusters) {
                        const cnt = clusterVideoCounts[c.slug] || 0;
                        if (cnt > 0) catClusters++;
                        catTotal += cnt;
                    }
                    const meta = card.querySelector('.topic-card-meta');
                    if (meta) {
                        meta.textContent = catTotal + ' videos \u00b7 ' + catClusters + ' clusters';
                    }
                    card.style.display = catTotal > 0 ? '' : 'none';
                }

                // Update expanded child cluster pills if a category is open
                if (expandedCategory) {
                    renderExpandedClusters(expandedCategory, clusterVideoCounts);
                }
            }
        }
    /* Click-to-activate scroll for genre/channel cards */
    (function() {
        var cards = document.querySelectorAll('.card-scroll');
        var activatable = [];
        cards.forEach(function(el) {
            var card = el.closest('.card');
            if (card && !card.querySelector('.video-list')) activatable.push(card);
            // Add overflow hint if content is clipped
            if (el.scrollHeight > el.clientHeight) {
                var totalRows = el.querySelectorAll('tbody tr').length;
                var visibleRows = Math.floor(el.clientHeight / (el.querySelector('tbody tr') ? el.querySelector('tbody tr').offsetHeight : 30));
                var moreCount = totalRows - visibleRows;
                if (moreCount > 0) {
                    el.classList.add('has-overflow');
                    el.setAttribute('data-more-hint', 'Click to scroll (' + moreCount + ' more)');
                }
            }
        });
        function deactivateAll() {
            activatable.forEach(function(c) { c.classList.remove('scroll-active'); });
        }
        activatable.forEach(function(card) {
            card.addEventListener('click', function(e) {
                if (e.target.closest('a[href]')) return;
                e.stopPropagation();
                if (card.classList.contains('scroll-active')) {
                    card.classList.remove('scroll-active');
                    return;
                }
                deactivateAll();
                card.classList.add('scroll-active');
            });
        });
        document.addEventListener('click', function(e) {
            var inside = false;
            activatable.forEach(function(c) { if (c.contains(e.target)) inside = true; });
            if (!inside) deactivateAll();
        });
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') deactivateAll();
        });
    })();
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
        # Exclude removed/private videos (title is the raw YouTube URL)
        videos_raw = [v for v in videos_raw if not is_removed_video(v)]
        channel_urls = get_channel_urls(config.db_path)

        # Load cluster slugs for all videos
        from yt_brain.infrastructure.database import get_all_video_cluster_slugs, get_clusters_by_category
        cluster_slugs = get_all_video_cluster_slugs(config.db_path)

        # Load liked status and published dates
        import sqlite3 as _sqlite3
        _conn = _sqlite3.connect(config.db_path)
        try:
            _liked_map = {r[0]: r[1] for r in _conn.execute("SELECT youtube_id, liked FROM videos WHERE liked IS NOT NULL").fetchall()}
            _published_map = {r[0]: r[1] for r in _conn.execute("SELECT youtube_id, published_at FROM videos WHERE published_at IS NOT NULL").fetchall()}
        finally:
            _conn.close()

        # Build topic grid data: {category: [{slug, count}, ...]}
        clusters_raw = get_clusters_by_category(config.db_path)
        topic_grid = {}
        for c in clusters_raw:
            # Skip numeric fallback clusters (cluster-01, cluster-02, etc.)
            import re as _re
            if _re.match(r"^cluster-\d+$", c["slug"]):
                continue
            cat = c["parent_category"]
            if cat not in topic_grid:
                topic_grid[cat] = {"clusters": [], "total": 0}
            topic_grid[cat]["clusters"].append({"slug": c["slug"], "count": c["count"]})
            topic_grid[cat]["total"] += c["count"]
        # Sort categories by total video count descending
        topic_grid_sorted = sorted(topic_grid.items(), key=lambda x: x[1]["total"], reverse=True)

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
                "cluster": cluster_slugs.get(v.youtube_id, ""),
                "liked": _liked_map.get(v.youtube_id, ""),
                "published_at": _published_map.get(v.youtube_id, ""),
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

        has_embeddings = get_embedding_count(config.db_path) > 0
        clustered_count = sum(1 for v in videos if v["cluster"])
        clustered_pct = round(clustered_count / total * 100) if total else 0

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
            has_embeddings=has_embeddings,
            clustered_pct=clustered_pct,
            topic_grid=topic_grid_sorted,
            topic_grid_json=json.dumps(
                {cat: {"clusters": data["clusters"], "total": data["total"]}
                 for cat, data in topic_grid_sorted}
            ),
        )

    @app.route("/images/<path:filename>")
    def serve_image(filename: str):
        images_dir = Path(__file__).parent / "static" / "images"
        return send_from_directory(images_dir, filename)

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

    # Preload embedding model at startup if embeddings exist
    config = load_config()
    if get_embedding_count(config.db_path) > 0:
        import struct as _struct

        from sentence_transformers import SentenceTransformer as _ST

        app._embed_model = _ST("all-MiniLM-L6-v2")
        app._struct = _struct

    @app.route("/api/search")
    def api_search():
        import re

        config = load_config()

        q = request.args.get("q", "").strip()
        limit = min(int(request.args.get("limit", 50)), 200)
        max_distance = float(request.args.get("max_distance", 0.6))
        if not q:
            return jsonify({"results": []})

        if not hasattr(app, "_embed_model"):
            return jsonify({"results": [], "error": "No embeddings. Run: yt-brain embed"}), 200

        # Extract field-specific filters: title:"x", desc:"x", channel:"x"
        # and bare quoted terms: "x" (matches title or description)
        field_filters = []  # list of (field, term_lower)
        for match in re.finditer(r'(title|desc|channel):"([^"]+)"', q):
            field_filters.append((match.group(1), match.group(2).lower()))
        bare_quotes = [t.lower() for t in re.findall(r'(?<![\w:])\"([^"]+)\"', re.sub(r'(title|desc|channel):"[^"]*"', '', q))]

        has_filters = bool(field_filters or bare_quotes)

        # Strip all filter syntax to get the semantic query
        semantic_q = re.sub(r'(title|desc|channel):"[^"]*"', '', q)
        semantic_q = re.sub(r'"[^"]*"', '', semantic_q).strip()

        if not semantic_q and has_filters:
            terms = [t for _, t in field_filters] + bare_quotes
            semantic_q = " ".join(terms)

        embedding = app._embed_model.encode(semantic_q)
        query_blob = app._struct.pack(f"{len(embedding)}f", *embedding.tolist())

        fetch_limit = limit * 5 if has_filters else limit
        results = search_similar(config.db_path, query_blob, limit=fetch_limit)

        if has_filters:
            conn = sqlite3.connect(config.db_path)
            try:
                filtered = []
                for vid, dist in results:
                    row = conn.execute(
                        "SELECT title, description, channel_id FROM videos WHERE youtube_id = ?", (vid,)
                    ).fetchone()
                    if not row:
                        continue
                    title_l, desc_l, channel_l = row[0].lower(), row[1].lower(), row[2].lower()

                    ok = True
                    for field, term in field_filters:
                        if field == "title" and term not in title_l:
                            ok = False
                        elif field == "desc" and term not in desc_l:
                            ok = False
                        elif field == "channel" and term not in channel_l:
                            ok = False
                    for term in bare_quotes:
                        if term not in title_l and term not in desc_l:
                            ok = False

                    if ok:
                        filtered.append((vid, dist))
                        if len(filtered) >= limit:
                            break
            finally:
                conn.close()
            results = filtered

        # Filter by distance cutoff
        results = [(vid, dist) for vid, dist in results if dist <= max_distance]

        return jsonify({
            "results": [{"youtube_id": vid, "distance": dist} for vid, dist in results]
        })

    return app


def run_dashboard(port: int = 5555, open_browser: bool = False) -> None:
    import signal
    import sys
    import threading
    import webbrowser

    def _handle_sigint(sig: int, frame: object) -> None:
        print("\nShutting down dashboard...")
        sys.exit(0)

    signal.signal(signal.SIGINT, _handle_sigint)

    app = create_app()

    if open_browser:
        url = f"http://127.0.0.1:{port}"

        def _open_browser() -> None:
            import urllib.request
            for _ in range(30):
                try:
                    urllib.request.urlopen(url, timeout=1)
                    webbrowser.open(url)
                    return
                except Exception:
                    import time
                    time.sleep(0.5)

        threading.Thread(target=_open_browser, daemon=True).start()

    app.run(host="127.0.0.1", port=port, debug=False, use_reloader=False)
