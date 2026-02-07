"""Composite tools that combine multiple API calls for common workflows."""

from __future__ import annotations

import asyncio
import json
from typing import Any

from mcp.server.fastmcp import FastMCP

from uk_parliament_mcp.config import (
    BILLS_API_BASE,
    COMMITTEES_API_BASE,
    COMMONS_VOTES_API_BASE,
    INTERESTS_API_BASE,
    MEMBERS_API_BASE,
)
from uk_parliament_mcp.http_client import build_url, get_result


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
    async def get_mp_profile(member_id: int) -> str:
        """Get comprehensive MP/Lord profile in one call - combines member details, biography, interests, and voting summary | complete MP info, full member profile, MP background, politician details, comprehensive member data | Use when you have a member ID and need a complete picture of an MP or Lord without multiple tool calls | Returns combined data: basic info, biography, registered interests, and recent voting activity

        Args:
            member_id: Parliament member ID. Get from member search first. Example: 4514 (Keir Starmer).

        Returns:
            Combined profile with basic info, biography, interests, and voting summary.
        """
        # Step 1: Fetch member details by ID
        member_url = f"{MEMBERS_API_BASE}/Members/{member_id}"
        member_response = await get_result(member_url)
        member_data = _parse_response(member_response)

        basic_info = member_data.get("value", member_data)
        latest_membership = basic_info.get("latestHouseMembership") or {}
        house = latest_membership.get("house", 1)

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
                    "member": member_url,
                    "biography": biography_url,
                    "interests": interests_url,
                    "voting": voting_url,
                },
            }
        )

    @mcp.tool()
    async def check_mp_vote(member_id: int, topic: str) -> str:
        """Check how an MP voted on a specific topic - combines member lookup and division search | MP voting stance, how did MP vote, voting record on topic, division lookup | Use when you have a member ID and need to know how they voted on a particular issue | Returns MP details and matching divisions with their vote

        Args:
            member_id: Parliament member ID. Get from member search first. Example: 4514 (Keir Starmer).
            topic: Topic or keyword to search for in Commons divisions (e.g., 'climate', 'NHS', 'brexit').

        Returns:
            MP info and divisions matching the topic with the MP's vote.
        """
        # Step 1: Fetch member details and search divisions in parallel
        member_url = f"{MEMBERS_API_BASE}/Members/{member_id}"
        divisions_url = build_url(
            f"{COMMONS_VOTES_API_BASE}/divisions.json/search",
            {
                "queryParameters.searchTerm": topic,
                "memberId": member_id,
            },
        )

        member_response, divisions_response = await asyncio.gather(
            get_result(member_url), get_result(divisions_url)
        )

        member_data = _parse_response(member_response)
        basic_info = member_data.get("value", member_data)
        divisions_data = _parse_response(divisions_response)

        return json.dumps(
            {
                "member_id": member_id,
                "member_info": basic_info,
                "topic_searched": topic,
                "divisions": divisions_data,
                "sources": {"member": member_url, "divisions": divisions_url},
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

    @mcp.tool()
    async def get_my_mp(postcode: str, topic: str | None = None) -> str:
        """Find your MP by postcode and get their full profile - combines postcode lookup, biography, interests, election result, and voting | who is my MP, postcode lookup, constituency MP, local representative | Use when someone wants to find their MP from a postcode | Returns MP profile with constituency, biography, interests, election results, and recent votes

        Args:
            postcode: UK postcode to look up (e.g., 'SW1A 1AA', 'N1 9GU').
            topic: Optional topic keyword to filter votes (e.g., 'climate', 'NHS').

        Returns:
            Combined MP profile with constituency, biography, interests, election result, and voting data.
        """
        # Step 1: Search for MP by postcode (Location parameter)
        search_url = build_url(
            f"{MEMBERS_API_BASE}/Members/Search",
            {
                "Location": postcode,
                "IsCurrentMember": "true",
                "House": 1,
            },
        )
        search_response = await get_result(search_url)
        member_data = _parse_response(search_response)

        member_id = _extract_member_id(member_data)
        if not member_id:
            return json.dumps(
                {
                    "error": f"No current MP found for postcode '{postcode}'",
                    "search_result": member_data,
                }
            )

        basic_info = member_data.get("items", [{}])[0].get("value", {})

        # Step 2: Parallel detail fetches
        biography_url = f"{MEMBERS_API_BASE}/Members/{member_id}/Biography"
        interests_url = f"{INTERESTS_API_BASE}/Interests/?MemberId={member_id}"
        election_url = f"{MEMBERS_API_BASE}/Members/{member_id}/LatestElectionResult"
        voting_url = build_url(
            f"{MEMBERS_API_BASE}/Members/{member_id}/Voting",
            {"house": 1, "page": 1},
        )

        tasks = [
            get_result(biography_url),
            get_result(interests_url),
            get_result(election_url),
            get_result(voting_url),
        ]

        # Optionally search topic-specific votes
        topic_votes_url = None
        if topic:
            topic_votes_url = build_url(
                f"{COMMONS_VOTES_API_BASE}/divisions.json/search",
                {
                    "queryParameters.searchTerm": topic,
                    "memberId": member_id,
                },
            )
            tasks.append(get_result(topic_votes_url))

        results = await asyncio.gather(*tasks)

        biography_response = results[0]
        interests_response = results[1]
        election_response = results[2]
        voting_response = results[3]

        output: dict[str, Any] = {
            "postcode": postcode,
            "member_id": member_id,
            "basic_info": basic_info,
            "biography": _parse_response(biography_response),
            "registered_interests": _parse_response(interests_response),
            "latest_election": _parse_response(election_response),
            "recent_voting": _parse_response(voting_response),
            "sources": {
                "search": search_url,
                "biography": biography_url,
                "interests": interests_url,
                "election": election_url,
                "voting": voting_url,
            },
        }

        if topic and len(results) > 4:
            output["topic_votes"] = _parse_response(results[4])
            output["topic_searched"] = topic
            output["sources"]["topic_votes"] = topic_votes_url

        return json.dumps(output)
