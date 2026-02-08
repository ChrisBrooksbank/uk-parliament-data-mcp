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

    def test_api_group_help(self, cli_runner: CliRunner):
        result = cli_runner.invoke(app, ["api", "--help"])
        assert result.exit_code == 0
        assert "api" in result.stdout.lower()
