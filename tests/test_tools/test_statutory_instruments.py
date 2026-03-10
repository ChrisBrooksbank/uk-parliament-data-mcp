"""Tests for statutory_instruments tools."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from mcp.server.fastmcp import FastMCP

from uk_parliament_mcp.config import STATUTORY_INSTRUMENTS_API_BASE
from uk_parliament_mcp.tools import statutory_instruments
from uk_parliament_mcp.tools.statutory_instruments import STATUTORY_INSTRUMENTS_API_BASE_V1


class TestStatutoryInstrumentsToolsRegistration:
    """Tests for statutory_instruments tools registration."""

    @pytest.fixture
    def mcp(self):
        """Create a FastMCP instance with statutory_instruments tools registered."""
        server = FastMCP(name="test-server")
        statutory_instruments.register_tools(server)
        return server

    @pytest.mark.asyncio
    async def test_register_tools_adds_statutory_instruments_tools(self, mcp: FastMCP):
        """register_tools adds all statutory instruments tools."""
        tools = await mcp.list_tools()
        tool_names = [t.name for t in tools]

        expected_tools = [
            "search_statutory_instruments",
            "search_acts_of_parliament",
            "get_statutory_instrument",
            "get_si_business_items",
            "get_act_of_parliament",
            "get_si_business_item",
            "get_laying_bodies",
            "get_si_procedures",
            "get_si_procedure",
            "search_proposed_negative_sis",
            "get_proposed_negative_si",
            "get_proposed_negative_si_business_items",
            "get_si_timeline_business_items",
        ]
        for tool_name in expected_tools:
            assert tool_name in tool_names

    @pytest.mark.asyncio
    async def test_search_statutory_instruments_has_description(self, mcp: FastMCP):
        """search_statutory_instruments tool has a description."""
        tools = await mcp.list_tools()
        tool = next(t for t in tools if t.name == "search_statutory_instruments")

        assert tool.description is not None
        assert len(tool.description) > 0

    @pytest.mark.asyncio
    async def test_search_acts_of_parliament_has_description(self, mcp: FastMCP):
        """search_acts_of_parliament tool has a description."""
        tools = await mcp.list_tools()
        tool = next(t for t in tools if t.name == "search_acts_of_parliament")

        assert tool.description is not None
        assert len(tool.description) > 0


class TestSearchStatutoryInstruments:
    """Tests for search_statutory_instruments tool."""

    @pytest.mark.asyncio
    async def test_builds_correct_url(self):
        """search_statutory_instruments builds correct URL with name parameter."""
        with patch(
            "uk_parliament_mcp.tools.statutory_instruments.get_result", new_callable=AsyncMock
        ) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            statutory_instruments.register_tools(mcp)

            await mcp.call_tool(
                "search_statutory_instruments",
                {"name": "Building Regulations"},
            )

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            expected_url = (
                f"{STATUTORY_INSTRUMENTS_API_BASE}/StatutoryInstrument?Name=Building%20Regulations"
            )
            assert call_url == expected_url

    @pytest.mark.asyncio
    async def test_handles_special_characters(self):
        """search_statutory_instruments properly URL-encodes special characters."""
        with patch(
            "uk_parliament_mcp.tools.statutory_instruments.get_result", new_callable=AsyncMock
        ) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            statutory_instruments.register_tools(mcp)

            await mcp.call_tool(
                "search_statutory_instruments",
                {"name": "Health & Safety Rules"},
            )

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert "Health%20%26%20Safety%20Rules" in call_url

    @pytest.mark.asyncio
    async def test_handles_single_quotes(self):
        """search_statutory_instruments handles single quotes in names."""
        with patch(
            "uk_parliament_mcp.tools.statutory_instruments.get_result", new_callable=AsyncMock
        ) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            statutory_instruments.register_tools(mcp)

            await mcp.call_tool(
                "search_statutory_instruments",
                {"name": "Queen's Regulations"},
            )

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert "Queen%27s%20Regulations" in call_url


class TestSearchActsOfParliament:
    """Tests for search_acts_of_parliament tool."""

    @pytest.mark.asyncio
    async def test_builds_correct_url(self):
        """search_acts_of_parliament builds correct URL with name parameter."""
        with patch(
            "uk_parliament_mcp.tools.statutory_instruments.get_result", new_callable=AsyncMock
        ) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            statutory_instruments.register_tools(mcp)

            await mcp.call_tool(
                "search_acts_of_parliament",
                {"name": "Human Rights Act"},
            )

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            expected_url = (
                f"{STATUTORY_INSTRUMENTS_API_BASE}/ActOfParliament?Name=Human%20Rights%20Act"
            )
            assert call_url == expected_url

    @pytest.mark.asyncio
    async def test_handles_special_characters(self):
        """search_acts_of_parliament properly URL-encodes special characters."""
        with patch(
            "uk_parliament_mcp.tools.statutory_instruments.get_result", new_callable=AsyncMock
        ) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            statutory_instruments.register_tools(mcp)

            await mcp.call_tool(
                "search_acts_of_parliament",
                {"name": "Climate Change & Environment Act"},
            )

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert "Climate%20Change%20%26%20Environment%20Act" in call_url

    @pytest.mark.asyncio
    async def test_handles_year_in_name(self):
        """search_acts_of_parliament handles act names with years."""
        with patch(
            "uk_parliament_mcp.tools.statutory_instruments.get_result", new_callable=AsyncMock
        ) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            statutory_instruments.register_tools(mcp)

            await mcp.call_tool(
                "search_acts_of_parliament",
                {"name": "Companies Act 2006"},
            )

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            expected_url = (
                f"{STATUTORY_INSTRUMENTS_API_BASE}/ActOfParliament?Name=Companies%20Act%202006"
            )
            assert call_url == expected_url


class TestGetSiBusinessItem:
    """Tests for get_si_business_item tool."""

    @pytest.mark.asyncio
    async def test_builds_correct_url(self):
        """get_si_business_item builds correct URL with item ID."""
        with patch(
            "uk_parliament_mcp.tools.statutory_instruments.get_result", new_callable=AsyncMock
        ) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            statutory_instruments.register_tools(mcp)

            await mcp.call_tool("get_si_business_item", {"item_id": "abc123"})

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert f"{STATUTORY_INSTRUMENTS_API_BASE_V1}/BusinessItem/abc123" in call_url

    @pytest.mark.asyncio
    async def test_includes_laid_paper_param(self):
        """get_si_business_item includes laidPaper query param when provided."""
        with patch(
            "uk_parliament_mcp.tools.statutory_instruments.get_result", new_callable=AsyncMock
        ) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            statutory_instruments.register_tools(mcp)

            await mcp.call_tool("get_si_business_item", {"item_id": "abc123", "laid_paper": True})

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert "laidPaper=true" in call_url


class TestGetLayingBodies:
    """Tests for get_laying_bodies tool."""

    @pytest.mark.asyncio
    async def test_builds_correct_url(self):
        """get_laying_bodies builds correct URL."""
        with patch(
            "uk_parliament_mcp.tools.statutory_instruments.get_result", new_callable=AsyncMock
        ) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            statutory_instruments.register_tools(mcp)

            await mcp.call_tool("get_laying_bodies", {})

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert call_url == f"{STATUTORY_INSTRUMENTS_API_BASE_V1}/LayingBody"


class TestGetSiProcedures:
    """Tests for get_si_procedures and get_si_procedure tools."""

    @pytest.mark.asyncio
    async def test_get_si_procedures_builds_correct_url(self):
        """get_si_procedures builds correct URL."""
        with patch(
            "uk_parliament_mcp.tools.statutory_instruments.get_result", new_callable=AsyncMock
        ) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            statutory_instruments.register_tools(mcp)

            await mcp.call_tool("get_si_procedures", {})

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert call_url == f"{STATUTORY_INSTRUMENTS_API_BASE_V1}/Procedure"

    @pytest.mark.asyncio
    async def test_get_si_procedure_builds_correct_url(self):
        """get_si_procedure builds correct URL with procedure ID."""
        with patch(
            "uk_parliament_mcp.tools.statutory_instruments.get_result", new_callable=AsyncMock
        ) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            statutory_instruments.register_tools(mcp)

            await mcp.call_tool("get_si_procedure", {"procedure_id": 3})

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert call_url == f"{STATUTORY_INSTRUMENTS_API_BASE_V1}/Procedure/3"


class TestSearchProposedNegativeSIs:
    """Tests for search_proposed_negative_sis tool."""

    @pytest.mark.asyncio
    async def test_builds_correct_url_no_params(self):
        """search_proposed_negative_sis builds correct URL with default params."""
        with patch(
            "uk_parliament_mcp.tools.statutory_instruments.get_result", new_callable=AsyncMock
        ) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            statutory_instruments.register_tools(mcp)

            await mcp.call_tool("search_proposed_negative_sis", {})

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert (
                f"{STATUTORY_INSTRUMENTS_API_BASE_V1}/ProposedNegativeStatutoryInstrument"
                in call_url
            )

    @pytest.mark.asyncio
    async def test_includes_name_filter(self):
        """search_proposed_negative_sis includes Name filter when provided."""
        with patch(
            "uk_parliament_mcp.tools.statutory_instruments.get_result", new_callable=AsyncMock
        ) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            statutory_instruments.register_tools(mcp)

            await mcp.call_tool("search_proposed_negative_sis", {"name": "Environment"})

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert "Name=Environment" in call_url


class TestGetProposedNegativeSI:
    """Tests for get_proposed_negative_si and get_proposed_negative_si_business_items tools."""

    @pytest.mark.asyncio
    async def test_get_proposed_negative_si_builds_correct_url(self):
        """get_proposed_negative_si builds correct URL."""
        with patch(
            "uk_parliament_mcp.tools.statutory_instruments.get_result", new_callable=AsyncMock
        ) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            statutory_instruments.register_tools(mcp)

            await mcp.call_tool("get_proposed_negative_si", {"pnsi_id": "pnsi-456"})

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert (
                f"{STATUTORY_INSTRUMENTS_API_BASE_V1}/ProposedNegativeStatutoryInstrument/pnsi-456"
                == call_url
            )

    @pytest.mark.asyncio
    async def test_get_proposed_negative_si_business_items_builds_correct_url(self):
        """get_proposed_negative_si_business_items builds correct URL."""
        with patch(
            "uk_parliament_mcp.tools.statutory_instruments.get_result", new_callable=AsyncMock
        ) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            statutory_instruments.register_tools(mcp)

            await mcp.call_tool(
                "get_proposed_negative_si_business_items", {"pnsi_id": "pnsi-456"}
            )

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert (
                f"{STATUTORY_INSTRUMENTS_API_BASE_V1}/ProposedNegativeStatutoryInstrument/pnsi-456/BusinessItems"
                == call_url
            )


class TestGetSiTimelineBusinessItems:
    """Tests for get_si_timeline_business_items tool."""

    @pytest.mark.asyncio
    async def test_builds_correct_url(self):
        """get_si_timeline_business_items builds correct URL."""
        with patch(
            "uk_parliament_mcp.tools.statutory_instruments.get_result", new_callable=AsyncMock
        ) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            statutory_instruments.register_tools(mcp)

            await mcp.call_tool("get_si_timeline_business_items", {"timeline_id": "tl-789"})

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert call_url == f"{STATUTORY_INSTRUMENTS_API_BASE}/Timeline/tl-789/BusinessItems"
