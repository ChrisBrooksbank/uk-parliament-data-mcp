"""Tests for CLI composite commands."""

from __future__ import annotations

import json
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from uk_parliament_mcp.cli.main import app


class TestMpProfile:
    """Tests for mp-profile command."""

    @pytest.fixture
    def mock_member_response(self) -> str:
        """Mock member direct response."""
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

    @pytest.fixture
    def mock_biography_response(self) -> str:
        """Mock biography response."""
        return json.dumps(
            {
                "url": "https://members-api.parliament.uk/api/Members/4514/Biography",
                "data": json.dumps(
                    {"value": {"nameDisplayAs": "Keir Starmer", "biographyEntries": []}}
                ),
            }
        )

    @pytest.fixture
    def mock_interests_response(self) -> str:
        """Mock interests response."""
        return json.dumps(
            {
                "url": "https://interests-api.parliament.uk/api/Interests/?MemberId=4514",
                "data": json.dumps({"items": []}),
            }
        )

    @pytest.fixture
    def mock_voting_response(self) -> str:
        """Mock voting response."""
        return json.dumps(
            {
                "url": "https://members-api.parliament.uk/api/Members/4514/Voting?house=1&page=1",
                "data": json.dumps({"items": []}),
            }
        )

    def test_mp_profile_help(self, cli_runner: CliRunner):
        """Test that mp-profile --help shows command info."""
        result = cli_runner.invoke(app, ["composite", "mp-profile", "--help"])
        assert result.exit_code == 0
        assert "mp-profile" in result.stdout.lower()
        assert "comprehensive" in result.stdout.lower()

    def test_mp_profile_requires_member_id(self, cli_runner: CliRunner):
        """Test that mp-profile requires a member_id argument."""
        result = cli_runner.invoke(app, ["composite", "mp-profile"])
        assert result.exit_code != 0

    def test_mp_profile_success(
        self,
        cli_runner: CliRunner,
        mock_member_response: str,
        mock_biography_response: str,
        mock_interests_response: str,
        mock_voting_response: str,
    ):
        """Test mp-profile returns combined data."""
        call_count = [0]

        async def mock_get_result(url: str) -> str:
            """Mock async get_result with call tracking."""
            responses = [
                mock_member_response,
                mock_biography_response,
                mock_interests_response,
                mock_voting_response,
            ]
            response = responses[call_count[0]]
            call_count[0] += 1
            return response

        with patch("uk_parliament_mcp.cli.composite.get_result", new=mock_get_result):
            result = cli_runner.invoke(app, ["composite", "mp-profile", "4514"])

        assert result.exit_code == 0
        output = json.loads(result.stdout)
        assert "member_id" in output
        assert output["member_id"] == 4514
        assert "basic_info" in output
        assert "biography" in output
        assert "registered_interests" in output
        assert "recent_voting" in output
        assert "sources" in output

    def test_mp_profile_pretty_output(
        self,
        cli_runner: CliRunner,
        mock_member_response: str,
        mock_biography_response: str,
        mock_interests_response: str,
        mock_voting_response: str,
    ):
        """Test mp-profile with --pretty flag formats output."""
        call_count = [0]

        async def mock_get_result(url: str) -> str:
            """Mock async get_result with call tracking."""
            responses = [
                mock_member_response,
                mock_biography_response,
                mock_interests_response,
                mock_voting_response,
            ]
            response = responses[call_count[0]]
            call_count[0] += 1
            return response

        with patch("uk_parliament_mcp.cli.composite.get_result", new=mock_get_result):
            result = cli_runner.invoke(app, ["composite", "mp-profile", "4514", "--pretty"])

        assert result.exit_code == 0
        # Pretty output has indentation
        assert "  " in result.stdout


class TestCheckVote:
    """Tests for check-vote command."""

    @pytest.fixture
    def mock_member_response(self) -> str:
        """Mock member direct response."""
        return json.dumps(
            {
                "url": "https://members-api.parliament.uk/api/Members/1234",
                "data": json.dumps(
                    {
                        "value": {
                            "id": 1234,
                            "nameDisplayAs": "Test MP",
                        }
                    }
                ),
            }
        )

    @pytest.fixture
    def mock_divisions_response(self) -> str:
        """Mock divisions response."""
        return json.dumps(
            {
                "url": "https://commonsvotes-api.parliament.uk/data/divisions.json/search",
                "data": json.dumps(
                    {
                        "items": [
                            {
                                "DivisionId": 123,
                                "Title": "Climate Change Act",
                                "AyeCount": 300,
                                "NoCount": 200,
                            }
                        ]
                    }
                ),
            }
        )

    def test_check_vote_help(self, cli_runner: CliRunner):
        """Test that check-vote --help shows command info."""
        result = cli_runner.invoke(app, ["composite", "check-vote", "--help"])
        assert result.exit_code == 0
        assert "check-vote" in result.stdout.lower()
        assert "topic" in result.stdout.lower()

    def test_check_vote_requires_two_args(self, cli_runner: CliRunner):
        """Test that check-vote requires member_id and topic."""
        result = cli_runner.invoke(app, ["composite", "check-vote", "1234"])
        assert result.exit_code != 0

    def test_check_vote_success(
        self,
        cli_runner: CliRunner,
        mock_member_response: str,
        mock_divisions_response: str,
    ):
        """Test check-vote returns combined data."""

        async def mock_get_result(url: str) -> str:
            """Mock async get_result."""
            if "Members/" in url and "divisions" not in url:
                return mock_member_response
            return mock_divisions_response

        with patch("uk_parliament_mcp.cli.composite.get_result", new=mock_get_result):
            result = cli_runner.invoke(app, ["composite", "check-vote", "1234", "climate"])

        assert result.exit_code == 0
        output = json.loads(result.stdout)
        assert "member_id" in output
        assert "member_info" in output
        assert "topic_searched" in output
        assert output["topic_searched"] == "climate"
        assert "divisions" in output
        assert "sources" in output

    def test_check_vote_data_only(
        self,
        cli_runner: CliRunner,
        mock_member_response: str,
        mock_divisions_response: str,
    ):
        """Test check-vote with --data-only flag."""

        async def mock_get_result(url: str) -> str:
            """Mock async get_result."""
            if "Members/" in url and "divisions" not in url:
                return mock_member_response
            return mock_divisions_response

        with patch("uk_parliament_mcp.cli.composite.get_result", new=mock_get_result):
            result = cli_runner.invoke(app, ["composite", "check-vote", "1234", "topic", "-d"])

        assert result.exit_code == 0
        # Should still be valid JSON
        output = json.loads(result.stdout)
        assert isinstance(output, dict)


class TestBillOverview:
    """Tests for bill-overview command."""

    @pytest.fixture
    def mock_bills_search_response(self) -> str:
        """Mock bill search response."""
        return json.dumps(
            {
                "url": "https://bills-api.parliament.uk/api/Bills?SearchTerm=Test",
                "data": json.dumps(
                    {
                        "items": [
                            {
                                "billId": 123,
                                "shortTitle": "Online Safety Bill",
                            }
                        ],
                        "totalResults": 1,
                    }
                ),
            }
        )

    @pytest.fixture
    def mock_bill_details_response(self) -> str:
        """Mock bill details response."""
        return json.dumps(
            {
                "url": "https://bills-api.parliament.uk/api/Bills/123",
                "data": json.dumps({"value": {"billId": 123, "shortTitle": "Online Safety Bill"}}),
            }
        )

    @pytest.fixture
    def mock_bill_stages_response(self) -> str:
        """Mock bill stages response."""
        return json.dumps(
            {
                "url": "https://bills-api.parliament.uk/api/Bills/123/Stages",
                "data": json.dumps({"items": []}),
            }
        )

    @pytest.fixture
    def mock_bill_publications_response(self) -> str:
        """Mock bill publications response."""
        return json.dumps(
            {
                "url": "https://bills-api.parliament.uk/api/Bills/123/Publications",
                "data": json.dumps({"items": []}),
            }
        )

    def test_bill_overview_help(self, cli_runner: CliRunner):
        """Test that bill-overview --help shows command info."""
        result = cli_runner.invoke(app, ["composite", "bill-overview", "--help"])
        assert result.exit_code == 0
        assert "bill-overview" in result.stdout.lower()
        assert "comprehensive" in result.stdout.lower()

    def test_bill_overview_requires_search_term(self, cli_runner: CliRunner):
        """Test that bill-overview requires a search term."""
        result = cli_runner.invoke(app, ["composite", "bill-overview"])
        assert result.exit_code != 0
        # Typer outputs help/error text which may vary
        # Just verify command failed (exit code != 0)

    def test_bill_overview_success(
        self,
        cli_runner: CliRunner,
        mock_bills_search_response: str,
        mock_bill_details_response: str,
        mock_bill_stages_response: str,
        mock_bill_publications_response: str,
    ):
        """Test bill-overview returns combined data."""
        call_count = [0]

        async def mock_get_result(url: str) -> str:
            """Mock async get_result with call tracking."""
            responses = [
                mock_bills_search_response,
                mock_bill_details_response,
                mock_bill_stages_response,
                mock_bill_publications_response,
            ]
            response = responses[call_count[0]]
            call_count[0] += 1
            return response

        with patch("uk_parliament_mcp.cli.composite.get_result", new=mock_get_result):
            result = cli_runner.invoke(app, ["composite", "bill-overview", "Online Safety"])

        assert result.exit_code == 0
        output = json.loads(result.stdout)
        assert "bill_id" in output
        assert output["bill_id"] == 123
        assert "search_summary" in output
        assert "details" in output
        assert "stages" in output
        assert "publications" in output
        assert "sources" in output

    def test_bill_overview_no_bills_found(self, cli_runner: CliRunner):
        """Test bill-overview when no bills found."""
        empty_response = json.dumps(
            {
                "url": "https://bills-api.parliament.uk/api/Bills?SearchTerm=NonExistent",
                "data": json.dumps({"items": [], "totalResults": 0}),
            }
        )

        async def mock_get_result(url: str) -> str:
            """Mock async get_result."""
            return empty_response

        with patch("uk_parliament_mcp.cli.composite.get_result", new=mock_get_result):
            result = cli_runner.invoke(app, ["composite", "bill-overview", "NonExistent"])

        assert result.exit_code == 0
        output = json.loads(result.stdout)
        assert "error" in output
        assert "No bills found" in output["error"]


class TestCommitteeSummary:
    """Tests for committee-summary command."""

    @pytest.fixture
    def mock_committees_search_response(self) -> str:
        """Mock committee search response."""
        return json.dumps(
            {
                "url": "https://committees-api.parliament.uk/api/Committees?SearchTerm=Test",
                "data": json.dumps(
                    {
                        "items": [
                            {
                                "id": 42,
                                "name": "Treasury Committee",
                            }
                        ],
                        "totalResults": 1,
                    }
                ),
            }
        )

    @pytest.fixture
    def mock_committee_details_response(self) -> str:
        """Mock committee details response."""
        return json.dumps(
            {
                "url": "https://committees-api.parliament.uk/api/Committees/42",
                "data": json.dumps({"value": {"id": 42, "name": "Treasury Committee"}}),
            }
        )

    @pytest.fixture
    def mock_oral_evidence_response(self) -> str:
        """Mock oral evidence response."""
        return json.dumps(
            {
                "url": "https://committees-api.parliament.uk/api/OralEvidence",
                "data": json.dumps({"items": []}),
            }
        )

    @pytest.fixture
    def mock_written_evidence_response(self) -> str:
        """Mock written evidence response."""
        return json.dumps(
            {
                "url": "https://committees-api.parliament.uk/api/WrittenEvidence",
                "data": json.dumps({"items": []}),
            }
        )

    @pytest.fixture
    def mock_publications_response(self) -> str:
        """Mock publications response."""
        return json.dumps(
            {
                "url": "https://committees-api.parliament.uk/api/Publications",
                "data": json.dumps({"items": []}),
            }
        )

    def test_committee_summary_help(self, cli_runner: CliRunner):
        """Test that committee-summary --help shows command info."""
        result = cli_runner.invoke(app, ["composite", "committee-summary", "--help"])
        assert result.exit_code == 0
        assert "committee-summary" in result.stdout.lower()
        assert "comprehensive" in result.stdout.lower()

    def test_committee_summary_requires_topic(self, cli_runner: CliRunner):
        """Test that committee-summary requires a topic."""
        result = cli_runner.invoke(app, ["composite", "committee-summary"])
        assert result.exit_code != 0
        # Typer outputs help/error text which may vary
        # Just verify command failed (exit code != 0)

    def test_committee_summary_success(
        self,
        cli_runner: CliRunner,
        mock_committees_search_response: str,
        mock_committee_details_response: str,
        mock_oral_evidence_response: str,
        mock_written_evidence_response: str,
        mock_publications_response: str,
    ):
        """Test committee-summary returns combined data."""
        call_count = [0]

        async def mock_get_result(url: str) -> str:
            """Mock async get_result with call tracking."""
            responses = [
                mock_committees_search_response,
                mock_committee_details_response,
                mock_oral_evidence_response,
                mock_written_evidence_response,
                mock_publications_response,
            ]
            response = responses[call_count[0]]
            call_count[0] += 1
            return response

        with patch("uk_parliament_mcp.cli.composite.get_result", new=mock_get_result):
            result = cli_runner.invoke(app, ["composite", "committee-summary", "Treasury"])

        assert result.exit_code == 0
        output = json.loads(result.stdout)
        assert "committee_id" in output
        assert output["committee_id"] == 42
        assert "search_summary" in output
        assert "details" in output
        assert "oral_evidence" in output
        assert "written_evidence" in output
        assert "publications" in output
        assert "sources" in output

    def test_committee_summary_no_committees_found(self, cli_runner: CliRunner):
        """Test committee-summary when no committees found."""
        empty_response = json.dumps(
            {
                "url": "https://committees-api.parliament.uk/api/Committees?SearchTerm=NonExistent",
                "data": json.dumps({"items": [], "totalResults": 0}),
            }
        )

        async def mock_get_result(url: str) -> str:
            """Mock async get_result."""
            return empty_response

        with patch("uk_parliament_mcp.cli.composite.get_result", new=mock_get_result):
            result = cli_runner.invoke(app, ["composite", "committee-summary", "NonExistent"])

        assert result.exit_code == 0
        output = json.loads(result.stdout)
        assert "error" in output
        assert "No committees found" in output["error"]

    def test_committee_summary_pretty_output(
        self,
        cli_runner: CliRunner,
        mock_committees_search_response: str,
        mock_committee_details_response: str,
        mock_oral_evidence_response: str,
        mock_written_evidence_response: str,
        mock_publications_response: str,
    ):
        """Test committee-summary with --pretty flag."""
        call_count = [0]

        async def mock_get_result(url: str) -> str:
            """Mock async get_result with call tracking."""
            responses = [
                mock_committees_search_response,
                mock_committee_details_response,
                mock_oral_evidence_response,
                mock_written_evidence_response,
                mock_publications_response,
            ]
            response = responses[call_count[0]]
            call_count[0] += 1
            return response

        with patch("uk_parliament_mcp.cli.composite.get_result", new=mock_get_result):
            result = cli_runner.invoke(app, ["composite", "committee-summary", "Test", "-p"])

        assert result.exit_code == 0
        # Pretty output has indentation
        assert "  " in result.stdout
