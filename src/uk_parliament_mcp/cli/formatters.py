"""Output formatters for CLI commands."""

from __future__ import annotations

import json
from enum import Enum
from io import StringIO
from typing import Any

from rich.console import Console
from rich.table import Table


class OutputFormat(str, Enum):
    """Output format options for CLI commands."""

    JSON = "json"
    TABLE = "table"
    MARKDOWN = "markdown"


# Column configurations for known response types
# Maps field names to display headers
MEMBER_COLUMNS = [
    ("id", "ID"),
    ("nameDisplayAs", "Name"),
    ("latestParty.name", "Party"),
    ("latestHouseMembership.membershipFrom", "Constituency"),
]

BILL_COLUMNS = [
    ("billId", "ID"),
    ("shortTitle", "Title"),
    ("currentStage.description", "Stage"),
    ("lastUpdate", "Last Update"),
]

DIVISION_COLUMNS = [
    ("DivisionId", "ID"),
    ("Title", "Title"),
    ("Date", "Date"),
    ("AyeCount", "Ayes"),
    ("NoCount", "Noes"),
]

COMMITTEE_COLUMNS = [
    ("id", "ID"),
    ("name", "Name"),
    ("house", "House"),
    ("isCommons", "Commons"),
]


def _get_nested_value(obj: dict[str, Any], path: str) -> Any:
    """Get a value from a nested dict using dot notation."""
    keys = path.split(".")
    value: Any = obj
    for key in keys:
        if isinstance(value, dict):
            value = value.get(key)
        else:
            return None
    return value


def _detect_columns(items: list[dict[str, Any]]) -> list[tuple[str, str]]:
    """Detect appropriate columns based on the data structure."""
    if not items:
        return []

    first_item = items[0]

    # Check for nested value structure (members API)
    if "value" in first_item and isinstance(first_item.get("value"), dict):
        first_item = first_item["value"]

    # Detect by presence of key fields
    if "billId" in first_item or "shortTitle" in first_item:
        return BILL_COLUMNS
    if "DivisionId" in first_item or "AyeCount" in first_item:
        return DIVISION_COLUMNS
    if "nameDisplayAs" in first_item or "latestParty" in first_item:
        return MEMBER_COLUMNS
    if "name" in first_item and ("isCommons" in first_item or "house" in first_item):
        return COMMITTEE_COLUMNS

    # Fallback: use first few keys from the item
    columns: list[tuple[str, str]] = []
    for key in list(first_item.keys())[:6]:
        if not key.startswith("_") and first_item.get(key) is not None:
            # Convert camelCase to Title Case
            header = "".join(" " + c if c.isupper() else c for c in key).strip().title()
            columns.append((key, header))
    return columns


def _extract_items(data: Any) -> list[dict[str, Any]]:
    """Extract list of items from various response structures."""
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]

    if isinstance(data, dict):
        # Common patterns in Parliament API responses
        for key in ["items", "results", "data", "divisions", "members", "bills"]:
            if key in data and isinstance(data[key], list):
                return [item for item in data[key] if isinstance(item, dict)]

        # Single item - wrap in list
        return [data]

    return []


class CLIFormatter:
    """Formatter for CLI output in various formats."""

    def __init__(
        self,
        output_format: OutputFormat = OutputFormat.JSON,
        pretty: bool = False,
        data_only: bool = False,
    ) -> None:
        """Initialize formatter.

        Args:
            output_format: The output format (json, table, markdown)
            pretty: Whether to pretty-print JSON
            data_only: Whether to extract only the data field
        """
        self.output_format = output_format
        self.pretty = pretty
        self.data_only = data_only

    def format_output(self, result: str) -> str:
        """Format the result according to the configured format.

        Args:
            result: JSON string from Parliament API

        Returns:
            Formatted output string
        """
        try:
            parsed = json.loads(result)
        except json.JSONDecodeError:
            return result

        # Extract data if requested
        data = self._extract_data(parsed)

        if self.output_format == OutputFormat.JSON:
            return self._format_json(data)
        elif self.output_format == OutputFormat.TABLE:
            return self._format_table(data)
        elif self.output_format == OutputFormat.MARKDOWN:
            return self._format_markdown(data)

        return self._format_json(data)

    def _extract_data(self, parsed: Any) -> Any:
        """Extract data from parsed response."""
        if self.data_only and isinstance(parsed, dict) and "data" in parsed:
            data_content = parsed["data"]
            if isinstance(data_content, str):
                try:
                    return json.loads(data_content)
                except (json.JSONDecodeError, TypeError):
                    return data_content
            return data_content
        return parsed

    def _format_json(self, data: Any) -> str:
        """Format data as JSON."""
        if self.pretty:
            return json.dumps(data, indent=2, ensure_ascii=False)
        return json.dumps(data, ensure_ascii=False)

    def _format_table(self, data: Any) -> str:
        """Format data as an ASCII table using rich."""
        items = _extract_items(data)

        if not items:
            return "(No data to display)"

        columns = _detect_columns(items)
        if not columns:
            return self._format_json(data)

        table = Table(show_header=True, header_style="bold")

        # Add columns
        for _, header in columns:
            table.add_column(header)

        # Add rows
        for item in items:
            # Handle nested value structure
            if "value" in item and isinstance(item.get("value"), dict):
                item = item["value"]

            row_values: list[str] = []
            for path, _ in columns:
                value = _get_nested_value(item, path)
                if value is None:
                    row_values.append("")
                elif isinstance(value, bool):
                    row_values.append("Yes" if value else "No")
                else:
                    row_values.append(str(value))
            table.add_row(*row_values)

        # Render to string
        string_io = StringIO()
        console = Console(file=string_io, force_terminal=False, width=120)
        console.print(table)
        return string_io.getvalue().rstrip()

    def _format_markdown(self, data: Any) -> str:
        """Format data as a markdown table."""
        items = _extract_items(data)

        if not items:
            return "(No data to display)"

        columns = _detect_columns(items)
        if not columns:
            return self._format_json(data)

        lines: list[str] = []

        # Header row
        headers = [header for _, header in columns]
        lines.append("| " + " | ".join(headers) + " |")

        # Separator row
        lines.append("| " + " | ".join(["---"] * len(columns)) + " |")

        # Data rows
        for item in items:
            # Handle nested value structure
            if "value" in item and isinstance(item.get("value"), dict):
                item = item["value"]

            row_values: list[str] = []
            for path, _ in columns:
                value = _get_nested_value(item, path)
                if value is None:
                    row_values.append("")
                elif isinstance(value, bool):
                    row_values.append("Yes" if value else "No")
                else:
                    # Escape pipe characters in markdown
                    row_values.append(str(value).replace("|", "\\|"))
            lines.append("| " + " | ".join(row_values) + " |")

        return "\n".join(lines)
