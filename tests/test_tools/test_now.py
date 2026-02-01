"""Tests for now tools."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from mcp.server.fastmcp import FastMCP

from uk_parliament_mcp.config import NOW_API_BASE
from uk_parliament_mcp.tools import now


class TestNowToolsRegistration:
    """Tests for now tools registration."""

    @pytest.fixture
    def mcp(self):
        """Create a FastMCP instance with now tools registered."""
        server = FastMCP(name="test-server")
        now.register_tools(server)
        return server

    @pytest.mark.asyncio
    async def test_register_tools_adds_now_tools(self, mcp: FastMCP):
        """register_tools adds both now tools."""
        tools = await mcp.list_tools()
        tool_names = [t.name for t in tools]

        assert "happening_now_in_commons" in tool_names
        assert "happening_now_in_lords" in tool_names

    @pytest.mark.asyncio
    async def test_happening_now_in_commons_has_description(self, mcp: FastMCP):
        """happening_now_in_commons tool has a description."""
        tools = await mcp.list_tools()
        tool = next(t for t in tools if t.name == "happening_now_in_commons")

        assert tool.description is not None
        assert len(tool.description) > 0

    @pytest.mark.asyncio
    async def test_happening_now_in_lords_has_description(self, mcp: FastMCP):
        """happening_now_in_lords tool has a description."""
        tools = await mcp.list_tools()
        tool = next(t for t in tools if t.name == "happening_now_in_lords")

        assert tool.description is not None
        assert len(tool.description) > 0


class TestHappeningNowInCommons:
    """Tests for happening_now_in_commons tool."""

    @pytest.mark.asyncio
    async def test_builds_correct_url(self):
        """happening_now_in_commons builds correct URL."""
        with patch("uk_parliament_mcp.tools.now.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            now.register_tools(mcp)

            await mcp.call_tool("happening_now_in_commons", {})

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert call_url == f"{NOW_API_BASE}/Message/message/CommonsMain/current"


class TestHappeningNowInLords:
    """Tests for happening_now_in_lords tool."""

    @pytest.mark.asyncio
    async def test_builds_correct_url(self):
        """happening_now_in_lords builds correct URL."""
        with patch("uk_parliament_mcp.tools.now.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            now.register_tools(mcp)

            await mcp.call_tool("happening_now_in_lords", {})

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert call_url == f"{NOW_API_BASE}/Message/message/LordsMain/current"
