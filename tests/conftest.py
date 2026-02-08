"""Pytest fixtures for UK Parliament MCP Server tests."""

from __future__ import annotations

import pytest

from uk_parliament_mcp.http_client import ParliamentHTTPClient
from uk_parliament_mcp.server import create_server


@pytest.fixture
def mcp_server():
    """Create a fresh MCP server instance for testing."""
    return create_server()


@pytest.fixture
async def http_client():
    """Create an HTTP client and clean up after test."""
    client = ParliamentHTTPClient()
    yield client
    await client.close()
