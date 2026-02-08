"""Procedures CLI commands for Erskine May parliamentary procedure."""

from __future__ import annotations

from urllib.parse import quote

import typer

from uk_parliament_mcp.cli.formatters import OutputFormat
from uk_parliament_mcp.cli.pagination import ERSKINE_MAY_PAGINATION
from uk_parliament_mcp.cli.utils import (
    DataOnlyOpt,
    FieldsOpt,
    FormatOpt,
    PrettyOpt,
    RawOpt,
    output_paginated,
    output_result,
)
from uk_parliament_mcp.config import ERSKINE_MAY_API_BASE
from uk_parliament_mcp.http_client import build_url

app = typer.Typer(
    help="Parliamentary procedure and Erskine May - rules, precedents, and procedure manual",
    no_args_is_help=True,
)


@app.command("search")
def search_erskine_may(
    search_term: str = typer.Argument(
        ..., help="Search term for parliamentary procedure rules (e.g. 'Speaker', 'amendment')"
    ),
    pretty: PrettyOpt = False,
    data_only: DataOnlyOpt = True,
    output_format: FormatOpt = OutputFormat.AUTO,
    raw: RawOpt = False,
    fields: FieldsOpt = None,
) -> None:
    """
    Search Erskine May parliamentary procedure manual.

    Use when you need to understand parliamentary rules, procedures, or precedents.
    Erskine May is the authoritative guide to parliamentary procedure.
    """
    url = f"{ERSKINE_MAY_API_BASE}/Search/ParagraphSearchResults/{quote(search_term)}"
    output_result(url, pretty, data_only, output_format, fields, raw)


@app.command("parts")
def get_erskine_may_parts(
    pretty: PrettyOpt = False,
    data_only: DataOnlyOpt = True,
    output_format: FormatOpt = OutputFormat.AUTO,
    raw: RawOpt = False,
    fields: FieldsOpt = None,
) -> None:
    """
    List all parts of Erskine May procedure manual.

    Returns the 6 major parts of parliamentary procedure with titles and descriptions.
    Use to navigate the structure of the manual.
    """
    url = f"{ERSKINE_MAY_API_BASE}/Part"
    output_result(url, pretty, data_only, output_format, fields, raw)


@app.command("part")
def get_erskine_may_part(
    part_number: int = typer.Argument(..., help="Part number (1-6)"),
    pretty: PrettyOpt = False,
    data_only: DataOnlyOpt = True,
    output_format: FormatOpt = OutputFormat.AUTO,
    raw: RawOpt = False,
    fields: FieldsOpt = None,
) -> None:
    """
    Get a specific part of Erskine May with its chapters.

    Use to explore chapters within a part of the parliamentary procedure manual.
    Returns part with title, description, and list of chapters.
    """
    url = f"{ERSKINE_MAY_API_BASE}/Part/{part_number}"
    output_result(url, pretty, data_only, output_format, fields, raw)


@app.command("chapter")
def get_erskine_may_chapter(
    chapter_number: int = typer.Argument(..., help="Chapter number"),
    pretty: PrettyOpt = False,
    data_only: DataOnlyOpt = True,
    output_format: FormatOpt = OutputFormat.AUTO,
    raw: RawOpt = False,
    fields: FieldsOpt = None,
) -> None:
    """
    Get a specific chapter of Erskine May with its sections.

    Use to explore sections within a chapter. Returns chapter with title,
    description, and list of sections.
    """
    url = f"{ERSKINE_MAY_API_BASE}/Chapter/{chapter_number}"
    output_result(url, pretty, data_only, output_format, fields, raw)


@app.command("section")
def get_erskine_may_section(
    section_id: int = typer.Argument(..., help="Section ID"),
    pretty: PrettyOpt = False,
    data_only: DataOnlyOpt = True,
    output_format: FormatOpt = OutputFormat.AUTO,
    raw: RawOpt = False,
    fields: FieldsOpt = None,
) -> None:
    """
    Get full content of an Erskine May section.

    Use to read the actual procedural content. Returns section with full text
    content and footnotes.
    """
    url = f"{ERSKINE_MAY_API_BASE}/Section/{section_id}"
    output_result(url, pretty, data_only, output_format, fields, raw)


@app.command("section-relative")
def get_erskine_may_section_relative(
    section_id: int = typer.Argument(..., help="Current section ID"),
    step: int = typer.Argument(..., help="Step offset (e.g. 1 for next, -1 for previous)"),
    pretty: PrettyOpt = False,
    data_only: DataOnlyOpt = True,
    output_format: FormatOpt = OutputFormat.AUTO,
    raw: RawOpt = False,
    fields: FieldsOpt = None,
) -> None:
    """
    Navigate to a section relative to current position.

    Use to move through sections sequentially. Returns section at offset from
    current section.
    """
    url = f"{ERSKINE_MAY_API_BASE}/Section/{section_id},{step}"
    output_result(url, pretty, data_only, output_format, fields, raw)


@app.command("paragraph")
def get_erskine_may_paragraph(
    reference: str = typer.Argument(..., help="Paragraph reference (e.g. '4.5', '12.3')"),
    pretty: PrettyOpt = False,
    data_only: DataOnlyOpt = True,
    output_format: FormatOpt = OutputFormat.AUTO,
    raw: RawOpt = False,
    fields: FieldsOpt = None,
) -> None:
    """
    Look up a specific paragraph by reference number.

    Use when you have a paragraph citation like '4.5' and need the specific
    rule content.
    """
    url = f"{ERSKINE_MAY_API_BASE}/Search/Paragraph/{quote(reference)}"
    output_result(url, pretty, data_only, output_format, fields, raw)


@app.command("browse-index")
def browse_erskine_may_index(
    start_letter: str | None = typer.Argument(None, help="Starting letter to browse from (A-Z)"),
    skip: int = typer.Option(0, "--skip", help="Number of results to skip for pagination"),
    take: int = typer.Option(30, "--take", help="Number of results to return"),
    pretty: PrettyOpt = False,
    data_only: DataOnlyOpt = True,
    output_format: FormatOpt = OutputFormat.AUTO,
    raw: RawOpt = False,
    fields: FieldsOpt = None,
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
    output_paginated(
        url, ERSKINE_MAY_PAGINATION, take, skip, pretty, data_only, output_format, fields, raw
    )


@app.command("index-term")
def get_erskine_may_index_term(
    index_term_id: int = typer.Argument(..., help="Index term ID (from browse-index)"),
    pretty: PrettyOpt = False,
    data_only: DataOnlyOpt = True,
    output_format: FormatOpt = OutputFormat.AUTO,
    raw: RawOpt = False,
    fields: FieldsOpt = None,
) -> None:
    """
    Get details of an index term.

    Use after browsing index to get term details. Returns index term with all
    paragraph references.
    """
    url = f"{ERSKINE_MAY_API_BASE}/IndexTerm/{index_term_id}"
    output_result(url, pretty, data_only, output_format, fields, raw)


@app.command("search-index")
def search_erskine_may_index(
    search_term: str = typer.Argument(..., help="Term to search for in the index"),
    skip: int = typer.Option(0, "--skip", help="Number of results to skip for pagination"),
    take: int = typer.Option(30, "--take", help="Number of results to return"),
    pretty: PrettyOpt = False,
    data_only: DataOnlyOpt = True,
    output_format: FormatOpt = OutputFormat.AUTO,
    raw: RawOpt = False,
    fields: FieldsOpt = None,
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
    output_paginated(
        url, ERSKINE_MAY_PAGINATION, take, skip, pretty, data_only, output_format, fields, raw
    )


@app.command("search-sections")
def search_erskine_may_sections(
    search_term: str = typer.Argument(..., help="Term to search for in section titles"),
    skip: int = typer.Option(0, "--skip", help="Number of results to skip for pagination"),
    take: int = typer.Option(30, "--take", help="Number of results to return"),
    pretty: PrettyOpt = False,
    data_only: DataOnlyOpt = True,
    output_format: FormatOpt = OutputFormat.AUTO,
    raw: RawOpt = False,
    fields: FieldsOpt = None,
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
    output_paginated(
        url, ERSKINE_MAY_PAGINATION, take, skip, pretty, data_only, output_format, fields, raw
    )
