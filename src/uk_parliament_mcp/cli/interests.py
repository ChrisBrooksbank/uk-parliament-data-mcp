"""Interests CLI commands for Register of Interests."""

from __future__ import annotations

import typer

from uk_parliament_mcp.cli.utils import format_output, run_async
from uk_parliament_mcp.config import INTERESTS_API_BASE
from uk_parliament_mcp.http_client import get_result

app = typer.Typer(help="Register of Interests - financial declarations and conflicts")


@app.command("search")
def search_roi(
    member_id: int = typer.Argument(..., help="Parliament member ID"),
    pretty: bool = typer.Option(False, "--pretty", "-p", help="Pretty-print JSON output"),
    data_only: bool = typer.Option(False, "--data-only", "-d", help="Return data only"),
) -> None:
    """
    Search member's Register of Interests for financial and business declarations.

    Returns declared interests including directorships, consultancies, gifts,
    and other financial interests. Use for investigating potential conflicts,
    researching member finances, or checking declared interests.
    """
    url = f"{INTERESTS_API_BASE}/Interests/?MemberId={member_id}"
    result = run_async(get_result(url))
    typer.echo(format_output(result, pretty, data_only))


@app.command("categories")
def interests_categories(
    pretty: bool = typer.Option(False, "--pretty", "-p", help="Pretty-print JSON output"),
    data_only: bool = typer.Option(False, "--data-only", "-d", help="Return data only"),
) -> None:
    """
    Get categories of interests that MPs and Lords must declare.

    Use when you need to understand what types of financial or other interests
    parliamentarians must declare in the Register of Interests.
    """
    url = f"{INTERESTS_API_BASE}/Categories"
    result = run_async(get_result(url))
    typer.echo(format_output(result, pretty, data_only))


@app.command("registers")
def get_registers_of_interests(
    pretty: bool = typer.Option(False, "--pretty", "-p", help="Pretty-print JSON output"),
    data_only: bool = typer.Option(False, "--data-only", "-d", help="Return data only"),
) -> None:
    """
    Get list of published Registers of Interests.

    Use when you need to see all available interest registers or understand
    the transparency framework for parliamentary interests.
    """
    url = f"{INTERESTS_API_BASE}/Registers"
    result = run_async(get_result(url))
    typer.echo(format_output(result, pretty, data_only))
