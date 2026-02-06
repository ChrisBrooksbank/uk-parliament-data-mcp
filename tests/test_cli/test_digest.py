"""Tests for parliament digest command."""

from __future__ import annotations

import json
from datetime import date
from unittest.mock import AsyncMock, patch

import pytest
from rich.panel import Panel

from uk_parliament_mcp.cli.digest import (
    _calculate_dates,
    _fetch_bills,
    _fetch_committees,
    _fetch_commons_votes,
    _fetch_digest_data,
    _fetch_edms,
    _fetch_hansard,
    _fetch_lords_votes,
    _fetch_oral_qs,
    _fetch_statements,
    _fetch_written_qs,
    _get_digest_async,
    _today,
    _week_range,
)
from uk_parliament_mcp.cli.renderers import (
    _render_bills_section,
    _render_committees_section,
    _render_digest_header,
    _render_divisions_section,
    _render_edms_section,
    _render_hansard_section,
    _render_oral_qs_section,
    _render_statements_section,
    _render_written_qs_section,
    _section_has_data,
    render_digest,
)

# ---------------------------------------------------------------------------
# Test data factories
# ---------------------------------------------------------------------------


def _mock_api_response(data: dict | list) -> str:
    """Build a mock API response JSON string."""
    return json.dumps({"url": "https://test.example.com", "data": data})


def _mock_error_response() -> str:
    """Build a mock error API response."""
    return json.dumps({"url": "https://test.example.com", "error": "Service unavailable", "statusCode": 503})


# ---------------------------------------------------------------------------
# Date helper tests
# ---------------------------------------------------------------------------


class TestDateHelpers:
    """Tests for date helper functions."""

    def test_today_format(self) -> None:
        """_today returns a YYYY-MM-DD string."""
        result = _today()
        # Should be parseable as ISO date
        parsed = date.fromisoformat(result)
        assert parsed == date.today()

    def test_week_range_monday(self) -> None:
        """_week_range returns Monday-Friday of the target week."""
        # 2025-01-15 is a Wednesday
        monday, friday = _week_range("2025-01-15")
        assert monday == "2025-01-13"
        assert friday == "2025-01-17"

    def test_week_range_on_monday(self) -> None:
        """_week_range from a Monday returns same week."""
        monday, friday = _week_range("2025-01-13")
        assert monday == "2025-01-13"
        assert friday == "2025-01-17"

    def test_week_range_on_friday(self) -> None:
        """_week_range from a Friday returns same week."""
        monday, friday = _week_range("2025-01-17")
        assert monday == "2025-01-13"
        assert friday == "2025-01-17"

    def test_calculate_dates_day(self) -> None:
        """_calculate_dates with period=day returns same date for start/end."""
        start, end = _calculate_dates("2025-01-15", "day")
        assert start == "2025-01-15"
        assert end == "2025-01-15"

    def test_calculate_dates_week(self) -> None:
        """_calculate_dates with period=week returns Mon-Fri."""
        start, end = _calculate_dates("2025-01-15", "week")
        assert start == "2025-01-13"
        assert end == "2025-01-17"

    def test_calculate_dates_default(self) -> None:
        """_calculate_dates with None target uses today."""
        start, end = _calculate_dates(None, "day")
        today = _today()
        assert start == today
        assert end == today


# ---------------------------------------------------------------------------
# Fetcher tests
# ---------------------------------------------------------------------------


class TestFetchers:
    """Tests for async fetcher functions."""

    @pytest.mark.asyncio
    async def test_fetch_hansard(self) -> None:
        """_fetch_hansard returns parsed debate results."""
        data = {
            "Results": [
                {"Title": "Debate on NHS", "House": "Commons", "DebateSection": "Commons Chamber"},
            ],
            "TotalResultCount": 1,
        }
        mock_resp = _mock_api_response(data)
        with patch("uk_parliament_mcp.cli.digest.get_result", new_callable=AsyncMock, return_value=mock_resp):
            result = await _fetch_hansard("2025-01-15", "2025-01-15", None)
            assert isinstance(result, dict)
            assert result["Results"][0]["Title"] == "Debate on NHS"

    @pytest.mark.asyncio
    async def test_fetch_hansard_error(self) -> None:
        """_fetch_hansard returns empty dict on error."""
        mock_resp = _mock_error_response()
        with patch("uk_parliament_mcp.cli.digest.get_result", new_callable=AsyncMock, return_value=mock_resp):
            result = await _fetch_hansard("2025-01-15", "2025-01-15", None)
            assert result == {}

    @pytest.mark.asyncio
    async def test_fetch_commons_votes(self) -> None:
        """_fetch_commons_votes returns list of divisions."""
        divisions = [{"DivisionId": 1, "Title": "Test Division", "AyeCount": 300, "NoCount": 200}]
        mock_resp = _mock_api_response(divisions)
        with patch("uk_parliament_mcp.cli.digest.get_result", new_callable=AsyncMock, return_value=mock_resp):
            result = await _fetch_commons_votes("2025-01-15", "2025-01-15")
            assert isinstance(result, list)
            assert len(result) == 1
            assert result[0]["Title"] == "Test Division"

    @pytest.mark.asyncio
    async def test_fetch_commons_votes_dict_response(self) -> None:
        """_fetch_commons_votes handles dict with items key."""
        data = {"items": [{"DivisionId": 1, "Title": "Test"}]}
        mock_resp = _mock_api_response(data)
        with patch("uk_parliament_mcp.cli.digest.get_result", new_callable=AsyncMock, return_value=mock_resp):
            result = await _fetch_commons_votes("2025-01-15", "2025-01-15")
            assert len(result) == 1

    @pytest.mark.asyncio
    async def test_fetch_lords_votes(self) -> None:
        """_fetch_lords_votes returns list of divisions."""
        divisions = [{"Title": "Lords Division", "AuthorityCount": 150, "NonAuthorityCount": 100}]
        mock_resp = _mock_api_response(divisions)
        with patch("uk_parliament_mcp.cli.digest.get_result", new_callable=AsyncMock, return_value=mock_resp):
            result = await _fetch_lords_votes("2025-01-15", "2025-01-15")
            assert isinstance(result, list)
            assert result[0]["Title"] == "Lords Division"

    @pytest.mark.asyncio
    async def test_fetch_bills(self) -> None:
        """_fetch_bills returns parsed bill sittings with enriched details."""
        bills_data = {"items": [{"billId": "42"}]}
        bill_detail = {"shortTitle": "Test Bill", "currentStage": {"description": "2nd reading"}}

        async def mock_get(url: str) -> str:
            if "/Bills/42" in url:
                return json.dumps({"url": url, "data": bill_detail})
            return json.dumps({"url": url, "data": bills_data})

        with patch("uk_parliament_mcp.cli.digest.get_result", side_effect=mock_get):
            result = await _fetch_bills("2025-01-15", "2025-01-15", None)
            assert "items" in result
            assert "_bill_details" in result
            assert "42" in result["_bill_details"]

    @pytest.mark.asyncio
    async def test_fetch_bills_house_filter(self) -> None:
        """_fetch_bills passes house filter."""
        mock_resp = _mock_api_response({"items": []})
        with patch("uk_parliament_mcp.cli.digest.get_result", new_callable=AsyncMock, return_value=mock_resp) as mock:
            await _fetch_bills("2025-01-15", "2025-01-15", 1)
            call_url = mock.call_args[0][0]
            assert "House=Commons" in call_url

    @pytest.mark.asyncio
    async def test_fetch_committees(self) -> None:
        """_fetch_committees returns parsed events."""
        events = {"items": [{"committee": {"name": "Treasury"}, "description": "Inquiry"}]}
        mock_resp = _mock_api_response(events)
        with patch("uk_parliament_mcp.cli.digest.get_result", new_callable=AsyncMock, return_value=mock_resp):
            result = await _fetch_committees("2025-01-15", "2025-01-15")
            assert "items" in result

    @pytest.mark.asyncio
    async def test_fetch_statements(self) -> None:
        """_fetch_statements returns parsed statements."""
        stmts = {"results": [{"title": "Statement on X", "answeringBodyName": "Treasury"}]}
        mock_resp = _mock_api_response(stmts)
        with patch("uk_parliament_mcp.cli.digest.get_result", new_callable=AsyncMock, return_value=mock_resp):
            result = await _fetch_statements("2025-01-15", "2025-01-15")
            assert "results" in result

    @pytest.mark.asyncio
    async def test_fetch_oral_qs(self) -> None:
        """_fetch_oral_qs returns parsed oral question times."""
        oqs = {"Response": [{"AnsweringBodyName": "Home Office"}]}
        mock_resp = _mock_api_response(oqs)
        with patch("uk_parliament_mcp.cli.digest.get_result", new_callable=AsyncMock, return_value=mock_resp):
            result = await _fetch_oral_qs("2025-01-15", "2025-01-15")
            assert "Response" in result

    @pytest.mark.asyncio
    async def test_fetch_edms(self) -> None:
        """_fetch_edms returns parsed EDMs."""
        edms = {"Response": [{"Title": "EDM on NHS", "UIN": 123}]}
        mock_resp = _mock_api_response(edms)
        with patch("uk_parliament_mcp.cli.digest.get_result", new_callable=AsyncMock, return_value=mock_resp):
            result = await _fetch_edms("2025-01-15", "2025-01-15")
            assert "Response" in result

    @pytest.mark.asyncio
    async def test_fetch_written_qs(self) -> None:
        """_fetch_written_qs returns parsed written questions."""
        wqs = {"results": [{"questionText": "What steps...", "dateAnswered": "2025-01-15"}]}
        mock_resp = _mock_api_response(wqs)
        with patch("uk_parliament_mcp.cli.digest.get_result", new_callable=AsyncMock, return_value=mock_resp):
            result = await _fetch_written_qs("2025-01-15", "2025-01-15")
            assert "results" in result


# ---------------------------------------------------------------------------
# Aggregator tests
# ---------------------------------------------------------------------------


class TestAggregator:
    """Tests for _fetch_digest_data."""

    @pytest.mark.asyncio
    async def test_fetch_digest_data_all(self) -> None:
        """_fetch_digest_data returns all 9 sections."""
        mock_resp = _mock_api_response({})
        with patch("uk_parliament_mcp.cli.digest.get_result", new_callable=AsyncMock, return_value=mock_resp):
            result = await _fetch_digest_data("2025-01-15", "2025-01-15", None)
            assert "hansard" in result
            assert "commons_divisions" in result
            assert "lords_divisions" in result
            assert "bills" in result
            assert "committees" in result
            assert "written_statements" in result
            assert "oral_questions" in result
            assert "edms" in result
            assert "written_questions" in result

    @pytest.mark.asyncio
    async def test_fetch_digest_data_commons_only(self) -> None:
        """_fetch_digest_data with house=1 excludes lords divisions."""
        mock_resp = _mock_api_response({})
        with patch("uk_parliament_mcp.cli.digest.get_result", new_callable=AsyncMock, return_value=mock_resp):
            result = await _fetch_digest_data("2025-01-15", "2025-01-15", 1)
            assert "commons_divisions" in result
            assert "lords_divisions" not in result

    @pytest.mark.asyncio
    async def test_fetch_digest_data_lords_only(self) -> None:
        """_fetch_digest_data with house=2 excludes commons divisions."""
        mock_resp = _mock_api_response({})
        with patch("uk_parliament_mcp.cli.digest.get_result", new_callable=AsyncMock, return_value=mock_resp):
            result = await _fetch_digest_data("2025-01-15", "2025-01-15", 2)
            assert "lords_divisions" in result
            assert "commons_divisions" not in result

    @pytest.mark.asyncio
    async def test_fetch_digest_data_handles_exceptions(self) -> None:
        """_fetch_digest_data wraps exceptions as error dicts."""
        async def _fail(*args, **kwargs):
            raise ConnectionError("Network down")

        with patch("uk_parliament_mcp.cli.digest.get_result", side_effect=_fail):
            result = await _fetch_digest_data("2025-01-15", "2025-01-15", None)
            # At least some sections should have error dicts
            errors = [v for v in result.values() if isinstance(v, dict) and "error" in v]
            assert len(errors) > 0


# ---------------------------------------------------------------------------
# Main async function tests
# ---------------------------------------------------------------------------


class TestGetDigestAsync:
    """Tests for _get_digest_async."""

    @pytest.mark.asyncio
    async def test_returns_json(self) -> None:
        """_get_digest_async returns valid JSON."""
        mock_resp = _mock_api_response({})
        with patch("uk_parliament_mcp.cli.digest.get_result", new_callable=AsyncMock, return_value=mock_resp):
            result = await _get_digest_async("2025-01-15", "day", None)
            data = json.loads(result)
            assert data["date"] == "2025-01-15"
            assert data["period"] == "day"
            assert data["house"] is None

    @pytest.mark.asyncio
    async def test_week_period(self) -> None:
        """_get_digest_async sets correct dates for week period."""
        mock_resp = _mock_api_response({})
        with patch("uk_parliament_mcp.cli.digest.get_result", new_callable=AsyncMock, return_value=mock_resp):
            result = await _get_digest_async("2025-01-15", "week", None)
            data = json.loads(result)
            assert data["start_date"] == "2025-01-13"
            assert data["end_date"] == "2025-01-17"
            assert data["period"] == "week"

    @pytest.mark.asyncio
    async def test_house_label(self) -> None:
        """_get_digest_async sets house label."""
        mock_resp = _mock_api_response({})
        with patch("uk_parliament_mcp.cli.digest.get_result", new_callable=AsyncMock, return_value=mock_resp):
            result = await _get_digest_async("2025-01-15", "day", 1)
            data = json.loads(result)
            assert data["house"] == "Commons"


# ---------------------------------------------------------------------------
# Renderer tests
# ---------------------------------------------------------------------------


class TestSectionHasData:
    """Tests for _section_has_data helper."""

    def test_none(self) -> None:
        assert _section_has_data(None) is False

    def test_empty_dict(self) -> None:
        assert _section_has_data({}) is False

    def test_empty_list(self) -> None:
        assert _section_has_data([]) is False

    def test_error_dict(self) -> None:
        assert _section_has_data({"error": "fail"}) is False

    def test_dict_with_data(self) -> None:
        assert _section_has_data({"items": [1]}) is True

    def test_nonempty_list(self) -> None:
        assert _section_has_data([1, 2]) is True


class TestDigestHeader:
    """Tests for _render_digest_header."""

    def test_day_header(self) -> None:
        """Header shows date for day period."""
        data = {"date": "2025-01-15", "period": "day", "house": None}
        panel = _render_digest_header(data)
        assert isinstance(panel, Panel)

    def test_week_header(self) -> None:
        """Header shows range for week period."""
        data = {
            "date": "2025-01-15",
            "period": "week",
            "start_date": "2025-01-13",
            "end_date": "2025-01-17",
            "house": None,
        }
        panel = _render_digest_header(data)
        assert isinstance(panel, Panel)

    def test_header_with_house(self) -> None:
        """Header shows house filter."""
        data = {"date": "2025-01-15", "period": "day", "house": "Commons"}
        panel = _render_digest_header(data)
        assert isinstance(panel, Panel)

    def test_header_with_counts(self) -> None:
        """Header shows summary counts."""
        data = {
            "date": "2025-01-15",
            "period": "day",
            "house": None,
            "commons_divisions": [{"id": 1}, {"id": 2}],
            "lords_divisions": [{"id": 3}],
            "bills": {"items": [{"id": 1}]},
            "committees": {"items": [{"id": 1}, {"id": 2}]},
        }
        panel = _render_digest_header(data)
        assert isinstance(panel, Panel)


class TestDivisionsSectionRenderer:
    """Tests for _render_divisions_section."""

    def test_no_divisions(self) -> None:
        assert _render_divisions_section([], []) is None

    def test_commons_divisions(self) -> None:
        commons = [{"Title": "Test Vote", "AyeCount": 300, "NoCount": 200, "Date": "2025-01-15"}]
        panel = _render_divisions_section(commons, [])
        assert isinstance(panel, Panel)

    def test_lords_divisions(self) -> None:
        lords = [{"Title": "Lords Vote", "AuthorityCount": 150, "NonAuthorityCount": 100, "Date": "2025-01-15"}]
        panel = _render_divisions_section([], lords)
        assert isinstance(panel, Panel)

    def test_both_houses(self) -> None:
        commons = [{"Title": "Commons Vote", "AyeCount": 300, "NoCount": 200, "Date": "2025-01-15"}]
        lords = [{"Title": "Lords Vote", "AuthorityCount": 150, "NonAuthorityCount": 100, "Date": "2025-01-15"}]
        panel = _render_divisions_section(commons, lords)
        assert isinstance(panel, Panel)


class TestHansardSectionRenderer:
    """Tests for _render_hansard_section."""

    def test_no_data(self) -> None:
        assert _render_hansard_section(None) is None
        assert _render_hansard_section({}) is None

    def test_results_from_debates_json(self) -> None:
        data = {
            "Results": [
                {"Title": "Debate on NHS", "House": "Commons", "DebateSection": "Commons Chamber"},
                {"Title": "Lords debate", "House": "Lords", "DebateSection": "Lords Chamber"},
            ],
            "TotalResultCount": 2,
        }
        panel = _render_hansard_section(data)
        assert isinstance(panel, Panel)

    def test_sections_list(self) -> None:
        data = [{"Title": "Debate on NHS", "House": "Commons"}]
        panel = _render_hansard_section(data)
        assert isinstance(panel, Panel)


class TestBillsSectionRenderer:
    """Tests for _render_bills_section."""

    def test_no_data(self) -> None:
        assert _render_bills_section(None) is None
        assert _render_bills_section({}) is None

    def test_with_items(self) -> None:
        data = {"items": [{"billId": "123", "date": "2025-01-15"}]}
        panel = _render_bills_section(data)
        assert isinstance(panel, Panel)

    def test_with_enriched_details(self) -> None:
        data = {
            "items": [{"billId": "42"}],
            "_bill_details": {
                "42": {"shortTitle": "Online Safety Bill", "currentStage": {"description": "Royal Assent"}},
            },
        }
        panel = _render_bills_section(data)
        assert isinstance(panel, Panel)


class TestCommitteesSectionRenderer:
    """Tests for _render_committees_section."""

    def test_no_data(self) -> None:
        assert _render_committees_section(None) is None

    def test_with_events(self) -> None:
        data = {"items": [{"committee": {"name": "Treasury"}, "description": "Inquiry", "startTime": "2025-01-15T10:00:00"}]}
        panel = _render_committees_section(data)
        assert isinstance(panel, Panel)


class TestStatementsSectionRenderer:
    """Tests for _render_statements_section."""

    def test_no_data(self) -> None:
        assert _render_statements_section(None) is None

    def test_with_statements(self) -> None:
        data = {"results": [{"title": "Statement", "answeringBodyName": "Treasury"}]}
        panel = _render_statements_section(data)
        assert isinstance(panel, Panel)


class TestOralQsSectionRenderer:
    """Tests for _render_oral_qs_section."""

    def test_no_data(self) -> None:
        assert _render_oral_qs_section(None) is None

    def test_with_data(self) -> None:
        data = {"Response": [{"AnsweringBodyName": "Home Office", "AnswerDate": "2025-01-15"}]}
        panel = _render_oral_qs_section(data)
        assert isinstance(panel, Panel)


class TestEdmsSectionRenderer:
    """Tests for _render_edms_section."""

    def test_no_data(self) -> None:
        assert _render_edms_section(None) is None

    def test_with_edms(self) -> None:
        data = {"Response": [{"UIN": 123, "Title": "NHS Funding", "PrimarySponsor": {"Name": "J Smith"}}]}
        panel = _render_edms_section(data)
        assert isinstance(panel, Panel)


class TestWrittenQsSectionRenderer:
    """Tests for _render_written_qs_section."""

    def test_no_data(self) -> None:
        assert _render_written_qs_section(None) is None

    def test_with_questions(self) -> None:
        data = {"results": [
            {"questionText": "Q1", "dateAnswered": "2025-01-15"},
            {"questionText": "Q2", "dateAnswered": None},
            {"questionText": "Q3", "dateAnswered": "2025-01-16"},
        ]}
        panel = _render_written_qs_section(data)
        assert isinstance(panel, Panel)


class TestRenderDigest:
    """Tests for the main render_digest function."""

    def test_invalid_json(self, capsys) -> None:
        """render_digest handles invalid JSON gracefully."""
        render_digest("not json")

    def test_error_response(self, capsys) -> None:
        """render_digest handles error in data."""
        render_digest(json.dumps({"error": "Something failed"}))

    def test_empty_digest(self, capsys) -> None:
        """render_digest handles digest with no section data."""
        data = {
            "date": "2025-01-15",
            "period": "day",
            "house": None,
            "start_date": "2025-01-15",
            "end_date": "2025-01-15",
        }
        render_digest(json.dumps(data))

    def test_full_digest(self, capsys) -> None:
        """render_digest renders all sections when data is available."""
        data = {
            "date": "2025-01-15",
            "period": "day",
            "house": None,
            "start_date": "2025-01-15",
            "end_date": "2025-01-15",
            "commons_divisions": [{"Title": "Vote A", "AyeCount": 300, "NoCount": 200, "Date": "2025-01-15"}],
            "lords_divisions": [{"Title": "Vote B", "AuthorityCount": 100, "NonAuthorityCount": 80, "Date": "2025-01-15"}],
            "hansard": {"Results": [{"Title": "Debate X", "House": "Commons", "DebateSection": "Commons Chamber"}], "TotalResultCount": 1},
            "bills": {"items": [{"billId": 100, "billShortTitle": "Bill Y", "date": "2025-01-15"}]},
            "committees": {"items": [{"committee": {"name": "Treasury"}, "description": "Hearing", "startTime": "2025-01-15T10:00:00"}]},
            "written_statements": {"results": [{"title": "Statement Z", "answeringBodyName": "DHSC"}]},
            "oral_questions": {"Response": [{"AnsweringBodyName": "MoD", "AnswerDate": "2025-01-15"}]},
            "edms": {"Response": [{"UIN": 42, "Title": "EDM on X", "PrimarySponsor": {"Name": "MP Name"}}]},
            "written_questions": {"results": [{"questionText": "Q", "dateAnswered": "2025-01-15"}]},
        }
        render_digest(json.dumps(data))
