"""Shell tab-completion helpers and the `parliament completion` command."""

from __future__ import annotations

import json
import os
import platform
import subprocess
import sys
from pathlib import Path

import typer

# ── Completer callbacks ─────────────────────────────────────────────
# Each follows the Typer autocompletion signature:
#   (incomplete: str) -> list[tuple[str, str]]

_GUIDE_TOPICS: list[tuple[str, str]] = [
    ("all", "Condensed reference of all 163 tools"),
    ("bills", "21 tools for legislation, amendments, stages"),
    ("committees", "26 tools for committee info, evidence"),
    ("composite", "5 high-level tools combining multiple API calls"),
    ("conventions", "Date formats, house IDs, pagination"),
    ("hansard", "20 tools for parliamentary record"),
    ("interests", "Register of Interests tools"),
    ("legislation", "SIs, treaties tools"),
    ("live", "Current activity, calendar tools"),
    ("members", "30 tools for MPs, Lords, constituencies"),
    ("procedures", "13 tools for Erskine May, bill types"),
    ("questions", "EDMs, oral & written questions"),
    ("votes", "10 tools for Commons and Lords divisions"),
    ("workflows", "Common research patterns"),
]

_COMMAND_GROUPS: list[tuple[str, str]] = [
    ("api", "Explore Parliament API specs"),
    ("bills", "Bill and legislation commands"),
    ("committees", "Committee info and evidence"),
    ("composite", "High-level combined commands"),
    ("digest", "Daily/weekly parliamentary summary"),
    ("guide", "Help and guidance commands"),
    ("hansard", "Parliamentary record commands"),
    ("interests", "Register of interests"),
    ("legislation", "SIs and treaties"),
    ("live", "Live activity and calendar"),
    ("members", "MP and Lords member tools"),
    ("procedures", "Erskine May procedure rules"),
    ("questions", "Oral, written questions, EDMs"),
    ("votes", "Commons and Lords divisions"),
    ("watch", "Live Parliament dashboard"),
]

_HOUSE_VALUES: list[tuple[str, str]] = [
    ("1", "Commons"),
    ("2", "Lords"),
]

# Lazily loaded from api_metadata.json
_api_names_cache: list[tuple[str, str]] | None = None


def _load_api_names() -> list[tuple[str, str]]:
    global _api_names_cache  # noqa: PLW0603
    if _api_names_cache is None:
        meta_path = Path(__file__).parent / "api_metadata.json"
        with open(meta_path, encoding="utf-8") as f:
            meta = json.load(f)
        _api_names_cache = [(api["name"], api["title"]) for api in meta["apis"]]
    return _api_names_cache


def complete_guide_topics(incomplete: str) -> list[tuple[str, str]]:
    """Return guide topics matching the incomplete prefix."""
    return [(name, desc) for name, desc in _GUIDE_TOPICS if name.startswith(incomplete.lower())]


def complete_command_groups(incomplete: str) -> list[tuple[str, str]]:
    """Return command group names matching the incomplete prefix."""
    return [
        (name, desc) for name, desc in _COMMAND_GROUPS if name.startswith(incomplete.lower())
    ]


def complete_api_names(incomplete: str) -> list[tuple[str, str]]:
    """Return API names matching the incomplete prefix."""
    return [
        (name, title) for name, title in _load_api_names() if name.startswith(incomplete.lower())
    ]


def complete_house(incomplete: str) -> list[tuple[str, str]]:
    """Return house IDs matching the incomplete prefix."""
    return [(val, desc) for val, desc in _HOUSE_VALUES if val.startswith(incomplete)]


# ── Completion command ──────────────────────────────────────────────

_SHELL_INSTRUCTIONS: dict[str, str] = {
    "bash": """\
Add this to your ~/.bashrc:

  eval "$(parliament --show-completion bash)"

Then reload:
  source ~/.bashrc""",
    "zsh": """\
Add this to your ~/.zshrc:

  eval "$(parliament --show-completion zsh)"

Then reload:
  source ~/.zshrc""",
    "fish": """\
Run once:

  parliament --show-completion fish | source

Or save to config:
  parliament --show-completion fish > ~/.config/fish/completions/parliament.fish""",
    "powershell": """\
Add this to your PowerShell profile ($PROFILE):

  parliament --show-completion powershell | Out-String | Invoke-Expression

To find your profile path:
  echo $PROFILE""",
}


def _detect_shell() -> str:
    """Detect the current shell."""
    if platform.system() == "Windows":
        # Check for common shells on Windows
        comspec = os.environ.get("COMSPEC", "").lower()
        shell_env = os.environ.get("SHELL", "").lower()
        if "pwsh" in shell_env or "powershell" in comspec:
            return "powershell"
        if "bash" in shell_env:
            return "bash"
        if "zsh" in shell_env:
            return "zsh"
        if "fish" in shell_env:
            return "fish"
        # Default on Windows
        return "powershell"

    shell_env = os.environ.get("SHELL", "")
    if "zsh" in shell_env:
        return "zsh"
    if "fish" in shell_env:
        return "fish"
    if "bash" in shell_env:
        return "bash"
    return "bash"


def completion(
    install: bool = typer.Option(False, "--install", "-i", help="Install completion for detected shell"),
    show: bool = typer.Option(False, "--show", "-s", help="Print the completion script"),
    shell: str | None = typer.Option(None, "--shell", help="Override shell detection (bash, zsh, fish, powershell)"),
) -> None:
    """Set up shell tab completion for the parliament CLI.

    Detects your shell and shows setup instructions.
    Use --install to install automatically, or --show to print the script.

    Supported shells: bash, zsh, fish, PowerShell.

    Examples:
      parliament completion              # Show setup instructions
      parliament completion --install    # Install for detected shell
      parliament completion --show       # Print the completion script
      parliament completion --shell bash # Force bash instructions
    """
    detected = shell or _detect_shell()
    detected_lower = detected.lower()

    if detected_lower not in _SHELL_INSTRUCTIONS:
        typer.echo(
            f"Unsupported shell: {detected}\n"
            f"Supported shells: {', '.join(_SHELL_INSTRUCTIONS)}",
            err=True,
        )
        raise typer.Exit(1)

    if show:
        # Delegate to Typer's built-in --show-completion
        try:
            result = subprocess.run(
                [sys.executable, "-m", "uk_parliament_mcp.cli", "--show-completion", detected_lower],
                capture_output=True,
                text=True,
            )
            if result.stdout:
                typer.echo(result.stdout)
            elif result.stderr:
                typer.echo(result.stderr, err=True)
        except Exception as exc:
            typer.echo(f"Error generating completion script: {exc}", err=True)
            raise typer.Exit(1) from exc
        return

    if install:
        typer.echo(f"Installing completion for {detected_lower}...")
        try:
            result = subprocess.run(
                [sys.executable, "-m", "uk_parliament_mcp.cli", "--install-completion", detected_lower],
                capture_output=True,
                text=True,
            )
            output = result.stdout or result.stderr or ""
            if output.strip():
                typer.echo(output.strip())
            else:
                typer.echo(f"Completion installed for {detected_lower}.")
        except Exception as exc:
            typer.echo(f"Error installing completion: {exc}", err=True)
            raise typer.Exit(1) from exc
        return

    # Default: show instructions
    typer.echo(f"Detected shell: {detected_lower}\n")
    typer.echo("Setup instructions:")
    typer.echo(_SHELL_INSTRUCTIONS[detected_lower])
    typer.echo(
        f"\nSupported shells: {', '.join(_SHELL_INSTRUCTIONS)}\n"
        "Use --shell <name> to override detection.\n"
        "Use --install to install automatically.\n"
        "Use --show to print the raw completion script."
    )
