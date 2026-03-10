"""Tests for hansard tools."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from mcp.server.fastmcp import FastMCP

from uk_parliament_mcp.config import HANSARD_API_BASE
from uk_parliament_mcp.tools import hansard


class TestHansardToolsRegistration:
    """Tests for hansard tools registration."""

    @pytest.fixture
    def mcp(self):
        """Create a FastMCP instance with hansard tools registered."""
        server = FastMCP(name="test-server")
        hansard.register_tools(server)
        return server

    @pytest.mark.asyncio
    async def test_register_tools_adds_all_hansard_tools(self, mcp: FastMCP):
        """register_tools adds all hansard tools."""
        tools = await mcp.list_tools()
        tool_names = [t.name for t in tools]

        expected_tools = [
            "search_hansard",
            "get_debate_by_id",
            "get_member_hansard_contributions",
            "get_debate_divisions",
            "get_division_details",
            "get_hansard_sitting_day",
            "get_hansard_calendar",
            "get_hansard_currently_processing",
            "get_hansard_first_year",
            "get_hansard_pdfs_for_day",
            "get_hansard_speakers_for_day",
            "search_committee_debates",
            "search_hansard_committees",
            "get_debate_by_column",
            "get_debate_by_external_id",
            "search_hansard_petitions",
            "get_hansard_timeline_stats",
        ]
        for tool_name in expected_tools:
            assert tool_name in tool_names

    @pytest.mark.asyncio
    async def test_all_tools_have_descriptions(self, mcp: FastMCP):
        """All hansard tools have descriptions."""
        tools = await mcp.list_tools()

        for tool in tools:
            assert tool.description is not None
            assert len(tool.description) > 0


class TestSearchHansard:
    """Tests for search_hansard tool."""

    @pytest.mark.asyncio
    async def test_builds_correct_url_commons(self):
        """search_hansard builds correct URL for Commons."""
        with patch("uk_parliament_mcp.tools.hansard.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            hansard.register_tools(mcp)

            await mcp.call_tool(
                "search_hansard",
                {
                    "house": 1,
                    "start_date": "2024-01-01",
                    "end_date": "2024-01-31",
                    "search_term": "climate change",
                },
            )

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert f"{HANSARD_API_BASE}/search/debates.json" in call_url
            assert "queryParameters.house=1" in call_url
            assert "queryParameters.startDate=2024-01-01" in call_url
            assert "queryParameters.endDate=2024-01-31" in call_url
            # URL encoding: space can be %20 or +
            assert "queryParameters.searchTerm=climate" in call_url
            assert "change" in call_url

    @pytest.mark.asyncio
    async def test_builds_correct_url_lords(self):
        """search_hansard builds correct URL for Lords."""
        with patch("uk_parliament_mcp.tools.hansard.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            hansard.register_tools(mcp)

            await mcp.call_tool(
                "search_hansard",
                {
                    "house": 2,
                    "start_date": "2024-06-01",
                    "end_date": "2024-06-30",
                    "search_term": "NHS",
                },
            )

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert "queryParameters.house=2" in call_url
            assert "queryParameters.startDate=2024-06-01" in call_url
            assert "queryParameters.endDate=2024-06-30" in call_url
            assert "queryParameters.searchTerm=NHS" in call_url

    @pytest.mark.asyncio
    async def test_url_encodes_special_characters(self):
        """search_hansard URL-encodes special characters in search term."""
        with patch("uk_parliament_mcp.tools.hansard.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            hansard.register_tools(mcp)

            await mcp.call_tool(
                "search_hansard",
                {
                    "house": 1,
                    "start_date": "2024-01-01",
                    "end_date": "2024-01-31",
                    "search_term": "Johnson & May's policies",
                },
            )

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            # URL encoding: & -> %26, ' -> %27, space -> %20
            assert "%20" in call_url or "+" in call_url  # Space encoding
            assert "Johnson" in call_url

    @pytest.mark.asyncio
    async def test_with_optional_member_id(self):
        """search_hansard includes member_id when provided."""
        with patch("uk_parliament_mcp.tools.hansard.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            hansard.register_tools(mcp)

            await mcp.call_tool(
                "search_hansard",
                {
                    "house": 1,
                    "start_date": "2024-01-01",
                    "end_date": "2024-01-31",
                    "search_term": "Brexit",
                    "member_id": 4514,
                },
            )

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert "queryParameters.memberId=4514" in call_url

    @pytest.mark.asyncio
    async def test_with_pagination(self):
        """search_hansard includes skip and take parameters."""
        with patch("uk_parliament_mcp.tools.hansard.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            hansard.register_tools(mcp)

            await mcp.call_tool(
                "search_hansard",
                {
                    "house": 1,
                    "start_date": "2024-01-01",
                    "end_date": "2024-01-31",
                    "search_term": "tax",
                    "skip": 20,
                    "take": 50,
                },
            )

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert "queryParameters.skip=20" in call_url
            assert "queryParameters.take=50" in call_url


class TestGetDebateById:
    """Tests for get_debate_by_id tool."""

    @pytest.mark.asyncio
    async def test_builds_correct_url(self):
        """get_debate_by_id builds correct URL."""
        with patch("uk_parliament_mcp.tools.hansard.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            hansard.register_tools(mcp)

            await mcp.call_tool(
                "get_debate_by_id",
                {"debate_section_id": "abc123-def456"},
            )

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert f"{HANSARD_API_BASE}/debates/debate/abc123-def456.json" == call_url


class TestGetMemberHansardContributions:
    """Tests for get_member_hansard_contributions tool."""

    @pytest.mark.asyncio
    async def test_builds_correct_url(self):
        """get_member_hansard_contributions builds correct URL."""
        with patch("uk_parliament_mcp.tools.hansard.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            hansard.register_tools(mcp)

            await mcp.call_tool(
                "get_member_hansard_contributions",
                {
                    "member_id": 4514,
                    "debate_section_id": "abc123",
                },
            )

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert f"{HANSARD_API_BASE}/debates/memberdebatecontributions/4514.json" in call_url
            assert "debateSectionExtId=abc123" in call_url


class TestGetDebateDivisions:
    """Tests for get_debate_divisions tool."""

    @pytest.mark.asyncio
    async def test_builds_correct_url(self):
        """get_debate_divisions builds correct URL."""
        with patch("uk_parliament_mcp.tools.hansard.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            hansard.register_tools(mcp)

            await mcp.call_tool(
                "get_debate_divisions",
                {"debate_section_id": "xyz789"},
            )

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert f"{HANSARD_API_BASE}/debates/divisions/xyz789.json" == call_url


class TestGetDivisionDetails:
    """Tests for get_division_details tool."""

    @pytest.mark.asyncio
    async def test_builds_correct_url_default(self):
        """get_division_details builds correct URL with defaults."""
        with patch("uk_parliament_mcp.tools.hansard.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            hansard.register_tools(mcp)

            await mcp.call_tool(
                "get_division_details",
                {"division_id": "div123"},
            )

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert f"{HANSARD_API_BASE}/debates/division/div123.json" in call_url
            # isEvel should not be in URL when False
            assert "isEvel" not in call_url

    @pytest.mark.asyncio
    async def test_builds_correct_url_with_evel(self):
        """get_division_details includes isEvel when True."""
        with patch("uk_parliament_mcp.tools.hansard.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            hansard.register_tools(mcp)

            await mcp.call_tool(
                "get_division_details",
                {
                    "division_id": "div123",
                    "is_evel": True,
                },
            )

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert "isEvel=True" in call_url or "isEvel=true" in call_url


class TestGetHansardSittingDay:
    """Tests for get_hansard_sitting_day tool."""

    @pytest.mark.asyncio
    async def test_builds_correct_url_commons(self):
        """get_hansard_sitting_day builds correct URL for Commons."""
        with patch("uk_parliament_mcp.tools.hansard.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            hansard.register_tools(mcp)

            await mcp.call_tool(
                "get_hansard_sitting_day",
                {
                    "sitting_date": "2024-03-15",
                    "house": 1,
                },
            )

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert f"{HANSARD_API_BASE}/overview/sectionsforday.json" in call_url
            assert "date=2024-03-15" in call_url
            assert "house=1" in call_url

    @pytest.mark.asyncio
    async def test_builds_correct_url_lords(self):
        """get_hansard_sitting_day builds correct URL for Lords."""
        with patch("uk_parliament_mcp.tools.hansard.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            hansard.register_tools(mcp)

            await mcp.call_tool(
                "get_hansard_sitting_day",
                {
                    "sitting_date": "2024-03-15",
                    "house": 2,
                },
            )

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert "house=2" in call_url


class TestGetHansardCalendar:
    """Tests for get_hansard_calendar tool."""

    @pytest.mark.asyncio
    async def test_builds_correct_url(self):
        """get_hansard_calendar builds correct URL."""
        with patch("uk_parliament_mcp.tools.hansard.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            hansard.register_tools(mcp)

            await mcp.call_tool(
                "get_hansard_calendar",
                {
                    "year": 2024,
                    "month": 3,
                    "house": 1,
                },
            )

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert f"{HANSARD_API_BASE}/overview/calendar.json" in call_url
            assert "year=2024" in call_url
            assert "month=3" in call_url
            assert "house=1" in call_url


class TestGetHansardCurrentlyProcessing:
    """Tests for get_hansard_currently_processing tool."""

    @pytest.mark.asyncio
    async def test_builds_correct_url(self):
        """get_hansard_currently_processing builds correct URL."""
        with patch("uk_parliament_mcp.tools.hansard.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            hansard.register_tools(mcp)

            await mcp.call_tool("get_hansard_currently_processing", {})

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert call_url == f"{HANSARD_API_BASE}/overview/currentlyprocessing.json"


class TestGetHansardFirstYear:
    """Tests for get_hansard_first_year tool."""

    @pytest.mark.asyncio
    async def test_builds_correct_url(self):
        """get_hansard_first_year builds correct URL."""
        with patch("uk_parliament_mcp.tools.hansard.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            hansard.register_tools(mcp)

            await mcp.call_tool("get_hansard_first_year", {})

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert call_url == f"{HANSARD_API_BASE}/overview/firstyear.json"


class TestGetHansardPdfsForDay:
    """Tests for get_hansard_pdfs_for_day tool."""

    @pytest.mark.asyncio
    async def test_builds_correct_url(self):
        """get_hansard_pdfs_for_day builds correct URL."""
        with patch("uk_parliament_mcp.tools.hansard.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            hansard.register_tools(mcp)

            await mcp.call_tool(
                "get_hansard_pdfs_for_day",
                {"date": "2024-03-15", "house": 1},
            )

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert f"{HANSARD_API_BASE}/overview/pdfsforday.json" in call_url
            assert "date=2024-03-15" in call_url
            assert "house=1" in call_url


class TestGetHansardSpeakersForDay:
    """Tests for get_hansard_speakers_for_day tool."""

    @pytest.mark.asyncio
    async def test_builds_correct_url(self):
        """get_hansard_speakers_for_day builds correct URL with path params."""
        with patch("uk_parliament_mcp.tools.hansard.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            hansard.register_tools(mcp)

            await mcp.call_tool(
                "get_hansard_speakers_for_day",
                {"date": "2024-03-15", "house": 1, "section": "Debate"},
            )

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert f"{HANSARD_API_BASE}/overview/speakerslist/2024-03-15/1.json" in call_url
            assert "section=Debate" in call_url


class TestSearchCommitteeDebates:
    """Tests for search_committee_debates tool."""

    @pytest.mark.asyncio
    async def test_builds_correct_url_with_committee_title(self):
        """search_committee_debates builds correct URL with committee title filter."""
        with patch("uk_parliament_mcp.tools.hansard.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            hansard.register_tools(mcp)

            await mcp.call_tool(
                "search_committee_debates",
                {
                    "house": 1,
                    "search_term": "NHS",
                    "committee_title": "Health Committee",
                },
            )

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert f"{HANSARD_API_BASE}/search/committeedebates.json" in call_url
            assert "queryParameters.house=1" in call_url
            assert "queryParameters.searchTerm=NHS" in call_url
            assert "queryParameters.committeeTitle=Health" in call_url


class TestSearchHansardCommittees:
    """Tests for search_hansard_committees tool."""

    @pytest.mark.asyncio
    async def test_builds_correct_url(self):
        """search_hansard_committees builds correct URL."""
        with patch("uk_parliament_mcp.tools.hansard.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            hansard.register_tools(mcp)

            await mcp.call_tool(
                "search_hansard_committees",
                {"search_term": "Treasury"},
            )

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert f"{HANSARD_API_BASE}/search/committees.json" in call_url
            assert "queryParameters.searchTerm=Treasury" in call_url


class TestGetDebateByColumn:
    """Tests for get_debate_by_column tool."""

    @pytest.mark.asyncio
    async def test_builds_correct_url(self):
        """get_debate_by_column builds correct URL."""
        with patch("uk_parliament_mcp.tools.hansard.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            hansard.register_tools(mcp)

            await mcp.call_tool(
                "get_debate_by_column",
                {"house": 1, "column_number": 425, "volume_number": 730},
            )

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert f"{HANSARD_API_BASE}/search/debatebycolumn.json" in call_url
            assert "queryParameters.house=1" in call_url
            assert "queryParameters.columnNumber=425" in call_url
            assert "queryParameters.volumeNumber=730" in call_url


class TestGetDebateByExternalId:
    """Tests for get_debate_by_external_id tool."""

    @pytest.mark.asyncio
    async def test_builds_correct_url(self):
        """get_debate_by_external_id builds correct URL."""
        with patch("uk_parliament_mcp.tools.hansard.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            hansard.register_tools(mcp)

            await mcp.call_tool(
                "get_debate_by_external_id",
                {"content_item_external_id": "ext-abc-123", "house": 1},
            )

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert f"{HANSARD_API_BASE}/search/debatebyexternalid.json" in call_url
            assert "contentItemExternalId=ext-abc-123" in call_url
            assert "house=1" in call_url


class TestSearchHansardPetitions:
    """Tests for search_hansard_petitions tool."""

    @pytest.mark.asyncio
    async def test_builds_correct_url(self):
        """search_hansard_petitions builds correct URL."""
        with patch("uk_parliament_mcp.tools.hansard.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            hansard.register_tools(mcp)

            await mcp.call_tool(
                "search_hansard_petitions",
                {"search_term": "climate", "house": 1},
            )

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert f"{HANSARD_API_BASE}/search/petitions.json" in call_url
            assert "queryParameters.searchTerm=climate" in call_url
            assert "queryParameters.house=1" in call_url


class TestGetHansardTimelineStats:
    """Tests for get_hansard_timeline_stats tool."""

    @pytest.mark.asyncio
    async def test_builds_correct_url(self):
        """get_hansard_timeline_stats builds correct URL."""
        with patch("uk_parliament_mcp.tools.hansard.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            hansard.register_tools(mcp)

            await mcp.call_tool(
                "get_hansard_timeline_stats",
                {
                    "search_term": "Brexit",
                    "house": 1,
                    "start_date": "2016-01-01",
                    "end_date": "2020-12-31",
                },
            )

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert f"{HANSARD_API_BASE}/timeline-stats.json" in call_url
            assert "queryParameters.searchTerm=Brexit" in call_url
            assert "queryParameters.house=1" in call_url
