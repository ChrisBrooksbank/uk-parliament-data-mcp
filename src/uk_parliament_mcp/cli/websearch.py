"""Web search CLI commands for searching the parliament.uk website."""

from __future__ import annotations

import typer

from uk_parliament_mcp.cli.formatters import OutputFormat
from uk_parliament_mcp.cli.utils import (
    DataOnlyOpt,
    FieldsOpt,
    FormatOpt,
    PrettyOpt,
    RawOpt,
    output_result,
)
from uk_parliament_mcp.config import WEBSEARCH_API_BASE
from uk_parliament_mcp.http_client import build_url

app = typer.Typer(help="Search the parliament.uk website", no_args_is_help=True)


@app.command("website")
def search_parliament_website(
    search_terms: str = typer.Argument(
        ..., help="Terms to search for (e.g. 'climate change', 'sitting hours')"
    ),
    start: int | None = typer.Option(None, "--start", help="First result to return (default 1)"),
    take: int | None = typer.Option(
        None, "--take", help="Number of results per page (default and maximum 20)"
    ),
    pretty: PrettyOpt = False,
    data_only: DataOnlyOpt = True,
    output_format: FormatOpt = OutputFormat.AUTO,
    raw: RawOpt = False,
    fields: FieldsOpt = None,
) -> None:
    """
    Search the parliament.uk website.

    Free-text search across parliament.uk content, including Commons Library briefings,
    research briefings and guides that the structured APIs don't cover.
    Results include title, description, url and tags.
    """
    url = build_url(
        f"{WEBSEARCH_API_BASE}/WebSearch",
        {"searchTerms": search_terms, "start": start, "take": take},
    )
    output_result(url, pretty, data_only, output_format, fields, raw)
