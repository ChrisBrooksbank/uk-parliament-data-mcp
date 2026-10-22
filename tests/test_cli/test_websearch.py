"""Tests for CLI search commands."""

from __future__ import annotations

import json
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

from typer.testing import CliRunner

from uk_parliament_mcp.cli.main import app
from uk_parliament_mcp.config import WEBSEARCH_API_BASE

RESPONSE = json.dumps(
    {
        "url": f"{WEBSEARCH_API_BASE}/WebSearch?searchTerms=climate",
        "data": json.dumps(
            {
                "totalResults": 1,
                "results": [
                    {
                        "title": "Climate Change Explainers",
                        "description": "<strong>Climate</strong> change fundamentals",
                        "url": "https://commonslibrary.parliament.uk/climate-change-explainers/",
                        "tags": ["Commons library"],
                    }
                ],
                "searchTerms": "climate",
                "start": 1,
                "take": 20,
            }
        ),
    }
)


class TestSearchWebsite:
    """Tests for search website command."""

    def test_website_help(self, cli_runner: CliRunner):
        """Test that website --help shows command info."""
        result = cli_runner.invoke(app, ["search", "website", "--help"])
        assert result.exit_code == 0
        assert "parliament.uk website" in result.stdout.lower()

    def test_website_builds_url_and_returns_data(self, cli_runner: CliRunner):
        """Test website passes terms and paging to /WebSearch and prints the data."""
        urls: list[str] = []

        async def mock_get_result(url: str) -> str:
            urls.append(url)
            return RESPONSE

        with patch("uk_parliament_mcp.cli.utils.get_result", new=mock_get_result):
            result = cli_runner.invoke(
                app, ["search", "website", "climate", "--start", "21", "--take", "10"]
            )

        assert result.exit_code == 0
        assert len(urls) == 1
        parts = urlsplit(urls[0])
        assert f"{parts.scheme}://{parts.netloc}{parts.path}" == f"{WEBSEARCH_API_BASE}/WebSearch"
        assert parse_qs(parts.query) == {
            "searchTerms": ["climate"],
            "start": ["21"],
            "take": ["10"],
        }
        assert json.loads(result.stdout)["totalResults"] == 1
