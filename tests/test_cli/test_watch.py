"""Tests for parliament watch live dashboard."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

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
    _parse_api_response,
    _render_calendar_table,
    _render_chamber_panel,
    _render_dashboard,
)


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
        response = json.dumps({"Description": "Debate", "Category": "Main"})
        result = _parse_api_response(response)
        assert result == {"Description": "Debate", "Category": "Main"}


class TestRenderChamberPanel:
    """Tests for _render_chamber_panel."""

    def test_renders_not_sitting_when_none(self) -> None:
        panel = _render_chamber_panel(None, "House of Commons")
        assert isinstance(panel, Panel)
        assert "House of Commons" in panel.title  # type: ignore[operator]

    def test_renders_not_sitting_when_empty(self) -> None:
        panel = _render_chamber_panel({}, "House of Lords")
        assert isinstance(panel, Panel)

    def test_renders_activity_data(self) -> None:
        data = {
            "Description": "Online Safety Bill - Second Reading",
            "Category": "Legislation",
            "StartTime": "14:00",
        }
        panel = _render_chamber_panel(data, "House of Commons")
        assert isinstance(panel, Panel)

    def test_renders_division_in_progress(self) -> None:
        data = {
            "Description": "Test Division",
            "DivisionInProgress": True,
        }
        panel = _render_chamber_panel(data, "House of Commons")
        assert isinstance(panel, Panel)

    def test_renders_fallback_fields(self) -> None:
        data = {"customField": "value", "anotherField": 42}
        panel = _render_chamber_panel(data, "House of Lords")
        assert isinstance(panel, Panel)


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
            },
            {
                "StartTime": "2024-01-15T14:00:00",
                "House": "Lords",
                "Title": "NHS Debate",
                "Type": "General Debate",
            },
        ]
        result = _render_calendar_table(events)
        assert isinstance(result, Table)

    def test_handles_missing_fields(self) -> None:
        events = [{"Description": "Test Event"}]
        result = _render_calendar_table(events)
        assert isinstance(result, Table)


class TestRenderDashboard:
    """Tests for _render_dashboard."""

    def test_renders_both_houses(self) -> None:
        data = {
            "commons": {"Description": "Test"},
            "lords": {"Description": "Test2"},
            "calendar": [],
        }
        result = _render_dashboard(data)
        assert isinstance(result, Layout)

    def test_renders_commons_only(self) -> None:
        data = {"commons": {"Description": "Test"}, "calendar": []}
        result = _render_dashboard(data)
        assert isinstance(result, Layout)

    def test_renders_lords_only(self) -> None:
        data = {"lords": {"Description": "Test"}, "calendar": []}
        result = _render_dashboard(data)
        assert isinstance(result, Layout)

    def test_renders_with_empty_data(self) -> None:
        data = {"commons": None, "lords": None, "calendar": []}
        result = _render_dashboard(data)
        assert isinstance(result, Layout)


class TestFetchFunctions:
    """Tests for async fetch functions."""

    @pytest.mark.asyncio
    async def test_fetch_commons_now(self) -> None:
        mock_response = json.dumps(
            {"url": "test", "data": {"Description": "Test Debate"}}
        )
        with patch("uk_parliament_mcp.cli.watch.get_result", return_value=mock_response):
            result = await _fetch_commons_now()
            assert result == {"Description": "Test Debate"}

    @pytest.mark.asyncio
    async def test_fetch_lords_now(self) -> None:
        mock_response = json.dumps(
            {"url": "test", "data": {"Description": "Lords Debate"}}
        )
        with patch("uk_parliament_mcp.cli.watch.get_result", return_value=mock_response):
            result = await _fetch_lords_now()
            assert result == {"Description": "Lords Debate"}

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
        mock_response = json.dumps({"url": "test", "data": {"Description": "Test"}})
        with patch("uk_parliament_mcp.cli.watch.get_result", return_value=mock_response):
            result = await _fetch_all_data()
            assert "commons" in result
            assert "lords" in result
            assert "calendar" in result

    @pytest.mark.asyncio
    async def test_fetch_all_data_commons_only(self) -> None:
        mock_response = json.dumps({"url": "test", "data": {"Description": "Test"}})
        with patch("uk_parliament_mcp.cli.watch.get_result", return_value=mock_response):
            result = await _fetch_all_data("commons")
            assert "commons" in result
            assert "lords" not in result

    @pytest.mark.asyncio
    async def test_fetch_all_data_lords_only(self) -> None:
        mock_response = json.dumps({"url": "test", "data": {"Description": "Test"}})
        with patch("uk_parliament_mcp.cli.watch.get_result", return_value=mock_response):
            result = await _fetch_all_data("lords")
            assert "lords" in result
            assert "commons" not in result


class TestWatchCommand:
    """Tests for the watch CLI command."""

    def test_min_interval_constant(self) -> None:
        assert MIN_INTERVAL == 10
