"""Shared utilities for CLI commands."""

from __future__ import annotations

import asyncio
from collections.abc import Coroutine
from typing import Any

from uk_parliament_mcp.cli.formatters import CLIFormatter, OutputFormat


def run_async(coro: Coroutine[Any, Any, str]) -> str:
    """
    Run an async function synchronously for CLI use.

    Args:
        coro: An async coroutine that returns a string

    Returns:
        The result from the coroutine
    """
    return asyncio.run(coro)


def format_output(
    result: str,
    pretty: bool = False,
    data_only: bool = False,
    output_format: OutputFormat = OutputFormat.JSON,
) -> str:
    """
    Format JSON output based on CLI flags.

    Args:
        result: JSON string response from API (format: {"url": "...", "data": "..."})
        pretty: If True, pretty-print the JSON with indentation
        data_only: If True, extract only the "data" field from the wrapper
        output_format: Output format (json, table, markdown)

    Returns:
        Formatted string ready for output
    """
    formatter = CLIFormatter(output_format, pretty, data_only)
    return formatter.format_output(result)
