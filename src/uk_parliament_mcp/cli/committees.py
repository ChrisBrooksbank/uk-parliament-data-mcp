"""Committees CLI commands for committee info, meetings, and evidence."""

from __future__ import annotations

from urllib.parse import quote

import typer

from uk_parliament_mcp.cli.formatters import OutputFormat
from uk_parliament_mcp.cli.pagination import COMMITTEES_PAGINATION, paginate_request
from uk_parliament_mcp.cli.utils import echo_utf8, format_output, run_async
from uk_parliament_mcp.config import COMMITTEES_API_BASE
from uk_parliament_mcp.http_client import build_url, get_result

app = typer.Typer(help="Committee information, meetings, and evidence")


@app.command("meetings")
def get_meetings(
    from_date: str = typer.Argument(..., help="Start date (YYYY-MM-DD)"),
    to_date: str = typer.Argument(..., help="End date (YYYY-MM-DD)"),
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
    Find committee meetings and hearings by date range.

    Get committee schedules, planning attendance, or research past committee activity.
    Covers both Commons and Lords committees.
    """
    url = f"{COMMITTEES_API_BASE}/Broadcast/Meetings?FromDate={quote(from_date)}&ToDate={quote(to_date)}"
    result = run_async(get_result(url))
    echo_utf8(format_output(result, pretty, data_only, output_format, fields, raw))


@app.command("search")
def search_committees(
    search_term: str = typer.Argument(..., help="Search term for committee names or subject areas"),
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
    Search for parliamentary committees by name or subject area.

    Use when you need to find which committee covers a specific policy area
    or when researching committee work (e.g., 'Treasury', 'Health', 'Defence').
    """
    url = f"{COMMITTEES_API_BASE}/Committees?SearchTerm={quote(search_term)}"
    result = run_async(get_result(url))
    echo_utf8(format_output(result, pretty, data_only, output_format, fields, raw))


@app.command("types")
def get_types(
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
    Get all types of parliamentary committees.

    Returns committee types like Select Committee, Public Bill Committee,
    Delegated Legislation Committee, etc.
    """
    url = f"{COMMITTEES_API_BASE}/CommitteeType"
    result = run_async(get_result(url))
    echo_utf8(format_output(result, pretty, data_only, output_format, fields, raw))


@app.command("get")
def get_committee(
    committee_id: int = typer.Argument(..., help="Committee ID"),
    include_banners: bool = typer.Option(False, "--banners", help="Include banner images"),
    show_on_website_only: bool = typer.Option(
        True, "--website-only/--all", help="Show only public committees"
    ),
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
    Get comprehensive committee profile and membership details.

    Returns full committee details including purpose, members, departments
    scrutinized, and contact information.
    """
    url = build_url(
        f"{COMMITTEES_API_BASE}/Committees/{committee_id}",
        {
            "includeBanners": include_banners,
            "showOnWebsiteOnly": show_on_website_only,
        },
    )
    result = run_async(get_result(url))
    echo_utf8(format_output(result, pretty, data_only, output_format, fields, raw))


@app.command("events")
def get_events(
    committee_id: int | None = typer.Option(None, "--committee-id", help="Filter by committee ID"),
    committee_business_id: int | None = typer.Option(
        None, "--business-id", help="Filter by business ID"
    ),
    search_term: str | None = typer.Option(None, "--search", help="Search term for event titles"),
    start_date_from: str | None = typer.Option(
        None, "--start-from", help="Start date from (YYYY-MM-DD)"
    ),
    start_date_to: str | None = typer.Option(None, "--start-to", help="Start date to (YYYY-MM-DD)"),
    end_date_from: str | None = typer.Option(None, "--end-from", help="End date from (YYYY-MM-DD)"),
    location_id: int | None = typer.Option(None, "--location-id", help="Location ID"),
    exclude_cancelled_events: bool | None = typer.Option(
        None, "--exclude-cancelled", help="Exclude cancelled events"
    ),
    sort_ascending: bool | None = typer.Option(None, "--sort-asc", help="Sort ascending by date"),
    event_type_id: int | None = typer.Option(None, "--type-id", help="Event type ID"),
    include_event_attendees: bool = typer.Option(
        False, "--include-attendees", help="Include attendees"
    ),
    show_on_website_only: bool = typer.Option(
        True, "--website-only/--all", help="Show only public events"
    ),
    skip: int = typer.Option(0, "--skip", help="Number of records to skip"),
    take: int = typer.Option(30, "--take", help="Number of records to return"),
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
    Search for committee events with flexible filtering.

    Find meetings, hearings, or other committee activities by date, location,
    or committee. Supports filtering by start/end dates, house, event type, and location.
    """
    url = build_url(
        f"{COMMITTEES_API_BASE}/Events",
        {
            "CommitteeId": committee_id,
            "CommitteeBusinessId": committee_business_id,
            "SearchTerm": search_term,
            "StartDateFrom": start_date_from,
            "StartDateTo": start_date_to,
            "EndDateFrom": end_date_from,
            "LocationId": location_id,
            "ExcludeCancelledEvents": exclude_cancelled_events,
            "SortAscending": sort_ascending,
            "EventTypeId": event_type_id,
            "IncludeEventAttendees": include_event_attendees,
            "ShowOnWebsiteOnly": show_on_website_only,
            "Skip": skip,
            "Take": take,
        },
    )
    result = run_async(paginate_request(url, COMMITTEES_PAGINATION, desired_total=take, start_skip=skip))
    echo_utf8(format_output(result, pretty, data_only, output_format, fields, raw))


@app.command("event")
def get_event(
    event_id: int = typer.Argument(..., help="Event ID"),
    show_on_website_only: bool = typer.Option(
        True, "--website-only/--all", help="Show only public events"
    ),
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
    Get detailed information about a specific committee event.

    Returns complete event details including activities, attendees, committees
    involved, and related business.
    """
    url = build_url(
        f"{COMMITTEES_API_BASE}/Events/{event_id}",
        {"showOnWebsiteOnly": show_on_website_only},
    )
    result = run_async(get_result(url))
    echo_utf8(format_output(result, pretty, data_only, output_format, fields, raw))


@app.command("committee-events")
def get_committee_events(
    committee_id: int = typer.Argument(..., help="Committee ID"),
    committee_business_id: int | None = typer.Option(
        None, "--business-id", help="Filter by business ID"
    ),
    search_term: str | None = typer.Option(None, "--search", help="Search term for event titles"),
    start_date_from: str | None = typer.Option(
        None, "--start-from", help="Start date from (YYYY-MM-DD)"
    ),
    start_date_to: str | None = typer.Option(None, "--start-to", help="Start date to (YYYY-MM-DD)"),
    end_date_from: str | None = typer.Option(None, "--end-from", help="End date from (YYYY-MM-DD)"),
    location_id: int | None = typer.Option(None, "--location-id", help="Location ID"),
    exclude_cancelled_events: bool | None = typer.Option(
        None, "--exclude-cancelled", help="Exclude cancelled events"
    ),
    sort_ascending: bool | None = typer.Option(None, "--sort-asc", help="Sort ascending by date"),
    event_type_id: int | None = typer.Option(None, "--type-id", help="Event type ID"),
    include_event_attendees: bool = typer.Option(
        False, "--include-attendees", help="Include attendees"
    ),
    show_on_website_only: bool = typer.Option(
        True, "--website-only/--all", help="Show only public events"
    ),
    skip: int = typer.Option(0, "--skip", help="Number of records to skip"),
    take: int = typer.Option(30, "--take", help="Number of records to return"),
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
    Get events for a specific committee.

    See all meetings and activities for a particular committee, with options
    to filter by date range, business, and event type.
    """
    url = build_url(
        f"{COMMITTEES_API_BASE}/Committees/{committee_id}/Events",
        {
            "CommitteeBusinessId": committee_business_id,
            "SearchTerm": search_term,
            "StartDateFrom": start_date_from,
            "StartDateTo": start_date_to,
            "EndDateFrom": end_date_from,
            "LocationId": location_id,
            "ExcludeCancelledEvents": exclude_cancelled_events,
            "SortAscending": sort_ascending,
            "EventTypeId": event_type_id,
            "IncludeEventAttendees": include_event_attendees,
            "ShowOnWebsiteOnly": show_on_website_only,
            "Skip": skip,
            "Take": take,
        },
    )
    result = run_async(paginate_request(url, COMMITTEES_PAGINATION, desired_total=take, start_skip=skip))
    echo_utf8(format_output(result, pretty, data_only, output_format, fields, raw))


@app.command("members")
def get_members(
    committee_id: int = typer.Argument(..., help="Committee ID"),
    membership_status: str | None = typer.Option(
        None, "--status", help="Membership status (Current/Former)"
    ),
    show_on_website_only: bool = typer.Option(
        True, "--website-only/--all", help="Show only public members"
    ),
    skip: int = typer.Option(0, "--skip", help="Number of records to skip"),
    take: int = typer.Option(30, "--take", help="Number of records to return"),
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
    Get members and staff of a specific committee.

    Know who serves on a committee, their roles, and membership status
    (current/former). Returns both elected members and lay members.
    """
    url = build_url(
        f"{COMMITTEES_API_BASE}/Committees/{committee_id}/Members",
        {
            "MembershipStatus": membership_status,
            "ShowOnWebsiteOnly": show_on_website_only,
            "Skip": skip,
            "Take": take,
        },
    )
    result = run_async(paginate_request(url, COMMITTEES_PAGINATION, desired_total=take, start_skip=skip))
    echo_utf8(format_output(result, pretty, data_only, output_format, fields, raw))


@app.command("publications")
def get_publications(
    search_term: str | None = typer.Option(None, "--search", help="Search term for publications"),
    start_date: str | None = typer.Option(None, "--start-date", help="Start date (YYYY-MM-DD)"),
    end_date: str | None = typer.Option(None, "--end-date", help="End date (YYYY-MM-DD)"),
    committee_business_id: int | None = typer.Option(
        None, "--business-id", help="Committee business ID"
    ),
    committee_id: int | None = typer.Option(None, "--committee-id", help="Committee ID"),
    show_on_website_only: bool = typer.Option(
        True, "--website-only/--all", help="Show only public publications"
    ),
    skip: int = typer.Option(0, "--skip", help="Number of records to skip"),
    take: int = typer.Option(30, "--take", help="Number of records to return"),
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
    Search for committee publications.

    Find reports, government responses, and other documents. Research committee
    outputs, find reports on specific topics, or track publication dates and paper numbers.
    """
    url = build_url(
        f"{COMMITTEES_API_BASE}/Publications",
        {
            "SearchTerm": search_term,
            "StartDate": start_date,
            "EndDate": end_date,
            "CommitteeBusinessId": committee_business_id,
            "CommitteeId": committee_id,
            "ShowOnWebsiteOnly": show_on_website_only,
            "Skip": skip,
            "Take": take,
        },
    )
    result = run_async(paginate_request(url, COMMITTEES_PAGINATION, desired_total=take, start_skip=skip))
    echo_utf8(format_output(result, pretty, data_only, output_format, fields, raw))


@app.command("publication")
def get_publication(
    publication_id: int = typer.Argument(..., help="Publication ID"),
    show_on_website_only: bool = typer.Option(
        True, "--website-only/--all", help="Show only public publications"
    ),
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
    Get detailed information about a specific committee publication.

    Complete publication details including documents, HC numbers, government
    responses, and associated committee business.
    """
    url = build_url(
        f"{COMMITTEES_API_BASE}/Publications/{publication_id}",
        {"showOnWebsiteOnly": show_on_website_only},
    )
    result = run_async(get_result(url))
    echo_utf8(format_output(result, pretty, data_only, output_format, fields, raw))


@app.command("written-evidence")
def get_written_evidence(
    committee_business_id: int | None = typer.Option(
        None, "--business-id", help="Committee business ID"
    ),
    committee_id: int | None = typer.Option(None, "--committee-id", help="Committee ID"),
    search_term: str | None = typer.Option(
        None, "--search", help="Search term for evidence or witnesses"
    ),
    start_date: str | None = typer.Option(None, "--start-date", help="Start date (YYYY-MM-DD)"),
    end_date: str | None = typer.Option(None, "--end-date", help="End date (YYYY-MM-DD)"),
    show_on_website_only: bool = typer.Option(
        True, "--website-only/--all", help="Show only public evidence"
    ),
    skip: int = typer.Option(0, "--skip", help="Number of records to skip"),
    take: int = typer.Option(30, "--take", help="Number of records to return"),
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
    Search for written evidence submissions to committees.

    Research stakeholder submissions, witness statements, or public input to
    committee inquiries. Filter by committee, business, witness names, or publication dates.
    """
    url = build_url(
        f"{COMMITTEES_API_BASE}/WrittenEvidence",
        {
            "CommitteeBusinessId": committee_business_id,
            "CommitteeId": committee_id,
            "SearchTerm": search_term,
            "StartDate": start_date,
            "EndDate": end_date,
            "ShowOnWebsiteOnly": show_on_website_only,
            "Skip": skip,
            "Take": take,
        },
    )
    result = run_async(paginate_request(url, COMMITTEES_PAGINATION, desired_total=take, start_skip=skip))
    echo_utf8(format_output(result, pretty, data_only, output_format, fields, raw))


@app.command("oral-evidence")
def get_oral_evidence(
    committee_business_id: int | None = typer.Option(
        None, "--business-id", help="Committee business ID"
    ),
    committee_id: int | None = typer.Option(None, "--committee-id", help="Committee ID"),
    search_term: str | None = typer.Option(
        None, "--search", help="Search term for evidence or witnesses"
    ),
    start_date: str | None = typer.Option(None, "--start-date", help="Start date (YYYY-MM-DD)"),
    end_date: str | None = typer.Option(None, "--end-date", help="End date (YYYY-MM-DD)"),
    show_on_website_only: bool = typer.Option(
        True, "--website-only/--all", help="Show only public evidence"
    ),
    skip: int = typer.Option(0, "--skip", help="Number of records to skip"),
    take: int = typer.Option(30, "--take", help="Number of records to return"),
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
    Search for oral evidence sessions from committee hearings.

    Research witness testimonies, committee hearings, or transcripts from evidence
    sessions. Filter by committee, business, witness names, or meeting dates.
    """
    url = build_url(
        f"{COMMITTEES_API_BASE}/OralEvidence",
        {
            "CommitteeBusinessId": committee_business_id,
            "CommitteeId": committee_id,
            "SearchTerm": search_term,
            "StartDate": start_date,
            "EndDate": end_date,
            "ShowOnWebsiteOnly": show_on_website_only,
            "Skip": skip,
            "Take": take,
        },
    )
    result = run_async(paginate_request(url, COMMITTEES_PAGINATION, desired_total=take, start_skip=skip))
    echo_utf8(format_output(result, pretty, data_only, output_format, fields, raw))


@app.command("business")
def get_business(
    search_term: str | None = typer.Option(
        None, "--search", help="Search term for business titles"
    ),
    committee_id: int | None = typer.Option(None, "--committee-id", help="Committee ID"),
    date_from: str | None = typer.Option(None, "--date-from", help="Start date (YYYY-MM-DD)"),
    date_to: str | None = typer.Option(None, "--date-to", help="End date (YYYY-MM-DD)"),
    business_type_id: int | None = typer.Option(None, "--type-id", help="Business type ID"),
    status: str | None = typer.Option(None, "--status", help="Status filter (Open/Closed)"),
    currently_accepting_evidence: bool | None = typer.Option(
        None, "--accepting-evidence", help="Filter to inquiries accepting evidence"
    ),
    show_on_website_only: bool = typer.Option(
        True, "--website-only/--all", help="Show only public items"
    ),
    skip: int = typer.Option(0, "--skip", help="Number of records to skip"),
    take: int = typer.Option(30, "--take", help="Number of records to return"),
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
    Search for committee business (inquiries, investigations).

    Find committee inquiries by topic, status, or whether accepting evidence.
    """
    url = build_url(
        f"{COMMITTEES_API_BASE}/CommitteeBusiness",
        {
            "SearchTerm": search_term,
            "CommitteeId": committee_id,
            "DateFrom": date_from,
            "DateTo": date_to,
            "BusinessTypeId": business_type_id,
            "Status": status,
            "CurrentlyAcceptingEvidence": currently_accepting_evidence,
            "ShowOnWebsiteOnly": show_on_website_only,
            "Skip": skip,
            "Take": take,
        },
    )
    result = run_async(paginate_request(url, COMMITTEES_PAGINATION, desired_total=take, start_skip=skip))
    echo_utf8(format_output(result, pretty, data_only, output_format, fields, raw))


@app.command("business-details")
def get_business_details(
    business_id: int = typer.Argument(..., help="Committee business ID"),
    show_on_website_only: bool = typer.Option(
        True, "--website-only/--all", help="Show only public items"
    ),
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
    Get detailed information about a specific committee business item.

    Complete details about a specific inquiry or investigation including
    evidence calls and reports.
    """
    url = build_url(
        f"{COMMITTEES_API_BASE}/CommitteeBusiness/{business_id}",
        {"showOnWebsiteOnly": show_on_website_only},
    )
    result = run_async(get_result(url))
    echo_utf8(format_output(result, pretty, data_only, output_format, fields, raw))


@app.command("business-types")
def get_business_types(
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
    Get all types of committee business.

    Understand different types of committee work (inquiries, debates, etc.).
    """
    url = f"{COMMITTEES_API_BASE}/CommitteeBusinessType"
    result = run_async(get_result(url))
    echo_utf8(format_output(result, pretty, data_only, output_format, fields, raw))


@app.command("next-events")
def get_next_events(
    house: int | None = typer.Option(None, "--house", help="Filter by house (1=Commons, 2=Lords)"),
    event_from_date: str | None = typer.Option(
        None, "--from-date", help="Start date (YYYY-MM-DD, default today)"
    ),
    skip: int = typer.Option(0, "--skip", help="Number of records to skip"),
    take: int = typer.Option(30, "--take", help="Number of records to return"),
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
    Get upcoming events for all committees.

    See what committee meetings are scheduled next.
    """
    url = build_url(
        f"{COMMITTEES_API_BASE}/Committees/NextEvent",
        {
            "House": house,
            "EventFromDate": event_from_date,
            "Skip": skip,
            "Take": take,
        },
    )
    result = run_async(paginate_request(url, COMMITTEES_PAGINATION, desired_total=take, start_skip=skip))
    echo_utf8(format_output(result, pretty, data_only, output_format, fields, raw))


@app.command("staff")
def get_staff(
    committee_id: int = typer.Argument(..., help="Committee ID"),
    membership_status: str | None = typer.Option(
        None, "--status", help="Membership status (Current/Former)"
    ),
    show_on_website_only: bool = typer.Option(
        True, "--website-only/--all", help="Show only public staff"
    ),
    skip: int = typer.Option(0, "--skip", help="Number of records to skip"),
    take: int = typer.Option(30, "--take", help="Number of records to return"),
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
    Get staff members of a committee.

    Find who supports a committee's work (clerks, advisers).
    """
    url = build_url(
        f"{COMMITTEES_API_BASE}/Committees/{committee_id}/Staff",
        {
            "MembershipStatus": membership_status,
            "ShowOnWebsiteOnly": show_on_website_only,
            "Skip": skip,
            "Take": take,
        },
    )
    result = run_async(paginate_request(url, COMMITTEES_PAGINATION, desired_total=take, start_skip=skip))
    echo_utf8(format_output(result, pretty, data_only, output_format, fields, raw))


@app.command("publications-summary")
def get_publications_summary(
    committee_id: int = typer.Argument(..., help="Committee ID"),
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
    Get summary of publications grouped by type.

    Overview of a committee's publication output with counts by type.
    """
    url = f"{COMMITTEES_API_BASE}/Committees/{committee_id}/Publications/Summary"
    result = run_async(get_result(url))
    echo_utf8(format_output(result, pretty, data_only, output_format, fields, raw))


@app.command("event-activities")
def get_event_activities(
    event_id: int = typer.Argument(..., help="Event ID"),
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
    Get activities scheduled for an event.

    See what's on the agenda for a committee meeting.
    """
    url = f"{COMMITTEES_API_BASE}/Events/{event_id}/Activities"
    result = run_async(get_result(url))
    echo_utf8(format_output(result, pretty, data_only, output_format, fields, raw))


@app.command("event-attendance")
def get_event_attendance(
    event_id: int = typer.Argument(..., help="Event ID"),
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
    Get attendance record for an event.

    See which members attended a committee meeting.
    """
    url = f"{COMMITTEES_API_BASE}/Events/{event_id}/Attendance"
    result = run_async(get_result(url))
    echo_utf8(format_output(result, pretty, data_only, output_format, fields, raw))


@app.command("member-memberships")
def get_member_memberships(
    member_ids: str = typer.Argument(
        ..., help="Comma-separated list of member IDs (e.g., '4514' or '4514,172')"
    ),
    membership_status: str | None = typer.Option(
        None, "--status", help="Membership status (Current/Former)"
    ),
    committee_category: str | None = typer.Option(None, "--category", help="Committee category"),
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
    Get committee memberships for one or more members.

    Find which committees a member serves on.
    """
    url = build_url(
        f"{COMMITTEES_API_BASE}/Members",
        {
            "Members": member_ids,
            "MembershipStatus": membership_status,
            "CommitteeCategory": committee_category,
        },
    )
    result = run_async(get_result(url))
    echo_utf8(format_output(result, pretty, data_only, output_format, fields, raw))


@app.command("oral-evidence-details")
def get_oral_evidence_details(
    evidence_id: int = typer.Argument(..., help="Oral evidence ID"),
    show_on_website_only: bool = typer.Option(
        True, "--website-only/--all", help="Show only public evidence"
    ),
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
    Get detailed oral evidence by ID.

    Full details of a specific oral evidence session.
    """
    url = build_url(
        f"{COMMITTEES_API_BASE}/OralEvidence/{evidence_id}",
        {"showOnWebsiteOnly": show_on_website_only},
    )
    result = run_async(get_result(url))
    echo_utf8(format_output(result, pretty, data_only, output_format, fields, raw))


@app.command("written-evidence-details")
def get_written_evidence_details(
    evidence_id: int = typer.Argument(..., help="Written evidence ID"),
    show_on_website_only: bool = typer.Option(
        True, "--website-only/--all", help="Show only public evidence"
    ),
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
    Get detailed written evidence by ID.

    Full details of a specific written evidence submission.
    """
    url = build_url(
        f"{COMMITTEES_API_BASE}/WrittenEvidence/{evidence_id}",
        {"showOnWebsiteOnly": show_on_website_only},
    )
    result = run_async(get_result(url))
    echo_utf8(format_output(result, pretty, data_only, output_format, fields, raw))


@app.command("publication-types")
def get_publication_types(
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
    Get all types of committee publications.

    Understand different types of committee publications (report types, document types).
    """
    url = f"{COMMITTEES_API_BASE}/PublicationType"
    result = run_async(get_result(url))
    echo_utf8(format_output(result, pretty, data_only, output_format, fields, raw))


@app.command("bill-petitions")
def search_bill_petitions(
    committee_business_id: int | None = typer.Option(
        None, "--business-id", help="Committee business ID"
    ),
    committee_id: int | None = typer.Option(None, "--committee-id", help="Committee ID"),
    search_term: str | None = typer.Option(
        None, "--search", help="Search term for petition content"
    ),
    start_date: str | None = typer.Option(None, "--start-date", help="Start date (YYYY-MM-DD)"),
    end_date: str | None = typer.Option(None, "--end-date", help="End date (YYYY-MM-DD)"),
    show_on_website_only: bool = typer.Option(
        True, "--website-only/--all", help="Show only public petitions"
    ),
    skip: int = typer.Option(0, "--skip", help="Number of records to skip"),
    take: int = typer.Option(30, "--take", help="Number of records to return"),
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
    Search petitions on Private Bills.

    Find public petitions submitted on Private Bills.
    """
    url = build_url(
        f"{COMMITTEES_API_BASE}/BillPetitions",
        {
            "CommitteeBusinessId": committee_business_id,
            "CommitteeId": committee_id,
            "SearchTerm": search_term,
            "StartDate": start_date,
            "EndDate": end_date,
            "ShowOnWebsiteOnly": show_on_website_only,
            "Skip": skip,
            "Take": take,
        },
    )
    result = run_async(paginate_request(url, COMMITTEES_PAGINATION, desired_total=take, start_skip=skip))
    echo_utf8(format_output(result, pretty, data_only, output_format, fields, raw))


@app.command("business-publications-summary")
def get_business_publications_summary(
    business_id: int = typer.Argument(..., help="Committee business ID"),
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
    Get publication summary for an inquiry.

    See publication types for a committee business/inquiry with counts.
    """
    url = f"{COMMITTEES_API_BASE}/CommitteeBusiness/{business_id}/Publications/Summary"
    result = run_async(get_result(url))
    echo_utf8(format_output(result, pretty, data_only, output_format, fields, raw))
