"""Votes CLI commands for Commons and Lords divisions."""

from __future__ import annotations

import typer

from uk_parliament_mcp.cli.formatters import OutputFormat
from uk_parliament_mcp.cli.utils import (
    DataOnlyOpt,
    FieldsOpt,
    FormatOpt,
    PrettyOpt,
    RawOpt,
    echo_utf8,
    format_output,
    run_async,
)
from uk_parliament_mcp.config import (
    COMMONS_VOTES_API_BASE,
    HOUSE_COMMONS,
    HOUSE_LORDS,
    LORDS_VOTES_API_BASE,
)
from uk_parliament_mcp.http_client import build_url, get_result

app = typer.Typer(help="Commons and Lords voting records and divisions", no_args_is_help=True)


def _validate_house(house: int) -> None:
    """Validate house parameter, raising typer.Exit on invalid value."""
    if house not in (HOUSE_COMMONS, HOUSE_LORDS):
        typer.echo(f"Invalid house value: {house}. Use 1 for Commons or 2 for Lords.")
        raise typer.Exit(code=1)


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
    pretty: PrettyOpt = False,
    data_only: DataOnlyOpt = True,
    output_format: FormatOpt = OutputFormat.AUTO,
    raw: RawOpt = False,
    fields: FieldsOpt = None,
) -> None:
    """
    Search voting divisions in Commons or Lords.

    Search for divisions by topic (e.g., 'brexit', 'climate', 'NHS').
    Use --house flag to specify Commons (1) or Lords (2).
    """
    _validate_house(house)
    if house == HOUSE_COMMONS:
        url = build_url(
            f"{COMMONS_VOTES_API_BASE}/divisions.json/search",
            {
                "queryParameters.searchTerm": search_term,
                "memberId": member_id,
                "queryParameters.startDate": start_date,
                "queryParameters.endDate": end_date,
                "queryParameters.divisionNumber": division_number,
                "queryParameters.includeWhenMemberWasTeller": include_when_member_was_teller,
                "queryParameters.skip": skip,
                "queryParameters.take": take,
            },
        )
    else:
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

    result = run_async(get_result(url))
    echo_utf8(format_output(result, pretty, data_only, output_format, fields, raw))


@app.command("get-division")
def get_division(
    division_id: int = typer.Argument(..., help="Division ID"),
    house: int = typer.Option(
        HOUSE_COMMONS,
        "--house",
        "-h",
        help="House to query (1=Commons, 2=Lords)",
    ),
    pretty: PrettyOpt = False,
    data_only: DataOnlyOpt = True,
    output_format: FormatOpt = OutputFormat.AUTO,
    raw: RawOpt = False,
    fields: FieldsOpt = None,
) -> None:
    """
    Get detailed information about a specific division.

    Returns complete division details including who voted for/against and vote totals.
    """
    _validate_house(house)
    if house == HOUSE_COMMONS:
        url = f"{COMMONS_VOTES_API_BASE}/division/{division_id}.json"
    else:
        url = f"{LORDS_VOTES_API_BASE}/Divisions/{division_id}"

    result = run_async(get_result(url))
    echo_utf8(format_output(result, pretty, data_only, output_format, fields, raw))


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
        None, "--include-teller", help="Include when member was a teller"
    ),
    start_date: str | None = typer.Option(None, "--start-date", help="Start date (YYYY-MM-DD)"),
    end_date: str | None = typer.Option(None, "--end-date", help="End date (YYYY-MM-DD)"),
    division_number: int | None = typer.Option(
        None, "--division-number", help="Specific division number"
    ),
    skip: int = typer.Option(0, "--skip", help="Number of records to skip (pagination)"),
    take: int = typer.Option(25, "--take", help="Number of records to return"),
    pretty: PrettyOpt = False,
    data_only: DataOnlyOpt = True,
    output_format: FormatOpt = OutputFormat.AUTO,
    raw: RawOpt = False,
    fields: FieldsOpt = None,
) -> None:
    """
    Get complete voting record for a member.

    Returns all votes cast by the specified member in Commons or Lords divisions.
    """
    _validate_house(house)
    if house == HOUSE_COMMONS:
        url = build_url(
            f"{COMMONS_VOTES_API_BASE}/divisions.json/membervoting",
            {
                "queryParameters.memberId": member_id,
                "queryParameters.searchTerm": search_term,
                "queryParameters.includeWhenMemberWasTeller": include_when_member_was_teller,
                "queryParameters.startDate": start_date,
                "queryParameters.endDate": end_date,
                "queryParameters.divisionNumber": division_number,
                "queryParameters.skip": skip,
                "queryParameters.take": take,
            },
        )
    else:
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

    result = run_async(get_result(url))
    echo_utf8(format_output(result, pretty, data_only, output_format, fields, raw))


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
    pretty: PrettyOpt = False,
    data_only: DataOnlyOpt = True,
    output_format: FormatOpt = OutputFormat.AUTO,
    raw: RawOpt = False,
    fields: FieldsOpt = None,
) -> None:
    """
    Get divisions grouped by party voting patterns.

    Shows how different parties voted on issues. Useful for analyzing party-line voting behavior.
    """
    _validate_house(house)
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
    else:
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

    result = run_async(get_result(url))
    echo_utf8(format_output(result, pretty, data_only, output_format, fields, raw))


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
    pretty: PrettyOpt = False,
    data_only: DataOnlyOpt = True,
    output_format: FormatOpt = OutputFormat.AUTO,
    raw: RawOpt = False,
    fields: FieldsOpt = None,
) -> None:
    """
    Get total count of divisions matching search criteria.

    Useful for knowing how many results a search will return before retrieving them.
    """
    _validate_house(house)
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
    else:
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

    result = run_async(get_result(url))
    echo_utf8(format_output(result, pretty, data_only, output_format, fields, raw))
