"""Tests for the `parliament guide` commands and the command-reference introspection."""

from __future__ import annotations

import json
from io import StringIO

from rich.console import Console
from typer.testing import CliRunner

from uk_parliament_mcp.cli import guide
from uk_parliament_mcp.cli.main import app

runner = CliRunner()


def _console() -> tuple[Console, StringIO]:
    output = StringIO()
    return Console(file=output, width=200, color_system=None), output


class TestIntrospection:
    def test_finds_every_group_and_command(self) -> None:
        groups = {g.name: g for g in guide._get_all_commands()}
        assert {"members", "bills", "votes", "composite", "guide"} <= set(groups)
        composite = {c.name: c for c in groups["composite"].commands}
        assert {"search", "compare-votes", "bill-committees"} <= set(composite)

    def test_extracts_arguments_and_options(self) -> None:
        groups = {g.name: g for g in guide._get_all_commands()}
        compare = next(c for c in groups["composite"].commands if c.name == "compare-votes")
        params = {p.name: p for p in compare.parameters}
        assert params["member_id_a"].param_type == "argument"
        assert params["member_id_a"].required
        assert params["topic"].param_type == "option"
        assert "--topic" in params["topic"].flags
        assert params["take"].default == 50

    def test_json_output(self) -> None:
        groups = guide._get_all_commands()
        data = json.loads(guide._format_json_output(groups))
        assert data["total_groups"] == len(groups)
        assert data["total_commands"] == sum(len(g.commands) for g in groups)
        assert data["groups"][0]["commands"][0]["name"]


class TestFormatting:
    def test_overview(self) -> None:
        console, output = _console()
        guide._format_overview(guide._get_all_commands(), console)
        text = output.getvalue()
        assert "Command Reference" in text
        assert "COMPOSITE" in text
        assert "compare-votes <member_id_a> <member_id_b>" in text

    def test_group_detail_skips_common_options(self) -> None:
        groups = {g.name: g for g in guide._get_all_commands()}
        console, output = _console()
        guide._format_group_detail(groups["composite"], console)
        text = output.getvalue()
        assert "Arguments:" in text and "member_id_a" in text
        assert "--topic" in text
        assert "--pretty" not in text
        assert "parliament composite compare-votes <member_id_a> <member_id_b>" in text

    def test_search_results(self) -> None:
        console, output = _console()
        guide._format_search_results(guide._get_all_commands(), "postcode", console)
        text = output.getvalue()
        assert "Search Results" in text
        assert "my-mp" in text

    def test_search_no_results(self) -> None:
        console, output = _console()
        guide._format_search_results(guide._get_all_commands(), "zzzzqqq", console)
        assert "No commands found" in output.getvalue()


class TestCommands:
    def test_reference_json_when_not_a_terminal(self) -> None:
        result = runner.invoke(app, ["guide", "reference"])
        assert result.exit_code == 0
        assert json.loads(result.stdout)["total_groups"] > 10

    def test_reference_table_overview(self) -> None:
        result = runner.invoke(app, ["guide", "reference", "--format", "table"])
        assert result.exit_code == 0
        assert "Command Reference" in result.stdout

    def test_reference_group(self) -> None:
        result = runner.invoke(app, ["guide", "reference", "votes", "--format", "table"])
        assert result.exit_code == 0
        assert "VOTES" in result.stdout

    def test_reference_search(self) -> None:
        result = runner.invoke(app, ["guide", "reference", "-s", "division", "--format", "table"])
        assert result.exit_code == 0
        assert "Search Results" in result.stdout

    def test_reference_unknown_group(self) -> None:
        result = runner.invoke(app, ["guide", "reference", "nope", "--format", "table"])
        assert result.exit_code == 1
        assert "not found" in result.stdout

    def test_tools(self) -> None:
        result = runner.invoke(app, ["guide", "tools"])
        assert result.exit_code == 0
        assert "Quick Reference" in result.stdout

    def test_topic(self) -> None:
        result = runner.invoke(app, ["guide", "topic", "Votes"])
        assert result.exit_code == 0
        assert "Voting Tools" in result.stdout

    def test_unknown_topic_lists_topics(self) -> None:
        result = runner.invoke(app, ["guide", "topic", "astrology"])
        assert "not recognized" in result.stdout
        assert "composite" in result.stdout

    def test_workflow(self) -> None:
        result = runner.invoke(app, ["guide", "workflow", "how did my MP vote on climate"])
        assert result.exit_code == 0
        assert result.stdout.strip()
