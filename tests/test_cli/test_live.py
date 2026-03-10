"""Tests for CLI live commands (new whatson endpoints)."""

from __future__ import annotations

import json
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from uk_parliament_mcp.cli.main import app
from uk_parliament_mcp.config import NOW_API_BASE, WHATSON_API_BASE


class TestAnnunciatorByDate:
    """Tests for annunciator-by-date command."""

    def test_help(self, cli_runner: CliRunner):
        """annunciator-by-date --help exits cleanly."""
        result = cli_runner.invoke(app, ["live", "annunciator-by-date", "--help"])
        assert result.exit_code == 0

    def test_requires_args(self, cli_runner: CliRunner):
        """annunciator-by-date requires annunciator and date arguments."""
        result = cli_runner.invoke(app, ["live", "annunciator-by-date"])
        assert result.exit_code != 0

    def test_success(self, cli_runner: CliRunner):
        """annunciator-by-date returns data for given annunciator and date."""
        mock_response = json.dumps({"url": "test", "data": json.dumps({})})

        async def mock_get_result(url: str) -> str:
            assert url == f"{NOW_API_BASE}/Message/message/CommonsMain/2024-03-15"
            return mock_response

        with patch("uk_parliament_mcp.cli.live.get_result", new=mock_get_result):
            result = cli_runner.invoke(
                app, ["live", "annunciator-by-date", "CommonsMain", "2024-03-15"]
            )

        assert result.exit_code == 0


class TestCalendarCategories:
    """Tests for calendar-categories command."""

    def test_help(self, cli_runner: CliRunner):
        """calendar-categories --help exits cleanly."""
        result = cli_runner.invoke(app, ["live", "calendar-categories", "--help"])
        assert result.exit_code == 0

    def test_success(self, cli_runner: CliRunner):
        """calendar-categories returns data."""
        mock_response = json.dumps({"url": "test", "data": json.dumps([{"id": 1, "name": "Test"}])})

        async def mock_get_result(url: str) -> str:
            return mock_response

        with patch("uk_parliament_mcp.cli.live.get_result", new=mock_get_result):
            result = cli_runner.invoke(app, ["live", "calendar-categories"])

        assert result.exit_code == 0


class TestEventTypeMetadata:
    """Tests for event-type-metadata command."""

    def test_help(self, cli_runner: CliRunner):
        """event-type-metadata --help exits cleanly."""
        result = cli_runner.invoke(app, ["live", "event-type-metadata", "--help"])
        assert result.exit_code == 0

    def test_success_no_params(self, cli_runner: CliRunner):
        """event-type-metadata with no params returns data."""
        mock_response = json.dumps({"url": "test", "data": json.dumps([])})

        async def mock_get_result(url: str) -> str:
            assert f"{WHATSON_API_BASE}/events/EventTypeMetaData.json" in url
            return mock_response

        with patch("uk_parliament_mcp.cli.live.get_result", new=mock_get_result):
            result = cli_runner.invoke(app, ["live", "event-type-metadata"])

        assert result.exit_code == 0

    def test_success_with_house(self, cli_runner: CliRunner):
        """event-type-metadata with --house filter works."""
        mock_response = json.dumps({"url": "test", "data": json.dumps([])})

        async def mock_get_result(url: str) -> str:
            assert "queryParameters.house=Commons" in url
            return mock_response

        with patch("uk_parliament_mcp.cli.live.get_result", new=mock_get_result):
            result = cli_runner.invoke(app, ["live", "event-type-metadata", "--house", "Commons"])

        assert result.exit_code == 0


class TestParliamentaryDiary:
    """Tests for parliamentary-diary command."""

    def test_help(self, cli_runner: CliRunner):
        """parliamentary-diary --help exits cleanly."""
        result = cli_runner.invoke(app, ["live", "parliamentary-diary", "--help"])
        assert result.exit_code == 0

    def test_success_with_date_range(self, cli_runner: CliRunner):
        """parliamentary-diary with date range returns data."""
        mock_response = json.dumps({"url": "test", "data": json.dumps([])})

        async def mock_get_result(url: str) -> str:
            assert f"{WHATSON_API_BASE}/events/diary.json" in url
            assert "queryParameters.startDate=2024-01-01" in url
            assert "queryParameters.endDate=2024-01-31" in url
            return mock_response

        with patch("uk_parliament_mcp.cli.live.get_result", new=mock_get_result):
            result = cli_runner.invoke(
                app,
                [
                    "live",
                    "parliamentary-diary",
                    "--start-date",
                    "2024-01-01",
                    "--end-date",
                    "2024-01-31",
                ],
            )

        assert result.exit_code == 0


class TestSpeakerEvents:
    """Tests for speaker-events command."""

    def test_help(self, cli_runner: CliRunner):
        """speaker-events --help exits cleanly."""
        result = cli_runner.invoke(app, ["live", "speaker-events", "--help"])
        assert result.exit_code == 0

    def test_success_with_date(self, cli_runner: CliRunner):
        """speaker-events with date param returns data."""
        mock_response = json.dumps({"url": "test", "data": json.dumps([])})

        async def mock_get_result(url: str) -> str:
            assert f"{WHATSON_API_BASE}/events/speakers.json" in url
            assert "queryParameters.date=2024-03-15" in url
            return mock_response

        with patch("uk_parliament_mcp.cli.live.get_result", new=mock_get_result):
            result = cli_runner.invoke(
                app, ["live", "speaker-events", "--date", "2024-03-15"]
            )

        assert result.exit_code == 0


class TestCalendarLocations:
    """Tests for calendar-locations command."""

    def test_help(self, cli_runner: CliRunner):
        """calendar-locations --help exits cleanly."""
        result = cli_runner.invoke(app, ["live", "calendar-locations", "--help"])
        assert result.exit_code == 0

    def test_success(self, cli_runner: CliRunner):
        """calendar-locations returns data."""
        mock_response = json.dumps({"url": "test", "data": json.dumps([])})

        async def mock_get_result(url: str) -> str:
            assert url == f"{WHATSON_API_BASE}/locations/list.json"
            return mock_response

        with patch("uk_parliament_mcp.cli.live.get_result", new=mock_get_result):
            result = cli_runner.invoke(app, ["live", "calendar-locations"])

        assert result.exit_code == 0


class TestAnnulmentDate:
    """Tests for annulment-date command."""

    def test_help(self, cli_runner: CliRunner):
        """annulment-date --help exits cleanly."""
        result = cli_runner.invoke(app, ["live", "annulment-date", "--help"])
        assert result.exit_code == 0

    def test_requires_args(self, cli_runner: CliRunner):
        """annulment-date requires date_laid and days_in_future."""
        result = cli_runner.invoke(app, ["live", "annulment-date"])
        assert result.exit_code != 0

    def test_success(self, cli_runner: CliRunner):
        """annulment-date with required args returns data."""
        mock_response = json.dumps({"url": "test", "data": json.dumps({})})

        async def mock_get_result(url: str) -> str:
            assert "dateLaid=2024-01-01" in url
            assert "daysInFuture=40" in url
            return mock_response

        with patch("uk_parliament_mcp.cli.live.get_result", new=mock_get_result):
            result = cli_runner.invoke(
                app, ["live", "annulment-date", "2024-01-01", "40"]
            )

        assert result.exit_code == 0


class TestLastSittingDate:
    """Tests for last-sitting-date command."""

    def test_help(self, cli_runner: CliRunner):
        """last-sitting-date --help exits cleanly."""
        result = cli_runner.invoke(app, ["live", "last-sitting-date", "--help"])
        assert result.exit_code == 0

    def test_requires_args(self, cli_runner: CliRunner):
        """last-sitting-date requires house and date_to_check."""
        result = cli_runner.invoke(app, ["live", "last-sitting-date"])
        assert result.exit_code != 0

    def test_success(self, cli_runner: CliRunner):
        """last-sitting-date with required args returns data."""
        mock_response = json.dumps({"url": "test", "data": json.dumps({})})

        async def mock_get_result(url: str) -> str:
            assert "Commons/lastsittingdate.json" in url
            assert "dateToCheck=2024-08-01" in url
            return mock_response

        with patch("uk_parliament_mcp.cli.live.get_result", new=mock_get_result):
            result = cli_runner.invoke(
                app, ["live", "last-sitting-date", "Commons", "2024-08-01"]
            )

        assert result.exit_code == 0


class TestSessionById:
    """Tests for session-by-id command."""

    def test_help(self, cli_runner: CliRunner):
        """session-by-id --help exits cleanly."""
        result = cli_runner.invoke(app, ["live", "session-by-id", "--help"])
        assert result.exit_code == 0

    def test_requires_id(self, cli_runner: CliRunner):
        """session-by-id requires session_id argument."""
        result = cli_runner.invoke(app, ["live", "session-by-id"])
        assert result.exit_code != 0

    def test_success(self, cli_runner: CliRunner):
        """session-by-id returns session data."""
        mock_response = json.dumps({"url": "test", "data": json.dumps({})})

        async def mock_get_result(url: str) -> str:
            assert url == f"{WHATSON_API_BASE}/sessions/byid.json/42"
            return mock_response

        with patch("uk_parliament_mcp.cli.live.get_result", new=mock_get_result):
            result = cli_runner.invoke(app, ["live", "session-by-id", "42"])

        assert result.exit_code == 0


class TestSessionForDate:
    """Tests for session-for-date command."""

    def test_help(self, cli_runner: CliRunner):
        """session-for-date --help exits cleanly."""
        result = cli_runner.invoke(app, ["live", "session-for-date", "--help"])
        assert result.exit_code == 0

    def test_requires_date(self, cli_runner: CliRunner):
        """session-for-date requires date argument."""
        result = cli_runner.invoke(app, ["live", "session-for-date"])
        assert result.exit_code != 0

    def test_success(self, cli_runner: CliRunner):
        """session-for-date returns session data."""
        mock_response = json.dumps({"url": "test", "data": json.dumps({})})

        async def mock_get_result(url: str) -> str:
            assert url == f"{WHATSON_API_BASE}/sessions/fordate.json/2024-06-15"
            return mock_response

        with patch("uk_parliament_mcp.cli.live.get_result", new=mock_get_result):
            result = cli_runner.invoke(app, ["live", "session-for-date", "2024-06-15"])

        assert result.exit_code == 0


class TestCalendarTags:
    """Tests for calendar-tags command."""

    def test_help(self, cli_runner: CliRunner):
        """calendar-tags --help exits cleanly."""
        result = cli_runner.invoke(app, ["live", "calendar-tags", "--help"])
        assert result.exit_code == 0

    def test_success(self, cli_runner: CliRunner):
        """calendar-tags returns data."""
        mock_response = json.dumps({"url": "test", "data": json.dumps([])})

        async def mock_get_result(url: str) -> str:
            assert url == f"{WHATSON_API_BASE}/tags/list.json"
            return mock_response

        with patch("uk_parliament_mcp.cli.live.get_result", new=mock_get_result):
            result = cli_runner.invoke(app, ["live", "calendar-tags"])

        assert result.exit_code == 0


class TestCalendarTypesCli:
    """Tests for calendar-types command."""

    def test_help(self, cli_runner: CliRunner):
        """calendar-types --help exits cleanly."""
        result = cli_runner.invoke(app, ["live", "calendar-types", "--help"])
        assert result.exit_code == 0

    def test_success(self, cli_runner: CliRunner):
        """calendar-types returns data."""
        mock_response = json.dumps({"url": "test", "data": json.dumps([])})

        async def mock_get_result(url: str) -> str:
            assert url == f"{WHATSON_API_BASE}/types/list.json"
            return mock_response

        with patch("uk_parliament_mcp.cli.live.get_result", new=mock_get_result):
            result = cli_runner.invoke(app, ["live", "calendar-types"])

        assert result.exit_code == 0
