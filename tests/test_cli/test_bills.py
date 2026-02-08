"""Tests for CLI bills commands."""

from __future__ import annotations

import json
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from uk_parliament_mcp.cli.main import app


class TestRecent:
    """Tests for recent command."""

    @pytest.fixture
    def mock_recent_response(self) -> str:
        """Mock recent bills response."""
        return json.dumps(
            {
                "url": "https://bills-api.parliament.uk/api/Bills?SortOrder=DateUpdatedDescending&skip=0&take=10",
                "data": json.dumps(
                    {
                        "items": [
                            {
                                "billId": 123,
                                "shortTitle": "Online Safety Bill",
                                "currentStage": {"name": "Royal Assent"},
                            },
                            {
                                "billId": 124,
                                "shortTitle": "Finance Bill",
                                "currentStage": {"name": "Committee Stage"},
                            },
                        ],
                        "totalResults": 2,
                    }
                ),
            }
        )

    def test_recent_help(self, cli_runner: CliRunner):
        """Test that recent --help shows command info."""
        result = cli_runner.invoke(app, ["bills", "recent", "--help"])
        assert result.exit_code == 0
        assert "recent" in result.stdout.lower()
        assert "bill" in result.stdout.lower()

    def test_recent_success(
        self,
        cli_runner: CliRunner,
        mock_recent_response: str,
    ):
        """Test recent returns bill data."""

        async def mock_get_result(url: str) -> str:
            """Mock async get_result."""
            return mock_recent_response

        with patch("uk_parliament_mcp.cli.pagination.get_result", new=mock_get_result):
            result = cli_runner.invoke(app, ["bills", "recent"])

        assert result.exit_code == 0
        output = json.loads(result.stdout)
        # data_only=True by default, so wrapper is stripped and inner data is returned
        assert "items" in output
        assert output["totalResults"] == 2

    def test_recent_with_take_option(
        self,
        cli_runner: CliRunner,
        mock_recent_response: str,
    ):
        """Test recent with --take option."""

        async def mock_get_result(url: str) -> str:
            """Mock async get_result."""
            return mock_recent_response

        with patch("uk_parliament_mcp.cli.pagination.get_result", new=mock_get_result):
            result = cli_runner.invoke(app, ["bills", "recent", "--take", "5"])

        assert result.exit_code == 0
        output = json.loads(result.stdout)
        # data_only=True by default, so wrapper is stripped and inner data is returned
        assert "items" in output
        assert output["totalResults"] == 2

    def test_recent_pretty_output(
        self,
        cli_runner: CliRunner,
        mock_recent_response: str,
    ):
        """Test recent with --pretty flag formats output."""

        async def mock_get_result(url: str) -> str:
            """Mock async get_result."""
            return mock_recent_response

        with patch("uk_parliament_mcp.cli.utils.get_result", new=mock_get_result):
            result = cli_runner.invoke(app, ["bills", "recent", "-p"])

        assert result.exit_code == 0
        # Pretty output has indentation
        assert "  " in result.stdout


class TestSearch:
    """Tests for search command."""

    @pytest.fixture
    def mock_search_response(self) -> str:
        """Mock bill search response."""
        return json.dumps(
            {
                "url": "https://bills-api.parliament.uk/api/Bills?SearchTerm=Online%20Safety",
                "data": json.dumps(
                    {
                        "items": [
                            {
                                "billId": 123,
                                "shortTitle": "Online Safety Bill",
                                "longTitle": "A Bill to make provision about online safety",
                            }
                        ],
                        "totalResults": 1,
                    }
                ),
            }
        )

    def test_search_help(self, cli_runner: CliRunner):
        """Test that search --help shows command info."""
        result = cli_runner.invoke(app, ["bills", "search", "--help"])
        assert result.exit_code == 0
        assert "search" in result.stdout.lower()

    def test_search_requires_term(self, cli_runner: CliRunner):
        """Test that search requires a search term."""
        result = cli_runner.invoke(app, ["bills", "search"])
        assert result.exit_code != 0

    def test_search_success(
        self,
        cli_runner: CliRunner,
        mock_search_response: str,
    ):
        """Test search returns bill data."""

        async def mock_get_result(url: str) -> str:
            """Mock async get_result."""
            return mock_search_response

        with patch("uk_parliament_mcp.cli.pagination.get_result", new=mock_get_result):
            result = cli_runner.invoke(app, ["bills", "search", "Online Safety"])

        assert result.exit_code == 0
        output = json.loads(result.stdout)
        # data_only=True by default, so wrapper is stripped and inner data is returned
        assert "items" in output
        assert output["totalResults"] == 1

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
            result = cli_runner.invoke(app, ["bills", "search", "Test", "-d"])

        assert result.exit_code == 0
        output = json.loads(result.stdout)
        # Should not have url wrapper
        assert "url" not in output or isinstance(output, str)


class TestGet:
    """Tests for get command."""

    @pytest.fixture
    def mock_bill_response(self) -> str:
        """Mock bill get response."""
        return json.dumps(
            {
                "url": "https://bills-api.parliament.uk/api/Bills/123",
                "data": json.dumps(
                    {
                        "value": {
                            "billId": 123,
                            "shortTitle": "Online Safety Bill",
                            "longTitle": "A Bill to make provision about online safety",
                            "currentStage": {"name": "Royal Assent"},
                        }
                    }
                ),
            }
        )

    def test_get_help(self, cli_runner: CliRunner):
        """Test that get --help shows command info."""
        result = cli_runner.invoke(app, ["bills", "get", "--help"])
        assert result.exit_code == 0
        assert "bill" in result.stdout.lower()
        assert "id" in result.stdout.lower()

    def test_get_requires_id(self, cli_runner: CliRunner):
        """Test that get requires a bill_id argument."""
        result = cli_runner.invoke(app, ["bills", "get"])
        assert result.exit_code != 0

    def test_get_success(
        self,
        cli_runner: CliRunner,
        mock_bill_response: str,
    ):
        """Test get returns bill data."""

        async def mock_get_result(url: str) -> str:
            """Mock async get_result."""
            return mock_bill_response

        with patch("uk_parliament_mcp.cli.utils.get_result", new=mock_get_result):
            result = cli_runner.invoke(app, ["bills", "get", "123"])

        assert result.exit_code == 0
        output = json.loads(result.stdout)
        # data_only=True by default, so wrapper is stripped and inner data is returned
        assert "value" in output
        assert output["value"]["billId"] == 123

    def test_get_pretty_output(
        self,
        cli_runner: CliRunner,
        mock_bill_response: str,
    ):
        """Test get with --pretty flag formats output."""

        async def mock_get_result(url: str) -> str:
            """Mock async get_result."""
            return mock_bill_response

        with patch("uk_parliament_mcp.cli.utils.get_result", new=mock_get_result):
            result = cli_runner.invoke(app, ["bills", "get", "123", "--pretty"])

        assert result.exit_code == 0
        # Pretty output has indentation
        assert "  " in result.stdout


class TestStages:
    """Tests for stages command."""

    @pytest.fixture
    def mock_stages_response(self) -> str:
        """Mock bill stages response."""
        return json.dumps(
            {
                "url": "https://bills-api.parliament.uk/api/Bills/123/Stages",
                "data": json.dumps(
                    {
                        "items": [
                            {
                                "id": 1,
                                "name": "First Reading",
                                "house": "Commons",
                            },
                            {
                                "id": 2,
                                "name": "Second Reading",
                                "house": "Commons",
                            },
                        ],
                        "totalResults": 2,
                    }
                ),
            }
        )

    def test_stages_help(self, cli_runner: CliRunner):
        """Test that stages --help shows command info."""
        result = cli_runner.invoke(app, ["bills", "stages", "--help"])
        assert result.exit_code == 0
        assert "stage" in result.stdout.lower()

    def test_stages_requires_id(self, cli_runner: CliRunner):
        """Test that stages requires a bill_id argument."""
        result = cli_runner.invoke(app, ["bills", "stages"])
        assert result.exit_code != 0

    def test_stages_success(
        self,
        cli_runner: CliRunner,
        mock_stages_response: str,
    ):
        """Test stages returns data."""

        async def mock_get_result(url: str) -> str:
            """Mock async get_result."""
            return mock_stages_response

        with patch("uk_parliament_mcp.cli.pagination.get_result", new=mock_get_result):
            result = cli_runner.invoke(app, ["bills", "stages", "123"])

        assert result.exit_code == 0
        output = json.loads(result.stdout)
        # data_only=True by default, so wrapper is stripped and inner data is returned
        assert "items" in output
        assert output["totalResults"] == 2

    def test_stages_with_pagination(
        self,
        cli_runner: CliRunner,
        mock_stages_response: str,
    ):
        """Test stages with pagination options."""

        async def mock_get_result(url: str) -> str:
            """Mock async get_result."""
            return mock_stages_response

        with patch("uk_parliament_mcp.cli.pagination.get_result", new=mock_get_result):
            result = cli_runner.invoke(
                app, ["bills", "stages", "123", "--skip", "0", "--take", "10"]
            )

        assert result.exit_code == 0
        output = json.loads(result.stdout)
        # data_only=True by default, so wrapper is stripped and inner data is returned
        assert "items" in output
        assert output["totalResults"] == 2


class TestAmendments:
    """Tests for amendments command."""

    @pytest.fixture
    def mock_amendments_response(self) -> str:
        """Mock amendments response."""
        return json.dumps(
            {
                "url": "https://bills-api.parliament.uk/api/Bills/123/Stages/456/Amendments",
                "data": json.dumps(
                    {
                        "items": [
                            {
                                "id": 789,
                                "number": "1",
                                "description": "Amendment to clause 5",
                            }
                        ],
                        "totalResults": 1,
                    }
                ),
            }
        )

    def test_amendments_help(self, cli_runner: CliRunner):
        """Test that amendments --help shows command info."""
        result = cli_runner.invoke(app, ["bills", "amendments", "--help"])
        assert result.exit_code == 0
        assert "amendment" in result.stdout.lower()

    def test_amendments_requires_ids(self, cli_runner: CliRunner):
        """Test that amendments requires bill_id and stage_id arguments."""
        result = cli_runner.invoke(app, ["bills", "amendments"])
        assert result.exit_code != 0

    def test_amendments_success(
        self,
        cli_runner: CliRunner,
        mock_amendments_response: str,
    ):
        """Test amendments returns data."""

        async def mock_get_result(url: str) -> str:
            """Mock async get_result."""
            return mock_amendments_response

        with patch("uk_parliament_mcp.cli.pagination.get_result", new=mock_get_result):
            result = cli_runner.invoke(app, ["bills", "amendments", "123", "456"])

        assert result.exit_code == 0
        output = json.loads(result.stdout)
        # data_only=True by default, so wrapper is stripped and inner data is returned
        assert "items" in output
        assert output["totalResults"] == 1

    def test_amendments_with_search(
        self,
        cli_runner: CliRunner,
        mock_amendments_response: str,
    ):
        """Test amendments with search filter."""

        async def mock_get_result(url: str) -> str:
            """Mock async get_result."""
            return mock_amendments_response

        with patch("uk_parliament_mcp.cli.pagination.get_result", new=mock_get_result):
            result = cli_runner.invoke(
                app, ["bills", "amendments", "123", "456", "--search", "clause"]
            )

        assert result.exit_code == 0
        output = json.loads(result.stdout)
        # data_only=True by default, so wrapper is stripped and inner data is returned
        assert "items" in output
        assert output["totalResults"] == 1

    def test_amendments_with_multiple_filters(
        self,
        cli_runner: CliRunner,
        mock_amendments_response: str,
    ):
        """Test amendments with multiple filters."""

        async def mock_get_result(url: str) -> str:
            """Mock async get_result."""
            return mock_amendments_response

        with patch("uk_parliament_mcp.cli.pagination.get_result", new=mock_get_result):
            result = cli_runner.invoke(
                app,
                ["bills", "amendments", "123", "456", "--search", "clause", "--decision", "Agreed"],
            )

        assert result.exit_code == 0
        output = json.loads(result.stdout)
        # data_only=True by default, so wrapper is stripped and inner data is returned
        assert "items" in output
        assert output["totalResults"] == 1


class TestPublications:
    """Tests for publications command."""

    @pytest.fixture
    def mock_publications_response(self) -> str:
        """Mock publications response."""
        return json.dumps(
            {
                "url": "https://bills-api.parliament.uk/api/Bills/123/Publications",
                "data": json.dumps(
                    {
                        "items": [
                            {
                                "id": 1,
                                "title": "Bill Text",
                                "publicationType": "Bill as introduced",
                            },
                            {
                                "id": 2,
                                "title": "Explanatory Notes",
                                "publicationType": "Explanatory notes",
                            },
                        ],
                        "totalResults": 2,
                    }
                ),
            }
        )

    def test_publications_help(self, cli_runner: CliRunner):
        """Test that publications --help shows command info."""
        result = cli_runner.invoke(app, ["bills", "publications", "--help"])
        assert result.exit_code == 0
        assert "publication" in result.stdout.lower()

    def test_publications_requires_id(self, cli_runner: CliRunner):
        """Test that publications requires a bill_id argument."""
        result = cli_runner.invoke(app, ["bills", "publications"])
        assert result.exit_code != 0

    def test_publications_success(
        self,
        cli_runner: CliRunner,
        mock_publications_response: str,
    ):
        """Test publications returns data."""

        async def mock_get_result(url: str) -> str:
            """Mock async get_result."""
            return mock_publications_response

        with patch("uk_parliament_mcp.cli.utils.get_result", new=mock_get_result):
            result = cli_runner.invoke(app, ["bills", "publications", "123"])

        assert result.exit_code == 0
        output = json.loads(result.stdout)
        # data_only=True by default, so wrapper is stripped and inner data is returned
        assert "items" in output
        assert output["totalResults"] == 2

    def test_publications_data_only(
        self,
        cli_runner: CliRunner,
        mock_publications_response: str,
    ):
        """Test publications with --data-only flag."""

        async def mock_get_result(url: str) -> str:
            """Mock async get_result."""
            return mock_publications_response

        with patch("uk_parliament_mcp.cli.utils.get_result", new=mock_get_result):
            result = cli_runner.invoke(app, ["bills", "publications", "123", "-d"])

        assert result.exit_code == 0
        output = json.loads(result.stdout)
        # Should not have url wrapper
        assert "url" not in output or isinstance(output, str)


class TestTypes:
    """Tests for types command."""

    @pytest.fixture
    def mock_types_response(self) -> str:
        """Mock bill types response."""
        return json.dumps(
            {
                "url": "https://bills-api.parliament.uk/api/BillTypes",
                "data": json.dumps(
                    {
                        "items": [
                            {
                                "id": 1,
                                "name": "Government Bill",
                                "description": "Bills introduced by government ministers",
                            },
                            {
                                "id": 2,
                                "name": "Private Member's Bill",
                                "description": "Bills introduced by backbench MPs",
                            },
                        ],
                        "totalResults": 2,
                    }
                ),
            }
        )

    def test_types_help(self, cli_runner: CliRunner):
        """Test that types --help shows command info."""
        result = cli_runner.invoke(app, ["bills", "types", "--help"])
        assert result.exit_code == 0
        assert "type" in result.stdout.lower()

    def test_types_success(
        self,
        cli_runner: CliRunner,
        mock_types_response: str,
    ):
        """Test types returns data."""

        async def mock_get_result(url: str) -> str:
            """Mock async get_result."""
            return mock_types_response

        with patch("uk_parliament_mcp.cli.utils.get_result", new=mock_get_result):
            result = cli_runner.invoke(app, ["bills", "types"])

        assert result.exit_code == 0
        output = json.loads(result.stdout)
        # data_only=True by default, so wrapper is stripped and inner data is returned
        assert "items" in output
        assert output["totalResults"] == 2

    def test_types_pretty_output(
        self,
        cli_runner: CliRunner,
        mock_types_response: str,
    ):
        """Test types with --pretty flag."""

        async def mock_get_result(url: str) -> str:
            """Mock async get_result."""
            return mock_types_response

        with patch("uk_parliament_mcp.cli.utils.get_result", new=mock_get_result):
            result = cli_runner.invoke(app, ["bills", "types", "-p"])

        assert result.exit_code == 0
        # Pretty output has indentation
        assert "  " in result.stdout


class TestStagesList:
    """Tests for stages-list command."""

    @pytest.fixture
    def mock_stages_list_response(self) -> str:
        """Mock stages list response."""
        return json.dumps(
            {
                "url": "https://bills-api.parliament.uk/api/Stages",
                "data": json.dumps(
                    {
                        "items": [
                            {
                                "id": 1,
                                "name": "First Reading",
                                "description": "Formal introduction of a bill",
                            },
                            {
                                "id": 2,
                                "name": "Second Reading",
                                "description": "General debate on bill principles",
                            },
                        ],
                        "totalResults": 2,
                    }
                ),
            }
        )

    def test_stages_list_help(self, cli_runner: CliRunner):
        """Test that stages-list --help shows command info."""
        result = cli_runner.invoke(app, ["bills", "stages-list", "--help"])
        assert result.exit_code == 0
        assert "stage" in result.stdout.lower()

    def test_stages_list_success(
        self,
        cli_runner: CliRunner,
        mock_stages_list_response: str,
    ):
        """Test stages-list returns data."""

        async def mock_get_result(url: str) -> str:
            """Mock async get_result."""
            return mock_stages_list_response

        with patch("uk_parliament_mcp.cli.utils.get_result", new=mock_get_result):
            result = cli_runner.invoke(app, ["bills", "stages-list"])

        assert result.exit_code == 0
        output = json.loads(result.stdout)
        # data_only=True by default, so wrapper is stripped and inner data is returned
        assert "items" in output
        assert output["totalResults"] == 2


class TestRSS:
    """Tests for RSS commands."""

    @pytest.fixture
    def mock_rss_response(self) -> str:
        """Mock RSS response."""
        return json.dumps(
            {
                "url": "https://bills-api.parliament.uk/api/Rss/allbills.rss",
                "data": json.dumps("<rss>...</rss>"),
            }
        )

    def test_rss_all_help(self, cli_runner: CliRunner):
        """Test that rss-all --help shows command info."""
        result = cli_runner.invoke(app, ["bills", "rss-all", "--help"])
        assert result.exit_code == 0
        assert "rss" in result.stdout.lower()

    def test_rss_all_success(
        self,
        cli_runner: CliRunner,
        mock_rss_response: str,
    ):
        """Test rss-all returns data."""

        async def mock_get_result(url: str) -> str:
            """Mock async get_result."""
            return mock_rss_response

        with patch("uk_parliament_mcp.cli.utils.get_result", new=mock_get_result):
            result = cli_runner.invoke(app, ["bills", "rss-all"])

        assert result.exit_code == 0
        # data_only=True by default, so wrapper is stripped and inner RSS data is returned
        output = json.loads(result.stdout)
        assert "rss" in output

    def test_rss_public_success(
        self,
        cli_runner: CliRunner,
        mock_rss_response: str,
    ):
        """Test rss-public returns data."""

        async def mock_get_result(url: str) -> str:
            """Mock async get_result."""
            return mock_rss_response

        with patch("uk_parliament_mcp.cli.utils.get_result", new=mock_get_result):
            result = cli_runner.invoke(app, ["bills", "rss-public"])

        assert result.exit_code == 0
        # data_only=True by default, so wrapper is stripped and inner RSS data is returned
        output = json.loads(result.stdout)
        assert "rss" in output

    def test_rss_private_success(
        self,
        cli_runner: CliRunner,
        mock_rss_response: str,
    ):
        """Test rss-private returns data."""

        async def mock_get_result(url: str) -> str:
            """Mock async get_result."""
            return mock_rss_response

        with patch("uk_parliament_mcp.cli.utils.get_result", new=mock_get_result):
            result = cli_runner.invoke(app, ["bills", "rss-private"])

        assert result.exit_code == 0
        # data_only=True by default, so wrapper is stripped and inner RSS data is returned
        output = json.loads(result.stdout)
        assert "rss" in output

    def test_rss_bill_requires_id(self, cli_runner: CliRunner):
        """Test that rss-bill requires a bill_id argument."""
        result = cli_runner.invoke(app, ["bills", "rss-bill"])
        assert result.exit_code != 0

    def test_rss_bill_success(
        self,
        cli_runner: CliRunner,
        mock_rss_response: str,
    ):
        """Test rss-bill returns data."""

        async def mock_get_result(url: str) -> str:
            """Mock async get_result."""
            return mock_rss_response

        with patch("uk_parliament_mcp.cli.utils.get_result", new=mock_get_result):
            result = cli_runner.invoke(app, ["bills", "rss-bill", "123"])

        assert result.exit_code == 0
        # data_only=True by default, so wrapper is stripped and inner RSS data is returned
        output = json.loads(result.stdout)
        assert "rss" in output


class TestSittings:
    """Tests for sittings command."""

    @pytest.fixture
    def mock_sittings_response(self) -> str:
        """Mock sittings response."""
        return json.dumps(
            {
                "url": "https://bills-api.parliament.uk/api/Sittings",
                "data": json.dumps(
                    {
                        "items": [
                            {
                                "id": 1,
                                "date": "2024-01-15",
                                "house": "Commons",
                            },
                            {
                                "id": 2,
                                "date": "2024-01-16",
                                "house": "Lords",
                            },
                        ],
                        "totalResults": 2,
                    }
                ),
            }
        )

    def test_sittings_help(self, cli_runner: CliRunner):
        """Test that sittings --help shows command info."""
        result = cli_runner.invoke(app, ["bills", "sittings", "--help"])
        assert result.exit_code == 0
        assert "sitting" in result.stdout.lower()

    def test_sittings_success(
        self,
        cli_runner: CliRunner,
        mock_sittings_response: str,
    ):
        """Test sittings returns data."""

        async def mock_get_result(url: str) -> str:
            """Mock async get_result."""
            return mock_sittings_response

        with patch("uk_parliament_mcp.cli.pagination.get_result", new=mock_get_result):
            result = cli_runner.invoke(app, ["bills", "sittings"])

        assert result.exit_code == 0
        output = json.loads(result.stdout)
        # data_only=True by default, so wrapper is stripped and inner data is returned
        assert "items" in output
        assert output["totalResults"] == 2

    def test_sittings_with_filters(
        self,
        cli_runner: CliRunner,
        mock_sittings_response: str,
    ):
        """Test sittings with house and date filters."""

        async def mock_get_result(url: str) -> str:
            """Mock async get_result."""
            return mock_sittings_response

        with patch("uk_parliament_mcp.cli.pagination.get_result", new=mock_get_result):
            result = cli_runner.invoke(
                app,
                [
                    "bills",
                    "sittings",
                    "--house",
                    "Commons",
                    "--from",
                    "2024-01-01",
                    "--to",
                    "2024-12-31",
                ],
            )

        assert result.exit_code == 0
        output = json.loads(result.stdout)
        # data_only=True by default, so wrapper is stripped and inner data is returned
        assert "items" in output
        assert output["totalResults"] == 2

    def test_sittings_pretty_output(
        self,
        cli_runner: CliRunner,
        mock_sittings_response: str,
    ):
        """Test sittings with --pretty flag."""

        async def mock_get_result(url: str) -> str:
            """Mock async get_result."""
            return mock_sittings_response

        with patch("uk_parliament_mcp.cli.utils.get_result", new=mock_get_result):
            result = cli_runner.invoke(app, ["bills", "sittings", "-p"])

        assert result.exit_code == 0
        # Pretty output has indentation
        assert "  " in result.stdout
