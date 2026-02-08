"""Tests for parliament watch live dashboard."""

from __future__ import annotations

import json
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
)
from uk_parliament_mcp.cli.watch import (
    _CHAMBER_MAX_FRACTION,
    _CHAMBER_MIN_HEIGHT,
    MIN_INTERVAL,
    _estimate_chamber_height,
    _fetch_all_data,
    _fetch_calendar_today,
    _fetch_commons_now,
    _fetch_lords_now,
    _render_dashboard,
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
        assert "----" in rendered.plain

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
