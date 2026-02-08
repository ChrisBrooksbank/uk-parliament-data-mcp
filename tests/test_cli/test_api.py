"""Tests for CLI api commands (API spec explorer)."""

from __future__ import annotations

import json

import pytest
from typer.testing import CliRunner

from uk_parliament_mcp.cli.main import app


class TestApiList:
    """Tests for `parliament api list`."""

    def test_list_returns_14_apis(self, cli_runner: CliRunner):
        result = cli_runner.invoke(app, ["api", "list"])
        assert result.exit_code == 0
        apis = json.loads(result.stdout)
        assert len(apis) == 14

    def test_list_has_expected_fields(self, cli_runner: CliRunner):
        result = cli_runner.invoke(app, ["api", "list"])
        apis = json.loads(result.stdout)
        for api in apis:
            assert "name" in api
            assert "title" in api
            assert "description" in api
            assert "baseUrl" in api
            assert "endpointCount" in api
            assert "schemaCount" in api

    def test_list_pretty(self, cli_runner: CliRunner):
        result = cli_runner.invoke(app, ["api", "list", "--pretty"])
        assert result.exit_code == 0
        # Pretty output has newlines/indentation
        assert "\n" in result.stdout
        apis = json.loads(result.stdout)
        assert len(apis) == 14

    def test_list_contains_known_apis(self, cli_runner: CliRunner):
        result = cli_runner.invoke(app, ["api", "list"])
        apis = json.loads(result.stdout)
        names = [a["name"] for a in apis]
        assert "members" in names
        assert "bills" in names
        assert "hansard" in names
        assert "committees" in names


class TestApiEndpoints:
    """Tests for `parliament api endpoints`."""

    def test_endpoints_members(self, cli_runner: CliRunner):
        result = cli_runner.invoke(app, ["api", "endpoints", "members"])
        assert result.exit_code == 0
        eps = json.loads(result.stdout)
        assert len(eps) > 0
        assert all("method" in e and "path" in e for e in eps)

    def test_endpoints_with_tag_filter(self, cli_runner: CliRunner):
        result = cli_runner.invoke(app, ["api", "endpoints", "bills", "--tag", "Amendments"])
        assert result.exit_code == 0
        eps = json.loads(result.stdout)
        assert len(eps) > 0
        for ep in eps:
            assert "Amendments" in ep.get("tags", [])

    def test_endpoints_unknown_api(self, cli_runner: CliRunner):
        result = cli_runner.invoke(app, ["api", "endpoints", "nonexistent"])
        assert result.exit_code == 1

    def test_endpoints_tag_no_results(self, cli_runner: CliRunner):
        result = cli_runner.invoke(app, ["api", "endpoints", "members", "--tag", "zzz_nonexistent"])
        assert result.exit_code == 0
        eps = json.loads(result.stdout)
        assert eps == []


class TestApiDetail:
    """Tests for `parliament api detail`."""

    def test_detail_exact_path(self, cli_runner: CliRunner):
        result = cli_runner.invoke(
            app, ["api", "detail", "members", "/api/Members/Search", "--pretty"]
        )
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        # Could be a single object or array of matches
        if isinstance(data, list):
            assert len(data) > 0
            assert data[0]["method"] == "GET"
        else:
            assert data["method"] == "GET"

    def test_detail_partial_path(self, cli_runner: CliRunner):
        result = cli_runner.invoke(app, ["api", "detail", "bills", "Bills/{billId}"])
        assert result.exit_code == 0

    def test_detail_not_found(self, cli_runner: CliRunner):
        result = cli_runner.invoke(app, ["api", "detail", "members", "/nonexistent/path"])
        assert result.exit_code == 1

    def test_detail_with_method(self, cli_runner: CliRunner):
        result = cli_runner.invoke(
            app, ["api", "detail", "members", "Members/Search", "--method", "POST"]
        )
        assert result.exit_code == 1  # No POST endpoints for Members/Search

    def test_detail_includes_parameters(self, cli_runner: CliRunner):
        result = cli_runner.invoke(app, ["api", "detail", "members", "/api/Members/Search"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        if isinstance(data, list):
            data = data[0]
        assert "parameters" in data
        assert len(data["parameters"]) > 0


class TestApiSearch:
    """Tests for `parliament api search`."""

    def test_search_division(self, cli_runner: CliRunner):
        result = cli_runner.invoke(app, ["api", "search", "division"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert "commonsvotes" in data
        assert "lordsvotes" in data

    def test_search_no_results(self, cli_runner: CliRunner):
        result = cli_runner.invoke(app, ["api", "search", "zzz_totally_nonexistent_term"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data == {}

    def test_search_case_insensitive(self, cli_runner: CliRunner):
        result_lower = cli_runner.invoke(app, ["api", "search", "division"])
        result_upper = cli_runner.invoke(app, ["api", "search", "DIVISION"])
        data_lower = json.loads(result_lower.stdout)
        data_upper = json.loads(result_upper.stdout)
        assert data_lower == data_upper

    def test_search_results_structure(self, cli_runner: CliRunner):
        result = cli_runner.invoke(app, ["api", "search", "member"])
        data = json.loads(result.stdout)
        for _api_name, endpoints in data.items():
            assert isinstance(endpoints, list)
            for ep in endpoints:
                assert "method" in ep
                assert "path" in ep


class TestApiSchema:
    """Tests for `parliament api schema`."""

    def test_schema_list_all(self, cli_runner: CliRunner):
        result = cli_runner.invoke(app, ["api", "schema", "members"])
        assert result.exit_code == 0
        schemas = json.loads(result.stdout)
        assert len(schemas) > 0
        for s in schemas:
            assert "name" in s
            assert "propertyCount" in s

    def test_schema_specific(self, cli_runner: CliRunner):
        result = cli_runner.invoke(app, ["api", "schema", "members", "Member", "--pretty"])
        assert result.exit_code == 0
        schema = json.loads(result.stdout)
        assert schema["name"] == "Member"
        assert "properties" in schema
        assert len(schema["properties"]) > 0

    def test_schema_case_insensitive(self, cli_runner: CliRunner):
        result = cli_runner.invoke(app, ["api", "schema", "members", "member"])
        assert result.exit_code == 0
        schema = json.loads(result.stdout)
        assert schema["name"] == "Member"

    def test_schema_not_found(self, cli_runner: CliRunner):
        result = cli_runner.invoke(app, ["api", "schema", "members", "NonExistentSchema"])
        assert result.exit_code == 1

    def test_schema_unknown_api(self, cli_runner: CliRunner):
        result = cli_runner.invoke(app, ["api", "schema", "nonexistent"])
        assert result.exit_code == 1


class TestApiParams:
    """Tests for `parliament api params`."""

    def test_params_bills_amendments(self, cli_runner: CliRunner):
        result = cli_runner.invoke(app, ["api", "params", "bills", "Amendments", "--pretty"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert "totalParams" in data
        assert "required" in data
        assert "optional" in data
        assert "byLocation" in data
        assert data["totalParams"] == data["required"] + data["optional"]

    def test_params_has_location_groups(self, cli_runner: CliRunner):
        result = cli_runner.invoke(app, ["api", "params", "bills", "Amendments"])
        data = json.loads(result.stdout)
        by_location = data["byLocation"]
        assert "path" in by_location
        assert "query" in by_location

    def test_params_not_found(self, cli_runner: CliRunner):
        result = cli_runner.invoke(app, ["api", "params", "members", "/nonexistent"])
        assert result.exit_code == 1

    def test_params_unknown_api(self, cli_runner: CliRunner):
        result = cli_runner.invoke(app, ["api", "params", "nonexistent", "/some/path"])
        assert result.exit_code == 1


class TestApiHelp:
    """Tests that help works for all api subcommands."""

    @pytest.mark.parametrize(
        "cmd",
        ["list", "endpoints", "detail", "search", "schema", "params"],
    )
    def test_help_exits_zero(self, cli_runner: CliRunner, cmd: str):
        result = cli_runner.invoke(app, ["api", cmd, "--help"])
        assert result.exit_code == 0

    @pytest.mark.parametrize(
        "cmd",
        ["list", "endpoints", "detail", "search", "schema", "params", "explore"],
    )
    def test_help_all_subcommands(self, cli_runner: CliRunner, cmd: str):
        result = cli_runner.invoke(app, ["api", cmd, "--help"])
        assert result.exit_code == 0

    def test_api_group_help(self, cli_runner: CliRunner):
        result = cli_runner.invoke(app, ["api", "--help"])
        assert result.exit_code == 0
        assert "api" in result.stdout.lower()


class TestApiExplore:
    """Tests for `parliament api explore`."""

    def test_explore_members_url(self, cli_runner: CliRunner):
        """Parse a Members API URL and check JSON output structure."""
        result = cli_runner.invoke(
            app,
            ["api", "explore", "https://members-api.parliament.uk/api/Members/4514"],
        )
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["api"]["name"] == "members"
        assert data["endpoint"] is not None
        assert data["endpoint"]["method"] == "GET"
        assert "{id}" in data["endpoint"]["path"]
        assert data["extractedParams"]["id"] == "4514"

    def test_explore_bills_url(self, cli_runner: CliRunner):
        """Parse a Bills API URL with a different base path."""
        result = cli_runner.invoke(
            app,
            ["api", "explore", "https://bills-api.parliament.uk/api/v1/Bills/123"],
        )
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["api"]["name"] == "bills"
        assert data["endpoint"] is not None
        assert data["extractedParams"].get("billId") == "123"

    def test_explore_with_query_params(self, cli_runner: CliRunner):
        """URL with query parameters extracts them."""
        result = cli_runner.invoke(
            app,
            [
                "api",
                "explore",
                "https://members-api.parliament.uk/api/Members/Search?Name=Starmer&skip=0&take=20",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["queryParams"]["Name"] == "Starmer"
        assert data["queryParams"]["skip"] == "0"
        assert data["queryParams"]["take"] == "20"

    def test_explore_unknown_domain(self, cli_runner: CliRunner):
        """Non-Parliament URL returns exit code 1."""
        result = cli_runner.invoke(
            app,
            ["api", "explore", "https://example.com/api/something"],
        )
        assert result.exit_code == 1

    def test_explore_no_endpoint_match(self, cli_runner: CliRunner):
        """Valid domain but unrecognized path still shows API info."""
        result = cli_runner.invoke(
            app,
            [
                "api",
                "explore",
                "https://members-api.parliament.uk/some/nonexistent/path",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["api"]["name"] == "members"
        assert data["endpoint"] is None

    @pytest.mark.parametrize(
        "api_name,expected_group",
        [
            ("members", "members"),
            ("bills", "bills"),
            ("committees", "committees"),
            ("hansard", "hansard"),
            ("commonsvotes", "votes"),
            ("lordsvotes", "votes"),
            ("interests", "interests"),
            ("parliamentnow", "live"),
            ("whatson", "live"),
            ("statutoryinstruments", "legislation"),
            ("treaties", "legislation"),
            ("erskinemay", "procedures"),
            ("oralquestions", "questions"),
            ("writtenquestions", "questions"),
        ],
    )
    def test_explore_cli_group_mapping(
        self, cli_runner: CliRunner, api_name: str, expected_group: str
    ):
        """Verify cliGroup is correct for each API."""
        from uk_parliament_mcp.cli.api import _API_CLI_GROUP

        assert _API_CLI_GROUP[api_name] == expected_group

    def test_explore_related_endpoints(self, cli_runner: CliRunner):
        """Matched endpoint returns related endpoints sharing tags."""
        result = cli_runner.invoke(
            app,
            ["api", "explore", "https://members-api.parliament.uk/api/Members/4514"],
        )
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        related = data["related"]
        assert isinstance(related, list)
        assert len(related) > 0
        # Related should have method and path
        for ep in related:
            assert "method" in ep
            assert "path" in ep

    def test_explore_pretty(self, cli_runner: CliRunner):
        """Pretty output is valid JSON with indentation."""
        result = cli_runner.invoke(
            app,
            [
                "api",
                "explore",
                "https://members-api.parliament.uk/api/Members/4514",
                "--pretty",
            ],
        )
        assert result.exit_code == 0
        assert "\n" in result.stdout
        data = json.loads(result.stdout)
        assert data["api"]["name"] == "members"

    def test_explore_has_cli_hint(self, cli_runner: CliRunner):
        """Explore output includes CLI hint."""
        result = cli_runner.invoke(
            app,
            ["api", "explore", "https://members-api.parliament.uk/api/Members/4514"],
        )
        data = json.loads(result.stdout)
        assert data["cliGroup"] == "members"
        assert "parliament members" in data["cliHint"]


class TestTemplateMatching:
    """Unit tests for URL-to-endpoint template matching."""

    def test_match_simple_path_param(self):
        from uk_parliament_mcp.cli.api import _match_url_to_endpoint

        api = {
            "endpoints": [
                {"method": "GET", "path": "/api/Items/{id}", "tags": []},
            ]
        }
        result = _match_url_to_endpoint(api, "/api/Items/42")
        assert result is not None
        ep, params = result
        assert params["id"] == "42"

    def test_match_multiple_path_params(self):
        from uk_parliament_mcp.cli.api import _match_url_to_endpoint

        api = {
            "endpoints": [
                {
                    "method": "GET",
                    "path": "/api/v1/Bills/{billId}/Stages/{stageId}",
                    "tags": [],
                },
            ]
        }
        result = _match_url_to_endpoint(api, "/api/v1/Bills/55/Stages/3")
        assert result is not None
        ep, params = result
        assert params["billId"] == "55"
        assert params["stageId"] == "3"

    def test_no_match(self):
        from uk_parliament_mcp.cli.api import _match_url_to_endpoint

        api = {
            "endpoints": [
                {"method": "GET", "path": "/api/Items/{id}", "tags": []},
            ]
        }
        result = _match_url_to_endpoint(api, "/completely/different/path")
        assert result is None

    def test_match_no_params(self):
        from uk_parliament_mcp.cli.api import _match_url_to_endpoint

        api = {
            "endpoints": [
                {"method": "GET", "path": "/api/Members/Search", "tags": []},
            ]
        }
        result = _match_url_to_endpoint(api, "/api/Members/Search")
        assert result is not None
        ep, params = result
        assert params == {}


class TestParseParliamentUrl:
    """Unit tests for _parse_parliament_url."""

    def test_parse_known_domain(self):
        from uk_parliament_mcp.cli.api import _parse_parliament_url

        result = _parse_parliament_url(
            "https://members-api.parliament.uk/api/Members/Search?Name=Test"
        )
        assert result is not None
        api, path, query = result
        assert api["name"] == "members"
        assert path == "/api/Members/Search"
        assert query["Name"] == ["Test"]

    def test_parse_unknown_domain(self):
        from uk_parliament_mcp.cli.api import _parse_parliament_url

        result = _parse_parliament_url("https://example.com/api/foo")
        assert result is None

    def test_parse_multiple_query_values(self):
        from uk_parliament_mcp.cli.api import _parse_parliament_url

        result = _parse_parliament_url(
            "https://bills-api.parliament.uk/api/v1/Bills?tag=1&tag=2"
        )
        assert result is not None
        _, _, query = result
        assert query["tag"] == ["1", "2"]
