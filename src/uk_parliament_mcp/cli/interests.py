"""Interests CLI commands for Register of Interests."""

from __future__ import annotations

import typer

from uk_parliament_mcp.cli.formatters import OutputFormat
from uk_parliament_mcp.cli.utils import echo_utf8, format_output, run_async
from uk_parliament_mcp.config import INTERESTS_API_BASE
from uk_parliament_mcp.http_client import build_url, get_result

app = typer.Typer(
    help="Register of Interests - financial declarations and conflicts", no_args_is_help=True
)


@app.command("search")
def search_roi(
    member_id: int = typer.Argument(..., help="Parliament member ID"),
    category_id: int | None = typer.Option(
        None, "--category-id", help="Filter by interest category ID"
    ),
    published_from: str | None = typer.Option(
        None, "--published-from", help="Published from date (YYYY-MM-DD)"
    ),
    published_to: str | None = typer.Option(
        None, "--published-to", help="Published to date (YYYY-MM-DD)"
    ),
    registered_from: str | None = typer.Option(
        None, "--registered-from", help="Registered from date (YYYY-MM-DD)"
    ),
    registered_to: str | None = typer.Option(
        None, "--registered-to", help="Registered to date (YYYY-MM-DD)"
    ),
    updated_from: str | None = typer.Option(
        None, "--updated-from", help="Updated from date (YYYY-MM-DD)"
    ),
    updated_to: str | None = typer.Option(
        None, "--updated-to", help="Updated to date (YYYY-MM-DD)"
    ),
    register_id: int | None = typer.Option(None, "--register-id", help="Filter by register ID"),
    expand_child_interests: bool | None = typer.Option(
        None, "--expand-children", help="Expand child interests in results"
    ),
    sort_order: str | None = typer.Option(
        None, "--sort-order", help="Sort order (e.g., CategoryAscending)"
    ),
    skip: int | None = typer.Option(None, "--skip", help="Number of records to skip (pagination)"),
    take: int | None = typer.Option(None, "--take", help="Number of records to return"),
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
    Search member's Register of Interests for financial and business declarations.

    Returns declared interests including directorships, consultancies, gifts,
    and other financial interests. Use for investigating potential conflicts,
    researching member finances, or checking declared interests.
    """
    url = build_url(
        f"{INTERESTS_API_BASE}/Interests/",
        {
            "MemberId": member_id,
            "CategoryId": category_id,
            "PublishedFrom": published_from,
            "PublishedTo": published_to,
            "RegisteredFrom": registered_from,
            "RegisteredTo": registered_to,
            "UpdatedFrom": updated_from,
            "UpdatedTo": updated_to,
            "RegisterId": register_id,
            "ExpandChildInterests": expand_child_interests,
            "SortOrder": sort_order,
            "Skip": skip,
            "Take": take,
        },
    )
    result = run_async(get_result(url))
    echo_utf8(format_output(result, pretty, data_only, output_format, fields, raw))


@app.command("categories")
def interests_categories(
    skip: int | None = typer.Option(None, "--skip", help="Number of records to skip (pagination)"),
    take: int | None = typer.Option(None, "--take", help="Number of records to return"),
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
    Get categories of interests that MPs and Lords must declare.

    Use when you need to understand what types of financial or other interests
    parliamentarians must declare in the Register of Interests.
    """
    url = build_url(
        f"{INTERESTS_API_BASE}/Categories",
        {"Skip": skip, "Take": take},
    )
    result = run_async(get_result(url))
    echo_utf8(format_output(result, pretty, data_only, output_format, fields, raw))


@app.command("registers")
def get_registers_of_interests(
    session_id: int | None = typer.Option(
        None, "--session-id", help="Filter by parliamentary session ID"
    ),
    skip: int | None = typer.Option(None, "--skip", help="Number of records to skip (pagination)"),
    take: int | None = typer.Option(None, "--take", help="Number of records to return"),
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
    Get list of published Registers of Interests.

    Use when you need to see all available interest registers or understand
    the transparency framework for parliamentary interests.
    """
    url = build_url(
        f"{INTERESTS_API_BASE}/Registers",
        {"SessionId": session_id, "Skip": skip, "Take": take},
    )
    result = run_async(get_result(url))
    echo_utf8(format_output(result, pretty, data_only, output_format, fields, raw))
