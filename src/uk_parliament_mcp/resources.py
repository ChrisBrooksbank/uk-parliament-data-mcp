"""MCP Resources for semi-static Parliament reference data.

Exposes reference data as MCP Resources so clients can read them without
tool calls, reducing round-trips for data that rarely changes.
"""

from __future__ import annotations

import json

from mcp.server.fastmcp import FastMCP

from uk_parliament_mcp.config import (
    BILLS_API_BASE,
    MEMBERS_API_BASE,
)
from uk_parliament_mcp.http_client import get_result_cached
from uk_parliament_mcp.tools.core import QUICK_REFERENCE


def register_resources(mcp: FastMCP) -> None:
    """Register MCP resources with the server."""

    @mcp.resource("parliament://conventions")
    async def conventions_resource() -> str:
        """UK Parliament API conventions: house IDs, date formats, pagination, naming."""
        return json.dumps(
            {
                "houses": {
                    "1": "House of Commons (MPs)",
                    "2": "House of Lords (Peers)",
                },
                "houseStrings": {
                    "Commons": "House of Commons",
                    "Lords": "House of Lords",
                },
                "dateFormat": "YYYY-MM-DD (e.g., 2024-03-15)",
                "pagination": {
                    "skip": "Number of records to skip (default: 0)",
                    "take": "Number of records to return (typical: 20-30, max: 100)",
                },
                "responseFormat": {
                    "success": '{"url": "...", "data": {...}}',
                    "error": '{"url": "...", "error": "...", "statusCode": N}',
                },
                "namingConventions": {
                    "search_*": "Search/discovery tools",
                    "get_*": "Retrieve specific item by ID or parameters",
                    "*_by_id": "Requires specific ID parameter",
                    "*_for_member": "Requires member_id parameter",
                },
            },
            indent=2,
        )

    @mcp.resource("parliament://houses")
    async def houses_resource() -> str:
        """House of Commons and House of Lords reference data."""
        return json.dumps(
            {
                "houses": [
                    {
                        "id": 1,
                        "name": "House of Commons",
                        "shortName": "Commons",
                        "members": "MPs (Members of Parliament)",
                        "electionMethod": "Elected by constituents",
                    },
                    {
                        "id": 2,
                        "name": "House of Lords",
                        "shortName": "Lords",
                        "members": "Lords (Peers)",
                        "electionMethod": "Appointed (life peers, hereditary, bishops)",
                    },
                ]
            },
            indent=2,
        )

    @mcp.resource("parliament://tools/summary")
    async def tools_summary_resource() -> str:
        """Quick reference of all available Parliament MCP tools."""
        return QUICK_REFERENCE

    @mcp.resource("parliament://member-types")
    async def member_types_resource() -> str:
        """MP vs Lord member type reference data."""
        return json.dumps(
            {
                "memberTypes": [
                    {
                        "type": "MP",
                        "house": 1,
                        "fullTitle": "Member of Parliament",
                        "electedBy": "Constituency election",
                        "represents": "Geographic constituency",
                    },
                    {
                        "type": "Lord",
                        "house": 2,
                        "fullTitle": "Member of the House of Lords",
                        "subtypes": [
                            "Life Peer - Appointed for lifetime",
                            "Hereditary Peer - Inherited (limited to 92)",
                            "Bishop - Lords Spiritual (26 Church of England bishops)",
                        ],
                    },
                ]
            },
            indent=2,
        )

    @mcp.resource("parliament://parties")
    async def parties_resource() -> str:
        """Active political parties in both houses (cached, refreshes every 15 min)."""
        commons_result = await get_result_cached(
            f"{MEMBERS_API_BASE}/Parties/GetActive/1",
            cache_key="resource:parties:commons",
        )
        lords_result = await get_result_cached(
            f"{MEMBERS_API_BASE}/Parties/GetActive/2",
            cache_key="resource:parties:lords",
        )

        # Parse and combine
        commons_data = _safe_parse_data(commons_result)
        lords_data = _safe_parse_data(lords_result)

        return json.dumps(
            {
                "commons": commons_data,
                "lords": lords_data,
            },
            indent=2,
        )

    @mcp.resource("parliament://bill-types")
    async def bill_types_resource() -> str:
        """Bill type reference list (cached, refreshes every 15 min)."""
        result = await get_result_cached(
            f"{BILLS_API_BASE}/BillTypes",
            cache_key="resource:bill-types",
        )
        return _extract_data_str(result)

    @mcp.resource("parliament://bill-stages")
    async def bill_stages_resource() -> str:
        """Legislative stage reference list (cached, refreshes every 15 min)."""
        result = await get_result_cached(
            f"{BILLS_API_BASE}/Stages",
            cache_key="resource:bill-stages",
        )
        return _extract_data_str(result)


def _safe_parse_data(result: str) -> object:
    """Parse a JSON result and extract the data field safely."""
    try:
        parsed = json.loads(result)
        if isinstance(parsed, dict) and "data" in parsed:
            return parsed["data"]
        return parsed
    except (json.JSONDecodeError, TypeError):
        return {"error": "Failed to parse response"}


def _extract_data_str(result: str) -> str:
    """Extract data from a result string and return as JSON string."""
    data = _safe_parse_data(result)
    return json.dumps(data, indent=2, ensure_ascii=False)
