"""Shared utilities for CLI commands."""

from __future__ import annotations

import asyncio
import sys
from collections.abc import Coroutine
from typing import Any

from uk_parliament_mcp.cli.formatters import CLIFormatter, OutputFormat


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

    Args:
        coro: An async coroutine that returns a string

    Returns:
        The result from the coroutine
    """
    return asyncio.run(coro)


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
