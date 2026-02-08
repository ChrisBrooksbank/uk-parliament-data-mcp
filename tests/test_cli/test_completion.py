"""Tests for shell tab-completion helpers."""

from __future__ import annotations

from typer.testing import CliRunner

from uk_parliament_mcp.cli.completion import (
    complete_api_names,
    complete_command_groups,
    complete_guide_topics,
    complete_house,
)
from uk_parliament_mcp.cli.main import app

runner = CliRunner()


# ── Completer callback tests ───────────────────────────────────────


class TestCompleteGuideTopics:
    def test_empty_returns_all(self) -> None:
        results = complete_guide_topics("")
        names = [name for name, _ in results]
        assert "members" in names
        assert "bills" in names
        assert "all" in names
        assert "workflows" in names
        assert len(results) >= 14

    def test_prefix_filter(self) -> None:
        results = complete_guide_topics("m")
        names = [name for name, _ in results]
        assert "members" in names
        assert "bills" not in names

    def test_no_match(self) -> None:
        results = complete_guide_topics("zzz")
        assert results == []

    def test_returns_tuples(self) -> None:
        results = complete_guide_topics("b")
        assert len(results) >= 1
        name, desc = results[0]
        assert isinstance(name, str)
        assert isinstance(desc, str)


class TestCompleteCommandGroups:
    def test_empty_returns_all(self) -> None:
        results = complete_command_groups("")
        names = [name for name, _ in results]
        assert "api" in names
        assert "members" in names
        assert "guide" in names
        assert len(results) >= 15

    def test_prefix_filter(self) -> None:
        results = complete_command_groups("l")
        names = [name for name, _ in results]
        assert "live" in names
        assert "legislation" in names
        assert "members" not in names

    def test_no_match(self) -> None:
        results = complete_command_groups("zzz")
        assert results == []


class TestCompleteApiNames:
    def test_empty_returns_all(self) -> None:
        results = complete_api_names("")
        names = [name for name, _ in results]
        assert "members" in names
        assert "bills" in names
        assert len(results) >= 14

    def test_prefix_filter(self) -> None:
        results = complete_api_names("m")
        names = [name for name, _ in results]
        assert "members" in names
        assert "bills" not in names

    def test_no_match(self) -> None:
        results = complete_api_names("zzz")
        assert results == []

    def test_returns_name_and_title(self) -> None:
        results = complete_api_names("members")
        assert len(results) == 1
        name, title = results[0]
        assert name == "members"
        assert isinstance(title, str)
        assert len(title) > 0


class TestCompleteHouse:
    def test_empty_returns_both(self) -> None:
        results = complete_house("")
        assert len(results) == 2
        names = [name for name, _ in results]
        assert "1" in names
        assert "2" in names

    def test_prefix_1(self) -> None:
        results = complete_house("1")
        assert len(results) == 1
        assert results[0] == ("1", "Commons")

    def test_prefix_2(self) -> None:
        results = complete_house("2")
        assert len(results) == 1
        assert results[0] == ("2", "Lords")

    def test_no_match(self) -> None:
        results = complete_house("3")
        assert results == []


# ── Completion command tests ────────────────────────────────────────


class TestCompletionCommand:
    def test_default_shows_instructions(self) -> None:
        result = runner.invoke(app, ["completion"])
        assert result.exit_code == 0
        assert "Detected shell:" in result.output
        assert "Setup instructions:" in result.output

    def test_force_bash(self) -> None:
        result = runner.invoke(app, ["completion", "--shell", "bash"])
        assert result.exit_code == 0
        assert "bashrc" in result.output

    def test_force_zsh(self) -> None:
        result = runner.invoke(app, ["completion", "--shell", "zsh"])
        assert result.exit_code == 0
        assert "zshrc" in result.output

    def test_force_fish(self) -> None:
        result = runner.invoke(app, ["completion", "--shell", "fish"])
        assert result.exit_code == 0
        assert "fish" in result.output

    def test_force_powershell(self) -> None:
        result = runner.invoke(app, ["completion", "--shell", "powershell"])
        assert result.exit_code == 0
        assert "PROFILE" in result.output

    def test_unsupported_shell(self) -> None:
        result = runner.invoke(app, ["completion", "--shell", "csh"])
        assert result.exit_code == 1

    def test_help_mentions_completion(self) -> None:
        result = runner.invoke(app, ["--help"])
        assert "completion" in result.output.lower()
