"""Tests for parliament watch live dashboard."""

from __future__ import annotations

import json
from unittest.mock import patch

import pytest
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from uk_parliament_mcp.cli.watch import (
    MIN_INTERVAL,
    _fetch_all_data,
    _fetch_calendar_today,
    _fetch_commons_now,
    _fetch_lords_now,
    _format_slide_type_label,
    _parse_api_response,
    _render_calendar_table,
    _render_chamber_panel,
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
        msg = _make_message(slides=[
            _make_slide(
                "Debate",
                lines=[
                    _make_line("Online Safety Bill - Second Reading", "Text100", 1),
                ],
                speaker_time="2024-01-15T14:32:00",
            ),
        ])
        panel = _render_chamber_panel(msg, "House of Commons")
        assert isinstance(panel, Panel)
        # Active debate -> green border
        assert panel.border_style == "green"  # type: ignore[union-attr]
        rendered = panel.renderable
        assert isinstance(rendered, Text)
        assert "Debate" in rendered.plain
        assert "Online Safety Bill" in rendered.plain
        assert "14:32" in rendered.plain

    def test_division_slide(self) -> None:
        msg = _make_message(slides=[
            _make_slide(
                "Division",
                lines=[
                    _make_line("Ayes: 310  Noes: 250", "Division", 1),
                ],
            ),
        ])
        panel = _render_chamber_panel(msg, "House of Commons")
        rendered = panel.renderable
        assert isinstance(rendered, Text)
        assert "DIVISION" in rendered.plain
        assert "Ayes" in rendered.plain

    def test_pmqs_with_member(self) -> None:
        msg = _make_message(slides=[
            _make_slide(
                "PrimeMinistersQuestions",
                lines=[
                    _make_line("", "Member", 1, member=_make_member()),
                    _make_line("Question 1", "Text100", 2),
                ],
            ),
        ])
        panel = _render_chamber_panel(msg, "House of Commons")
        rendered = panel.renderable
        assert isinstance(rendered, Text)
        assert "Prime Minister's Questions" in rendered.plain
        assert "Sir Keir Starmer" in rendered.plain
        assert "Labour" in rendered.plain
        assert "Holborn and St Pancras" in rendered.plain

    def test_not_sitting_slide(self) -> None:
        msg = _make_message(slides=[
            _make_slide("NotSitting"),
        ])
        panel = _render_chamber_panel(msg, "House of Commons")
        assert panel.border_style == "dim"  # type: ignore[union-attr]
        rendered = panel.renderable
        assert isinstance(rendered, Text)
        assert "Not Sitting" in rendered.plain

    def test_house_risen_slide(self) -> None:
        msg = _make_message(slides=[
            _make_slide("HouseRisen"),
        ])
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
        msg = _make_message(slides=[
            _make_slide("Debate", lines=[_make_line("First item", "Text100", 1)]),
            _make_slide("Statement", lines=[_make_line("Ministerial Statement", "Text100", 1)]),
        ])
        panel = _render_chamber_panel(msg, "House of Commons")
        rendered = panel.renderable
        assert isinstance(rendered, Text)
        assert "Debate" in rendered.plain
        assert "Statement" in rendered.plain
        assert "Ministerial Statement" in rendered.plain

    def test_blank_slide_skipped(self) -> None:
        msg = _make_message(slides=[
            _make_slide("BlankSlide"),
            _make_slide("Debate", lines=[_make_line("Actual content", "Text100", 1)]),
        ])
        panel = _render_chamber_panel(msg, "House of Commons")
        rendered = panel.renderable
        assert isinstance(rendered, Text)
        assert "BlankSlide" not in rendered.plain
        assert "Actual content" in rendered.plain

    def test_divider_lines(self) -> None:
        msg = _make_message(slides=[
            _make_slide("Debate", lines=[
                _make_line("Before divider", "Text100", 1),
                _make_line("", "DividerSolid", 2),
                _make_line("After divider", "Text100", 3),
            ]),
        ])
        panel = _render_chamber_panel(msg, "House of Commons")
        rendered = panel.renderable
        assert isinstance(rendered, Text)
        assert "Before divider" in rendered.plain
        assert "After divider" in rendered.plain
        assert "----" in rendered.plain

    def test_empty_line_style(self) -> None:
        msg = _make_message(slides=[
            _make_slide("Debate", lines=[
                _make_line("Line one", "Text100", 1),
                _make_line("", "EmptyLine", 2),
                _make_line("Line two", "Text100", 3),
            ]),
        ])
        panel = _render_chamber_panel(msg, "House of Commons")
        rendered = panel.renderable
        assert isinstance(rendered, Text)
        assert "Line one" in rendered.plain
        assert "Line two" in rendered.plain

    def test_footer_style_dim(self) -> None:
        msg = _make_message(slides=[
            _make_slide("Debate", lines=[
                _make_line("Footer text", "Footer", 1),
            ]),
        ])
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
        msg = _make_message(slides=[
            _make_slide("Debate", lines=[
                _make_line("Third", "Text100", 3),
                _make_line("First", "Text100", 1),
                _make_line("Second", "Text100", 2),
            ]),
        ])
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
        result = _render_calendar_table([])
        assert isinstance(result, Text)

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
        result = _render_calendar_table(events)
        assert isinstance(result, Table)
        # Should have 6 columns: Time, House, Event, Type, Location, Category
        assert len(result.columns) == 6

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
        result = _render_calendar_table(events)
        assert isinstance(result, Table)
        assert len(result.columns) == 6
        # Verify column headers
        col_headers = [col.header for col in result.columns]
        assert "Type" in [str(h) for h in col_headers]
        assert "Location" in [str(h) for h in col_headers]

    def test_handles_missing_fields(self) -> None:
        events = [{"Description": "Test Event"}]
        result = _render_calendar_table(events)
        assert isinstance(result, Table)
        # Still has 6 columns even with missing data
        assert len(result.columns) == 6


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
        mock_response = json.dumps(
            {"url": "test", "data": [{"Description": "Event 1"}]}
        )
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
        assert MIN_INTERVAL == 10

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
