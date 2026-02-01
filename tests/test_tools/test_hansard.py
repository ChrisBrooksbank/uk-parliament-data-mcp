"""Tests for hansard tools."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from mcp.server.fastmcp import FastMCP

from uk_parliament_mcp.config import HANSARD_API_BASE
from uk_parliament_mcp.tools import hansard


class TestHansardToolsRegistration:
    """Tests for hansard tools registration."""

    @pytest.fixture
    def mcp(self):
        """Create a FastMCP instance with hansard tools registered."""
        server = FastMCP(name="test-server")
        hansard.register_tools(server)
        return server

    @pytest.mark.asyncio
    async def test_register_tools_adds_hansard_tool(self, mcp: FastMCP):
        """register_tools adds the search_hansard tool."""
        tools = await mcp.list_tools()
        tool_names = [t.name for t in tools]

        assert "search_hansard" in tool_names

    @pytest.mark.asyncio
    async def test_search_hansard_has_description(self, mcp: FastMCP):
        """search_hansard tool has a description."""
        tools = await mcp.list_tools()
        tool = next(t for t in tools if t.name == "search_hansard")

        assert tool.description is not None
        assert len(tool.description) > 0


class TestSearchHansard:
    """Tests for search_hansard tool."""

    @pytest.mark.asyncio
    async def test_builds_correct_url_commons(self):
        """search_hansard builds correct URL for Commons."""
        with patch("uk_parliament_mcp.tools.hansard.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            hansard.register_tools(mcp)

            await mcp.call_tool(
                "search_hansard",
                {
                    "house": 1,
                    "start_date": "2024-01-01",
                    "end_date": "2024-01-31",
                    "search_term": "climate change",
                },
            )

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert f"{HANSARD_API_BASE}/search.json" in call_url
            assert "queryParameters.house=1" in call_url
            assert "queryParameters.startDate=2024-01-01" in call_url
            assert "queryParameters.endDate=2024-01-31" in call_url
            # URL encoding: space can be %20 or +
            assert "queryParameters.searchTerm=climate" in call_url
            assert "change" in call_url

    @pytest.mark.asyncio
    async def test_builds_correct_url_lords(self):
        """search_hansard builds correct URL for Lords."""
        with patch("uk_parliament_mcp.tools.hansard.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            hansard.register_tools(mcp)

            await mcp.call_tool(
                "search_hansard",
                {
                    "house": 2,
                    "start_date": "2024-06-01",
                    "end_date": "2024-06-30",
                    "search_term": "NHS",
                },
            )

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert "queryParameters.house=2" in call_url
            assert "queryParameters.startDate=2024-06-01" in call_url
            assert "queryParameters.endDate=2024-06-30" in call_url
            assert "queryParameters.searchTerm=NHS" in call_url

    @pytest.mark.asyncio
    async def test_url_encodes_special_characters(self):
        """search_hansard URL-encodes special characters in search term."""
        with patch("uk_parliament_mcp.tools.hansard.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            hansard.register_tools(mcp)

            await mcp.call_tool(
                "search_hansard",
                {
                    "house": 1,
                    "start_date": "2024-01-01",
                    "end_date": "2024-01-31",
                    "search_term": "Johnson & May's policies",
                },
            )

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            # URL encoding: & -> %26, ' -> %27, space -> %20
            assert "%20" in call_url or "+" in call_url  # Space encoding
            assert "Johnson" in call_url
