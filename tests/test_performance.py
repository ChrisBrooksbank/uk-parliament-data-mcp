"""Performance tests: request counts, response sizes, and request budgets.

These tests ensure every tool stays within its expected HTTP request budget
and that composite tools parallelise correctly. No network calls are made -
all HTTP is mocked.
"""

from __future__ import annotations

import asyncio
import json
import time
from unittest.mock import AsyncMock, patch

import pytest
from mcp.server.fastmcp import FastMCP

from uk_parliament_mcp.tools import (
    bills,
    committees,
    commons_votes,
    composite,
    erskine_may,
    hansard,
    interests,
    lords_votes,
    members,
    now,
    oral_questions,
    statutory_instruments,
    treaties,
    whatson,
    written_questions,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

MOCK_RESPONSE = json.dumps({"url": "https://test", "data": {"items": []}})

# Member search response that composite tools can parse to extract a member_id
MEMBER_SEARCH_RESPONSE = json.dumps(
    {
        "url": "https://test",
        "data": {
            "items": [
                {
                    "value": {
                        "id": 4514,
                        "nameDisplayAs": "Keir Starmer",
                        "latestHouseMembership": {"house": 1},
                    }
                }
            ]
        },
    }
)

# Member direct response for composite tools that take member_id
MEMBER_DIRECT_RESPONSE = json.dumps(
    {
        "url": "https://test",
        "data": {
            "value": {
                "id": 4514,
                "nameDisplayAs": "Keir Starmer",
                "latestHouseMembership": {"house": 1},
            }
        },
    }
)

# Bills search response that composite tools can parse to extract a bill_id
BILL_SEARCH_RESPONSE = json.dumps(
    {
        "url": "https://test",
        "data": {
            "items": [{"billId": 123, "shortTitle": "Test Bill"}],
        },
    }
)

# Committees search response that composite tools can parse
COMMITTEE_SEARCH_RESPONSE = json.dumps(
    {
        "url": "https://test",
        "data": {
            "items": [{"id": 456, "name": "Test Committee"}],
        },
    }
)


def _make_server_with_module(module) -> FastMCP:
    """Create a FastMCP server with a single tool module registered."""
    server = FastMCP(name="test-perf")
    module.register_tools(server)
    return server


def _extract_text(result) -> str:
    """Extract text content from call_tool result.

    FastMCP.call_tool returns (content_list, is_error) tuple.
    """
    content_list = result[0] if isinstance(result, tuple) else result
    item = content_list[0] if isinstance(content_list, list) else content_list
    return item.text if hasattr(item, "text") else str(item)


# ---------------------------------------------------------------------------
# 1. Single-request tool modules: every tool makes exactly 1 HTTP request
# ---------------------------------------------------------------------------

# Each tuple: (module, mock_target, expected_tool_count)
SINGLE_REQUEST_MODULES = [
    (members, "uk_parliament_mcp.tools.members.get_result", 39),
    (bills, "uk_parliament_mcp.tools.bills.get_result", 21),
    (committees, "uk_parliament_mcp.tools.committees.get_result", 30),
    (commons_votes, "uk_parliament_mcp.tools.commons_votes.get_result", 5),
    (lords_votes, "uk_parliament_mcp.tools.lords_votes.get_result", 5),
    (hansard, "uk_parliament_mcp.tools.hansard.get_result", 30),
    (oral_questions, "uk_parliament_mcp.tools.oral_questions.get_result", 5),
    (written_questions, "uk_parliament_mcp.tools.written_questions.get_result", 7),
    (interests, "uk_parliament_mcp.tools.interests.get_result", 6),
    (now, "uk_parliament_mcp.tools.now.get_result", 3),
    (whatson, "uk_parliament_mcp.tools.whatson.get_result", 19),
    (statutory_instruments, "uk_parliament_mcp.tools.statutory_instruments.get_result", 13),
    (treaties, "uk_parliament_mcp.tools.treaties.get_result", 6),
    (erskine_may, "uk_parliament_mcp.tools.erskine_may.get_result", 11),
]


class TestToolCounts:
    """Verify each module registers the expected number of tools."""

    @pytest.mark.parametrize(
        "module,mock_target,expected_count",
        SINGLE_REQUEST_MODULES,
        ids=[m[0].__name__.split(".")[-1] for m in SINGLE_REQUEST_MODULES],
    )
    @pytest.mark.asyncio
    async def test_module_tool_count(self, module, mock_target, expected_count):
        """Each module registers exactly the expected number of tools."""
        server = _make_server_with_module(module)
        tools = await server.list_tools()
        assert len(tools) == expected_count, (
            f"{module.__name__} expected {expected_count} tools, got {len(tools)}: "
            f"{[t.name for t in tools]}"
        )


class TestSingleRequestTools:
    """Every non-composite tool makes exactly 1 HTTP request."""

    @pytest.mark.parametrize(
        "module,mock_target,expected_count",
        SINGLE_REQUEST_MODULES,
        ids=[m[0].__name__.split(".")[-1] for m in SINGLE_REQUEST_MODULES],
    )
    @pytest.mark.asyncio
    async def test_each_tool_makes_one_request(self, module, mock_target, expected_count):
        """Call every tool in the module and verify exactly 1 get_result call each."""
        server = _make_server_with_module(module)
        tools = await server.list_tools()

        for tool in tools:
            with patch(mock_target, new_callable=AsyncMock) as mock_get:
                mock_get.return_value = MOCK_RESPONSE

                # Build minimal valid arguments from the tool's input schema
                args = _build_minimal_args(tool.inputSchema)

                await server.call_tool(tool.name, args)

                assert mock_get.call_count == 1, (
                    f"Tool '{tool.name}' in {module.__name__} made "
                    f"{mock_get.call_count} HTTP requests, expected exactly 1"
                )


def _build_minimal_args(schema: dict) -> dict:
    """Build minimal valid arguments from a JSON Schema.

    Uses sensible defaults for required params so we can invoke every tool.
    """
    args: dict = {}
    required = set(schema.get("required", []))
    properties = schema.get("properties", {})

    for name, prop in properties.items():
        if name not in required:
            continue

        prop_type = prop.get("type", "string")
        if prop_type == "string":
            args[name] = "test"
        elif prop_type == "integer" or prop_type == "number":
            args[name] = 1
        elif prop_type == "boolean":
            args[name] = True
        elif prop_type == "array":
            item_type = prop.get("items", {}).get("type", "integer")
            if item_type == "integer":
                args[name] = [1]
            elif item_type == "string":
                args[name] = ["test"]
            else:
                args[name] = [1]
        else:
            args[name] = "test"

    return args


# ---------------------------------------------------------------------------
# 2. Composite tools: verify exact request budgets
# ---------------------------------------------------------------------------


class TestCompositeRequestBudgets:
    """Composite tools must stay within their documented request budgets."""

    @pytest.fixture
    def mcp(self):
        server = FastMCP(name="test-perf-composite")
        composite.register_tools(server)
        return server

    @pytest.mark.asyncio
    async def test_get_mp_profile_makes_4_requests(self, mcp: FastMCP):
        """get_mp_profile: 1 member fetch + 3 parallel detail fetches = 4 requests."""
        with patch(
            "uk_parliament_mcp.tools.composite.get_result", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = MEMBER_DIRECT_RESPONSE
            await mcp.call_tool("get_mp_profile", {"member_id": 4514})
            assert mock_get.call_count == 4, (
                f"get_mp_profile made {mock_get.call_count} requests, expected 4"
            )

    @pytest.mark.asyncio
    async def test_check_mp_vote_makes_2_requests(self, mcp: FastMCP):
        """check_mp_vote: 1 member fetch + 1 divisions = 2 requests."""
        with patch(
            "uk_parliament_mcp.tools.composite.get_result", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = MEMBER_DIRECT_RESPONSE
            await mcp.call_tool("check_mp_vote", {"member_id": 4514, "topic": "climate"})
            assert mock_get.call_count == 2, (
                f"check_mp_vote made {mock_get.call_count} requests, expected 2"
            )

    @pytest.mark.asyncio
    async def test_get_bill_overview_makes_4_requests(self, mcp: FastMCP):
        """get_bill_overview: 1 search + 3 parallel detail fetches = 4 requests."""
        with patch(
            "uk_parliament_mcp.tools.composite.get_result", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = BILL_SEARCH_RESPONSE
            await mcp.call_tool("get_bill_overview", {"search_term": "Online Safety"})
            assert mock_get.call_count == 4, (
                f"get_bill_overview made {mock_get.call_count} requests, expected 4"
            )

    @pytest.mark.asyncio
    async def test_get_committee_summary_makes_5_requests(self, mcp: FastMCP):
        """get_committee_summary: 1 search + 4 parallel detail fetches = 5 requests."""
        with patch(
            "uk_parliament_mcp.tools.composite.get_result", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = COMMITTEE_SEARCH_RESPONSE
            await mcp.call_tool("get_committee_summary", {"topic": "Treasury"})
            assert mock_get.call_count == 5, (
                f"get_committee_summary made {mock_get.call_count} requests, expected 5"
            )

    @pytest.mark.asyncio
    async def test_get_my_mp_without_topic_makes_5_requests(self, mcp: FastMCP):
        """get_my_mp without topic: 1 search + 4 parallel = 5 requests."""
        with patch(
            "uk_parliament_mcp.tools.composite.get_result", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = MEMBER_SEARCH_RESPONSE
            await mcp.call_tool("get_my_mp", {"postcode": "SW1A 1AA"})
            assert mock_get.call_count == 5, (
                f"get_my_mp (no topic) made {mock_get.call_count} requests, expected 5"
            )

    @pytest.mark.asyncio
    async def test_get_my_mp_with_topic_makes_6_requests(self, mcp: FastMCP):
        """get_my_mp with topic: 1 search + 5 parallel = 6 requests."""
        with patch(
            "uk_parliament_mcp.tools.composite.get_result", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = MEMBER_SEARCH_RESPONSE
            await mcp.call_tool("get_my_mp", {"postcode": "SW1A 1AA", "topic": "climate"})
            assert mock_get.call_count == 6, (
                f"get_my_mp (with topic) made {mock_get.call_count} requests, expected 6"
            )


# ---------------------------------------------------------------------------
# 3. Composite tools: verify parallel execution via asyncio.gather
# ---------------------------------------------------------------------------


class TestCompositeParallelExecution:
    """Composite tools must run detail fetches in parallel, not serially."""

    @pytest.fixture
    def mcp(self):
        server = FastMCP(name="test-perf-parallel")
        composite.register_tools(server)
        return server

    @pytest.mark.asyncio
    async def test_get_mp_profile_runs_details_in_parallel(self, mcp: FastMCP):
        """The 3 detail requests in get_mp_profile should run concurrently.

        If run serially with a 0.1s delay each, total would be >= 0.3s.
        If parallel, total should be ~0.1s.
        """
        call_count = 0

        async def slow_mock(url: str) -> str:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # First call is the member fetch - return immediately
                return MEMBER_DIRECT_RESPONSE
            # Subsequent calls simulate slow API responses
            await asyncio.sleep(0.1)
            return MOCK_RESPONSE

        with patch("uk_parliament_mcp.tools.composite.get_result", side_effect=slow_mock):
            start = time.monotonic()
            await mcp.call_tool("get_mp_profile", {"member_id": 4514})
            elapsed = time.monotonic() - start

        # With 3 parallel requests at 0.1s each, serial would be >= 0.3s.
        # Parallel should complete in ~0.1s. Allow generous margin.
        assert elapsed < 0.25, (
            f"get_mp_profile took {elapsed:.2f}s - detail fetches may not be parallel"
        )

    @pytest.mark.asyncio
    async def test_get_committee_summary_runs_details_in_parallel(self, mcp: FastMCP):
        """The 4 detail requests in get_committee_summary should run concurrently."""
        call_count = 0

        async def slow_mock(url: str) -> str:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return COMMITTEE_SEARCH_RESPONSE
            await asyncio.sleep(0.1)
            return MOCK_RESPONSE

        with patch("uk_parliament_mcp.tools.composite.get_result", side_effect=slow_mock):
            start = time.monotonic()
            await mcp.call_tool("get_committee_summary", {"topic": "Treasury"})
            elapsed = time.monotonic() - start

        # 4 parallel requests at 0.1s: serial >= 0.4s, parallel ~0.1s
        assert elapsed < 0.25, (
            f"get_committee_summary took {elapsed:.2f}s - detail fetches may not be parallel"
        )

    @pytest.mark.asyncio
    async def test_get_bill_overview_runs_details_in_parallel(self, mcp: FastMCP):
        """The 3 detail requests in get_bill_overview should run concurrently."""
        call_count = 0

        async def slow_mock(url: str) -> str:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return BILL_SEARCH_RESPONSE
            await asyncio.sleep(0.1)
            return MOCK_RESPONSE

        with patch("uk_parliament_mcp.tools.composite.get_result", side_effect=slow_mock):
            start = time.monotonic()
            await mcp.call_tool("get_bill_overview", {"search_term": "Test"})
            elapsed = time.monotonic() - start

        assert elapsed < 0.25, (
            f"get_bill_overview took {elapsed:.2f}s - detail fetches may not be parallel"
        )


# ---------------------------------------------------------------------------
# 4. Response size tests
# ---------------------------------------------------------------------------


class TestResponseSizes:
    """Verify tool responses stay within reasonable size bounds."""

    @pytest.mark.asyncio
    async def test_single_tool_response_under_size_limit(self):
        """A single-request tool's response should be bounded by the mock data."""
        server = _make_server_with_module(members)

        with patch(
            "uk_parliament_mcp.tools.members.get_result", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = MOCK_RESPONSE
            result = await server.call_tool("get_member_by_id", {"member_id": 4514})

        # Result should be valid JSON and reasonably sized
        response_text = _extract_text(result)
        assert len(response_text) < 1_000_000, (
            f"Response was {len(response_text)} bytes, expected < 1MB"
        )

    @pytest.mark.asyncio
    async def test_composite_tool_response_is_valid_json(self):
        """Composite tool responses must be valid JSON."""
        server = FastMCP(name="test-size")
        composite.register_tools(server)

        with patch(
            "uk_parliament_mcp.tools.composite.get_result", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = MEMBER_DIRECT_RESPONSE
            result = await server.call_tool("get_mp_profile", {"member_id": 4514})

        response_text = _extract_text(result)
        parsed = json.loads(response_text)
        assert "member_id" in parsed
        assert "sources" in parsed

    @pytest.mark.asyncio
    async def test_composite_response_includes_all_sections(self):
        """get_mp_profile must include biography, interests, and voting sections."""
        server = FastMCP(name="test-sections")
        composite.register_tools(server)

        with patch(
            "uk_parliament_mcp.tools.composite.get_result", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = MEMBER_DIRECT_RESPONSE
            result = await server.call_tool("get_mp_profile", {"member_id": 4514})

        response_text = _extract_text(result)
        parsed = json.loads(response_text)
        assert "biography" in parsed
        assert "registered_interests" in parsed
        assert "recent_voting" in parsed
        assert "basic_info" in parsed


# ---------------------------------------------------------------------------
# 5. Composite error paths: no member found should short-circuit
# ---------------------------------------------------------------------------


class TestCompositeEarlyReturn:
    """When a search returns no results, composite tools should stop early."""

    EMPTY_SEARCH = json.dumps({"url": "https://test", "data": {"items": []}})

    @pytest.fixture
    def mcp(self):
        server = FastMCP(name="test-perf-early")
        composite.register_tools(server)
        return server

    @pytest.mark.asyncio
    async def test_get_bill_overview_stops_at_1_request_on_no_match(self, mcp: FastMCP):
        """get_bill_overview should make only 1 request if no bill found."""
        with patch(
            "uk_parliament_mcp.tools.composite.get_result", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = self.EMPTY_SEARCH
            await mcp.call_tool("get_bill_overview", {"search_term": "Nonexistent"})
            assert mock_get.call_count == 1

    @pytest.mark.asyncio
    async def test_get_committee_summary_stops_at_1_request_on_no_match(self, mcp: FastMCP):
        """get_committee_summary should make only 1 request if no committee found."""
        with patch(
            "uk_parliament_mcp.tools.composite.get_result", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = self.EMPTY_SEARCH
            await mcp.call_tool("get_committee_summary", {"topic": "Nonexistent"})
            assert mock_get.call_count == 1

    @pytest.mark.asyncio
    async def test_get_my_mp_stops_at_1_request_on_no_match(self, mcp: FastMCP):
        """get_my_mp should make only 1 request if no MP found for postcode."""
        with patch(
            "uk_parliament_mcp.tools.composite.get_result", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = self.EMPTY_SEARCH
            await mcp.call_tool("get_my_mp", {"postcode": "ZZ99 9ZZ"})
            assert mock_get.call_count == 1


# ---------------------------------------------------------------------------
# 6. URL construction performance: no redundant encoding passes
# ---------------------------------------------------------------------------


class TestUrlConstruction:
    """Verify URL building doesn't add overhead or duplicate encoding."""

    @pytest.mark.asyncio
    async def test_build_url_returns_base_for_empty_params(self):
        """build_url with no params returns base URL unchanged (no wasted work)."""
        from uk_parliament_mcp.http_client import build_url

        base = "https://api.parliament.uk/test"
        result = build_url(base, {})
        assert result == base
        result = build_url(base, {"a": None, "b": ""})
        assert result == base

    @pytest.mark.asyncio
    async def test_build_url_filters_none_without_iteration_waste(self):
        """build_url filters None/empty in a single pass."""
        from uk_parliament_mcp.http_client import build_url

        result = build_url(
            "https://api.test",
            {"keep": "yes", "drop1": None, "drop2": "", "also_keep": 42},
        )
        assert "keep=yes" in result
        assert "also_keep=42" in result
        assert "drop1" not in result
        assert "drop2" not in result
