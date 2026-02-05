"""Tests for CLI utilities."""
from __future__ import annotations

import asyncio
import json

import pytest

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

    def test_format_output_default_returns_compact_json(self, sample_response: str):
        """Test default output is compact JSON."""
        result = format_output(sample_response)
        assert result == sample_response
        assert "\n" not in result  # No newlines in compact JSON

    def test_format_output_pretty_adds_indentation(self, sample_response: str):
        """Test --pretty flag adds indentation."""
        result = format_output(sample_response, pretty=True)
        parsed = json.loads(result)

        # Verify structure is preserved
        assert parsed["url"] == "https://members-api.parliament.uk/api/Members/1234"
        assert parsed["data"]["id"] == 1234

        # Verify formatting
        assert "\n" in result
        assert "  " in result  # Indentation present

    def test_format_output_data_only_strips_wrapper(self, sample_response: str):
        """Test --data-only flag strips url wrapper."""
        result = format_output(sample_response, data_only=True)
        parsed = json.loads(result)

        # Should only have data contents
        assert "url" not in parsed
        assert parsed["id"] == 1234
        assert parsed["name"] == "Test Member"

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

        assert parsed["error"] == "Not found"
        assert parsed["statusCode"] == 404

    def test_format_output_data_only_with_missing_data_field(self):
        """Test --data-only when response has no data field."""
        response_without_data = json.dumps({"error": "Something went wrong"})

        result = format_output(response_without_data, data_only=True)
        parsed = json.loads(result)

        # Should return the whole object if no data field
        assert parsed == {"error": "Something went wrong"}
