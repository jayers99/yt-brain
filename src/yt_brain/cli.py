from __future__ import annotations

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
        from yt_brain.infrastructure.database import init_db, save_video

        db_path = _get_db_path()
        _ensure_db(db_path)
        count = 0
        for entry in entries:
            video = parse_ytdlp_metadata(entry)
            save_video(db_path, video)
            count += 1
        console.print(f"\n[green]Saved {count} videos to database.[/green]")
    else:
        console.print(f"\n[dim]Use --save to add these to your brain.[/dim]")


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
    table.add_row("OAuth credentials", str(cfg.oauth_credentials))
    table.add_row("Bounce threshold", f"{cfg.bounce_threshold:.0%}")
    table.add_row("Watched threshold", f"{cfg.watched_threshold:.0%}")
    table.add_row("Transcript language", cfg.transcript_language)

    console.print(table)


@app.command()
def dashboard(
    port: Annotated[int, typer.Option("--port", "-p", help="Port to serve on")] = 5555,
) -> None:
    """Launch the yt-brain dashboard in your browser."""
    import webbrowser

    from yt_brain.web.dashboard import run_dashboard

    db_path = _get_db_path()
    _ensure_db(db_path)

    url = f"http://127.0.0.1:{port}"
    console.print(f"[green]Launching dashboard at {url}[/green]")
    webbrowser.open(url)
    run_dashboard(port=port)


if __name__ == "__main__":
    app()
