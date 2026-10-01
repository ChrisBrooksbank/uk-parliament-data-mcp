"""Tests for CLI main entry point."""

from __future__ import annotations

from typer.testing import CliRunner

from uk_parliament_mcp.cli.main import app


class TestMainApp:
    """Tests for main CLI application."""

    def test_app_help(self, cli_runner: CliRunner):
        """Test that --help shows command groups."""
        result = cli_runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "parliament" in result.stdout.lower()
        assert "members" in result.stdout.lower()
        assert "bills" in result.stdout.lower()
        assert "votes" in result.stdout.lower()
        assert "committees" in result.stdout.lower()
        assert "composite" in result.stdout.lower()

    def test_app_no_args_shows_help(self, cli_runner: CliRunner):
        """Test that running with no args shows help."""
        result = cli_runner.invoke(app, [])
        # Exit code 2 is expected when no args provided (Typer behavior)
        # This is correct - it shows help but indicates missing required command
        assert result.exit_code in [0, 2]
        assert "Usage:" in result.stdout

    def test_members_subcommand_exists(self, cli_runner: CliRunner):
        """Test that members subcommand is available."""
        result = cli_runner.invoke(app, ["members", "--help"])
        assert result.exit_code == 0
        assert "members" in result.stdout.lower()

    def test_bills_subcommand_exists(self, cli_runner: CliRunner):
        """Test that bills subcommand is available."""
        result = cli_runner.invoke(app, ["bills", "--help"])
        assert result.exit_code == 0
        assert "bills" in result.stdout.lower()

    def test_composite_subcommand_exists(self, cli_runner: CliRunner):
        """Test that composite subcommand is available."""
        result = cli_runner.invoke(app, ["composite", "--help"])
        assert result.exit_code == 0
        assert "composite" in result.stdout.lower()

    def test_votes_subcommand_exists(self, cli_runner: CliRunner):
        """Test that votes subcommand is available."""
        result = cli_runner.invoke(app, ["votes", "--help"])
        assert result.exit_code == 0
        assert "votes" in result.stdout.lower()

    def test_committees_subcommand_exists(self, cli_runner: CliRunner):
        """Test that committees subcommand is available."""
        result = cli_runner.invoke(app, ["committees", "--help"])
        assert result.exit_code == 0
        assert "committees" in result.stdout.lower()

    def test_hansard_subcommand_exists(self, cli_runner: CliRunner):
        """Test that hansard subcommand is available."""
        result = cli_runner.invoke(app, ["hansard", "--help"])
        assert result.exit_code == 0
        assert "hansard" in result.stdout.lower()

    def test_questions_subcommand_exists(self, cli_runner: CliRunner):
        """Test that questions subcommand is available."""
        result = cli_runner.invoke(app, ["questions", "--help"])
        assert result.exit_code == 0
        assert "questions" in result.stdout.lower()

    def test_interests_subcommand_exists(self, cli_runner: CliRunner):
        """Test that interests subcommand is available."""
        result = cli_runner.invoke(app, ["interests", "--help"])
        assert result.exit_code == 0
        assert "interests" in result.stdout.lower()

    def test_live_subcommand_exists(self, cli_runner: CliRunner):
        """Test that live subcommand is available."""
        result = cli_runner.invoke(app, ["live", "--help"])
        assert result.exit_code == 0
        assert "live" in result.stdout.lower()

    def test_legislation_subcommand_exists(self, cli_runner: CliRunner):
        """Test that legislation subcommand is available."""
        result = cli_runner.invoke(app, ["legislation", "--help"])
        assert result.exit_code == 0
        assert "legislation" in result.stdout.lower()

    def test_procedures_subcommand_exists(self, cli_runner: CliRunner):
        """Test that procedures subcommand is available."""
        result = cli_runner.invoke(app, ["procedures", "--help"])
        assert result.exit_code == 0
        assert "procedures" in result.stdout.lower()

    def test_guide_subcommand_exists(self, cli_runner: CliRunner):
        """Test that guide subcommand is available."""
        result = cli_runner.invoke(app, ["guide", "--help"])
        assert result.exit_code == 0
        assert "guide" in result.stdout.lower()


class TestMissingArgShowsHelp:
    """Tests for missing argument behavior."""

    def test_missing_arg_exits_with_error(self, cli_runner: CliRunner):
        """Missing required argument reports error."""
        result = cli_runner.invoke(app, ["committees", "search"])
        assert result.exit_code == 2


def test_global_raw_and_fields_apply_to_subcommand() -> None:
    """`parliament --raw <cmd>` and `parliament --fields ... <cmd>` take effect."""
    import json
    from unittest.mock import AsyncMock, patch

    response = json.dumps(
        {"url": "https://test/BillTypes", "data": {"items": [{"id": 1, "name": "A", "x": 2}]}}
    )
    runner = CliRunner()
    with patch("uk_parliament_mcp.cli.utils.get_result", new=AsyncMock(return_value=response)):
        raw = runner.invoke(app, ["--raw", "bills", "types"])
        fields = runner.invoke(app, ["--fields", "id,name", "bills", "types", "--format", "csv"])
        plain = runner.invoke(app, ["bills", "types", "--format", "csv"])
    assert json.loads(raw.stdout)["url"] == "https://test/BillTypes"
    assert fields.stdout.splitlines()[0] == "Id,Name"
    # The callback resets the globals on each invocation
    assert plain.stdout.splitlines()[0] == "Id,Name,X"


def test_cli_imports_without_mcp_package() -> None:
    """The standalone executable (parliament.spec) bundles the CLI without mcp."""
    import subprocess
    import sys

    code = (
        "import sys; sys.modules['mcp'] = None\nimport uk_parliament_mcp.cli.main  # noqa: F401\n"
    )
    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
