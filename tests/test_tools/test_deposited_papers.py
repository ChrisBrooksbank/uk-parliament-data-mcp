"""Tests for deposited_papers tools."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch
from urllib.parse import parse_qs, urlsplit

import pytest
from mcp.server.fastmcp import FastMCP

from uk_parliament_mcp.config import DEPOSITED_PAPERS_API_BASE
from uk_parliament_mcp.tools import deposited_papers


async def _call(tool: str, arguments: dict) -> str:
    with patch(
        "uk_parliament_mcp.tools.deposited_papers.get_result", new_callable=AsyncMock
    ) as mock:
        mock.return_value = '{"url": "test", "data": "{}"}'

        mcp = FastMCP(name="test")
        deposited_papers.register_tools(mcp)
        await mcp.call_tool(tool, arguments)

        mock.assert_called_once()
        return mock.call_args[0][0]


class TestDepositedPapersToolsRegistration:
    """Tests for deposited_papers tools registration."""

    @pytest.mark.asyncio
    async def test_registers_both_tools(self):
        """register_tools adds the search and get tools, each with a description."""
        mcp = FastMCP(name="test-server")
        deposited_papers.register_tools(mcp)
        tools = await mcp.list_tools()

        assert {t.name for t in tools} == {"search_deposited_papers", "get_deposited_paper"}
        assert all(t.description for t in tools)


class TestSearchDepositedPapers:
    """Tests for search_deposited_papers tool."""

    @pytest.mark.asyncio
    async def test_no_arguments_has_no_query(self):
        url = await _call("search_deposited_papers", {})
        assert url == f"{DEPOSITED_PAPERS_API_BASE}/DepositedPapers"

    @pytest.mark.asyncio
    async def test_maps_all_parameters(self):
        url = await _call(
            "search_deposited_papers",
            {
                "terms": "defence",
                "house": "lords",
                "deposited_from": "2025-01-01",
                "deposited_to": "2025-12-31",
                "department_ses_id": 17,
                "order_by": "CommitmentDateDesc",
                "skip": 20,
                "take": 10,
            },
        )
        assert url.startswith(f"{DEPOSITED_PAPERS_API_BASE}/DepositedPapers?")
        assert parse_qs(urlsplit(url).query) == {
            "Terms": ["defence"],
            "House": ["Lords"],
            "DepositedFrom": ["2025-01-01"],
            "DepositedTo": ["2025-12-31"],
            "DepartmentSesId": ["17"],
            "OrderBy": ["CommitmentDateDesc"],
            "Skip": ["20"],
            "Take": ["10"],
        }

    @pytest.mark.asyncio
    @pytest.mark.parametrize(("house", "expected"), [(1, "Commons"), (2, "Lords")])
    async def test_house_accepts_ids(self, house: int, expected: str):
        url = await _call("search_deposited_papers", {"house": house})
        assert parse_qs(urlsplit(url).query) == {"House": [expected]}


class TestGetDepositedPaper:
    """Tests for get_deposited_paper tool."""

    @pytest.mark.asyncio
    async def test_builds_correct_url(self):
        url = await _call("get_deposited_paper", {"paper_id": 2288285})
        assert url == f"{DEPOSITED_PAPERS_API_BASE}/DepositedPapers/2288285"
