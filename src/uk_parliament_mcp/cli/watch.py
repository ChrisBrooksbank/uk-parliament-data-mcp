"""Live Parliament dashboard with auto-refresh."""

from __future__ import annotations

import asyncio
import json
import queue
import shutil
import signal
import sys
import threading
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
POLL_INTERVAL = 0.15  # Seconds between key polls (150ms for responsive input)


def _read_keys_windows(key_queue: queue.Queue[str], stop_reading: threading.Event) -> None:
    """Read keys on Windows using msvcrt."""
    import msvcrt
    import time

    while not stop_reading.is_set():
        if msvcrt.kbhit():  # type: ignore[attr-defined,unused-ignore]
            ch = msvcrt.getwch()  # type: ignore[attr-defined,unused-ignore]
            if ch == "\xe0" or ch == "\x00":
                # Arrow key prefix — read the second byte
                ch2 = msvcrt.getwch()  # type: ignore[attr-defined,unused-ignore]
                if ch2 == "H":
                    key_queue.put("up")
                elif ch2 == "P":
                    key_queue.put("down")
            elif ch == " ":
                key_queue.put("space")
            elif ch.lower() == "q":
                key_queue.put("q")
        time.sleep(0.05)


def _read_keys_unix(key_queue: queue.Queue[str], stop_reading: threading.Event) -> None:
    """Read keys on Unix using termios/tty."""
    import select
    import termios
    import time
    import tty

    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)  # type: ignore[attr-defined,unused-ignore]
    try:
        tty.setcbreak(fd)  # type: ignore[attr-defined,unused-ignore]
        while not stop_reading.is_set():
            if select.select([sys.stdin], [], [], 0.05)[0]:
                ch = sys.stdin.read(1)
                if ch == "\x1b":
                    # Escape sequence — try to read bracket + code
                    if select.select([sys.stdin], [], [], 0.05)[0]:
                        ch2 = sys.stdin.read(1)
                        if ch2 == "[" and select.select([sys.stdin], [], [], 0.05)[0]:
                            ch3 = sys.stdin.read(1)
                            if ch3 == "A":
                                key_queue.put("up")
                            elif ch3 == "B":
                                key_queue.put("down")
                elif ch == " ":
                    key_queue.put("space")
                elif ch.lower() == "q":
                    key_queue.put("q")
            else:
                time.sleep(0.05)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)  # type: ignore[attr-defined,unused-ignore]


def _start_key_reader(
    key_queue: queue.Queue[str], stop_reading: threading.Event
) -> threading.Thread:
    """Start a daemon thread that reads keyboard input.

    Args:
        key_queue: Queue to put normalized key names into.
        stop_reading: Event to signal the reader to stop.

    Returns:
        The started daemon thread.
    """
    target = _read_keys_windows if sys.platform == "win32" else _read_keys_unix
    thread = threading.Thread(target=target, args=(key_queue, stop_reading), daemon=True)
    thread.start()
    return thread


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
_SIDE_BY_SIDE_MIN_WIDTH = 80  # Stack panels vertically below this terminal width


def _estimate_chamber_height(panel: Panel, width: int | None = None) -> int:
    """Estimate the number of terminal rows a chamber panel needs.

    Uses Rich's own rendering engine to measure height accurately,
    accounting for text wrapping at the given width.

    Args:
        panel: Rich Panel produced by _render_chamber_panel.
        width: Available width in columns for the panel.  When two
            panels are side-by-side this should be roughly half the
            terminal width.  ``None`` falls back to the full terminal
            width.

    Returns:
        Estimated row count including panel borders and wrapped lines.
    """
    if width is None:
        width = shutil.get_terminal_size().columns
    # Use a hidden Console to render the panel at the target width and
    # count the lines it actually produces (including wrapping).
    console = Console(width=width, file=None, force_terminal=True)
    lines = list(console.render_lines(panel, console.options.update_width(width)))
    return len(lines)


def _render_dashboard(
    data: dict[str, Any],
    scroll_offset_commons: int = 0,
    scroll_offset_lords: int = 0,
    *,
    auto_scroll_paused: bool = False,
) -> Layout:
    """Render the full dashboard layout.

    Args:
        data: Dict with commons, lords, and calendar data.
        scroll_offset_commons: Scroll position for Commons calendar auto-scrolling.
        scroll_offset_lords: Scroll position for Lords calendar auto-scrolling.
        auto_scroll_paused: Whether auto-scrolling is paused by the user.

    Returns:
        Rich Layout for the dashboard.
    """
    now = datetime.now().strftime("%H:%M:%S")
    layout = Layout()

    # Header
    paused_indicator = "  PAUSED" if auto_scroll_paused else ""
    header = Text(
        f"  UK Parliament Live | Last updated: {now}{paused_indicator}"
        f" | \u2191\u2193 scroll  space pause  q quit",
        style="bold white on blue",
    )

    # Chamber panels — build and measure
    terminal_width = shutil.get_terminal_size().columns
    terminal_height = shutil.get_terminal_size().lines
    chamber_panels: list[Panel] = []
    chambers = Layout()
    both_houses = "commons" in data and "lords" in data
    # Stack panels vertically on narrow terminals to avoid excessive wrapping
    stack_chambers = both_houses and terminal_width < _SIDE_BY_SIDE_MIN_WIDTH
    if "commons" in data:
        commons_panel = _render_chamber_panel(data.get("commons"), "House of Commons")
        chamber_panels.append(commons_panel)
        if "lords" in data:
            lords_panel = _render_chamber_panel(data.get("lords"), "House of Lords")
            chamber_panels.append(lords_panel)
            if stack_chambers:
                chambers.split_column(Layout(commons_panel), Layout(lords_panel))
            else:
                chambers.split_row(Layout(commons_panel), Layout(lords_panel))
        else:
            chambers.update(commons_panel)
    elif "lords" in data:
        lords_panel = _render_chamber_panel(data.get("lords"), "House of Lords")
        chamber_panels.append(lords_panel)
        chambers.update(lords_panel)

    # Size the chamber section to fit content, give calendar the rest
    max_chamber = int(terminal_height * _CHAMBER_MAX_FRACTION)
    if chamber_panels:
        # Measure panels at their actual rendered width
        panel_width = terminal_width // 2 if both_houses and not stack_chambers else terminal_width
        if stack_chambers:
            # Stacked: sum of both panel heights
            total = sum(
                _estimate_chamber_height(p, width=panel_width) for p in chamber_panels
            )
            chamber_size = max(_CHAMBER_MIN_HEIGHT, min(total, max_chamber))
        else:
            tallest = max(
                _estimate_chamber_height(p, width=panel_width) for p in chamber_panels
            )
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
            paused=auto_scroll_paused,
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
            paused=auto_scroll_paused,
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
            paused=auto_scroll_paused,
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

    Keyboard controls:
        Up/Down arrows: Scroll calendar events manually (pauses auto-scroll).
        Space: Toggle auto-scroll pause/resume.
        q: Quit the dashboard.

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

    # Key reader infrastructure
    key_queue: queue.Queue[str] = queue.Queue()
    stop_reading = threading.Event()
    reader_thread: threading.Thread | None = None

    try:
        reader_thread = _start_key_reader(key_queue, stop_reading)

        data: dict[str, Any] | None = None
        last_fetch_time = 0.0
        scroll_offset_commons = 0
        scroll_offset_lords = 0
        auto_scroll = True
        elapsed_since_scroll = 0.0

        with Live(console=console, screen=True, refresh_per_second=4) as live:
            while not stop_event.is_set():
                try:
                    # Fetch new data when interval has elapsed
                    now_mono = asyncio.get_event_loop().time()
                    if data is None or (now_mono - last_fetch_time) >= interval:
                        data = await _fetch_all_data(house)
                        last_fetch_time = now_mono
                        scroll_offset_commons = 0
                        scroll_offset_lords = 0

                    # Process queued key presses
                    while True:
                        try:
                            key = key_queue.get_nowait()
                        except queue.Empty:
                            break
                        if key == "q":
                            stop_event.set()
                        elif key == "up":
                            scroll_offset_commons = max(0, scroll_offset_commons - 1)
                            scroll_offset_lords = max(0, scroll_offset_lords - 1)
                            auto_scroll = False
                        elif key == "down":
                            scroll_offset_commons += 1
                            scroll_offset_lords += 1
                            auto_scroll = False
                        elif key == "space":
                            auto_scroll = not auto_scroll
                            if auto_scroll:
                                elapsed_since_scroll = 0.0

                    dashboard = _render_dashboard(
                        data,
                        scroll_offset_commons=scroll_offset_commons,
                        scroll_offset_lords=scroll_offset_lords,
                        auto_scroll_paused=not auto_scroll,
                    )
                    live.update(dashboard)

                    # Auto-scroll timer
                    if auto_scroll:
                        elapsed_since_scroll += POLL_INTERVAL
                        if elapsed_since_scroll >= SCROLL_INTERVAL:
                            elapsed_since_scroll = 0.0
                            # Compute whether scrolling is needed
                            calendar_events = data.get("calendar", [])
                            terminal_height = shutil.get_terminal_size().lines
                            chamber_panels_exist = "commons" in data or "lords" in data
                            if chamber_panels_exist:
                                max_chamber = int(terminal_height * _CHAMBER_MAX_FRACTION)
                                chamber_size = max(
                                    _CHAMBER_MIN_HEIGHT,
                                    min(max_chamber, max_chamber),
                                )
                            else:
                                chamber_size = _CHAMBER_MIN_HEIGHT
                            available_rows = max(terminal_height - 3 - chamber_size - 5, 3)

                            both_houses = "commons" in data and "lords" in data
                            if both_houses and calendar_events:
                                commons_events, lords_events = _split_events_by_house(
                                    calendar_events
                                )
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

                # Wait for poll interval or stop signal
                try:
                    await asyncio.wait_for(stop_event.wait(), timeout=POLL_INTERVAL)
                    break  # Stop event was set
                except TimeoutError:
                    continue  # Timeout expired, continue
    except KeyboardInterrupt:
        pass  # Clean exit on Ctrl+C
    finally:
        stop_reading.set()
        if reader_thread is not None:
            reader_thread.join(timeout=1.0)


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

    Keyboard controls:
      Up/Down arrows  Scroll calendar events (pauses auto-scroll)
      Space           Pause / resume auto-scrolling
      q               Quit the dashboard
      Ctrl+C          Quit the dashboard

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
