"""Tests for CLI utilities."""

from __future__ import annotations

import asyncio
import json
from unittest.mock import patch

import pytest

from uk_parliament_mcp.cli.formatters import OutputFormat
from uk_parliament_mcp.cli.utils import format_output, run_async


class TestRunAsync:
    """Tests for run_async utility."""

    def test_run_async_executes_coroutine(self):
        """Test that run_async executes an async function."""

        async def sample_coro():
            await asyncio.sleep(0.001)
            return "result"

        result = run_async(sample_coro())
        assert result == "result"

    def test_run_async_handles_async_with_params(self):
        """Test run_async with async function that takes parameters."""

        async def add(a: int, b: int) -> int:
            await asyncio.sleep(0.001)
            return a + b

        result = run_async(add(2, 3))
        assert result == 5


class TestFormatOutput:
    """Tests for format_output utility."""

    @pytest.fixture
    def sample_response(self) -> str:
        """Sample JSON response from Parliament API."""
        return json.dumps(
            {
                "url": "https://members-api.parliament.uk/api/Members/1234",
                "data": {"id": 1234, "name": "Test Member", "party": "Test Party"},
            }
        )

    def test_format_output_default_extracts_data(self, sample_response: str):
        """Test default output extracts data only (new default: data_only=True)."""
        result = format_output(sample_response)
        parsed = json.loads(result)
        # Default is now data_only=True, so url wrapper is stripped
        assert "url" not in parsed
        assert parsed["id"] == 1234

    def test_format_output_raw_returns_wrapper(self, sample_response: str):
        """Test --raw flag returns full wrapper JSON."""
        result = format_output(sample_response, raw=True)
        parsed = json.loads(result)
        assert "url" in parsed
        assert parsed["data"]["id"] == 1234

    def test_format_output_pretty_adds_indentation(self, sample_response: str):
        """Test --pretty flag adds indentation."""
        result = format_output(sample_response, pretty=True)
        parsed = json.loads(result)

        # Default is data_only=True, so only data content
        assert parsed["id"] == 1234

        # Verify formatting
        assert "\n" in result
        assert "  " in result  # Indentation present

    def test_format_output_data_only_strips_wrapper(self, sample_response: str):
        """Test data_only=True strips url wrapper."""
        result = format_output(sample_response, data_only=True)
        parsed = json.loads(result)

        # Should only have data contents
        assert "url" not in parsed
        assert parsed["id"] == 1234
        assert parsed["name"] == "Test Member"

    def test_format_output_data_only_false_keeps_wrapper(self, sample_response: str):
        """Test data_only=False keeps the full wrapper."""
        result = format_output(sample_response, data_only=False, output_format=OutputFormat.JSON)
        parsed = json.loads(result)
        assert "url" in parsed
        assert parsed["data"]["id"] == 1234

    def test_format_output_data_only_and_pretty_combined(self, sample_response: str):
        """Test combining --data-only and --pretty flags."""
        result = format_output(sample_response, pretty=True, data_only=True)
        parsed = json.loads(result)

        # Should have data only
        assert "url" not in parsed
        assert parsed["id"] == 1234

        # Should be formatted
        assert "\n" in result
        assert "  " in result

    def test_format_output_handles_error_response(self):
        """Test format_output with error response structure."""
        error_response = json.dumps(
            {
                "url": "https://members-api.parliament.uk/api/Members/9999",
                "error": "Not found",
                "statusCode": 404,
            }
        )

        result = format_output(error_response, pretty=True)
        parsed = json.loads(result)

        # data_only=True but no "data" key, so full object is returned
        assert parsed["error"] == "Not found"
        assert parsed["statusCode"] == 404

    def test_format_output_data_only_with_missing_data_field(self):
        """Test data_only when response has no data field."""
        response_without_data = json.dumps({"error": "Something went wrong"})

        result = format_output(response_without_data, data_only=True)
        parsed = json.loads(result)

        # Should return the whole object if no data field
        assert parsed == {"error": "Something went wrong"}

    def test_format_output_with_fields(self, sample_response: str):
        """Test --fields parameter selects specific columns."""
        result = format_output(sample_response, fields="id,name", output_format=OutputFormat.CSV)
        assert "Id" in result
        assert "1234" in result

    def test_format_output_raw_overrides_data_only(self, sample_response: str):
        """Test --raw overrides data_only and format."""
        result = format_output(sample_response, raw=True, data_only=True)
        parsed = json.loads(result)
        # raw=True should force data_only=False and JSON format
        assert "url" in parsed


class TestFieldsHintPrinting:
    """Tests for fields hint printing to stderr."""

    @pytest.fixture
    def table_response(self) -> str:
        """Response with items that produce a table."""
        return json.dumps(
            {
                "url": "https://api.parliament.uk/test",
                "data": json.dumps({"items": [{"id": 1, "name": "Test", "extra": "hidden"}]}),
            }
        )

    @patch("uk_parliament_mcp.cli.utils.sys")
    def test_hint_printed_when_tty_and_table(self, mock_sys, table_response: str, capsys):
        """Test hint is printed to stderr when TTY + table format."""
        mock_sys.stdout.isatty.return_value = True
        mock_sys.platform = "linux"
        # Use real stderr for capsys capture
        import sys

        mock_sys.stderr = sys.stderr
        format_output(table_response, output_format=OutputFormat.TABLE, data_only=True)
        captured = capsys.readouterr()
        assert "Showing:" in captured.err
        assert "Tip:" in captured.err

    @patch("uk_parliament_mcp.cli.utils.sys")
    def test_hint_not_printed_when_piped(self, mock_sys, table_response: str, capsys):
        """Test hint is NOT printed when stdout is not a TTY."""
        mock_sys.stdout.isatty.return_value = False
        mock_sys.platform = "linux"
        import sys

        mock_sys.stderr = sys.stderr
        format_output(table_response, output_format=OutputFormat.JSON, data_only=True)
        captured = capsys.readouterr()
        assert "Showing:" not in captured.err

    @patch("uk_parliament_mcp.cli.utils.sys")
    def test_hint_not_printed_for_json_format(self, mock_sys, table_response: str, capsys):
        """Test hint is NOT printed for JSON format (no fields_hint set)."""
        mock_sys.stdout.isatty.return_value = True
        mock_sys.platform = "linux"
        import sys

        mock_sys.stderr = sys.stderr
        format_output(table_response, output_format=OutputFormat.JSON, data_only=True)
        captured = capsys.readouterr()
        assert "Showing:" not in captured.err

    @patch("uk_parliament_mcp.cli.utils.sys")
    def test_hint_not_printed_for_raw_mode(self, mock_sys, table_response: str, capsys):
        """Test hint is NOT printed for raw mode."""
        mock_sys.stdout.isatty.return_value = True
        mock_sys.platform = "linux"
        import sys

        mock_sys.stderr = sys.stderr
        format_output(table_response, raw=True)
        captured = capsys.readouterr()
        assert "Showing:" not in captured.err
