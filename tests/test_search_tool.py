"""Tests for the universal_search MCP tool."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _mock_api_response(data: dict | list) -> str:
    """Build a mock API response JSON string."""
    return json.dumps({"url": "https://test.example.com", "data": data})


# ---------------------------------------------------------------------------
# MCP tool tests
# ---------------------------------------------------------------------------


class TestUniversalSearchTool:
    """Tests for the universal_search MCP tool wrapper."""

    @pytest.mark.asyncio
    async def test_tool_returns_valid_json(self) -> None:
        """Tool returns valid JSON with expected structure."""
        mock_data = {"items": [{"value": {"id": 1}}], "totalResults": 1}
        with patch("uk_parliament_mcp.cli.search.get_result", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = _mock_api_response(mock_data)

            from uk_parliament_mcp.cli.search import _universal_search_async

            result = await _universal_search_async("NHS", ["members"], None, 5, 30)

        parsed = json.loads(result)
        assert parsed["query"] == "NHS"
        assert "summary" in parsed
        assert "results" in parsed

    @pytest.mark.asyncio
    async def test_tool_scope_parsing(self) -> None:
        """Tool correctly parses comma-separated scope string."""
        mock_data = {"items": [], "totalResults": 0}
        with patch("uk_parliament_mcp.cli.search.get_result", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = _mock_api_response(mock_data)

            from uk_parliament_mcp.cli.search import _universal_search_async

            result = await _universal_search_async("test", ["bills", "members"], None, 5, 30)

        parsed = json.loads(result)
        assert parsed["sources_queried"] == 2
        assert set(parsed["results"].keys()) == {"bills", "members"}

    @pytest.mark.asyncio
    async def test_tool_empty_scope_searches_all(self) -> None:
        """Empty scope searches all sources."""
        mock_data = {"items": [], "totalResults": 0}
        with patch("uk_parliament_mcp.cli.search.get_result", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = _mock_api_response(mock_data)

            from uk_parliament_mcp.cli.search import _universal_search_async

            result = await _universal_search_async("test", None, None, 5, 30)

        parsed = json.loads(result)
        assert parsed["sources_queried"] == 12

    @pytest.mark.asyncio
    async def test_tool_result_structure(self) -> None:
        """Tool result has expected top-level keys."""
        mock_data = {"items": [{"value": {"id": 1, "nameDisplayAs": "Test"}}], "totalResults": 1}
        with patch("uk_parliament_mcp.cli.search.get_result", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = _mock_api_response(mock_data)

            from uk_parliament_mcp.cli.search import _universal_search_async

            result = await _universal_search_async("test", ["members"], None, 5, 30)

        parsed = json.loads(result)
        assert "query" in parsed
        assert "sources_queried" in parsed
        assert "summary" in parsed
        assert "results" in parsed

        # Check summary structure
        assert "members" in parsed["summary"]
        member_summary = parsed["summary"]["members"]
        assert "total" in member_summary
        assert "returned" in member_summary
        assert "error" in member_summary

        # Check result structure
        assert "members" in parsed["results"]
        member_result = parsed["results"]["members"]
        assert "source" in member_result
        assert "display_name" in member_result
        assert "items" in member_result
