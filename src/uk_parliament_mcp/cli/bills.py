"""Bills CLI commands for legislation, amendments, and stages."""

from __future__ import annotations

from urllib.parse import quote

import typer

from uk_parliament_mcp.cli.formatters import OutputFormat
from uk_parliament_mcp.cli.pagination import BILLS_PAGINATION, paginate_request
from uk_parliament_mcp.cli.utils import echo_utf8, format_output, run_async
from uk_parliament_mcp.config import BILLS_API_BASE
from uk_parliament_mcp.http_client import build_url, get_result

app = typer.Typer(help="Bills and legislation tools")


@app.command("recent")
def get_recent_bills(
    take: int = typer.Option(10, "--take", "-t", help="Number of bills to return (default: 10)"),
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
    Get most recently updated bills and current legislative activity.

    Returns bill titles, stages, sponsors, dates, and current status.
    """
    url = f"{BILLS_API_BASE}/Bills?SortOrder=DateUpdatedDescending&skip=0&take={take}"
    result = run_async(paginate_request(url, BILLS_PAGINATION, desired_total=take, start_skip=0))
    echo_utf8(format_output(result, pretty, data_only, output_format, fields, raw))


@app.command("search")
def search_bills(
    search_term: str = typer.Argument(..., help="Search term for bill titles or content"),
    member_id: int | None = typer.Option(
        None, "--member-id", "-m", help="Filter by sponsoring member ID"
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
    Search for parliamentary bills by title, subject, or keyword.

    Returns matching bills with titles, stages, and sponsors.
    """
    url = f"{BILLS_API_BASE}/Bills?SearchTerm={quote(search_term)}"
    result = run_async(get_result(url))
    echo_utf8(format_output(result, pretty, data_only, output_format, fields, raw))


@app.command("types")
def get_bill_types(
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
    Get all types of bills that can be introduced in Parliament.

    Returns bill types with descriptions (e.g., Government Bill, Private Member's Bill).
    """
    url = f"{BILLS_API_BASE}/BillTypes"
    result = run_async(get_result(url))
    echo_utf8(format_output(result, pretty, data_only, output_format, fields, raw))


@app.command("stages-list")
def get_bill_stages_list(
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
    Get all possible stages a bill can go through in its legislative journey.

    Returns all bill stages with descriptions (e.g., First Reading, Committee Stage, Royal Assent).
    """
    url = f"{BILLS_API_BASE}/Stages"
    result = run_async(get_result(url))
    echo_utf8(format_output(result, pretty, data_only, output_format, fields, raw))


@app.command("get")
def get_bill(
    bill_id: int = typer.Argument(..., help="Bill ID"),
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
    Get detailed information about a specific bill by ID.

    Returns comprehensive bill details including title, sponsors, stages, summary, and status.
    """
    url = f"{BILLS_API_BASE}/Bills/{bill_id}"
    result = run_async(get_result(url))
    echo_utf8(format_output(result, pretty, data_only, output_format, fields, raw))


@app.command("stages")
def get_stages(
    bill_id: int = typer.Argument(..., help="Bill ID"),
    skip: int | None = typer.Option(None, "--skip", help="Number of records to skip (pagination)"),
    take: int | None = typer.Option(None, "--take", "-t", help="Number of records to return"),
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
    Get all stages of a specific bill by bill ID.

    Returns all stages for tracking bill progress through Parliament.
    """
    url = build_url(
        f"{BILLS_API_BASE}/Bills/{bill_id}/Stages",
        {"Skip": skip, "Take": take},
    )
    result = run_async(paginate_request(url, BILLS_PAGINATION, desired_total=take, start_skip=skip or 0))
    echo_utf8(format_output(result, pretty, data_only, output_format, fields, raw))


@app.command("stage-details")
def get_stage_details(
    bill_id: int = typer.Argument(..., help="Bill ID"),
    stage_id: int = typer.Argument(..., help="Bill stage ID"),
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
    Get detailed information about a specific stage of a bill.

    Returns complete details including timings, committee involvement, and related activities.
    """
    url = f"{BILLS_API_BASE}/Bills/{bill_id}/Stages/{stage_id}"
    result = run_async(get_result(url))
    echo_utf8(format_output(result, pretty, data_only, output_format, fields, raw))


@app.command("amendments")
def get_amendments(
    bill_id: int = typer.Argument(..., help="Bill ID"),
    stage_id: int = typer.Argument(..., help="Bill stage ID"),
    search_term: str | None = typer.Option(
        None, "--search", "-s", help="Search term for amendment content"
    ),
    amendment_number: str | None = typer.Option(
        None, "--number", "-n", help="Specific amendment number"
    ),
    decision: str | None = typer.Option(None, "--decision", help="Amendment decision status"),
    member_id: int | None = typer.Option(
        None, "--member-id", "-m", help="Member ID who proposed amendment"
    ),
    skip: int | None = typer.Option(None, "--skip", help="Number of records to skip (pagination)"),
    take: int | None = typer.Option(None, "--take", "-t", help="Number of records to return"),
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
    Get all amendments for a specific bill stage.

    Returns amendments for researching proposed changes to legislation.
    """
    url = build_url(
        f"{BILLS_API_BASE}/Bills/{bill_id}/Stages/{stage_id}/Amendments",
        {
            "SearchTerm": search_term,
            "AmendmentNumber": amendment_number,
            "Decision": decision,
            "MemberId": member_id,
            "Skip": skip,
            "Take": take,
        },
    )
    result = run_async(paginate_request(url, BILLS_PAGINATION, desired_total=take, start_skip=skip or 0))
    echo_utf8(format_output(result, pretty, data_only, output_format, fields, raw))


@app.command("amendment")
def get_amendment(
    bill_id: int = typer.Argument(..., help="Bill ID"),
    stage_id: int = typer.Argument(..., help="Bill stage ID"),
    amendment_id: int = typer.Argument(..., help="Amendment ID"),
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
    Get detailed information about a specific amendment.

    Returns complete amendment details including text, sponsors, decision, and explanatory notes.
    """
    url = f"{BILLS_API_BASE}/Bills/{bill_id}/Stages/{stage_id}/Amendments/{amendment_id}"
    result = run_async(get_result(url))
    echo_utf8(format_output(result, pretty, data_only, output_format, fields, raw))


@app.command("ping-pong")
def get_ping_pong_items(
    bill_id: int = typer.Argument(..., help="Bill ID"),
    stage_id: int = typer.Argument(..., help="Bill stage ID"),
    search_term: str | None = typer.Option(
        None, "--search", "-s", help="Search term for ping pong item content"
    ),
    amendment_number: str | None = typer.Option(
        None, "--number", "-n", help="Specific amendment number"
    ),
    decision: str | None = typer.Option(None, "--decision", help="Ping pong item decision status"),
    member_id: int | None = typer.Option(
        None, "--member-id", "-m", help="Member ID who proposed item"
    ),
    skip: int | None = typer.Option(None, "--skip", help="Number of records to skip (pagination)"),
    take: int | None = typer.Option(None, "--take", "-t", help="Number of records to return"),
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
    Get ping pong items (amendments and motions) for a bill stage.

    Returns ping pong items for researching final stages of bills passing between Commons and Lords.
    """
    url = build_url(
        f"{BILLS_API_BASE}/Bills/{bill_id}/Stages/{stage_id}/PingPongItems",
        {
            "SearchTerm": search_term,
            "AmendmentNumber": amendment_number,
            "Decision": decision,
            "MemberId": member_id,
            "Skip": skip,
            "Take": take,
        },
    )
    result = run_async(paginate_request(url, BILLS_PAGINATION, desired_total=take, start_skip=skip or 0))
    echo_utf8(format_output(result, pretty, data_only, output_format, fields, raw))


@app.command("ping-pong-item")
def get_ping_pong_item(
    bill_id: int = typer.Argument(..., help="Bill ID"),
    stage_id: int = typer.Argument(..., help="Bill stage ID"),
    item_id: int = typer.Argument(..., help="Ping pong item ID"),
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
    Get detailed information about a specific ping pong item.

    Returns complete details about final stage amendments or motions in the legislative process.
    """
    url = f"{BILLS_API_BASE}/Bills/{bill_id}/Stages/{stage_id}/PingPongItems/{item_id}"
    result = run_async(get_result(url))
    echo_utf8(format_output(result, pretty, data_only, output_format, fields, raw))


@app.command("publications")
def get_publications(
    bill_id: int = typer.Argument(..., help="Bill ID"),
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
    Get all publications for a specific bill.

    Returns publications including documents, impact assessments, and explanatory notes.
    """
    url = f"{BILLS_API_BASE}/Bills/{bill_id}/Publications"
    result = run_async(get_result(url))
    echo_utf8(format_output(result, pretty, data_only, output_format, fields, raw))


@app.command("stage-publications")
def get_stage_publications(
    bill_id: int = typer.Argument(..., help="Bill ID"),
    stage_id: int = typer.Argument(..., help="Stage ID"),
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
    Get publications for a specific bill stage.

    Returns documents related to a particular stage of legislation.
    """
    url = f"{BILLS_API_BASE}/Bills/{bill_id}/Stages/{stage_id}/Publications"
    result = run_async(get_result(url))
    echo_utf8(format_output(result, pretty, data_only, output_format, fields, raw))


@app.command("publication-document")
def get_publication_document(
    publication_id: int = typer.Argument(..., help="Publication ID"),
    document_id: int = typer.Argument(..., help="Document ID"),
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
    Get information about a specific publication document.

    Returns metadata about bill documents including filename, content type, and size.
    """
    url = f"{BILLS_API_BASE}/Publications/{publication_id}/Documents/{document_id}"
    result = run_async(get_result(url))
    echo_utf8(format_output(result, pretty, data_only, output_format, fields, raw))


@app.command("news")
def get_news_articles(
    bill_id: int = typer.Argument(..., help="Bill ID"),
    skip: int | None = typer.Option(None, "--skip", help="Number of records to skip (pagination)"),
    take: int | None = typer.Option(None, "--take", "-t", help="Number of records to return"),
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
    Get news articles related to a specific bill.

    Returns news articles, media coverage, press releases, and official communications about legislation.
    """
    url = build_url(
        f"{BILLS_API_BASE}/Bills/{bill_id}/NewsArticles",
        {"Skip": skip, "Take": take},
    )
    result = run_async(paginate_request(url, BILLS_PAGINATION, desired_total=take, start_skip=skip or 0))
    echo_utf8(format_output(result, pretty, data_only, output_format, fields, raw))


@app.command("rss-all")
def get_all_bills_rss(
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
    Get RSS feed of all bills.

    Returns RSS feed for staying updated on all legislative activity.
    """
    url = f"{BILLS_API_BASE}/Rss/allbills.rss"
    result = run_async(get_result(url))
    echo_utf8(format_output(result, pretty, data_only, output_format, fields, raw))


@app.command("rss-public")
def get_public_bills_rss(
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
    Get RSS feed of public bills only.

    Returns RSS feed for monitoring government and public bills, excluding private bills.
    """
    url = f"{BILLS_API_BASE}/Rss/publicbills.rss"
    result = run_async(get_result(url))
    echo_utf8(format_output(result, pretty, data_only, output_format, fields, raw))


@app.command("rss-private")
def get_private_bills_rss(
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
    Get RSS feed of private bills only.

    Returns RSS feed for monitoring private member bills and private bills.
    """
    url = f"{BILLS_API_BASE}/Rss/privatebills.rss"
    result = run_async(get_result(url))
    echo_utf8(format_output(result, pretty, data_only, output_format, fields, raw))


@app.command("rss-bill")
def get_bill_rss(
    bill_id: int = typer.Argument(..., help="Bill ID"),
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
    Get RSS feed for a specific bill by ID.

    Returns RSS feed for tracking updates and changes to a particular piece of legislation.
    """
    url = f"{BILLS_API_BASE}/Rss/Bills/{bill_id}.rss"
    result = run_async(get_result(url))
    echo_utf8(format_output(result, pretty, data_only, output_format, fields, raw))


@app.command("publication-types")
def get_publication_types(
    skip: int | None = typer.Option(None, "--skip", help="Number of records to skip (pagination)"),
    take: int | None = typer.Option(None, "--take", "-t", help="Number of records to return"),
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
    Get all publication types available for bills.

    Returns all publication types with descriptions for understanding document categories.
    """
    url = build_url(
        f"{BILLS_API_BASE}/PublicationTypes",
        {"Skip": skip, "Take": take},
    )
    result = run_async(paginate_request(url, BILLS_PAGINATION, desired_total=take, start_skip=skip or 0))
    echo_utf8(format_output(result, pretty, data_only, output_format, fields, raw))


@app.command("sittings")
def get_sittings(
    house: str | None = typer.Option(None, "--house", help="House name ('Commons' or 'Lords')"),
    date_from: str | None = typer.Option(None, "--from", help="Start date (YYYY-MM-DD)"),
    date_to: str | None = typer.Option(None, "--to", help="End date (YYYY-MM-DD)"),
    skip: int | None = typer.Option(None, "--skip", help="Number of records to skip (pagination)"),
    take: int | None = typer.Option(None, "--take", "-t", help="Number of records to return"),
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
    Get parliamentary sittings with optional filtering by house and date range.

    Returns parliamentary sittings for researching when Parliament was in session.
    """
    url = build_url(
        f"{BILLS_API_BASE}/Sittings",
        {
            "House": house,
            "DateFrom": date_from,
            "DateTo": date_to,
            "Skip": skip,
            "Take": take,
        },
    )
    result = run_async(paginate_request(url, BILLS_PAGINATION, desired_total=take, start_skip=skip or 0))
    echo_utf8(format_output(result, pretty, data_only, output_format, fields, raw))
