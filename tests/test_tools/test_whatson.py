"""Tests for whatson tools."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from mcp.server.fastmcp import FastMCP

from uk_parliament_mcp.config import WHATSON_API_BASE
from uk_parliament_mcp.tools import whatson


class TestWhatsOnToolsRegistration:
    """Tests for whatson tools registration."""

    @pytest.fixture
    def mcp(self):
        """Create a FastMCP instance with whatson tools registered."""
        server = FastMCP(name="test-server")
        whatson.register_tools(server)
        return server

    @pytest.mark.asyncio
    async def test_register_tools_adds_whatson_tools(self, mcp: FastMCP):
        """register_tools adds all three whatson tools."""
        tools = await mcp.list_tools()
        tool_names = [t.name for t in tools]

        assert "search_calendar" in tool_names
        assert "get_sessions" in tool_names
        assert "get_non_sitting_days" in tool_names

    @pytest.mark.asyncio
    async def test_search_calendar_has_description(self, mcp: FastMCP):
        """search_calendar tool has a description."""
        tools = await mcp.list_tools()
        tool = next(t for t in tools if t.name == "search_calendar")

        assert tool.description is not None
        assert len(tool.description) > 0

    @pytest.mark.asyncio
    async def test_get_sessions_has_description(self, mcp: FastMCP):
        """get_sessions tool has a description."""
        tools = await mcp.list_tools()
        tool = next(t for t in tools if t.name == "get_sessions")

        assert tool.description is not None
        assert len(tool.description) > 0

    @pytest.mark.asyncio
    async def test_get_non_sitting_days_has_description(self, mcp: FastMCP):
        """get_non_sitting_days tool has a description."""
        tools = await mcp.list_tools()
        tool = next(t for t in tools if t.name == "get_non_sitting_days")

        assert tool.description is not None
        assert len(tool.description) > 0


class TestSearchCalendar:
    """Tests for search_calendar tool."""

    @pytest.mark.asyncio
    async def test_builds_correct_url(self):
        """search_calendar builds correct URL with parameters."""
        with patch("uk_parliament_mcp.tools.whatson.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            whatson.register_tools(mcp)

            await mcp.call_tool(
                "search_calendar",
                {
                    "house": "Commons",
                    "start_date": "2024-01-01",
                    "end_date": "2024-01-31",
                },
            )

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            expected_base = f"{WHATSON_API_BASE}/events/list.json"
            assert expected_base in call_url
            assert "queryParameters.house=Commons" in call_url
            assert "queryParameters.startDate=2024-01-01" in call_url
            assert "queryParameters.endDate=2024-01-31" in call_url

    @pytest.mark.asyncio
    async def test_handles_lords_house(self):
        """search_calendar handles Lords house parameter."""
        with patch("uk_parliament_mcp.tools.whatson.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            whatson.register_tools(mcp)

            await mcp.call_tool(
                "search_calendar",
                {
                    "house": "Lords",
                    "start_date": "2024-02-01",
                    "end_date": "2024-02-28",
                },
            )

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert "queryParameters.house=Lords" in call_url


class TestGetSessions:
    """Tests for get_sessions tool."""

    @pytest.mark.asyncio
    async def test_builds_correct_url(self):
        """get_sessions builds correct URL."""
        with patch("uk_parliament_mcp.tools.whatson.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            whatson.register_tools(mcp)

            await mcp.call_tool("get_sessions", {})

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert call_url == f"{WHATSON_API_BASE}/sessions/list.json"


class TestGetNonSittingDays:
    """Tests for get_non_sitting_days tool."""

    @pytest.mark.asyncio
    async def test_builds_correct_url(self):
        """get_non_sitting_days builds correct URL with parameters."""
        with patch("uk_parliament_mcp.tools.whatson.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            whatson.register_tools(mcp)

            await mcp.call_tool(
                "get_non_sitting_days",
                {
                    "house": "Commons",
                    "start_date": "2024-01-01",
                    "end_date": "2024-12-31",
                },
            )

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            expected_base = f"{WHATSON_API_BASE}/events/nonsitting.json"
            assert expected_base in call_url
            assert "queryParameters.house=Commons" in call_url
            assert "queryParameters.startDate=2024-01-01" in call_url
            assert "queryParameters.endDate=2024-12-31" in call_url

    @pytest.mark.asyncio
    async def test_handles_lords_house(self):
        """get_non_sitting_days handles Lords house parameter."""
        with patch("uk_parliament_mcp.tools.whatson.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            whatson.register_tools(mcp)

            await mcp.call_tool(
                "get_non_sitting_days",
                {
                    "house": "Lords",
                    "start_date": "2024-06-01",
                    "end_date": "2024-08-31",
                },
            )

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert "queryParameters.house=Lords" in call_url
