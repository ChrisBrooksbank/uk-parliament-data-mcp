"""Tests for universal search CLI command and async core."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import pytest
from typer.testing import CliRunner

from uk_parliament_mcp.cli.search import (
    ALL_SOURCE_NAMES,
    SCOPE_ALIASES,
    SOURCE_MAP,
    SOURCES,
    _fetch_source,
    _resolve_scope,
    _universal_search_async,
)

runner = CliRunner()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _mock_api_response(data: dict | list) -> str:
    """Build a mock API response JSON string."""
    return json.dumps({"url": "https://test.example.com", "data": data})


def _mock_error_response() -> str:
    """Build a mock error API response."""
    return json.dumps({"url": "https://test.example.com", "error": "Service unavailable", "statusCode": 503})


def _parse_json_output(output: str) -> dict:
    """Extract JSON from CLI output, skipping non-JSON lines (e.g. warnings)."""
    for line in output.splitlines():
        line = line.strip()
        if line.startswith("{"):
            return json.loads(line)
    raise ValueError(f"No JSON found in output: {output!r}")


# ---------------------------------------------------------------------------
# Source registry tests
# ---------------------------------------------------------------------------


class TestSourceRegistry:
    """Tests for the search source registry."""

    def test_all_12_sources_registered(self) -> None:
        """All 12 search sources are registered."""
        assert len(SOURCES) == 12

    def test_source_map_matches_list(self) -> None:
        """SOURCE_MAP keys match SOURCES names."""
        assert set(SOURCE_MAP.keys()) == {s.name for s in SOURCES}

    def test_all_source_names_list(self) -> None:
        """ALL_SOURCE_NAMES matches SOURCE_MAP keys."""
        assert set(ALL_SOURCE_NAMES) == set(SOURCE_MAP.keys())

    @pytest.mark.parametrize("name", ALL_SOURCE_NAMES)
    def test_url_builders_produce_strings(self, name: str) -> None:
        """Each source's URL builder returns a string."""
        source = SOURCE_MAP[name]
        if name == "hansard":
            url = source.build_url("test", 5, 30)  # type: ignore[call-arg]
        else:
            url = source.build_url("test", 5)
        assert isinstance(url, str)
        assert "test" in url or "test" in url.lower()

    def test_members_url_has_name_param(self) -> None:
        """Members URL uses the Name parameter."""
        url = SOURCE_MAP["members"].build_url("Starmer", 5)
        assert "Name=Starmer" in url

    def test_bills_url_has_search_term(self) -> None:
        """Bills URL uses the SearchTerm parameter."""
        url = SOURCE_MAP["bills"].build_url("Safety", 5)
        assert "SearchTerm=Safety" in url

    def test_hansard_url_has_date_range(self) -> None:
        """Hansard URL includes date range parameters."""
        url = SOURCE_MAP["hansard"].build_url("NHS", 5, 30)  # type: ignore[call-arg]
        assert "startDate" in url
        assert "endDate" in url

    def test_erskine_may_url_has_path_segment(self) -> None:
        """Erskine May uses a path segment for search term."""
        url = SOURCE_MAP["erskine-may"].build_url("Speaker", 5)
        assert "ParagraphSearchResults/Speaker" in url


# ---------------------------------------------------------------------------
# Scope resolution tests
# ---------------------------------------------------------------------------


class TestScopeResolution:
    """Tests for _resolve_scope."""

    def test_none_scope_returns_all(self) -> None:
        """None scope returns all source names."""
        result = _resolve_scope(None, None)
        assert set(result) == set(ALL_SOURCE_NAMES)

    def test_specific_scope(self) -> None:
        """Specific source names are returned."""
        result = _resolve_scope(["bills", "members"], None)
        assert result == ["bills", "members"]

    def test_votes_alias(self) -> None:
        """'votes' alias expands to commons-votes and lords-votes."""
        result = _resolve_scope(["votes"], None)
        assert set(result) == {"commons-votes", "lords-votes"}

    def test_questions_alias(self) -> None:
        """'questions' alias expands correctly."""
        result = _resolve_scope(["questions"], None)
        assert set(result) == set(SCOPE_ALIASES["questions"])

    def test_legislation_alias(self) -> None:
        """'legislation' alias expands correctly."""
        result = _resolve_scope(["legislation"], None)
        assert set(result) == set(SCOPE_ALIASES["legislation"])

    def test_mixed_scope_and_alias(self) -> None:
        """Mixing direct names and aliases works."""
        result = _resolve_scope(["members", "votes"], None)
        assert set(result) == {"members", "commons-votes", "lords-votes"}

    def test_exclude_removes_source(self) -> None:
        """Exclude removes a specific source."""
        result = _resolve_scope(None, ["erskine-may"])
        assert "erskine-may" not in result
        assert len(result) == len(ALL_SOURCE_NAMES) - 1

    def test_exclude_alias(self) -> None:
        """Exclude with alias removes expanded sources."""
        result = _resolve_scope(None, ["votes"])
        assert "commons-votes" not in result
        assert "lords-votes" not in result

    def test_invalid_scope_raises(self) -> None:
        """Unknown source name raises ValueError."""
        with pytest.raises(ValueError, match="Unknown source"):
            _resolve_scope(["nonexistent"], None)


# ---------------------------------------------------------------------------
# Item extractor tests
# ---------------------------------------------------------------------------


class TestItemExtractors:
    """Tests for source-specific item extractors."""

    def test_members_extracts_value(self) -> None:
        """Members extractor unwraps items[].value."""
        data = {"items": [{"value": {"id": 1, "nameDisplayAs": "Test"}}], "totalResults": 1}
        items = SOURCE_MAP["members"].extract_items(data)
        assert len(items) == 1
        assert items[0]["nameDisplayAs"] == "Test"

    def test_bills_extracts_items(self) -> None:
        """Bills extractor gets items list."""
        data = {"items": [{"shortTitle": "Test Bill"}], "totalResults": 1}
        items = SOURCE_MAP["bills"].extract_items(data)
        assert len(items) == 1

    def test_hansard_extracts_results(self) -> None:
        """Hansard extractor gets Results list."""
        data = {"Results": [{"Title": "Test"}], "TotalResultCount": 1}
        items = SOURCE_MAP["hansard"].extract_items(data)
        assert len(items) == 1

    def test_edms_extracts_response(self) -> None:
        """EDMs extractor gets Response list."""
        data = {"Response": [{"Title": "Test EDM"}], "PagingInfo": {"Total": 1}}
        items = SOURCE_MAP["edms"].extract_items(data)
        assert len(items) == 1

    def test_written_questions_extracts_results(self) -> None:
        """Written questions extractor gets results list."""
        data = {"results": [{"value": {"title": "Test"}}], "totalResults": 1}
        items = SOURCE_MAP["written-questions"].extract_items(data)
        assert len(items) == 1


# ---------------------------------------------------------------------------
# Total extractor tests
# ---------------------------------------------------------------------------


class TestTotalExtractors:
    """Tests for source-specific total extractors."""

    def test_members_total(self) -> None:
        """Members total uses totalResults."""
        data = {"items": [], "totalResults": 42}
        assert SOURCE_MAP["members"].extract_total(data) == 42

    def test_hansard_total(self) -> None:
        """Hansard total uses TotalResultCount."""
        data = {"Results": [], "TotalResultCount": 100}
        assert SOURCE_MAP["hansard"].extract_total(data) == 100

    def test_edms_total(self) -> None:
        """EDMs total uses PagingInfo.Total."""
        data = {"Response": [], "PagingInfo": {"Total": 55}}
        assert SOURCE_MAP["edms"].extract_total(data) == 55

    def test_commons_votes_total_none(self) -> None:
        """Commons votes returns None for total."""
        data = [{"Title": "Test"}]
        assert SOURCE_MAP["commons-votes"].extract_total(data) is None


# ---------------------------------------------------------------------------
# Fetch source tests
# ---------------------------------------------------------------------------


class TestFetchSource:
    """Tests for _fetch_source."""

    @pytest.mark.asyncio
    async def test_successful_fetch(self) -> None:
        """Successful fetch returns items and total."""
        mock_data = {"items": [{"value": {"id": 1, "nameDisplayAs": "Test"}}], "totalResults": 1}
        with patch("uk_parliament_mcp.cli.search.get_result", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = _mock_api_response(mock_data)
            result = await _fetch_source(SOURCE_MAP["members"], "Test", 5, 30)

        assert result["source"] == "members"
        assert len(result["items"]) == 1
        assert result["total"] == 1
        assert result["error"] is None

    @pytest.mark.asyncio
    async def test_error_response(self) -> None:
        """Error response returns error string."""
        with patch("uk_parliament_mcp.cli.search.get_result", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = _mock_error_response()
            result = await _fetch_source(SOURCE_MAP["members"], "Test", 5, 30)

        assert result["error"] == "Failed to parse response"
        assert result["items"] == []

    @pytest.mark.asyncio
    async def test_exception_returns_error(self) -> None:
        """Exception in fetch returns error dict."""
        with patch("uk_parliament_mcp.cli.search.get_result", new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = RuntimeError("Connection failed")
            result = await _fetch_source(SOURCE_MAP["members"], "Test", 5, 30)

        assert "Connection failed" in result["error"]
        assert result["items"] == []

    @pytest.mark.asyncio
    async def test_hansard_passes_days(self) -> None:
        """Hansard source passes days parameter to URL builder."""
        mock_data = {"Results": [{"Title": "Test"}], "TotalResultCount": 1}
        with patch("uk_parliament_mcp.cli.search.get_result", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = _mock_api_response(mock_data)
            result = await _fetch_source(SOURCE_MAP["hansard"], "NHS", 5, 60)

        assert result["source"] == "hansard"
        assert result["error"] is None
        # Verify the URL contains date parameters
        assert "startDate" in result["url"]

    @pytest.mark.asyncio
    async def test_limit_caps_items(self) -> None:
        """Items are capped at the limit."""
        mock_data = {"items": [{"value": {"id": i}} for i in range(20)], "totalResults": 20}
        with patch("uk_parliament_mcp.cli.search.get_result", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = _mock_api_response(mock_data)
            result = await _fetch_source(SOURCE_MAP["members"], "Test", 3, 30)

        assert len(result["items"]) == 3


# ---------------------------------------------------------------------------
# Universal search async tests
# ---------------------------------------------------------------------------


class TestUniversalSearchAsync:
    """Tests for _universal_search_async."""

    @pytest.mark.asyncio
    async def test_returns_valid_json(self) -> None:
        """_universal_search_async returns valid JSON."""
        mock_data = {"items": [], "totalResults": 0}
        with patch("uk_parliament_mcp.cli.search.get_result", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = _mock_api_response(mock_data)
            result = await _universal_search_async("test", scope=["members"])

        parsed = json.loads(result)
        assert parsed["query"] == "test"
        assert parsed["sources_queried"] == 1
        assert "summary" in parsed
        assert "results" in parsed

    @pytest.mark.asyncio
    async def test_scope_limits_sources(self) -> None:
        """Scope parameter limits which sources are queried."""
        mock_data = {"items": [], "totalResults": 0}
        with patch("uk_parliament_mcp.cli.search.get_result", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = _mock_api_response(mock_data)
            result = await _universal_search_async("test", scope=["bills", "members"])

        parsed = json.loads(result)
        assert parsed["sources_queried"] == 2
        assert set(parsed["results"].keys()) == {"bills", "members"}

    @pytest.mark.asyncio
    async def test_partial_failure_returns_other_results(self) -> None:
        """One failing source doesn't prevent other sources from returning."""
        members_data = {"items": [{"value": {"id": 1}}], "totalResults": 1}
        bills_error = _mock_error_response()

        call_count = 0

        async def mock_get(url: str) -> str:
            nonlocal call_count
            call_count += 1
            if "members" in url.lower():
                return _mock_api_response(members_data)
            return bills_error

        with patch("uk_parliament_mcp.cli.search.get_result", side_effect=mock_get):
            result = await _universal_search_async("test", scope=["members", "bills"])

        parsed = json.loads(result)
        # Members should succeed
        assert parsed["summary"]["members"]["returned"] == 1
        # Bills should show error
        assert parsed["summary"]["bills"]["error"] is not None

    @pytest.mark.asyncio
    async def test_exclude_removes_sources(self) -> None:
        """Exclude parameter removes sources."""
        mock_data = {"items": [], "totalResults": 0}
        with patch("uk_parliament_mcp.cli.search.get_result", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = _mock_api_response(mock_data)
            result = await _universal_search_async("test", exclude=["erskine-may"])

        parsed = json.loads(result)
        assert parsed["sources_queried"] == 11
        assert "erskine-may" not in parsed["results"]


# ---------------------------------------------------------------------------
# CLI command tests
# ---------------------------------------------------------------------------


class TestSearchCLI:
    """Tests for the CLI search command."""

    def test_basic_search(self) -> None:
        """Basic search command produces JSON output."""
        from uk_parliament_mcp.cli.main import app

        mock_data = {"items": [{"value": {"id": 1, "nameDisplayAs": "Test"}}], "totalResults": 1}
        with patch("uk_parliament_mcp.cli.search.get_result", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = _mock_api_response(mock_data)
            result = runner.invoke(app, ["search", "NHS", "--format", "json"])

        assert result.exit_code == 0
        parsed = _parse_json_output(result.output)
        assert parsed["query"] == "NHS"

    def test_scoped_search(self) -> None:
        """Scoped search only queries specified sources."""
        from uk_parliament_mcp.cli.main import app

        mock_data = {"items": [], "totalResults": 0}
        with patch("uk_parliament_mcp.cli.search.get_result", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = _mock_api_response(mock_data)
            result = runner.invoke(app, ["search", "NHS", "--scope", "bills,members", "--format", "json"])

        assert result.exit_code == 0
        parsed = _parse_json_output(result.output)
        assert parsed["sources_queried"] == 2

    def test_counts_only(self) -> None:
        """--counts-only strips items from output."""
        from uk_parliament_mcp.cli.main import app

        mock_data = {"items": [{"value": {"id": 1}}], "totalResults": 1}
        with patch("uk_parliament_mcp.cli.search.get_result", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = _mock_api_response(mock_data)
            result = runner.invoke(app, ["search", "NHS", "--counts-only", "--scope", "members", "--format", "json"])

        assert result.exit_code == 0
        parsed = _parse_json_output(result.output)
        assert "summary" in parsed
        assert "results" not in parsed

    def test_invalid_scope_error(self) -> None:
        """Invalid scope name produces error."""
        from uk_parliament_mcp.cli.main import app

        result = runner.invoke(app, ["search", "NHS", "--scope", "nonexistent", "--format", "json"])
        assert result.exit_code == 1

    def test_limit_option(self) -> None:
        """--limit option is passed through."""
        from uk_parliament_mcp.cli.main import app

        mock_data = {"items": [{"value": {"id": i}} for i in range(20)], "totalResults": 20}
        with patch("uk_parliament_mcp.cli.search.get_result", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = _mock_api_response(mock_data)
            result = runner.invoke(app, ["search", "NHS", "--limit", "3", "--scope", "members", "--format", "json"])

        assert result.exit_code == 0
        parsed = _parse_json_output(result.output)
        assert parsed["summary"]["members"]["returned"] == 3

    def test_exclude_option(self) -> None:
        """--exclude removes sources."""
        from uk_parliament_mcp.cli.main import app

        mock_data = {"items": [], "totalResults": 0}
        with patch("uk_parliament_mcp.cli.search.get_result", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = _mock_api_response(mock_data)
            result = runner.invoke(app, ["search", "NHS", "--exclude", "erskine-may", "--format", "json"])

        assert result.exit_code == 0
        parsed = _parse_json_output(result.output)
        assert parsed["sources_queried"] == 11

    def test_experimental_warning(self) -> None:
        """Search command emits an experimental warning on stderr."""
        from uk_parliament_mcp.cli.main import app

        mock_data = {"items": [], "totalResults": 0}
        with patch("uk_parliament_mcp.cli.search.get_result", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = _mock_api_response(mock_data)
            result = runner.invoke(app, ["search", "NHS", "--scope", "members", "--format", "json"])

        assert result.exit_code == 0
        # Typer CliRunner captures stderr in output by default
        assert "experimental" in result.output.lower() or "experimental" in (result.stderr or "").lower()
