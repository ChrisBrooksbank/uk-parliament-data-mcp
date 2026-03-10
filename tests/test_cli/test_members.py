"""Tests for CLI members commands."""

from __future__ import annotations

import json
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from uk_parliament_mcp.cli.main import app


class TestSearchMember:
    """Tests for search command."""

    @pytest.fixture
    def mock_search_response(self) -> str:
        """Mock member search response."""
        return json.dumps(
            {
                "url": "https://members-api.parliament.uk/api/Members/Search?Name=Starmer",
                "data": json.dumps(
                    {
                        "items": [
                            {
                                "value": {
                                    "id": 4514,
                                    "nameDisplayAs": "Keir Starmer",
                                    "latestHouseMembership": {
                                        "house": 1,
                                        "membershipFrom": "Holborn and St Pancras",
                                    },
                                }
                            }
                        ],
                        "totalResults": 1,
                    }
                ),
            }
        )

    def test_search_help(self, cli_runner: CliRunner):
        """Test that search --help shows command info."""
        result = cli_runner.invoke(app, ["members", "search", "--help"])
        assert result.exit_code == 0
        assert "search" in result.stdout.lower()
        assert "name" in result.stdout.lower()

    def test_search_requires_name(self, cli_runner: CliRunner):
        """Test that search requires a name argument."""
        result = cli_runner.invoke(app, ["members", "search"])
        assert result.exit_code != 0

    def test_search_success(
        self,
        cli_runner: CliRunner,
        mock_search_response: str,
    ):
        """Test search returns member data."""

        async def mock_get_result(url: str) -> str:
            """Mock async get_result."""
            return mock_search_response

        with patch("uk_parliament_mcp.cli.pagination.get_result", new=mock_get_result):
            result = cli_runner.invoke(app, ["members", "search", "Starmer"])

        assert result.exit_code == 0
        output = json.loads(result.stdout)
        # data_only=True by default, so wrapper is stripped and inner data is returned
        assert "items" in output
        assert output["totalResults"] == 1

    def test_search_pretty_output(
        self,
        cli_runner: CliRunner,
        mock_search_response: str,
    ):
        """Test search with --pretty flag formats output."""

        async def mock_get_result(url: str) -> str:
            """Mock async get_result."""
            return mock_search_response

        with patch("uk_parliament_mcp.cli.pagination.get_result", new=mock_get_result):
            result = cli_runner.invoke(app, ["members", "search", "Test", "--pretty"])

        assert result.exit_code == 0
        # Pretty output has indentation
        assert "  " in result.stdout

    def test_search_data_only(
        self,
        cli_runner: CliRunner,
        mock_search_response: str,
    ):
        """Test search with --data-only flag strips wrapper."""

        async def mock_get_result(url: str) -> str:
            """Mock async get_result."""
            return mock_search_response

        with patch("uk_parliament_mcp.cli.pagination.get_result", new=mock_get_result):
            result = cli_runner.invoke(app, ["members", "search", "Test", "-d"])

        assert result.exit_code == 0
        output = json.loads(result.stdout)
        # Should not have url wrapper
        assert "url" not in output or isinstance(output, str)

    def test_search_with_filters(
        self,
        cli_runner: CliRunner,
        mock_search_response: str,
    ):
        """Test search with advanced filter flags."""

        async def mock_get_result(url: str) -> str:
            """Mock async get_result."""
            return mock_search_response

        with patch("uk_parliament_mcp.cli.pagination.get_result", new=mock_get_result):
            result = cli_runner.invoke(
                app,
                ["members", "search", "Test", "--house", "1", "--is-current-member"],
            )

        assert result.exit_code == 0
        output = json.loads(result.stdout)
        assert "items" in output


class TestGetMember:
    """Tests for get command."""

    @pytest.fixture
    def mock_member_response(self) -> str:
        """Mock member get response."""
        return json.dumps(
            {
                "url": "https://members-api.parliament.uk/api/Members/4514",
                "data": json.dumps(
                    {
                        "value": {
                            "id": 4514,
                            "nameDisplayAs": "Keir Starmer",
                            "latestHouseMembership": {
                                "house": 1,
                                "membershipFrom": "Holborn and St Pancras",
                            },
                        }
                    }
                ),
            }
        )

    def test_get_help(self, cli_runner: CliRunner):
        """Test that get --help shows command info."""
        result = cli_runner.invoke(app, ["members", "get", "--help"])
        assert result.exit_code == 0
        assert "member" in result.stdout.lower()
        assert "id" in result.stdout.lower()

    def test_get_requires_id(self, cli_runner: CliRunner):
        """Test that get requires a member_id argument."""
        result = cli_runner.invoke(app, ["members", "get"])
        assert result.exit_code != 0

    def test_get_success(
        self,
        cli_runner: CliRunner,
        mock_member_response: str,
    ):
        """Test get returns member data."""

        async def mock_get_result(url: str) -> str:
            """Mock async get_result."""
            return mock_member_response

        with patch("uk_parliament_mcp.cli.utils.get_result", new=mock_get_result):
            result = cli_runner.invoke(app, ["members", "get", "4514"])

        assert result.exit_code == 0
        output = json.loads(result.stdout)
        # data_only=True by default, so wrapper is stripped and inner data is returned
        assert "value" in output
        assert output["value"]["id"] == 4514

    def test_get_pretty_output(
        self,
        cli_runner: CliRunner,
        mock_member_response: str,
    ):
        """Test get with --pretty flag formats output."""

        async def mock_get_result(url: str) -> str:
            """Mock async get_result."""
            return mock_member_response

        with patch("uk_parliament_mcp.cli.utils.get_result", new=mock_get_result):
            result = cli_runner.invoke(app, ["members", "get", "4514", "-p"])

        assert result.exit_code == 0
        # Pretty output has indentation
        assert "  " in result.stdout


class TestGetBiography:
    """Tests for biography command."""

    @pytest.fixture
    def mock_biography_response(self) -> str:
        """Mock biography response."""
        return json.dumps(
            {
                "url": "https://members-api.parliament.uk/api/Members/4514/Biography",
                "data": json.dumps(
                    {
                        "value": {
                            "nameDisplayAs": "Keir Starmer",
                            "biographyEntries": [
                                {"category": "Education", "entry": "University of Leeds"}
                            ],
                        }
                    }
                ),
            }
        )

    def test_biography_help(self, cli_runner: CliRunner):
        """Test that biography --help shows command info."""
        result = cli_runner.invoke(app, ["members", "biography", "--help"])
        assert result.exit_code == 0
        assert "biography" in result.stdout.lower()

    def test_biography_requires_id(self, cli_runner: CliRunner):
        """Test that biography requires a member_id argument."""
        result = cli_runner.invoke(app, ["members", "biography"])
        assert result.exit_code != 0

    def test_biography_success(
        self,
        cli_runner: CliRunner,
        mock_biography_response: str,
    ):
        """Test biography returns data."""

        async def mock_get_result(url: str) -> str:
            """Mock async get_result."""
            return mock_biography_response

        with patch("uk_parliament_mcp.cli.utils.get_result", new=mock_get_result):
            result = cli_runner.invoke(app, ["members", "biography", "4514"])

        assert result.exit_code == 0
        output = json.loads(result.stdout)
        # data_only=True by default, so wrapper is stripped and inner data is returned
        assert "value" in output
        assert output["value"]["nameDisplayAs"] == "Keir Starmer"


class TestGetContact:
    """Tests for contact command."""

    @pytest.fixture
    def mock_contact_response(self) -> str:
        """Mock contact response."""
        return json.dumps(
            {
                "url": "https://members-api.parliament.uk/api/Members/4514/Contact",
                "data": json.dumps(
                    {"value": {"id": 4514, "email": "test@parliament.uk", "phone": "020 7219 0000"}}
                ),
            }
        )

    def test_contact_help(self, cli_runner: CliRunner):
        """Test that contact --help shows command info."""
        result = cli_runner.invoke(app, ["members", "contact", "--help"])
        assert result.exit_code == 0
        assert "contact" in result.stdout.lower()

    def test_contact_requires_id(self, cli_runner: CliRunner):
        """Test that contact requires a member_id argument."""
        result = cli_runner.invoke(app, ["members", "contact"])
        assert result.exit_code != 0

    def test_contact_success(
        self,
        cli_runner: CliRunner,
        mock_contact_response: str,
    ):
        """Test contact returns data."""

        async def mock_get_result(url: str) -> str:
            """Mock async get_result."""
            return mock_contact_response

        with patch("uk_parliament_mcp.cli.utils.get_result", new=mock_get_result):
            result = cli_runner.invoke(app, ["members", "contact", "4514"])

        assert result.exit_code == 0
        output = json.loads(result.stdout)
        # data_only=True by default, so wrapper is stripped and inner data is returned
        assert "value" in output
        assert output["value"]["id"] == 4514


class TestParties:
    """Tests for parties command."""

    @pytest.fixture
    def mock_parties_response(self) -> str:
        """Mock parties response."""
        return json.dumps(
            {
                "url": "https://members-api.parliament.uk/api/Parties/GetActive/1",
                "data": json.dumps(
                    {
                        "items": [
                            {
                                "value": {
                                    "id": 15,
                                    "name": "Labour",
                                }
                            },
                            {
                                "value": {
                                    "id": 4,
                                    "name": "Conservative",
                                }
                            },
                        ],
                        "totalResults": 2,
                    }
                ),
            }
        )

    def test_parties_help(self, cli_runner: CliRunner):
        """Test that parties --help shows command info."""
        result = cli_runner.invoke(app, ["members", "parties", "--help"])
        assert result.exit_code == 0
        assert "parties" in result.stdout.lower()

    def test_parties_requires_house(self, cli_runner: CliRunner):
        """Test that parties requires a house argument."""
        result = cli_runner.invoke(app, ["members", "parties"])
        assert result.exit_code != 0

    def test_parties_commons_success(
        self,
        cli_runner: CliRunner,
        mock_parties_response: str,
    ):
        """Test parties returns data for Commons."""

        async def mock_get_result(url: str) -> str:
            """Mock async get_result."""
            return mock_parties_response

        with patch("uk_parliament_mcp.cli.utils.get_result", new=mock_get_result):
            result = cli_runner.invoke(app, ["members", "parties", "1"])

        assert result.exit_code == 0
        output = json.loads(result.stdout)
        # data_only=True by default, so wrapper is stripped and inner data is returned
        assert "items" in output
        assert output["totalResults"] == 2

    def test_parties_lords_success(
        self,
        cli_runner: CliRunner,
        mock_parties_response: str,
    ):
        """Test parties returns data for Lords."""

        async def mock_get_result(url: str) -> str:
            """Mock async get_result."""
            return mock_parties_response

        with patch("uk_parliament_mcp.cli.utils.get_result", new=mock_get_result):
            result = cli_runner.invoke(app, ["members", "parties", "2"])

        assert result.exit_code == 0
        output = json.loads(result.stdout)
        # data_only=True by default, so wrapper is stripped and inner data is returned
        assert "items" in output
        assert output["totalResults"] == 2


class TestConstituencies:
    """Tests for constituencies command."""

    @pytest.fixture
    def mock_constituencies_response(self) -> str:
        """Mock constituencies response."""
        return json.dumps(
            {
                "url": "https://members-api.parliament.uk/api/Location/Constituency/Search",
                "data": json.dumps(
                    {
                        "items": [
                            {
                                "value": {
                                    "id": 123,
                                    "name": "Holborn and St Pancras",
                                }
                            },
                            {
                                "value": {
                                    "id": 124,
                                    "name": "Westminster",
                                }
                            },
                        ],
                        "totalResults": 2,
                    }
                ),
            }
        )

    def test_constituencies_help(self, cli_runner: CliRunner):
        """Test that constituencies --help shows command info."""
        result = cli_runner.invoke(app, ["members", "constituencies", "--help"])
        assert result.exit_code == 0
        assert "constituenc" in result.stdout.lower()

    def test_constituencies_success(
        self,
        cli_runner: CliRunner,
        mock_constituencies_response: str,
    ):
        """Test constituencies returns data."""

        async def mock_get_result(url: str) -> str:
            """Mock async get_result."""
            return mock_constituencies_response

        with patch("uk_parliament_mcp.cli.pagination.get_result", new=mock_get_result):
            result = cli_runner.invoke(app, ["members", "constituencies"])

        assert result.exit_code == 0
        output = json.loads(result.stdout)
        # data_only=True by default, so wrapper is stripped and inner data is returned
        assert "items" in output
        assert output["totalResults"] == 2

    def test_constituencies_with_pagination(
        self,
        cli_runner: CliRunner,
        mock_constituencies_response: str,
    ):
        """Test constituencies with pagination options."""

        async def mock_get_result(url: str) -> str:
            """Mock async get_result."""
            return mock_constituencies_response

        with patch("uk_parliament_mcp.cli.pagination.get_result", new=mock_get_result):
            result = cli_runner.invoke(
                app, ["members", "constituencies", "--skip", "0", "--take", "20"]
            )

        assert result.exit_code == 0
        output = json.loads(result.stdout)
        # data_only=True by default, so wrapper is stripped and inner data is returned
        assert "items" in output


class TestGetConstituency:
    """Tests for constituency-get command."""

    @pytest.fixture
    def mock_constituency_response(self) -> str:
        """Mock constituency response."""
        return json.dumps(
            {
                "url": "https://members-api.parliament.uk/api/Location/Constituency/3510",
                "data": json.dumps({"value": {"id": 3510, "name": "Holborn and St Pancras"}}),
            }
        )

    def test_constituency_get_help(self, cli_runner: CliRunner):
        """Test that constituency-get --help shows command info."""
        result = cli_runner.invoke(app, ["members", "constituency-get", "--help"])
        assert result.exit_code == 0

    def test_constituency_get_requires_id(self, cli_runner: CliRunner):
        """Test that constituency-get requires an ID argument."""
        result = cli_runner.invoke(app, ["members", "constituency-get"])
        assert result.exit_code != 0

    def test_constituency_get_success(
        self, cli_runner: CliRunner, mock_constituency_response: str
    ):
        """Test constituency-get returns constituency data."""

        async def mock_get_result(url: str) -> str:
            return mock_constituency_response

        with patch("uk_parliament_mcp.cli.utils.get_result", new=mock_get_result):
            result = cli_runner.invoke(app, ["members", "constituency-get", "3510"])

        assert result.exit_code == 0
        output = json.loads(result.stdout)
        assert "value" in output
        assert output["value"]["id"] == 3510


class TestGetConstituencyLatestElection:
    """Tests for constituency-latest-election command."""

    def test_help(self, cli_runner: CliRunner):
        """Test that constituency-latest-election --help shows command info."""
        result = cli_runner.invoke(app, ["members", "constituency-latest-election", "--help"])
        assert result.exit_code == 0

    def test_requires_id(self, cli_runner: CliRunner):
        """Test that constituency-latest-election requires an ID argument."""
        result = cli_runner.invoke(app, ["members", "constituency-latest-election"])
        assert result.exit_code != 0


class TestGetConstituencyElectionResult:
    """Tests for constituency-election command."""

    def test_help(self, cli_runner: CliRunner):
        """Test that constituency-election --help shows command info."""
        result = cli_runner.invoke(app, ["members", "constituency-election", "--help"])
        assert result.exit_code == 0

    def test_requires_args(self, cli_runner: CliRunner):
        """Test that constituency-election requires both IDs."""
        result = cli_runner.invoke(app, ["members", "constituency-election"])
        assert result.exit_code != 0


class TestGetConstituencyRepresentations:
    """Tests for constituency-representations command."""

    def test_help(self, cli_runner: CliRunner):
        """Test that constituency-representations --help shows command info."""
        result = cli_runner.invoke(app, ["members", "constituency-representations", "--help"])
        assert result.exit_code == 0

    def test_requires_id(self, cli_runner: CliRunner):
        """Test that constituency-representations requires an ID argument."""
        result = cli_runner.invoke(app, ["members", "constituency-representations"])
        assert result.exit_code != 0


class TestGetConstituencySynopsis:
    """Tests for constituency-synopsis command."""

    def test_help(self, cli_runner: CliRunner):
        """Test that constituency-synopsis --help shows command info."""
        result = cli_runner.invoke(app, ["members", "constituency-synopsis", "--help"])
        assert result.exit_code == 0

    def test_requires_id(self, cli_runner: CliRunner):
        """Test that constituency-synopsis requires an ID argument."""
        result = cli_runner.invoke(app, ["members", "constituency-synopsis"])
        assert result.exit_code != 0


class TestSearchHistoricalMembers:
    """Tests for search-historical command."""

    @pytest.fixture
    def mock_historical_response(self) -> str:
        """Mock historical members response."""
        return json.dumps(
            {
                "url": "https://members-api.parliament.uk/api/Members/SearchHistorical",
                "data": json.dumps({"items": [], "totalResults": 0}),
            }
        )

    def test_help(self, cli_runner: CliRunner):
        """Test that search-historical --help shows command info."""
        result = cli_runner.invoke(app, ["members", "search-historical", "--help"])
        assert result.exit_code == 0

    def test_search_historical_success(
        self, cli_runner: CliRunner, mock_historical_response: str
    ):
        """Test search-historical returns data."""

        async def mock_get_result(url: str) -> str:
            return mock_historical_response

        with patch("uk_parliament_mcp.cli.utils.get_result", new=mock_get_result):
            result = cli_runner.invoke(
                app, ["members", "search-historical", "--name", "Churchill"]
            )

        assert result.exit_code == 0


class TestGetSpeakerAndDeputies:
    """Tests for speaker-and-deputies command."""

    def test_help(self, cli_runner: CliRunner):
        """Test that speaker-and-deputies --help shows command info."""
        result = cli_runner.invoke(app, ["members", "speaker-and-deputies", "--help"])
        assert result.exit_code == 0

    def test_requires_date(self, cli_runner: CliRunner):
        """Test that speaker-and-deputies requires a date argument."""
        result = cli_runner.invoke(app, ["members", "speaker-and-deputies"])
        assert result.exit_code != 0


class TestBrowseLocations:
    """Tests for browse-locations command."""

    def test_help(self, cli_runner: CliRunner):
        """Test that browse-locations --help shows command info."""
        result = cli_runner.invoke(app, ["members", "browse-locations", "--help"])
        assert result.exit_code == 0

    def test_requires_args(self, cli_runner: CliRunner):
        """Test that browse-locations requires both arguments."""
        result = cli_runner.invoke(app, ["members", "browse-locations"])
        assert result.exit_code != 0


class TestLordsInterestsRegister:
    """Tests for lords-interests-register command."""

    @pytest.fixture
    def mock_register_response(self) -> str:
        """Mock lords interests register response."""
        return json.dumps(
            {
                "url": "https://members-api.parliament.uk/api/LordsInterests/Register",
                "data": json.dumps({"items": [], "totalResults": 0}),
            }
        )

    def test_help(self, cli_runner: CliRunner):
        """Test that lords-interests-register --help shows command info."""
        result = cli_runner.invoke(app, ["members", "lords-interests-register", "--help"])
        assert result.exit_code == 0

    def test_success_no_args(
        self, cli_runner: CliRunner, mock_register_response: str
    ):
        """Test lords-interests-register works without arguments."""

        async def mock_get_result(url: str) -> str:
            return mock_register_response

        with patch("uk_parliament_mcp.cli.utils.get_result", new=mock_get_result):
            result = cli_runner.invoke(app, ["members", "lords-interests-register"])

        assert result.exit_code == 0
