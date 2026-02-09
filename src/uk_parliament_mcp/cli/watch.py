"""Live Parliament dashboard with auto-refresh."""

from __future__ import annotations

import asyncio
import json
import shutil
import signal
import sys
from datetime import datetime
from typing import Any

import typer
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.text import Text

from uk_parliament_mcp.cli.renderers import (
    _calendar_subtitle,
    _parse_api_response,
    _render_calendar_table,
    _render_chamber_panel,
    _split_events_by_house,
)
from uk_parliament_mcp.config import NOW_API_BASE, WHATSON_API_BASE
from uk_parliament_mcp.http_client import build_url, get_result

app = typer.Typer(help="Live Parliament dashboard with auto-refresh")

MIN_INTERVAL = 30  # Minimum refresh interval in seconds
SCROLL_INTERVAL = 5  # Seconds between scroll steps


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
    for key, result in zip(tasks.keys(), gathered, strict=False):
        if isinstance(result, Exception):
            results[key] = None
        else:
            results[key] = result

    return results


_CHAMBER_MIN_HEIGHT = 5  # Panel chrome (2) + at least 3 content lines
_CHAMBER_MAX_FRACTION = 0.4  # Never exceed 40% of terminal height


def _estimate_chamber_height(panel: Panel) -> int:
    """Estimate the number of terminal rows a chamber panel needs.

    Args:
        panel: Rich Panel produced by _render_chamber_panel.

    Returns:
        Estimated row count including panel borders.
    """
    renderable = panel.renderable
    if isinstance(renderable, Text):
        content = renderable.plain.rstrip("\n")
        return content.count("\n") + 1 + 2  # content lines + panel borders
    return _CHAMBER_MIN_HEIGHT


def _render_dashboard(
    data: dict[str, Any],
    scroll_offset_commons: int = 0,
    scroll_offset_lords: int = 0,
) -> Layout:
    """Render the full dashboard layout.

    Args:
        data: Dict with commons, lords, and calendar data.
        scroll_offset_commons: Scroll position for Commons calendar auto-scrolling.
        scroll_offset_lords: Scroll position for Lords calendar auto-scrolling.

    Returns:
        Rich Layout for the dashboard.
    """
    now = datetime.now().strftime("%H:%M:%S")
    layout = Layout()

    # Header
    header = Text(
        f"  UK Parliament Live | Last updated: {now} | Ctrl+C to exit", style="bold white on blue"
    )

    # Chamber panels — build and measure
    chamber_panels: list[Panel] = []
    chambers = Layout()
    both_houses = "commons" in data and "lords" in data
    if "commons" in data:
        commons_panel = _render_chamber_panel(data.get("commons"), "House of Commons")
        chamber_panels.append(commons_panel)
        if "lords" in data:
            lords_panel = _render_chamber_panel(data.get("lords"), "House of Lords")
            chamber_panels.append(lords_panel)
            chambers.split_row(Layout(commons_panel), Layout(lords_panel))
        else:
            chambers.update(commons_panel)
    elif "lords" in data:
        lords_panel = _render_chamber_panel(data.get("lords"), "House of Lords")
        chamber_panels.append(lords_panel)
        chambers.update(lords_panel)

    # Size the chamber section to fit content, give calendar the rest
    terminal_height = shutil.get_terminal_size().lines
    max_chamber = int(terminal_height * _CHAMBER_MAX_FRACTION)
    if chamber_panels:
        tallest = max(_estimate_chamber_height(p) for p in chamber_panels)
        chamber_size = max(_CHAMBER_MIN_HEIGHT, min(tallest, max_chamber))
    else:
        chamber_size = _CHAMBER_MIN_HEIGHT

    # Calendar — compute how many rows fit in the remaining space
    # header=3, chamber=chamber_size, calendar panel chrome=5 (border+title+header+subtitle+border)
    available_rows = max(terminal_height - 3 - chamber_size - 5, 3)

    calendar_events = data.get("calendar", [])
    now_dt = datetime.now()

    if both_houses and calendar_events:
        # Split into two side-by-side calendar panels
        commons_events, lords_events = _split_events_by_house(calendar_events)

        commons_content, commons_total = _render_calendar_table(
            commons_events,
            max_rows=available_rows,
            now=now_dt,
            scroll_offset=scroll_offset_commons,
            include_house_column=False,
        )
        commons_displayed = min(len(commons_events), available_rows) if commons_events else 0
        commons_scrolling = scroll_offset_commons > 0 and commons_total > available_rows
        commons_subtitle = _calendar_subtitle(
            commons_displayed,
            commons_total,
            scrolling=commons_scrolling,
            scroll_offset=scroll_offset_commons,
        )
        commons_cal_panel = Panel(
            commons_content,
            title="[bold green]Commons Business[/bold green]",
            subtitle=commons_subtitle,
            border_style="green",
        )

        lords_content, lords_total = _render_calendar_table(
            lords_events,
            max_rows=available_rows,
            now=now_dt,
            scroll_offset=scroll_offset_lords,
            include_house_column=False,
        )
        lords_displayed = min(len(lords_events), available_rows) if lords_events else 0
        lords_scrolling = scroll_offset_lords > 0 and lords_total > available_rows
        lords_subtitle = _calendar_subtitle(
            lords_displayed,
            lords_total,
            scrolling=lords_scrolling,
            scroll_offset=scroll_offset_lords,
        )
        lords_cal_panel = Panel(
            lords_content,
            title="[bold red]Lords Business[/bold red]",
            subtitle=lords_subtitle,
            border_style="red",
        )

        calendar_layout = Layout()
        calendar_layout.split_row(
            Layout(commons_cal_panel),
            Layout(lords_cal_panel),
        )
    else:
        # Single house or no events — full-width calendar with House column
        scroll_offset = scroll_offset_commons if "commons" in data else scroll_offset_lords
        calendar_content, total_count = _render_calendar_table(
            calendar_events,
            max_rows=available_rows,
            now=now_dt,
            scroll_offset=scroll_offset,
        )
        displayed = min(len(calendar_events), available_rows) if calendar_events else 0
        is_scrolling = scroll_offset > 0 and total_count > available_rows
        subtitle = _calendar_subtitle(
            displayed,
            total_count,
            scrolling=is_scrolling,
            scroll_offset=scroll_offset,
        )
        calendar_layout = Layout(
            Panel(
                calendar_content,
                title="[bold]Today's Business[/bold]",
                subtitle=subtitle,
            )
        )

    layout.split_column(
        Layout(Panel(header, style=""), size=3),
        Layout(chambers, size=chamber_size),
        Layout(calendar_layout, ratio=1),
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
        data: dict[str, Any] | None = None
        last_fetch_time = 0.0
        scroll_offset_commons = 0
        scroll_offset_lords = 0

        with Live(console=console, screen=True, refresh_per_second=1) as live:
            while not stop_event.is_set():
                try:
                    # Fetch new data when interval has elapsed
                    now_mono = asyncio.get_event_loop().time()
                    if data is None or (now_mono - last_fetch_time) >= interval:
                        data = await _fetch_all_data(house)
                        last_fetch_time = now_mono
                        scroll_offset_commons = 0
                        scroll_offset_lords = 0

                    dashboard = _render_dashboard(
                        data,
                        scroll_offset_commons=scroll_offset_commons,
                        scroll_offset_lords=scroll_offset_lords,
                    )
                    live.update(dashboard)

                    # Compute whether scrolling is needed
                    calendar_events = data.get("calendar", [])
                    terminal_height = shutil.get_terminal_size().lines
                    chamber_panels_exist = "commons" in data or "lords" in data
                    if chamber_panels_exist:
                        max_chamber = int(terminal_height * _CHAMBER_MAX_FRACTION)
                        chamber_size = max(_CHAMBER_MIN_HEIGHT, min(max_chamber, max_chamber))
                    else:
                        chamber_size = _CHAMBER_MIN_HEIGHT
                    available_rows = max(terminal_height - 3 - chamber_size - 5, 3)

                    both_houses = "commons" in data and "lords" in data
                    if both_houses and calendar_events:
                        commons_events, lords_events = _split_events_by_house(calendar_events)
                        if len(commons_events) > available_rows:
                            scroll_offset_commons += 1
                        if len(lords_events) > available_rows:
                            scroll_offset_lords += 1
                    else:
                        total_events = len(calendar_events)
                        if total_events > available_rows:
                            if "commons" in data:
                                scroll_offset_commons += 1
                            else:
                                scroll_offset_lords += 1
                except Exception:
                    # Don't crash on transient errors
                    pass

                # Wait for scroll interval or stop signal
                try:
                    await asyncio.wait_for(stop_event.wait(), timeout=SCROLL_INTERVAL)
                    break  # Stop event was set
                except TimeoutError:
                    continue  # Timeout expired, continue
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
        help="Refresh interval in seconds (minimum 30)",
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
