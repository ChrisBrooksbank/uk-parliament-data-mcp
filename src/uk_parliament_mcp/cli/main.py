"""CLI entry point for UK Parliament data access."""

from __future__ import annotations

import typer
from rich.console import Console

from uk_parliament_mcp.cli import (
    bills,
    committees,
    composite,
    guide,
    hansard,
    interests,
    legislation,
    live,
    members,
    procedures,
    questions,
    votes,
)

app = typer.Typer(
    name="parliament",
    help="UK Parliament data CLI - Access 161 Parliament API tools from the terminal.",
    no_args_is_help=True,
)

# Register subcommand groups
app.add_typer(composite.app, name="composite")
app.add_typer(members.app, name="members")
app.add_typer(bills.app, name="bills")
app.add_typer(votes.app, name="votes")
app.add_typer(committees.app, name="committees")
app.add_typer(hansard.app, name="hansard")
app.add_typer(questions.app, name="questions")
app.add_typer(interests.app, name="interests")
app.add_typer(live.app, name="live")
app.add_typer(legislation.app, name="legislation")
app.add_typer(procedures.app, name="procedures")
app.add_typer(guide.app, name="guide")


# Top-level reference command for easy discoverability
@app.command("reference")
def reference(
    group: str | None = typer.Argument(None, help="Group to show details for"),
    search: str | None = typer.Option(None, "--search", "-s", help="Search commands by keyword"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
) -> None:
    """
    Show comprehensive CLI command reference.

    With no arguments, shows an overview of all command groups.
    Specify a group name to see detailed info for that group.
    Use --search to find commands matching a keyword.

    Examples:
      parliament reference              # Overview of all groups
      parliament reference members      # Detailed view of members commands
      parliament reference --search vote # Search for vote-related commands
      parliament reference --json       # Export as JSON
    """
    # Import here to avoid circular imports at module load time
    from uk_parliament_mcp.cli.guide import (
        _format_group_detail,
        _format_json_output,
        _format_overview,
        _format_search_results,
        _get_all_commands,
    )

    console = Console()
    groups = _get_all_commands()

    if json_output:
        typer.echo(_format_json_output(groups))
        return

    if search:
        _format_search_results(groups, search, console)
        return

    if group:
        # Find the specific group
        group_lower = group.lower()
        matching = [g for g in groups if g.name.lower() == group_lower]
        if not matching:
            available = ", ".join(g.name for g in groups)
            console.print(
                f"[red]Group '[bold]{group}[/bold]' not found.[/red]\n"
                f"[dim]Available groups: {available}[/dim]"
            )
            raise typer.Exit(1)
        _format_group_detail(matching[0], console)
        return

    _format_overview(groups, console)


@app.callback()
def callback() -> None:
    """
    UK Parliament CLI - query Parliament APIs from the terminal.

    Access MPs, bills, votes, committees, Hansard, and more.
    All data sourced from official parliament.uk APIs.
    """
    pass


def main() -> None:
    """Entry point for the CLI application."""
    app()


if __name__ == "__main__":
    main()
