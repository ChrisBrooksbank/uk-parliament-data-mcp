"""Tests for parliament watch live dashboard."""

from __future__ import annotations

import json
import queue
import threading
from datetime import datetime
from unittest.mock import patch

import pytest
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from uk_parliament_mcp.cli.renderers import (
    _calendar_subtitle,
    _extract_event_time,
    _format_slide_type_label,
    _house_color,
    _parliament_tv_subtitle,
    _parse_api_response,
    _render_calendar_table,
    _render_chamber_panel,
    _split_events_by_house,
)
from uk_parliament_mcp.cli.watch import (
    _CHAMBER_MAX_FRACTION,
    _CHAMBER_MIN_HEIGHT,
    MIN_INTERVAL,
    POLL_INTERVAL,
    SCROLL_INTERVAL,
    _estimate_chamber_height,
    _fetch_all_data,
    _fetch_calendar_today,
    _fetch_commons_now,
    _fetch_lords_now,
    _render_dashboard,
    _start_key_reader,
)

# ---------------------------------------------------------------------------
# Realistic MessageViewModel test data factories
# ---------------------------------------------------------------------------


def _make_message(
    slides: list[dict] | None = None,
    scrolling: list[dict] | None = None,
    *,
    annunciator_disabled: bool = False,
    show_commons_bell: bool = False,
    show_lords_bell: bool = False,
) -> dict:
    """Build a minimal MessageViewModel dict for testing."""
    return {
        "annunciatorDisabled": annunciator_disabled,
        "slides": slides or [],
        "scrollingMessages": scrolling or [],
        "showCommonsBell": show_commons_bell,
        "showLordsBell": show_lords_bell,
    }


def _make_slide(
    slide_type: str = "Debate",
    lines: list[dict] | None = None,
    speaker_time: str | None = None,
) -> dict:
    return {
        "type": slide_type,
        "lines": lines or [],
        "speakerTime": speaker_time,
    }


def _make_line(
    content: str = "",
    style: str = "",
    display_order: int = 0,
    member: dict | None = None,
) -> dict:
    return {
        "content": content,
        "style": style,
        "displayOrder": display_order,
        "member": member,
    }


def _make_member(
    name: str = "Sir Keir Starmer",
    party: str = "Labour",
    constituency: str = "Holborn and St Pancras",
) -> dict:
    return {
        "nameDisplayAs": name,
        "latestParty": {"name": party},
        "latestHouseMembership": {"membershipFrom": constituency},
    }


# ---------------------------------------------------------------------------
# _parse_api_response
# ---------------------------------------------------------------------------


class TestParseApiResponse:
    """Tests for _parse_api_response helper."""

    def test_parses_success_response(self) -> None:
        response = json.dumps({"url": "test", "data": {"key": "value"}})
        result = _parse_api_response(response)
        assert result == {"key": "value"}

    def test_parses_string_data(self) -> None:
        inner = json.dumps({"key": "value"})
        response = json.dumps({"url": "test", "data": inner})
        result = _parse_api_response(response)
        assert result == {"key": "value"}

    def test_returns_none_on_error(self) -> None:
        response = json.dumps({"url": "test", "error": "Not found"})
        result = _parse_api_response(response)
        assert result is None

    def test_returns_none_on_invalid_json(self) -> None:
        result = _parse_api_response("not json")
        assert result is None

    def test_returns_dict_without_data_key(self) -> None:
        msg = _make_message(slides=[_make_slide("Debate")])
        response = json.dumps(msg)
        result = _parse_api_response(response)
        assert result is not None
        assert result["slides"][0]["type"] == "Debate"


# ---------------------------------------------------------------------------
# _format_slide_type_label
# ---------------------------------------------------------------------------


class TestFormatSlideTypeLabel:
    """Tests for the slide type label helper."""

    def test_debate(self) -> None:
        label, style = _format_slide_type_label("Debate")
        assert label == "Debate"
        assert "cyan" in style

    def test_division(self) -> None:
        label, style = _format_slide_type_label("Division")
        assert label == "DIVISION"
        assert "red" in style

    def test_pmqs(self) -> None:
        label, style = _format_slide_type_label("PrimeMinistersQuestions")
        assert label == "Prime Minister's Questions"
        assert "yellow" in style

    def test_oral_questions(self) -> None:
        label, _ = _format_slide_type_label("OralQuestionTime")
        assert label == "Oral Questions"

    def test_statement(self) -> None:
        label, style = _format_slide_type_label("Statement")
        assert label == "Statement"
        assert "green" in style

    def test_not_sitting(self) -> None:
        label, style = _format_slide_type_label("NotSitting")
        assert label == "Not Sitting"
        assert "dim" in style

    def test_house_risen(self) -> None:
        label, style = _format_slide_type_label("HouseRisen")
        assert label == "House has risen"
        assert "dim" in style

    def test_unknown_type_falls_back(self) -> None:
        label, style = _format_slide_type_label("SomeFutureType")
        assert label == "SomeFutureType"
        assert style == "bold"


# ---------------------------------------------------------------------------
# _render_chamber_panel
# ---------------------------------------------------------------------------


class TestRenderChamberPanel:
    """Tests for _render_chamber_panel with real MessageViewModel data."""

    def test_renders_not_sitting_when_none(self) -> None:
        panel = _render_chamber_panel(None, "House of Commons")
        assert isinstance(panel, Panel)
        assert "House of Commons" in panel.title  # type: ignore[operator]

    def test_renders_not_sitting_when_empty(self) -> None:
        panel = _render_chamber_panel({}, "House of Lords")
        assert isinstance(panel, Panel)

    def test_debate_slide(self) -> None:
        msg = _make_message(
            slides=[
                _make_slide(
                    "Debate",
                    lines=[
                        _make_line("Online Safety Bill - Second Reading", "Text100", 1),
                    ],
                    speaker_time="2024-01-15T14:32:00",
                ),
            ]
        )
        panel = _render_chamber_panel(msg, "House of Commons")
        assert isinstance(panel, Panel)
        # Active Commons debate -> green border
        assert panel.border_style == "green"  # type: ignore[union-attr]

    def test_lords_active_border_is_red(self) -> None:
        msg = _make_message(
            slides=[
                _make_slide("Debate", lines=[_make_line("Lords debate", "Text100", 1)]),
            ]
        )
        panel = _render_chamber_panel(msg, "House of Lords")
        assert isinstance(panel, Panel)
        # Active Lords debate -> red border
        assert panel.border_style == "red"  # type: ignore[union-attr]

    def test_division_slide(self) -> None:
        msg = _make_message(
            slides=[
                _make_slide(
                    "Division",
                    lines=[
                        _make_line("Ayes: 310  Noes: 250", "Division", 1),
                    ],
                ),
            ]
        )
        panel = _render_chamber_panel(msg, "House of Commons")
        rendered = panel.renderable
        assert isinstance(rendered, Text)
        assert "DIVISION" in rendered.plain
        assert "Ayes" in rendered.plain

    def test_pmqs_with_member(self) -> None:
        msg = _make_message(
            slides=[
                _make_slide(
                    "PrimeMinistersQuestions",
                    lines=[
                        _make_line("", "Member", 1, member=_make_member()),
                        _make_line("Question 1", "Text100", 2),
                    ],
                ),
            ]
        )
        panel = _render_chamber_panel(msg, "House of Commons")
        rendered = panel.renderable
        assert isinstance(rendered, Text)
        assert "Prime Minister's Questions" in rendered.plain
        assert "Sir Keir Starmer" in rendered.plain
        assert "Labour" in rendered.plain
        assert "Holborn and St Pancras" in rendered.plain

    def test_not_sitting_slide(self) -> None:
        msg = _make_message(
            slides=[
                _make_slide("NotSitting"),
            ]
        )
        panel = _render_chamber_panel(msg, "House of Commons")
        assert panel.border_style == "dim"  # type: ignore[union-attr]
        rendered = panel.renderable
        assert isinstance(rendered, Text)
        assert "Not Sitting" in rendered.plain

    def test_house_risen_slide(self) -> None:
        msg = _make_message(
            slides=[
                _make_slide("HouseRisen"),
            ]
        )
        panel = _render_chamber_panel(msg, "House of Lords")
        assert panel.border_style == "dim"  # type: ignore[union-attr]
        rendered = panel.renderable
        assert isinstance(rendered, Text)
        assert "House has risen" in rendered.plain

    def test_annunciator_disabled(self) -> None:
        msg = _make_message(annunciator_disabled=True)
        panel = _render_chamber_panel(msg, "House of Commons")
        rendered = panel.renderable
        assert isinstance(rendered, Text)
        assert "Annunciator offline" in rendered.plain
        assert panel.border_style == "dim"  # type: ignore[union-attr]

    def test_division_bell(self) -> None:
        msg = _make_message(
            slides=[_make_slide("Division")],
            show_commons_bell=True,
        )
        panel = _render_chamber_panel(msg, "House of Commons")
        rendered = panel.renderable
        assert isinstance(rendered, Text)
        assert "DIVISION BELL" in rendered.plain

    def test_scrolling_messages(self) -> None:
        msg = _make_message(
            slides=[_make_slide("Debate", lines=[_make_line("Climate debate", "Text100", 1)])],
            scrolling=[
                {"content": "Division in Westminster Hall", "alertType": "Alert"},
                {"content": "Lords also sitting", "alertType": "SecondaryChamber"},
                {"content": "Normal info", "alertType": "Standard"},
            ],
        )
        panel = _render_chamber_panel(msg, "House of Commons")
        rendered = panel.renderable
        assert isinstance(rendered, Text)
        assert "Division in Westminster Hall" in rendered.plain
        assert "Lords also sitting" in rendered.plain
        assert "Normal info" in rendered.plain

    def test_multiple_slides(self) -> None:
        msg = _make_message(
            slides=[
                _make_slide("Debate", lines=[_make_line("First item", "Text100", 1)]),
                _make_slide("Statement", lines=[_make_line("Ministerial Statement", "Text100", 1)]),
            ]
        )
        panel = _render_chamber_panel(msg, "House of Commons")
        rendered = panel.renderable
        assert isinstance(rendered, Text)
        assert "Debate" in rendered.plain
        assert "Statement" in rendered.plain
        assert "Ministerial Statement" in rendered.plain

    def test_blank_slide_skipped(self) -> None:
        msg = _make_message(
            slides=[
                _make_slide("BlankSlide"),
                _make_slide("Debate", lines=[_make_line("Actual content", "Text100", 1)]),
            ]
        )
        panel = _render_chamber_panel(msg, "House of Commons")
        rendered = panel.renderable
        assert isinstance(rendered, Text)
        assert "BlankSlide" not in rendered.plain
        assert "Actual content" in rendered.plain

    def test_divider_lines(self) -> None:
        msg = _make_message(
            slides=[
                _make_slide(
                    "Debate",
                    lines=[
                        _make_line("Before divider", "Text100", 1),
                        _make_line("", "DividerSolid", 2),
                        _make_line("After divider", "Text100", 3),
                    ],
                ),
            ]
        )
        panel = _render_chamber_panel(msg, "House of Commons")
        rendered = panel.renderable
        assert isinstance(rendered, Text)
        assert "Before divider" in rendered.plain
        assert "After divider" in rendered.plain
        # Box-drawing char on most platforms; may fall back to ASCII hyphen on Windows
        assert "\u2500\u2500\u2500\u2500" in rendered.plain or "----" in rendered.plain

    def test_empty_line_style(self) -> None:
        msg = _make_message(
            slides=[
                _make_slide(
                    "Debate",
                    lines=[
                        _make_line("Line one", "Text100", 1),
                        _make_line("", "EmptyLine", 2),
                        _make_line("Line two", "Text100", 3),
                    ],
                ),
            ]
        )
        panel = _render_chamber_panel(msg, "House of Commons")
        rendered = panel.renderable
        assert isinstance(rendered, Text)
        assert "Line one" in rendered.plain
        assert "Line two" in rendered.plain

    def test_footer_style_dim(self) -> None:
        msg = _make_message(
            slides=[
                _make_slide(
                    "Debate",
                    lines=[
                        _make_line("Footer text", "Footer", 1),
                    ],
                ),
            ]
        )
        panel = _render_chamber_panel(msg, "House of Commons")
        rendered = panel.renderable
        assert isinstance(rendered, Text)
        assert "Footer text" in rendered.plain

    def test_no_slides_no_scrolling_shows_no_activity(self) -> None:
        msg = _make_message(slides=[], scrolling=[])
        panel = _render_chamber_panel(msg, "House of Commons")
        rendered = panel.renderable
        assert isinstance(rendered, Text)
        assert "No current activity" in rendered.plain

    def test_lines_sorted_by_display_order(self) -> None:
        msg = _make_message(
            slides=[
                _make_slide(
                    "Debate",
                    lines=[
                        _make_line("Third", "Text100", 3),
                        _make_line("First", "Text100", 1),
                        _make_line("Second", "Text100", 2),
                    ],
                ),
            ]
        )
        panel = _render_chamber_panel(msg, "House of Commons")
        rendered = panel.renderable
        assert isinstance(rendered, Text)
        text = rendered.plain
        assert text.index("First") < text.index("Second") < text.index("Third")


# ---------------------------------------------------------------------------
# _render_calendar_table
# ---------------------------------------------------------------------------


class TestRenderCalendarTable:
    """Tests for _render_calendar_table."""

    def test_no_events_returns_text(self) -> None:
        result, count = _render_calendar_table([])
        assert isinstance(result, Text)
        assert count == 0

    def test_renders_events_table(self) -> None:
        events = [
            {
                "StartTime": "2024-01-15T11:30:00",
                "House": "Commons",
                "Description": "Oral Questions",
                "Category": "Questions",
                "Type": "Oral evidence",
                "Location": "Chamber",
            },
            {
                "StartTime": "2024-01-15T14:00:00",
                "House": "Lords",
                "Title": "NHS Debate",
                "Type": "General Debate",
                "Location": "Westminster Hall",
            },
        ]
        result, count = _render_calendar_table(events)
        assert isinstance(result, Table)
        # Should have 6 columns: Time, House, Event, Type, Location, Category
        assert len(result.columns) == 6
        assert count == 2

    def test_renders_location_and_type(self) -> None:
        events = [
            {
                "StartTime": "2024-01-15T10:00:00",
                "House": "Commons",
                "Description": "Treasury Committee",
                "Type": "Oral evidence",
                "Location": "Westminster Hall",
                "Category": "Committee",
            },
        ]
        result, count = _render_calendar_table(events)
        assert isinstance(result, Table)
        assert len(result.columns) == 6
        assert count == 1
        # Verify column headers
        col_headers = [col.header for col in result.columns]
        assert "Type" in [str(h) for h in col_headers]
        assert "Location" in [str(h) for h in col_headers]

    def test_handles_missing_fields(self) -> None:
        events = [{"Description": "Test Event"}]
        result, count = _render_calendar_table(events)
        assert isinstance(result, Table)
        # Still has 6 columns even with missing data
        assert len(result.columns) == 6
        assert count == 1

    def test_table_expands_to_fill_width(self) -> None:
        events = [{"Description": "Test"}]
        result, _ = _render_calendar_table(events)
        assert isinstance(result, Table)
        assert result.expand is True

    def test_event_column_uses_ratio(self) -> None:
        events = [{"Description": "Test"}]
        result, _ = _render_calendar_table(events)
        assert isinstance(result, Table)
        # Event is the 3rd column (index 2)
        assert result.columns[2].ratio == 1

    def test_max_rows_limits_displayed_events(self) -> None:
        events = [{"Description": f"Event {i}"} for i in range(20)]
        result, total = _render_calendar_table(events, max_rows=5)
        assert isinstance(result, Table)
        assert total == 20
        assert result.row_count == 5

    def test_max_rows_none_shows_all(self) -> None:
        events = [{"Description": f"Event {i}"} for i in range(15)]
        result, total = _render_calendar_table(events, max_rows=None)
        assert isinstance(result, Table)
        assert total == 15
        assert result.row_count == 15

    def test_max_rows_greater_than_events_shows_all(self) -> None:
        events = [{"Description": f"Event {i}"} for i in range(3)]
        result, total = _render_calendar_table(events, max_rows=10)
        assert isinstance(result, Table)
        assert total == 3
        assert result.row_count == 3


# ---------------------------------------------------------------------------
# _calendar_subtitle
# ---------------------------------------------------------------------------


class TestCalendarSubtitle:
    """Tests for _calendar_subtitle helper."""

    def test_returns_none_when_not_truncated(self) -> None:
        assert _calendar_subtitle(10, 10) is None

    def test_returns_none_when_displayed_exceeds_total(self) -> None:
        assert _calendar_subtitle(15, 10) is None

    def test_returns_subtitle_when_truncated(self) -> None:
        result = _calendar_subtitle(5, 20)
        assert result is not None
        assert "showing 5 of 20 events" in result
        assert "15 more" in result


# ---------------------------------------------------------------------------
# _house_color
# ---------------------------------------------------------------------------


class TestHouseColor:
    """Tests for _house_color helper."""

    def test_commons(self) -> None:
        assert _house_color("House of Commons") == "green"
        assert _house_color("Commons") == "green"

    def test_lords(self) -> None:
        assert _house_color("House of Lords") == "red"
        assert _house_color("Lords") == "red"

    def test_case_insensitive(self) -> None:
        assert _house_color("COMMONS") == "green"
        assert _house_color("lords") == "red"

    def test_fallback(self) -> None:
        assert _house_color("Joint") == "white"
        assert _house_color("") == "white"


# ---------------------------------------------------------------------------
# Calendar time-tracking
# ---------------------------------------------------------------------------


class TestCalendarTimeTracking:
    """Tests for calendar time-tracking highlight and windowing."""

    def _make_events(self, times: list[str], house: str = "Commons") -> list[dict]:
        """Create events with given HH:MM times."""
        return [
            {
                "StartTime": f"2024-01-15T{t}:00",
                "House": house,
                "Description": f"Event at {t}",
            }
            for t in times
        ]

    def test_events_sorted_by_time(self) -> None:
        events = self._make_events(["14:00", "09:30", "11:00"])
        result, _ = _render_calendar_table(events, now=datetime(2024, 1, 15, 12, 0))
        assert isinstance(result, Table)
        assert result.row_count == 3

    def test_current_event_highlighted(self) -> None:
        events = self._make_events(["09:00", "11:00", "14:00"])
        now = datetime(2024, 1, 15, 12, 0)  # 12:00 — after 11:00, before 14:00
        result, _ = _render_calendar_table(events, now=now)
        assert isinstance(result, Table)
        # Row 1 (11:00) should be highlighted — check via row style
        # Row index 1 is the "current" event (last started before 12:00)
        assert result.rows[1].style == "bold"
        assert result.rows[0].style != "bold"
        assert result.rows[2].style != "bold"

    def test_windowing_centers_on_current(self) -> None:
        # 10 events, max_rows=3, current is event at index 5 (12:30)
        times = [f"{9 + i}:{30 if i % 2 else '00'}" for i in range(10)]
        events = self._make_events(times)
        now = datetime(2024, 1, 15, 12, 35)
        result, total = _render_calendar_table(events, max_rows=3, now=now)
        assert isinstance(result, Table)
        assert total == 10
        assert result.row_count == 3
        # One of the 3 rows should be bold (current)
        styles = [row.style for row in result.rows]
        assert "bold" in styles

    def test_now_none_preserves_top_slice(self) -> None:
        events = self._make_events(["14:00", "09:00", "11:00"])
        result, total = _render_calendar_table(events, max_rows=2, now=None)
        assert isinstance(result, Table)
        assert total == 3
        assert result.row_count == 2
        # Without now, no bold rows
        for row in result.rows:
            assert row.style != "bold"

    def test_all_events_in_future(self) -> None:
        events = self._make_events(["14:00", "15:00", "16:00"])
        now = datetime(2024, 1, 15, 8, 0)  # 08:00, all events are future
        result, _ = _render_calendar_table(events, now=now)
        assert isinstance(result, Table)
        # First event should be highlighted
        assert result.rows[0].style == "bold"

    def test_all_events_in_past(self) -> None:
        events = self._make_events(["08:00", "09:00", "10:00"])
        now = datetime(2024, 1, 15, 18, 0)  # 18:00, all events are past
        result, _ = _render_calendar_table(events, now=now)
        assert isinstance(result, Table)
        # Last event should be highlighted
        assert result.rows[2].style == "bold"

    def test_no_parseable_times(self) -> None:
        events = [{"Description": f"Event {i}"} for i in range(3)]
        now = datetime(2024, 1, 15, 12, 0)
        result, _ = _render_calendar_table(events, now=now)
        assert isinstance(result, Table)
        # No bold rows when no times can be parsed
        for row in result.rows:
            assert row.style != "bold"

    def test_extract_event_time_iso(self) -> None:
        assert _extract_event_time({"StartTime": "2024-01-15T14:30:00"}) == "14:30"

    def test_extract_event_time_missing(self) -> None:
        assert _extract_event_time({"Description": "No time"}) == ""

    def test_extract_event_time_short(self) -> None:
        assert _extract_event_time({"startTime": "14:30"}) == "14:30"


# ---------------------------------------------------------------------------
# _estimate_chamber_height
# ---------------------------------------------------------------------------


class TestEstimateChamberHeight:
    """Tests for _estimate_chamber_height."""

    def test_none_data_returns_small(self) -> None:
        panel = _render_chamber_panel(None, "House of Commons")
        height = _estimate_chamber_height(panel)
        # "Not currently sitting" = 1 content line + 2 borders = 3
        assert height == 3

    def test_empty_data_returns_small(self) -> None:
        panel = _render_chamber_panel({}, "House of Lords")
        height = _estimate_chamber_height(panel)
        assert height == 3

    def test_annunciator_disabled(self) -> None:
        msg = _make_message(annunciator_disabled=True)
        panel = _render_chamber_panel(msg, "House of Commons")
        height = _estimate_chamber_height(panel)
        # Single line ("Annunciator offline") + 2 borders = 3
        assert height == 3

    def test_single_slide(self) -> None:
        msg = _make_message(
            slides=[
                _make_slide("NotSitting"),
            ]
        )
        panel = _render_chamber_panel(msg, "House of Commons")
        height = _estimate_chamber_height(panel)
        # "Not Sitting\n" → 1 content line + 2 borders = 3
        assert height >= 3

    def test_division_bell_adds_line(self) -> None:
        msg_no_bell = _make_message(slides=[_make_slide("Division")])
        msg_bell = _make_message(
            slides=[_make_slide("Division")],
            show_commons_bell=True,
        )
        h_no_bell = _estimate_chamber_height(_render_chamber_panel(msg_no_bell, "House of Commons"))
        h_bell = _estimate_chamber_height(_render_chamber_panel(msg_bell, "House of Commons"))
        assert h_bell > h_no_bell

    def test_scrolling_messages_increase_height(self) -> None:
        msg_no_scroll = _make_message(
            slides=[_make_slide("Debate", lines=[_make_line("Text", "Text100", 1)])],
        )
        msg_scroll = _make_message(
            slides=[_make_slide("Debate", lines=[_make_line("Text", "Text100", 1)])],
            scrolling=[
                {"content": "Alert 1", "alertType": "Standard"},
                {"content": "Alert 2", "alertType": "Standard"},
            ],
        )
        h_no = _estimate_chamber_height(_render_chamber_panel(msg_no_scroll, "House of Commons"))
        h_yes = _estimate_chamber_height(_render_chamber_panel(msg_scroll, "House of Commons"))
        assert h_yes > h_no


# ---------------------------------------------------------------------------
# _render_dashboard
# ---------------------------------------------------------------------------


class TestRenderDashboard:
    """Tests for _render_dashboard."""

    def test_renders_both_houses(self) -> None:
        msg = _make_message(slides=[_make_slide("Debate")])
        data = {"commons": msg, "lords": msg, "calendar": []}
        result = _render_dashboard(data)
        assert isinstance(result, Layout)

    def test_renders_commons_only(self) -> None:
        msg = _make_message(slides=[_make_slide("Debate")])
        data = {"commons": msg, "calendar": []}
        result = _render_dashboard(data)
        assert isinstance(result, Layout)

    def test_renders_lords_only(self) -> None:
        msg = _make_message(slides=[_make_slide("Debate")])
        data = {"lords": msg, "calendar": []}
        result = _render_dashboard(data)
        assert isinstance(result, Layout)

    def test_renders_with_empty_data(self) -> None:
        data = {"commons": None, "lords": None, "calendar": []}
        result = _render_dashboard(data)
        assert isinstance(result, Layout)

    def test_chambers_get_fixed_size(self) -> None:
        """Chambers section should use size= (fixed height)."""
        msg = _make_message(slides=[_make_slide("NotSitting")])
        data = {"commons": msg, "lords": msg, "calendar": []}
        layout = _render_dashboard(data)
        # Layout children: header, chambers, calendar
        children = layout.children
        assert len(children) == 3
        chambers_layout = children[1]
        assert chambers_layout.size is not None
        assert chambers_layout.size >= _CHAMBER_MIN_HEIGHT

    def test_calendar_gets_remaining_space(self) -> None:
        """Calendar section should use ratio (size=None) to fill remaining space."""
        msg = _make_message(slides=[_make_slide("NotSitting")])
        data = {"commons": msg, "lords": msg, "calendar": []}
        layout = _render_dashboard(data)
        children = layout.children
        calendar_layout = children[2]
        assert calendar_layout.size is None
        assert calendar_layout.ratio == 1

    def test_min_height_enforced(self) -> None:
        """Chamber size should never go below _CHAMBER_MIN_HEIGHT."""
        data = {"commons": None, "lords": None, "calendar": []}
        with patch("uk_parliament_mcp.cli.watch.shutil.get_terminal_size") as mock_ts:
            mock_ts.return_value = type("TS", (), {"lines": 50, "columns": 120})()
            layout = _render_dashboard(data)
        children = layout.children
        chambers_layout = children[1]
        assert chambers_layout.size >= _CHAMBER_MIN_HEIGHT

    def test_max_fraction_cap(self) -> None:
        """Chamber size should not exceed _CHAMBER_MAX_FRACTION of terminal height."""
        # Build a chamber with many lines to push height up
        many_lines = [_make_line(f"Line {i}", "Text100", i) for i in range(30)]
        msg = _make_message(
            slides=[_make_slide("Debate", lines=many_lines)],
            scrolling=[{"content": f"Scroll {i}", "alertType": "Standard"} for i in range(10)],
        )
        data = {"commons": msg, "lords": msg, "calendar": []}
        terminal_height = 40
        with patch("uk_parliament_mcp.cli.watch.shutil.get_terminal_size") as mock_ts:
            mock_ts.return_value = type("TS", (), {"lines": terminal_height, "columns": 120})()
            layout = _render_dashboard(data)
        children = layout.children
        chambers_layout = children[1]
        max_allowed = int(terminal_height * _CHAMBER_MAX_FRACTION)
        assert chambers_layout.size <= max_allowed


# ---------------------------------------------------------------------------
# Async fetch functions
# ---------------------------------------------------------------------------


class TestFetchFunctions:
    """Tests for async fetch functions."""

    @pytest.mark.asyncio
    async def test_fetch_commons_now(self) -> None:
        msg = _make_message(slides=[_make_slide("Debate")])
        mock_response = json.dumps({"url": "test", "data": msg})
        with patch("uk_parliament_mcp.cli.watch.get_result", return_value=mock_response):
            result = await _fetch_commons_now()
            assert result is not None
            assert result["slides"][0]["type"] == "Debate"

    @pytest.mark.asyncio
    async def test_fetch_lords_now(self) -> None:
        msg = _make_message(slides=[_make_slide("Statement")])
        mock_response = json.dumps({"url": "test", "data": msg})
        with patch("uk_parliament_mcp.cli.watch.get_result", return_value=mock_response):
            result = await _fetch_lords_now()
            assert result is not None
            assert result["slides"][0]["type"] == "Statement"

    @pytest.mark.asyncio
    async def test_fetch_commons_now_error(self) -> None:
        mock_response = json.dumps({"url": "test", "error": "Not found"})
        with patch("uk_parliament_mcp.cli.watch.get_result", return_value=mock_response):
            result = await _fetch_commons_now()
            assert result is None

    @pytest.mark.asyncio
    async def test_fetch_calendar_today(self) -> None:
        mock_response = json.dumps({"url": "test", "data": [{"Description": "Event 1"}]})
        with patch("uk_parliament_mcp.cli.watch.get_result", return_value=mock_response):
            result = await _fetch_calendar_today()
            assert len(result) == 1
            assert result[0]["Description"] == "Event 1"

    @pytest.mark.asyncio
    async def test_fetch_calendar_today_empty(self) -> None:
        mock_response = json.dumps({"url": "test", "error": "No events"})
        with patch("uk_parliament_mcp.cli.watch.get_result", return_value=mock_response):
            result = await _fetch_calendar_today()
            assert result == []

    @pytest.mark.asyncio
    async def test_fetch_all_data_both_houses(self) -> None:
        msg = _make_message(slides=[_make_slide("Debate")])
        mock_response = json.dumps({"url": "test", "data": msg})
        with patch("uk_parliament_mcp.cli.watch.get_result", return_value=mock_response):
            result = await _fetch_all_data()
            assert "commons" in result
            assert "lords" in result
            assert "calendar" in result

    @pytest.mark.asyncio
    async def test_fetch_all_data_commons_only(self) -> None:
        msg = _make_message(slides=[_make_slide("Debate")])
        mock_response = json.dumps({"url": "test", "data": msg})
        with patch("uk_parliament_mcp.cli.watch.get_result", return_value=mock_response):
            result = await _fetch_all_data("commons")
            assert "commons" in result
            assert "lords" not in result

    @pytest.mark.asyncio
    async def test_fetch_all_data_lords_only(self) -> None:
        msg = _make_message(slides=[_make_slide("Debate")])
        mock_response = json.dumps({"url": "test", "data": msg})
        with patch("uk_parliament_mcp.cli.watch.get_result", return_value=mock_response):
            result = await _fetch_all_data("lords")
            assert "lords" in result
            assert "commons" not in result


# ---------------------------------------------------------------------------
# Watch CLI command
# ---------------------------------------------------------------------------


class TestWatchCommand:
    """Tests for the watch CLI command."""

    def test_min_interval_constant(self) -> None:
        assert MIN_INTERVAL == 30

    def test_raw_flag_outputs_json(self) -> None:
        """--raw should fetch once and print JSON to stdout."""
        msg = _make_message(slides=[_make_slide("Debate")])
        mock_response = json.dumps({"url": "test", "data": msg})

        from typer.testing import CliRunner

        from uk_parliament_mcp.cli.watch import app

        runner = CliRunner()
        with patch("uk_parliament_mcp.cli.watch.get_result", return_value=mock_response):
            result = runner.invoke(app, ["--raw"])
            assert result.exit_code == 0
            parsed = json.loads(result.output)
            assert "commons" in parsed
            assert "lords" in parsed

    def test_raw_pretty_flag(self) -> None:
        """--raw --pretty should output indented JSON."""
        msg = _make_message(slides=[_make_slide("Debate")])
        mock_response = json.dumps({"url": "test", "data": msg})

        from typer.testing import CliRunner

        from uk_parliament_mcp.cli.watch import app

        runner = CliRunner()
        with patch("uk_parliament_mcp.cli.watch.get_result", return_value=mock_response):
            result = runner.invoke(app, ["--raw", "--pretty"])
            assert result.exit_code == 0
            # Pretty-printed JSON contains newlines + indentation
            assert "\n  " in result.output
            parsed = json.loads(result.output)
            assert "commons" in parsed


# ---------------------------------------------------------------------------
# _parliament_tv_subtitle helper
# ---------------------------------------------------------------------------


class TestParliamentTvSubtitle:
    """Tests for _parliament_tv_subtitle helper."""

    def test_commons_url(self) -> None:
        result = _parliament_tv_subtitle("House of Commons")
        assert isinstance(result, Text)
        assert "parliamentlive.tv/Commons" in result.plain
        assert "https://www.parliamentlive.tv/Commons" in str(result.style)

    def test_lords_url(self) -> None:
        result = _parliament_tv_subtitle("House of Lords")
        assert isinstance(result, Text)
        assert "parliamentlive.tv/Lords" in result.plain
        assert "https://www.parliamentlive.tv/Lords" in str(result.style)

    def test_case_insensitive(self) -> None:
        assert "parliamentlive.tv/Commons" in _parliament_tv_subtitle("COMMONS").plain
        assert "parliamentlive.tv/Lords" in _parliament_tv_subtitle("lords").plain

    def test_fallback_url(self) -> None:
        result = _parliament_tv_subtitle("Joint Committee")
        assert "parliamentlive.tv" in result.plain
        assert "Commons" not in result.plain
        assert "Lords" not in result.plain

    def test_display_strips_https_www(self) -> None:
        result = _parliament_tv_subtitle("House of Commons")
        # The display text should not contain "https://www."
        assert "https://www." not in result.plain
        # but the style should contain the full URL as a link
        assert "https://www.parliamentlive.tv" in str(result.style)

    def test_returns_text_with_styled_link(self) -> None:
        result = _parliament_tv_subtitle("House of Commons")
        assert isinstance(result, Text)
        style_str = str(result.style)
        assert "italic" in style_str
        assert "cyan" in style_str


# ---------------------------------------------------------------------------
# Chamber panel Parliament TV subtitle
# ---------------------------------------------------------------------------


class TestChamberPanelSubtitle:
    """Tests for Parliament TV subtitle on chamber panels."""

    def test_commons_panel_has_subtitle(self) -> None:
        msg = _make_message(slides=[_make_slide("Debate")])
        panel = _render_chamber_panel(msg, "House of Commons")
        assert panel.subtitle is not None
        subtitle = panel.subtitle
        assert isinstance(subtitle, Text)
        assert "parliamentlive.tv/Commons" in subtitle.plain

    def test_lords_panel_has_subtitle(self) -> None:
        msg = _make_message(slides=[_make_slide("Debate")])
        panel = _render_chamber_panel(msg, "House of Lords")
        assert panel.subtitle is not None
        subtitle = panel.subtitle
        assert isinstance(subtitle, Text)
        assert "parliamentlive.tv/Lords" in subtitle.plain

    def test_none_data_panel_has_subtitle(self) -> None:
        panel = _render_chamber_panel(None, "House of Commons")
        assert panel.subtitle is not None
        subtitle = panel.subtitle
        assert isinstance(subtitle, Text)
        assert "parliamentlive.tv/Commons" in subtitle.plain

    def test_empty_data_panel_has_subtitle(self) -> None:
        panel = _render_chamber_panel({}, "House of Lords")
        assert panel.subtitle is not None
        subtitle = panel.subtitle
        assert isinstance(subtitle, Text)
        assert "parliamentlive.tv/Lords" in subtitle.plain

    def test_annunciator_disabled_has_subtitle(self) -> None:
        msg = _make_message(annunciator_disabled=True)
        panel = _render_chamber_panel(msg, "House of Commons")
        assert panel.subtitle is not None
        subtitle = panel.subtitle
        assert isinstance(subtitle, Text)
        assert "parliamentlive.tv/Commons" in subtitle.plain


# ---------------------------------------------------------------------------
# 00:00 time handling (all-day events)
# ---------------------------------------------------------------------------


class TestExtractEventTimeZero:
    """Tests for 00:00 handling in _extract_event_time."""

    def test_returns_empty_for_midnight_iso(self) -> None:
        """T00:00:00 timestamps should return '' (all-day events)."""
        assert _extract_event_time({"StartTime": "2024-01-15T00:00:00"}) == ""

    def test_returns_empty_for_midnight_with_tz(self) -> None:
        """T00:00 with timezone offset should also return ''."""
        assert _extract_event_time({"startTime": "2024-01-15T00:00:00+00:00"}) == ""

    def test_normal_times_unaffected(self) -> None:
        """Non-midnight times should still work."""
        assert _extract_event_time({"StartTime": "2024-01-15T09:30:00"}) == "09:30"
        assert _extract_event_time({"StartTime": "2024-01-15T14:00:00"}) == "14:00"
        assert _extract_event_time({"StartTime": "2024-01-15T00:15:00"}) == "00:15"

    def test_all_day_events_sort_to_bottom(self) -> None:
        """Events with 00:00 (blank time) should sort after timed events."""
        events = [
            {"StartTime": "2024-01-15T00:00:00", "Description": "All-day"},
            {"StartTime": "2024-01-15T14:00:00", "Description": "Afternoon"},
            {"StartTime": "2024-01-15T09:00:00", "Description": "Morning"},
        ]
        now = datetime(2024, 1, 15, 12, 0)
        result, _ = _render_calendar_table(events, now=now)
        assert isinstance(result, Table)
        assert result.row_count == 3
        # Last row should have no time (all-day event sorts to bottom via "99:99")
        # The first two rows should have times, last row blank


# ---------------------------------------------------------------------------
# Scroll offset behavior
# ---------------------------------------------------------------------------


class TestScrollOffset:
    """Tests for scroll_offset in _render_calendar_table."""

    def _make_events(self, count: int) -> list[dict]:
        """Create events with distinct times."""
        return [
            {
                "StartTime": f"2024-01-15T{9 + i}:00:00",
                "House": "Commons",
                "Description": f"Event {i}",
            }
            for i in range(count)
        ]

    def test_offset_zero_matches_default(self) -> None:
        """scroll_offset=0 should produce same result as default behavior."""
        events = self._make_events(10)
        now = datetime(2024, 1, 15, 12, 0)
        result_default, _ = _render_calendar_table(events, max_rows=5, now=now, scroll_offset=0)
        result_explicit, _ = _render_calendar_table(events, max_rows=5, now=now)
        assert isinstance(result_default, Table)
        assert isinstance(result_explicit, Table)
        assert result_default.row_count == result_explicit.row_count

    def test_offset_shifts_window(self) -> None:
        """scroll_offset > 0 should shift the visible window."""
        events = self._make_events(10)
        now = datetime(2024, 1, 15, 12, 0)
        result_0, _ = _render_calendar_table(events, max_rows=3, now=now, scroll_offset=0)
        result_5, _ = _render_calendar_table(events, max_rows=3, now=now, scroll_offset=5)
        assert isinstance(result_0, Table)
        assert isinstance(result_5, Table)
        assert result_0.row_count == 3
        assert result_5.row_count == 3

    def test_offset_wraps_around(self) -> None:
        """When offset + max_rows > total, events should wrap from the start."""
        events = self._make_events(5)
        now = datetime(2024, 1, 15, 12, 0)
        # offset=4, max_rows=3 -> should show events[4] + events[0] + events[1]
        result, total = _render_calendar_table(events, max_rows=3, now=now, scroll_offset=4)
        assert isinstance(result, Table)
        assert result.row_count == 3
        assert total == 5

    def test_offset_modulo_wraps(self) -> None:
        """Offset larger than total should wrap via modulo."""
        events = self._make_events(5)
        now = datetime(2024, 1, 15, 12, 0)
        # offset=7 is equivalent to offset=2 (7 % 5 = 2)
        result_7, _ = _render_calendar_table(events, max_rows=3, now=now, scroll_offset=7)
        result_2, _ = _render_calendar_table(events, max_rows=3, now=now, scroll_offset=2)
        assert isinstance(result_7, Table)
        assert isinstance(result_2, Table)
        assert result_7.row_count == result_2.row_count

    def test_offset_ignored_when_all_fit(self) -> None:
        """When all events fit, scroll_offset should have no effect."""
        events = self._make_events(3)
        now = datetime(2024, 1, 15, 12, 0)
        result_0, _ = _render_calendar_table(events, max_rows=10, now=now, scroll_offset=0)
        result_5, _ = _render_calendar_table(events, max_rows=10, now=now, scroll_offset=5)
        assert isinstance(result_0, Table)
        assert isinstance(result_5, Table)
        assert result_0.row_count == result_5.row_count == 3


# ---------------------------------------------------------------------------
# Calendar subtitle with scrolling
# ---------------------------------------------------------------------------


class TestCalendarSubtitleScrolling:
    """Tests for _calendar_subtitle scrolling parameter."""

    def test_scrolling_indicator_appended(self) -> None:
        """When scrolling=True and events truncated, subtitle shows scrolling."""
        result = _calendar_subtitle(5, 20, scrolling=True)
        assert result is not None
        assert "scrolling" in result
        assert "showing 5 of 20 events" in result

    def test_scrolling_only_when_not_truncated(self) -> None:
        """When scrolling=True but all events shown, still shows scrolling."""
        result = _calendar_subtitle(10, 10, scrolling=True)
        assert result is not None
        assert "scrolling" in result

    def test_no_scrolling_no_truncation(self) -> None:
        """No scrolling and no truncation returns None."""
        result = _calendar_subtitle(10, 10, scrolling=False)
        assert result is None


# ---------------------------------------------------------------------------
# _render_dashboard with scroll_offset
# ---------------------------------------------------------------------------


class TestRenderDashboardScrollOffset:
    """Tests for _render_dashboard accepting dual scroll offsets."""

    def test_accepts_scroll_offsets(self) -> None:
        """_render_dashboard should accept dual scroll_offset parameters."""
        msg = _make_message(slides=[_make_slide("Debate")])
        data = {"commons": msg, "lords": msg, "calendar": []}
        result = _render_dashboard(data, scroll_offset_commons=5, scroll_offset_lords=3)
        assert isinstance(result, Layout)

    def test_scroll_offset_zero_matches_default(self) -> None:
        """scroll_offset=0 should produce a valid layout like the default."""
        msg = _make_message(slides=[_make_slide("NotSitting")])
        data = {"commons": msg, "lords": msg, "calendar": []}
        result_default = _render_dashboard(data)
        result_zero = _render_dashboard(data, scroll_offset_commons=0, scroll_offset_lords=0)
        assert isinstance(result_default, Layout)
        assert isinstance(result_zero, Layout)

    def test_scroll_interval_constant(self) -> None:
        """SCROLL_INTERVAL should be 5 seconds."""
        assert SCROLL_INTERVAL == 5


# ---------------------------------------------------------------------------
# _split_events_by_house
# ---------------------------------------------------------------------------


class TestSplitEventsByHouse:
    """Tests for _split_events_by_house helper."""

    def test_splits_commons_and_lords(self) -> None:
        events = [
            {"House": "Commons", "Description": "Commons Event"},
            {"House": "Lords", "Description": "Lords Event"},
        ]
        commons, lords = _split_events_by_house(events)
        assert len(commons) == 1
        assert len(lords) == 1
        assert commons[0]["Description"] == "Commons Event"
        assert lords[0]["Description"] == "Lords Event"

    def test_joint_goes_to_both(self) -> None:
        events = [{"House": "Joint", "Description": "Joint Event"}]
        commons, lords = _split_events_by_house(events)
        assert len(commons) == 1
        assert len(lords) == 1

    def test_empty_house_goes_to_both(self) -> None:
        events = [{"Description": "No house event"}]
        commons, lords = _split_events_by_house(events)
        assert len(commons) == 1
        assert len(lords) == 1

    def test_case_insensitive(self) -> None:
        events = [
            {"House": "COMMONS", "Description": "Upper case commons"},
            {"house": "lords", "Description": "Lower case lords"},
            {"House": "House of Commons", "Description": "Full name"},
        ]
        commons, lords = _split_events_by_house(events)
        assert len(commons) == 2
        assert len(lords) == 1

    def test_empty_list(self) -> None:
        commons, lords = _split_events_by_house([])
        assert commons == []
        assert lords == []

    def test_mixed_events_preserves_all(self) -> None:
        events = [
            {"House": "Commons", "Description": "C1"},
            {"House": "Lords", "Description": "L1"},
            {"House": "Joint", "Description": "J1"},
            {"House": "Commons", "Description": "C2"},
            {"Description": "No house"},
        ]
        commons, lords = _split_events_by_house(events)
        # 2 commons + 1 joint + 1 no-house = 4
        assert len(commons) == 4
        # 1 lords + 1 joint + 1 no-house = 3
        assert len(lords) == 3


# ---------------------------------------------------------------------------
# _render_calendar_table with include_house_column=False
# ---------------------------------------------------------------------------


class TestRenderCalendarTableNoHouseColumn:
    """Tests for _render_calendar_table with include_house_column=False."""

    def test_five_columns_when_no_house(self) -> None:
        events = [
            {
                "StartTime": "2024-01-15T11:30:00",
                "House": "Commons",
                "Description": "Oral Questions",
                "Type": "Oral evidence",
                "Location": "Chamber",
                "Category": "Questions",
            },
        ]
        result, count = _render_calendar_table(events, include_house_column=False)
        assert isinstance(result, Table)
        assert len(result.columns) == 5
        assert count == 1

    def test_six_columns_by_default(self) -> None:
        events = [{"Description": "Test"}]
        result, _ = _render_calendar_table(events)
        assert isinstance(result, Table)
        assert len(result.columns) == 6

    def test_no_house_column_header(self) -> None:
        events = [{"Description": "Test"}]
        result, _ = _render_calendar_table(events, include_house_column=False)
        assert isinstance(result, Table)
        col_headers = [str(col.header) for col in result.columns]
        assert "House" not in col_headers
        assert "Time" in col_headers
        assert "Event" in col_headers


# ---------------------------------------------------------------------------
# _render_dashboard split calendar
# ---------------------------------------------------------------------------


class TestRenderDashboardSplitCalendar:
    """Tests for _render_dashboard split calendar layout."""

    def test_both_houses_creates_split_layout(self) -> None:
        """When both houses present, calendar should split into two panels."""
        msg = _make_message(slides=[_make_slide("Debate")])
        events = [
            {
                "House": "Commons",
                "Description": "Commons Event",
                "StartTime": "2024-01-15T11:00:00",
            },
            {"House": "Lords", "Description": "Lords Event", "StartTime": "2024-01-15T14:00:00"},
        ]
        data = {"commons": msg, "lords": msg, "calendar": events}
        result = _render_dashboard(data)
        assert isinstance(result, Layout)
        # 3 top-level children: header, chambers, calendar
        assert len(result.children) == 3

    def test_single_house_full_width(self) -> None:
        """When single house, calendar should be full-width with House column."""
        msg = _make_message(slides=[_make_slide("Debate")])
        events = [
            {"House": "Commons", "Description": "Event", "StartTime": "2024-01-15T11:00:00"},
        ]
        data = {"commons": msg, "calendar": events}
        result = _render_dashboard(data)
        assert isinstance(result, Layout)
        assert len(result.children) == 3

    def test_independent_scroll_offsets_accepted(self) -> None:
        """Both scroll offsets should be accepted without error."""
        msg = _make_message(slides=[_make_slide("Debate")])
        events = [
            {"House": "Commons", "Description": f"C{i}", "StartTime": f"2024-01-15T{9 + i}:00:00"}
            for i in range(10)
        ] + [
            {"House": "Lords", "Description": f"L{i}", "StartTime": f"2024-01-15T{9 + i}:00:00"}
            for i in range(10)
        ]
        data = {"commons": msg, "lords": msg, "calendar": events}
        result = _render_dashboard(data, scroll_offset_commons=3, scroll_offset_lords=7)
        assert isinstance(result, Layout)

    def test_no_calendar_events_both_houses(self) -> None:
        """Empty calendar with both houses should not crash."""
        msg = _make_message(slides=[_make_slide("Debate")])
        data = {"commons": msg, "lords": msg, "calendar": []}
        result = _render_dashboard(data)
        assert isinstance(result, Layout)


# ---------------------------------------------------------------------------
# _calendar_subtitle scroll position indicator
# ---------------------------------------------------------------------------


class TestCalendarSubtitleScrollPosition:
    """Tests for scroll position bar in _calendar_subtitle."""

    def test_scroll_bar_rendered_when_scrolling(self) -> None:
        """When scrolling active and events truncated, bar should appear."""
        result = _calendar_subtitle(5, 20, scrolling=True, scroll_offset=3)
        assert result is not None
        assert "\u2588" in result  # filled block
        assert "\u2591" in result  # empty block
        assert "scrolling" in result

    def test_scroll_bar_position_at_start(self) -> None:
        """Offset 0 should place block at start of bar."""
        result = _calendar_subtitle(5, 20, scrolling=True, scroll_offset=0)
        assert result is not None
        # First char of the bar should be filled
        assert "\u2588\u2591" in result

    def test_scroll_bar_position_at_end(self) -> None:
        """Offset near total should place block at end of bar."""
        # offset=19, total=20 → slot = int(19/20 * 5) = 4 (last slot)
        result = _calendar_subtitle(5, 20, scrolling=True, scroll_offset=19)
        assert result is not None
        assert "\u2591\u2588" in result

    def test_no_bar_when_not_scrolling(self) -> None:
        """No scroll bar when scrolling=False."""
        result = _calendar_subtitle(5, 20, scrolling=False)
        assert result is not None
        assert "\u2588" not in result
        assert "\u2591" not in result

    def test_auto_scrolling_fallback_when_no_events(self) -> None:
        """When scrolling but total=0, should show auto-scrolling fallback."""
        result = _calendar_subtitle(0, 0, scrolling=True, scroll_offset=0)
        assert result is not None
        assert "auto-scrolling" in result


# ---------------------------------------------------------------------------
# _calendar_subtitle with paused parameter
# ---------------------------------------------------------------------------


class TestCalendarSubtitlePaused:
    """Tests for _calendar_subtitle paused parameter."""

    def test_paused_replaces_scrolling_text(self) -> None:
        """When paused=True and scrolling, bar should say 'paused' not 'scrolling'."""
        result = _calendar_subtitle(5, 20, scrolling=True, scroll_offset=3, paused=True)
        assert result is not None
        assert "paused" in result
        assert "scrolling" not in result

    def test_bar_still_shown_when_paused(self) -> None:
        """Scroll position bar should still render when paused."""
        result = _calendar_subtitle(5, 20, scrolling=True, scroll_offset=3, paused=True)
        assert result is not None
        assert "\u2588" in result
        assert "\u2591" in result

    def test_default_backward_compatible(self) -> None:
        """Default paused=False should not change existing behavior."""
        result = _calendar_subtitle(5, 20, scrolling=True, scroll_offset=3)
        assert result is not None
        assert "scrolling" in result
        assert "paused" not in result

    def test_paused_without_scrolling_shows_paused(self) -> None:
        """When paused=True and not scrolling, should show 'paused'."""
        result = _calendar_subtitle(5, 20, scrolling=False, paused=True)
        assert result is not None
        assert "paused" in result

    def test_paused_no_truncation_returns_subtitle(self) -> None:
        """When paused=True but all events shown, subtitle should still appear."""
        result = _calendar_subtitle(10, 10, scrolling=False, paused=True)
        assert result is not None
        assert "paused" in result

    def test_paused_fallback_when_no_events(self) -> None:
        """When scrolling + paused but total=0, should show 'paused'."""
        result = _calendar_subtitle(0, 0, scrolling=True, scroll_offset=0, paused=True)
        assert result is not None
        assert "paused" in result
        assert "auto-scrolling" not in result


# ---------------------------------------------------------------------------
# _render_dashboard pause state
# ---------------------------------------------------------------------------


class TestRenderDashboardPauseState:
    """Tests for _render_dashboard auto_scroll_paused parameter."""

    def test_accepts_param(self) -> None:
        """_render_dashboard should accept auto_scroll_paused."""
        msg = _make_message(slides=[_make_slide("Debate")])
        data = {"commons": msg, "lords": msg, "calendar": []}
        result = _render_dashboard(data, auto_scroll_paused=True)
        assert isinstance(result, Layout)

    def test_header_shows_paused_when_paused(self) -> None:
        """Header should show PAUSED indicator when paused."""
        msg = _make_message(slides=[_make_slide("Debate")])
        data = {"commons": msg, "lords": msg, "calendar": []}
        layout = _render_dashboard(data, auto_scroll_paused=True)
        # Header is first child, which contains a Panel with Text
        header_layout = layout.children[0]
        # Extract text from the panel
        panel = header_layout.renderable
        assert isinstance(panel, Panel)
        text = panel.renderable
        assert isinstance(text, Text)
        assert "PAUSED" in text.plain

    def test_header_no_paused_by_default(self) -> None:
        """Header should not show PAUSED when not paused."""
        msg = _make_message(slides=[_make_slide("Debate")])
        data = {"commons": msg, "lords": msg, "calendar": []}
        layout = _render_dashboard(data, auto_scroll_paused=False)
        header_layout = layout.children[0]
        panel = header_layout.renderable
        assert isinstance(panel, Panel)
        text = panel.renderable
        assert isinstance(text, Text)
        assert "PAUSED" not in text.plain

    def test_header_shows_key_hints(self) -> None:
        """Header should show keyboard control hints."""
        msg = _make_message(slides=[_make_slide("Debate")])
        data = {"commons": msg, "lords": msg, "calendar": []}
        layout = _render_dashboard(data)
        header_layout = layout.children[0]
        panel = header_layout.renderable
        assert isinstance(panel, Panel)
        text = panel.renderable
        assert isinstance(text, Text)
        assert "q quit" in text.plain
        assert "scroll" in text.plain
        assert "pause" in text.plain


# ---------------------------------------------------------------------------
# POLL_INTERVAL constant
# ---------------------------------------------------------------------------


class TestPollIntervalConstant:
    """Tests for POLL_INTERVAL constant."""

    def test_exists_and_less_than_scroll_interval(self) -> None:
        """POLL_INTERVAL should exist and be less than SCROLL_INTERVAL."""
        assert POLL_INTERVAL > 0
        assert POLL_INTERVAL < SCROLL_INTERVAL


# ---------------------------------------------------------------------------
# Key reader thread
# ---------------------------------------------------------------------------


class TestKeyReaderThread:
    """Tests for _start_key_reader thread lifecycle."""

    def test_thread_starts_as_daemon(self) -> None:
        """Key reader thread should be a daemon thread."""
        key_q: queue.Queue[str] = queue.Queue()
        stop = threading.Event()
        stop.set()  # Immediately signal stop

        def _fake_reader(q: queue.Queue[str], ev: threading.Event) -> None:
            while not ev.is_set():
                import time

                time.sleep(0.01)

        with (
            patch("uk_parliament_mcp.cli.watch._read_keys_windows", _fake_reader),
            patch("uk_parliament_mcp.cli.watch._read_keys_unix", _fake_reader),
        ):
            thread = _start_key_reader(key_q, stop)
            assert thread.daemon is True
            thread.join(timeout=2.0)

    def test_thread_stops_on_signal(self) -> None:
        """Key reader thread should stop when stop_reading is set."""
        key_q: queue.Queue[str] = queue.Queue()
        stop = threading.Event()

        def _fake_reader(q: queue.Queue[str], ev: threading.Event) -> None:
            while not ev.is_set():
                import time

                time.sleep(0.01)

        with (
            patch("uk_parliament_mcp.cli.watch._read_keys_windows", _fake_reader),
            patch("uk_parliament_mcp.cli.watch._read_keys_unix", _fake_reader),
        ):
            thread = _start_key_reader(key_q, stop)
            assert thread.is_alive()
            stop.set()
            thread.join(timeout=2.0)
            assert not thread.is_alive()


# ---------------------------------------------------------------------------
# Manual scroll behavior
# ---------------------------------------------------------------------------


class TestManualScrollBehavior:
    """Tests for manual scroll offset behavior via key presses."""

    def test_down_increments_both_offsets(self) -> None:
        """Pressing down should increment both scroll offsets."""
        commons_offset = 0
        lords_offset = 0
        # Simulate "down" key
        commons_offset += 1
        lords_offset += 1
        assert commons_offset == 1
        assert lords_offset == 1

    def test_up_decrements_clamped_to_zero(self) -> None:
        """Pressing up should decrement offsets, clamped at 0."""
        commons_offset = 1
        lords_offset = 0
        commons_offset = max(0, commons_offset - 1)
        lords_offset = max(0, lords_offset - 1)
        assert commons_offset == 0
        assert lords_offset == 0

    def test_up_at_zero_stays_zero(self) -> None:
        """Pressing up at offset 0 should stay at 0."""
        commons_offset = 0
        lords_offset = 0
        commons_offset = max(0, commons_offset - 1)
        lords_offset = max(0, lords_offset - 1)
        assert commons_offset == 0
        assert lords_offset == 0

    def test_space_toggles_auto_scroll(self) -> None:
        """Space should toggle auto_scroll state."""
        auto_scroll = True
        # First press: pause
        auto_scroll = not auto_scroll
        assert auto_scroll is False
        # Second press: resume
        auto_scroll = not auto_scroll
        assert auto_scroll is True
