"""Guide CLI commands for help and workflow guidance."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Any

import click
import typer
import typer.main
from rich.console import Console
from rich.panel import Panel

from uk_parliament_mcp.cli.utils import echo_utf8, run_async
from uk_parliament_mcp.tools.core import (
    GUIDANCE_CONTENT,
    QUICK_REFERENCE,
    SYSTEM_PROMPT,
    WORKFLOW_PATTERNS,
    _format_workflow,
    _suggest_general_approach,
)


# Data classes for command metadata
@dataclass
class ParameterInfo:
    """Information about a command parameter."""

    name: str
    param_type: str
    required: bool
    default: Any
    flags: list[str]
    help_text: str


@dataclass
class CommandInfo:
    """Information about a CLI command."""

    name: str
    group: str
    description: str
    parameters: list[ParameterInfo] = field(default_factory=list)


@dataclass
class GroupInfo:
    """Information about a command group."""

    name: str
    description: str
    commands: list[CommandInfo] = field(default_factory=list)


def _extract_parameters(cmd: click.Command) -> list[ParameterInfo]:
    """Extract parameter info from a Click command."""
    params = []
    for param in cmd.params:
        if isinstance(param, click.Argument):
            params.append(
                ParameterInfo(
                    name=param.name or "",
                    param_type="argument",
                    required=param.required,
                    default=param.default,
                    flags=[],
                    help_text=getattr(param, "help", "") or "",
                )
            )
        elif isinstance(param, click.Option):
            params.append(
                ParameterInfo(
                    name=param.name or "",
                    param_type="option",
                    required=param.required,
                    default=param.default if param.default != param.type else None,
                    flags=list(param.opts),
                    help_text=param.help or "",
                )
            )
    return params


def _get_all_commands() -> list[GroupInfo]:
    """Get all commands from the main CLI app via introspection."""
    # Import inside function to avoid circular imports
    from uk_parliament_mcp.cli.main import app as main_app

    click_app = typer.main.get_command(main_app)
    groups: list[GroupInfo] = []

    if not isinstance(click_app, click.Group):
        return groups

    for group_name, group_cmd in sorted(click_app.commands.items()):
        if not isinstance(group_cmd, click.Group):
            continue

        group_help = group_cmd.help or ""
        group_info = GroupInfo(name=group_name, description=group_help, commands=[])

        for cmd_name, cmd in sorted(group_cmd.commands.items()):
            if not isinstance(cmd, click.Command):
                continue

            cmd_help = cmd.help or ""
            # Take first line of help as description
            description = cmd_help.split("\n")[0].strip() if cmd_help else ""

            cmd_info = CommandInfo(
                name=cmd_name,
                group=group_name,
                description=description,
                parameters=_extract_parameters(cmd),
            )
            group_info.commands.append(cmd_info)

        groups.append(group_info)

    return groups


def _format_overview(groups: list[GroupInfo], console: Console) -> None:
    """Format an overview of all command groups."""
    total_commands = sum(len(g.commands) for g in groups)

    console.print(
        Panel(
            f"[bold]{total_commands}[/bold] commands across [bold]{len(groups)}[/bold] groups",
            title="[bold cyan]UK Parliament CLI - Command Reference[/bold cyan]",
            border_style="cyan",
        )
    )
    console.print()

    for group in groups:
        # Group header
        console.print(
            f"[bold yellow]{group.name.upper()}[/bold yellow] "
            f"[dim]({len(group.commands)} commands)[/dim]"
        )

        # Commands table
        for cmd in group.commands:
            # Build argument signature
            args = []
            for p in cmd.parameters:
                if p.param_type == "argument":
                    args.append(f"<{p.name}>")

            arg_str = " ".join(args)
            cmd_sig = f"  [green]{cmd.name}[/green]"
            if arg_str:
                cmd_sig += f" [cyan]{arg_str}[/cyan]"

            # Truncate description if too long
            desc = cmd.description[:50] + "..." if len(cmd.description) > 50 else cmd.description
            console.print(f"{cmd_sig:<40} [dim]{desc}[/dim]")

        console.print()


def _format_group_detail(group: GroupInfo, console: Console) -> None:
    """Format detailed view of a single command group."""
    console.print(
        Panel(
            f"[dim]{group.description}[/dim]",
            title=f"[bold yellow]{group.name.upper()}[/bold yellow]",
            border_style="yellow",
        )
    )
    console.print()

    for cmd in group.commands:
        # Command name and description
        console.print(f"[bold green]{cmd.name}[/bold green]")
        if cmd.description:
            console.print(f"  [dim]{cmd.description}[/dim]")
        console.print()

        # Arguments
        args = [p for p in cmd.parameters if p.param_type == "argument"]
        if args:
            console.print("  [bold]Arguments:[/bold]")
            for arg in args:
                req_str = "[red][required][/red]" if arg.required else "[dim][optional][/dim]"
                console.print(f"    [cyan]{arg.name:<20}[/cyan] {req_str}")
                if arg.help_text:
                    console.print(f"    [dim]{arg.help_text}[/dim]")

        # Options (exclude common flags like --pretty, --data-only, --format)
        common_opts = {"pretty", "data_only", "output_format"}
        opts = [p for p in cmd.parameters if p.param_type == "option" and p.name not in common_opts]
        if opts:
            console.print("  [bold]Options:[/bold]")
            for opt in opts:
                flags = ", ".join(opt.flags) if opt.flags else f"--{opt.name}"
                console.print(f"    [magenta]{flags}[/magenta]")
                if opt.help_text:
                    console.print(f"      [dim]{opt.help_text}[/dim]")

        # Example usage
        arg_str = " ".join(f"<{a.name}>" for a in args)
        example = f"parliament {group.name} {cmd.name}"
        if arg_str:
            example += f" {arg_str}"
        console.print("  [bold]Example:[/bold]")
        console.print(f"    [white on black]{example}[/white on black]")
        console.print()


def _format_search_results(groups: list[GroupInfo], search_term: str, console: Console) -> None:
    """Format search results matching a keyword."""
    search_lower = search_term.lower()
    matches: list[CommandInfo] = []

    for group in groups:
        for cmd in group.commands:
            # Search in command name, description, and parameter names
            searchable = f"{cmd.name} {cmd.description} {' '.join(p.name for p in cmd.parameters)}"
            if search_lower in searchable.lower():
                matches.append(cmd)

    if not matches:
        console.print(f"[yellow]No commands found matching '[bold]{search_term}[/bold]'[/yellow]")
        return

    console.print(
        Panel(
            f"[bold]{len(matches)}[/bold] commands matching '[bold]{search_term}[/bold]'",
            title="[bold cyan]Search Results[/bold cyan]",
            border_style="cyan",
        )
    )
    console.print()

    for cmd in matches:
        # Build argument signature
        args = [f"<{p.name}>" for p in cmd.parameters if p.param_type == "argument"]
        arg_str = " ".join(args)

        cmd_line = f"[green]{cmd.group}[/green] [bold]{cmd.name}[/bold]"
        if arg_str:
            cmd_line += f" [cyan]{arg_str}[/cyan]"

        console.print(cmd_line)
        if cmd.description:
            console.print(f"  [dim]{cmd.description}[/dim]")
        console.print()


def _format_json_output(groups: list[GroupInfo]) -> str:
    """Format all commands as JSON."""
    output = {
        "total_commands": sum(len(g.commands) for g in groups),
        "total_groups": len(groups),
        "groups": [asdict(g) for g in groups],
    }
    return json.dumps(output, indent=2, default=str)


app = typer.Typer(help="Help and guidance for UK Parliament research", no_args_is_help=True)


async def _order_order_async() -> str:
    """Start UK Parliament research session."""
    return f"{SYSTEM_PROMPT}\n\n---\n\n{QUICK_REFERENCE}"


async def _parliament_guide_async(topic: str) -> str:
    """Get detailed guidance for a specific Parliament data domain."""
    topic_lower = topic.lower().strip()

    if topic_lower not in GUIDANCE_CONTENT:
        available = ", ".join(sorted(GUIDANCE_CONTENT.keys()))
        return f"Topic '{topic}' not recognized.\n\nAvailable topics: {available}"

    return GUIDANCE_CONTENT[topic_lower]


async def _parliament_workflow_async(query: str) -> str:
    """Get step-by-step workflow guidance for a parliamentary research task."""
    query_lower = query.lower()

    # Find matching workflow pattern
    for pattern in WORKFLOW_PATTERNS:
        if any(keyword in query_lower for keyword in pattern["keywords"]):
            return _format_workflow(pattern)

    # No match - provide general guidance
    return _suggest_general_approach(query)


@app.command("tools")
def tools(
    pretty: bool = typer.Option(False, "--pretty", "-p", help="Pretty-print output"),
) -> None:
    """
    Start UK Parliament research session - list all available tools.

    Returns system prompt and quick reference of all 161 tool categories with
    entry points, key conventions, and common patterns.
    """
    result = run_async(_order_order_async())
    # For guide commands, output is plain text, not JSON
    # So we skip the format_output wrapper
    echo_utf8(result)


@app.command("topic")
def topic(
    domain: str = typer.Argument(..., help="Domain to get guidance for"),
    pretty: bool = typer.Option(False, "--pretty", "-p", help="Pretty-print output"),
) -> None:
    """
    Get detailed guidance for a specific Parliament data domain.

    Available topics: members, bills, votes, committees, hansard, questions,
    interests, live, legislation, procedures, all, conventions, workflows.

    Returns comprehensive guidance including tool names, parameters, and
    typical workflows for the selected domain.
    """
    result = run_async(_parliament_guide_async(domain))
    echo_utf8(result)


@app.command("workflow")
def workflow(
    query: str = typer.Argument(..., help="Research question or task description"),
    pretty: bool = typer.Option(False, "--pretty", "-p", help="Pretty-print output"),
) -> None:
    """
    Get step-by-step workflow guidance for a parliamentary research task.

    Matches queries to predefined patterns and returns recommended sequence
    of tools with parameters and expected data flow.

    Examples:
      - "How did my MP vote on X?"
      - "Track bill progress"
      - "What committee examined X?"
      - "Does MP have conflicts of interest?"
    """
    result = run_async(_parliament_workflow_async(query))
    echo_utf8(result)


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
      parliament guide reference              # Overview of all groups
      parliament guide reference members      # Detailed view of members commands
      parliament guide reference --search vote # Search for vote-related commands
      parliament guide reference --json       # Export as JSON
    """
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
