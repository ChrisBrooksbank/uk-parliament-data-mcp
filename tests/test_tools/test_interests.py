"""Tests for interests tools."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from mcp.server.fastmcp import FastMCP

from uk_parliament_mcp.config import INTERESTS_API_BASE
from uk_parliament_mcp.tools import interests


class TestInterestsToolsRegistration:
    """Tests for interests tools registration."""

    @pytest.fixture
    def mcp(self):
        """Create a FastMCP instance with interests tools registered."""
        server = FastMCP(name="test-server")
        interests.register_tools(server)
        return server

    @pytest.mark.asyncio
    async def test_register_tools_adds_all_interest_tools(self, mcp: FastMCP):
        """register_tools adds all 3 interest tools."""
        tools = await mcp.list_tools()
        tool_names = [t.name for t in tools]

        assert "search_roi" in tool_names
        assert "interests_categories" in tool_names
        assert "get_registers_of_interests" in tool_names

    @pytest.mark.asyncio
    async def test_tools_have_descriptions(self, mcp: FastMCP):
        """All interest tools have descriptions."""
        tools = await mcp.list_tools()
        interest_tools = [t for t in tools if t.name in ["search_roi", "interests_categories", "get_registers_of_interests"]]

        for tool in interest_tools:
            assert tool.description is not None
            assert len(tool.description) > 0


class TestSearchROI:
    """Tests for search_roi tool."""

    @pytest.mark.asyncio
    async def test_builds_correct_url(self):
        """search_roi builds correct URL with member_id."""
        with patch("uk_parliament_mcp.tools.interests.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            interests.register_tools(mcp)

            await mcp.call_tool(
                "search_roi",
                {"member_id": 172},
            )

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert call_url == f"{INTERESTS_API_BASE}/Interests/?MemberId=172"

    @pytest.mark.asyncio
    async def test_handles_different_member_ids(self):
        """search_roi correctly handles different member IDs."""
        with patch("uk_parliament_mcp.tools.interests.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            interests.register_tools(mcp)

            # Test with different member ID
            await mcp.call_tool(
                "search_roi",
                {"member_id": 4567},
            )

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert "MemberId=4567" in call_url


class TestInterestsCategories:
    """Tests for interests_categories tool."""

    @pytest.mark.asyncio
    async def test_builds_correct_url(self):
        """interests_categories builds correct URL."""
        with patch("uk_parliament_mcp.tools.interests.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            interests.register_tools(mcp)

            await mcp.call_tool("interests_categories", {})

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert call_url == f"{INTERESTS_API_BASE}/Categories"


class TestGetRegistersOfInterests:
    """Tests for get_registers_of_interests tool."""

    @pytest.mark.asyncio
    async def test_builds_correct_url(self):
        """get_registers_of_interests builds correct URL."""
        with patch("uk_parliament_mcp.tools.interests.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            interests.register_tools(mcp)

            await mcp.call_tool("get_registers_of_interests", {})

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert call_url == f"{INTERESTS_API_BASE}/Registers"
