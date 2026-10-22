"""Tests for CLI deposited-papers commands."""

from __future__ import annotations

import json
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

from typer.testing import CliRunner

from uk_parliament_mcp.cli.main import app
from uk_parliament_mcp.config import DEPOSITED_PAPERS_API_BASE

RESPONSE = json.dumps({"url": "https://test", "data": json.dumps({"totalResults": 1})})


def _run(cli_runner: CliRunner, args: list[str]) -> tuple[str, str]:
    """Invoke the CLI with get_result mocked; return (url requested, stdout)."""
    urls: list[str] = []

    async def mock_get_result(url: str) -> str:
        urls.append(url)
        return RESPONSE

    with patch("uk_parliament_mcp.cli.utils.get_result", new=mock_get_result):
        result = cli_runner.invoke(app, ["deposited-papers", *args])

    assert result.exit_code == 0, result.output
    assert len(urls) == 1
    return urls[0], result.stdout


class TestDepositedPapersCommands:
    """Each command builds the same URL as its MCP tool twin."""

    def test_group_help_lists_commands(self, cli_runner: CliRunner):
        result = cli_runner.invoke(app, ["deposited-papers", "--help"])
        assert result.exit_code == 0
        assert "search" in result.stdout
        assert "get" in result.stdout

    def test_search_maps_options(self, cli_runner: CliRunner):
        url, stdout = _run(
            cli_runner,
            [
                "search",
                "defence",
                "--house",
                "Commons",
                "--from",
                "2025-01-01",
                "--to",
                "2025-12-31",
                "--department-id",
                "17",
                "--order-by",
                "CommitmentDateDesc",
                "--skip",
                "20",
                "--take",
                "10",
            ],
        )
        parts = urlsplit(url)
        assert f"{parts.scheme}://{parts.netloc}{parts.path}" == (
            f"{DEPOSITED_PAPERS_API_BASE}/DepositedPapers"
        )
        assert parse_qs(parts.query) == {
            "Terms": ["defence"],
            "House": ["Commons"],
            "DepositedFrom": ["2025-01-01"],
            "DepositedTo": ["2025-12-31"],
            "DepartmentSesId": ["17"],
            "OrderBy": ["CommitmentDateDesc"],
            "Skip": ["20"],
            "Take": ["10"],
        }
        assert json.loads(stdout) == {"totalResults": 1}

    def test_search_without_arguments(self, cli_runner: CliRunner):
        url, _ = _run(cli_runner, ["search"])
        assert url == f"{DEPOSITED_PAPERS_API_BASE}/DepositedPapers"

    def test_get(self, cli_runner: CliRunner):
        url, _ = _run(cli_runner, ["get", "2288285"])
        assert url == f"{DEPOSITED_PAPERS_API_BASE}/DepositedPapers/2288285"
