"""Tests for lords_votes tools."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from mcp.server.fastmcp import FastMCP

from uk_parliament_mcp.config import LORDS_VOTES_API_BASE
from uk_parliament_mcp.tools import lords_votes


class TestLordsVotesToolsRegistration:
    """Tests for lords_votes tools registration."""

    @pytest.fixture
    def mcp(self):
        """Create a FastMCP instance with lords_votes tools registered."""
        server = FastMCP(name="test-server")
        lords_votes.register_tools(server)
        return server

    @pytest.mark.asyncio
    async def test_register_tools_adds_all_5_tools(self, mcp: FastMCP):
        """register_tools adds all 5 lords votes tools."""
        tools = await mcp.list_tools()
        tool_names = [t.name for t in tools]

        expected_tools = [
            "search_lords_divisions",
            "get_lords_voting_record_for_member",
            "get_lords_division_by_id",
            "get_lords_divisions_grouped_by_party",
            "get_lords_divisions_search_count",
        ]

        for tool_name in expected_tools:
            assert tool_name in tool_names

    @pytest.mark.asyncio
    async def test_all_lords_votes_tools_have_descriptions(self, mcp: FastMCP):
        """All lords_votes tools have descriptions."""
        tools = await mcp.list_tools()
        for tool in tools:
            assert tool.description is not None
            assert len(tool.description) > 0


class TestSearchLordsDivisions:
    """Tests for search_lords_divisions tool."""

    @pytest.mark.asyncio
    async def test_builds_url_with_search_term(self):
        """search_lords_divisions builds URL with search term."""
        with patch("uk_parliament_mcp.tools.lords_votes.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            lords_votes.register_tools(mcp)

            await mcp.call_tool("search_lords_divisions", {"search_term": "brexit"})

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert f"{LORDS_VOTES_API_BASE}/divisions/search" in call_url
            assert "queryParameters.searchTerm=brexit" in call_url

    @pytest.mark.asyncio
    async def test_url_encodes_special_characters(self):
        """search_lords_divisions URL-encodes special characters in search term."""
        with patch("uk_parliament_mcp.tools.lords_votes.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            lords_votes.register_tools(mcp)

            await mcp.call_tool("search_lords_divisions", {"search_term": "tax & spend"})

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert "tax%20%26%20spend" in call_url or "tax+%26+spend" in call_url


class TestGetLordsVotingRecordForMember:
    """Tests for get_lords_voting_record_for_member tool."""

    @pytest.mark.asyncio
    async def test_builds_url_with_member_id_only(self):
        """get_lords_voting_record_for_member builds URL with member_id only."""
        with patch("uk_parliament_mcp.tools.lords_votes.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            lords_votes.register_tools(mcp)

            await mcp.call_tool("get_lords_voting_record_for_member", {"member_id": 4514})

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert f"{LORDS_VOTES_API_BASE}/Divisions/membervoting" in call_url
            assert "MemberId=4514" in call_url

    @pytest.mark.asyncio
    async def test_builds_url_with_search_term(self):
        """get_lords_voting_record_for_member builds URL with search term parameter."""
        with patch("uk_parliament_mcp.tools.lords_votes.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            lords_votes.register_tools(mcp)

            await mcp.call_tool("get_lords_voting_record_for_member", {"member_id": 4514, "search_term": "climate"})

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert "MemberId=4514" in call_url
            assert "SearchTerm=climate" in call_url

    @pytest.mark.asyncio
    async def test_builds_url_with_date_range(self):
        """get_lords_voting_record_for_member builds URL with date range parameters."""
        with patch("uk_parliament_mcp.tools.lords_votes.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            lords_votes.register_tools(mcp)

            await mcp.call_tool(
                "get_lords_voting_record_for_member",
                {
                    "member_id": 4514,
                    "start_date": "2023-01-01",
                    "end_date": "2023-12-31",
                },
            )

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert "StartDate=2023-01-01" in call_url
            assert "EndDate=2023-12-31" in call_url

    @pytest.mark.asyncio
    async def test_builds_url_with_pagination(self):
        """get_lords_voting_record_for_member builds URL with pagination parameters."""
        with patch("uk_parliament_mcp.tools.lords_votes.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            lords_votes.register_tools(mcp)

            await mcp.call_tool("get_lords_voting_record_for_member", {"member_id": 4514, "skip": 10, "take": 50})

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert "skip=10" in call_url
            assert "take=50" in call_url

    @pytest.mark.asyncio
    async def test_builds_url_with_all_params(self):
        """get_lords_voting_record_for_member builds URL with all parameters."""
        with patch("uk_parliament_mcp.tools.lords_votes.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            lords_votes.register_tools(mcp)

            await mcp.call_tool(
                "get_lords_voting_record_for_member",
                {
                    "member_id": 4514,
                    "search_term": "NHS",
                    "include_when_member_was_teller": True,
                    "start_date": "2023-01-01",
                    "end_date": "2023-12-31",
                    "division_number": 100,
                    "skip": 10,
                    "take": 50,
                },
            )

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert "MemberId=4514" in call_url
            assert "SearchTerm=NHS" in call_url
            assert "IncludeWhenMemberWasTeller=true" in call_url
            assert "StartDate=2023-01-01" in call_url
            assert "EndDate=2023-12-31" in call_url
            assert "DivisionNumber=100" in call_url
            assert "skip=10" in call_url
            assert "take=50" in call_url

    @pytest.mark.asyncio
    async def test_filters_none_values(self):
        """get_lords_voting_record_for_member filters out None parameter values."""
        with patch("uk_parliament_mcp.tools.lords_votes.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            lords_votes.register_tools(mcp)

            await mcp.call_tool(
                "get_lords_voting_record_for_member",
                {
                    "member_id": 4514,
                    "search_term": None,
                    "include_when_member_was_teller": None,
                    "start_date": None,
                    "end_date": None,
                    "division_number": None,
                },
            )

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert "MemberId=4514" in call_url
            assert "SearchTerm" not in call_url
            assert "IncludeWhenMemberWasTeller" not in call_url
            assert "StartDate" not in call_url
            assert "EndDate" not in call_url
            assert "DivisionNumber" not in call_url


class TestGetLordsDivisionById:
    """Tests for get_lords_division_by_id tool."""

    @pytest.mark.asyncio
    async def test_builds_correct_url(self):
        """get_lords_division_by_id builds correct URL."""
        with patch("uk_parliament_mcp.tools.lords_votes.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            lords_votes.register_tools(mcp)

            await mcp.call_tool("get_lords_division_by_id", {"division_id": 12345})

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert call_url == f"{LORDS_VOTES_API_BASE}/Divisions/12345"


class TestGetLordsDivisionsGroupedByParty:
    """Tests for get_lords_divisions_grouped_by_party tool."""

    @pytest.mark.asyncio
    async def test_builds_url_with_no_params(self):
        """get_lords_divisions_grouped_by_party builds URL with no optional params."""
        with patch("uk_parliament_mcp.tools.lords_votes.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            lords_votes.register_tools(mcp)

            await mcp.call_tool("get_lords_divisions_grouped_by_party", {})

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert call_url == f"{LORDS_VOTES_API_BASE}/Divisions/groupedbyparty"

    @pytest.mark.asyncio
    async def test_builds_url_with_search_term(self):
        """get_lords_divisions_grouped_by_party builds URL with search term."""
        with patch("uk_parliament_mcp.tools.lords_votes.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            lords_votes.register_tools(mcp)

            await mcp.call_tool("get_lords_divisions_grouped_by_party", {"search_term": "education"})

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert "SearchTerm=education" in call_url

    @pytest.mark.asyncio
    async def test_builds_url_with_all_params(self):
        """get_lords_divisions_grouped_by_party builds URL with all parameters."""
        with patch("uk_parliament_mcp.tools.lords_votes.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            lords_votes.register_tools(mcp)

            await mcp.call_tool(
                "get_lords_divisions_grouped_by_party",
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
            assert "SearchTerm=budget" in call_url
            assert "MemberId=4514" in call_url
            assert "StartDate=2023-01-01" in call_url
            assert "EndDate=2023-12-31" in call_url
            assert "DivisionNumber=50" in call_url
            assert "IncludeWhenMemberWasTeller=true" in call_url

    @pytest.mark.asyncio
    async def test_filters_none_values(self):
        """get_lords_divisions_grouped_by_party filters out None parameter values."""
        with patch("uk_parliament_mcp.tools.lords_votes.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            lords_votes.register_tools(mcp)

            await mcp.call_tool(
                "get_lords_divisions_grouped_by_party",
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
            assert "SearchTerm=test" in call_url
            assert "MemberId" not in call_url or "MemberId=None" not in call_url


class TestGetLordsDivisionsSearchCount:
    """Tests for get_lords_divisions_search_count tool."""

    @pytest.mark.asyncio
    async def test_builds_url_with_no_params(self):
        """get_lords_divisions_search_count builds URL with no optional params."""
        with patch("uk_parliament_mcp.tools.lords_votes.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            lords_votes.register_tools(mcp)

            await mcp.call_tool("get_lords_divisions_search_count", {})

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert call_url == f"{LORDS_VOTES_API_BASE}/Divisions/searchTotalResults"

    @pytest.mark.asyncio
    async def test_builds_url_with_search_term(self):
        """get_lords_divisions_search_count builds URL with search term."""
        with patch("uk_parliament_mcp.tools.lords_votes.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            lords_votes.register_tools(mcp)

            await mcp.call_tool("get_lords_divisions_search_count", {"search_term": "immigration"})

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert "SearchTerm=immigration" in call_url

    @pytest.mark.asyncio
    async def test_builds_url_with_all_params(self):
        """get_lords_divisions_search_count builds URL with all parameters."""
        with patch("uk_parliament_mcp.tools.lords_votes.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            lords_votes.register_tools(mcp)

            await mcp.call_tool(
                "get_lords_divisions_search_count",
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
            assert "SearchTerm=housing" in call_url
            assert "MemberId=1423" in call_url
            assert "StartDate=2022-06-01" in call_url
            assert "EndDate=2023-06-01" in call_url
            assert "DivisionNumber=75" in call_url
            assert "IncludeWhenMemberWasTeller=false" in call_url

    @pytest.mark.asyncio
    async def test_filters_none_values(self):
        """get_lords_divisions_search_count filters out None parameter values."""
        with patch("uk_parliament_mcp.tools.lords_votes.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            lords_votes.register_tools(mcp)

            await mcp.call_tool(
                "get_lords_divisions_search_count",
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
            assert call_url == f"{LORDS_VOTES_API_BASE}/Divisions/searchTotalResults"
