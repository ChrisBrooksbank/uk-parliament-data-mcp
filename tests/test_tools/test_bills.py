"""Tests for bills tools."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from mcp.server.fastmcp import FastMCP

from uk_parliament_mcp.config import BILLS_API_BASE
from uk_parliament_mcp.tools import bills


class TestBillsToolsRegistration:
    """Tests for bills tools registration."""

    @pytest.fixture
    def mcp(self):
        """Create a FastMCP instance with bills tools registered."""
        server = FastMCP(name="test-server")
        bills.register_tools(server)
        return server

    @pytest.mark.asyncio
    async def test_register_tools_adds_all_21_tools(self, mcp: FastMCP):
        """register_tools adds all 21 bill tools."""
        tools = await mcp.list_tools()
        tool_names = [t.name for t in tools]

        expected_tools = [
            "get_recently_updated_bills",
            "search_bills",
            "bill_types",
            "bill_stages",
            "get_bill_by_id",
            "get_bill_stages",
            "get_bill_stage_details",
            "get_bill_stage_amendments",
            "get_amendment_by_id",
            "get_bill_stage_ping_pong_items",
            "get_ping_pong_item_by_id",
            "get_bill_publications",
            "get_bill_stage_publications",
            "get_publication_document",
            "get_bill_news_articles",
            "get_all_bills_rss",
            "get_public_bills_rss",
            "get_private_bills_rss",
            "get_bill_rss",
            "get_publication_types",
            "get_sittings",
        ]

        for tool_name in expected_tools:
            assert tool_name in tool_names

    @pytest.mark.asyncio
    async def test_all_bills_tools_have_descriptions(self, mcp: FastMCP):
        """All bills tools have descriptions."""
        tools = await mcp.list_tools()
        for tool in tools:
            assert tool.description is not None
            assert len(tool.description) > 0


class TestGetRecentlyUpdatedBills:
    """Tests for get_recently_updated_bills tool."""

    @pytest.mark.asyncio
    async def test_builds_url_with_default_take(self):
        """get_recently_updated_bills builds URL with default take parameter."""
        with patch("uk_parliament_mcp.tools.bills.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            bills.register_tools(mcp)

            await mcp.call_tool("get_recently_updated_bills", {})

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert (
                call_url == f"{BILLS_API_BASE}/Bills?SortOrder=DateUpdatedDescending&skip=0&take=10"
            )

    @pytest.mark.asyncio
    async def test_builds_url_with_custom_take(self):
        """get_recently_updated_bills builds URL with custom take parameter."""
        with patch("uk_parliament_mcp.tools.bills.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            bills.register_tools(mcp)

            await mcp.call_tool("get_recently_updated_bills", {"take": 25})

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert "take=25" in call_url


class TestSearchBills:
    """Tests for search_bills tool."""

    @pytest.mark.asyncio
    async def test_builds_url_with_search_term(self):
        """search_bills builds URL with search term."""
        with patch("uk_parliament_mcp.tools.bills.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            bills.register_tools(mcp)

            await mcp.call_tool("search_bills", {"search_term": "environment"})

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert call_url == f"{BILLS_API_BASE}/Bills?SearchTerm=environment"

    @pytest.mark.asyncio
    async def test_url_encodes_special_characters(self):
        """search_bills URL-encodes special characters in search term."""
        with patch("uk_parliament_mcp.tools.bills.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            bills.register_tools(mcp)

            await mcp.call_tool("search_bills", {"search_term": "online safety & privacy"})

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert "online%20safety%20%26%20privacy" in call_url


class TestBillTypes:
    """Tests for bill_types tool."""

    @pytest.mark.asyncio
    async def test_builds_correct_url(self):
        """bill_types builds correct URL."""
        with patch("uk_parliament_mcp.tools.bills.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            bills.register_tools(mcp)

            await mcp.call_tool("bill_types", {})

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert call_url == f"{BILLS_API_BASE}/BillTypes"


class TestBillStages:
    """Tests for bill_stages tool."""

    @pytest.mark.asyncio
    async def test_builds_correct_url(self):
        """bill_stages builds correct URL."""
        with patch("uk_parliament_mcp.tools.bills.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            bills.register_tools(mcp)

            await mcp.call_tool("bill_stages", {})

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert call_url == f"{BILLS_API_BASE}/Stages"


class TestGetBillById:
    """Tests for get_bill_by_id tool."""

    @pytest.mark.asyncio
    async def test_builds_correct_url(self):
        """get_bill_by_id builds correct URL."""
        with patch("uk_parliament_mcp.tools.bills.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            bills.register_tools(mcp)

            await mcp.call_tool("get_bill_by_id", {"bill_id": 12345})

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert call_url == f"{BILLS_API_BASE}/Bills/12345"


class TestGetBillStages:
    """Tests for get_bill_stages tool."""

    @pytest.mark.asyncio
    async def test_builds_url_without_pagination(self):
        """get_bill_stages builds URL without pagination params."""
        with patch("uk_parliament_mcp.tools.bills.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            bills.register_tools(mcp)

            await mcp.call_tool("get_bill_stages", {"bill_id": 12345})

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert call_url == f"{BILLS_API_BASE}/Bills/12345/Stages"

    @pytest.mark.asyncio
    async def test_builds_url_with_pagination(self):
        """get_bill_stages builds URL with skip and take params."""
        with patch("uk_parliament_mcp.tools.bills.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            bills.register_tools(mcp)

            await mcp.call_tool("get_bill_stages", {"bill_id": 12345, "skip": 10, "take": 20})

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert "Skip=10" in call_url
            assert "Take=20" in call_url


class TestGetBillStageDetails:
    """Tests for get_bill_stage_details tool."""

    @pytest.mark.asyncio
    async def test_builds_correct_url(self):
        """get_bill_stage_details builds correct URL."""
        with patch("uk_parliament_mcp.tools.bills.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            bills.register_tools(mcp)

            await mcp.call_tool(
                "get_bill_stage_details", {"bill_id": 12345, "bill_stage_id": 67890}
            )

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert call_url == f"{BILLS_API_BASE}/Bills/12345/Stages/67890"


class TestGetBillStageAmendments:
    """Tests for get_bill_stage_amendments tool."""

    @pytest.mark.asyncio
    async def test_builds_url_without_filters(self):
        """get_bill_stage_amendments builds URL without optional filters."""
        with patch("uk_parliament_mcp.tools.bills.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            bills.register_tools(mcp)

            await mcp.call_tool(
                "get_bill_stage_amendments", {"bill_id": 12345, "bill_stage_id": 67890}
            )

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert call_url == f"{BILLS_API_BASE}/Bills/12345/Stages/67890/Amendments"

    @pytest.mark.asyncio
    async def test_builds_url_with_filters(self):
        """get_bill_stage_amendments builds URL with all filter params."""
        with patch("uk_parliament_mcp.tools.bills.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            bills.register_tools(mcp)

            await mcp.call_tool(
                "get_bill_stage_amendments",
                {
                    "bill_id": 12345,
                    "bill_stage_id": 67890,
                    "search_term": "clause",
                    "amendment_number": "1",
                    "decision": "Agreed",
                    "member_id": 4514,
                    "skip": 5,
                    "take": 15,
                },
            )

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert "SearchTerm=clause" in call_url
            assert "AmendmentNumber=1" in call_url
            assert "Decision=Agreed" in call_url
            assert "MemberId=4514" in call_url
            assert "Skip=5" in call_url
            assert "Take=15" in call_url


class TestGetAmendmentById:
    """Tests for get_amendment_by_id tool."""

    @pytest.mark.asyncio
    async def test_builds_correct_url(self):
        """get_amendment_by_id builds correct URL."""
        with patch("uk_parliament_mcp.tools.bills.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            bills.register_tools(mcp)

            await mcp.call_tool(
                "get_amendment_by_id",
                {"bill_id": 12345, "bill_stage_id": 67890, "amendment_id": 11111},
            )

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert call_url == f"{BILLS_API_BASE}/Bills/12345/Stages/67890/Amendments/11111"


class TestGetBillStagePingPongItems:
    """Tests for get_bill_stage_ping_pong_items tool."""

    @pytest.mark.asyncio
    async def test_builds_url_without_filters(self):
        """get_bill_stage_ping_pong_items builds URL without optional filters."""
        with patch("uk_parliament_mcp.tools.bills.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            bills.register_tools(mcp)

            await mcp.call_tool(
                "get_bill_stage_ping_pong_items", {"bill_id": 12345, "bill_stage_id": 67890}
            )

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert call_url == f"{BILLS_API_BASE}/Bills/12345/Stages/67890/PingPongItems"

    @pytest.mark.asyncio
    async def test_builds_url_with_filters(self):
        """get_bill_stage_ping_pong_items builds URL with all filter params."""
        with patch("uk_parliament_mcp.tools.bills.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            bills.register_tools(mcp)

            await mcp.call_tool(
                "get_bill_stage_ping_pong_items",
                {
                    "bill_id": 12345,
                    "bill_stage_id": 67890,
                    "search_term": "motion",
                    "amendment_number": "2",
                    "decision": "Withdrawn",
                    "member_id": 1423,
                    "skip": 0,
                    "take": 10,
                },
            )

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert "SearchTerm=motion" in call_url
            assert "AmendmentNumber=2" in call_url
            assert "Decision=Withdrawn" in call_url
            assert "MemberId=1423" in call_url
            assert "Skip=0" in call_url
            assert "Take=10" in call_url


class TestGetPingPongItemById:
    """Tests for get_ping_pong_item_by_id tool."""

    @pytest.mark.asyncio
    async def test_builds_correct_url(self):
        """get_ping_pong_item_by_id builds correct URL."""
        with patch("uk_parliament_mcp.tools.bills.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            bills.register_tools(mcp)

            await mcp.call_tool(
                "get_ping_pong_item_by_id",
                {"bill_id": 12345, "bill_stage_id": 67890, "ping_pong_item_id": 22222},
            )

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert call_url == f"{BILLS_API_BASE}/Bills/12345/Stages/67890/PingPongItems/22222"


class TestGetBillPublications:
    """Tests for get_bill_publications tool."""

    @pytest.mark.asyncio
    async def test_builds_correct_url(self):
        """get_bill_publications builds correct URL."""
        with patch("uk_parliament_mcp.tools.bills.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            bills.register_tools(mcp)

            await mcp.call_tool("get_bill_publications", {"bill_id": 12345})

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert call_url == f"{BILLS_API_BASE}/Bills/12345/Publications"


class TestGetBillStagePublications:
    """Tests for get_bill_stage_publications tool."""

    @pytest.mark.asyncio
    async def test_builds_correct_url(self):
        """get_bill_stage_publications builds correct URL."""
        with patch("uk_parliament_mcp.tools.bills.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            bills.register_tools(mcp)

            await mcp.call_tool(
                "get_bill_stage_publications", {"bill_id": 12345, "stage_id": 67890}
            )

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert call_url == f"{BILLS_API_BASE}/Bills/12345/Stages/67890/Publications"


class TestGetPublicationDocument:
    """Tests for get_publication_document tool."""

    @pytest.mark.asyncio
    async def test_builds_correct_url(self):
        """get_publication_document builds correct URL."""
        with patch("uk_parliament_mcp.tools.bills.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            bills.register_tools(mcp)

            await mcp.call_tool(
                "get_publication_document", {"publication_id": 33333, "document_id": 44444}
            )

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert call_url == f"{BILLS_API_BASE}/Publications/33333/Documents/44444"


class TestGetBillNewsArticles:
    """Tests for get_bill_news_articles tool."""

    @pytest.mark.asyncio
    async def test_builds_url_without_pagination(self):
        """get_bill_news_articles builds URL without pagination params."""
        with patch("uk_parliament_mcp.tools.bills.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            bills.register_tools(mcp)

            await mcp.call_tool("get_bill_news_articles", {"bill_id": 12345})

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert call_url == f"{BILLS_API_BASE}/Bills/12345/NewsArticles"

    @pytest.mark.asyncio
    async def test_builds_url_with_pagination(self):
        """get_bill_news_articles builds URL with skip and take params."""
        with patch("uk_parliament_mcp.tools.bills.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            bills.register_tools(mcp)

            await mcp.call_tool("get_bill_news_articles", {"bill_id": 12345, "skip": 5, "take": 25})

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert "Skip=5" in call_url
            assert "Take=25" in call_url


class TestGetAllBillsRss:
    """Tests for get_all_bills_rss tool."""

    @pytest.mark.asyncio
    async def test_builds_correct_url(self):
        """get_all_bills_rss builds correct RSS feed URL."""
        with patch("uk_parliament_mcp.tools.bills.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            bills.register_tools(mcp)

            await mcp.call_tool("get_all_bills_rss", {})

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert call_url == f"{BILLS_API_BASE}/Rss/allbills.rss"


class TestGetPublicBillsRss:
    """Tests for get_public_bills_rss tool."""

    @pytest.mark.asyncio
    async def test_builds_correct_url(self):
        """get_public_bills_rss builds correct RSS feed URL."""
        with patch("uk_parliament_mcp.tools.bills.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            bills.register_tools(mcp)

            await mcp.call_tool("get_public_bills_rss", {})

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert call_url == f"{BILLS_API_BASE}/Rss/publicbills.rss"


class TestGetPrivateBillsRss:
    """Tests for get_private_bills_rss tool."""

    @pytest.mark.asyncio
    async def test_builds_correct_url(self):
        """get_private_bills_rss builds correct RSS feed URL."""
        with patch("uk_parliament_mcp.tools.bills.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            bills.register_tools(mcp)

            await mcp.call_tool("get_private_bills_rss", {})

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert call_url == f"{BILLS_API_BASE}/Rss/privatebills.rss"


class TestGetBillRss:
    """Tests for get_bill_rss tool."""

    @pytest.mark.asyncio
    async def test_builds_correct_url(self):
        """get_bill_rss builds correct RSS feed URL for specific bill."""
        with patch("uk_parliament_mcp.tools.bills.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            bills.register_tools(mcp)

            await mcp.call_tool("get_bill_rss", {"bill_id": 12345})

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert call_url == f"{BILLS_API_BASE}/Rss/Bills/12345.rss"


class TestGetPublicationTypes:
    """Tests for get_publication_types tool."""

    @pytest.mark.asyncio
    async def test_builds_url_without_pagination(self):
        """get_publication_types builds URL without pagination params."""
        with patch("uk_parliament_mcp.tools.bills.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            bills.register_tools(mcp)

            await mcp.call_tool("get_publication_types", {})

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert call_url == f"{BILLS_API_BASE}/PublicationTypes"

    @pytest.mark.asyncio
    async def test_builds_url_with_pagination(self):
        """get_publication_types builds URL with skip and take params."""
        with patch("uk_parliament_mcp.tools.bills.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            bills.register_tools(mcp)

            await mcp.call_tool("get_publication_types", {"skip": 10, "take": 30})

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert "Skip=10" in call_url
            assert "Take=30" in call_url


class TestGetSittings:
    """Tests for get_sittings tool."""

    @pytest.mark.asyncio
    async def test_builds_url_without_filters(self):
        """get_sittings builds URL without optional filters."""
        with patch("uk_parliament_mcp.tools.bills.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            bills.register_tools(mcp)

            await mcp.call_tool("get_sittings", {})

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert call_url == f"{BILLS_API_BASE}/Sittings"

    @pytest.mark.asyncio
    async def test_builds_url_with_all_filters(self):
        """get_sittings builds URL with all filter params."""
        with patch("uk_parliament_mcp.tools.bills.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            bills.register_tools(mcp)

            await mcp.call_tool(
                "get_sittings",
                {
                    "house": "Commons",
                    "date_from": "2024-01-01",
                    "date_to": "2024-12-31",
                    "skip": 0,
                    "take": 100,
                },
            )

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert "House=Commons" in call_url
            assert "DateFrom=2024-01-01" in call_url
            assert "DateTo=2024-12-31" in call_url
            assert "Skip=0" in call_url
            assert "Take=100" in call_url
