"""Tests for whatson tools."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from mcp.server.fastmcp import FastMCP

from uk_parliament_mcp.config import WHATSON_API_BASE
from uk_parliament_mcp.tools import whatson


class TestWhatsOnToolsRegistration:
    """Tests for whatson tools registration."""

    @pytest.fixture
    def mcp(self):
        """Create a FastMCP instance with whatson tools registered."""
        server = FastMCP(name="test-server")
        whatson.register_tools(server)
        return server

    @pytest.mark.asyncio
    async def test_register_tools_adds_whatson_tools(self, mcp: FastMCP):
        """register_tools adds all three whatson tools."""
        tools = await mcp.list_tools()
        tool_names = [t.name for t in tools]

        assert "search_calendar" in tool_names
        assert "get_sessions" in tool_names
        assert "get_non_sitting_days" in tool_names

    @pytest.mark.asyncio
    async def test_search_calendar_has_description(self, mcp: FastMCP):
        """search_calendar tool has a description."""
        tools = await mcp.list_tools()
        tool = next(t for t in tools if t.name == "search_calendar")

        assert tool.description is not None
        assert len(tool.description) > 0

    @pytest.mark.asyncio
    async def test_get_sessions_has_description(self, mcp: FastMCP):
        """get_sessions tool has a description."""
        tools = await mcp.list_tools()
        tool = next(t for t in tools if t.name == "get_sessions")

        assert tool.description is not None
        assert len(tool.description) > 0

    @pytest.mark.asyncio
    async def test_get_non_sitting_days_has_description(self, mcp: FastMCP):
        """get_non_sitting_days tool has a description."""
        tools = await mcp.list_tools()
        tool = next(t for t in tools if t.name == "get_non_sitting_days")

        assert tool.description is not None
        assert len(tool.description) > 0


class TestSearchCalendar:
    """Tests for search_calendar tool."""

    @pytest.mark.asyncio
    async def test_builds_correct_url(self):
        """search_calendar builds correct URL with parameters."""
        with patch("uk_parliament_mcp.tools.whatson.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            whatson.register_tools(mcp)

            await mcp.call_tool(
                "search_calendar",
                {
                    "house": "Commons",
                    "start_date": "2024-01-01",
                    "end_date": "2024-01-31",
                },
            )

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            expected_base = f"{WHATSON_API_BASE}/events/list.json"
            assert expected_base in call_url
            assert "queryParameters.house=Commons" in call_url
            assert "queryParameters.startDate=2024-01-01" in call_url
            assert "queryParameters.endDate=2024-01-31" in call_url

    @pytest.mark.asyncio
    async def test_handles_lords_house(self):
        """search_calendar handles Lords house parameter."""
        with patch("uk_parliament_mcp.tools.whatson.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            whatson.register_tools(mcp)

            await mcp.call_tool(
                "search_calendar",
                {
                    "house": "Lords",
                    "start_date": "2024-02-01",
                    "end_date": "2024-02-28",
                },
            )

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert "queryParameters.house=Lords" in call_url


class TestGetSessions:
    """Tests for get_sessions tool."""

    @pytest.mark.asyncio
    async def test_builds_correct_url(self):
        """get_sessions builds correct URL."""
        with patch("uk_parliament_mcp.tools.whatson.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            whatson.register_tools(mcp)

            await mcp.call_tool("get_sessions", {})

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert call_url == f"{WHATSON_API_BASE}/sessions/list.json"


class TestGetNonSittingDays:
    """Tests for get_non_sitting_days tool."""

    @pytest.mark.asyncio
    async def test_builds_correct_url(self):
        """get_non_sitting_days builds correct URL with parameters."""
        with patch("uk_parliament_mcp.tools.whatson.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            whatson.register_tools(mcp)

            await mcp.call_tool(
                "get_non_sitting_days",
                {
                    "house": "Commons",
                    "start_date": "2024-01-01",
                    "end_date": "2024-12-31",
                },
            )

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            expected_base = f"{WHATSON_API_BASE}/events/nonsitting.json"
            assert expected_base in call_url
            assert "queryParameters.house=Commons" in call_url
            assert "queryParameters.startDate=2024-01-01" in call_url
            assert "queryParameters.endDate=2024-12-31" in call_url

    @pytest.mark.asyncio
    async def test_handles_lords_house(self):
        """get_non_sitting_days handles Lords house parameter."""
        with patch("uk_parliament_mcp.tools.whatson.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            whatson.register_tools(mcp)

            await mcp.call_tool(
                "get_non_sitting_days",
                {
                    "house": "Lords",
                    "start_date": "2024-06-01",
                    "end_date": "2024-08-31",
                },
            )

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert "queryParameters.house=Lords" in call_url


class TestGetCalendarCategories:
    """Tests for get_calendar_categories tool."""

    @pytest.mark.asyncio
    async def test_builds_correct_url(self):
        """get_calendar_categories builds correct URL."""
        with patch("uk_parliament_mcp.tools.whatson.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            whatson.register_tools(mcp)

            await mcp.call_tool("get_calendar_categories", {})

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert call_url == f"{WHATSON_API_BASE}/categories/list.json"


class TestGetEventTypeMetadata:
    """Tests for get_event_type_metadata tool."""

    @pytest.mark.asyncio
    async def test_builds_correct_url_no_params(self):
        """get_event_type_metadata builds correct URL with no params."""
        with patch("uk_parliament_mcp.tools.whatson.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            whatson.register_tools(mcp)

            await mcp.call_tool("get_event_type_metadata", {})

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert f"{WHATSON_API_BASE}/events/EventTypeMetaData.json" in call_url

    @pytest.mark.asyncio
    async def test_builds_correct_url_with_params(self):
        """get_event_type_metadata builds correct URL with params."""
        with patch("uk_parliament_mcp.tools.whatson.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            whatson.register_tools(mcp)

            await mcp.call_tool(
                "get_event_type_metadata",
                {"house": "Commons", "search_term": "debate"},
            )

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert "queryParameters.house=Commons" in call_url
            assert "queryParameters.searchTerm=debate" in call_url


class TestGetParliamentaryDiary:
    """Tests for get_parliamentary_diary tool."""

    @pytest.mark.asyncio
    async def test_builds_correct_url(self):
        """get_parliamentary_diary builds correct URL."""
        with patch("uk_parliament_mcp.tools.whatson.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            whatson.register_tools(mcp)

            await mcp.call_tool(
                "get_parliamentary_diary",
                {"house": "Commons", "start_date": "2024-01-01", "end_date": "2024-01-31"},
            )

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert f"{WHATSON_API_BASE}/events/diary.json" in call_url
            assert "queryParameters.house=Commons" in call_url
            assert "queryParameters.startDate=2024-01-01" in call_url
            assert "queryParameters.endDate=2024-01-31" in call_url


class TestGetSpeakerEvents:
    """Tests for get_speaker_events tool."""

    @pytest.mark.asyncio
    async def test_builds_correct_url(self):
        """get_speaker_events builds correct URL."""
        with patch("uk_parliament_mcp.tools.whatson.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            whatson.register_tools(mcp)

            await mcp.call_tool(
                "get_speaker_events",
                {"house": "Lords", "date": "2024-03-15"},
            )

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert f"{WHATSON_API_BASE}/events/speakers.json" in call_url
            assert "queryParameters.house=Lords" in call_url
            assert "queryParameters.date=2024-03-15" in call_url


class TestGetCalendarLocations:
    """Tests for get_calendar_locations tool."""

    @pytest.mark.asyncio
    async def test_builds_correct_url(self):
        """get_calendar_locations builds correct URL."""
        with patch("uk_parliament_mcp.tools.whatson.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            whatson.register_tools(mcp)

            await mcp.call_tool("get_calendar_locations", {})

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert call_url == f"{WHATSON_API_BASE}/locations/list.json"


class TestGetAnnulmentDate:
    """Tests for get_annulment_date tool."""

    @pytest.mark.asyncio
    async def test_builds_correct_url(self):
        """get_annulment_date builds correct URL with required params."""
        with patch("uk_parliament_mcp.tools.whatson.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            whatson.register_tools(mcp)

            await mcp.call_tool(
                "get_annulment_date",
                {"date_laid": "2024-01-01", "days_in_future": 40},
            )

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert f"{WHATSON_API_BASE}/proceduraldates/annulmentdate/forDate.json" in call_url
            assert "dateLaid=2024-01-01" in call_url
            assert "daysInFuture=40" in call_url

    @pytest.mark.asyncio
    async def test_builds_correct_url_with_is_treaty(self):
        """get_annulment_date includes isTreaty param when provided."""
        with patch("uk_parliament_mcp.tools.whatson.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            whatson.register_tools(mcp)

            await mcp.call_tool(
                "get_annulment_date",
                {"date_laid": "2024-01-01", "days_in_future": 21, "is_treaty": True},
            )

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert "isTreaty=true" in call_url


class TestGetLastSittingDate:
    """Tests for get_last_sitting_date tool."""

    @pytest.mark.asyncio
    async def test_builds_correct_url(self):
        """get_last_sitting_date builds correct URL."""
        with patch("uk_parliament_mcp.tools.whatson.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            whatson.register_tools(mcp)

            await mcp.call_tool(
                "get_last_sitting_date",
                {"house": "Commons", "date_to_check": "2024-08-01"},
            )

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert f"{WHATSON_API_BASE}/proceduraldates/Commons/lastsittingdate.json" in call_url
            assert "dateToCheck=2024-08-01" in call_url


class TestGetSessionById:
    """Tests for get_session_by_id tool."""

    @pytest.mark.asyncio
    async def test_builds_correct_url(self):
        """get_session_by_id builds correct URL with session ID."""
        with patch("uk_parliament_mcp.tools.whatson.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            whatson.register_tools(mcp)

            await mcp.call_tool("get_session_by_id", {"session_id": 42})

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert call_url == f"{WHATSON_API_BASE}/sessions/byid.json/42"


class TestGetSessionForDate:
    """Tests for get_session_for_date tool."""

    @pytest.mark.asyncio
    async def test_builds_correct_url(self):
        """get_session_for_date builds correct URL with date."""
        with patch("uk_parliament_mcp.tools.whatson.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            whatson.register_tools(mcp)

            await mcp.call_tool("get_session_for_date", {"date": "2024-06-15"})

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert call_url == f"{WHATSON_API_BASE}/sessions/fordate.json/2024-06-15"


class TestGetCalendarTags:
    """Tests for get_calendar_tags tool."""

    @pytest.mark.asyncio
    async def test_builds_correct_url(self):
        """get_calendar_tags builds correct URL."""
        with patch("uk_parliament_mcp.tools.whatson.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            whatson.register_tools(mcp)

            await mcp.call_tool("get_calendar_tags", {})

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert call_url == f"{WHATSON_API_BASE}/tags/list.json"


class TestGetCalendarTypes:
    """Tests for get_calendar_types tool."""

    @pytest.mark.asyncio
    async def test_builds_correct_url(self):
        """get_calendar_types builds correct URL."""
        with patch("uk_parliament_mcp.tools.whatson.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            whatson.register_tools(mcp)

            await mcp.call_tool("get_calendar_types", {})

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert call_url == f"{WHATSON_API_BASE}/types/list.json"
