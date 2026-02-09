"""Rich rendering functions for CLI commands.

Shared rendering helpers extracted from watch.py, plus domain-specific
renderers for live and composite commands.
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

# ---------------------------------------------------------------------------
# Slide type mapping (shared with watch.py)
# ---------------------------------------------------------------------------

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


def _house_color(house_name: str) -> str:
    """Return a Rich color for the given house name.

    Args:
        house_name: House name string (e.g. "House of Commons", "Commons", "Lords").

    Returns:
        Rich color string: "green" for Commons, "red" for Lords, "white" fallback.
    """
    lower = house_name.lower()
    if "commons" in lower:
        return "green"
    if "lords" in lower:
        return "red"
    return "white"


_PARLIAMENT_TV_URLS: dict[str, str] = {
    "commons": "https://www.parliamentlive.tv/Commons",
    "lords": "https://www.parliamentlive.tv/Lords",
}


def _parliament_tv_subtitle(house_name: str) -> Text:
    """Return a Rich Text subtitle linking to Parliament TV for the given house.

    Args:
        house_name: House name string (e.g. "House of Commons", "Lords").

    Returns:
        Rich Text object with dim link to the appropriate Parliament TV URL.
    """
    lower = house_name.lower()
    if "commons" in lower:
        url = _PARLIAMENT_TV_URLS["commons"]
    elif "lords" in lower:
        url = _PARLIAMENT_TV_URLS["lords"]
    else:
        url = "https://www.parliamentlive.tv"
    display = url.replace("https://www.", "")
    return Text(display, style=f"italic cyan link {url}")


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


# ---------------------------------------------------------------------------
# Slide / member / scrolling message renderers
# ---------------------------------------------------------------------------


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


def _render_scrolling_messages(messages: list[dict[str, Any]], text: Text) -> None:
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


# ---------------------------------------------------------------------------
# Chamber panel renderer (shared with watch.py)
# ---------------------------------------------------------------------------


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
        return Panel(
            content,
            title=f"[bold]{house_name}[/bold]",
            subtitle=_parliament_tv_subtitle(house_name),
            border_style="dim",
        )

    # Check if annunciator is disabled
    if data.get("annunciatorDisabled"):
        content = Text("Annunciator offline", style="dim italic")
        return Panel(
            content,
            title=f"[bold]{house_name}[/bold]",
            subtitle=_parliament_tv_subtitle(house_name),
            border_style="dim",
        )

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

    color = _house_color(house_name)
    border_style = color if is_active else "dim"
    return Panel(
        text,
        title=f"[bold {color}]{house_name}[/bold {color}]",
        subtitle=_parliament_tv_subtitle(house_name),
        border_style=border_style,
    )


# ---------------------------------------------------------------------------
# Calendar table renderer (shared with watch.py)
# ---------------------------------------------------------------------------


def _calendar_subtitle(
    displayed: int,
    total: int,
    *,
    scrolling: bool = False,
    scroll_offset: int = 0,
    paused: bool = False,
) -> str | None:
    """Return a subtitle string when calendar rows are truncated.

    Args:
        displayed: Number of rows actually shown.
        total: Total number of events available.
        scrolling: Whether auto-scrolling is active.
        scroll_offset: Current scroll position (used for scroll indicator bar).
        paused: Whether auto-scrolling is paused by the user.

    Returns:
        Rich markup string, or None when not truncated.
    """
    if total <= displayed and not scrolling and not paused:
        return None
    parts: list[str] = []
    if total > displayed:
        hidden = total - displayed
        parts.append(f"showing {displayed} of {total} events ({hidden} more)")
    if scrolling and total > 0:
        # Build a 5-char scroll position bar
        track_len = 5
        position = scroll_offset % total if total > 0 else 0
        slot = int(position / total * track_len) if total > 0 else 0
        slot = min(slot, track_len - 1)
        bar = "".join("\u2588" if i == slot else "\u2591" for i in range(track_len))
        label = "paused" if paused else "scrolling"
        parts.append(f"{bar} {label}")
    elif scrolling:
        label = "paused" if paused else "auto-scrolling"
        parts.append(label)
    elif paused:
        parts.append("paused")
    return "[dim]" + " | ".join(parts) + "[/dim]" if parts else None


def _extract_event_time(event: dict[str, Any]) -> str:
    """Extract an "HH:MM" time string from an event dict.

    Args:
        event: Calendar event dict.

    Returns:
        Time string like "14:30", or "" if no parseable time found.
        Returns "" for "00:00" (all-day events with no real time).
    """
    for key in ["StartTime", "startTime", "StartDate", "startDate"]:
        if key in event and event[key]:
            raw = str(event[key])
            if "T" in raw:
                time_part = raw.split("T")[1][:5]
                if time_part == "00:00":
                    return ""
                return time_part
            if len(raw) > 5:
                return raw[:5]
            return raw
    return ""


def _split_events_by_house(
    events: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Split calendar events into Commons and Lords lists.

    Events with no house, empty house, or unrecognised house (e.g. "Joint")
    are included in **both** lists so no events are lost.

    Args:
        events: List of calendar event dicts.

    Returns:
        Tuple of (commons_events, lords_events).
    """
    commons: list[dict[str, Any]] = []
    lords: list[dict[str, Any]] = []
    for event in events:
        house_str = ""
        for key in ["House", "house"]:
            if key in event and event[key]:
                house_str = str(event[key])
                break
        lower = house_str.lower()
        if "commons" in lower:
            commons.append(event)
        elif "lords" in lower:
            lords.append(event)
        else:
            # Joint / empty / unrecognised → both lists
            commons.append(event)
            lords.append(event)
    return commons, lords


def _render_calendar_table(
    events: list[dict[str, Any]],
    max_rows: int | None = None,
    now: datetime | None = None,
    scroll_offset: int = 0,
    include_house_column: bool = True,
) -> tuple[Table | Text, int]:
    """Render today's business as a Rich table.

    Args:
        events: List of calendar event dicts.
        max_rows: Maximum number of rows to display. None means show all.
        now: Current datetime for time-tracking highlight. None disables
            sorting/highlighting (backward-compatible).
        scroll_offset: When > 0 and events are truncated, use as the window
            start position with wrap-around (carousel effect). When 0, use
            existing current-event-centered behavior.

    Returns:
        Tuple of (Rich Table or Text if no events, total event count).
    """
    if not events:
        return Text("No events scheduled for today", style="dim italic"), 0

    total_count = len(events)

    # Sort by start time when time-tracking is enabled
    if now is not None:
        events = sorted(events, key=lambda e: _extract_event_time(e) or "99:99")

    # Determine current-event index
    current_idx: int | None = None
    if now is not None:
        now_hm = now.strftime("%H:%M")
        last_started: int | None = None
        first_future: int | None = None
        for i, event in enumerate(events):
            t = _extract_event_time(event)
            if not t:
                continue
            if t <= now_hm:
                last_started = i
            elif first_future is None:
                first_future = i
        if last_started is not None:
            current_idx = last_started
        elif first_future is not None:
            current_idx = first_future

    # Window events around current index when truncating
    if max_rows is not None and max_rows < total_count:
        if scroll_offset > 0:
            # Carousel-style scrolling: use offset as window start, wrap around
            start = scroll_offset % total_count
            end = start + max_rows
            if end <= total_count:
                display_events = events[start:end]
            else:
                # Wrap around
                display_events = events[start:] + events[: end - total_count]
            # Adjust current_idx relative to the window
            if current_idx is not None:
                # Check if current_idx is in the visible window
                if end <= total_count:
                    current_idx = current_idx - start if start <= current_idx < end else None
                else:
                    # Wrapped window
                    wrap_end = end - total_count
                    if current_idx >= start:
                        current_idx = current_idx - start
                    elif current_idx < wrap_end:
                        current_idx = (total_count - start) + current_idx
                    else:
                        current_idx = None
        elif now is not None and current_idx is not None:
            half = max_rows // 2
            start = max(0, current_idx - half)
            end = start + max_rows
            if end > total_count:
                end = total_count
                start = max(0, end - max_rows)
            display_events = events[start:end]
            # Adjust current_idx relative to the window
            current_idx = current_idx - start
        else:
            display_events = events[:max_rows]
    else:
        display_events = events

    table = Table(
        show_header=True,
        header_style="bold",
        expand=True,
    )
    table.add_column("Time", width=7, style="cyan", no_wrap=True)
    if include_house_column:
        table.add_column("House", width=7, no_wrap=True)
    table.add_column("Event", ratio=1, overflow="ellipsis")
    table.add_column("Type", max_width=16)
    table.add_column("Location", max_width=20)
    table.add_column("Category", max_width=14)

    for row_idx, event in enumerate(display_events):
        time_str = _extract_event_time(event)

        house_str = ""
        for key in ["House", "house"]:
            if key in event and event[key]:
                house_str = str(event[key])
                break

        event_str = ""
        for key in ["Description", "description", "Title", "title", "Name", "name"]:
            if key in event and event[key]:
                event_str = str(event[key])
                break

        type_str = ""
        for key in ["Type", "type"]:
            if key in event and event[key]:
                type_str = str(event[key])
                break

        location_str = ""
        for key in ["Location", "location"]:
            if key in event and event[key]:
                location_str = str(event[key])
                break

        category_str = ""
        for key in ["Category", "category"]:
            if key in event and event[key]:
                category_str = str(event[key])
                break

        # Highlight current event
        is_current = current_idx is not None and row_idx == current_idx
        if is_current:
            time_display = f"> {time_str}" if time_str else "> "
            row_style = "bold"
        else:
            time_display = f"  {time_str}" if time_str else ""
            row_style = "" if row_idx % 2 == 0 else "dim"

        if include_house_column:
            house_text = Text(house_str, style=_house_color(house_str))
            table.add_row(
                time_display,
                house_text,
                event_str,
                type_str,
                location_str,
                category_str,
                style=row_style,
            )
        else:
            table.add_row(
                time_display,
                event_str,
                type_str,
                location_str,
                category_str,
                style=row_style,
            )

    return table, total_count


# ---------------------------------------------------------------------------
# JSON parsing helper
# ---------------------------------------------------------------------------


def _parse_api_response(response_str: str) -> dict[str, Any] | None:
    """Parse API response, extracting data field.

    Args:
        response_str: Raw JSON response string from get_result.

    Returns:
        Parsed data dict, or None on error.
    """
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


# ---------------------------------------------------------------------------
# Live command renderers
# ---------------------------------------------------------------------------


def render_chamber_now(result_json: str, house_name: str) -> None:
    """Render a chamber status panel from a raw API response and print it.

    Args:
        result_json: Raw JSON string from get_result for a Now API endpoint.
        house_name: "House of Commons" or "House of Lords".
    """
    data = _parse_api_response(result_json)
    panel = _render_chamber_panel(data, house_name)
    Console().print(panel)


def render_calendar(result_json: str) -> None:
    """Render a calendar table from a raw API response and print it.

    Args:
        result_json: Raw JSON string from get_result for a WhatSON API endpoint.
    """
    data = _parse_api_response(result_json)
    if data is None:
        events: list[dict[str, Any]] = []
    elif isinstance(data, list):
        events = data
    else:
        # Calendar API may return events in various structures
        events = []
        for key in ["items", "results", "data"]:
            if key in data and isinstance(data[key], list):
                events = list(data[key])
                break
        if not events and isinstance(data, dict):
            events = [data]

    table_content, total_count = _render_calendar_table(events, now=datetime.now())
    displayed = min(len(events), total_count)
    subtitle = _calendar_subtitle(displayed, total_count)
    panel = Panel(
        table_content,
        title="[bold]Calendar[/bold]",
        subtitle=subtitle,
    )
    Console().print(panel)


# ---------------------------------------------------------------------------
# Composite command renderers
# ---------------------------------------------------------------------------


def render_mp_profile(result_json: str) -> None:
    """Render a comprehensive MP profile with rich formatting.

    Args:
        result_json: JSON string from _get_mp_profile_async.
    """
    try:
        data = json.loads(result_json)
    except (json.JSONDecodeError, TypeError):
        Console().print("[red]Failed to parse MP profile data[/red]")
        return

    if "error" in data:
        Console().print(f"[red]{data['error']}[/red]")
        return

    console = Console()

    # Header panel: name, party, constituency
    basic = data.get("basic_info", {})
    name = basic.get("nameDisplayAs", "Unknown")
    party_name = ""
    party_info = basic.get("latestParty")
    if isinstance(party_info, dict):
        party_name = party_info.get("name", "")
    constituency = ""
    membership = basic.get("latestHouseMembership")
    if isinstance(membership, dict):
        constituency = membership.get("membershipFrom", "")
    member_id = data.get("member_id", "")

    header_text = Text()
    header_text.append(name, style="bold white")
    parts: list[str] = []
    if party_name:
        parts.append(party_name)
    if constituency:
        parts.append(constituency)
    if parts:
        header_text.append(f"\n{' | '.join(parts)}", style="dim")
    if member_id:
        header_text.append(f"\nMember ID: {member_id}", style="dim")

    console.print(Panel(header_text, title="[bold]MP Profile[/bold]", border_style="blue"))

    # Biography section
    bio = data.get("biography", {})
    if isinstance(bio, dict):
        bio_value = bio.get("value", bio)
        if isinstance(bio_value, dict):
            entries = bio_value.get("biographyEntries", [])
            if entries and isinstance(entries, list):
                bio_text = Text()
                for entry in entries[:10]:
                    if isinstance(entry, dict):
                        cat = entry.get("category", "")
                        val = entry.get("entry", "")
                        if cat or val:
                            bio_text.append(f"  {cat}: ", style="bold")
                            bio_text.append(f"{val}\n")
                if bio_text.plain.strip():
                    console.print(
                        Panel(bio_text, title="[bold]Biography[/bold]", border_style="dim")
                    )

    # Registered interests
    # Interests API returns flat items: each item has .category (object with .name)
    # and .summary (the interest description).
    interests = data.get("registered_interests", {})
    if isinstance(interests, dict):
        interest_items = interests.get("items", [])
        if interest_items and isinstance(interest_items, list):
            table = Table(
                show_header=True, header_style="bold", expand=True, row_styles=["", "dim"]
            )
            table.add_column("Category", ratio=1)
            table.add_column("Interest", ratio=2)
            for item in interest_items[:20]:
                if isinstance(item, dict):
                    cat_info = item.get("category")
                    if isinstance(cat_info, dict):
                        cat = cat_info.get("name", "")
                    else:
                        cat = str(cat_info) if cat_info else ""
                    summary = item.get("summary", "")
                    table.add_row(cat, str(summary) if summary else "")
            if table.row_count > 0:
                console.print(
                    Panel(table, title="[bold]Registered Interests[/bold]", border_style="dim")
                )

    # Recent voting
    voting = data.get("recent_voting", {})
    if isinstance(voting, dict):
        vote_items = voting.get("items", [])
        if vote_items and isinstance(vote_items, list):
            table = Table(
                show_header=True, header_style="bold", expand=True, row_styles=["", "dim"]
            )
            table.add_column("Div ID", style="cyan", no_wrap=True)
            table.add_column("Title", ratio=1)
            table.add_column("Date", width=10)
            table.add_column("Vote", width=10)
            for item in vote_items[:15]:
                if isinstance(item, dict):
                    value = item.get("value", item)
                    if isinstance(value, dict):
                        div_num = value.get(
                            "id", value.get("divisionId", value.get("divisionNumber", ""))
                        )
                        div_id = value.get("id", value.get("divisionId", ""))
                        title = str(value.get("title", value.get("Title", "")))
                        date = str(value.get("date", value.get("Date", "")))[:10]
                        voted_aye = value.get("memberVotedAye", value.get("inAffirmativeLobby"))
                        vote_str = "Aye" if voted_aye else ("No" if voted_aye is False else "")
                        div_text = Text(str(div_num))
                        if div_id:
                            div_text.stylize(
                                f"link https://votes.parliament.uk/Votes/Commons/Division/{div_id}"
                            )
                        table.add_row(div_text, title, date, vote_str)
            if table.row_count > 0:
                console.print(Panel(table, title="[bold]Recent Votes[/bold]", border_style="dim"))


def render_check_vote(result_json: str) -> None:
    """Render an MP vote check with rich formatting.

    Args:
        result_json: JSON string from _check_mp_vote_async.
    """
    try:
        data = json.loads(result_json)
    except (json.JSONDecodeError, TypeError):
        Console().print("[red]Failed to parse vote data[/red]")
        return

    if "error" in data:
        Console().print(f"[red]{data['error']}[/red]")
        return

    console = Console()

    # Header: MP name, party, topic
    member_info = data.get("member_info", {})
    name = member_info.get("nameDisplayAs", "Unknown")
    topic = data.get("topic_searched", "")

    header_text = Text()
    header_text.append(name, style="bold white")
    if topic:
        header_text.append(f"\nTopic: {topic}", style="dim")

    console.print(Panel(header_text, title="[bold]Vote Check[/bold]", border_style="blue"))

    # Divisions table
    divisions = data.get("divisions", {})
    if isinstance(divisions, dict):
        div_items = divisions.get("items", divisions.get("results", []))
        if not isinstance(div_items, list):
            div_items = []
    elif isinstance(divisions, list):
        div_items = divisions
    else:
        div_items = []

    if div_items:
        table = Table(show_header=True, header_style="bold", expand=True, row_styles=["", "dim"])
        table.add_column("ID", style="cyan", width=8)
        table.add_column("Title", ratio=1)
        table.add_column("Date", width=10)
        table.add_column("Ayes", width=6, justify="right")
        table.add_column("Noes", width=6, justify="right")
        for div in div_items[:20]:
            if isinstance(div, dict):
                div_id = div.get("DivisionId", div.get("divisionId", ""))
                title = str(div.get("Title", div.get("title", "")))
                date = str(div.get("Date", div.get("date", "")))[:10]
                ayes = str(div.get("AyeCount", div.get("ayeCount", "")))
                noes = str(div.get("NoCount", div.get("noCount", "")))
                div_text = Text(str(div_id))
                if div_id:
                    div_text.stylize(
                        f"link https://votes.parliament.uk/Votes/Commons/Division/{div_id}"
                    )
                table.add_row(div_text, title, date, ayes, noes)
        if table.row_count > 0:
            console.print(Panel(table, title="[bold]Divisions[/bold]", border_style="dim"))
        else:
            console.print("[dim]No divisions found for this topic[/dim]")
    else:
        console.print("[dim]No divisions found for this topic[/dim]")


def render_bill_overview(result_json: str) -> None:
    """Render a comprehensive bill overview with rich formatting.

    Args:
        result_json: JSON string from _get_bill_overview_async.
    """
    try:
        data = json.loads(result_json)
    except (json.JSONDecodeError, TypeError):
        Console().print("[red]Failed to parse bill data[/red]")
        return

    if "error" in data:
        Console().print(f"[red]{data['error']}[/red]")
        return

    console = Console()

    # Header: bill title, ID, current stage
    summary = data.get("search_summary", {})
    details = data.get("details", {})
    detail_value = details.get("value", details) if isinstance(details, dict) else {}

    title = summary.get("shortTitle", detail_value.get("shortTitle", "Unknown"))
    bill_id = data.get("bill_id", "")
    current_stage = ""
    stage_info = summary.get("currentStage", detail_value.get("currentStage"))
    if isinstance(stage_info, dict):
        current_stage = str(stage_info.get("description", stage_info.get("stageName", "")))
    elif isinstance(stage_info, str):
        current_stage = stage_info

    header_text = Text()
    header_text.append(title, style="bold white")
    parts: list[str] = []
    if bill_id:
        parts.append(f"Bill ID: {bill_id}")
    if current_stage:
        parts.append(f"Stage: {current_stage}")
    if parts:
        header_text.append(f"\n{' | '.join(parts)}", style="dim")

    other_matches = data.get("other_matches", 0)
    if other_matches:
        header_text.append(f"\n{other_matches} other matching bill(s)", style="dim italic")

    console.print(Panel(header_text, title="[bold]Bill Overview[/bold]", border_style="blue"))

    # Stages table
    stages = data.get("stages", {})
    if isinstance(stages, dict):
        stage_items = stages.get("items", [])
    elif isinstance(stages, list):
        stage_items = stages
    else:
        stage_items = []

    if stage_items and isinstance(stage_items, list):
        table = Table(show_header=True, header_style="bold", expand=True, row_styles=["", "dim"])
        table.add_column("Stage", ratio=1)
        table.add_column("House", width=8)
        table.add_column("Date", width=10)
        for stage in stage_items:
            if isinstance(stage, dict):
                stage_name = ""
                sittings = stage.get("stageSittings", [])
                s_info = stage.get("stageType") or stage.get("description") or {}
                if isinstance(s_info, dict):
                    stage_name = str(s_info.get("name", s_info.get("description", "")))
                elif isinstance(s_info, str):
                    stage_name = s_info
                house = ""
                house_info = stage.get("house") or stage.get("stageHouse")
                if isinstance(house_info, dict):
                    house = house_info.get("name", "")
                elif isinstance(house_info, str):
                    house = house_info
                elif isinstance(house_info, int):
                    house = "Commons" if house_info == 1 else "Lords"
                date = ""
                if isinstance(sittings, list) and sittings:
                    first_sitting = sittings[0]
                    if isinstance(first_sitting, dict):
                        date = str(first_sitting.get("date", ""))[:10]
                if not date:
                    date = str(stage.get("date", ""))[:10]
                table.add_row(stage_name, house, date)
        if table.row_count > 0:
            console.print(Panel(table, title="[bold]Legislative Stages[/bold]", border_style="dim"))

    # Publications
    pubs = data.get("publications", {})
    if isinstance(pubs, dict):
        pub_items = pubs.get("items", [])
    elif isinstance(pubs, list):
        pub_items = pubs
    else:
        pub_items = []

    if pub_items and isinstance(pub_items, list):
        pub_text = Text()
        for pub in pub_items[:10]:
            if isinstance(pub, dict):
                pub_title = pub.get("title", pub.get("displayName", ""))
                pub_type = pub.get("publicationType", pub.get("type", ""))
                if isinstance(pub_type, dict):
                    pub_type = pub_type.get("name", "")
                if pub_title:
                    pub_text.append(f"  {pub_title}", style="bold")
                    if pub_type:
                        pub_text.append(f"  ({pub_type})", style="dim")
                    pub_text.append("\n")
        if pub_text.plain.strip():
            console.print(Panel(pub_text, title="[bold]Publications[/bold]", border_style="dim"))


def render_committee_summary(result_json: str) -> None:
    """Render a comprehensive committee summary with rich formatting.

    Args:
        result_json: JSON string from _get_committee_summary_async.
    """
    try:
        data = json.loads(result_json)
    except (json.JSONDecodeError, TypeError):
        Console().print("[red]Failed to parse committee data[/red]")
        return

    if "error" in data:
        Console().print(f"[red]{data['error']}[/red]")
        return

    console = Console()

    # Header: committee name, house
    summary = data.get("search_summary", {})
    details = data.get("details", {})
    detail_value = details.get("value", details) if isinstance(details, dict) else {}

    name = summary.get("name", detail_value.get("name", "Unknown"))
    committee_id = data.get("committee_id", "")
    house = ""
    house_info = summary.get("house", detail_value.get("house"))
    if isinstance(house_info, str):
        house = house_info
    elif isinstance(house_info, int):
        house = "Commons" if house_info == 1 else "Lords"
    is_commons = summary.get("isCommons", detail_value.get("isCommons"))
    if not house and is_commons is not None:
        house = "Commons" if is_commons else "Lords"

    header_text = Text()
    header_text.append(name, style="bold white")
    parts: list[str] = []
    if house:
        parts.append(house)
    if committee_id:
        parts.append(f"ID: {committee_id}")
    if parts:
        header_text.append(f"\n{' | '.join(parts)}", style="dim")

    other_matches = data.get("other_matches", 0)
    if other_matches:
        header_text.append(f"\n{other_matches} other matching committee(s)", style="dim italic")

    console.print(Panel(header_text, title="[bold]Committee Summary[/bold]", border_style="blue"))

    # Oral evidence table
    oral = data.get("oral_evidence", {})
    if isinstance(oral, dict):
        oral_items = oral.get("items", [])
    elif isinstance(oral, list):
        oral_items = oral
    else:
        oral_items = []

    if oral_items and isinstance(oral_items, list):
        table = Table(show_header=True, header_style="bold", expand=True, row_styles=["", "dim"])
        table.add_column("Date", width=10)
        table.add_column("Title", ratio=1)
        table.add_column("Witnesses", ratio=1)
        for item in oral_items[:10]:
            if isinstance(item, dict):
                date = str(item.get("date", item.get("evidenceDate", "")))[:10]
                title = str(item.get("title", item.get("activityName", "")))
                witnesses = ""
                witness_list = item.get("witnesses", [])
                if isinstance(witness_list, list):
                    names = [
                        str(w.get("name", ""))
                        for w in witness_list
                        if isinstance(w, dict) and w.get("name")
                    ]
                    witnesses = ", ".join(names[:3])
                    if len(names) > 3:
                        witnesses += f" +{len(names) - 3} more"
                table.add_row(date, title, witnesses)
        if table.row_count > 0:
            console.print(Panel(table, title="[bold]Oral Evidence[/bold]", border_style="dim"))

    # Written evidence table
    written = data.get("written_evidence", {})
    if isinstance(written, dict):
        written_items = written.get("items", [])
    elif isinstance(written, list):
        written_items = written
    else:
        written_items = []

    if written_items and isinstance(written_items, list):
        table = Table(show_header=True, header_style="bold", expand=True, row_styles=["", "dim"])
        table.add_column("Date", width=10)
        table.add_column("Title", ratio=1)
        table.add_column("Author", ratio=1)
        for item in written_items[:10]:
            if isinstance(item, dict):
                date = str(item.get("dateReceived", item.get("date", "")))[:10]
                title = str(item.get("title", ""))
                author = str(item.get("authorName", item.get("author", "")))
                table.add_row(date, title, author)
        if table.row_count > 0:
            console.print(Panel(table, title="[bold]Written Evidence[/bold]", border_style="dim"))

    # Publications
    pubs = data.get("publications", {})
    if isinstance(pubs, dict):
        pub_items = pubs.get("items", [])
    elif isinstance(pubs, list):
        pub_items = pubs
    else:
        pub_items = []

    if pub_items and isinstance(pub_items, list):
        pub_text = Text()
        for pub in pub_items[:10]:
            if isinstance(pub, dict):
                pub_title = pub.get("title", pub.get("displayName", ""))
                pub_type = pub.get("publicationType", pub.get("type", ""))
                if isinstance(pub_type, dict):
                    pub_type = pub_type.get("name", "")
                if pub_title:
                    pub_text.append(f"  {pub_title}", style="bold")
                    if pub_type:
                        pub_text.append(f"  ({pub_type})", style="dim")
                    pub_text.append("\n")
        if pub_text.plain.strip():
            console.print(Panel(pub_text, title="[bold]Publications[/bold]", border_style="dim"))


def render_my_mp(result_json: str) -> None:
    """Render a 'my MP' profile with rich formatting.

    Args:
        result_json: JSON string from _get_my_mp_async.
    """
    try:
        data = json.loads(result_json)
    except (json.JSONDecodeError, TypeError):
        Console().print("[red]Failed to parse MP data[/red]")
        return

    if "error" in data:
        Console().print(f"[red]{data['error']}[/red]")
        return

    console = Console()

    # --- Header panel: name, party, constituency, majority ---
    basic = data.get("basic_info", {})
    name = basic.get("nameDisplayAs", "Unknown")
    party_name = ""
    party_info = basic.get("latestParty")
    if isinstance(party_info, dict):
        party_name = party_info.get("name", "")
    constituency = ""
    membership_info = basic.get("latestHouseMembership")
    if isinstance(membership_info, dict):
        constituency = membership_info.get("membershipFrom", "")
    member_id = data.get("member_id", "")
    postcode = data.get("postcode", "")

    header_text = Text()
    header_text.append(name, style="bold white")
    parts: list[str] = []
    if party_name:
        parts.append(party_name)
    if constituency:
        parts.append(constituency)
    if member_id:
        parts.append(f"Member ID: {member_id}")
    if parts:
        header_text.append(f"\n{' | '.join(parts)}", style="dim")

    # Extract majority from election result
    election = data.get("latest_election", {})
    election_value = election.get("value", election) if isinstance(election, dict) else {}
    if isinstance(election_value, dict):
        majority = election_value.get("majority")
        election_date = str(election_value.get("electionDate", ""))[:4]
        if majority is not None:
            maj_str = (
                f"Majority: {majority:,}" if isinstance(majority, int) else f"Majority: {majority}"
            )
            if election_date:
                maj_str += f" ({election_date})"
            header_text.append(f"\n{maj_str}", style="dim")

    if postcode:
        header_text.append(f"\nPostcode: {postcode}", style="dim italic")

    console.print(Panel(header_text, title="[bold]Your MP[/bold]", border_style="green"))

    # --- Biography section ---
    bio = data.get("biography", {})
    if isinstance(bio, dict):
        bio_value = bio.get("value", bio)
        if isinstance(bio_value, dict):
            entries = bio_value.get("biographyEntries", [])
            if entries and isinstance(entries, list):
                bio_text = Text()
                for entry in entries[:10]:
                    if isinstance(entry, dict):
                        cat = entry.get("category", "")
                        val = entry.get("entry", "")
                        if cat or val:
                            bio_text.append(f"  {cat}: ", style="bold")
                            bio_text.append(f"{val}\n")
                if bio_text.plain.strip():
                    console.print(
                        Panel(bio_text, title="[bold]Biography[/bold]", border_style="dim")
                    )

    # --- Registered interests ---
    # Interests API returns flat items: each item has .category (object with .name)
    # and .summary (the interest description), plus optional .fields for detail.
    interests = data.get("registered_interests", {})
    if isinstance(interests, dict):
        interest_items = interests.get("items", [])
        if interest_items and isinstance(interest_items, list):
            table = Table(
                show_header=True, header_style="bold", expand=True, row_styles=["", "dim"]
            )
            table.add_column("Category", ratio=1)
            table.add_column("Interest", ratio=2)
            for item in interest_items[:20]:
                if isinstance(item, dict):
                    cat_info = item.get("category")
                    if isinstance(cat_info, dict):
                        cat = cat_info.get("name", "")
                    else:
                        cat = str(cat_info) if cat_info else ""
                    summary = item.get("summary", "")
                    table.add_row(cat, str(summary) if summary else "")
            if table.row_count > 0:
                console.print(
                    Panel(table, title="[bold]Registered Interests[/bold]", border_style="dim")
                )

    # --- Latest election result ---
    if isinstance(election_value, dict):
        candidates = election_value.get("candidates", [])
        if candidates and isinstance(candidates, list):
            election_title = election_value.get("electionTitle", "")
            electorate = election_value.get("electorate")
            turnout = election_value.get("turnout")
            table = Table(
                show_header=True, header_style="bold", expand=True, row_styles=["", "dim"]
            )
            table.add_column("Candidate", ratio=1)
            table.add_column("Party", ratio=1)
            table.add_column("Votes", width=8, justify="right")
            table.add_column("Vote %", width=7, justify="right")
            for candidate in candidates:
                if isinstance(candidate, dict):
                    cand_name = str(candidate.get("name", ""))
                    cand_party = ""
                    cand_party_info = candidate.get("party")
                    if isinstance(cand_party_info, dict):
                        cand_party = cand_party_info.get("name", "")
                    elif isinstance(cand_party_info, str):
                        cand_party = cand_party_info
                    cand_votes = candidate.get("votes", "")
                    vote_share = candidate.get("voteShare")
                    votes_str = (
                        f"{cand_votes:,}" if isinstance(cand_votes, int) else str(cand_votes)
                    )
                    share_str = (
                        f"{vote_share * 100:.1f}%" if isinstance(vote_share, (int, float)) else ""
                    )
                    table.add_row(cand_name, cand_party, votes_str, share_str)
            if table.row_count > 0:
                title = (
                    f"[bold]Latest Election ({election_title})[/bold]"
                    if election_title
                    else "[bold]Latest Election[/bold]"
                )
                subtitle_parts: list[str] = []
                if isinstance(electorate, int):
                    subtitle_parts.append(f"Electorate: {electorate:,}")
                if isinstance(turnout, int):
                    subtitle_parts.append(f"Turnout: {turnout:,}")
                    if isinstance(electorate, int) and electorate > 0:
                        subtitle_parts.append(f"({turnout * 100 / electorate:.1f}%)")
                subtitle = (
                    "[dim]" + " | ".join(subtitle_parts) + "[/dim]" if subtitle_parts else None
                )
                console.print(Panel(table, title=title, subtitle=subtitle, border_style="dim"))

    # --- Recent votes ---
    voting = data.get("recent_voting", {})
    if isinstance(voting, dict):
        vote_items = voting.get("items", [])
        if vote_items and isinstance(vote_items, list):
            table = Table(
                show_header=True, header_style="bold", expand=True, row_styles=["", "dim"]
            )
            table.add_column("Div ID", style="cyan", no_wrap=True)
            table.add_column("Title", ratio=1)
            table.add_column("Date", width=10)
            table.add_column("Vote", width=10)
            for item in vote_items[:15]:
                if isinstance(item, dict):
                    value = item.get("value", item)
                    if isinstance(value, dict):
                        div_num = value.get(
                            "id", value.get("divisionId", value.get("divisionNumber", ""))
                        )
                        div_id = value.get("id", value.get("divisionId", ""))
                        title = str(value.get("title", value.get("Title", "")))
                        date = str(value.get("date", value.get("Date", "")))[:10]
                        voted_aye = value.get("memberVotedAye", value.get("inAffirmativeLobby"))
                        vote_str = "Aye" if voted_aye else ("No" if voted_aye is False else "")
                        div_text = Text(str(div_num))
                        if div_id:
                            div_text.stylize(
                                f"link https://votes.parliament.uk/Votes/Commons/Division/{div_id}"
                            )
                        table.add_row(div_text, title, date, vote_str)
            if table.row_count > 0:
                console.print(Panel(table, title="[bold]Recent Votes[/bold]", border_style="dim"))

    # --- Topic votes (only if --votes was provided) ---
    topic_votes = data.get("topic_votes")
    topic_searched = data.get("topic_searched", "")
    if topic_votes is not None:
        if isinstance(topic_votes, dict):
            div_items = topic_votes.get("items", topic_votes.get("results", []))
            if not isinstance(div_items, list):
                div_items = []
        elif isinstance(topic_votes, list):
            div_items = topic_votes
        else:
            div_items = []

        if div_items:
            table = Table(
                show_header=True, header_style="bold", expand=True, row_styles=["", "dim"]
            )
            table.add_column("ID", style="cyan", width=8)
            table.add_column("Title", ratio=1)
            table.add_column("Date", width=10)
            table.add_column("Ayes", width=6, justify="right")
            table.add_column("Noes", width=6, justify="right")
            for div in div_items[:20]:
                if isinstance(div, dict):
                    div_id = div.get("DivisionId", div.get("divisionId", ""))
                    title = str(div.get("Title", div.get("title", "")))
                    date = str(div.get("Date", div.get("date", "")))[:10]
                    ayes = str(div.get("AyeCount", div.get("ayeCount", "")))
                    noes = str(div.get("NoCount", div.get("noCount", "")))
                    div_text = Text(str(div_id))
                    if div_id:
                        div_text.stylize(
                            f"link https://votes.parliament.uk/Votes/Commons/Division/{div_id}"
                        )
                    table.add_row(div_text, title, date, ayes, noes)
            if table.row_count > 0:
                panel_title = (
                    f'[bold]Votes on "{topic_searched}"[/bold]'
                    if topic_searched
                    else "[bold]Topic Votes[/bold]"
                )
                console.print(Panel(table, title=panel_title, border_style="dim"))
        else:
            if topic_searched:
                console.print(f'[dim]No divisions found for "{topic_searched}"[/dim]')


# ---------------------------------------------------------------------------
# Digest command renderers
# ---------------------------------------------------------------------------


def _safe_list(data: Any, *keys: str) -> list[dict[str, Any]]:
    """Extract a list from data, trying multiple dict keys.

    Args:
        data: Raw parsed data (dict or list).
        keys: Dict keys to probe (e.g. "items", "results", "Response").

    Returns:
        List of dicts, or empty list.
    """
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for k in keys:
            if k in data and isinstance(data[k], list):
                return list(data[k])
    return []


def _section_has_data(data: Any) -> bool:
    """Return True if a digest section has meaningful data."""
    if data is None:
        return False
    if isinstance(data, dict) and data.get("error"):
        return False
    if isinstance(data, dict) and not data:
        return False
    return not (isinstance(data, list) and not data)


def _render_digest_header(data: dict[str, Any]) -> Panel:
    """Render the digest header panel.

    Args:
        data: Full digest payload dict.

    Returns:
        Rich Panel with date/period/house info.
    """
    text = Text()
    period = data.get("period", "day")
    house = data.get("house")

    if period == "week":
        start = data.get("start_date", "")
        end = data.get("end_date", "")
        text.append(f"Week of {start} to {end}", style="bold white")
    else:
        text.append(data.get("date", ""), style="bold white")

    if house:
        text.append(f"  ({house} only)", style="dim")

    # Summary counts
    counts: list[str] = []

    hansard = data.get("hansard")
    if isinstance(hansard, dict):
        hansard_total = hansard.get("TotalResultCount", hansard.get("totalResultCount", 0))
        if hansard_total:
            counts.append(f"Debates: {hansard_total}")

    commons = data.get("commons_divisions")
    lords = data.get("lords_divisions")
    if isinstance(commons, list):
        counts.append(f"Commons divisions: {len(commons)}")
    if isinstance(lords, list):
        counts.append(f"Lords divisions: {len(lords)}")

    bills = data.get("bills")
    if isinstance(bills, dict):
        bill_items = _safe_list(bills, "items", "results")
        if bill_items:
            counts.append(f"Bill sittings: {len(bill_items)}")

    committees = data.get("committees")
    if isinstance(committees, dict):
        comm_items = _safe_list(committees, "items", "results")
        if comm_items:
            counts.append(f"Committee events: {len(comm_items)}")

    statements = data.get("written_statements")
    if isinstance(statements, dict):
        stmt_items = _safe_list(statements, "results", "items")
        if stmt_items:
            counts.append(f"Written statements: {len(stmt_items)}")

    edms = data.get("edms")
    if isinstance(edms, dict):
        edm_items = _safe_list(edms, "Response", "items", "results")
        if edm_items:
            counts.append(f"EDMs: {len(edm_items)}")

    if counts:
        text.append("\n" + " | ".join(counts), style="dim")

    return Panel(text, title="[bold]Parliamentary Digest[/bold]", border_style="green")


def _render_divisions_section(commons: Any, lords: Any) -> Panel | None:
    """Render a combined divisions panel.

    Args:
        commons: Commons divisions data (list or dict).
        lords: Lords divisions data (list or dict).

    Returns:
        Rich Panel, or None if no data.
    """
    commons_list = commons if isinstance(commons, list) else []
    lords_list = lords if isinstance(lords, list) else []
    if not commons_list and not lords_list:
        return None

    table = Table(show_header=True, header_style="bold", expand=True, row_styles=["", "dim"])
    table.add_column("House", width=8)
    table.add_column("Division", ratio=1)
    table.add_column("Ayes", width=6, justify="right")
    table.add_column("Noes", width=6, justify="right")
    table.add_column("Date", width=10)

    for div in commons_list[:20]:
        if isinstance(div, dict):
            div_id = div.get("DivisionId", div.get("divisionId", ""))
            title = str(div.get("Title", div.get("title", "")))
            title_text = Text(title)
            if div_id:
                title_text.stylize(
                    f"link https://votes.parliament.uk/Votes/Commons/Division/{div_id}"
                )
            ayes = str(div.get("AyeCount", div.get("ayeCount", "")))
            noes = str(div.get("NoCount", div.get("noCount", "")))
            dt = str(div.get("Date", div.get("date", "")))[:10]
            table.add_row(Text("Commons", style="green"), title_text, ayes, noes, dt)

    for div in lords_list[:20]:
        if isinstance(div, dict):
            div_id = div.get("DivisionId", div.get("divisionId", ""))
            title = str(div.get("Title", div.get("title", "")))
            title_text = Text(title)
            if div_id:
                title_text.stylize(
                    f"link https://votes.parliament.uk/Votes/Lords/Division/{div_id}"
                )
            ayes = str(div.get("AuthorityCount", div.get("authorityCount", "")))
            noes = str(div.get("NonAuthorityCount", div.get("nonAuthorityCount", "")))
            dt = str(div.get("Date", div.get("date", "")))[:10]
            table.add_row(Text("Lords", style="red"), title_text, ayes, noes, dt)

    if table.row_count == 0:
        return None
    return Panel(table, title="[bold]Divisions[/bold]", border_style="dim")


def _render_hansard_section(data: Any) -> Panel | None:
    """Render Hansard debate sections as a table with clickable IDs.

    Args:
        data: Parsed Hansard search/debates.json response.

    Returns:
        Rich Panel, or None if no data.
    """
    if not _section_has_data(data):
        return None

    # search/debates.json returns {"Results": [...], "TotalResultCount": N}
    sections: list[Any] = []
    if isinstance(data, list):
        sections = data
    elif isinstance(data, dict):
        for key in ("Results", "results", "Sections", "sections", "items"):
            if key in data and isinstance(data[key], list):
                sections = data[key]
                break

    total = 0
    if isinstance(data, dict):
        total = int(data.get("TotalResultCount") or data.get("totalResultCount") or 0)

    table = Table(show_header=True, header_style="bold", expand=True, row_styles=["", "dim"])
    table.add_column("ID", width=10, style="cyan", no_wrap=True)
    table.add_column("House", width=8)
    table.add_column("Section", width=16, style="dim italic")
    table.add_column("Title", ratio=1)

    for section in sections[:15]:
        if isinstance(section, dict):
            title = section.get("Title", section.get("title", ""))
            if not title:
                continue
            house_name = str(section.get("House", section.get("house", "")))
            debate_section = str(section.get("DebateSection", section.get("debateSection", "")))
            ext_id = section.get(
                "DebateSectionExtId",
                section.get("ExternalId", section.get("externalId", "")),
            )
            # Short display ID (first 8 chars of UUID)
            id_display = str(ext_id)[:8] if ext_id else ""
            id_text = Text(id_display)
            if ext_id:
                sitting_date = str(section.get("SittingDate", section.get("sittingDate", "")))[:10]
                slug = re.sub(r"[^A-Za-z0-9]", "", str(title))
                house_lower = house_name.lower()
                id_text.stylize(
                    f"link https://hansard.parliament.uk/{house_lower}/{sitting_date}/debates/{ext_id}/{slug}"
                )
            house_text = Text(house_name, style=_house_color(house_name))
            table.add_row(id_text, house_text, debate_section, str(title))

    if table.row_count == 0:
        return None
    subtitle = f"[dim]{total} debates total[/dim]" if total > len(sections) else None
    return Panel(table, title="[bold]Hansard Debates[/bold]", subtitle=subtitle, border_style="dim")


def _render_bills_section(data: Any) -> Panel | None:
    """Render bill sittings, enriched with bill details when available.

    Args:
        data: Parsed Bills/Sittings response (may include _bill_details).

    Returns:
        Rich Panel, or None if no data.
    """
    if not _section_has_data(data):
        return None

    items = _safe_list(data, "items", "results")
    if not items:
        return None

    # Get enriched bill details if available
    bill_details: dict[str, dict[str, Any]] = {}
    if isinstance(data, dict):
        bill_details = data.get("_bill_details", {})

    # Deduplicate by billId
    bill_ids: list[str] = []
    seen: set[str] = set()
    for item in items:
        if isinstance(item, dict):
            val = item.get("value", item)
            if not isinstance(val, dict):
                val = item
            bid = str(val.get("billId", item.get("billId", "")))
            if bid and bid not in seen:
                bill_ids.append(bid)
                seen.add(bid)

    if not bill_ids:
        return None

    # If we have enriched details, show a proper table
    if bill_details:
        table = Table(show_header=True, header_style="bold", expand=True, row_styles=["", "dim"])
        table.add_column("Bill", ratio=2)
        table.add_column("Stage", ratio=1)

        for bid in bill_ids[:20]:
            detail = bill_details.get(bid, {})
            title = detail.get("shortTitle", detail.get("longTitle", f"Bill {bid}"))
            bill_text = Text(str(title))
            bill_text.stylize(f"link https://bills.parliament.uk/bills/{bid}")

            stage = ""
            current_stage = detail.get("currentStage")
            if isinstance(current_stage, dict):
                stage_desc = current_stage.get("description", "")
                if stage_desc:
                    stage = str(stage_desc)
                else:
                    stage_name = current_stage.get("stageName", "")
                    if stage_name:
                        stage = str(stage_name)

            table.add_row(bill_text, stage)

        if table.row_count == 0:
            return None
        return Panel(table, title="[bold]Bills[/bold]", border_style="dim")

    # Fallback: no enriched details, show count + IDs
    text = Text()
    text.append(f"  {len(bill_ids)} bill(s) with sittings", style="bold")
    text.append(f"\n  Bill IDs: {', '.join(bill_ids[:20])}", style="dim")
    return Panel(text, title="[bold]Bills[/bold]", border_style="dim")


def _render_committees_section(data: Any) -> Panel | None:
    """Render committee events.

    Args:
        data: Parsed Committees/Events response.

    Returns:
        Rich Panel, or None if no data.
    """
    if not _section_has_data(data):
        return None

    items = _safe_list(data, "items", "results")
    if not items:
        return None

    table = Table(show_header=True, header_style="bold", expand=True, row_styles=["", "dim"])
    table.add_column("Date", width=10)
    table.add_column("Time", width=5, style="cyan")
    table.add_column("Committee", ratio=1)
    table.add_column("Topic", ratio=1)

    for item in items[:10]:
        if isinstance(item, dict):
            date_str = ""
            time_str = ""
            for key in ["startDate", "StartDate", "startTime", "StartTime"]:
                raw = item.get(key, "")
                if raw and isinstance(raw, str) and "T" in raw:
                    date_str = raw.split("T")[0]
                    time_str = raw.split("T")[1][:5]
                    break

            committee_name = ""
            committee_id = ""
            # Single committee object
            comm = item.get("committee", item.get("Committee"))
            if isinstance(comm, dict):
                committee_name = str(comm.get("name", comm.get("Name", "")))
                committee_id = str(comm.get("id", comm.get("Id", "")))
            elif isinstance(comm, str):
                committee_name = comm
            # List of committees (Events API returns "committees" array)
            if not committee_name:
                comms = item.get("committees", [])
                if isinstance(comms, list) and comms:
                    first = comms[0]
                    if isinstance(first, dict):
                        committee_name = str(first.get("name", first.get("Name", "")))
                        if not committee_id:
                            committee_id = str(first.get("id", first.get("Id", "")))
            if not committee_name:
                committee_name = str(item.get("committeeName", item.get("CommitteeName", "")))

            # Make committee name a link if we have an ID
            comm_text = Text(committee_name)
            if committee_id:
                comm_text.stylize(
                    f"link https://committees.parliament.uk/committee/{committee_id}/"
                )

            topic = str(item.get("description", item.get("Description", item.get("title", ""))))
            # Fallback: show event type + location
            if not topic or topic == "None":
                parts: list[str] = []
                evt = item.get("eventType")
                if isinstance(evt, dict):
                    parts.append(evt.get("name", ""))
                loc = item.get("location", "")
                if loc:
                    parts.append(str(loc))
                topic = " — ".join(p for p in parts if p)

            table.add_row(date_str, time_str, comm_text, topic)

    if table.row_count == 0:
        return None
    return Panel(table, title="[bold]Committee Meetings[/bold]", border_style="dim")


def _render_statements_section(data: Any) -> Panel | None:
    """Render written statements.

    Args:
        data: Parsed written statements response.

    Returns:
        Rich Panel, or None if no data.
    """
    if not _section_has_data(data):
        return None

    items = _safe_list(data, "results", "items")
    if not items:
        return None

    table = Table(show_header=True, header_style="bold", expand=True, row_styles=["", "dim"])
    table.add_column("Department", ratio=1)
    table.add_column("Title", ratio=2)

    for item in items[:10]:
        if isinstance(item, dict):
            # Written statements API wraps each item in a "value" object
            val = item.get("value", item)
            if not isinstance(val, dict):
                val = item
            dept = str(val.get("answeringBodyName", val.get("department", "")))
            title = str(val.get("title", val.get("heading", "")))
            title_text = Text(title)
            stmt_id = val.get("id", val.get("Id", ""))
            if stmt_id:
                title_text.stylize(
                    f"link https://questions-statements.parliament.uk/written-statements/detail/{stmt_id}"
                )
            table.add_row(dept, title_text)

    if table.row_count == 0:
        return None
    return Panel(table, title="[bold]Written Statements[/bold]", border_style="dim")


def _render_oral_qs_section(data: Any) -> Panel | None:
    """Render oral question times.

    Args:
        data: Parsed oral question times response.

    Returns:
        Rich Panel, or None if no data.
    """
    if not _section_has_data(data):
        return None

    items = _safe_list(data, "Response", "items", "results")
    if not items:
        return None

    text = Text()
    for item in items[:10]:
        if isinstance(item, dict):
            dept = str(
                item.get(
                    "AnsweringBodyNames",
                    item.get("AnsweringBodyName", item.get("answeringBodyName", "")),
                )
            )
            answer_date = str(
                item.get("AnsweringWhen", item.get("AnswerDate", item.get("answerDate", "")))
            )[:10]
            if dept:
                text.append(f"  {dept}", style="bold")
                if answer_date:
                    text.append(f"  ({answer_date})", style="dim")
                text.append("\n")

    if not text.plain.strip():
        return None
    return Panel(text, title="[bold]Oral Questions[/bold]", border_style="dim")


def _render_edms_section(data: Any) -> Panel | None:
    """Render Early Day Motions.

    Args:
        data: Parsed EDMs response.

    Returns:
        Rich Panel, or None if no data.
    """
    if not _section_has_data(data):
        return None

    items = _safe_list(data, "Response", "items", "results")
    if not items:
        return None

    table = Table(show_header=True, header_style="bold", expand=True, row_styles=["", "dim"])
    table.add_column("EDM #", width=7, style="cyan")
    table.add_column("Title", ratio=1)
    table.add_column("Primary Sponsor", ratio=1)

    for item in items[:10]:
        if isinstance(item, dict):
            edm_id = item.get("Id", item.get("id", ""))
            edm_num = str(item.get("UIN", item.get("uin", edm_id)))
            title = str(item.get("Title", item.get("title", "")))
            title_text = Text(title)
            if edm_id:
                title_text.stylize(f"link https://edm.parliament.uk/early-day-motion/{edm_id}")
            sponsor = str(item.get("PrimarySponsor", item.get("primarySponsor", "")))
            if isinstance(item.get("PrimarySponsor"), dict):
                sponsor = item["PrimarySponsor"].get("Name", item["PrimarySponsor"].get("name", ""))
            elif isinstance(item.get("primarySponsor"), dict):
                sponsor = item["primarySponsor"].get("Name", item["primarySponsor"].get("name", ""))
            table.add_row(edm_num, title_text, sponsor)

    if table.row_count == 0:
        return None
    return Panel(table, title="[bold]Early Day Motions[/bold]", border_style="dim")


def _render_written_qs_section(
    data: Any,
    start_date: str | None = None,
    end_date: str | None = None,
) -> Panel | None:
    """Render written questions grouped by answering body.

    Args:
        data: Parsed written questions response.
        start_date: Start date (YYYY-MM-DD) for Parliament website links.
        end_date: End date (YYYY-MM-DD) for Parliament website links.

    Returns:
        Rich Panel, or None if no data.
    """
    if not _section_has_data(data):
        return None

    items = _safe_list(data, "results", "items")
    if not items:
        return None

    # Group by answering body — items may be wrapped in "value"
    bodies: dict[str, dict[str, Any]] = {}
    total_answered = 0
    for q in items:
        if not isinstance(q, dict):
            continue
        val = q.get("value", q)
        if not isinstance(val, dict):
            val = q
        body_name = str(val.get("answeringBodyName", "Unknown"))
        body_id = val.get("answeringBodyId", "")
        is_answered = bool(val.get("dateAnswered"))
        if is_answered:
            total_answered += 1
        if body_name not in bodies:
            bodies[body_name] = {"id": body_id, "tabled": 0, "answered": 0}
        if is_answered:
            bodies[body_name]["answered"] += 1
        else:
            bodies[body_name]["tabled"] += 1

    if not bodies:
        return None

    # Sort by total count descending
    sorted_bodies = sorted(
        bodies.items(),
        key=lambda x: x[1]["tabled"] + x[1]["answered"],
        reverse=True,
    )

    table = Table(show_header=True, header_style="bold", expand=True, row_styles=["", "dim"])
    table.add_column("Department", ratio=3)
    table.add_column("Tabled", width=7, justify="right")
    table.add_column("Ans'd", width=7, justify="right")
    table.add_column("Total", width=7, justify="right", style="bold")

    for body_name, info in sorted_bodies:
        dept_total = info["tabled"] + info["answered"]
        dept_text = Text(body_name)
        if info["id"] and start_date:
            # Convert YYYY-MM-DD to DD/MM/YYYY for Parliament website
            def _uk_date(iso: str) -> str:
                parts = iso.split("-")
                return f"{parts[2]}%2F{parts[1]}%2F{parts[0]}" if len(parts) == 3 else iso

            d_from = _uk_date(start_date)
            d_to = _uk_date(end_date or start_date)
            link = (
                f"https://questions-statements.parliament.uk/written-questions"
                f"?DateFrom={d_from}&DateTo={d_to}"
                f"&AnsweringBodyId={info['id']}"
                f"&House=Bicameral&Answered=Any&Expanded=true"
            )
            dept_text.stylize(f"link {link}")
        table.add_row(dept_text, str(info["tabled"]), str(info["answered"]), str(dept_total))

    # Use API-reported total if available, else fall back to fetched count
    api_total = len(items)
    if isinstance(data, dict) and isinstance(data.get("totalResults"), int):
        api_total = data["totalResults"]

    subtitle = (
        f"[dim]{api_total} total | {total_answered} answered | {len(bodies)} departments[/dim]"
    )
    return Panel(
        table, title="[bold]Written Questions[/bold]", subtitle=subtitle, border_style="dim"
    )


def render_digest(result_json: str) -> None:
    """Render a full parliamentary digest with rich formatting.

    Args:
        result_json: JSON string from _get_digest_async.
    """
    try:
        data = json.loads(result_json)
    except (json.JSONDecodeError, TypeError):
        Console().print("[red]Failed to parse digest data[/red]")
        return

    if "error" in data:
        Console().print(f"[red]{data['error']}[/red]")
        return

    console = Console()

    # Header
    console.print(_render_digest_header(data))

    # Divisions
    panel = _render_divisions_section(data.get("commons_divisions"), data.get("lords_divisions"))
    if panel:
        console.print(panel)

    # Hansard
    panel = _render_hansard_section(data.get("hansard"))
    if panel:
        console.print(panel)

    # Bills
    panel = _render_bills_section(data.get("bills"))
    if panel:
        console.print(panel)

    # Committees
    panel = _render_committees_section(data.get("committees"))
    if panel:
        console.print(panel)

    # Written statements
    panel = _render_statements_section(data.get("written_statements"))
    if panel:
        console.print(panel)

    # Oral questions
    panel = _render_oral_qs_section(data.get("oral_questions"))
    if panel:
        console.print(panel)

    # EDMs
    panel = _render_edms_section(data.get("edms"))
    if panel:
        console.print(panel)

    # Written questions
    panel = _render_written_qs_section(
        data.get("written_questions"),
        start_date=data.get("start_date"),
        end_date=data.get("end_date"),
    )
    if panel:
        console.print(panel)

    # If nothing rendered beyond the header, note that
    sections = [
        "commons_divisions",
        "lords_divisions",
        "hansard",
        "bills",
        "committees",
        "written_statements",
        "oral_questions",
        "edms",
        "written_questions",
    ]
    has_any = any(_section_has_data(data.get(s)) for s in sections)
    if not has_any:
        console.print("[dim]No parliamentary activity found for this date/period.[/dim]")
