"""Composite tools that combine multiple API calls for common workflows."""

from __future__ import annotations

import asyncio
import json
from typing import Any

from mcp.server.fastmcp import FastMCP

from uk_parliament_mcp.http_client import build_url, get_result

# API bases
MEMBERS_API_BASE = "https://members-api.parliament.uk/api"
BILLS_API_BASE = "https://bills-api.parliament.uk/api/v1"
COMMONS_VOTES_API_BASE = "http://commonsvotes-api.parliament.uk/data"
COMMITTEES_API_BASE = "https://committees-api.parliament.uk/api"
INTERESTS_API_BASE = "https://interests-api.parliament.uk/api/v1"


def _parse_response(response: str) -> dict[str, Any]:
    """Parse JSON response and extract data."""
    try:
        parsed: dict[str, Any] = json.loads(response)
        if "data" in parsed:
            # Data is a JSON string, parse it
            data = parsed["data"]
            if isinstance(data, str):
                result: dict[str, Any] = json.loads(data)
                return result
            return dict(data) if isinstance(data, dict) else {"data": data}
        return parsed
    except (json.JSONDecodeError, TypeError):
        return {"error": "Failed to parse response"}


def _extract_member_id(member_response: dict[str, Any]) -> int | None:
    """Extract member_id from member search response."""
    try:
        items = member_response.get("items", [])
        if items:
            member_id = items[0].get("value", {}).get("id")
            if isinstance(member_id, int):
                return member_id
    except (KeyError, IndexError, TypeError):
        pass
    return None


def register_tools(mcp: FastMCP) -> None:
    """Register composite tools with the MCP server."""

    @mcp.tool()
    async def get_mp_profile(name: str) -> str:
        """Get comprehensive MP/Lord profile in one call - combines search, details, biography, interests, and voting summary | complete MP info, full member profile, MP background, politician details, comprehensive member data | Use when you need a complete picture of an MP or Lord without multiple tool calls | Returns combined data: basic info, biography, registered interests, and recent voting activity

        Args:
            name: Full or partial name of the MP or Lord to look up (e.g., 'Keir Starmer', 'Boris Johnson').

        Returns:
            Combined profile with basic info, biography, interests, and voting summary.
        """
        from urllib.parse import quote

        # Step 1: Search for member
        search_url = f"{MEMBERS_API_BASE}/Members/Search?Name={quote(name)}"
        search_response = await get_result(search_url)
        member_data = _parse_response(search_response)

        member_id = _extract_member_id(member_data)
        if not member_id:
            return json.dumps(
                {"error": f"No member found matching '{name}'", "search_result": member_data}
            )

        # Get basic info from search result
        basic_info = member_data.get("items", [{}])[0].get("value", {})
        house = 1 if basic_info.get("latestHouseMembership", {}).get("house") == 1 else 2

        # Step 2: Parallel requests for details
        biography_url = f"{MEMBERS_API_BASE}/Members/{member_id}/Biography"
        interests_url = f"{INTERESTS_API_BASE}/Interests/?MemberId={member_id}"
        voting_url = build_url(
            f"{MEMBERS_API_BASE}/Members/{member_id}/Voting", {"house": house, "page": 1}
        )

        biography_task = get_result(biography_url)
        interests_task = get_result(interests_url)
        voting_task = get_result(voting_url)

        biography_response, interests_response, voting_response = await asyncio.gather(
            biography_task, interests_task, voting_task
        )

        return json.dumps(
            {
                "member_id": member_id,
                "basic_info": basic_info,
                "biography": _parse_response(biography_response),
                "registered_interests": _parse_response(interests_response),
                "recent_voting": _parse_response(voting_response),
                "sources": {
                    "search": search_url,
                    "biography": biography_url,
                    "interests": interests_url,
                    "voting": voting_url,
                },
            }
        )

    @mcp.tool()
    async def check_mp_vote(mp_name: str, topic: str) -> str:
        """Check how an MP voted on a specific topic - combines member search and division lookup | MP voting stance, how did MP vote, voting record on topic, division lookup | Use when you need to know how a specific MP voted on a particular issue | Returns MP details and matching divisions with their vote

        Args:
            mp_name: Name of the MP to look up (e.g., 'Boris Johnson', 'Keir Starmer').
            topic: Topic or keyword to search for in Commons divisions (e.g., 'climate', 'NHS', 'brexit').

        Returns:
            MP info and divisions matching the topic with the MP's vote.
        """
        from urllib.parse import quote

        # Step 1: Search for member
        search_url = f"{MEMBERS_API_BASE}/Members/Search?Name={quote(mp_name)}"
        search_response = await get_result(search_url)
        member_data = _parse_response(search_response)

        member_id = _extract_member_id(member_data)
        if not member_id:
            return json.dumps(
                {"error": f"No member found matching '{mp_name}'", "search_result": member_data}
            )

        basic_info = member_data.get("items", [{}])[0].get("value", {})

        # Step 2: Search for divisions on topic with this member
        divisions_url = build_url(
            f"{COMMONS_VOTES_API_BASE}/divisions.json/search",
            {
                "queryParameters.searchTerm": topic,
                "memberId": member_id,
            },
        )
        divisions_response = await get_result(divisions_url)
        divisions_data = _parse_response(divisions_response)

        return json.dumps(
            {
                "member_id": member_id,
                "member_info": basic_info,
                "topic_searched": topic,
                "divisions": divisions_data,
                "sources": {"member_search": search_url, "divisions": divisions_url},
            }
        )

    @mcp.tool()
    async def get_bill_overview(search_term: str) -> str:
        """Get comprehensive bill overview in one call - combines search, details, stages, and publications | complete bill info, legislation overview, bill progress, full bill details | Use when you need complete information about a bill without multiple tool calls | Returns bill details, legislative stages, and associated publications

        Args:
            search_term: Search term for bill title or content (e.g., 'Online Safety', 'Environment', 'Finance').

        Returns:
            Combined bill data: details, stages, and publications.
        """
        from urllib.parse import quote

        # Step 1: Search for bills
        search_url = f"{BILLS_API_BASE}/Bills?SearchTerm={quote(search_term)}"
        search_response = await get_result(search_url)
        bills_data = _parse_response(search_response)

        items = bills_data.get("items", [])
        if not items:
            return json.dumps(
                {"error": f"No bills found matching '{search_term}'", "search_result": bills_data}
            )

        # Get first matching bill
        bill = items[0]
        bill_id = bill.get("billId")
        if not bill_id:
            return json.dumps({"error": "Could not extract bill ID", "search_result": bills_data})

        # Step 2: Parallel requests for details, stages, publications
        details_url = f"{BILLS_API_BASE}/Bills/{bill_id}"
        stages_url = f"{BILLS_API_BASE}/Bills/{bill_id}/Stages"
        publications_url = f"{BILLS_API_BASE}/Bills/{bill_id}/Publications"

        details_task = get_result(details_url)
        stages_task = get_result(stages_url)
        publications_task = get_result(publications_url)

        details_response, stages_response, publications_response = await asyncio.gather(
            details_task, stages_task, publications_task
        )

        return json.dumps(
            {
                "bill_id": bill_id,
                "search_summary": bill,
                "details": _parse_response(details_response),
                "stages": _parse_response(stages_response),
                "publications": _parse_response(publications_response),
                "other_matches": len(items) - 1,
                "sources": {
                    "search": search_url,
                    "details": details_url,
                    "stages": stages_url,
                    "publications": publications_url,
                },
            }
        )

    @mcp.tool()
    async def get_committee_summary(topic: str) -> str:
        """Get comprehensive committee summary in one call - combines search, details, evidence, and publications | complete committee info, inquiry overview, committee research, full committee details | Use when you need complete information about a committee's work without multiple tool calls | Returns committee details, oral/written evidence, and publications

        Args:
            topic: Search term for committee name or subject area (e.g., 'Treasury', 'Health', 'Defence').

        Returns:
            Combined committee data: details, evidence, and publications.
        """
        from urllib.parse import quote

        # Step 1: Search for committees
        search_url = f"{COMMITTEES_API_BASE}/Committees?SearchTerm={quote(topic)}"
        search_response = await get_result(search_url)
        committees_data = _parse_response(search_response)

        items = committees_data.get("items", [])
        if not items:
            return json.dumps(
                {
                    "error": f"No committees found matching '{topic}'",
                    "search_result": committees_data,
                }
            )

        # Get first matching committee
        committee = items[0]
        committee_id = committee.get("id")
        if not committee_id:
            return json.dumps(
                {"error": "Could not extract committee ID", "search_result": committees_data}
            )

        # Step 2: Parallel requests for details, evidence, publications
        details_url = f"{COMMITTEES_API_BASE}/Committees/{committee_id}"
        oral_evidence_url = build_url(
            f"{COMMITTEES_API_BASE}/OralEvidence", {"CommitteeId": committee_id, "Take": 10}
        )
        written_evidence_url = build_url(
            f"{COMMITTEES_API_BASE}/WrittenEvidence", {"CommitteeId": committee_id, "Take": 10}
        )
        publications_url = build_url(
            f"{COMMITTEES_API_BASE}/Publications", {"CommitteeId": committee_id, "Take": 10}
        )

        details_task = get_result(details_url)
        oral_task = get_result(oral_evidence_url)
        written_task = get_result(written_evidence_url)
        publications_task = get_result(publications_url)

        (
            details_response,
            oral_response,
            written_response,
            publications_response,
        ) = await asyncio.gather(details_task, oral_task, written_task, publications_task)

        return json.dumps(
            {
                "committee_id": committee_id,
                "search_summary": committee,
                "details": _parse_response(details_response),
                "oral_evidence": _parse_response(oral_response),
                "written_evidence": _parse_response(written_response),
                "publications": _parse_response(publications_response),
                "other_matches": len(items) - 1,
                "sources": {
                    "search": search_url,
                    "details": details_url,
                    "oral_evidence": oral_evidence_url,
                    "written_evidence": written_evidence_url,
                    "publications": publications_url,
                },
            }
        )
