"""Tests for treaties tools."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from mcp.server.fastmcp import FastMCP

from uk_parliament_mcp.config import TREATIES_API_BASE
from uk_parliament_mcp.tools import treaties


class TestTreatiesToolsRegistration:
    """Tests for treaties tools registration."""

    @pytest.fixture
    def mcp(self):
        """Create a FastMCP instance with treaties tools registered."""
        server = FastMCP(name="test-server")
        treaties.register_tools(server)
        return server

    @pytest.mark.asyncio
    async def test_register_tools_adds_search_treaties(self, mcp: FastMCP):
        """register_tools adds search_treaties tool."""
        tools = await mcp.list_tools()
        tool_names = [t.name for t in tools]

        assert "search_treaties" in tool_names

    @pytest.mark.asyncio
    async def test_search_treaties_has_description(self, mcp: FastMCP):
        """search_treaties tool has a description."""
        tools = await mcp.list_tools()
        tool = next(t for t in tools if t.name == "search_treaties")

        assert tool.description is not None
        assert len(tool.description) > 0


class TestSearchTreaties:
    """Tests for search_treaties tool."""

    @pytest.mark.asyncio
    async def test_builds_correct_url(self):
        """search_treaties builds correct URL with search_text parameter."""
        with patch("uk_parliament_mcp.tools.treaties.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            treaties.register_tools(mcp)

            await mcp.call_tool(
                "search_treaties",
                {"search_text": "trade"},
            )

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            expected_url = f"{TREATIES_API_BASE}/Treaty?SearchText=trade"
            assert call_url == expected_url

    @pytest.mark.asyncio
    async def test_handles_special_characters(self):
        """search_treaties properly URL-encodes special characters."""
        with patch("uk_parliament_mcp.tools.treaties.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            treaties.register_tools(mcp)

            await mcp.call_tool(
                "search_treaties",
                {"search_text": "climate & environment"},
            )

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            # Both %20 and + are valid encodings for space
            assert (
                "climate%20%26%20environment" in call_url or "climate+%26+environment" in call_url
            )

    @pytest.mark.asyncio
    async def test_handles_single_quotes(self):
        """search_treaties handles single quotes in search text."""
        with patch("uk_parliament_mcp.tools.treaties.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            treaties.register_tools(mcp)

            await mcp.call_tool(
                "search_treaties",
                {"search_text": "Queen's Commonwealth"},
            )

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            # Both %20 and + are valid encodings for space
            assert "Queen%27s%20Commonwealth" in call_url or "Queen%27s+Commonwealth" in call_url

    @pytest.mark.asyncio
    async def test_handles_abbreviations(self):
        """search_treaties handles abbreviations like EU, NATO."""
        with patch("uk_parliament_mcp.tools.treaties.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            treaties.register_tools(mcp)

            await mcp.call_tool(
                "search_treaties",
                {"search_text": "EU"},
            )

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            expected_url = f"{TREATIES_API_BASE}/Treaty?SearchText=EU"
            assert call_url == expected_url

    @pytest.mark.asyncio
    async def test_handles_multi_word_search(self):
        """search_treaties handles multi-word search terms."""
        with patch("uk_parliament_mcp.tools.treaties.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            treaties.register_tools(mcp)

            await mcp.call_tool(
                "search_treaties",
                {"search_text": "international trade agreements"},
            )

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            # Both %20 and + are valid encodings for space
            assert (
                "international%20trade%20agreements" in call_url
                or "international+trade+agreements" in call_url
            )
