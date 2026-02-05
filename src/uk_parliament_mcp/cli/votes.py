"""Votes CLI commands for Commons and Lords divisions."""

from __future__ import annotations

import typer

from uk_parliament_mcp.cli.formatters import OutputFormat
from uk_parliament_mcp.cli.utils import echo_utf8, format_output, run_async
from uk_parliament_mcp.config import (
    COMMONS_VOTES_API_BASE,
    HOUSE_COMMONS,
    HOUSE_LORDS,
    LORDS_VOTES_API_BASE,
)
from uk_parliament_mcp.http_client import build_url, get_result

app = typer.Typer(help="Commons and Lords voting records and divisions")


@app.command("search")
def search_divisions(
    search_term: str = typer.Argument(..., help="Search term for division topics"),
    house: int = typer.Option(
        HOUSE_COMMONS,
        "--house",
        "-h",
        help="House to search (1=Commons, 2=Lords)",
    ),
    member_id: int | None = typer.Option(None, "--member-id", "-m", help="Filter by member ID"),
    start_date: str | None = typer.Option(None, "--start-date", help="Start date (YYYY-MM-DD)"),
    end_date: str | None = typer.Option(None, "--end-date", help="End date (YYYY-MM-DD)"),
    division_number: int | None = typer.Option(
        None, "--division-number", help="Specific division number"
    ),
    include_when_member_was_teller: bool | None = typer.Option(
        None, "--include-teller", help="Include when member was a teller"
    ),
    skip: int = typer.Option(0, "--skip", help="Number of records to skip (pagination)"),
    take: int = typer.Option(25, "--take", help="Number of records to return"),
    pretty: bool = typer.Option(False, "--pretty", "-p", help="Pretty-print JSON output"),
    data_only: bool = typer.Option(False, "--data-only", "-d", help="Return data only"),
    output_format: OutputFormat = typer.Option(
        OutputFormat.JSON, "--format", "-f", help="Output format: json, table, markdown"
    ),
) -> None:
    """
    Search voting divisions in Commons or Lords.

    Search for divisions by topic (e.g., 'brexit', 'climate', 'NHS').
    Use --house flag to specify Commons (1) or Lords (2).
    """
    if house == HOUSE_COMMONS:
        url = build_url(
            f"{COMMONS_VOTES_API_BASE}/divisions.json/search",
            {
                "queryParameters.searchTerm": search_term,
                "memberId": member_id,
                "queryParameters.startDate": start_date,
                "queryParameters.endDate": end_date,
                "queryParameters.divisionNumber": division_number,
            },
        )
    elif house == HOUSE_LORDS:
        url = build_url(
            f"{LORDS_VOTES_API_BASE}/Divisions/search",
            {
                "SearchTerm": search_term,
                "MemberId": member_id,
                "StartDate": start_date,
                "EndDate": end_date,
                "DivisionNumber": division_number,
                "IncludeWhenMemberWasTeller": include_when_member_was_teller,
                "skip": skip,
                "take": take,
            },
        )
    else:
        typer.echo(f"Invalid house value: {house}. Use 1 for Commons or 2 for Lords.")
        raise typer.Exit(code=1)

    result = run_async(get_result(url))
    echo_utf8(format_output(result, pretty, data_only, output_format))


@app.command("get-division")
def get_division(
    division_id: int = typer.Argument(..., help="Division ID"),
    house: int = typer.Option(
        HOUSE_COMMONS,
        "--house",
        "-h",
        help="House to query (1=Commons, 2=Lords)",
    ),
    pretty: bool = typer.Option(False, "--pretty", "-p", help="Pretty-print JSON output"),
    data_only: bool = typer.Option(False, "--data-only", "-d", help="Return data only"),
    output_format: OutputFormat = typer.Option(
        OutputFormat.JSON, "--format", "-f", help="Output format: json, table, markdown"
    ),
) -> None:
    """
    Get detailed information about a specific division.

    Returns complete division details including who voted for/against and vote totals.
    """
    if house == HOUSE_COMMONS:
        url = f"{COMMONS_VOTES_API_BASE}/division/{division_id}.json"
    elif house == HOUSE_LORDS:
        url = f"{LORDS_VOTES_API_BASE}/Divisions/{division_id}"
    else:
        typer.echo(f"Invalid house value: {house}. Use 1 for Commons or 2 for Lords.")
        raise typer.Exit(code=1)

    result = run_async(get_result(url))
    echo_utf8(format_output(result, pretty, data_only, output_format))


@app.command("member-voting")
def get_member_voting_record(
    member_id: int = typer.Argument(..., help="Member ID"),
    house: int = typer.Option(
        HOUSE_COMMONS,
        "--house",
        "-h",
        help="House to query (1=Commons, 2=Lords)",
    ),
    search_term: str | None = typer.Option(
        None, "--search-term", help="Search term to filter divisions"
    ),
    include_when_member_was_teller: bool | None = typer.Option(
        None, "--include-teller", help="Include when member was a teller (Lords only)"
    ),
    start_date: str | None = typer.Option(
        None, "--start-date", help="Start date (YYYY-MM-DD, Lords only)"
    ),
    end_date: str | None = typer.Option(
        None, "--end-date", help="End date (YYYY-MM-DD, Lords only)"
    ),
    division_number: int | None = typer.Option(
        None, "--division-number", help="Specific division number (Lords only)"
    ),
    skip: int = typer.Option(0, "--skip", help="Number of records to skip (Lords only)"),
    take: int = typer.Option(25, "--take", help="Number of records to return (Lords only)"),
    pretty: bool = typer.Option(False, "--pretty", "-p", help="Pretty-print JSON output"),
    data_only: bool = typer.Option(False, "--data-only", "-d", help="Return data only"),
    output_format: OutputFormat = typer.Option(
        OutputFormat.JSON, "--format", "-f", help="Output format: json, table, markdown"
    ),
) -> None:
    """
    Get complete voting record for a member.

    Returns all votes cast by the specified member in Commons or Lords divisions.
    """
    if house == HOUSE_COMMONS:
        url = f"{COMMONS_VOTES_API_BASE}/divisions.json/membervoting?queryParameters.memberId={member_id}"
    elif house == HOUSE_LORDS:
        url = build_url(
            f"{LORDS_VOTES_API_BASE}/Divisions/membervoting",
            {
                "MemberId": member_id,
                "SearchTerm": search_term,
                "IncludeWhenMemberWasTeller": include_when_member_was_teller,
                "StartDate": start_date,
                "EndDate": end_date,
                "DivisionNumber": division_number,
                "skip": skip,
                "take": take,
            },
        )
    else:
        typer.echo(f"Invalid house value: {house}. Use 1 for Commons or 2 for Lords.")
        raise typer.Exit(code=1)

    result = run_async(get_result(url))
    echo_utf8(format_output(result, pretty, data_only, output_format))


@app.command("grouped-by-party")
def get_divisions_grouped_by_party(
    house: int = typer.Option(
        HOUSE_COMMONS,
        "--house",
        "-h",
        help="House to query (1=Commons, 2=Lords)",
    ),
    search_term: str | None = typer.Option(
        None, "--search-term", help="Search term to filter divisions"
    ),
    member_id: int | None = typer.Option(None, "--member-id", "-m", help="Filter by member ID"),
    start_date: str | None = typer.Option(None, "--start-date", help="Start date (YYYY-MM-DD)"),
    end_date: str | None = typer.Option(None, "--end-date", help="End date (YYYY-MM-DD)"),
    division_number: int | None = typer.Option(
        None, "--division-number", help="Specific division number"
    ),
    include_when_member_was_teller: bool | None = typer.Option(
        None, "--include-teller", help="Include when member was a teller"
    ),
    pretty: bool = typer.Option(False, "--pretty", "-p", help="Pretty-print JSON output"),
    data_only: bool = typer.Option(False, "--data-only", "-d", help="Return data only"),
    output_format: OutputFormat = typer.Option(
        OutputFormat.JSON, "--format", "-f", help="Output format: json, table, markdown"
    ),
) -> None:
    """
    Get divisions grouped by party voting patterns.

    Shows how different parties voted on issues. Useful for analyzing party-line voting behavior.
    """
    if house == HOUSE_COMMONS:
        url = build_url(
            f"{COMMONS_VOTES_API_BASE}/divisions.json/groupedbyparty",
            {
                "queryParameters.searchTerm": search_term,
                "queryParameters.memberId": member_id,
                "queryParameters.startDate": start_date,
                "queryParameters.endDate": end_date,
                "queryParameters.divisionNumber": division_number,
                "queryParameters.includeWhenMemberWasTeller": include_when_member_was_teller,
            },
        )
    elif house == HOUSE_LORDS:
        url = build_url(
            f"{LORDS_VOTES_API_BASE}/Divisions/groupedbyparty",
            {
                "SearchTerm": search_term,
                "MemberId": member_id,
                "StartDate": start_date,
                "EndDate": end_date,
                "DivisionNumber": division_number,
                "IncludeWhenMemberWasTeller": include_when_member_was_teller,
            },
        )
    else:
        typer.echo(f"Invalid house value: {house}. Use 1 for Commons or 2 for Lords.")
        raise typer.Exit(code=1)

    result = run_async(get_result(url))
    echo_utf8(format_output(result, pretty, data_only, output_format))


@app.command("search-count")
def get_divisions_search_count(
    house: int = typer.Option(
        HOUSE_COMMONS,
        "--house",
        "-h",
        help="House to query (1=Commons, 2=Lords)",
    ),
    search_term: str | None = typer.Option(
        None, "--search-term", help="Search term to filter divisions"
    ),
    member_id: int | None = typer.Option(None, "--member-id", "-m", help="Filter by member ID"),
    start_date: str | None = typer.Option(None, "--start-date", help="Start date (YYYY-MM-DD)"),
    end_date: str | None = typer.Option(None, "--end-date", help="End date (YYYY-MM-DD)"),
    division_number: int | None = typer.Option(
        None, "--division-number", help="Specific division number"
    ),
    include_when_member_was_teller: bool | None = typer.Option(
        None, "--include-teller", help="Include when member was a teller"
    ),
    pretty: bool = typer.Option(False, "--pretty", "-p", help="Pretty-print JSON output"),
    data_only: bool = typer.Option(False, "--data-only", "-d", help="Return data only"),
    output_format: OutputFormat = typer.Option(
        OutputFormat.JSON, "--format", "-f", help="Output format: json, table, markdown"
    ),
) -> None:
    """
    Get total count of divisions matching search criteria.

    Useful for knowing how many results a search will return before retrieving them.
    """
    if house == HOUSE_COMMONS:
        url = build_url(
            f"{COMMONS_VOTES_API_BASE}/divisions.json/searchTotalResults",
            {
                "queryParameters.searchTerm": search_term,
                "queryParameters.memberId": member_id,
                "queryParameters.startDate": start_date,
                "queryParameters.endDate": end_date,
                "queryParameters.divisionNumber": division_number,
                "queryParameters.includeWhenMemberWasTeller": include_when_member_was_teller,
            },
        )
    elif house == HOUSE_LORDS:
        url = build_url(
            f"{LORDS_VOTES_API_BASE}/Divisions/searchTotalResults",
            {
                "SearchTerm": search_term,
                "MemberId": member_id,
                "StartDate": start_date,
                "EndDate": end_date,
                "DivisionNumber": division_number,
                "IncludeWhenMemberWasTeller": include_when_member_was_teller,
            },
        )
    else:
        typer.echo(f"Invalid house value: {house}. Use 1 for Commons or 2 for Lords.")
        raise typer.Exit(code=1)

    result = run_async(get_result(url))
    echo_utf8(format_output(result, pretty, data_only, output_format))
