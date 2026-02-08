"""Tests for committees tools."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from mcp.server.fastmcp import FastMCP

from uk_parliament_mcp.config import COMMITTEES_API_BASE
from uk_parliament_mcp.tools import committees


class TestCommitteesToolsRegistration:
    """Tests for committees tools registration."""

    @pytest.fixture
    def mcp(self):
        """Create a FastMCP instance with committees tools registered."""
        server = FastMCP(name="test-server")
        committees.register_tools(server)
        return server

    @pytest.mark.asyncio
    async def test_register_tools_adds_all_12_tools(self, mcp: FastMCP):
        """register_tools adds all 12 committee tools."""
        tools = await mcp.list_tools()
        tool_names = [t.name for t in tools]

        expected_tools = [
            "get_committee_meetings",
            "search_committees",
            "get_committee_types",
            "get_committee_by_id",
            "get_events",
            "get_event_by_id",
            "get_committee_events",
            "get_committee_members",
            "get_publications",
            "get_publication_by_id",
            "get_written_evidence",
            "get_oral_evidence",
        ]

        for tool_name in expected_tools:
            assert tool_name in tool_names

    @pytest.mark.asyncio
    async def test_all_committees_tools_have_descriptions(self, mcp: FastMCP):
        """All committees tools have descriptions."""
        tools = await mcp.list_tools()
        for tool in tools:
            assert tool.description is not None
            assert len(tool.description) > 0


class TestGetCommitteeMeetings:
    """Tests for get_committee_meetings tool."""

    @pytest.mark.asyncio
    async def test_builds_correct_url(self):
        """get_committee_meetings builds correct URL."""
        with patch("uk_parliament_mcp.tools.committees.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            committees.register_tools(mcp)

            await mcp.call_tool(
                "get_committee_meetings", {"from_date": "2024-01-01", "to_date": "2024-01-31"}
            )

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert (
                call_url
                == f"{COMMITTEES_API_BASE}/Broadcast/Meetings?FromDate=2024-01-01&ToDate=2024-01-31"
            )

    @pytest.mark.asyncio
    async def test_url_encodes_special_characters(self):
        """get_committee_meetings URL-encodes special characters."""
        with patch("uk_parliament_mcp.tools.committees.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            committees.register_tools(mcp)

            await mcp.call_tool(
                "get_committee_meetings", {"from_date": "2024-01-01 00:00", "to_date": "2024-01-31"}
            )

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert "2024-01-01%2000%3A00" in call_url


class TestSearchCommittees:
    """Tests for search_committees tool."""

    @pytest.mark.asyncio
    async def test_builds_correct_url(self):
        """search_committees builds correct URL."""
        with patch("uk_parliament_mcp.tools.committees.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            committees.register_tools(mcp)

            await mcp.call_tool("search_committees", {"search_term": "Treasury"})

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert call_url == f"{COMMITTEES_API_BASE}/Committees?SearchTerm=Treasury"

    @pytest.mark.asyncio
    async def test_url_encodes_special_characters(self):
        """search_committees URL-encodes special characters."""
        with patch("uk_parliament_mcp.tools.committees.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            committees.register_tools(mcp)

            await mcp.call_tool("search_committees", {"search_term": "Women & Equalities"})

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert "Women%20%26%20Equalities" in call_url


class TestGetCommitteeTypes:
    """Tests for get_committee_types tool."""

    @pytest.mark.asyncio
    async def test_builds_correct_url(self):
        """get_committee_types builds correct URL."""
        with patch("uk_parliament_mcp.tools.committees.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            committees.register_tools(mcp)

            await mcp.call_tool("get_committee_types", {})

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert call_url == f"{COMMITTEES_API_BASE}/CommitteeType"


class TestGetCommitteeById:
    """Tests for get_committee_by_id tool."""

    @pytest.mark.asyncio
    async def test_builds_url_with_defaults(self):
        """get_committee_by_id builds URL with default parameters."""
        with patch("uk_parliament_mcp.tools.committees.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            committees.register_tools(mcp)

            await mcp.call_tool("get_committee_by_id", {"committee_id": 739})

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert f"{COMMITTEES_API_BASE}/Committees/739" in call_url
            assert "includeBanners=false" in call_url
            assert "showOnWebsiteOnly=true" in call_url

    @pytest.mark.asyncio
    async def test_builds_url_with_banners(self):
        """get_committee_by_id builds URL with include_banners=True."""
        with patch("uk_parliament_mcp.tools.committees.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            committees.register_tools(mcp)

            await mcp.call_tool(
                "get_committee_by_id", {"committee_id": 739, "include_banners": True}
            )

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert "includeBanners=true" in call_url


class TestGetEvents:
    """Tests for get_events tool."""

    @pytest.mark.asyncio
    async def test_builds_url_with_defaults(self):
        """get_events builds URL with default parameters."""
        with patch("uk_parliament_mcp.tools.committees.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            committees.register_tools(mcp)

            await mcp.call_tool("get_events", {})

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert f"{COMMITTEES_API_BASE}/Events" in call_url
            assert "IncludeEventAttendees=false" in call_url
            assert "ShowOnWebsiteOnly=true" in call_url
            assert "Skip=0" in call_url
            assert "Take=30" in call_url

    @pytest.mark.asyncio
    async def test_builds_url_with_all_params(self):
        """get_events builds URL with all optional parameters."""
        with patch("uk_parliament_mcp.tools.committees.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            committees.register_tools(mcp)

            await mcp.call_tool(
                "get_events",
                {
                    "committee_id": 123,
                    "search_term": "climate",
                    "start_date_from": "2024-01-01",
                    "start_date_to": "2024-12-31",
                    "exclude_cancelled_events": True,
                    "skip": 10,
                    "take": 50,
                },
            )

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert "CommitteeId=123" in call_url
            assert "SearchTerm=climate" in call_url
            assert "StartDateFrom=2024-01-01" in call_url
            assert "StartDateTo=2024-12-31" in call_url
            assert "ExcludeCancelledEvents=true" in call_url
            assert "Skip=10" in call_url
            assert "Take=50" in call_url

    @pytest.mark.asyncio
    async def test_filters_none_values(self):
        """get_events filters out None parameter values."""
        with patch("uk_parliament_mcp.tools.committees.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            committees.register_tools(mcp)

            await mcp.call_tool("get_events", {"committee_id": 123, "search_term": None})

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert "CommitteeId=123" in call_url
            assert "SearchTerm" not in call_url


class TestGetEventById:
    """Tests for get_event_by_id tool."""

    @pytest.mark.asyncio
    async def test_builds_correct_url(self):
        """get_event_by_id builds correct URL."""
        with patch("uk_parliament_mcp.tools.committees.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            committees.register_tools(mcp)

            await mcp.call_tool("get_event_by_id", {"event_id": 456})

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert f"{COMMITTEES_API_BASE}/Events/456" in call_url
            assert "showOnWebsiteOnly=true" in call_url


class TestGetCommitteeEvents:
    """Tests for get_committee_events tool."""

    @pytest.mark.asyncio
    async def test_builds_url_with_required_param(self):
        """get_committee_events builds URL with required committee_id."""
        with patch("uk_parliament_mcp.tools.committees.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            committees.register_tools(mcp)

            await mcp.call_tool("get_committee_events", {"committee_id": 739})

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert f"{COMMITTEES_API_BASE}/Committees/739/Events" in call_url
            assert "Skip=0" in call_url
            assert "Take=30" in call_url

    @pytest.mark.asyncio
    async def test_builds_url_with_filters(self):
        """get_committee_events builds URL with optional filters."""
        with patch("uk_parliament_mcp.tools.committees.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            committees.register_tools(mcp)

            await mcp.call_tool(
                "get_committee_events",
                {
                    "committee_id": 739,
                    "start_date_from": "2024-01-01",
                    "sort_ascending": True,
                },
            )

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert "StartDateFrom=2024-01-01" in call_url
            assert "SortAscending=true" in call_url


class TestGetCommitteeMembers:
    """Tests for get_committee_members tool."""

    @pytest.mark.asyncio
    async def test_builds_url_with_defaults(self):
        """get_committee_members builds URL with default parameters."""
        with patch("uk_parliament_mcp.tools.committees.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            committees.register_tools(mcp)

            await mcp.call_tool("get_committee_members", {"committee_id": 739})

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert f"{COMMITTEES_API_BASE}/Committees/739/Members" in call_url
            assert "ShowOnWebsiteOnly=true" in call_url
            assert "Skip=0" in call_url
            assert "Take=30" in call_url

    @pytest.mark.asyncio
    async def test_builds_url_with_membership_status(self):
        """get_committee_members builds URL with membership_status filter."""
        with patch("uk_parliament_mcp.tools.committees.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            committees.register_tools(mcp)

            await mcp.call_tool(
                "get_committee_members", {"committee_id": 739, "membership_status": "Current"}
            )

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert "MembershipStatus=Current" in call_url


class TestGetPublications:
    """Tests for get_publications tool."""

    @pytest.mark.asyncio
    async def test_builds_url_with_defaults(self):
        """get_publications builds URL with default parameters."""
        with patch("uk_parliament_mcp.tools.committees.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            committees.register_tools(mcp)

            await mcp.call_tool("get_publications", {})

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert f"{COMMITTEES_API_BASE}/Publications" in call_url
            assert "ShowOnWebsiteOnly=true" in call_url
            assert "Skip=0" in call_url
            assert "Take=30" in call_url

    @pytest.mark.asyncio
    async def test_builds_url_with_all_filters(self):
        """get_publications builds URL with all optional filters."""
        with patch("uk_parliament_mcp.tools.committees.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            committees.register_tools(mcp)

            await mcp.call_tool(
                "get_publications",
                {
                    "search_term": "climate change",
                    "start_date": "2024-01-01",
                    "end_date": "2024-12-31",
                    "committee_id": 739,
                    "skip": 20,
                    "take": 50,
                },
            )

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert "SearchTerm=climate+change" in call_url
            assert "StartDate=2024-01-01" in call_url
            assert "EndDate=2024-12-31" in call_url
            assert "CommitteeId=739" in call_url
            assert "Skip=20" in call_url
            assert "Take=50" in call_url


class TestGetPublicationById:
    """Tests for get_publication_by_id tool."""

    @pytest.mark.asyncio
    async def test_builds_correct_url(self):
        """get_publication_by_id builds correct URL."""
        with patch("uk_parliament_mcp.tools.committees.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            committees.register_tools(mcp)

            await mcp.call_tool("get_publication_by_id", {"publication_id": 12345})

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert f"{COMMITTEES_API_BASE}/Publications/12345" in call_url
            assert "showOnWebsiteOnly=true" in call_url


class TestGetWrittenEvidence:
    """Tests for get_written_evidence tool."""

    @pytest.mark.asyncio
    async def test_builds_url_with_defaults(self):
        """get_written_evidence builds URL with default parameters."""
        with patch("uk_parliament_mcp.tools.committees.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            committees.register_tools(mcp)

            await mcp.call_tool("get_written_evidence", {})

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert f"{COMMITTEES_API_BASE}/WrittenEvidence" in call_url
            assert "ShowOnWebsiteOnly=true" in call_url
            assert "Skip=0" in call_url
            assert "Take=30" in call_url

    @pytest.mark.asyncio
    async def test_builds_url_with_filters(self):
        """get_written_evidence builds URL with optional filters."""
        with patch("uk_parliament_mcp.tools.committees.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            committees.register_tools(mcp)

            await mcp.call_tool(
                "get_written_evidence",
                {
                    "committee_id": 739,
                    "search_term": "witness",
                    "start_date": "2024-01-01",
                    "end_date": "2024-12-31",
                },
            )

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert "CommitteeId=739" in call_url
            assert "SearchTerm=witness" in call_url
            assert "StartDate=2024-01-01" in call_url
            assert "EndDate=2024-12-31" in call_url


class TestGetOralEvidence:
    """Tests for get_oral_evidence tool."""

    @pytest.mark.asyncio
    async def test_builds_url_with_defaults(self):
        """get_oral_evidence builds URL with default parameters."""
        with patch("uk_parliament_mcp.tools.committees.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            committees.register_tools(mcp)

            await mcp.call_tool("get_oral_evidence", {})

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert f"{COMMITTEES_API_BASE}/OralEvidence" in call_url
            assert "ShowOnWebsiteOnly=true" in call_url
            assert "Skip=0" in call_url
            assert "Take=30" in call_url

    @pytest.mark.asyncio
    async def test_builds_url_with_filters(self):
        """get_oral_evidence builds URL with optional filters."""
        with patch("uk_parliament_mcp.tools.committees.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            committees.register_tools(mcp)

            await mcp.call_tool(
                "get_oral_evidence",
                {
                    "committee_id": 739,
                    "search_term": "testimony",
                    "start_date": "2024-01-01",
                },
            )

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert "CommitteeId=739" in call_url
            assert "SearchTerm=testimony" in call_url
            assert "StartDate=2024-01-01" in call_url
