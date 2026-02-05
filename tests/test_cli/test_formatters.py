"""Tests for CLI formatters."""

from __future__ import annotations

import json

import pytest

from uk_parliament_mcp.cli.formatters import (
    CLIFormatter,
    OutputFormat,
    _detect_columns,
    _extract_items,
    _get_nested_value,
)


class TestGetNestedValue:
    """Tests for _get_nested_value helper."""

    def test_simple_key(self) -> None:
        """Test getting a simple key."""
        obj = {"name": "Test", "id": 123}
        assert _get_nested_value(obj, "name") == "Test"
        assert _get_nested_value(obj, "id") == 123

    def test_nested_key(self) -> None:
        """Test getting a nested key with dot notation."""
        obj = {"party": {"name": "Labour", "id": 1}}
        assert _get_nested_value(obj, "party.name") == "Labour"
        assert _get_nested_value(obj, "party.id") == 1

    def test_deeply_nested_key(self) -> None:
        """Test getting a deeply nested key."""
        obj = {"level1": {"level2": {"level3": "value"}}}
        assert _get_nested_value(obj, "level1.level2.level3") == "value"

    def test_missing_key(self) -> None:
        """Test missing key returns None."""
        obj = {"name": "Test"}
        assert _get_nested_value(obj, "missing") is None
        assert _get_nested_value(obj, "missing.nested") is None

    def test_non_dict_intermediate(self) -> None:
        """Test non-dict intermediate value returns None."""
        obj = {"name": "Test"}
        assert _get_nested_value(obj, "name.nested") is None


class TestExtractItems:
    """Tests for _extract_items helper."""

    def test_list_input(self) -> None:
        """Test extracting items from a list."""
        data = [{"id": 1}, {"id": 2}]
        assert _extract_items(data) == [{"id": 1}, {"id": 2}]

    def test_dict_with_items_key(self) -> None:
        """Test extracting items from dict with 'items' key."""
        data = {"items": [{"id": 1}, {"id": 2}], "total": 2}
        assert _extract_items(data) == [{"id": 1}, {"id": 2}]

    def test_dict_with_results_key(self) -> None:
        """Test extracting items from dict with 'results' key."""
        data = {"results": [{"id": 1}], "count": 1}
        assert _extract_items(data) == [{"id": 1}]

    def test_dict_with_data_key(self) -> None:
        """Test extracting items from dict with 'data' key."""
        data = {"data": [{"id": 1}]}
        assert _extract_items(data) == [{"id": 1}]

    def test_single_dict(self) -> None:
        """Test wrapping single dict in list."""
        data = {"id": 1, "name": "Test"}
        assert _extract_items(data) == [{"id": 1, "name": "Test"}]

    def test_empty_list(self) -> None:
        """Test empty list returns empty."""
        assert _extract_items([]) == []

    def test_non_dict_items_filtered(self) -> None:
        """Test non-dict items are filtered out."""
        data = [{"id": 1}, "string", 123, {"id": 2}]
        assert _extract_items(data) == [{"id": 1}, {"id": 2}]


class TestDetectColumns:
    """Tests for _detect_columns helper."""

    def test_member_columns_detected(self) -> None:
        """Test member columns are detected by nameDisplayAs."""
        items = [{"nameDisplayAs": "John Doe", "latestParty": {"name": "Labour"}}]
        columns = _detect_columns(items)
        assert any(col[0] == "nameDisplayAs" for col in columns)

    def test_bill_columns_detected(self) -> None:
        """Test bill columns are detected by billId."""
        items = [{"billId": 123, "shortTitle": "Test Bill"}]
        columns = _detect_columns(items)
        assert any(col[0] == "billId" for col in columns)

    def test_division_columns_detected(self) -> None:
        """Test division columns are detected by DivisionId."""
        items = [{"DivisionId": 1, "AyeCount": 100, "NoCount": 50}]
        columns = _detect_columns(items)
        assert any(col[0] == "DivisionId" for col in columns)

    def test_committee_columns_detected(self) -> None:
        """Test committee columns are detected."""
        items = [{"name": "Treasury Committee", "isCommons": True}]
        columns = _detect_columns(items)
        assert any(col[0] == "name" for col in columns)

    def test_fallback_columns(self) -> None:
        """Test fallback to first few keys."""
        items = [{"foo": 1, "bar": 2, "baz": 3}]
        columns = _detect_columns(items)
        assert len(columns) <= 6
        assert any(col[0] == "foo" for col in columns)

    def test_empty_items(self) -> None:
        """Test empty items returns empty columns."""
        assert _detect_columns([]) == []

    def test_nested_value_structure(self) -> None:
        """Test handling of nested 'value' structure from members API."""
        items = [{"value": {"nameDisplayAs": "John", "latestParty": {"name": "Lab"}}}]
        columns = _detect_columns(items)
        assert any(col[0] == "nameDisplayAs" for col in columns)


class TestCLIFormatterJSON:
    """Tests for CLIFormatter JSON output."""

    @pytest.fixture
    def sample_response(self) -> str:
        """Sample JSON response from Parliament API."""
        return json.dumps(
            {
                "url": "https://api.parliament.uk/test",
                "data": json.dumps(
                    {"items": [{"id": 1, "name": "Test"}], "total": 1}
                ),
            }
        )

    def test_json_format_default(self, sample_response: str) -> None:
        """Test default JSON format returns compact JSON."""
        formatter = CLIFormatter(OutputFormat.JSON)
        result = formatter.format_output(sample_response)
        # Should be valid JSON
        parsed = json.loads(result)
        assert "url" in parsed

    def test_json_format_pretty(self, sample_response: str) -> None:
        """Test pretty JSON format adds indentation."""
        formatter = CLIFormatter(OutputFormat.JSON, pretty=True)
        result = formatter.format_output(sample_response)
        assert "\n" in result
        assert "  " in result

    def test_json_format_data_only(self, sample_response: str) -> None:
        """Test data_only extracts just the data field."""
        formatter = CLIFormatter(OutputFormat.JSON, data_only=True)
        result = formatter.format_output(sample_response)
        parsed = json.loads(result)
        assert "url" not in parsed
        assert "items" in parsed

    def test_json_format_invalid_json(self) -> None:
        """Test invalid JSON returns input as-is."""
        formatter = CLIFormatter(OutputFormat.JSON)
        result = formatter.format_output("not json")
        assert result == "not json"


class TestCLIFormatterTable:
    """Tests for CLIFormatter table output."""

    @pytest.fixture
    def member_response(self) -> str:
        """Sample member search response."""
        return json.dumps(
            {
                "url": "https://api.parliament.uk/test",
                "data": json.dumps(
                    {
                        "items": [
                            {
                                "value": {
                                    "id": 4514,
                                    "nameDisplayAs": "Keir Starmer",
                                    "latestParty": {"name": "Labour"},
                                    "latestHouseMembership": {
                                        "membershipFrom": "Holborn and St Pancras"
                                    },
                                }
                            }
                        ]
                    }
                ),
            }
        )

    def test_table_format_produces_output(self, member_response: str) -> None:
        """Test table format produces non-empty output."""
        formatter = CLIFormatter(OutputFormat.TABLE, data_only=True)
        result = formatter.format_output(member_response)
        assert len(result) > 0
        # Should contain table elements
        assert "Keir Starmer" in result or "4514" in result

    def test_table_format_empty_data(self) -> None:
        """Test table format with empty data."""
        response = json.dumps({"items": []})
        formatter = CLIFormatter(OutputFormat.TABLE)
        result = formatter.format_output(response)
        assert result == "(No data to display)"

    def test_table_format_no_items(self) -> None:
        """Test table format when no items can be extracted."""
        response = json.dumps({"error": "Not found"})
        formatter = CLIFormatter(OutputFormat.TABLE)
        result = formatter.format_output(response)
        # Single dict should still produce output
        assert len(result) > 0


class TestCLIFormatterMarkdown:
    """Tests for CLIFormatter markdown output."""

    @pytest.fixture
    def bill_response(self) -> str:
        """Sample bill search response."""
        return json.dumps(
            {
                "items": [
                    {
                        "billId": 123,
                        "shortTitle": "Test Bill",
                        "currentStage": {"description": "Second Reading"},
                        "lastUpdate": "2024-01-15",
                    }
                ]
            }
        )

    def test_markdown_format_produces_table(self, bill_response: str) -> None:
        """Test markdown format produces markdown table."""
        formatter = CLIFormatter(OutputFormat.MARKDOWN)
        result = formatter.format_output(bill_response)
        # Should have header row
        assert "|" in result
        # Should have separator row
        assert "---" in result
        # Should have data
        assert "Test Bill" in result

    def test_markdown_format_header_row(self, bill_response: str) -> None:
        """Test markdown has proper header row."""
        formatter = CLIFormatter(OutputFormat.MARKDOWN)
        result = formatter.format_output(bill_response)
        lines = result.split("\n")
        assert len(lines) >= 3  # Header, separator, at least one data row
        assert lines[0].startswith("|")
        assert lines[1].startswith("|")
        assert "---" in lines[1]

    def test_markdown_format_empty_data(self) -> None:
        """Test markdown format with empty data."""
        response = json.dumps({"items": []})
        formatter = CLIFormatter(OutputFormat.MARKDOWN)
        result = formatter.format_output(response)
        assert result == "(No data to display)"

    def test_markdown_escapes_pipes(self) -> None:
        """Test markdown escapes pipe characters in values."""
        response = json.dumps({"items": [{"name": "Test | Value", "id": 1}]})
        formatter = CLIFormatter(OutputFormat.MARKDOWN)
        result = formatter.format_output(response)
        assert "\\|" in result


class TestCLIFormatterBooleanValues:
    """Tests for boolean value formatting."""

    def test_boolean_true_in_table(self) -> None:
        """Test True is formatted as 'Yes' in table."""
        response = json.dumps({"items": [{"name": "Test", "isActive": True}]})
        formatter = CLIFormatter(OutputFormat.TABLE)
        result = formatter.format_output(response)
        assert "Yes" in result

    def test_boolean_false_in_markdown(self) -> None:
        """Test False is formatted as 'No' in markdown."""
        response = json.dumps({"items": [{"name": "Test", "isActive": False}]})
        formatter = CLIFormatter(OutputFormat.MARKDOWN)
        result = formatter.format_output(response)
        assert "No" in result


class TestOutputFormatEnum:
    """Tests for OutputFormat enum."""

    def test_enum_values(self) -> None:
        """Test enum has expected values."""
        assert OutputFormat.JSON.value == "json"
        assert OutputFormat.TABLE.value == "table"
        assert OutputFormat.MARKDOWN.value == "markdown"

    def test_enum_is_string(self) -> None:
        """Test enum inherits from str."""
        assert isinstance(OutputFormat.JSON, str)
        assert OutputFormat.JSON == "json"
