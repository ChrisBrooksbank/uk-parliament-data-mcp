"""Tests for HTTP client with retry logic."""
from __future__ import annotations

import json

import httpx
import pytest
from pytest_httpx import HTTPXMock

from uk_parliament_mcp.http_client import (
    ParliamentHTTPClient,
    build_url,
    get_result,
)


class TestBuildUrl:
    """Tests for build_url function."""

    def test_no_params(self):
        """build_url returns base URL when no parameters provided."""
        result = build_url("https://api.example.com/test", {})
        assert result == "https://api.example.com/test"

    def test_filters_none_values(self):
        """build_url filters out None values from parameters."""
        result = build_url(
            "https://api.example.com/test",
            {
                "param1": "value1",
                "param2": None,
                "param3": "value3",
            },
        )
        assert "param1=value1" in result
        assert "param2" not in result
        assert "param3=value3" in result

    def test_filters_empty_strings(self):
        """build_url filters out empty string values."""
        result = build_url(
            "https://api.example.com/test",
            {
                "param1": "value1",
                "param2": "",
            },
        )
        assert "param1=value1" in result
        assert "param2" not in result

    def test_converts_booleans_to_lowercase(self):
        """build_url converts boolean True/False to lowercase 'true'/'false'."""
        result = build_url("https://api.example.com/test", {"flag": True})
        assert "flag=true" in result

        result = build_url("https://api.example.com/test", {"flag": False})
        assert "flag=false" in result

    def test_url_encodes_special_characters(self):
        """build_url properly encodes special characters in values."""
        result = build_url("https://api.example.com/test", {"q": "hello world"})
        # urlencode uses + for spaces by default
        assert "hello+world" in result or "hello%20world" in result

    def test_integer_values(self):
        """build_url converts integer values to strings."""
        result = build_url("https://api.example.com/test", {"skip": 10, "take": 20})
        assert "skip=10" in result
        assert "take=20" in result

    def test_preserves_zero_value(self):
        """build_url preserves zero as a valid parameter value."""
        result = build_url("https://api.example.com/test", {"skip": 0})
        assert "skip=0" in result


class TestParliamentHTTPClient:
    """Tests for ParliamentHTTPClient class."""

    @pytest.mark.asyncio
    async def test_successful_request(self, httpx_mock: HTTPXMock):
        """Successful request returns data in expected format."""
        httpx_mock.add_response(
            url="https://api.example.com/test",
            json={"items": []},
        )

        client = ParliamentHTTPClient()
        try:
            result = await client.get_result("https://api.example.com/test")
            parsed = json.loads(result)

            assert parsed["url"] == "https://api.example.com/test"
            assert "data" in parsed
            assert "error" not in parsed
        finally:
            await client.close()

    @pytest.mark.asyncio
    async def test_returns_error_on_404(self, httpx_mock: HTTPXMock):
        """404 response returns error with status code."""
        httpx_mock.add_response(
            url="https://api.example.com/test",
            status_code=404,
        )

        client = ParliamentHTTPClient()
        try:
            result = await client.get_result("https://api.example.com/test")
            parsed = json.loads(result)

            assert "error" in parsed
            assert parsed["statusCode"] == 404
            assert parsed["url"] == "https://api.example.com/test"
        finally:
            await client.close()

    @pytest.mark.asyncio
    async def test_retries_on_500_error(self, httpx_mock: HTTPXMock):
        """500 errors are retried up to MAX_RETRY_ATTEMPTS times."""
        # First two attempts fail, third succeeds
        httpx_mock.add_response(status_code=500)
        httpx_mock.add_response(status_code=500)
        httpx_mock.add_response(json={"success": True})

        client = ParliamentHTTPClient()
        try:
            result = await client.get_result("https://api.example.com/test")
            parsed = json.loads(result)

            assert "data" in parsed
            assert "error" not in parsed
        finally:
            await client.close()

    @pytest.mark.asyncio
    async def test_max_retries_exceeded(self, httpx_mock: HTTPXMock):
        """After MAX_RETRY_ATTEMPTS, returns error."""
        # All attempts fail
        httpx_mock.add_response(status_code=503)
        httpx_mock.add_response(status_code=503)
        httpx_mock.add_response(status_code=503)

        client = ParliamentHTTPClient()
        try:
            result = await client.get_result("https://api.example.com/test")
            parsed = json.loads(result)

            assert "error" in parsed
            assert parsed["statusCode"] == 503
        finally:
            await client.close()

    @pytest.mark.asyncio
    async def test_no_retry_on_400_error(self, httpx_mock: HTTPXMock):
        """400 errors are not retried (not transient)."""
        httpx_mock.add_response(status_code=400)

        client = ParliamentHTTPClient()
        try:
            result = await client.get_result("https://api.example.com/test")
            parsed = json.loads(result)

            assert "error" in parsed
            assert parsed["statusCode"] == 400
            # Should have only made one request
            assert len(httpx_mock.get_requests()) == 1
        finally:
            await client.close()

    @pytest.mark.asyncio
    async def test_timeout_handling(self, httpx_mock: HTTPXMock):
        """Timeout exceptions are caught and retried."""

        def raise_timeout(request: httpx.Request) -> httpx.Response:
            raise httpx.TimeoutException("Connection timed out")

        httpx_mock.add_callback(raise_timeout)
        httpx_mock.add_callback(raise_timeout)
        httpx_mock.add_callback(raise_timeout)

        client = ParliamentHTTPClient()
        try:
            result = await client.get_result("https://api.example.com/test")
            parsed = json.loads(result)

            assert "error" in parsed
            assert "timed out" in parsed["error"]
        finally:
            await client.close()

    @pytest.mark.asyncio
    async def test_client_reuse(self, httpx_mock: HTTPXMock):
        """Client instance is reused across multiple requests."""
        httpx_mock.add_response(json={"request": 1})
        httpx_mock.add_response(json={"request": 2})

        client = ParliamentHTTPClient()
        try:
            result1 = await client.get_result("https://api.example.com/test1")
            result2 = await client.get_result("https://api.example.com/test2")

            assert "data" in json.loads(result1)
            assert "data" in json.loads(result2)
        finally:
            await client.close()


class TestGetResultGlobal:
    """Tests for the global get_result convenience function."""

    @pytest.mark.asyncio
    async def test_global_get_result(self, httpx_mock: HTTPXMock):
        """Global get_result function works correctly."""
        httpx_mock.add_response(
            url="https://api.example.com/test",
            json={"items": ["a", "b", "c"]},
        )

        result = await get_result("https://api.example.com/test")
        parsed = json.loads(result)

        assert parsed["url"] == "https://api.example.com/test"
        assert "data" in parsed
