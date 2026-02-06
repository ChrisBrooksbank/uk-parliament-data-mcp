"""Tests for CLI my-mp command."""
from __future__ import annotations

import json
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from uk_parliament_mcp.cli.main import app


class TestMyMp:
    """Tests for my-mp command."""

    @pytest.fixture
    def mock_member_response(self) -> str:
        """Mock member search by postcode response."""
        return json.dumps({
            "url": "https://members-api.parliament.uk/api/Members/Search?Location=SW1A+1AA&IsCurrentMember=true&House=1",
            "data": json.dumps({
                "items": [
                    {
                        "value": {
                            "id": 172,
                            "nameDisplayAs": "Nickie Aiken",
                            "latestParty": {"name": "Conservative"},
                            "latestHouseMembership": {
                                "house": 1,
                                "membershipFrom": "Cities of London and Westminster",
                            },
                        }
                    }
                ],
                "totalResults": 1,
            })
        })

    @pytest.fixture
    def mock_biography_response(self) -> str:
        """Mock biography response."""
        return json.dumps({
            "url": "https://members-api.parliament.uk/api/Members/172/Biography",
            "data": json.dumps({
                "value": {
                    "biographyEntries": [
                        {"category": "Political", "entry": "MP for Cities of London and Westminster"}
                    ]
                }
            })
        })

    @pytest.fixture
    def mock_interests_response(self) -> str:
        """Mock interests response."""
        return json.dumps({
            "url": "https://interests-api.parliament.uk/api/Interests/?MemberId=172",
            "data": json.dumps({"items": []})
        })

    @pytest.fixture
    def mock_election_response(self) -> str:
        """Mock latest election result response."""
        return json.dumps({
            "url": "https://members-api.parliament.uk/api/Members/172/LatestElectionResult",
            "data": json.dumps({
                "value": {
                    "majority": 3953,
                    "electionDate": "2024-07-04T00:00:00",
                    "electionTitle": "2024 General Election",
                    "candidates": [
                        {
                            "name": "Nickie Aiken",
                            "party": {"name": "Conservative"},
                            "votes": 12345,
                            "voteShare": 0.352,
                        },
                        {
                            "name": "Other Candidate",
                            "party": {"name": "Labour"},
                            "votes": 8392,
                            "voteShare": 0.239,
                        },
                    ],
                }
            })
        })

    @pytest.fixture
    def mock_voting_response(self) -> str:
        """Mock voting response."""
        return json.dumps({
            "url": "https://members-api.parliament.uk/api/Members/172/Voting?house=1&page=1",
            "data": json.dumps({"items": []})
        })

    @pytest.fixture
    def mock_topic_votes_response(self) -> str:
        """Mock topic-specific votes response."""
        return json.dumps({
            "url": "https://commonsvotes-api.parliament.uk/data/divisions.json/search",
            "data": json.dumps([
                {
                    "DivisionId": 999,
                    "Title": "Climate Change Act",
                    "Date": "2024-03-15T00:00:00",
                    "AyeCount": 300,
                    "NoCount": 150,
                }
            ])
        })

    def test_my_mp_help(self, cli_runner: CliRunner):
        """Test that my-mp --help shows command info."""
        result = cli_runner.invoke(app, ["composite", "my-mp", "--help"])
        assert result.exit_code == 0
        assert "postcode" in result.stdout.lower()

    def test_my_mp_requires_postcode(self, cli_runner: CliRunner):
        """Test that my-mp requires a postcode argument."""
        result = cli_runner.invoke(app, ["composite", "my-mp"])
        assert result.exit_code != 0

    def test_my_mp_success(
        self,
        cli_runner: CliRunner,
        mock_member_response: str,
        mock_biography_response: str,
        mock_interests_response: str,
        mock_election_response: str,
        mock_voting_response: str,
    ):
        """Test my-mp returns combined profile data."""
        call_count = [0]

        async def mock_get_result(url: str) -> str:
            responses = [
                mock_member_response,
                mock_biography_response,
                mock_interests_response,
                mock_election_response,
                mock_voting_response,
            ]
            response = responses[call_count[0]]
            call_count[0] += 1
            return response

        with patch("uk_parliament_mcp.cli.composite.get_result", new=mock_get_result):
            result = cli_runner.invoke(app, ["composite", "my-mp", "SW1A 1AA"])

        assert result.exit_code == 0
        output = json.loads(result.stdout)
        assert output["postcode"] == "SW1A 1AA"
        assert output["member_id"] == 172
        assert "basic_info" in output
        assert "biography" in output
        assert "registered_interests" in output
        assert "latest_election" in output
        assert "recent_voting" in output
        assert "sources" in output
        # No topic_votes when --votes not provided
        assert "topic_votes" not in output

    def test_my_mp_no_mp_found(self, cli_runner: CliRunner):
        """Test my-mp when no MP found for postcode."""
        empty_response = json.dumps({
            "url": "https://members-api.parliament.uk/api/Members/Search",
            "data": json.dumps({"items": [], "totalResults": 0})
        })

        async def mock_get_result(url: str) -> str:
            return empty_response

        with patch("uk_parliament_mcp.cli.composite.get_result", new=mock_get_result):
            result = cli_runner.invoke(app, ["composite", "my-mp", "ZZ99 9ZZ"])

        assert result.exit_code == 0
        output = json.loads(result.stdout)
        assert "error" in output
        assert "No current MP found" in output["error"]

    def test_my_mp_with_votes_topic(
        self,
        cli_runner: CliRunner,
        mock_member_response: str,
        mock_biography_response: str,
        mock_interests_response: str,
        mock_election_response: str,
        mock_voting_response: str,
        mock_topic_votes_response: str,
    ):
        """Test my-mp with --votes topic filter."""
        call_count = [0]

        async def mock_get_result(url: str) -> str:
            responses = [
                mock_member_response,
                mock_biography_response,
                mock_interests_response,
                mock_election_response,
                mock_voting_response,
                mock_topic_votes_response,
            ]
            response = responses[call_count[0]]
            call_count[0] += 1
            return response

        with patch("uk_parliament_mcp.cli.composite.get_result", new=mock_get_result):
            result = cli_runner.invoke(app, ["composite", "my-mp", "SW1A 1AA", "--votes", "climate"])

        assert result.exit_code == 0
        output = json.loads(result.stdout)
        assert output["member_id"] == 172
        assert "topic_votes" in output
        assert output["topic_searched"] == "climate"

    def test_my_mp_pretty_output(
        self,
        cli_runner: CliRunner,
        mock_member_response: str,
        mock_biography_response: str,
        mock_interests_response: str,
        mock_election_response: str,
        mock_voting_response: str,
    ):
        """Test my-mp with --pretty flag formats output."""
        call_count = [0]

        async def mock_get_result(url: str) -> str:
            responses = [
                mock_member_response,
                mock_biography_response,
                mock_interests_response,
                mock_election_response,
                mock_voting_response,
            ]
            response = responses[call_count[0]]
            call_count[0] += 1
            return response

        with patch("uk_parliament_mcp.cli.composite.get_result", new=mock_get_result):
            result = cli_runner.invoke(app, ["composite", "my-mp", "SW1A 1AA", "--pretty"])

        assert result.exit_code == 0
        assert "  " in result.stdout

    def test_my_mp_json_format(
        self,
        cli_runner: CliRunner,
        mock_member_response: str,
        mock_biography_response: str,
        mock_interests_response: str,
        mock_election_response: str,
        mock_voting_response: str,
    ):
        """Test my-mp with --format json outputs valid JSON."""
        call_count = [0]

        async def mock_get_result(url: str) -> str:
            responses = [
                mock_member_response,
                mock_biography_response,
                mock_interests_response,
                mock_election_response,
                mock_voting_response,
            ]
            response = responses[call_count[0]]
            call_count[0] += 1
            return response

        with patch("uk_parliament_mcp.cli.composite.get_result", new=mock_get_result):
            result = cli_runner.invoke(app, ["composite", "my-mp", "SW1A 1AA", "--format", "json"])

        assert result.exit_code == 0
        output = json.loads(result.stdout)
        assert isinstance(output, dict)
        assert output["basic_info"]["nameDisplayAs"] == "Nickie Aiken"
