"""CLI entry point for UK Parliament data access."""

from __future__ import annotations

import sys
from typing import Optional

import click
import typer
from rich.console import Console

from uk_parliament_mcp.cli import (
    bills,
    committees,
    composite,
    digest,
    guide,
    hansard,
    interests,
    legislation,
    live,
    members,
    procedures,
    questions,
    votes,
    watch,
)
from uk_parliament_mcp.cli.formatters import OutputFormat
from uk_parliament_mcp.cli.utils import echo_utf8, format_output, run_async, should_render_rich

app = typer.Typer(
    name="parliament",
    help="UK Parliament CLI (Unofficial) - not affiliated with UK Parliament.\n\nAccess 161 Parliament API tools from the terminal.\nData sourced from publicly available parliament.uk APIs.\nhttps://github.com/ChrisBrooksbank/uk-parliament-mcp-lab",
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
app.add_typer(watch.app, name="watch")
app.add_typer(digest.app, name="digest")


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
        echo_utf8(_format_json_output(groups))
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


@app.command("my-mp")
def my_mp(
    postcode: str = typer.Argument(..., help="UK postcode (e.g., 'SW1A 1AA', 'N1 9GU')"),
    votes: str | None = typer.Option(None, "--votes", "-v", help="Filter votes by topic keyword"),
    pretty: bool = typer.Option(False, "--pretty", "-p", help="Pretty-print JSON output"),
    data_only: bool = typer.Option(
        True, "--data-only", "-d", help="Return data only (use --no-data-only for wrapper)"
    ),
    output_format: OutputFormat = typer.Option(
        OutputFormat.AUTO, "--format", "-f", help="Output format: json, table, markdown, csv, auto"
    ),
    raw: bool = typer.Option(False, "--raw", help="Output full wrapper JSON (url + data)"),
    fields: str | None = typer.Option(
        None, "--fields", help="Comma-separated field paths for columns"
    ),
) -> None:
    """
    Find your MP by postcode.

    Looks up your constituency from a UK postcode, finds the current MP,
    and shows their biography, registered interests, latest election result,
    and recent votes. Use --votes to filter votes by topic.

    Examples:
      parliament my-mp "SW1A 1AA"
      parliament my-mp "N1 9GU" --votes climate
      parliament my-mp "SW1A 1AA" --format json | jq '.basic_info'
    """
    from uk_parliament_mcp.cli.composite import _get_my_mp_async
    from uk_parliament_mcp.cli.renderers import render_my_mp

    result = run_async(_get_my_mp_async(postcode, votes))
    if should_render_rich(output_format, raw):
        render_my_mp(result)
    else:
        echo_utf8(format_output(result, pretty, data_only, output_format, fields, raw))


@app.callback()
def callback(
    raw: Optional[bool] = typer.Option(  # noqa: UP007
        None,
        "--raw",
        help="Output full wrapper JSON (url + data), disabling auto-formatting",
        is_eager=True,
    ),
    fields: Optional[str] = typer.Option(  # noqa: UP007
        None,
        "--fields",
        help="Comma-separated field paths for column selection (e.g., 'id,nameDisplayAs')",
        is_eager=True,
    ),
) -> None:
    """
    UK Parliament CLI (Unofficial) - query Parliament APIs from the terminal.

    Access MPs, bills, votes, committees, Hansard, and more.
    Data sourced from publicly available parliament.uk APIs.
    This tool is not affiliated with or endorsed by UK Parliament.
    https://github.com/ChrisBrooksbank/uk-parliament-mcp-lab
    """
    # Store global flags in typer context for subcommands to access
    ctx = typer.Context
    # We use module-level variables since typer callbacks don't propagate context easily
    import uk_parliament_mcp.cli.main as _self

    _self._global_raw = raw or False
    _self._global_fields = fields


# Module-level globals for callback-set flags
_global_raw: bool = False
_global_fields: str | None = None


def main() -> None:
    """Entry point for the CLI application."""
    # Disable response pruning — it's for MCP context windows, CLI users want full data
    from uk_parliament_mcp.pruning import disable_pruning

    disable_pruning()

    try:
        rv = app(standalone_mode=False)
        sys.exit(rv or 0)
    except click.MissingParameter as e:
        if e.ctx:
            click.echo(e.ctx.get_help())
            click.echo()
        click.echo(f"Error: {e.format_message()}", err=True)
        sys.exit(2)
    except click.ClickException as e:
        e.show()
        sys.exit(e.exit_code)
    except click.Abort:
        click.echo("Aborted!", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
