"""Shared utilities for CLI commands."""

from __future__ import annotations

import asyncio
import json
from collections.abc import Coroutine
from typing import Any


def run_async(coro: Coroutine[Any, Any, str]) -> str:
    """
    Run an async function synchronously for CLI use.

    Args:
        coro: An async coroutine that returns a string

    Returns:
        The result from the coroutine
    """
    return asyncio.run(coro)


def format_output(result: str, pretty: bool = False, data_only: bool = False) -> str:
    """
    Format JSON output based on CLI flags.

    Args:
        result: JSON string response from API (format: {"url": "...", "data": "..."})
        pretty: If True, pretty-print the JSON with indentation
        data_only: If True, extract only the "data" field from the wrapper

    Returns:
        Formatted JSON string ready for output
    """
    try:
        parsed = json.loads(result)

        # If data_only flag is set, extract just the data field
        if data_only and "data" in parsed:
            # The data field itself is a JSON string, so parse it
            data_content = parsed["data"]
            try:
                data_parsed = json.loads(data_content)
                parsed = data_parsed
            except (json.JSONDecodeError, TypeError):
                # If data is not valid JSON, use it as-is
                parsed = data_content

        # Apply pretty formatting if requested
        if pretty:
            return json.dumps(parsed, indent=2, ensure_ascii=False)

        return json.dumps(parsed, ensure_ascii=False)

    except json.JSONDecodeError:
        # If the result is not valid JSON, return it as-is
        return result
