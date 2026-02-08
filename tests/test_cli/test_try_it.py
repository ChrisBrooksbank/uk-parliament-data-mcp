"""Tests for CLI 'api try' interactive mode."""

from __future__ import annotations

import json
from unittest.mock import patch

from typer.testing import CliRunner

from uk_parliament_mcp.cli.main import app
from uk_parliament_mcp.cli.try_it import (
    _build_api_url,
    _find_endpoint_by_path,
    _prompt_for_params,
)


class TestBuildApiUrl:
    """Tests for URL construction from endpoint templates and params."""

    def test_simple_query_params(self):
        api = {"baseUrl": "https://members-api.parliament.uk"}
        endpoint = {"path": "/api/Members/Search"}
        url = _build_api_url(api, endpoint, {}, {"Name": "Starmer"})
        assert url == "https://members-api.parliament.uk/api/Members/Search?Name=Starmer"

    def test_path_params_substitution(self):
        api = {"baseUrl": "https://members-api.parliament.uk"}
        endpoint = {"path": "/api/Members/{id}"}
        url = _build_api_url(api, endpoint, {"id": "4514"}, {})
        assert url == "https://members-api.parliament.uk/api/Members/4514"

    def test_multiple_path_params(self):
        api = {"baseUrl": "https://bills-api.parliament.uk"}
        endpoint = {"path": "/api/v1/Bills/{billId}/Stages/{stageId}"}
        url = _build_api_url(api, endpoint, {"billId": "55", "stageId": "3"}, {})
        assert url == "https://bills-api.parliament.uk/api/v1/Bills/55/Stages/3"

    def test_path_and_query_params(self):
        api = {"baseUrl": "https://bills-api.parliament.uk"}
        endpoint = {"path": "/api/v1/Bills/{billId}/Amendments"}
        url = _build_api_url(api, endpoint, {"billId": "10"}, {"SearchTerm": "test", "Skip": "0"})
        assert "Bills/10/Amendments" in url
        assert "SearchTerm=test" in url
        assert "Skip=0" in url

    def test_no_params(self):
        api = {"baseUrl": "https://now-api.parliament.uk"}
        endpoint = {"path": "/api/Message/message"}
        url = _build_api_url(api, endpoint, {}, {})
        assert url == "https://now-api.parliament.uk/api/Message/message"

    def test_path_param_encoding(self):
        api = {"baseUrl": "https://example.parliament.uk"}
        endpoint = {"path": "/api/Items/{name}"}
        url = _build_api_url(api, endpoint, {"name": "hello world"}, {})
        assert "hello%20world" in url

    def test_query_param_encoding(self):
        api = {"baseUrl": "https://members-api.parliament.uk"}
        endpoint = {"path": "/api/Members/Search"}
        url = _build_api_url(api, endpoint, {}, {"Name": "De Souza"})
        assert "Name=De+Souza" in url or "Name=De%20Souza" in url


class TestFindEndpointByPath:
    """Tests for endpoint lookup by partial path."""

    def test_exact_match(self):
        api = {
            "endpoints": [
                {"path": "/api/Members/Search", "method": "GET"},
                {"path": "/api/Members/{id}", "method": "GET"},
            ]
        }
        ep = _find_endpoint_by_path(api, "/api/Members/Search")
        assert ep is not None
        assert ep["path"] == "/api/Members/Search"

    def test_partial_match(self):
        api = {
            "endpoints": [
                {"path": "/api/Members/Search", "method": "GET"},
                {"path": "/api/Members/{id}", "method": "GET"},
            ]
        }
        ep = _find_endpoint_by_path(api, "Members/Search")
        assert ep is not None
        assert ep["path"] == "/api/Members/Search"

    def test_case_insensitive(self):
        api = {
            "endpoints": [
                {"path": "/api/Members/Search", "method": "GET"},
            ]
        }
        ep = _find_endpoint_by_path(api, "members/search")
        assert ep is not None

    def test_no_match(self):
        api = {
            "endpoints": [
                {"path": "/api/Members/Search", "method": "GET"},
            ]
        }
        ep = _find_endpoint_by_path(api, "nonexistent")
        assert ep is None


class TestTryEndpointCommand:
    """Tests for the `parliament api try` command registration and help."""

    def test_help_exits_zero(self, cli_runner: CliRunner):
        result = cli_runner.invoke(app, ["api", "try", "--help"])
        assert result.exit_code == 0
        assert "try" in result.stdout.lower() or "interactively" in result.stdout.lower()

    def test_unknown_api_name(self, cli_runner: CliRunner):
        result = cli_runner.invoke(app, ["api", "try", "nonexistent"])
        assert result.exit_code == 1

    def test_known_api_unknown_path(self, cli_runner: CliRunner):
        result = cli_runner.invoke(app, ["api", "try", "members", "zzz_nonexistent"])
        assert result.exit_code == 1


class TestTryEndpointWithInput:
    """Tests that simulate user input through the interactive flow."""

    def test_direct_api_and_path_calls_api(self, cli_runner: CliRunner):
        """Providing api_name + path skips menus and prompts for params."""
        mock_response = json.dumps(
            {
                "url": "https://members-api.parliament.uk/api/Members/Search?Name=Starmer",
                "data": {
                    "items": [{"value": {"id": 4514, "nameDisplayAs": "Keir Starmer"}}],
                    "totalResults": 1,
                },
            }
        )

        async def _mock_get_result(url: str) -> str:
            return mock_response

        with patch("uk_parliament_mcp.cli.try_it.get_result", _mock_get_result):
            # Simulate: fill param "Name" = "Starmer", skip rest, then quit
            # Members/Search has 20 params; we need Enter for each
            inputs = ["Starmer"] + [""] * 19 + ["q"]
            result = cli_runner.invoke(
                app,
                ["api", "try", "members", "Members/Search"],
                input="\n".join(inputs),
            )
            assert result.exit_code == 0
            assert "Starmer" in result.output

    def test_endpoint_with_path_param_only(self, cli_runner: CliRunner):
        """An endpoint with a single path param prompts for it."""
        mock_response = json.dumps(
            {
                "url": "https://now-api.parliament.uk/api/Message/message/Commons/current",
                "data": {"message": "House is sitting"},
            }
        )

        async def _mock_get_result(url: str) -> str:
            return mock_response

        with patch("uk_parliament_mcp.cli.try_it.get_result", _mock_get_result):
            # parliamentnow "message/{annunciator}/current" has 1 path param
            result = cli_runner.invoke(
                app,
                ["api", "try", "parliamentnow", "current"],
                input="Commons\nq\n",
            )
            assert result.exit_code == 0

    def test_api_error_displayed(self, cli_runner: CliRunner):
        """API errors are shown in red panel."""
        mock_response = json.dumps(
            {"url": "https://example.com", "error": "Not Found", "statusCode": 404}
        )

        async def _mock_get_result(url: str) -> str:
            return mock_response

        with patch("uk_parliament_mcp.cli.try_it.get_result", _mock_get_result):
            # Members/{id} has 2 params: id (path, required) + detailsForDate (query, optional)
            result = cli_runner.invoke(
                app,
                ["api", "try", "members", "Members/{id}"],
                input="9999999\n\nq\n",
            )
            assert result.exit_code == 0

    def test_try_again_action(self, cli_runner: CliRunner):
        """The 't' action re-prompts for the same endpoint."""
        call_count = 0
        mock_response = json.dumps({"url": "https://example.com", "data": {"items": []}})

        async def _mock_get_result(url: str) -> str:
            nonlocal call_count
            call_count += 1
            return mock_response

        with patch("uk_parliament_mcp.cli.try_it.get_result", _mock_get_result):
            # Members/{id} has 2 params: id (required) + detailsForDate (optional)
            # First call: id=1, skip detailsForDate, action=t
            # Second call: id=2, skip detailsForDate, action=q
            inputs = ["1", "", "t", "2", "", "q"]
            result = cli_runner.invoke(
                app,
                ["api", "try", "members", "Members/{id}"],
                input="\n".join(inputs),
            )
            assert result.exit_code == 0
            assert call_count == 2


class TestPromptForParams:
    """Tests for the parameter prompting logic."""

    def test_no_params_returns_empty(self):
        from io import StringIO

        from rich.console import Console

        console = Console(file=StringIO())
        endpoint = {"parameters": []}
        path_params, query_params = _prompt_for_params(console, endpoint)
        assert path_params == {}
        assert query_params == {}

    def test_no_params_key_returns_empty(self):
        from io import StringIO

        from rich.console import Console

        console = Console(file=StringIO())
        endpoint = {}
        path_params, query_params = _prompt_for_params(console, endpoint)
        assert path_params == {}
        assert query_params == {}
