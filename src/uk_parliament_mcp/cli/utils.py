"""Shared utilities for CLI commands."""

from __future__ import annotations

import asyncio
import sys
from collections.abc import Coroutine
from typing import Annotated, Any

import typer

from uk_parliament_mcp.cli.formatters import CLIFormatter, OutputFormat
from uk_parliament_mcp.http_client import clear_called_urls, get_called_urls, get_result

# ── Annotated type aliases for the 5 output params on every command ──
PrettyOpt = Annotated[bool, typer.Option("--pretty", "-p", help="Pretty-print JSON output")]
DataOnlyOpt = Annotated[
    bool,
    typer.Option("--data-only", "-d", help="Return data only (use --no-data-only for wrapper)"),
]
FormatOpt = Annotated[
    OutputFormat,
    typer.Option("--format", "-f", help="Output format: json, table, markdown, csv, auto"),
]
RawOpt = Annotated[bool, typer.Option("--raw", help="Output full wrapper JSON (url + data)")]
FieldsOpt = Annotated[
    str | None, typer.Option("--fields", help="Comma-separated field paths for columns")
]


def should_render_rich(output_format: OutputFormat, raw: bool) -> bool:
    """Determine whether to use rich rendering instead of JSON output.

    Rich rendering is used when:
    - raw mode is not enabled
    - format is AUTO or TABLE
    - stdout is a TTY (interactive terminal)

    Args:
        output_format: The requested output format.
        raw: Whether --raw flag was specified.

    Returns:
        True if rich rendering should be used.
    """
    if raw:
        return False
    if output_format in (OutputFormat.AUTO, OutputFormat.TABLE):
        return sys.stdout.isatty()
    return False


def run_async(coro: Coroutine[Any, Any, str]) -> str:
    """
    Run an async function synchronously for CLI use.

    Clears URL tracking before execution and prints all called URLs
    to stderr after the command completes.

    Args:
        coro: An async coroutine that returns a string

    Returns:
        The result from the coroutine
    """
    clear_called_urls()
    result = asyncio.run(coro)
    _print_called_urls()
    return result


def _print_called_urls() -> None:
    """Print all URLs called during command execution to stderr."""
    urls = get_called_urls()
    if urls:
        print("\nURLs called:", file=sys.stderr)
        for url in urls:
            print(f"  {url}", file=sys.stderr)


def echo_utf8(text: str) -> None:
    """
    Print text with UTF-8 encoding, avoiding Windows cp1252 encoding errors.

    Args:
        text: The text to print
    """
    if sys.platform == "win32":
        # On Windows, write directly to stdout buffer with UTF-8 encoding
        sys.stdout.buffer.write((text + "\n").encode("utf-8"))
        sys.stdout.buffer.flush()
    else:
        # On Unix-like systems, print normally
        print(text)


def format_output(
    result: str,
    pretty: bool = False,
    data_only: bool = True,
    output_format: OutputFormat = OutputFormat.AUTO,
    fields: str | None = None,
    raw: bool = False,
) -> str:
    """
    Format JSON output based on CLI flags.

    Args:
        result: JSON string response from API (format: {"url": "...", "data": "..."})
        pretty: If True, pretty-print the JSON with indentation
        data_only: If True, extract only the "data" field from the wrapper
        output_format: Output format (json, table, markdown, csv, auto)
        fields: Optional comma-separated field paths for column selection
        raw: If True, output full wrapper JSON (overrides data_only and format)

    Returns:
        Formatted string ready for output
    """
    if raw:
        data_only = False
        output_format = OutputFormat.JSON
    formatter = CLIFormatter(output_format, pretty, data_only, fields)
    return formatter.format_output(result)


def output_result(
    url: str,
    pretty: bool = False,
    data_only: bool = True,
    output_format: OutputFormat = OutputFormat.AUTO,
    fields: str | None = None,
    raw: bool = False,
) -> None:
    """Fetch a URL and print formatted output. Combines run_async + format_output + echo_utf8."""
    result = run_async(get_result(url))
    echo_utf8(format_output(result, pretty, data_only, output_format, fields, raw))


def output_paginated(
    url: str,
    config: Any,
    take: int | None,
    skip: int,
    pretty: bool = False,
    data_only: bool = True,
    output_format: OutputFormat = OutputFormat.AUTO,
    fields: str | None = None,
    raw: bool = False,
) -> None:
    """Fetch a paginated URL and print formatted output."""
    from uk_parliament_mcp.cli.pagination import paginate_request

    result = run_async(paginate_request(url, config, desired_total=take, start_skip=skip))
    echo_utf8(format_output(result, pretty, data_only, output_format, fields, raw))
