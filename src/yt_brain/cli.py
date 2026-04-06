from __future__ import annotations

from datetime import UTC
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from yt_brain.domain.models import EngagementLevel

app = typer.Typer(
    name="yt-brain",
    help="YouTube knowledge brain — ingest, classify, and curate your YouTube activity.",
    no_args_is_help=True,
)

ingest_app = typer.Typer(help="Ingest YouTube data from various sources.")
app.add_typer(ingest_app, name="ingest")

console = Console()
err_console = Console(stderr=True)


def _get_db_path() -> Path:
    from yt_brain.infrastructure.config import load_config

    config = load_config()
    config.config_dir.mkdir(parents=True, exist_ok=True)
    return config.db_path


def _ensure_db(db_path: Path) -> None:
    from yt_brain.infrastructure.database import init_db

    init_db(db_path)


@app.callback()
def main() -> None:
    """yt-brain - YouTube Knowledge Brain."""
    pass


@ingest_app.command("takeout")
def ingest_takeout(
    path: Annotated[Path, typer.Argument(help="Path to Google Takeout export directory or watch-history.json")],
) -> None:
    """Import YouTube history from a Google Takeout export."""
    from yt_brain.application.ingest import ingest_takeout as do_ingest

    db_path = _get_db_path()
    _ensure_db(db_path)

    try:
        count = do_ingest(db_path, path)
        console.print(f"[green]Ingested {count} videos from Takeout.[/green]")
    except Exception as e:
        err_console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1) from None


@ingest_app.command("video")
def ingest_video(
    url: Annotated[str, typer.Argument(help="YouTube video URL")],
) -> None:
    """Add a single video by URL."""
    from yt_brain.application.ingest import ingest_video as do_ingest

    db_path = _get_db_path()
    _ensure_db(db_path)

    try:
        video = do_ingest(db_path, url)
        console.print(f"[green]Added:[/green] {video.title} ({video.youtube_id})")
    except Exception as e:
        err_console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1) from None


@app.command()
def history(
    limit: Annotated[int, typer.Option("--limit", "-n", help="Number of recent videos to fetch")] = 20,
    browser: Annotated[str, typer.Option("--browser", "-b", help="Browser to read cookies from")] = "chrome",
    save: Annotated[bool, typer.Option("--save", help="Save fetched videos to the database")] = False,
) -> None:
    """Show your recent YouTube watch history."""
    from yt_brain.infrastructure.ytdlp_adapter import fetch_history, parse_ytdlp_metadata

    console.print(f"[dim]Fetching last {limit} videos from YouTube history ({browser} cookies)...[/dim]")

    try:
        entries = fetch_history(limit=limit, browser=browser)
    except Exception as e:
        err_console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1) from None

    if not entries:
        console.print("[yellow]No history found. Make sure you're logged into YouTube in your browser.[/yellow]")
        return

    table = Table(title=f"YouTube History (last {len(entries)})")
    table.add_column("#", style="dim", justify="right")
    table.add_column("Title", max_width=60)
    table.add_column("Channel", max_width=25)
    table.add_column("Duration", justify="right")
    table.add_column("ID", style="dim")

    for i, entry in enumerate(entries, 1):
        duration = entry.get("duration")
        if duration:
            mins, secs = divmod(int(duration), 60)
            dur_str = f"{mins}:{secs:02d}"
        else:
            dur_str = "-"
        table.add_row(
            str(i),
            (entry.get("title") or "")[:60],
            (entry.get("channel") or entry.get("uploader") or "")[:25],
            dur_str,
            entry.get("id", ""),
        )

    console.print(table)

    if save:
        from yt_brain.infrastructure.database import save_video

        db_path = _get_db_path()
        _ensure_db(db_path)
        count = 0
        for entry in entries:
            video = parse_ytdlp_metadata(entry)
            save_video(db_path, video)
            count += 1
        console.print(f"\n[green]Saved {count} videos to database.[/green]")

        # Backfill missing channel names via oEmbed
        import json as _json
        import urllib.request
        from urllib.error import URLError

        from yt_brain.infrastructure.database import get_videos_missing_channel, update_channel_id

        missing = get_videos_missing_channel(db_path)
        if missing:
            console.print(f"[dim]Backfilling channel names for {len(missing)} videos...[/dim]")
            filled = 0
            for vid_id, _title in missing:
                try:
                    url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={vid_id}&format=json"
                    resp = urllib.request.urlopen(url, timeout=10)
                    data = _json.loads(resp.read())
                    name = data.get("author_name", "")
                    if name:
                        update_channel_id(db_path, vid_id, name)
                        filled += 1
                except (URLError, _json.JSONDecodeError, TimeoutError):
                    pass
            console.print(f"[green]Backfilled {filled}/{len(missing)} channel names.[/green]")
    else:
        console.print("\n[dim]Use --save to add these to your brain.[/dim]")


@app.command()
def sync(
    browser: Annotated[str, typer.Option("--browser", "-b", help="Browser to read cookies from")] = "chrome",
    batch_size: Annotated[int, typer.Option("--batch-size", help="Videos per fetch batch")] = 200,
) -> None:
    """Fetch new videos from YouTube history and update the database."""
    from yt_brain.application.sync import sync_videos
    from yt_brain.infrastructure.config import load_config

    config = load_config()
    db_path = config.db_path
    _ensure_db(db_path)

    console.print(f"[dim]Syncing YouTube history ({browser} cookies)...[/dim]")

    try:
        result = sync_videos(
            db_path=db_path,
            browser=browser,
            batch_size=batch_size,
            api_key=config.youtube_api_key or None,
        )
    except Exception as e:
        err_console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1) from None

    if result.new_videos == 0 and result.rewatched_videos == 0:
        console.print("[green]Already up to date.[/green]")
    else:
        if result.new_videos:
            console.print(f"[green]Synced {result.new_videos} new videos[/green]")
        if result.rewatched_videos:
            console.print(f"[green]Updated {result.rewatched_videos} re-watched videos[/green]")
        if result.channels_backfilled:
            console.print(f"  Channels backfilled: {result.channels_backfilled}")
        if result.categories_backfilled:
            console.print(f"  Categories backfilled: {result.categories_backfilled}")
        if result.dates_backfilled:
            console.print(f"  Dates backfilled: {result.dates_backfilled}")
        if result.likes_synced:
            console.print(f"  Likes synced: {result.likes_synced}")


@app.command("backfill-categories")
def backfill_categories() -> None:
    """Backfill missing video categories via YouTube Data API."""
    from yt_brain.application.backfill import backfill_categories as do_backfill
    from yt_brain.infrastructure.config import load_config
    from yt_brain.infrastructure.database import get_videos_missing_category

    config = load_config()
    if not config.youtube_api_key:
        err_console.print("[red]No YouTube API key configured.[/red]")
        raise typer.Exit(1)

    db_path = config.db_path
    _ensure_db(db_path)

    missing_count = len(get_videos_missing_category(db_path))
    if not missing_count:
        console.print("[green]All videos have categories.[/green]")
        return

    console.print(f"[dim]Backfilling categories for {missing_count} videos...[/dim]")
    filled = do_backfill(db_path, config.youtube_api_key)
    console.print(f"[green]Backfilled {filled}/{missing_count} categories.[/green]")


@app.command()
def fetch(
    period: Annotated[str, typer.Argument(help="How far back to fetch, e.g. 1yr, 2yr, 3yr")],
    browser: Annotated[str, typer.Option("--browser", "-b", help="Browser to read cookies from")] = "chrome",
) -> None:
    """Fetch YouTube watch history for a time period and save to database.

    Fetches in batches of 200, backfills upload dates after each batch,
    and stops once it hits videos published before the cutoff.
    """
    import json as _json
    import re
    import urllib.request
    from datetime import datetime, timedelta
    from urllib.error import URLError

    from yt_brain.infrastructure.config import load_config as _load_config
    from yt_brain.infrastructure.database import (
        get_videos_missing_channel,
        save_video,
        update_channel_id,
        update_watched_at,
    )
    from yt_brain.infrastructure.ytdlp_adapter import fetch_history_range, parse_ytdlp_metadata

    match = re.match(r"^(\d+)\s*yr$", period.strip())
    if not match:
        err_console.print("[red]Format: 1yr, 2yr, 3yr, etc.[/red]")
        raise typer.Exit(1)

    years = int(match.group(1))
    cutoff = datetime.now(UTC) - timedelta(days=years * 365)
    console.print(f"[dim]Fetching watch history back to {cutoff.strftime('%b %Y')}...[/dim]")

    config = _load_config()
    if not config.youtube_api_key:
        err_console.print("[red]YouTube API key required for date-based fetching. Run: yt-brain config[/red]")
        raise typer.Exit(1)

    db_path = _get_db_path()
    _ensure_db(db_path)

    batch_size = 200
    start = 1
    total_saved = 0
    reached_cutoff = False

    while not reached_cutoff:
        end = start + batch_size - 1
        console.print(f"[dim]Fetching videos {start}-{end}...[/dim]")

        try:
            entries = fetch_history_range(start, end, browser)
        except Exception as e:
            err_console.print(f"[red]Error: {e}[/red]")
            break

        if not entries:
            console.print("[dim]No more history entries.[/dim]")
            break

        # Save videos
        batch_ids = []
        for entry in entries:
            video = parse_ytdlp_metadata(entry)
            save_video(db_path, video)
            batch_ids.append(video.youtube_id)
            total_saved += 1

        # Backfill dates for this batch via YouTube API
        ids_str = ",".join(batch_ids)
        try:
            api_url = (
                f"https://www.googleapis.com/youtube/v3/videos"
                f"?part=snippet&id={ids_str}&key={config.youtube_api_key}"
            )
            resp = urllib.request.urlopen(api_url, timeout=15)
            data = _json.loads(resp.read())
            oldest_in_batch = None
            for item in data.get("items", []):
                published = item["snippet"].get("publishedAt", "")
                if published:
                    update_watched_at(db_path, item["id"], published)
                    pub_dt = datetime.fromisoformat(published.replace("Z", "+00:00"))
                    if oldest_in_batch is None or pub_dt < oldest_in_batch:
                        oldest_in_batch = pub_dt
        except (URLError, _json.JSONDecodeError, KeyError) as e:
            err_console.print(f"[yellow]API error: {e}[/yellow]")
            oldest_in_batch = None

        if oldest_in_batch:
            console.print(f"[dim]  Oldest in batch: {oldest_in_batch.strftime('%b %d, %Y')}[/dim]")
            if oldest_in_batch < cutoff:
                console.print(f"[green]Reached cutoff ({cutoff.strftime('%b %Y')}).[/green]")
                reached_cutoff = True

        if len(entries) < batch_size:
            console.print("[dim]Reached end of history.[/dim]")
            break

        start += batch_size

    console.print(f"[green]Saved {total_saved} videos.[/green]")

    # Backfill channel names for all missing
    missing_channels = get_videos_missing_channel(db_path)
    if missing_channels:
        console.print(f"[dim]Backfilling channel names for {len(missing_channels)} videos...[/dim]")
        filled = 0
        for vid_id, _title in missing_channels:
            try:
                url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={vid_id}&format=json"
                resp = urllib.request.urlopen(url, timeout=10)
                data = _json.loads(resp.read())
                name = data.get("author_name", "")
                if name:
                    update_channel_id(db_path, vid_id, name)
                    filled += 1
            except (URLError, _json.JSONDecodeError, TimeoutError):
                pass
        console.print(f"[green]Backfilled {filled}/{len(missing_channels)} channel names.[/green]")


@app.command()
def classify(
    reclassify: Annotated[bool, typer.Option("--reclassify", help="Re-classify all videos")] = False,
) -> None:
    """Run engagement classification on videos."""
    from yt_brain.application.classify import classify_all
    from yt_brain.infrastructure.config import load_config

    config = load_config()
    db_path = config.db_path
    _ensure_db(db_path)

    counts = classify_all(
        db_path,
        reclassify=reclassify,
        bounce_threshold=config.bounce_threshold,
        watched_threshold=config.watched_threshold,
    )

    total = sum(counts.values())
    console.print(f"[green]Classified {total} videos:[/green]")
    for level, count in sorted(counts.items()):
        console.print(f"  {level}: {count}")


@app.command()
def review(
    level: Annotated[str | None, typer.Option("--level", "-l", help="Filter by engagement level")] = None,
) -> None:
    """Review videos by engagement tier."""
    from yt_brain.application.review import get_review_list, override_engagement

    db_path = _get_db_path()
    _ensure_db(db_path)

    filter_level = EngagementLevel(level) if level else None
    videos = get_review_list(db_path, filter_level)

    if not videos:
        console.print("[yellow]No videos to review.[/yellow]")
        return

    table = Table(title="Video Review")
    table.add_column("ID", style="dim", max_width=12)
    table.add_column("Title", max_width=50)
    table.add_column("Channel", max_width=20)
    table.add_column("Watch %", justify="right")
    table.add_column("Engagement", style="bold")
    table.add_column("Override", style="italic")

    for video in videos:
        pct = f"{video.watch_percentage:.0%}" if video.watch_percentage is not None else "-"
        override = video.engagement_override.value if video.engagement_override else ""
        table.add_row(
            video.youtube_id,
            video.title[:50],
            video.channel_id[:20],
            pct,
            video.engagement_level.value,
            override,
        )

    console.print(table)
    console.print(f"\nTotal: {len(videos)} videos")
    console.print("\nTo reclassify a video: [bold]yt-brain review[/bold] then use override prompt")

    while True:
        response = console.input("\n[bold]Override a video? Enter video ID (or 'q' to quit):[/bold] ").strip()
        if response.lower() in ("q", "quit", ""):
            break

        video_id = response
        level_input = console.input("[b]ounce [w]atched [l]iked [c]urated [s]kip: ").strip().lower()
        level_map = {"b": "BOUNCED", "w": "WATCHED", "l": "LIKED", "c": "CURATED"}
        if level_input in level_map:
            override_engagement(db_path, video_id, EngagementLevel(level_map[level_input]))
            console.print(f"[green]Overridden {video_id} → {level_map[level_input]}[/green]")
        elif level_input != "s":
            console.print("[yellow]Skipped.[/yellow]")


@app.command()
def status() -> None:
    """Show dashboard with video counts by engagement tier."""
    from yt_brain.application.status import get_status_summary

    db_path = _get_db_path()
    _ensure_db(db_path)

    summary = get_status_summary(db_path)

    table = Table(title="yt-brain Status")
    table.add_column("Tier", style="bold")
    table.add_column("Count", justify="right")

    for level in EngagementLevel:
        count = summary.by_engagement.get(level.value, 0)
        table.add_row(level.value, str(count))

    table.add_section()
    table.add_row("TOTAL", str(summary.total), style="bold")
    table.add_row("With transcripts", str(summary.with_transcripts))

    console.print(table)


@app.command()
def transcript(
    video_id: Annotated[str | None, typer.Argument(help="YouTube video ID")] = None,
    level: Annotated[
        str | None, typer.Option("--level", "-l", help="Fetch transcripts for all videos at this engagement level")
    ] = None,
) -> None:
    """Fetch video transcript(s) via yt-dlp."""
    from yt_brain.application.transcript import fetch_transcripts_by_level, fetch_video_transcript
    from yt_brain.infrastructure.config import load_config

    config = load_config()
    db_path = config.db_path
    _ensure_db(db_path)

    if video_id:
        result = fetch_video_transcript(db_path, video_id, config.transcript_language)
        if result:
            console.print(f"[green]Transcript fetched for {video_id}[/green] ({len(result)} chars)")
        else:
            console.print(f"[yellow]No transcript available for {video_id}[/yellow]")
    elif level:
        results = fetch_transcripts_by_level(db_path, EngagementLevel(level), config.transcript_language)
        success = sum(1 for v in results.values() if v)
        console.print(f"[green]Fetched {success}/{len(results)} transcripts for {level} videos[/green]")
    else:
        err_console.print("[red]Provide a video ID or --level flag[/red]")
        raise typer.Exit(1)


@app.command()
def config() -> None:
    """Show current configuration."""
    from yt_brain.infrastructure.config import load_config

    cfg = load_config()

    table = Table(title="yt-brain Config")
    table.add_column("Setting", style="bold")
    table.add_column("Value")

    table.add_row("Config dir", str(cfg.config_dir))
    table.add_row("Database", str(cfg.db_path))
    table.add_row("API key", "***" if cfg.youtube_api_key else "(not set)")
    table.add_row("Bounce threshold", f"{cfg.bounce_threshold:.0%}")
    table.add_row("Watched threshold", f"{cfg.watched_threshold:.0%}")
    table.add_row("Transcript language", cfg.transcript_language)

    console.print(table)


@app.command("backfill-dates")
def backfill_dates() -> None:
    """Backfill missing video dates via YouTube Data API."""
    from yt_brain.application.backfill import backfill_dates as do_backfill
    from yt_brain.infrastructure.config import load_config
    from yt_brain.infrastructure.database import get_videos_missing_watched_at

    config = load_config()
    if not config.youtube_api_key:
        err_console.print("[red]No YouTube API key configured. Run: yt-brain config[/red]")
        raise typer.Exit(1)

    db_path = config.db_path
    _ensure_db(db_path)

    missing_count = len(get_videos_missing_watched_at(db_path))
    if not missing_count:
        console.print("[green]All videos have dates.[/green]")
        return

    console.print(f"[dim]Backfilling dates for {missing_count} videos via YouTube Data API...[/dim]")
    filled = do_backfill(db_path, config.youtube_api_key)
    console.print(f"[green]Backfilled {filled}/{missing_count} video dates.[/green]")


@app.command()
def embed(
    rebuild: Annotated[bool, typer.Option("--rebuild", help="Regenerate all embeddings")] = False,
) -> None:
    """Generate semantic embeddings for video titles and descriptions."""
    from yt_brain.infrastructure.database import SQLITE_VEC_AVAILABLE

    if not SQLITE_VEC_AVAILABLE:
        console.print("[red]sqlite-vec is not installed. Embedding and clustering features are unavailable.[/red]")
        console.print("[dim]Install with: uv sync  (or pip install sqlite-vec)[/dim]")
        raise typer.Exit(1)

    from yt_brain.application.embed import embed_videos
    from yt_brain.infrastructure.database import get_embedding_count, get_videos_for_embedding

    db_path = _get_db_path()
    _ensure_db(db_path)

    pending = len(get_videos_for_embedding(db_path, rebuild=rebuild))
    if not pending:
        count = get_embedding_count(db_path)
        console.print(f"[green]All {count} videos already have embeddings.[/green]")
        return

    console.print(f"[dim]Embedding {pending} videos (this may take a minute)...[/dim]")

    def on_progress(done: int, total: int) -> None:
        console.print(f"  [dim]{done}/{total}[/dim]")

    embedded = embed_videos(db_path, rebuild=rebuild, on_progress=on_progress)
    total = get_embedding_count(db_path)
    console.print(f"[green]Embedded {embedded} videos. Total embeddings: {total}[/green]")


# --- Cluster commands ---
cluster_app = typer.Typer(help="Manage video topic clusters.")
app.add_typer(cluster_app, name="cluster")


@cluster_app.callback(invoke_without_command=True)
def cluster_default(
    ctx: typer.Context,
    rebuild: Annotated[bool, typer.Option("--rebuild", help="Full recluster from scratch")] = False,
    min_cluster_size: Annotated[int, typer.Option("--min-cluster-size", help="Minimum videos per cluster")] = 5,
) -> None:
    """Run video clustering (incremental by default, --rebuild for full)."""
    if ctx.invoked_subcommand is not None:
        return

    from yt_brain.infrastructure.database import SQLITE_VEC_AVAILABLE

    if not SQLITE_VEC_AVAILABLE:
        console.print("[red]sqlite-vec is not installed. Embedding and clustering features are unavailable.[/red]")
        console.print("[dim]Install with: uv sync  (or pip install sqlite-vec)[/dim]")
        raise typer.Exit(1)

    from yt_brain.infrastructure.config import load_config
    from yt_brain.infrastructure.database import get_embedding_count

    db_path = _get_db_path()
    _ensure_db(db_path)

    emb_count = get_embedding_count(db_path)
    if emb_count == 0:
        console.print("[red]No embeddings found. Run: yt-brain embed[/red]")
        raise typer.Exit(1)

    if emb_count < 10:
        console.print("[red]Not enough videos to cluster (need at least 10 embeddings).[/red]")
        raise typer.Exit(1)

    config = load_config()
    api_key = getattr(config, "anthropic_api_key", "") or ""

    if rebuild:
        if not api_key:
            console.print("[yellow]No anthropic_api_key in config. Slugs will be numeric.[/yellow]")
            api_key = ""

        console.print(f"[dim]Clustering {emb_count} videos (min_cluster_size={min_cluster_size})...[/dim]")

        def on_progress(done: int, total: int) -> None:
            console.print(f"  [dim]Named {done}/{total} clusters[/dim]")

        from yt_brain.application.cluster import cluster_videos

        n = cluster_videos(db_path, api_key=api_key, min_cluster_size=min_cluster_size, on_progress=on_progress)
        console.print(f"[green]Created {n} clusters.[/green]")
    else:
        from yt_brain.application.cluster import assign_new_videos
        from yt_brain.infrastructure.database import get_clusters_with_counts

        clusters = get_clusters_with_counts(db_path)
        if not clusters:
            console.print("[yellow]No clusters exist yet. Run with --rebuild first.[/yellow]")
            raise typer.Exit(1)

        n = assign_new_videos(db_path)
        console.print(f"[green]Assigned {n} new videos to existing clusters.[/green]")


@cluster_app.command("list")
def cluster_list() -> None:
    """Show all clusters with video counts."""
    from yt_brain.infrastructure.database import get_clusters_with_counts

    db_path = _get_db_path()
    _ensure_db(db_path)

    clusters = get_clusters_with_counts(db_path)
    if not clusters:
        console.print("[dim]No clusters yet. Run: yt-brain cluster --rebuild[/dim]")
        return

    from rich.table import Table

    table = Table(title="Video Clusters")
    table.add_column("Slug", style="cyan")
    table.add_column("Videos", justify="right")
    for c in clusters:
        table.add_row(c["slug"], str(c["count"]))
    console.print(table)


@cluster_app.command("rename")
def cluster_rename(
    old_slug: Annotated[str, typer.Argument(help="Current cluster slug")],
    new_slug: Annotated[str, typer.Argument(help="New cluster slug")],
) -> None:
    """Rename a cluster slug."""
    from yt_brain.infrastructure.database import rename_cluster

    db_path = _get_db_path()
    _ensure_db(db_path)

    if rename_cluster(db_path, old_slug, new_slug):
        console.print(f"[green]Renamed '{old_slug}' → '{new_slug}'[/green]")
    else:
        console.print(f"[red]Cluster '{old_slug}' not found.[/red]")


@app.command("backfill-descriptions")
def backfill_descriptions(
    limit: Annotated[int | None, typer.Option("--limit", "-n", help="Max videos to backfill")] = None,
) -> None:
    """Backfill missing video descriptions via YouTube Data API."""
    from yt_brain.application.backfill import backfill_descriptions as do_backfill
    from yt_brain.infrastructure.config import load_config
    from yt_brain.infrastructure.database import get_videos_missing_description

    config = load_config()
    if not config.youtube_api_key:
        err_console.print("[red]No YouTube API key configured. Run: yt-brain config[/red]")
        raise typer.Exit(1)

    db_path = config.db_path
    _ensure_db(db_path)

    missing_count = len(get_videos_missing_description(db_path))
    if not missing_count:
        console.print("[green]All videos have descriptions.[/green]")
        return

    target = min(missing_count, limit) if limit else missing_count
    console.print(
        f"[dim]Backfilling descriptions for {target}/{missing_count} videos via YouTube API (batches of 50)...[/dim]"
    )

    def on_progress(done: int, total: int) -> None:
        console.print(f"  [dim]{done}/{total}[/dim]")

    filled = do_backfill(db_path, config.youtube_api_key, limit=limit, on_progress=on_progress)
    console.print(f"[green]Backfilled {filled}/{target} descriptions.[/green]")


@app.command("backfill-channels")
def backfill_channels() -> None:
    """Backfill missing channel names via YouTube oEmbed API."""
    from yt_brain.application.backfill import backfill_channels as do_backfill
    from yt_brain.infrastructure.database import get_videos_missing_channel

    db_path = _get_db_path()
    _ensure_db(db_path)

    missing_count = len(get_videos_missing_channel(db_path))
    if not missing_count:
        console.print("[green]All videos have channel names.[/green]")
        return

    console.print(f"[dim]Backfilling channel names for {missing_count} videos...[/dim]")
    filled = do_backfill(db_path)
    console.print(f"[green]Backfilled {filled}/{missing_count} channel names.[/green]")


@app.command("backfill-likes")
def backfill_likes_cmd(
    browser: Annotated[str, typer.Option("--browser", "-b", help="Browser to read cookies from")] = "chrome",
) -> None:
    """Backfill liked video status from YouTube."""
    from yt_brain.application.backfill import backfill_likes

    db_path = _get_db_path()
    _ensure_db(db_path)

    console.print(f"[dim]Fetching liked videos from YouTube ({browser} cookies)...[/dim]")
    try:
        count = backfill_likes(db_path, browser=browser)
    except Exception as e:
        err_console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1) from None
    console.print(f"[green]Marked {count} videos as liked.[/green]")


@app.command()
def dashboard(
    port: Annotated[int, typer.Option("--port", "-p", help="Port to serve on")] = 5555,
) -> None:
    """Launch the yt-brain dashboard in your browser."""
    from yt_brain.web.dashboard import run_dashboard

    db_path = _get_db_path()
    _ensure_db(db_path)

    console.print(f"[dim]Loading model and starting dashboard on port {port}...[/dim]")
    run_dashboard(port=port, open_browser=True)


if __name__ == "__main__":
    app()
