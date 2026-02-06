"""Composite CLI commands that combine multiple API calls."""

from __future__ import annotations

import asyncio
import json
from typing import Any
from urllib.parse import quote

import typer

from uk_parliament_mcp.cli.formatters import OutputFormat
from uk_parliament_mcp.cli.renderers import (
    render_bill_overview,
    render_check_vote,
    render_committee_summary,
    render_mp_profile,
    render_my_mp,
)
from uk_parliament_mcp.cli.utils import echo_utf8, format_output, run_async, should_render_rich
from uk_parliament_mcp.config import (
    BILLS_API_BASE,
    COMMITTEES_API_BASE,
    COMMONS_VOTES_API_BASE,
    INTERESTS_API_BASE,
    MEMBERS_API_BASE,
)
from uk_parliament_mcp.http_client import build_url, get_result

app = typer.Typer(help="High-level composite commands combining multiple API calls", no_args_is_help=True)


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


async def _get_mp_profile_async(name: str) -> str:
    """Get comprehensive MP/Lord profile in one call."""
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
                "search": search_url,
                "biography": biography_url,
                "interests": interests_url,
                "voting": voting_url,
            },
        }
    )


async def _check_mp_vote_async(mp_name: str, topic: str) -> str:
    """Check how an MP voted on a specific topic."""
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


async def _get_bill_overview_async(search_term: str) -> str:
    """Get comprehensive bill overview in one call."""
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


async def _get_committee_summary_async(topic: str) -> str:
    """Get comprehensive committee summary in one call."""
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


@app.command("mp-profile")
def mp_profile(
    name: str = typer.Argument(..., help="Full or partial name of MP or Lord"),
    pretty: bool = typer.Option(False, "--pretty", "-p", help="Pretty-print JSON output"),
    data_only: bool = typer.Option(
        True, "--data-only", "-d", help="Return data only (use --no-data-only for wrapper)"
    ),
    output_format: OutputFormat = typer.Option(
        OutputFormat.AUTO, "--format", "-f", help="Output format: json, table, markdown, csv, auto"
    ),
    raw: bool = typer.Option(False, "--raw", help="Output full wrapper JSON (url + data)"),
    fields: str | None = typer.Option(
        None, "--fields", help="Comma-separated field paths for columns"
    ),
) -> None:
    """
    Get comprehensive MP/Lord profile in one call.

    Combines member search, biography, interests, and voting summary.
    Returns basic info, biography, registered interests, and recent votes.
    """
    result = run_async(_get_mp_profile_async(name))
    if should_render_rich(output_format, raw):
        render_mp_profile(result)
    else:
        echo_utf8(format_output(result, pretty, data_only, output_format, fields, raw))


@app.command("check-vote")
def check_vote(
    mp_name: str = typer.Argument(..., help="Name of MP to look up"),
    topic: str = typer.Argument(..., help="Topic or keyword to search divisions"),
    pretty: bool = typer.Option(False, "--pretty", "-p", help="Pretty-print JSON output"),
    data_only: bool = typer.Option(
        True, "--data-only", "-d", help="Return data only (use --no-data-only for wrapper)"
    ),
    output_format: OutputFormat = typer.Option(
        OutputFormat.AUTO, "--format", "-f", help="Output format: json, table, markdown, csv, auto"
    ),
    raw: bool = typer.Option(False, "--raw", help="Output full wrapper JSON (url + data)"),
    fields: str | None = typer.Option(
        None, "--fields", help="Comma-separated field paths for columns"
    ),
) -> None:
    """
    Check how an MP voted on a specific topic.

    Combines member search and division lookup.
    Returns MP info and divisions on the topic where they voted.
    """
    result = run_async(_check_mp_vote_async(mp_name, topic))
    if should_render_rich(output_format, raw):
        render_check_vote(result)
    else:
        echo_utf8(format_output(result, pretty, data_only, output_format, fields, raw))


@app.command("bill-overview")
def bill_overview(
    search_term: str = typer.Argument(..., help="Search term for bill title or content"),
    pretty: bool = typer.Option(False, "--pretty", "-p", help="Pretty-print JSON output"),
    data_only: bool = typer.Option(
        True, "--data-only", "-d", help="Return data only (use --no-data-only for wrapper)"
    ),
    output_format: OutputFormat = typer.Option(
        OutputFormat.AUTO, "--format", "-f", help="Output format: json, table, markdown, csv, auto"
    ),
    raw: bool = typer.Option(False, "--raw", help="Output full wrapper JSON (url + data)"),
    fields: str | None = typer.Option(
        None, "--fields", help="Comma-separated field paths for columns"
    ),
) -> None:
    """
    Get comprehensive bill overview in one call.

    Combines bill search, details, stages, and publications.
    Returns bill details, legislative stages, and associated documents.
    """
    result = run_async(_get_bill_overview_async(search_term))
    if should_render_rich(output_format, raw):
        render_bill_overview(result)
    else:
        echo_utf8(format_output(result, pretty, data_only, output_format, fields, raw))


@app.command("committee-summary")
def committee_summary(
    topic: str = typer.Argument(..., help="Search term for committee name or subject"),
    pretty: bool = typer.Option(False, "--pretty", "-p", help="Pretty-print JSON output"),
    data_only: bool = typer.Option(
        True, "--data-only", "-d", help="Return data only (use --no-data-only for wrapper)"
    ),
    output_format: OutputFormat = typer.Option(
        OutputFormat.AUTO, "--format", "-f", help="Output format: json, table, markdown, csv, auto"
    ),
    raw: bool = typer.Option(False, "--raw", help="Output full wrapper JSON (url + data)"),
    fields: str | None = typer.Option(
        None, "--fields", help="Comma-separated field paths for columns"
    ),
) -> None:
    """
    Get comprehensive committee summary in one call.

    Combines committee search, details, evidence, and publications.
    Returns committee info, witness testimonies, written submissions, and reports.
    """
    result = run_async(_get_committee_summary_async(topic))
    if should_render_rich(output_format, raw):
        render_committee_summary(result)
    else:
        echo_utf8(format_output(result, pretty, data_only, output_format, fields, raw))


async def _get_my_mp_async(postcode: str, topic: str | None = None) -> str:
    """Find MP by postcode and get their full profile."""
    # Step 1: Search for MP by postcode
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


@app.command("my-mp")
def my_mp(
    postcode: str = typer.Argument(..., help="UK postcode (e.g., 'SW1A 1AA', 'N1 9GU')"),
    votes: str | None = typer.Option(None, "--votes", "-v", help="Filter votes by topic keyword"),
    pretty: bool = typer.Option(False, "--pretty", "-p", help="Pretty-print JSON output"),
    data_only: bool = typer.Option(
        True, "--data-only", "-d", help="Return data only (use --no-data-only for wrapper)"
    ),
    output_format: OutputFormat = typer.Option(
        OutputFormat.AUTO, "--format", "-f", help="Output format: json, table, markdown, csv, auto"
    ),
    raw: bool = typer.Option(False, "--raw", help="Output full wrapper JSON (url + data)"),
    fields: str | None = typer.Option(
        None, "--fields", help="Comma-separated field paths for columns"
    ),
) -> None:
    """
    Find your MP by postcode and get their full profile.

    Looks up constituency from postcode, finds the current MP, and pulls
    their biography, registered interests, latest election result, and
    recent votes. Use --votes to filter votes by topic.
    """
    result = run_async(_get_my_mp_async(postcode, votes))
    if should_render_rich(output_format, raw):
        render_my_mp(result)
    else:
        echo_utf8(format_output(result, pretty, data_only, output_format, fields, raw))
