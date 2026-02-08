"""Output formatters for CLI commands."""

from __future__ import annotations

import csv
import json
import sys
from dataclasses import dataclass
from dataclasses import field as dataclass_field
from enum import StrEnum
from io import StringIO
from typing import Any

from rich.console import Console
from rich.json import JSON
from rich.table import Table


@dataclass
class FieldsHint:
    """Tracks which fields are shown and which are available."""

    showing: list[str] = dataclass_field(default_factory=list)
    available: list[str] = dataclass_field(default_factory=list)


class OutputFormat(StrEnum):
    """Output format options for CLI commands."""

    JSON = "json"
    TABLE = "table"
    MARKDOWN = "markdown"
    CSV = "csv"
    AUTO = "auto"


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
        for key in [
            "items",
            "results",
            "Results",
            "searchResults",
            "data",
            "divisions",
            "members",
            "bills",
        ]:
            if key in data and isinstance(data[key], list):
                return [item for item in data[key] if isinstance(item, dict)]

        # Single item - wrap in list
        return [data]

    return []


def _parse_fields(fields: str) -> list[tuple[str, str]]:
    """Parse a comma-separated fields string into column tuples.

    Args:
        fields: Comma-separated field paths (e.g., "id,nameDisplayAs,latestParty.name").

    Returns:
        List of (path, header) tuples.
    """
    columns: list[tuple[str, str]] = []
    for field in fields.split(","):
        field = field.strip()
        if field:
            # Use last part of path as header, converting camelCase to Title Case
            last_part = field.split(".")[-1]
            header = "".join(" " + c if c.isupper() else c for c in last_part).strip().title()
            columns.append((field, header))
    return columns


def _extract_all_field_paths(
    item: dict[str, Any], prefix: str = "", max_depth: int = 3
) -> list[str]:
    """Recursively extract all dot-notation field paths from a dict.

    Args:
        item: Dictionary to extract paths from.
        prefix: Current dot-notation prefix.
        max_depth: Maximum recursion depth.

    Returns:
        Sorted list of dot-notation paths.
    """
    if max_depth <= 0:
        return []
    paths: list[str] = []
    for key, value in item.items():
        if key.startswith("_"):
            continue
        full_path = f"{prefix}{key}" if not prefix else f"{prefix}.{key}"
        paths.append(full_path)
        if isinstance(value, dict) and max_depth > 1:
            paths.extend(_extract_all_field_paths(value, full_path, max_depth - 1))
    return sorted(paths)


def _format_hint_text(hint: FieldsHint) -> str:
    """Format a FieldsHint into text for stderr output.

    Args:
        hint: The FieldsHint with showing/available fields.

    Returns:
        Formatted hint string.
    """
    lines: list[str] = []
    lines.append(f"  Showing: {', '.join(hint.showing)}")
    if hint.available:
        max_show = 15
        avail = hint.available[:max_show]
        suffix = f", (+{len(hint.available) - max_show} more)" if len(hint.available) > max_show else ""
        lines.append(f"  Available: {', '.join(avail)}{suffix}")
    example_fields = hint.showing[:2] + hint.available[:1] if hint.available else hint.showing[:3]
    lines.append(f'  Tip: use --fields to select columns, e.g. --fields "{",".join(example_fields)}"')
    return "\n".join(lines)


def _resolve_format(fmt: OutputFormat) -> OutputFormat:
    """Resolve AUTO format based on whether stdout is a TTY.

    Args:
        fmt: The requested output format.

    Returns:
        Resolved format (TABLE for TTY, JSON for pipes).
    """
    if fmt == OutputFormat.AUTO:
        return OutputFormat.TABLE if sys.stdout.isatty() else OutputFormat.JSON
    return fmt


class CLIFormatter:
    """Formatter for CLI output in various formats."""

    def __init__(
        self,
        output_format: OutputFormat = OutputFormat.AUTO,
        pretty: bool = False,
        data_only: bool = False,
        fields: str | None = None,
    ) -> None:
        """Initialize formatter.

        Args:
            output_format: The output format (json, table, markdown, csv, auto)
            pretty: Whether to pretty-print JSON
            data_only: Whether to extract only the data field
            fields: Optional comma-separated field paths for column selection
        """
        self.output_format = _resolve_format(output_format)
        self.pretty = pretty
        self.data_only = data_only
        self.fields = fields
        self.fields_hint: FieldsHint | None = None

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
        elif self.output_format == OutputFormat.CSV:
            return self._format_csv(data)

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

    def _get_columns(self, items: list[dict[str, Any]]) -> list[tuple[str, str]]:
        """Get columns, using user-specified fields if set."""
        if self.fields:
            return _parse_fields(self.fields)
        return _detect_columns(items)

    def _build_fields_hint(
        self, items: list[dict[str, Any]], columns: list[tuple[str, str]]
    ) -> FieldsHint | None:
        """Build a FieldsHint from items and the columns being displayed.

        Args:
            items: The data items.
            columns: The columns being shown.

        Returns:
            FieldsHint or None if no items.
        """
        if not items:
            return None
        first_item = items[0]
        if "value" in first_item and isinstance(first_item.get("value"), dict):
            first_item = first_item["value"]
        all_paths = _extract_all_field_paths(first_item)
        showing = [path for path, _ in columns]
        available = [p for p in all_paths if p not in showing]
        return FieldsHint(showing=showing, available=available)

    def _format_json(self, data: Any) -> str:
        """Format data as JSON.

        When pretty=True and outputting to a terminal, uses rich for
        syntax highlighting. Falls back to plain indented JSON for
        pipes/files to ensure valid JSON output.
        """
        if self.pretty:
            if sys.stdout.isatty():
                # Use rich for colored output on terminal
                string_io = StringIO()
                console = Console(file=string_io, force_terminal=True)
                console.print(JSON.from_data(data))
                return string_io.getvalue().rstrip()
            # Plain indented JSON for pipes/files
            return json.dumps(data, indent=2, ensure_ascii=False)
        return json.dumps(data, ensure_ascii=False)

    def _format_table(self, data: Any) -> str:
        """Format data as an ASCII table using rich."""
        items = _extract_items(data)

        if not items:
            return "(No data to display)"

        columns = self._get_columns(items)
        if not columns:
            return self._format_json(data)

        self.fields_hint = self._build_fields_hint(items, columns)

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

        columns = self._get_columns(items)
        if not columns:
            return self._format_json(data)

        self.fields_hint = self._build_fields_hint(items, columns)

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

    def _format_csv(self, data: Any) -> str:
        """Format data as CSV."""
        items = _extract_items(data)

        if not items:
            return "(No data to display)"

        columns = self._get_columns(items)
        if not columns:
            return self._format_json(data)

        self.fields_hint = self._build_fields_hint(items, columns)

        output = StringIO()
        writer = csv.writer(output)

        # Header row
        writer.writerow([header for _, header in columns])

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
                    row_values.append(str(value))
            writer.writerow(row_values)

        return output.getvalue().rstrip()
