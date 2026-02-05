"""Procedures CLI commands for Erskine May parliamentary procedure."""

from __future__ import annotations

from urllib.parse import quote

import typer

from uk_parliament_mcp.cli.utils import format_output, run_async
from uk_parliament_mcp.config import ERSKINE_MAY_API_BASE
from uk_parliament_mcp.http_client import build_url, get_result

app = typer.Typer(
    help="Parliamentary procedure and Erskine May - rules, precedents, and procedure manual"
)


@app.command("search")
def search_erskine_may(
    search_term: str = typer.Argument(
        ..., help="Search term for parliamentary procedure rules (e.g. 'Speaker', 'amendment')"
    ),
    pretty: bool = typer.Option(False, "--pretty", "-p", help="Pretty-print JSON output"),
    data_only: bool = typer.Option(False, "--data-only", "-d", help="Return data only"),
) -> None:
    """
    Search Erskine May parliamentary procedure manual.

    Use when you need to understand parliamentary rules, procedures, or precedents.
    Erskine May is the authoritative guide to parliamentary procedure.
    """
    url = f"{ERSKINE_MAY_API_BASE}/Search/ParagraphSearchResults/{quote(search_term)}"
    result = run_async(get_result(url))
    typer.echo(format_output(result, pretty, data_only))


@app.command("parts")
def get_erskine_may_parts(
    pretty: bool = typer.Option(False, "--pretty", "-p", help="Pretty-print JSON output"),
    data_only: bool = typer.Option(False, "--data-only", "-d", help="Return data only"),
) -> None:
    """
    List all parts of Erskine May procedure manual.

    Returns the 6 major parts of parliamentary procedure with titles and descriptions.
    Use to navigate the structure of the manual.
    """
    url = f"{ERSKINE_MAY_API_BASE}/Part"
    result = run_async(get_result(url))
    typer.echo(format_output(result, pretty, data_only))


@app.command("part")
def get_erskine_may_part(
    part_number: int = typer.Argument(..., help="Part number (1-6)"),
    pretty: bool = typer.Option(False, "--pretty", "-p", help="Pretty-print JSON output"),
    data_only: bool = typer.Option(False, "--data-only", "-d", help="Return data only"),
) -> None:
    """
    Get a specific part of Erskine May with its chapters.

    Use to explore chapters within a part of the parliamentary procedure manual.
    Returns part with title, description, and list of chapters.
    """
    url = f"{ERSKINE_MAY_API_BASE}/Part/{part_number}"
    result = run_async(get_result(url))
    typer.echo(format_output(result, pretty, data_only))


@app.command("chapter")
def get_erskine_may_chapter(
    chapter_number: int = typer.Argument(..., help="Chapter number"),
    pretty: bool = typer.Option(False, "--pretty", "-p", help="Pretty-print JSON output"),
    data_only: bool = typer.Option(False, "--data-only", "-d", help="Return data only"),
) -> None:
    """
    Get a specific chapter of Erskine May with its sections.

    Use to explore sections within a chapter. Returns chapter with title,
    description, and list of sections.
    """
    url = f"{ERSKINE_MAY_API_BASE}/Chapter/{chapter_number}"
    result = run_async(get_result(url))
    typer.echo(format_output(result, pretty, data_only))


@app.command("section")
def get_erskine_may_section(
    section_id: int = typer.Argument(..., help="Section ID"),
    pretty: bool = typer.Option(False, "--pretty", "-p", help="Pretty-print JSON output"),
    data_only: bool = typer.Option(False, "--data-only", "-d", help="Return data only"),
) -> None:
    """
    Get full content of an Erskine May section.

    Use to read the actual procedural content. Returns section with full text
    content and footnotes.
    """
    url = f"{ERSKINE_MAY_API_BASE}/Section/{section_id}"
    result = run_async(get_result(url))
    typer.echo(format_output(result, pretty, data_only))


@app.command("section-relative")
def get_erskine_may_section_relative(
    section_id: int = typer.Argument(..., help="Current section ID"),
    step: int = typer.Argument(..., help="Step offset (e.g. 1 for next, -1 for previous)"),
    pretty: bool = typer.Option(False, "--pretty", "-p", help="Pretty-print JSON output"),
    data_only: bool = typer.Option(False, "--data-only", "-d", help="Return data only"),
) -> None:
    """
    Navigate to a section relative to current position.

    Use to move through sections sequentially. Returns section at offset from
    current section.
    """
    url = f"{ERSKINE_MAY_API_BASE}/Section/{section_id},{step}"
    result = run_async(get_result(url))
    typer.echo(format_output(result, pretty, data_only))


@app.command("paragraph")
def get_erskine_may_paragraph(
    reference: str = typer.Argument(..., help="Paragraph reference (e.g. '4.5', '12.3')"),
    pretty: bool = typer.Option(False, "--pretty", "-p", help="Pretty-print JSON output"),
    data_only: bool = typer.Option(False, "--data-only", "-d", help="Return data only"),
) -> None:
    """
    Look up a specific paragraph by reference number.

    Use when you have a paragraph citation like '4.5' and need the specific
    rule content.
    """
    url = f"{ERSKINE_MAY_API_BASE}/Search/Paragraph/{quote(reference)}"
    result = run_async(get_result(url))
    typer.echo(format_output(result, pretty, data_only))


@app.command("browse-index")
def browse_erskine_may_index(
    start_letter: str | None = typer.Argument(None, help="Starting letter to browse from (A-Z)"),
    skip: int = typer.Option(0, "--skip", help="Number of results to skip for pagination"),
    take: int = typer.Option(30, "--take", help="Number of results to return"),
    pretty: bool = typer.Option(False, "--pretty", "-p", help="Pretty-print JSON output"),
    data_only: bool = typer.Option(False, "--data-only", "-d", help="Return data only"),
) -> None:
    """
    Browse the Erskine May index alphabetically.

    Use to discover topics by browsing alphabetically. Returns index terms
    starting with given letter (or all if no letter specified).
    """
    url = build_url(
        f"{ERSKINE_MAY_API_BASE}/IndexTerm/browse",
        {
            "startLetter": start_letter,
            "skip": skip,
            "take": take,
        },
    )
    result = run_async(get_result(url))
    typer.echo(format_output(result, pretty, data_only))


@app.command("index-term")
def get_erskine_may_index_term(
    index_term_id: int = typer.Argument(..., help="Index term ID (from browse-index)"),
    pretty: bool = typer.Option(False, "--pretty", "-p", help="Pretty-print JSON output"),
    data_only: bool = typer.Option(False, "--data-only", "-d", help="Return data only"),
) -> None:
    """
    Get details of an index term.

    Use after browsing index to get term details. Returns index term with all
    paragraph references.
    """
    url = f"{ERSKINE_MAY_API_BASE}/IndexTerm/{index_term_id}"
    result = run_async(get_result(url))
    typer.echo(format_output(result, pretty, data_only))


@app.command("search-index")
def search_erskine_may_index(
    search_term: str = typer.Argument(..., help="Term to search for in the index"),
    skip: int = typer.Option(0, "--skip", help="Number of results to skip for pagination"),
    take: int = typer.Option(30, "--take", help="Number of results to return"),
    pretty: bool = typer.Option(False, "--pretty", "-p", help="Pretty-print JSON output"),
    data_only: bool = typer.Option(False, "--data-only", "-d", help="Return data only"),
) -> None:
    """
    Search the Erskine May index for terms.

    Use to find index entries by keyword. Returns matching index terms.
    """
    url = build_url(
        f"{ERSKINE_MAY_API_BASE}/Search/IndexTermSearchResults/{quote(search_term)}",
        {
            "skip": skip,
            "take": take,
        },
    )
    result = run_async(get_result(url))
    typer.echo(format_output(result, pretty, data_only))


@app.command("search-sections")
def search_erskine_may_sections(
    search_term: str = typer.Argument(..., help="Term to search for in section titles"),
    skip: int = typer.Option(0, "--skip", help="Number of results to skip for pagination"),
    take: int = typer.Option(30, "--take", help="Number of results to return"),
    pretty: bool = typer.Option(False, "--pretty", "-p", help="Pretty-print JSON output"),
    data_only: bool = typer.Option(False, "--data-only", "-d", help="Return data only"),
) -> None:
    """
    Search Erskine May section titles.

    Use to find sections by title rather than content. Returns sections with
    matching titles.
    """
    url = build_url(
        f"{ERSKINE_MAY_API_BASE}/Search/SectionSearchResults/{quote(search_term)}",
        {
            "skip": skip,
            "take": take,
        },
    )
    result = run_async(get_result(url))
    typer.echo(format_output(result, pretty, data_only))
