"""Tests for commons_votes tools."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from mcp.server.fastmcp import FastMCP

from uk_parliament_mcp.config import COMMONS_VOTES_API_BASE
from uk_parliament_mcp.tools import commons_votes


class TestCommonsVotesToolsRegistration:
    """Tests for commons_votes tools registration."""

    @pytest.fixture
    def mcp(self):
        """Create a FastMCP instance with commons_votes tools registered."""
        server = FastMCP(name="test-server")
        commons_votes.register_tools(server)
        return server

    @pytest.mark.asyncio
    async def test_register_tools_adds_all_5_tools(self, mcp: FastMCP):
        """register_tools adds all 5 commons votes tools."""
        tools = await mcp.list_tools()
        tool_names = [t.name for t in tools]

        expected_tools = [
            "search_commons_divisions",
            "get_commons_voting_record_for_member",
            "get_commons_division_by_id",
            "get_commons_divisions_grouped_by_party",
            "get_commons_divisions_search_count",
        ]

        for tool_name in expected_tools:
            assert tool_name in tool_names

    @pytest.mark.asyncio
    async def test_all_commons_votes_tools_have_descriptions(self, mcp: FastMCP):
        """All commons_votes tools have descriptions."""
        tools = await mcp.list_tools()
        for tool in tools:
            assert tool.description is not None
            assert len(tool.description) > 0


class TestSearchCommonsDivisions:
    """Tests for search_commons_divisions tool."""

    @pytest.mark.asyncio
    async def test_builds_url_with_search_term_only(self):
        """search_commons_divisions builds URL with search term only."""
        with patch(
            "uk_parliament_mcp.tools.commons_votes.get_result", new_callable=AsyncMock
        ) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            commons_votes.register_tools(mcp)

            await mcp.call_tool("search_commons_divisions", {"search_term": "brexit"})

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert f"{COMMONS_VOTES_API_BASE}/divisions.json/search" in call_url
            assert "queryParameters.searchTerm=brexit" in call_url

    @pytest.mark.asyncio
    async def test_builds_url_with_member_id(self):
        """search_commons_divisions builds URL with member_id parameter."""
        with patch(
            "uk_parliament_mcp.tools.commons_votes.get_result", new_callable=AsyncMock
        ) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            commons_votes.register_tools(mcp)

            await mcp.call_tool(
                "search_commons_divisions", {"search_term": "climate", "member_id": 4514}
            )

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert "queryParameters.searchTerm=climate" in call_url
            assert "memberId=4514" in call_url

    @pytest.mark.asyncio
    async def test_builds_url_with_date_range(self):
        """search_commons_divisions builds URL with date range parameters."""
        with patch(
            "uk_parliament_mcp.tools.commons_votes.get_result", new_callable=AsyncMock
        ) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            commons_votes.register_tools(mcp)

            await mcp.call_tool(
                "search_commons_divisions",
                {
                    "search_term": "NHS",
                    "start_date": "2023-01-01",
                    "end_date": "2023-12-31",
                },
            )

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert "queryParameters.startDate=2023-01-01" in call_url
            assert "queryParameters.endDate=2023-12-31" in call_url

    @pytest.mark.asyncio
    async def test_builds_url_with_division_number(self):
        """search_commons_divisions builds URL with division_number parameter."""
        with patch(
            "uk_parliament_mcp.tools.commons_votes.get_result", new_callable=AsyncMock
        ) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            commons_votes.register_tools(mcp)

            await mcp.call_tool(
                "search_commons_divisions", {"search_term": "test", "division_number": 100}
            )

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert "queryParameters.divisionNumber=100" in call_url

    @pytest.mark.asyncio
    async def test_filters_none_values(self):
        """search_commons_divisions filters out None parameter values."""
        with patch(
            "uk_parliament_mcp.tools.commons_votes.get_result", new_callable=AsyncMock
        ) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            commons_votes.register_tools(mcp)

            await mcp.call_tool(
                "search_commons_divisions",
                {
                    "search_term": "test",
                    "member_id": None,
                    "start_date": None,
                    "end_date": None,
                    "division_number": None,
                },
            )

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert "queryParameters.searchTerm=test" in call_url
            assert "memberId" not in call_url
            assert "startDate" not in call_url
            assert "endDate" not in call_url
            assert "divisionNumber" not in call_url

    @pytest.mark.asyncio
    async def test_url_encodes_special_characters(self):
        """search_commons_divisions URL-encodes special characters in search term."""
        with patch(
            "uk_parliament_mcp.tools.commons_votes.get_result", new_callable=AsyncMock
        ) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            commons_votes.register_tools(mcp)

            await mcp.call_tool("search_commons_divisions", {"search_term": "tax & spend"})

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert "tax%20%26%20spend" in call_url or "tax+%26+spend" in call_url


class TestGetCommonsVotingRecordForMember:
    """Tests for get_commons_voting_record_for_member tool."""

    @pytest.mark.asyncio
    async def test_builds_correct_url(self):
        """get_commons_voting_record_for_member builds correct URL."""
        with patch(
            "uk_parliament_mcp.tools.commons_votes.get_result", new_callable=AsyncMock
        ) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            commons_votes.register_tools(mcp)

            await mcp.call_tool("get_commons_voting_record_for_member", {"member_id": 4514})

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert (
                call_url
                == f"{COMMONS_VOTES_API_BASE}/divisions.json/membervoting?queryParameters.memberId=4514"
            )


class TestGetCommonsDivisionById:
    """Tests for get_commons_division_by_id tool."""

    @pytest.mark.asyncio
    async def test_builds_correct_url(self):
        """get_commons_division_by_id builds correct URL."""
        with patch(
            "uk_parliament_mcp.tools.commons_votes.get_result", new_callable=AsyncMock
        ) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            commons_votes.register_tools(mcp)

            await mcp.call_tool("get_commons_division_by_id", {"division_id": 12345})

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert call_url == f"{COMMONS_VOTES_API_BASE}/division/12345.json"


class TestGetCommonsDivisionsGroupedByParty:
    """Tests for get_commons_divisions_grouped_by_party tool."""

    @pytest.mark.asyncio
    async def test_builds_url_with_no_params(self):
        """get_commons_divisions_grouped_by_party builds URL with no optional params."""
        with patch(
            "uk_parliament_mcp.tools.commons_votes.get_result", new_callable=AsyncMock
        ) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            commons_votes.register_tools(mcp)

            await mcp.call_tool("get_commons_divisions_grouped_by_party", {})

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert call_url == f"{COMMONS_VOTES_API_BASE}/divisions.json/groupedbyparty"

    @pytest.mark.asyncio
    async def test_builds_url_with_search_term(self):
        """get_commons_divisions_grouped_by_party builds URL with search term."""
        with patch(
            "uk_parliament_mcp.tools.commons_votes.get_result", new_callable=AsyncMock
        ) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            commons_votes.register_tools(mcp)

            await mcp.call_tool(
                "get_commons_divisions_grouped_by_party", {"search_term": "education"}
            )

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert "queryParameters.searchTerm=education" in call_url

    @pytest.mark.asyncio
    async def test_builds_url_with_all_params(self):
        """get_commons_divisions_grouped_by_party builds URL with all parameters."""
        with patch(
            "uk_parliament_mcp.tools.commons_votes.get_result", new_callable=AsyncMock
        ) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            commons_votes.register_tools(mcp)

            await mcp.call_tool(
                "get_commons_divisions_grouped_by_party",
                {
                    "search_term": "budget",
                    "member_id": 4514,
                    "start_date": "2023-01-01",
                    "end_date": "2023-12-31",
                    "division_number": 50,
                    "include_when_member_was_teller": True,
                },
            )

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert "queryParameters.searchTerm=budget" in call_url
            assert "queryParameters.memberId=4514" in call_url
            assert "queryParameters.startDate=2023-01-01" in call_url
            assert "queryParameters.endDate=2023-12-31" in call_url
            assert "queryParameters.divisionNumber=50" in call_url
            assert "queryParameters.includeWhenMemberWasTeller=true" in call_url

    @pytest.mark.asyncio
    async def test_filters_none_values(self):
        """get_commons_divisions_grouped_by_party filters out None parameter values."""
        with patch(
            "uk_parliament_mcp.tools.commons_votes.get_result", new_callable=AsyncMock
        ) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            commons_votes.register_tools(mcp)

            await mcp.call_tool(
                "get_commons_divisions_grouped_by_party",
                {
                    "search_term": "test",
                    "member_id": None,
                    "start_date": None,
                    "end_date": None,
                    "division_number": None,
                    "include_when_member_was_teller": None,
                },
            )

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert "queryParameters.searchTerm=test" in call_url
            assert "memberId" not in call_url or "memberId=None" not in call_url


class TestGetCommonsDivisionsSearchCount:
    """Tests for get_commons_divisions_search_count tool."""

    @pytest.mark.asyncio
    async def test_builds_url_with_no_params(self):
        """get_commons_divisions_search_count builds URL with no optional params."""
        with patch(
            "uk_parliament_mcp.tools.commons_votes.get_result", new_callable=AsyncMock
        ) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            commons_votes.register_tools(mcp)

            await mcp.call_tool("get_commons_divisions_search_count", {})

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert call_url == f"{COMMONS_VOTES_API_BASE}/divisions.json/searchTotalResults"

    @pytest.mark.asyncio
    async def test_builds_url_with_search_term(self):
        """get_commons_divisions_search_count builds URL with search term."""
        with patch(
            "uk_parliament_mcp.tools.commons_votes.get_result", new_callable=AsyncMock
        ) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            commons_votes.register_tools(mcp)

            await mcp.call_tool(
                "get_commons_divisions_search_count", {"search_term": "immigration"}
            )

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert "queryParameters.searchTerm=immigration" in call_url

    @pytest.mark.asyncio
    async def test_builds_url_with_all_params(self):
        """get_commons_divisions_search_count builds URL with all parameters."""
        with patch(
            "uk_parliament_mcp.tools.commons_votes.get_result", new_callable=AsyncMock
        ) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            commons_votes.register_tools(mcp)

            await mcp.call_tool(
                "get_commons_divisions_search_count",
                {
                    "search_term": "housing",
                    "member_id": 1423,
                    "start_date": "2022-06-01",
                    "end_date": "2023-06-01",
                    "division_number": 75,
                    "include_when_member_was_teller": False,
                },
            )

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert "queryParameters.searchTerm=housing" in call_url
            assert "queryParameters.memberId=1423" in call_url
            assert "queryParameters.startDate=2022-06-01" in call_url
            assert "queryParameters.endDate=2023-06-01" in call_url
            assert "queryParameters.divisionNumber=75" in call_url
            assert "queryParameters.includeWhenMemberWasTeller=false" in call_url

    @pytest.mark.asyncio
    async def test_filters_none_values(self):
        """get_commons_divisions_search_count filters out None parameter values."""
        with patch(
            "uk_parliament_mcp.tools.commons_votes.get_result", new_callable=AsyncMock
        ) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            commons_votes.register_tools(mcp)

            await mcp.call_tool(
                "get_commons_divisions_search_count",
                {
                    "search_term": None,
                    "member_id": None,
                    "start_date": None,
                    "end_date": None,
                    "division_number": None,
                    "include_when_member_was_teller": None,
                },
            )

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            # Should not have any parameters besides the base URL
            assert call_url == f"{COMMONS_VOTES_API_BASE}/divisions.json/searchTotalResults"
