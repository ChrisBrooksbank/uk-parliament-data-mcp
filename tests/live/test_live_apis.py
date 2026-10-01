"""Live checks against the real Parliament APIs.

Every other test mocks HTTP, so they stay green when Parliament changes or
retires an endpoint (as happened with Statutory Instruments API v1). These
tests call the real APIs through the MCP server and fail on any error
response. They are skipped unless PARLIAMENT_LIVE_TESTS=1, and run weekly in
.github/workflows/live-api.yml.

    PARLIAMENT_LIVE_TESTS=1 pytest tests/live --no-cov
"""

from __future__ import annotations

import asyncio
import json
import os
from typing import Any

import pytest

from uk_parliament_mcp.server import create_server

pytestmark = [
    pytest.mark.live,
    # One event loop for the module: the shared httpx client is bound to the loop
    # it first ran on, as it is in the real server.
    pytest.mark.asyncio(loop_scope="module"),
    pytest.mark.skipif(
        os.environ.get("PARLIAMENT_LIVE_TESTS") != "1",
        reason="set PARLIAMENT_LIVE_TESTS=1 to call the real Parliament APIs",
    ),
]

# Guidance tools that never touch the network.
OFFLINE_TOOLS = {"order_order", "get_cli_reference"}

# Tools whose upstream endpoint is known to be broken. Each entry needs a reason;
# remove it once the API is fixed.
KNOWN_BROKEN: dict[str, str] = {}

# Tools with required arguments, called with long-lived IDs and search terms.
WITH_ARGS: list[tuple[str, dict[str, Any]]] = [
    ("get_member_by_name", {"name": "Starmer"}),
    ("get_member_by_id", {"member_id": 4514}),
    ("get_members_biography", {"member_id": 4514}),
    ("parties_list_by_house", {"house": 1}),
    ("search_bills", {"search_term": "Online Safety"}),
    ("search_committees", {"search_term": "Treasury"}),
    ("search_commons_divisions", {"search_term": "climate"}),
    ("search_hansard_members", {"search_term": "Starmer"}),
    ("search_statutory_instruments", {"name": "Regulations"}),
    ("search_acts_of_parliament", {"name": "Climate Change"}),
    ("search_treaties", {"search_text": "trade"}),
    ("search_erskine_may", {"search_term": "quorum"}),
    ("search_historical_members", {"name": "Churchill", "date_to_search_for": "1950-01-01"}),
    ("get_si_procedure", {"procedure_id": "H5YJQsK2"}),
    ("get_mp_profile", {"member_id": 4514}),
    ("check_mp_vote", {"member_id": 4514, "topic": "climate"}),
    ("get_my_mp", {"postcode": "SW1A 1AA"}),
    ("get_bill_overview", {"search_term": "Online Safety"}),
    ("get_committee_summary", {"topic": "Treasury"}),
    ("parliament_guide", {"topic": "members"}),
]


def _no_arg_tools() -> list[str]:
    async def collect() -> list[str]:
        tools = await create_server().list_tools()
        return sorted(
            t.name
            for t in tools
            if not t.inputSchema.get("required")
            and t.name not in OFFLINE_TOOLS
            and t.name not in KNOWN_BROKEN
        )

    return asyncio.run(collect())


CASES = [(name, {}) for name in _no_arg_tools()] + WITH_ARGS


@pytest.fixture(scope="module")
def server():
    return create_server()


@pytest.mark.parametrize(("tool", "args"), CASES, ids=[c[0] for c in CASES])
async def test_tool_returns_data(server, tool: str, args: dict[str, Any]):
    content, _ = await server.call_tool(tool, args)
    text = content[0].text

    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        # Guidance tools return plain text
        assert text.strip(), f"{tool} returned an empty response"
        return

    assert isinstance(payload, dict | list), f"{tool} returned {type(payload).__name__}"
    if isinstance(payload, dict):
        assert "error" not in payload, f"{tool} failed: {payload.get('url')} -> {payload['error']}"
