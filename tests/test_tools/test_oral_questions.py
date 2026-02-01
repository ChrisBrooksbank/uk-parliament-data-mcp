"""Tests for oral_questions tools."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from mcp.server.fastmcp import FastMCP

from uk_parliament_mcp.config import ORAL_QUESTIONS_API_BASE
from uk_parliament_mcp.tools import oral_questions


class TestOralQuestionsToolsRegistration:
    """Tests for oral_questions tools registration."""

    @pytest.fixture
    def mcp(self):
        """Create a FastMCP instance with oral_questions tools registered."""
        server = FastMCP(name="test-server")
        oral_questions.register_tools(server)
        return server

    @pytest.mark.asyncio
    async def test_register_tools_adds_all_tools(self, mcp: FastMCP):
        """register_tools adds all oral_questions tools."""
        tools = await mcp.list_tools()
        tool_names = [t.name for t in tools]

        assert "get_recently_tabled_edms" in tool_names
        assert "search_early_day_motions" in tool_names
        assert "search_oral_question_times" in tool_names

    @pytest.mark.asyncio
    async def test_tools_have_descriptions(self, mcp: FastMCP):
        """All oral_questions tools have descriptions."""
        tools = await mcp.list_tools()
        oral_question_tools = [
            t
            for t in tools
            if t.name
            in [
                "get_recently_tabled_edms",
                "search_early_day_motions",
                "search_oral_question_times",
            ]
        ]

        for tool in oral_question_tools:
            assert tool.description is not None
            assert len(tool.description) > 0


class TestGetRecentlyTabledEdms:
    """Tests for get_recently_tabled_edms tool."""

    @pytest.mark.asyncio
    async def test_builds_correct_url_default_take(self):
        """get_recently_tabled_edms builds correct URL with default take parameter."""
        with patch(
            "uk_parliament_mcp.tools.oral_questions.get_result", new_callable=AsyncMock
        ) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            oral_questions.register_tools(mcp)

            await mcp.call_tool("get_recently_tabled_edms", {})

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert f"{ORAL_QUESTIONS_API_BASE}/EarlyDayMotions/list" in call_url
            assert "parameters.orderBy=DateTabledDesc" in call_url
            assert "skip=0" in call_url
            assert "take=10" in call_url

    @pytest.mark.asyncio
    async def test_builds_correct_url_custom_take(self):
        """get_recently_tabled_edms builds correct URL with custom take parameter."""
        with patch(
            "uk_parliament_mcp.tools.oral_questions.get_result", new_callable=AsyncMock
        ) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            oral_questions.register_tools(mcp)

            await mcp.call_tool("get_recently_tabled_edms", {"take": 25})

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert f"{ORAL_QUESTIONS_API_BASE}/EarlyDayMotions/list" in call_url
            assert "take=25" in call_url


class TestSearchEarlyDayMotions:
    """Tests for search_early_day_motions tool."""

    @pytest.mark.asyncio
    async def test_builds_correct_url(self):
        """search_early_day_motions builds correct URL."""
        with patch(
            "uk_parliament_mcp.tools.oral_questions.get_result", new_callable=AsyncMock
        ) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            oral_questions.register_tools(mcp)

            await mcp.call_tool(
                "search_early_day_motions", {"search_term": "climate change"}
            )

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert f"{ORAL_QUESTIONS_API_BASE}/EarlyDayMotions/list" in call_url
            assert "parameters.searchTerm=climate" in call_url
            assert "change" in call_url

    @pytest.mark.asyncio
    async def test_url_encodes_special_characters(self):
        """search_early_day_motions URL-encodes special characters."""
        with patch(
            "uk_parliament_mcp.tools.oral_questions.get_result", new_callable=AsyncMock
        ) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            oral_questions.register_tools(mcp)

            await mcp.call_tool(
                "search_early_day_motions", {"search_term": "NHS & care reforms"}
            )

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            # URL encoding: & -> %26, space -> %20 or +
            assert "%20" in call_url or "+" in call_url  # Space encoding
            assert "NHS" in call_url
            assert "care" in call_url
            assert "reforms" in call_url


class TestSearchOralQuestionTimes:
    """Tests for search_oral_question_times tool."""

    @pytest.mark.asyncio
    async def test_builds_correct_url(self):
        """search_oral_question_times builds correct URL."""
        with patch(
            "uk_parliament_mcp.tools.oral_questions.get_result", new_callable=AsyncMock
        ) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            oral_questions.register_tools(mcp)

            await mcp.call_tool(
                "search_oral_question_times",
                {"answering_date_start": "2024-01-01", "answering_date_end": "2024-01-31"},
            )

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert f"{ORAL_QUESTIONS_API_BASE}/oralquestiontimes/list" in call_url
            assert "parameters.answeringDateStart=2024-01-01" in call_url
            assert "parameters.answeringDateEnd=2024-01-31" in call_url

    @pytest.mark.asyncio
    async def test_url_encodes_date_parameters(self):
        """search_oral_question_times handles date parameters correctly."""
        with patch(
            "uk_parliament_mcp.tools.oral_questions.get_result", new_callable=AsyncMock
        ) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            oral_questions.register_tools(mcp)

            await mcp.call_tool(
                "search_oral_question_times",
                {"answering_date_start": "2024-06-01", "answering_date_end": "2024-06-30"},
            )

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert "parameters.answeringDateStart=2024-06-01" in call_url
            assert "parameters.answeringDateEnd=2024-06-30" in call_url
