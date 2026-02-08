"""Tests for CLI formatters."""

from __future__ import annotations

import json
from unittest.mock import patch

import pytest

from uk_parliament_mcp.cli.formatters import (
    CLIFormatter,
    FieldsHint,
    OutputFormat,
    _detect_columns,
    _extract_all_field_paths,
    _extract_items,
    _format_hint_text,
    _get_nested_value,
    _parse_fields,
    _resolve_format,
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

    def test_case_insensitive_fallback(self) -> None:
        """Test case-insensitive fallback when exact key not found."""
        obj = {"name": "Test", "id": 123}
        assert _get_nested_value(obj, "Name") == "Test"
        assert _get_nested_value(obj, "ID") == 123

    def test_case_insensitive_nested(self) -> None:
        """Test case-insensitive fallback on nested keys."""
        obj = {"Party": {"Name": "Labour"}}
        assert _get_nested_value(obj, "party.name") == "Labour"

    def test_exact_match_preferred_over_case_insensitive(self) -> None:
        """Test exact match is preferred when both exist."""
        obj = {"Name": "exact", "name": "lower"}
        assert _get_nested_value(obj, "Name") == "exact"
        assert _get_nested_value(obj, "name") == "lower"


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


class TestParseFields:
    """Tests for _parse_fields helper."""

    def test_simple_fields(self) -> None:
        """Test parsing simple field names."""
        result = _parse_fields("id,name")
        assert result == [("id", "Id"), ("name", "Name")]

    def test_dotted_fields(self) -> None:
        """Test parsing dotted field paths."""
        result = _parse_fields("id,latestParty.name")
        assert result[1] == ("latestParty.name", "Name")

    def test_camel_case_headers(self) -> None:
        """Test camelCase conversion to Title Case."""
        result = _parse_fields("nameDisplayAs")
        assert result[0] == ("nameDisplayAs", "Name Display As")

    def test_whitespace_handling(self) -> None:
        """Test whitespace around commas is stripped."""
        result = _parse_fields("id , name , party")
        assert len(result) == 3
        assert result[0][0] == "id"
        assert result[2][0] == "party"

    def test_empty_fields_ignored(self) -> None:
        """Test empty fields are ignored."""
        result = _parse_fields("id,,name")
        assert len(result) == 2


class TestResolveFormat:
    """Tests for _resolve_format helper."""

    def test_non_auto_passes_through(self) -> None:
        """Test non-AUTO formats pass through unchanged."""
        assert _resolve_format(OutputFormat.JSON) == OutputFormat.JSON
        assert _resolve_format(OutputFormat.TABLE) == OutputFormat.TABLE
        assert _resolve_format(OutputFormat.CSV) == OutputFormat.CSV

    @patch("uk_parliament_mcp.cli.formatters.sys")
    def test_auto_tty_resolves_to_table(self, mock_sys: object) -> None:
        """Test AUTO resolves to TABLE when stdout is a TTY."""
        import uk_parliament_mcp.cli.formatters as fmt

        original = fmt.sys
        try:
            fmt.sys = type(
                "MockSys", (), {"stdout": type("Stdout", (), {"isatty": lambda self: True})()}
            )()  # type: ignore[assignment]
            assert _resolve_format(OutputFormat.AUTO) == OutputFormat.TABLE
        finally:
            fmt.sys = original  # type: ignore[assignment]

    @patch("uk_parliament_mcp.cli.formatters.sys")
    def test_auto_pipe_resolves_to_json(self, mock_sys: object) -> None:
        """Test AUTO resolves to JSON when stdout is piped."""
        import uk_parliament_mcp.cli.formatters as fmt

        original = fmt.sys
        try:
            fmt.sys = type(
                "MockSys", (), {"stdout": type("Stdout", (), {"isatty": lambda self: False})()}
            )()  # type: ignore[assignment]
            assert _resolve_format(OutputFormat.AUTO) == OutputFormat.JSON
        finally:
            fmt.sys = original  # type: ignore[assignment]


class TestCLIFormatterJSON:
    """Tests for CLIFormatter JSON output."""

    @pytest.fixture
    def sample_response(self) -> str:
        """Sample JSON response from Parliament API."""
        return json.dumps(
            {
                "url": "https://api.parliament.uk/test",
                "data": json.dumps({"items": [{"id": 1, "name": "Test"}], "total": 1}),
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

    def test_table_with_custom_fields(self) -> None:
        """Test table format with custom fields parameter."""
        response = json.dumps({"items": [{"id": 1, "name": "Test", "extra": "data"}]})
        formatter = CLIFormatter(OutputFormat.TABLE, fields="id,name")
        result = formatter.format_output(response)
        assert "Test" in result
        # extra field should not be shown (only id and name columns)


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


class TestCLIFormatterCSV:
    """Tests for CLIFormatter CSV output."""

    def test_csv_format_produces_output(self) -> None:
        """Test CSV format produces CSV with header and data."""
        response = json.dumps(
            {
                "items": [
                    {
                        "billId": 123,
                        "shortTitle": "Test Bill",
                        "currentStage": {"description": "Second Reading"},
                        "lastUpdate": "2024-01-15",
                    },
                ]
            }
        )
        formatter = CLIFormatter(OutputFormat.CSV)
        result = formatter.format_output(response)
        lines = result.strip().split("\n")
        assert len(lines) == 2  # Header + 1 data row
        assert "ID" in lines[0]
        assert "123" in lines[1]
        assert "Test Bill" in lines[1]

    def test_csv_format_empty_data(self) -> None:
        """Test CSV format with empty data."""
        response = json.dumps({"items": []})
        formatter = CLIFormatter(OutputFormat.CSV)
        result = formatter.format_output(response)
        assert result == "(No data to display)"

    def test_csv_format_multiple_rows(self) -> None:
        """Test CSV with multiple rows."""
        response = json.dumps({"items": [{"name": "Alice", "id": 1}, {"name": "Bob", "id": 2}]})
        formatter = CLIFormatter(OutputFormat.CSV)
        result = formatter.format_output(response)
        lines = result.strip().split("\n")
        assert len(lines) == 3  # Header + 2 data rows

    def test_csv_escapes_commas(self) -> None:
        """Test CSV properly handles values with commas."""
        response = json.dumps({"items": [{"name": "Doe, John", "id": 1}]})
        formatter = CLIFormatter(OutputFormat.CSV)
        result = formatter.format_output(response)
        # csv module wraps values with commas in quotes
        assert '"Doe, John"' in result

    def test_csv_with_custom_fields(self) -> None:
        """Test CSV with custom fields selection."""
        response = json.dumps({"items": [{"id": 1, "name": "Test", "extra": "data"}]})
        formatter = CLIFormatter(OutputFormat.CSV, fields="id,name")
        result = formatter.format_output(response)
        lines = result.strip().split("\n")
        assert "Id" in lines[0]
        assert "Name" in lines[0]
        # extra should not appear in header
        assert "Extra" not in lines[0]

    def test_csv_boolean_values(self) -> None:
        """Test CSV formats booleans as Yes/No."""
        response = json.dumps({"items": [{"name": "Test", "isActive": True}]})
        formatter = CLIFormatter(OutputFormat.CSV)
        result = formatter.format_output(response)
        assert "Yes" in result


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
        assert OutputFormat.CSV.value == "csv"
        assert OutputFormat.AUTO.value == "auto"

    def test_enum_is_string(self) -> None:
        """Test enum inherits from str."""
        assert isinstance(OutputFormat.JSON, str)
        assert OutputFormat.JSON == "json"


class TestExtractAllFieldPaths:
    """Tests for _extract_all_field_paths helper."""

    def test_flat_dict(self) -> None:
        """Test flat dict produces simple paths."""
        item = {"id": 1, "name": "Test", "active": True}
        paths = _extract_all_field_paths(item)
        assert paths == ["active", "id", "name"]

    def test_nested_dict(self) -> None:
        """Test nested dict produces dot-notation paths."""
        item = {"id": 1, "party": {"name": "Labour", "id": 15}}
        paths = _extract_all_field_paths(item)
        assert "party" in paths
        assert "party.id" in paths
        assert "party.name" in paths

    def test_depth_limit(self) -> None:
        """Test recursion stops at max_depth."""
        item = {"a": {"b": {"c": {"d": "deep"}}}}
        paths = _extract_all_field_paths(item, max_depth=2)
        assert "a" in paths
        assert "a.b" in paths
        # depth=2 means we go into 'a' (depth 2->1) then 'b' (depth 1->0, no recurse)
        assert "a.b.c" not in paths

    def test_list_values_not_recursed(self) -> None:
        """Test list values are noted as key only, not recursed into."""
        item = {"id": 1, "tags": ["a", "b"]}
        paths = _extract_all_field_paths(item)
        assert "tags" in paths
        # Should not recurse into list elements
        assert len([p for p in paths if p.startswith("tags.")]) == 0

    def test_underscore_keys_skipped(self) -> None:
        """Test keys starting with _ are skipped."""
        item = {"id": 1, "_internal": "hidden", "name": "Test"}
        paths = _extract_all_field_paths(item)
        assert "_internal" not in paths
        assert "id" in paths

    def test_empty_dict(self) -> None:
        """Test empty dict returns empty list."""
        assert _extract_all_field_paths({}) == []

    def test_sorted_output(self) -> None:
        """Test output is sorted."""
        item = {"zebra": 1, "alpha": 2, "middle": 3}
        paths = _extract_all_field_paths(item)
        assert paths == sorted(paths)


class TestBuildFieldsHint:
    """Tests for CLIFormatter._build_fields_hint."""

    def test_correct_showing_available_split(self) -> None:
        """Test showing/available are correctly split."""
        items = [{"id": 1, "name": "Test", "extra": "data", "score": 99}]
        columns = [("id", "ID"), ("name", "Name")]
        formatter = CLIFormatter(OutputFormat.TABLE)
        hint = formatter._build_fields_hint(items, columns)
        assert hint is not None
        assert hint.showing == ["id", "name"]
        assert "extra" in hint.available
        assert "score" in hint.available
        assert "id" not in hint.available
        assert "name" not in hint.available

    def test_value_wrapper_handling(self) -> None:
        """Test items with 'value' wrapper are unwrapped."""
        items = [{"value": {"id": 1, "name": "Test", "extra": "data"}}]
        columns = [("id", "ID")]
        formatter = CLIFormatter(OutputFormat.TABLE)
        hint = formatter._build_fields_hint(items, columns)
        assert hint is not None
        assert "name" in hint.available
        assert "extra" in hint.available

    def test_empty_items(self) -> None:
        """Test empty items returns None."""
        formatter = CLIFormatter(OutputFormat.TABLE)
        hint = formatter._build_fields_hint([], [("id", "ID")])
        assert hint is None

    def test_nested_fields_in_available(self) -> None:
        """Test nested fields appear in available."""
        items = [{"id": 1, "party": {"name": "Lab", "abbr": "L"}}]
        columns = [("id", "ID")]
        formatter = CLIFormatter(OutputFormat.TABLE)
        hint = formatter._build_fields_hint(items, columns)
        assert hint is not None
        assert "party.name" in hint.available
        assert "party.abbr" in hint.available


class TestFormatHintText:
    """Tests for _format_hint_text helper."""

    def test_output_format(self) -> None:
        """Test hint text has expected structure."""
        hint = FieldsHint(showing=["id", "name"], available=["extra", "score"])
        text = _format_hint_text(hint)
        assert "Showing: id, name" in text
        assert "Available: extra, score" in text
        assert "Tip: use --fields" in text

    def test_all_available_fields_shown(self) -> None:
        """Test all available fields are shown without truncation."""
        available = [f"field{i}" for i in range(20)]
        hint = FieldsHint(showing=["id"], available=available)
        text = _format_hint_text(hint)
        # All fields should be present
        assert "field0" in text
        assert "field19" in text
        assert "(+" not in text

    def test_no_available_fields(self) -> None:
        """Test hint when no extra fields are available."""
        hint = FieldsHint(showing=["id", "name"], available=[])
        text = _format_hint_text(hint)
        assert "Showing: id, name" in text
        assert "Available:" not in text
        assert "Tip:" in text

    def test_tip_includes_example(self) -> None:
        """Test tip includes example with field names."""
        hint = FieldsHint(showing=["id", "name"], available=["extra"])
        text = _format_hint_text(hint)
        assert '--fields "id,name,extra"' in text


class TestFieldsHintIntegration:
    """Tests that fields_hint is set after formatting."""

    def test_table_format_sets_hint(self) -> None:
        """Test _format_table sets fields_hint."""
        response = json.dumps({"items": [{"id": 1, "name": "Test", "extra": "data"}]})
        formatter = CLIFormatter(OutputFormat.TABLE)
        formatter.format_output(response)
        assert formatter.fields_hint is not None
        assert len(formatter.fields_hint.showing) > 0

    def test_markdown_format_sets_hint(self) -> None:
        """Test _format_markdown sets fields_hint."""
        response = json.dumps({"items": [{"id": 1, "name": "Test"}]})
        formatter = CLIFormatter(OutputFormat.MARKDOWN)
        formatter.format_output(response)
        assert formatter.fields_hint is not None

    def test_csv_format_sets_hint(self) -> None:
        """Test _format_csv sets fields_hint."""
        response = json.dumps({"items": [{"id": 1, "name": "Test"}]})
        formatter = CLIFormatter(OutputFormat.CSV)
        formatter.format_output(response)
        assert formatter.fields_hint is not None

    def test_json_format_does_not_set_hint(self) -> None:
        """Test _format_json does NOT set fields_hint."""
        response = json.dumps({"items": [{"id": 1, "name": "Test"}]})
        formatter = CLIFormatter(OutputFormat.JSON)
        formatter.format_output(response)
        assert formatter.fields_hint is None
