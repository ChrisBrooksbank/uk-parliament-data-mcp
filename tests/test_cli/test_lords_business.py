"""Tests for CLI lords-business commands."""

from __future__ import annotations

import json
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

import pytest
from typer.testing import CliRunner

from uk_parliament_mcp.cli.main import app
from uk_parliament_mcp.config import LORDS_BUSINESS_API_BASE

RESPONSE = json.dumps({"url": "https://test", "data": json.dumps([{"SectionId": 40}])})


def _run(cli_runner: CliRunner, args: list[str]) -> tuple[str, str]:
    """Invoke the CLI with get_result mocked; return (url requested, stdout)."""
    urls: list[str] = []

    async def mock_get_result(url: str) -> str:
        urls.append(url)
        return RESPONSE

    with patch("uk_parliament_mcp.cli.utils.get_result", new=mock_get_result):
        result = cli_runner.invoke(app, ["lords-business", *args])

    assert result.exit_code == 0, result.output
    assert len(urls) == 1
    return urls[0], result.stdout


class TestLordsBusinessCommands:
    """Each command builds the same URL as its MCP tool twin."""

    def test_group_help_lists_commands(self, cli_runner: CliRunner):
        result = cli_runner.invoke(app, ["lords-business", "--help"])
        assert result.exit_code == 0
        for command in ("sections", "journal-volumes", "search-written-questions"):
            assert command in result.stdout

    @pytest.mark.parametrize(
        ("args", "path"),
        [
            (["sections"], "GetSections.json"),
            (["documents", "2025-01-15"], "Day/DocumentForDay.json/2025-01-15"),
            (["document", "5947"], "DocumentForDay/5947"),
            (["non-sitting-days", "1", "2025"], "NonSittingDays.json/1/2025"),
            (["journal-volumes"], "journal-volumes"),
            (["journal-volume", "30"], "journal-volumes/30"),
            (["journal-sittings", "2020-01-15", "Papers"], "sittings/2020-01-15/Papers"),
            (["journal-attachment", "9"], "journal-attachments/9"),
            (["legacy-business", "2020-01-15"], "legacybusiness/2020-01-15"),
            (["written-question", "150323"], "WrittenQuestions/150323.json"),
        ],
    )
    def test_path_only_commands(self, cli_runner: CliRunner, args: list[str], path: str):
        url, stdout = _run(cli_runner, args)
        assert url == f"{LORDS_BUSINESS_API_BASE}/{path}"
        assert json.loads(stdout) == [{"SectionId": 40}]

    @pytest.mark.parametrize(
        ("args", "path", "query"),
        [
            (
                ["sections-for-date", "2025-01-15"],
                "GetSectionsForDate.json",
                {"businessPaperDate": ["2025-01-15"]},
            ),
            (
                ["section-data", "--date", "2025-01-15", "--section-id", "40"],
                "GetData.json",
                {"BusinessPaperDate": ["2025-01-15"], "SectionId": ["40"]},
            ),
            (
                ["item-summary", "7", "2025-01-15"],
                "ItemOfBusinessSummary.json",
                {"itemOfBusinessId": ["7"], "businessPaperDate": ["2025-01-15"]},
            ),
            (
                ["divisions-exist", "2025-01-15"],
                "DivisionsExistForDate.json",
                {"date": ["2025-01-15"]},
            ),
            (
                ["next-prev-days", "2025-01-15"],
                "GetNextPrevDaysWithItemsOfBusiness.json",
                {"initialDate": ["2025-01-15"]},
            ),
            (
                ["journal-general-index", "30", "--starting-with", "A"],
                "journal-volumes/30/general-index",
                {"StartingWith": ["A"]},
            ),
            (
                ["journal-membership-index", "30", "--starting-with", "A"],
                "journal-volumes/30/membership-index",
                {"StartingWith": ["A"]},
            ),
            (
                ["journal-index-item", "abc-123", "30"],
                "index-items/abc-123",
                {"journalVolumeId": ["30"]},
            ),
            (
                ["journal-dates", "--from", "2020-01-01", "--to", "2020-12-31"],
                "sittings/journalContentDates",
                {"startDate": ["2020-01-01"], "endDate": ["2020-12-31"]},
            ),
            (
                ["journal-volumes", "--skip", "5", "--take", "10"],
                "journal-volumes",
                {"Skip": ["5"], "Take": ["10"]},
            ),
            (
                ["non-sitting-days", "12", "2024", "--source", "PublishedBusiness"],
                "NonSittingDays.json/12/2024",
                {"dataSource": ["PublishedBusiness"]},
            ),
            (
                [
                    "search-written-questions",
                    "--member-id",
                    "4689",
                    "--status",
                    "Answered",
                    "--tabled-from",
                    "2025-01-01",
                    "--tabled-to",
                    "2025-01-31",
                    "--take",
                    "5",
                ],
                "WrittenQuestions/list.json",
                {
                    "MemberId": ["4689"],
                    "Statuses": ["Answered"],
                    "TabledStartDate": ["2025-01-01"],
                    "TabledEndDate": ["2025-01-31"],
                    "Take": ["5"],
                },
            ),
        ],
    )
    def test_commands_with_query(
        self, cli_runner: CliRunner, args: list[str], path: str, query: dict[str, list[str]]
    ):
        url, _ = _run(cli_runner, args)
        parts = urlsplit(url)
        assert f"{parts.scheme}://{parts.netloc}{parts.path}" == f"{LORDS_BUSINESS_API_BASE}/{path}"
        assert parse_qs(parts.query) == query
