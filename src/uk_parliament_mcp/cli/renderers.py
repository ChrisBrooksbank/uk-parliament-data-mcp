"""Rich rendering functions for CLI commands.

Shared rendering helpers extracted from watch.py, plus domain-specific
renderers for live and composite commands.
"""

from __future__ import annotations

import json
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
        return Panel(content, title=f"[bold]{house_name}[/bold]", subtitle=_parliament_tv_subtitle(house_name), border_style="dim")

    # Check if annunciator is disabled
    if data.get("annunciatorDisabled"):
        content = Text("Annunciator offline", style="dim italic")
        return Panel(content, title=f"[bold]{house_name}[/bold]", subtitle=_parliament_tv_subtitle(house_name), border_style="dim")

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
    return Panel(text, title=f"[bold {color}]{house_name}[/bold {color}]", subtitle=_parliament_tv_subtitle(house_name), border_style=border_style)


# ---------------------------------------------------------------------------
# Calendar table renderer (shared with watch.py)
# ---------------------------------------------------------------------------


def _calendar_subtitle(displayed: int, total: int) -> str | None:
    """Return a subtitle string when calendar rows are truncated.

    Args:
        displayed: Number of rows actually shown.
        total: Total number of events available.

    Returns:
        Rich markup string, or None when not truncated.
    """
    if total <= displayed:
        return None
    hidden = total - displayed
    return f"[dim]showing {displayed} of {total} events ({hidden} more)[/dim]"


def _extract_event_time(event: dict[str, Any]) -> str:
    """Extract an "HH:MM" time string from an event dict.

    Args:
        event: Calendar event dict.

    Returns:
        Time string like "14:30", or "" if no parseable time found.
    """
    for key in ["StartTime", "startTime", "StartDate", "startDate"]:
        if key in event and event[key]:
            raw = str(event[key])
            if "T" in raw:
                return raw.split("T")[1][:5]
            if len(raw) > 5:
                return raw[:5]
            return raw
    return ""


def _render_calendar_table(
    events: list[dict[str, Any]],
    max_rows: int | None = None,
    now: datetime | None = None,
) -> tuple[Table | Text, int]:
    """Render today's business as a Rich table.

    Args:
        events: List of calendar event dicts.
        max_rows: Maximum number of rows to display. None means show all.
        now: Current datetime for time-tracking highlight. None disables
            sorting/highlighting (backward-compatible).

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
        if now is not None and current_idx is not None:
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

        house_text = Text(house_str, style=_house_color(house_str))
        table.add_row(
            time_display, house_text, event_str, type_str, location_str, category_str,
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
                    console.print(Panel(bio_text, title="[bold]Biography[/bold]", border_style="dim"))

    # Registered interests
    interests = data.get("registered_interests", {})
    if isinstance(interests, dict):
        interest_items = interests.get("items", [])
        if interest_items and isinstance(interest_items, list):
            table = Table(show_header=True, header_style="bold", expand=True)
            table.add_column("Category", ratio=1)
            table.add_column("Interest", ratio=2)
            for item in interest_items[:15]:
                if isinstance(item, dict):
                    cat = str(item.get("category", item.get("name", "")))
                    entries = item.get("interests", item.get("entries", []))
                    if isinstance(entries, list) and entries:
                        for entry in entries[:3]:
                            if isinstance(entry, dict):
                                desc = str(entry.get("interest", entry.get("description", "")))
                                table.add_row(cat, desc)
                                cat = ""  # Only show category on first row
                    else:
                        table.add_row(cat, "")
            if table.row_count > 0:
                console.print(Panel(table, title="[bold]Registered Interests[/bold]", border_style="dim"))

    # Recent voting
    voting = data.get("recent_voting", {})
    if isinstance(voting, dict):
        vote_items = voting.get("items", [])
        if vote_items and isinstance(vote_items, list):
            table = Table(show_header=True, header_style="bold", expand=True)
            table.add_column("Division", style="cyan", no_wrap=True)
            table.add_column("Title", ratio=1)
            table.add_column("Date", width=10)
            table.add_column("Vote", width=10)
            for item in vote_items[:15]:
                if isinstance(item, dict):
                    value = item.get("value", item)
                    if isinstance(value, dict):
                        div_id = str(value.get("divisionId", value.get("DivisionId", "")))
                        title = str(value.get("title", value.get("Title", "")))
                        date = str(value.get("date", value.get("Date", "")))[:10]
                        voted_aye = value.get("memberVotedAye", value.get("inAffirmativeLobby"))
                        vote_str = "Aye" if voted_aye else ("No" if voted_aye is False else "")
                        table.add_row(div_id, title, date, vote_str)
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
        table = Table(show_header=True, header_style="bold", expand=True)
        table.add_column("ID", style="cyan", width=8)
        table.add_column("Title", ratio=1)
        table.add_column("Date", width=10)
        table.add_column("Ayes", width=6, justify="right")
        table.add_column("Noes", width=6, justify="right")
        for div in div_items[:20]:
            if isinstance(div, dict):
                div_id = str(div.get("DivisionId", div.get("divisionId", "")))
                title = str(div.get("Title", div.get("title", "")))
                date = str(div.get("Date", div.get("date", "")))[:10]
                ayes = str(div.get("AyeCount", div.get("ayeCount", "")))
                noes = str(div.get("NoCount", div.get("noCount", "")))
                table.add_row(div_id, title, date, ayes, noes)
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
        current_stage = stage_info.get("description", stage_info.get("stageName", ""))
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
        table = Table(show_header=True, header_style="bold", expand=True)
        table.add_column("Stage", ratio=1)
        table.add_column("House", width=8)
        table.add_column("Date", width=10)
        for stage in stage_items:
            if isinstance(stage, dict):
                stage_name = ""
                sittings = stage.get("stageSittings", [])
                s_info = stage.get("stageType") or stage.get("description") or {}
                if isinstance(s_info, dict):
                    stage_name = s_info.get("name", s_info.get("description", ""))
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
        table = Table(show_header=True, header_style="bold", expand=True)
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
                    names = [str(w.get("name", "")) for w in witness_list if isinstance(w, dict) and w.get("name")]
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
        table = Table(show_header=True, header_style="bold", expand=True)
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
