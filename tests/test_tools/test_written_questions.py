"""Tests for written questions tools."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from mcp.server.fastmcp import FastMCP

from uk_parliament_mcp.config import WRITTEN_QUESTIONS_API_BASE
from uk_parliament_mcp.tools import written_questions


class TestWrittenQuestionsToolsRegistration:
    """Tests for written questions tools registration."""

    @pytest.fixture
    def mcp(self):
        """Create a FastMCP instance with written questions tools registered."""
        server = FastMCP(name="test-server")
        written_questions.register_tools(server)
        return server

    @pytest.mark.asyncio
    async def test_register_tools_adds_all_written_questions_tools(self, mcp: FastMCP):
        """register_tools adds all 7 written questions tools."""
        tools = await mcp.list_tools()
        tool_names = [t.name for t in tools]

        assert "search_written_questions" in tool_names
        assert "get_written_question" in tool_names
        assert "get_written_question_by_uin" in tool_names
        assert "search_written_statements" in tool_names
        assert "get_written_statement" in tool_names
        assert "get_written_statement_by_uin" in tool_names
        assert "get_daily_reports" in tool_names

    @pytest.mark.asyncio
    async def test_tools_have_descriptions(self, mcp: FastMCP):
        """All written questions tools have descriptions."""
        tools = await mcp.list_tools()
        tool_names = [
            "search_written_questions",
            "get_written_question",
            "get_written_question_by_uin",
            "search_written_statements",
            "get_written_statement",
            "get_written_statement_by_uin",
            "get_daily_reports",
        ]
        wq_tools = [t for t in tools if t.name in tool_names]

        for tool in wq_tools:
            assert tool.description is not None
            assert len(tool.description) > 0


class TestSearchWrittenQuestions:
    """Tests for search_written_questions tool."""

    @pytest.mark.asyncio
    async def test_builds_correct_url_with_search_term(self):
        """search_written_questions builds correct URL with search term."""
        with patch(
            "uk_parliament_mcp.tools.written_questions.get_result", new_callable=AsyncMock
        ) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            written_questions.register_tools(mcp)

            await mcp.call_tool(
                "search_written_questions",
                {"search_term": "climate"},
            )

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert f"{WRITTEN_QUESTIONS_API_BASE}/writtenquestions/questions" in call_url
            assert "searchTerm=climate" in call_url

    @pytest.mark.asyncio
    async def test_builds_correct_url_with_all_parameters(self):
        """search_written_questions builds correct URL with all parameters."""
        with patch(
            "uk_parliament_mcp.tools.written_questions.get_result", new_callable=AsyncMock
        ) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            written_questions.register_tools(mcp)

            await mcp.call_tool(
                "search_written_questions",
                {
                    "search_term": "NHS",
                    "asking_member_id": 123,
                    "answering_body_id": 456,
                    "answered": "Answered",
                    "tabled_from": "2024-01-01",
                    "tabled_to": "2024-12-31",
                    "house": "Commons",
                    "skip": 10,
                    "take": 50,
                },
            )

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert "searchTerm=NHS" in call_url
            assert "askingMemberId=123" in call_url
            assert "answeringBodyId=456" in call_url
            assert "answered=Answered" in call_url
            assert "tabledWhenFrom=2024-01-01" in call_url
            assert "tabledWhenTo=2024-12-31" in call_url
            assert "house=Commons" in call_url
            assert "skip=10" in call_url
            assert "take=50" in call_url

    @pytest.mark.asyncio
    async def test_default_pagination(self):
        """search_written_questions uses default pagination values."""
        with patch(
            "uk_parliament_mcp.tools.written_questions.get_result", new_callable=AsyncMock
        ) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            written_questions.register_tools(mcp)

            await mcp.call_tool("search_written_questions", {})

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert "skip=0" in call_url
            assert "take=20" in call_url


class TestGetWrittenQuestion:
    """Tests for get_written_question tool."""

    @pytest.mark.asyncio
    async def test_builds_correct_url(self):
        """get_written_question builds correct URL with question_id."""
        with patch(
            "uk_parliament_mcp.tools.written_questions.get_result", new_callable=AsyncMock
        ) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            written_questions.register_tools(mcp)

            await mcp.call_tool(
                "get_written_question",
                {"question_id": 12345},
            )

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert f"{WRITTEN_QUESTIONS_API_BASE}/writtenquestions/questions/12345" in call_url
            assert "expandMember=true" in call_url

    @pytest.mark.asyncio
    async def test_expand_member_false(self):
        """get_written_question respects expand_member=False."""
        with patch(
            "uk_parliament_mcp.tools.written_questions.get_result", new_callable=AsyncMock
        ) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            written_questions.register_tools(mcp)

            await mcp.call_tool(
                "get_written_question",
                {"question_id": 12345, "expand_member": False},
            )

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert "expandMember=false" in call_url


class TestGetWrittenQuestionByUin:
    """Tests for get_written_question_by_uin tool."""

    @pytest.mark.asyncio
    async def test_builds_correct_url(self):
        """get_written_question_by_uin builds correct URL."""
        with patch(
            "uk_parliament_mcp.tools.written_questions.get_result", new_callable=AsyncMock
        ) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            written_questions.register_tools(mcp)

            await mcp.call_tool(
                "get_written_question_by_uin",
                {"date": "2024-03-15", "uin": "HL12345"},
            )

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert (
                f"{WRITTEN_QUESTIONS_API_BASE}/writtenquestions/questions/2024-03-15/HL12345"
                in call_url
            )
            assert "expandMember=true" in call_url


class TestSearchWrittenStatements:
    """Tests for search_written_statements tool."""

    @pytest.mark.asyncio
    async def test_builds_correct_url_with_search_term(self):
        """search_written_statements builds correct URL with search term."""
        with patch(
            "uk_parliament_mcp.tools.written_questions.get_result", new_callable=AsyncMock
        ) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            written_questions.register_tools(mcp)

            await mcp.call_tool(
                "search_written_statements",
                {"search_term": "budget"},
            )

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert f"{WRITTEN_QUESTIONS_API_BASE}/writtenstatements/statements" in call_url
            assert "searchTerm=budget" in call_url

    @pytest.mark.asyncio
    async def test_builds_correct_url_with_all_parameters(self):
        """search_written_statements builds correct URL with all parameters."""
        with patch(
            "uk_parliament_mcp.tools.written_questions.get_result", new_callable=AsyncMock
        ) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            written_questions.register_tools(mcp)

            await mcp.call_tool(
                "search_written_statements",
                {
                    "search_term": "economy",
                    "member_id": 789,
                    "answering_body_id": 456,
                    "made_from": "2024-01-01",
                    "made_to": "2024-12-31",
                    "house": "Lords",
                    "skip": 5,
                    "take": 25,
                },
            )

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert "searchTerm=economy" in call_url
            assert "memberId=789" in call_url
            assert "answeringBodyId=456" in call_url
            assert "madeWhenFrom=2024-01-01" in call_url
            assert "madeWhenTo=2024-12-31" in call_url
            assert "house=Lords" in call_url
            assert "skip=5" in call_url
            assert "take=25" in call_url


class TestGetWrittenStatement:
    """Tests for get_written_statement tool."""

    @pytest.mark.asyncio
    async def test_builds_correct_url(self):
        """get_written_statement builds correct URL with statement_id."""
        with patch(
            "uk_parliament_mcp.tools.written_questions.get_result", new_callable=AsyncMock
        ) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            written_questions.register_tools(mcp)

            await mcp.call_tool(
                "get_written_statement",
                {"statement_id": 67890},
            )

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert f"{WRITTEN_QUESTIONS_API_BASE}/writtenstatements/statements/67890" in call_url
            assert "expandMember=true" in call_url


class TestGetWrittenStatementByUin:
    """Tests for get_written_statement_by_uin tool."""

    @pytest.mark.asyncio
    async def test_builds_correct_url(self):
        """get_written_statement_by_uin builds correct URL."""
        with patch(
            "uk_parliament_mcp.tools.written_questions.get_result", new_callable=AsyncMock
        ) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            written_questions.register_tools(mcp)

            await mcp.call_tool(
                "get_written_statement_by_uin",
                {"date": "2024-06-20", "uin": "HCWS123"},
            )

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert (
                f"{WRITTEN_QUESTIONS_API_BASE}/writtenstatements/statements/2024-06-20/HCWS123"
                in call_url
            )
            assert "expandMember=true" in call_url


class TestGetDailyReports:
    """Tests for get_daily_reports tool."""

    @pytest.mark.asyncio
    async def test_builds_correct_url_with_dates(self):
        """get_daily_reports builds correct URL with date range."""
        with patch(
            "uk_parliament_mcp.tools.written_questions.get_result", new_callable=AsyncMock
        ) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            written_questions.register_tools(mcp)

            await mcp.call_tool(
                "get_daily_reports",
                {"date_from": "2024-01-01", "date_to": "2024-01-31"},
            )

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert f"{WRITTEN_QUESTIONS_API_BASE}/dailyreports/dailyreports" in call_url
            assert "dateFrom=2024-01-01" in call_url
            assert "dateTo=2024-01-31" in call_url

    @pytest.mark.asyncio
    async def test_builds_correct_url_with_house_filter(self):
        """get_daily_reports builds correct URL with house filter."""
        with patch(
            "uk_parliament_mcp.tools.written_questions.get_result", new_callable=AsyncMock
        ) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            written_questions.register_tools(mcp)

            await mcp.call_tool(
                "get_daily_reports",
                {"house": "Bicameral"},
            )

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert "house=Bicameral" in call_url

    @pytest.mark.asyncio
    async def test_default_pagination(self):
        """get_daily_reports uses default pagination values."""
        with patch(
            "uk_parliament_mcp.tools.written_questions.get_result", new_callable=AsyncMock
        ) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            written_questions.register_tools(mcp)

            await mcp.call_tool("get_daily_reports", {})

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert "skip=0" in call_url
            assert "take=20" in call_url
