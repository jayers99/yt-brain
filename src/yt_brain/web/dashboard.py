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
    get_starred_channels,
    init_db,
    toggle_starred_channel,
)

from .classifier import classify_genre, genre_stats

TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>yt-brain Dashboard</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700;800&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4"></script>
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
            max-height: 500px;
            overflow: hidden;
            min-width: 0;
            contain: inline-size;
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
        }
        .bar {
            height: 100%;
            border-radius: 3px;
            background: var(--accent);
            transition: width 0.4s cubic-bezier(0.4, 0, 0.2, 1);
            box-shadow: 0 0 6px var(--accent-glow);
        }
        .bar-label {
            flex-shrink: 0;
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
        .video-list { max-height: 1000px; overflow-y: auto; overflow-x: hidden; width: 100%; min-width: 0; }
        .card.full-width { overflow: hidden; min-width: 0; width: 100%; max-width: calc(100vw - 80px); contain: inline-size; }
        .video-list table { table-layout: fixed; width: 100%; max-width: 100%; }
        #videoTable col.col-title { width: 55%; }
        #videoTable col.col-channel { width: 25%; }
        #videoTable col.col-genre { width: 20%; }
        #videoTable td, #videoTable th { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 0; }
        #videoTable td a { display: block; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
        #videoTable thead tr:first-child th { position: sticky; top: 0; background: var(--bg-surface); z-index: 2; }
        #videoTable thead tr:last-child th { position: sticky; top: 45px; background: var(--bg-surface); z-index: 1; }
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
        #genreTable tbody tr {
            border-left: 3px solid transparent;
            transition: border-color 0.2s ease, background 0.15s ease;
        }
        #genreTable tbody tr:hover {
            border-left-color: var(--accent);
        }
        .card-scroll { overflow-y: auto; flex: 1; }
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

        <div class="card card-primary full-width">
            <h2>All Videos</h2>
            <div class="video-list">
                <table id="videoTable">
                    <colgroup>
                        <col class="col-title">
                        <col class="col-channel">
                        <col class="col-genre">
                    </colgroup>
                    <thead>
                        <tr>
                            <th style="padding-bottom:12px"><div class="search-wrap"><input type="text" id="titleSearch" placeholder="Search titles..." oninput="scheduleFilter()" class="search-input"><span class="clear-btn" onclick="clearInput('titleSearch')">&times;</span></div></th>
                            <th colspan="2" style="padding-bottom:12px"><div class="search-wrap"><input type="text" id="channelSearch" placeholder="Search channels..." oninput="scheduleFilter()" class="search-input"><span class="clear-btn" onclick="clearInput('channelSearch')">&times;</span></div></th>
                        </tr>
                        <tr><th>Title</th><th>Channel</th><th>Genre</th></tr>
                    </thead>
                    <tbody>
                    {% for v in videos %}
                    <tr data-genre="{{ v.genre }}" data-watched="{{ v.watched_at }}">
                        <td><a href="https://www.youtube.com/watch?v={{ v.id }}" target="_blank" class="link-title">{{ v.title }}</a></td>
                        <td class="channel"><a href="{{ v.channel_url or 'https://www.youtube.com/results?search_query=' + v.channel|urlencode }}" target="_blank" class="link-channel">{{ v.channel[:20] }}</a></td>
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

        // Pre-cache video data from DOM once — avoids DOM reads in filter loop
        const videoRows = document.querySelectorAll('#videoTable tbody tr');
        const videoData = Array.from(videoRows).map(row => ({
            row,
            genre: row.dataset.genre,
            watchedTs: row.dataset.watched ? new Date(row.dataset.watched).getTime() : null,
            title: (row.children[0]?.textContent || '').toLowerCase(),
            channel: row.children[1]?.textContent || '',
            channelLower: (row.children[1]?.textContent || '').toLowerCase(),
        }));

        // Cache DOM refs
        const yearFilterEl = document.getElementById('yearFilter');
        const titleSearchEl = document.getElementById('titleSearch');
        const channelSearchEl = document.getElementById('channelSearch');
        const selectAllCb = document.getElementById('genreSelectAll');
        const filteredCountEl = document.getElementById('filteredCount');
        const dateRangeEl = document.getElementById('dateRangeLabel');
        const statNumbers = document.querySelectorAll('.stat-box .number');
        const genreTbody = document.querySelector('#genreTable tbody');
        const channelTbody = document.getElementById('channelTable')?.querySelector('tbody');
        const genreCheckboxes = document.querySelectorAll('.genre-cb');

        // Debounce for text inputs
        let filterRafId = null;
        function clearInput(id) {
            const el = document.getElementById(id);
            el.value = '';
            el.focus();
            applyFilters();
        }

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

            const searchTerm = titleSearchEl.value.toLowerCase();
            const channelTerm = channelSearchEl.value.toLowerCase();
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

            for (let i = 0, len = videoData.length; i < len; i++) {
                const v = videoData[i];

                const dateOk = cutoffTs === null
                    ? true
                    : (v.watchedTs !== null && v.watchedTs >= cutoffTs);

                const searchOk = !searchTerm || v.title.includes(searchTerm);
                const channelOk = !channelTerm || v.channelLower.includes(channelTerm);
                const starOk = !starFilterActive || starredChannels.has(v.channel);
                const genreOk = selectedGenres.has(v.genre);
                const passesNonGenre = dateOk && searchOk && channelOk && starOk;
                const visible = passesNonGenre && genreOk;

                v.row.style.display = visible ? '' : 'none';

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

    return app


def run_dashboard(port: int = 5555) -> None:
    app = create_app()
    app.run(host="127.0.0.1", port=port, debug=False)
