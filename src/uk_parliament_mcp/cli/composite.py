"""Composite CLI commands that combine multiple API calls."""

from __future__ import annotations

import asyncio
import json
from collections.abc import Callable, Coroutine
from typing import Any
from urllib.parse import quote

import typer

from uk_parliament_mcp.cli.formatters import OutputFormat
from uk_parliament_mcp.cli.renderers import (
    render_bill_committees,
    render_bill_overview,
    render_check_vote,
    render_committee_bills,
    render_committee_summary,
    render_compare_votes,
    render_member_bills,
    render_mp_profile,
    render_my_mp,
    render_search_parliament,
)
from uk_parliament_mcp.cli.utils import echo_utf8, format_output, run_async, should_render_rich
from uk_parliament_mcp.config import (
    BILLS_API_BASE,
    COMMITTEES_API_BASE,
    HOUSE_COMMONS,
    INTERESTS_API_BASE,
    MEMBERS_API_BASE,
)
from uk_parliament_mcp.http_client import build_url, get_result
from uk_parliament_mcp.tools import composite
from uk_parliament_mcp.tools.composite import _extract_member_id, _parse_response

app = typer.Typer(
    help="High-level composite commands combining multiple API calls", no_args_is_help=True
)


async def _get_mp_profile_async(member_id: int) -> str:
    """Get comprehensive MP/Lord profile in one call."""
    # Step 1: Fetch member directly by ID
    member_url = f"{MEMBERS_API_BASE}/Members/{member_id}"
    member_response = await get_result(member_url)
    member_data = _parse_response(member_response)

    basic_info = member_data.get("value", {})
    latest_membership = basic_info.get("latestHouseMembership") or {}
    house = latest_membership.get("house", 1)

    # Step 2: Parallel requests for details
    biography_url = f"{MEMBERS_API_BASE}/Members/{member_id}/Biography"
    interests_url = f"{INTERESTS_API_BASE}/Interests/?MemberId={member_id}"
    voting_url = build_url(
        f"{MEMBERS_API_BASE}/Members/{member_id}/Voting", {"house": house, "page": 1}
    )

    biography_response, interests_response, voting_response = await asyncio.gather(
        get_result(biography_url), get_result(interests_url), get_result(voting_url)
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


async def _check_mp_vote_async(member_id: int, topic: str, take: int = 25) -> str:
    """Check how a member voted on a specific topic (in whichever House they sit)."""
    return json.dumps(await composite.check_member_votes(member_id, topic, take))


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
    member_id: int = typer.Argument(..., help="Parliament member ID (e.g., 4514)"),
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

    Combines member details, biography, interests, and voting summary.
    Returns basic info, biography, registered interests, and recent votes.
    """
    result = run_async(_get_mp_profile_async(member_id))
    if should_render_rich(output_format, raw):
        render_mp_profile(result)
    else:
        echo_utf8(format_output(result, pretty, data_only, output_format, fields, raw))


@app.command("check-vote")
def check_vote(
    member_id: int = typer.Argument(..., help="Parliament member ID (e.g., 4514)"),
    topic: str = typer.Argument(..., help="Topic or keyword to search divisions"),
    take: int = typer.Option(25, "--take", "-n", help="Number of divisions to return"),
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
    Check how an MP or Lord voted on a specific topic.

    Looks up the member, then their votes in their own House on divisions
    matching the topic: Aye/No (Commons) or Content/Not Content (Lords).
    """
    result = run_async(_check_mp_vote_async(member_id, topic, take))
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
        topic_votes_url = composite.member_voting_url(member_id, HOUSE_COMMONS, topic)
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
        output["topic_votes"] = composite.normalise_member_votes(_parse_response(results[4]))
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


async def _as_json(coro: Coroutine[Any, Any, dict[str, Any]]) -> str:
    return json.dumps(await coro)


def _emit(
    result: str,
    renderer: Callable[[str], None],
    pretty: bool,
    data_only: bool,
    output_format: OutputFormat,
    fields: str | None,
    raw: bool,
) -> None:
    if should_render_rich(output_format, raw):
        renderer(result)
    else:
        echo_utf8(format_output(result, pretty, data_only, output_format, fields, raw))


_PRETTY = typer.Option(False, "--pretty", "-p", help="Pretty-print JSON output")
_DATA_ONLY = typer.Option(
    True, "--data-only", "-d", help="Return data only (use --no-data-only for wrapper)"
)
_FORMAT = typer.Option(
    OutputFormat.AUTO, "--format", "-f", help="Output format: json, table, markdown, csv, auto"
)
_RAW = typer.Option(False, "--raw", help="Output full wrapper JSON (url + data)")
_FIELDS = typer.Option(None, "--fields", help="Comma-separated field paths for columns")


@app.command("compare-votes")
def compare_votes(
    member_id_a: int = typer.Argument(..., help="First member ID (e.g., 4514)"),
    member_id_b: int = typer.Argument(..., help="Second member ID, same House (e.g., 172)"),
    topic: str | None = typer.Option(None, "--topic", "-t", help="Only divisions on this topic"),
    take: int = typer.Option(50, "--take", "-n", help="Recent divisions per member to compare"),
    pretty: bool = _PRETTY,
    data_only: bool = _DATA_ONLY,
    output_format: OutputFormat = _FORMAT,
    raw: bool = _RAW,
    fields: str | None = _FIELDS,
) -> None:
    """
    Compare how two MPs (or two Lords) voted, division by division.

    Shows how often they agreed and each division both voted in.
    """
    result = run_async(_as_json(composite.compare_votes(member_id_a, member_id_b, topic, take)))
    _emit(result, render_compare_votes, pretty, data_only, output_format, fields, raw)


@app.command("member-bills")
def member_bills(
    member_id: int = typer.Argument(..., help="Parliament member ID (e.g., 4514)"),
    take: int = typer.Option(20, "--take", "-n", help="Number of bills to return"),
    pretty: bool = _PRETTY,
    data_only: bool = _DATA_ONLY,
    output_format: OutputFormat = _FORMAT,
    raw: bool = _RAW,
    fields: str | None = _FIELDS,
) -> None:
    """
    List the bills a member has sponsored, most recently updated first.
    """
    result = run_async(_as_json(composite.member_bills(member_id, take)))
    _emit(result, render_member_bills, pretty, data_only, output_format, fields, raw)


@app.command("bill-committees")
def bill_committees(
    bill_id: int = typer.Argument(..., help="Bill ID (e.g., 3764)"),
    pretty: bool = _PRETTY,
    data_only: bool = _DATA_ONLY,
    output_format: OutputFormat = _FORMAT,
    raw: bool = _RAW,
    fields: str | None = _FIELDS,
) -> None:
    """
    Find the committees that examined a bill.

    Shows the bill's committee stages and select committee business on it.
    """
    result = run_async(_as_json(composite.bill_committees(bill_id)))
    _emit(result, render_bill_committees, pretty, data_only, output_format, fields, raw)


@app.command("committee-bills")
def committee_bills(
    committee_id: int = typer.Argument(..., help="Committee ID (e.g., 172)"),
    take: int = typer.Option(10, "--take", "-n", help="Number of scrutiny items (max 20)"),
    pretty: bool = _PRETTY,
    data_only: bool = _DATA_ONLY,
    output_format: OutputFormat = _FORMAT,
    raw: bool = _RAW,
    fields: str | None = _FIELDS,
) -> None:
    """
    Find the bills a committee has examined (its legislative scrutiny).
    """
    result = run_async(_as_json(composite.committee_bills(committee_id, take)))
    _emit(result, render_committee_bills, pretty, data_only, output_format, fields, raw)


@app.command("search")
def search(
    query: str = typer.Argument(..., help="Search text (e.g., 'renters rights')"),
    take: int = typer.Option(5, "--take", "-n", help="Top matches per kind of record"),
    pretty: bool = _PRETTY,
    data_only: bool = _DATA_ONLY,
    output_format: OutputFormat = _FORMAT,
    raw: bool = _RAW,
    fields: str | None = _FIELDS,
) -> None:
    """
    Search members, bills, committees, Hansard and written questions at once.
    """
    result = run_async(_as_json(composite.search_everything(query, take)))
    _emit(result, render_search_parliament, pretty, data_only, output_format, fields, raw)
