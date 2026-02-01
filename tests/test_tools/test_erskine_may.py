"""Tests for erskine_may tools."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from mcp.server.fastmcp import FastMCP

from uk_parliament_mcp.config import ERSKINE_MAY_API_BASE
from uk_parliament_mcp.tools import erskine_may


class TestErskineMayToolsRegistration:
    """Tests for erskine_may tools registration."""

    @pytest.fixture
    def mcp(self):
        """Create a FastMCP instance with erskine_may tools registered."""
        server = FastMCP(name="test-server")
        erskine_may.register_tools(server)
        return server

    @pytest.mark.asyncio
    async def test_register_tools_adds_erskine_may_tool(self, mcp: FastMCP):
        """register_tools adds the search_erskine_may tool."""
        tools = await mcp.list_tools()
        tool_names = [t.name for t in tools]

        assert "search_erskine_may" in tool_names

    @pytest.mark.asyncio
    async def test_search_erskine_may_has_description(self, mcp: FastMCP):
        """search_erskine_may tool has a description."""
        tools = await mcp.list_tools()
        tool = next(t for t in tools if t.name == "search_erskine_may")

        assert tool.description is not None
        assert len(tool.description) > 0


class TestSearchErskineMay:
    """Tests for search_erskine_may tool."""

    @pytest.mark.asyncio
    async def test_builds_correct_url(self):
        """search_erskine_may builds correct URL."""
        with patch("uk_parliament_mcp.tools.erskine_may.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            erskine_may.register_tools(mcp)

            await mcp.call_tool(
                "search_erskine_may",
                {
                    "search_term": "Speaker",
                },
            )

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert f"{ERSKINE_MAY_API_BASE}/Search/ParagraphSearchResults/Speaker" in call_url

    @pytest.mark.asyncio
    async def test_url_encodes_spaces(self):
        """search_erskine_may URL-encodes spaces in search term."""
        with patch("uk_parliament_mcp.tools.erskine_may.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            erskine_may.register_tools(mcp)

            await mcp.call_tool(
                "search_erskine_may",
                {
                    "search_term": "parliamentary procedure",
                },
            )

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            # URL encoding: space -> %20
            assert "parliamentary%20procedure" in call_url

    @pytest.mark.asyncio
    async def test_url_encodes_special_characters(self):
        """search_erskine_may URL-encodes special characters in search term."""
        with patch("uk_parliament_mcp.tools.erskine_may.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            erskine_may.register_tools(mcp)

            await mcp.call_tool(
                "search_erskine_may",
                {
                    "search_term": "Speaker's rulings & precedents",
                },
            )

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            # URL encoding: ' -> %27, & -> %26, space -> %20
            assert "Speaker" in call_url
            assert "rulings" in call_url
            assert "precedents" in call_url
            # Special characters should be encoded
            assert "%26" in call_url or "&" not in call_url  # & should be encoded
