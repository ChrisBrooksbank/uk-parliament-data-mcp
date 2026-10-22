"""Tests for websearch tools."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch
from urllib.parse import parse_qs, urlsplit

import pytest
from mcp.server.fastmcp import FastMCP

from uk_parliament_mcp.config import WEBSEARCH_API_BASE
from uk_parliament_mcp.tools import websearch


class TestWebSearchToolsRegistration:
    """Tests for websearch tools registration."""

    @pytest.fixture
    def mcp(self):
        """Create a FastMCP instance with websearch tools registered."""
        server = FastMCP(name="test-server")
        websearch.register_tools(server)
        return server

    @pytest.mark.asyncio
    async def test_register_tools_adds_search_parliament_website(self, mcp: FastMCP):
        """register_tools adds the search_parliament_website tool."""
        tools = await mcp.list_tools()

        assert [t.name for t in tools] == ["search_parliament_website"]

    @pytest.mark.asyncio
    async def test_search_parliament_website_has_description(self, mcp: FastMCP):
        """search_parliament_website tool has a description."""
        tools = await mcp.list_tools()

        assert tools[0].description


class TestSearchParliamentWebsite:
    """Tests for search_parliament_website tool."""

    @staticmethod
    async def _call(arguments: dict) -> str:
        with patch("uk_parliament_mcp.tools.websearch.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            websearch.register_tools(mcp)
            await mcp.call_tool("search_parliament_website", arguments)

            mock.assert_called_once()
            return mock.call_args[0][0]

    @pytest.mark.asyncio
    async def test_builds_correct_url(self):
        """Search terms go to /WebSearch as searchTerms."""
        url = await self._call({"search_terms": "climate change"})

        assert url.startswith(f"{WEBSEARCH_API_BASE}/WebSearch?")
        assert parse_qs(urlsplit(url).query) == {"searchTerms": ["climate change"]}

    @pytest.mark.asyncio
    async def test_includes_paging_parameters(self):
        """start and take are passed through when given."""
        url = await self._call({"search_terms": "budget", "start": 21, "take": 10})

        assert parse_qs(urlsplit(url).query) == {
            "searchTerms": ["budget"],
            "start": ["21"],
            "take": ["10"],
        }
