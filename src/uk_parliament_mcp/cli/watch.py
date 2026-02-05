"""Live Parliament dashboard with auto-refresh."""

from __future__ import annotations

import asyncio
import json
import signal
import sys
from datetime import datetime
from typing import Any

import typer
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from uk_parliament_mcp.config import NOW_API_BASE, WHATSON_API_BASE
from uk_parliament_mcp.http_client import build_url, get_result

app = typer.Typer(help="Live Parliament dashboard with auto-refresh")

MIN_INTERVAL = 10  # Minimum refresh interval in seconds


async def _fetch_commons_now() -> dict[str, Any] | None:
    """Fetch current Commons chamber activity."""
    url = f"{NOW_API_BASE}/Message/message/CommonsMain/current"
    return _parse_api_response(await get_result(url))


async def _fetch_lords_now() -> dict[str, Any] | None:
    """Fetch current Lords chamber activity."""
    url = f"{NOW_API_BASE}/Message/message/LordsMain/current"
    return _parse_api_response(await get_result(url))


async def _fetch_calendar_today() -> list[dict[str, Any]]:
    """Fetch today's calendar events."""
    today = datetime.now().strftime("%Y-%m-%d")
    url = build_url(
        f"{WHATSON_API_BASE}/events/list.json",
        {
            "queryParameters.startDate": today,
            "queryParameters.endDate": today,
        },
    )
    result = _parse_api_response(await get_result(url))
    if result is None:
        return []
    if isinstance(result, list):
        return result
    # Calendar API may return events in various structures
    for key in ["items", "results", "data"]:
        if key in result and isinstance(result[key], list):
            return list(result[key])
    return []


async def _fetch_all_data(
    house: str | None = None,
) -> dict[str, Any]:
    """Fetch all dashboard data in parallel.

    Args:
        house: Optional house filter ("commons", "lords", or None for both).

    Returns:
        Dict with commons, lords, and calendar data.
    """
    tasks: dict[str, Any] = {}

    if house is None or house == "commons":
        tasks["commons"] = _fetch_commons_now()
    if house is None or house == "lords":
        tasks["lords"] = _fetch_lords_now()
    tasks["calendar"] = _fetch_calendar_today()

    results: dict[str, Any] = {}
    gathered = await asyncio.gather(*tasks.values(), return_exceptions=True)
    for key, result in zip(tasks.keys(), gathered):
        if isinstance(result, Exception):
            results[key] = None
        else:
            results[key] = result

    return results


def _parse_api_response(response_str: str) -> dict[str, Any] | None:
    """Parse API response, extracting data field."""
    try:
        parsed = json.loads(response_str)
        if isinstance(parsed, dict):
            if "error" in parsed:
                return None
            if "data" in parsed:
                data = parsed["data"]
                if isinstance(data, str):
                    result: dict[str, Any] = json.loads(data)
                    return result
                return dict(data) if isinstance(data, dict) else data
            return parsed
        return dict(parsed) if isinstance(parsed, dict) else None
    except (json.JSONDecodeError, TypeError):
        return None


_SLIDE_TYPE_LABELS: dict[str, tuple[str, str]] = {
    "Debate": ("Debate", "bold cyan"),
    "Division": ("DIVISION", "bold red"),
    "PrimeMinistersQuestions": ("Prime Minister's Questions", "bold yellow"),
    "OralQuestionTime": ("Oral Questions", "bold yellow"),
    "UrgentQuestion": ("Urgent Question", "bold yellow"),
    "Statement": ("Statement", "bold green"),
    "Prayers": ("Prayers", "bold"),
    "PointsOfOrder": ("Points of Order", "bold"),
    "Generic": ("Business", "bold"),
    "NotSitting": ("Not Sitting", "dim italic"),
    "HouseRisen": ("House has risen", "dim italic"),
}

_ACTIVE_SLIDE_TYPES = {
    "Debate",
    "Division",
    "PrimeMinistersQuestions",
    "OralQuestionTime",
    "UrgentQuestion",
    "Statement",
    "Prayers",
    "PointsOfOrder",
    "Generic",
}


def _format_slide_type_label(slide_type: str) -> tuple[str, str]:
    """Map a SlideType string to a human-readable label and Rich style.

    Args:
        slide_type: SlideType enum value from the Now API.

    Returns:
        Tuple of (label, rich_style).
    """
    return _SLIDE_TYPE_LABELS.get(slide_type, (slide_type, "bold"))


def _render_member_line(member: dict[str, Any], text: Text) -> None:
    """Render a MemberViewModel as formatted text lines.

    Args:
        member: MemberViewModel dict from the Now API.
        text: Rich Text object to append to.
    """
    name = member.get("nameDisplayAs") or member.get("nameFullTitle") or ""
    if not name:
        return
    text.append(f"  {name}", style="bold")
    parts: list[str] = []
    party = member.get("latestParty")
    if party and party.get("name"):
        parts.append(party["name"])
    membership = member.get("latestHouseMembership")
    if membership and membership.get("membershipFrom"):
        parts.append(membership["membershipFrom"])
    if parts:
        text.append(f"\n  {' | '.join(parts)}", style="dim")


def _render_slide_lines(lines: list[dict[str, Any]], text: Text) -> None:
    """Render LineViewModel items into Rich Text.

    Args:
        lines: List of LineViewModel dicts, sorted by displayOrder.
        text: Rich Text object to append to.
    """
    sorted_lines = sorted(lines, key=lambda ln: ln.get("displayOrder", 0))
    for line in sorted_lines:
        style = line.get("style", "")
        content = line.get("content") or ""
        member = line.get("member")

        # Divider styles -> horizontal rules
        if style in ("DividerSolid", "DividerDotted", "DividerDashed"):
            char = "-" if style == "DividerSolid" else ("." if style == "DividerDotted" else "- ")
            text.append(char * 20 + "\n", style="dim")
            continue

        if style == "EmptyLine":
            text.append("\n")
            continue

        # Member line with embedded data
        if member and (member.get("nameDisplayAs") or member.get("nameFullTitle")):
            _render_member_line(member, text)
            text.append("\n")
            continue

        # Content with style-based formatting
        if content:
            if style == "Footer":
                text.append(content, style="dim")
            elif style == "Division":
                text.append(content, style="bold red")
            else:
                text.append(content)
            text.append("\n")


def _render_scrolling_messages(
    messages: list[dict[str, Any]], text: Text
) -> None:
    """Render ScrollingMessageViewModel items below slides.

    Args:
        messages: List of ScrollingMessageViewModel dicts.
        text: Rich Text object to append to.
    """
    if not messages:
        return
    text.append("---\n", style="dim")
    for msg in messages:
        content = msg.get("content") or ""
        if not content:
            continue
        alert_type = msg.get("alertType", "Standard")
        if alert_type == "Alert":
            text.append(f"! {content}\n", style="bold red")
        elif alert_type == "SecondaryChamber":
            text.append(f"  {content}\n", style="italic")
        else:
            text.append(f"  {content}\n", style="dim")


def _render_chamber_panel(data: dict[str, Any] | None, house_name: str) -> Panel:
    """Render a chamber status panel from MessageViewModel data.

    Args:
        data: MessageViewModel dict from the Now API, or None.
        house_name: "House of Commons" or "House of Lords".

    Returns:
        Rich Panel with chamber status.
    """
    if data is None or not data:
        content = Text("Not currently sitting", style="dim italic")
        return Panel(content, title=f"[bold]{house_name}[/bold]", border_style="dim")

    # Check if annunciator is disabled
    if data.get("annunciatorDisabled"):
        content = Text("Annunciator offline", style="dim italic")
        return Panel(content, title=f"[bold]{house_name}[/bold]", border_style="dim")

    text = Text()
    is_active = False

    # Division bell indicator
    if data.get("showCommonsBell") or data.get("showLordsBell"):
        text.append("DIVISION BELL\n", style="bold red")
        is_active = True

    # Render slides
    slides = data.get("slides") or []
    for slide in slides:
        slide_type = slide.get("type", "")

        # Skip blank slides
        if slide_type == "BlankSlide":
            continue

        # Track if chamber is active
        if slide_type in _ACTIVE_SLIDE_TYPES:
            is_active = True

        # Slide type label
        label, style = _format_slide_type_label(slide_type)
        text.append(label, style=style)

        # Speaker time
        speaker_time = slide.get("speakerTime")
        if speaker_time and isinstance(speaker_time, str) and "T" in speaker_time:
            time_part = speaker_time.split("T")[1][:5]
            text.append(f"  {time_part}", style="dim")
        text.append("\n")

        # Slide lines
        slide_lines = slide.get("lines") or []
        if slide_lines:
            _render_slide_lines(slide_lines, text)

    # Scrolling messages
    scrolling = data.get("scrollingMessages") or []
    if scrolling:
        _render_scrolling_messages(scrolling, text)

    # Fallback if nothing rendered
    if not text.plain.strip():
        text.append("No current activity", style="dim italic")

    border_style = "green" if is_active else "dim"
    return Panel(text, title=f"[bold]{house_name}[/bold]", border_style=border_style)


def _render_calendar_table(events: list[dict[str, Any]]) -> Table | Text:
    """Render today's business as a Rich table.

    Args:
        events: List of calendar event dicts.

    Returns:
        Rich Table or Text if no events.
    """
    if not events:
        return Text("No events scheduled for today", style="dim italic")

    table = Table(
        show_header=True,
        header_style="bold",
        expand=False,
        row_styles=["", "dim"],
    )
    table.add_column("Time", width=5, style="cyan", no_wrap=True)
    table.add_column("House", width=7, no_wrap=True)
    table.add_column("Event", max_width=55, overflow="ellipsis")
    table.add_column("Category", max_width=16, style="dim")

    for event in events:
        time_str = ""
        for key in ["StartTime", "startTime", "StartDate", "startDate"]:
            if key in event and event[key]:
                raw = str(event[key])
                # Try to extract just the time portion
                if "T" in raw:
                    time_str = raw.split("T")[1][:5]
                elif len(raw) > 5:
                    time_str = raw[:5]
                else:
                    time_str = raw
                break

        house_str = ""
        for key in ["House", "house"]:
            if key in event and event[key]:
                house_str = str(event[key])
                break

        event_str = ""
        for key in ["Description", "description", "Title", "title", "Name", "name"]:
            if key in event and event[key]:
                event_str = str(event[key])[:60]
                break

        category_str = ""
        for key in ["Category", "category", "Type", "type"]:
            if key in event and event[key]:
                category_str = str(event[key])
                break

        table.add_row(time_str, house_str, event_str, category_str)

    return table


def _render_dashboard(data: dict[str, Any]) -> Layout:
    """Render the full dashboard layout.

    Args:
        data: Dict with commons, lords, and calendar data.

    Returns:
        Rich Layout for the dashboard.
    """
    now = datetime.now().strftime("%H:%M:%S")
    layout = Layout()

    # Header
    header = Text(
        f"  UK Parliament Live | Last updated: {now} | Ctrl+C to exit", style="bold white on blue"
    )

    # Chamber panels
    chambers = Layout()
    if "commons" in data:
        commons_panel = _render_chamber_panel(data.get("commons"), "House of Commons")
        if "lords" in data:
            lords_panel = _render_chamber_panel(data.get("lords"), "House of Lords")
            chambers.split_row(Layout(commons_panel), Layout(lords_panel))
        else:
            chambers.update(commons_panel)
    elif "lords" in data:
        lords_panel = _render_chamber_panel(data.get("lords"), "House of Lords")
        chambers.update(lords_panel)

    # Calendar
    calendar_content = _render_calendar_table(data.get("calendar", []))
    calendar_panel = Panel(calendar_content, title="[bold]Today's Business[/bold]")

    layout.split_column(
        Layout(Panel(header, style=""), size=3),
        Layout(chambers, ratio=1),
        Layout(calendar_panel),
    )

    return layout


async def _run_watch(house: str | None = None, interval: int = 30) -> None:
    """Run the live watch dashboard.

    Args:
        house: Optional house filter ("commons", "lords", or None for both).
        interval: Refresh interval in seconds.
    """
    console = Console()

    # Handle graceful exit
    stop_event = asyncio.Event()

    def _handle_signal(*args: Any) -> None:
        stop_event.set()

    # Register signal handlers
    if sys.platform != "win32":
        loop = asyncio.get_running_loop()
        loop.add_signal_handler(signal.SIGINT, _handle_signal)
        loop.add_signal_handler(signal.SIGTERM, _handle_signal)

    try:
        with Live(console=console, screen=True, refresh_per_second=1) as live:
            while not stop_event.is_set():
                try:
                    data = await _fetch_all_data(house)
                    dashboard = _render_dashboard(data)
                    live.update(dashboard)
                except Exception:
                    # Don't crash on transient errors
                    pass

                # Wait for interval or stop signal
                try:
                    await asyncio.wait_for(stop_event.wait(), timeout=interval)
                    break  # Stop event was set
                except asyncio.TimeoutError:
                    continue  # Timeout expired, refresh
    except KeyboardInterrupt:
        pass  # Clean exit on Ctrl+C


@app.callback(invoke_without_command=True)
def watch(
    house: str | None = typer.Argument(
        None,
        help="House to watch: 'commons', 'lords', or omit for both",
    ),
    interval: int = typer.Option(
        30,
        "--interval",
        "-i",
        help="Refresh interval in seconds (minimum 10)",
    ),
    raw: bool = typer.Option(
        False,
        "--raw",
        help="Fetch data once, output raw JSON, and exit (no live dashboard)",
    ),
    pretty: bool = typer.Option(
        False,
        "--pretty",
        "-p",
        help="Pretty-print JSON output (only with --raw)",
    ),
) -> None:
    """
    Live Parliament dashboard with auto-refresh.

    Shows current chamber activity and today's business in a live-updating display.
    Press Ctrl+C to exit.

    Examples:
      parliament watch                # Both houses
      parliament watch commons        # Commons only
      parliament watch lords          # Lords only
      parliament watch --interval 10  # Refresh every 10 seconds
      parliament watch --raw --pretty # Dump raw JSON and exit
    """
    # Validate house argument
    if house is not None:
        house_lower = house.lower()
        if house_lower not in ("commons", "lords"):
            console = Console()
            console.print(f"[red]Invalid house '{house}'. Use 'commons' or 'lords'.[/red]")
            raise typer.Exit(1)
        house = house_lower
    else:
        house = None

    if raw:
        data = asyncio.run(_fetch_all_data(house))
        indent = 2 if pretty else None
        print(json.dumps(data, indent=indent, default=str))
        return

    # Enforce minimum interval
    if interval < MIN_INTERVAL:
        interval = MIN_INTERVAL

    asyncio.run(_run_watch(house, interval))
