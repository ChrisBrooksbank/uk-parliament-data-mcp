"""Tests that reference-data tools are served from the 15-minute response cache."""

from __future__ import annotations

import importlib
import json

import pytest
from mcp.server.fastmcp import FastMCP

from uk_parliament_mcp import http_client
from uk_parliament_mcp.config import (
    BILLS_API_BASE,
    COMMITTEES_API_BASE,
    ERSKINE_MAY_API_BASE,
    INTERESTS_API_BASE,
    MEMBERS_API_BASE,
    STATUTORY_INSTRUMENTS_API_BASE_V1,
    TREATIES_API_BASE,
    WHATSON_API_BASE,
)

CACHED_TOOLS = [
    ("bills", "bill_types", f"{BILLS_API_BASE}/BillTypes"),
    ("bills", "bill_stages", f"{BILLS_API_BASE}/Stages"),
    ("committees", "get_committee_types", f"{COMMITTEES_API_BASE}/CommitteeType"),
    (
        "committees",
        "get_committee_business_types",
        f"{COMMITTEES_API_BASE}/CommitteeBusinessType",
    ),
    ("committees", "get_committee_publication_types", f"{COMMITTEES_API_BASE}/PublicationType"),
    ("erskine_may", "get_erskine_may_parts", f"{ERSKINE_MAY_API_BASE}/Part"),
    ("interests", "interests_categories", f"{INTERESTS_API_BASE}/Categories"),
    ("members", "get_policy_interests", f"{MEMBERS_API_BASE}/Reference/PolicyInterests"),
    (
        "statutory_instruments",
        "get_laying_bodies",
        f"{STATUTORY_INSTRUMENTS_API_BASE_V1}/LayingBody",
    ),
    (
        "statutory_instruments",
        "get_si_procedures",
        f"{STATUTORY_INSTRUMENTS_API_BASE_V1}/Procedure",
    ),
    (
        "treaties",
        "get_treaty_government_organisations",
        f"{TREATIES_API_BASE}/GovernmentOrganisation",
    ),
    ("treaties", "get_treaty_series_memberships", f"{TREATIES_API_BASE}/SeriesMembership"),
    ("whatson", "get_calendar_categories", f"{WHATSON_API_BASE}/categories/list.json"),
    ("whatson", "get_calendar_locations", f"{WHATSON_API_BASE}/locations/list.json"),
    ("whatson", "get_calendar_tags", f"{WHATSON_API_BASE}/tags/list.json"),
    ("whatson", "get_calendar_types", f"{WHATSON_API_BASE}/types/list.json"),
]


@pytest.fixture
def fetched_urls(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    urls: list[str] = []

    async def fake_get_result(url: str) -> str:
        urls.append(url)
        return json.dumps({"url": url, "data": []})

    monkeypatch.setattr(http_client._client, "get_result", fake_get_result)
    http_client.clear_cache()
    yield urls
    http_client.clear_cache()


@pytest.mark.parametrize(("module", "tool", "url"), CACHED_TOOLS, ids=[t[1] for t in CACHED_TOOLS])
async def test_reference_tool_fetches_once(
    module: str, tool: str, url: str, fetched_urls: list[str]
):
    mcp = FastMCP(name="test")
    importlib.import_module(f"uk_parliament_mcp.tools.{module}").register_tools(mcp)

    await mcp.call_tool(tool, {})
    await mcp.call_tool(tool, {})

    assert fetched_urls == [url]


async def test_errors_are_not_cached(monkeypatch: pytest.MonkeyPatch):
    calls = 0

    async def failing_get_result(url: str) -> str:
        nonlocal calls
        calls += 1
        return json.dumps({"url": url, "error": "boom", "statusCode": 500})

    monkeypatch.setattr(http_client._client, "get_result", failing_get_result)
    http_client.clear_cache()
    mcp = FastMCP(name="test")
    importlib.import_module("uk_parliament_mcp.tools.bills").register_tools(mcp)

    await mcp.call_tool("bill_types", {})
    await mcp.call_tool("bill_types", {})

    assert calls == 2
