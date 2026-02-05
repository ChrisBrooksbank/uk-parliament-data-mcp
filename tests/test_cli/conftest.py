"""Pytest fixtures for CLI tests."""
from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock

import pytest
from typer.testing import CliRunner


@pytest.fixture
def cli_runner() -> CliRunner:
    """Create a Typer CLI runner for testing."""
    return CliRunner()


@pytest.fixture
def mock_http_response() -> dict[str, Any]:
    """Mock HTTP response with typical Parliament API structure."""
    return {
        "url": "https://members-api.parliament.uk/api/Members/Search?Name=Test",
        "data": {
            "items": [
                {
                    "id": 1234,
                    "name": "Test Member",
                    "party": "Test Party",
                }
            ],
            "totalResults": 1,
        },
    }


@pytest.fixture
def mock_get_result(mock_http_response: dict[str, Any], monkeypatch: pytest.MonkeyPatch):
    """Mock get_result to return test data without hitting real API."""
    import json

    async def _mock_get_result(url: str) -> str:
        """Return mocked JSON response."""
        return json.dumps(mock_http_response)

    # Patch at the http_client module level
    monkeypatch.setattr("uk_parliament_mcp.http_client.get_result", _mock_get_result)
    return _mock_get_result
