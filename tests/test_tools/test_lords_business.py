"""Tests for lords_business tools."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch
from urllib.parse import parse_qs, urlsplit

import pytest
from mcp.server.fastmcp import FastMCP

from uk_parliament_mcp.config import LORDS_BUSINESS_API_BASE
from uk_parliament_mcp.tools import lords_business

EXPECTED_TOOLS = {
    "get_lords_business_sections",
    "get_lords_business_sections_for_date",
    "get_lords_business_section_data",
    "get_lords_item_of_business_summary",
    "get_lords_business_documents_for_date",
    "get_lords_business_document",
    "check_lords_divisions_exist",
    "get_lords_non_sitting_days",
    "get_lords_next_prev_business_days",
    "get_lords_journal_volumes",
    "get_lords_journal_volume",
    "get_lords_journal_general_index",
    "get_lords_journal_membership_index",
    "get_lords_journal_index_items",
    "get_lords_journal_content_dates",
    "get_lords_journal_sittings",
    "get_lords_journal_attachment",
    "get_lords_legacy_business",
    "search_lords_written_questions",
    "get_lords_written_question",
}


async def _call(tool: str, arguments: dict, target: str = "get_result") -> str:
    with patch(f"uk_parliament_mcp.tools.lords_business.{target}", new_callable=AsyncMock) as mock:
        mock.return_value = '{"url": "test", "data": "{}"}'

        mcp = FastMCP(name="test")
        lords_business.register_tools(mcp)
        await mcp.call_tool(tool, arguments)

        mock.assert_called_once()
        return mock.call_args[0][0]


def _query(url: str) -> dict[str, list[str]]:
    return parse_qs(urlsplit(url).query)


class TestLordsBusinessToolsRegistration:
    """Tests for lords_business tools registration."""

    @pytest.mark.asyncio
    async def test_registers_every_tool(self):
        """register_tools adds exactly the expected tools, each with a description."""
        mcp = FastMCP(name="test-server")
        lords_business.register_tools(mcp)
        tools = await mcp.list_tools()

        assert {t.name for t in tools} == EXPECTED_TOOLS
        assert all(t.description for t in tools)


class TestBusinessPapers:
    """Tests for business paper section and document tools."""

    @pytest.mark.asyncio
    async def test_sections_is_cached_reference_data(self):
        url = await _call("get_lords_business_sections", {}, target="get_result_cached")
        assert url == f"{LORDS_BUSINESS_API_BASE}/GetSections.json"

    @pytest.mark.asyncio
    async def test_sections_for_date(self):
        url = await _call(
            "get_lords_business_sections_for_date", {"business_paper_date": "2025-01-15"}
        )
        assert url.startswith(f"{LORDS_BUSINESS_API_BASE}/GetSectionsForDate.json?")
        assert _query(url) == {"businessPaperDate": ["2025-01-15"]}

    @pytest.mark.asyncio
    async def test_section_data(self):
        url = await _call(
            "get_lords_business_section_data",
            {"business_paper_date": "2025-01-15", "section_id": 40},
        )
        assert url.startswith(f"{LORDS_BUSINESS_API_BASE}/GetData.json?")
        assert _query(url) == {"BusinessPaperDate": ["2025-01-15"], "SectionId": ["40"]}

    @pytest.mark.asyncio
    async def test_item_of_business_summary(self):
        url = await _call(
            "get_lords_item_of_business_summary",
            {"item_of_business_id": 7, "business_paper_date": "2025-01-15"},
        )
        assert url.startswith(f"{LORDS_BUSINESS_API_BASE}/ItemOfBusinessSummary.json?")
        assert _query(url) == {"itemOfBusinessId": ["7"], "businessPaperDate": ["2025-01-15"]}

    @pytest.mark.asyncio
    async def test_documents_for_date(self):
        url = await _call("get_lords_business_documents_for_date", {"day_date": "2025-01-15"})
        assert url == f"{LORDS_BUSINESS_API_BASE}/Day/DocumentForDay.json/2025-01-15"

    @pytest.mark.asyncio
    async def test_document(self):
        url = await _call("get_lords_business_document", {"document_day_id": 5947})
        assert url == f"{LORDS_BUSINESS_API_BASE}/DocumentForDay/5947"


class TestSittingDays:
    """Tests for sitting-day tools."""

    @pytest.mark.asyncio
    async def test_divisions_exist(self):
        url = await _call("check_lords_divisions_exist", {"date": "2025-01-15"})
        assert url.startswith(f"{LORDS_BUSINESS_API_BASE}/DivisionsExistForDate.json?")
        assert _query(url) == {"date": ["2025-01-15"]}

    @pytest.mark.asyncio
    async def test_non_sitting_days_default_source(self):
        url = await _call("get_lords_non_sitting_days", {"month": 1, "year": 2025})
        assert url == f"{LORDS_BUSINESS_API_BASE}/NonSittingDays.json/1/2025"

    @pytest.mark.asyncio
    async def test_non_sitting_days_with_source(self):
        url = await _call(
            "get_lords_non_sitting_days",
            {"month": 12, "year": 2024, "data_source": "PublishedBusiness"},
        )
        assert url.startswith(f"{LORDS_BUSINESS_API_BASE}/NonSittingDays.json/12/2024?")
        assert _query(url) == {"dataSource": ["PublishedBusiness"]}

    @pytest.mark.asyncio
    async def test_next_prev_business_days(self):
        url = await _call("get_lords_next_prev_business_days", {"initial_date": "2025-01-15"})
        assert url.startswith(f"{LORDS_BUSINESS_API_BASE}/GetNextPrevDaysWithItemsOfBusiness.json?")
        assert _query(url) == {"initialDate": ["2025-01-15"]}


class TestJournal:
    """Tests for Lords Journal tools."""

    @pytest.mark.asyncio
    async def test_volumes_paging(self):
        url = await _call("get_lords_journal_volumes", {"skip": 5, "take": 10})
        assert url.startswith(f"{LORDS_BUSINESS_API_BASE}/journal-volumes?")
        assert _query(url) == {"Skip": ["5"], "Take": ["10"]}

    @pytest.mark.asyncio
    async def test_volumes_without_paging(self):
        url = await _call("get_lords_journal_volumes", {})
        assert url == f"{LORDS_BUSINESS_API_BASE}/journal-volumes"

    @pytest.mark.asyncio
    async def test_volume(self):
        url = await _call("get_lords_journal_volume", {"volume_id": 30})
        assert url == f"{LORDS_BUSINESS_API_BASE}/journal-volumes/30"

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ("tool", "segment"),
        [
            ("get_lords_journal_general_index", "general-index"),
            ("get_lords_journal_membership_index", "membership-index"),
        ],
    )
    async def test_indexes(self, tool: str, segment: str):
        url = await _call(tool, {"volume_id": 30, "starting_with": "A"})
        assert url.startswith(f"{LORDS_BUSINESS_API_BASE}/journal-volumes/30/{segment}?")
        assert _query(url) == {"StartingWith": ["A"]}

    @pytest.mark.asyncio
    async def test_index_item(self):
        url = await _call(
            "get_lords_journal_index_items",
            {"index_item_guid": "abc-123", "journal_volume_id": 30},
        )
        assert url.startswith(f"{LORDS_BUSINESS_API_BASE}/index-items/abc-123?")
        assert _query(url) == {"journalVolumeId": ["30"]}

    @pytest.mark.asyncio
    async def test_content_dates(self):
        url = await _call(
            "get_lords_journal_content_dates",
            {"start_date": "2020-01-01", "end_date": "2020-12-31"},
        )
        assert url.startswith(f"{LORDS_BUSINESS_API_BASE}/sittings/journalContentDates?")
        assert _query(url) == {"startDate": ["2020-01-01"], "endDate": ["2020-12-31"]}

    @pytest.mark.asyncio
    async def test_sittings(self):
        url = await _call(
            "get_lords_journal_sittings",
            {"sitting_date": "2020-01-15", "content_type": "MinutesOfProceedings"},
        )
        assert url == f"{LORDS_BUSINESS_API_BASE}/sittings/2020-01-15/MinutesOfProceedings"

    @pytest.mark.asyncio
    async def test_attachment(self):
        url = await _call("get_lords_journal_attachment", {"attachment_id": 9})
        assert url == f"{LORDS_BUSINESS_API_BASE}/journal-attachments/9"

    @pytest.mark.asyncio
    async def test_legacy_business(self):
        url = await _call("get_lords_legacy_business", {"day_date": "2020-01-15"})
        assert url == f"{LORDS_BUSINESS_API_BASE}/legacybusiness/2020-01-15"


class TestLordsWrittenQuestions:
    """Tests for Lords written question tools."""

    @pytest.mark.asyncio
    async def test_search_maps_all_parameters(self):
        url = await _call(
            "search_lords_written_questions",
            {
                "member_id": 4689,
                "uin": "4578",
                "status": "Answered",
                "tabled_start_date": "2025-01-01",
                "tabled_end_date": "2025-01-31",
                "order_by": "DateTabledDesc",
                "skip": 0,
                "take": 5,
            },
        )
        assert url.startswith(f"{LORDS_BUSINESS_API_BASE}/WrittenQuestions/list.json?")
        assert _query(url) == {
            "MemberId": ["4689"],
            "Uin": ["4578"],
            "Statuses": ["Answered"],
            "TabledStartDate": ["2025-01-01"],
            "TabledEndDate": ["2025-01-31"],
            "OrderBy": ["DateTabledDesc"],
            "Skip": ["0"],
            "Take": ["5"],
        }

    @pytest.mark.asyncio
    async def test_get_question(self):
        url = await _call("get_lords_written_question", {"question_id": 150323})
        assert url == f"{LORDS_BUSINESS_API_BASE}/WrittenQuestions/150323.json"
