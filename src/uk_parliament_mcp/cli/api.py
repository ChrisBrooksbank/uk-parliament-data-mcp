"""API spec explorer CLI commands.

Lets users query the 14 Parliament OpenAPI specs directly:
discover endpoints, parameters, schemas, and search across all APIs.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import typer
from rich.console import Console
from rich.table import Table

from uk_parliament_mcp.cli.utils import echo_utf8

app = typer.Typer(
    name="api",
    help="Explore Parliament API specs — endpoints, parameters, schemas.",
    no_args_is_help=True,
)

_METADATA_PATH = Path(__file__).parent / "api_metadata.json"
_metadata_cache: dict[str, Any] | None = None


def _load_metadata() -> dict[str, Any]:
    """Load and cache the API metadata."""
    global _metadata_cache  # noqa: PLW0603
    if _metadata_cache is None:
        with open(_METADATA_PATH, encoding="utf-8") as f:
            _metadata_cache = json.load(f)
    return _metadata_cache


def _find_api(name: str) -> dict[str, Any] | None:
    """Find an API by name (case-insensitive)."""
    meta = _load_metadata()
    name_lower = name.lower()
    for api in meta["apis"]:
        if api["name"].lower() == name_lower:
            return api
    return None


def _format_json(data: Any, pretty: bool) -> str:
    """Format data as JSON string."""
    if pretty:
        return json.dumps(data, indent=2, ensure_ascii=False)
    return json.dumps(data, ensure_ascii=False)


def _match_path(endpoint_path: str, search_path: str) -> bool:
    """Check if search_path matches endpoint_path (partial suffix match)."""
    return endpoint_path.lower().endswith(search_path.lower()) or (
        search_path.lower() in endpoint_path.lower()
    )


def _is_tty() -> bool:
    """Check if stdout is an interactive terminal."""
    return sys.stdout.isatty()


def _use_rich(json_flag: bool) -> bool:
    """Determine whether to use rich rendering."""
    return not json_flag and _is_tty()


@app.command("list")
def list_apis(
    json_output: bool = typer.Option(False, "--json", "-j", help="Output raw JSON"),
    pretty: bool = typer.Option(False, "--pretty", "-p", help="Pretty-print JSON output"),
) -> None:
    """List all 14 Parliament APIs with endpoint and schema counts.

    Examples:
      parliament api list
      parliament api list --json
    """
    meta = _load_metadata()
    apis = [
        {
            "name": api["name"],
            "title": api["title"],
            "description": api["description"],
            "baseUrl": api["baseUrl"],
            "endpointCount": api["endpointCount"],
            "schemaCount": api["schemaCount"],
        }
        for api in meta["apis"]
    ]

    if not _use_rich(json_output):
        echo_utf8(_format_json(apis, pretty))
        return

    console = Console()
    table = Table(title="Parliament APIs", show_lines=True)
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("Title", style="bold")
    table.add_column("Endpoints", justify="right", style="green")
    table.add_column("Schemas", justify="right", style="green")
    table.add_column("Description", max_width=50)

    for api in apis:
        table.add_row(
            api["name"],
            api["title"],
            str(api["endpointCount"]),
            str(api["schemaCount"]),
            api["description"],
        )
    console.print(table)


@app.command("endpoints")
def endpoints(
    api_name: str = typer.Argument(..., help="API name (e.g., 'members', 'bills')"),
    tag: str | None = typer.Option(None, "--tag", "-t", help="Filter by tag"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output raw JSON"),
    pretty: bool = typer.Option(False, "--pretty", "-p", help="Pretty-print JSON output"),
) -> None:
    """List all endpoints for an API.

    Examples:
      parliament api endpoints members
      parliament api endpoints bills --tag Amendments
    """
    api = _find_api(api_name)
    if api is None:
        _print_api_not_found(api_name)
        raise typer.Exit(1)

    eps = api["endpoints"]
    if tag:
        tag_lower = tag.lower()
        eps = [e for e in eps if any(t.lower() == tag_lower for t in e.get("tags", []))]

    result = [
        {
            "method": e["method"],
            "path": e["path"],
            **({"summary": e["summary"]} if "summary" in e else {}),
            **({"tags": e["tags"]} if "tags" in e else {}),
        }
        for e in eps
    ]

    if not _use_rich(json_output):
        echo_utf8(_format_json(result, pretty))
        return

    console = Console()
    table = Table(title=f"{api_name} endpoints ({len(result)})")
    table.add_column("Method", style="bold yellow", no_wrap=True, width=6)
    table.add_column("Path", style="cyan")
    table.add_column("Summary")
    table.add_column("Tags", style="dim")

    for ep in result:
        table.add_row(
            ep["method"],
            ep["path"],
            ep.get("summary", ""),
            ", ".join(ep.get("tags", [])),
        )
    console.print(table)


@app.command("detail")
def detail(
    api_name: str = typer.Argument(..., help="API name (e.g., 'members', 'bills')"),
    path: str = typer.Argument(..., help="Endpoint path (supports partial matching)"),
    method: str = typer.Option("GET", "--method", "-m", help="HTTP method"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output raw JSON"),
    pretty: bool = typer.Option(False, "--pretty", "-p", help="Pretty-print JSON output"),
) -> None:
    """Show full details for a specific endpoint.

    Supports partial path matching — e.g., 'Bills/{billId}' matches '/api/v1/Bills/{billId}'.

    Examples:
      parliament api detail members "/api/Members/Search"
      parliament api detail bills "Bills/{billId}"
    """
    api = _find_api(api_name)
    if api is None:
        _print_api_not_found(api_name)
        raise typer.Exit(1)

    method_upper = method.upper()
    matches = [
        e for e in api["endpoints"] if e["method"] == method_upper and _match_path(e["path"], path)
    ]

    if not matches:
        typer.echo(f"No {method_upper} endpoint matching '{path}' in {api_name}.", err=True)
        raise typer.Exit(1)

    if not _use_rich(json_output):
        if len(matches) == 1:
            echo_utf8(_format_json(matches[0], pretty))
        else:
            echo_utf8(_format_json(matches, pretty))
        return

    console = Console()
    for ep in matches:
        console.print()
        console.print(f"[bold yellow]{ep['method']}[/] [cyan]{ep['path']}[/]")
        if ep.get("summary"):
            console.print(f"  [bold]{ep['summary']}[/]")
        if ep.get("description"):
            console.print(f"  [dim]{ep['description']}[/]")
        if ep.get("tags"):
            console.print(f"  Tags: [dim]{', '.join(ep['tags'])}[/]")
        if ep.get("operationId"):
            console.print(f"  Operation ID: [dim]{ep['operationId']}[/]")
        if ep.get("responseSchema"):
            console.print(f"  Response: [green]{ep['responseSchema']}[/]")

        params = ep.get("parameters", [])
        if params:
            console.print()
            table = Table(title="Parameters", show_lines=False, padding=(0, 1))
            table.add_column("Name", style="cyan", no_wrap=True)
            table.add_column("In", style="dim", width=5)
            table.add_column("Type", style="green")
            table.add_column("Req", width=3)
            table.add_column("Description", max_width=50)
            for p in params:
                ptype = p.get("type", "")
                if p.get("format"):
                    ptype += f" ({p['format']})"
                req = "[bold red]*[/]" if p.get("required") else ""
                desc = p.get("description", "")
                if p.get("default") is not None:
                    desc += f" [dim](default: {p['default']})[/dim]"
                if p.get("enum"):
                    desc += f" [dim]enum: {p['enum']}[/dim]"
                table.add_row(p["name"], p.get("in", ""), ptype, req, desc)
            console.print(table)


@app.command("search")
def search(
    term: str = typer.Argument(..., help="Search term"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output raw JSON"),
    pretty: bool = typer.Option(False, "--pretty", "-p", help="Pretty-print JSON output"),
) -> None:
    """Search all APIs for endpoints matching a term.

    Searches path, summary, description, and operationId across all 14 specs.

    Examples:
      parliament api search "division"
      parliament api search "committee"
    """
    meta = _load_metadata()
    term_lower = term.lower()
    results: dict[str, list[dict]] = {}

    for api in meta["apis"]:
        matches = []
        for ep in api["endpoints"]:
            searchable = " ".join(
                filter(
                    None,
                    [
                        ep.get("path", ""),
                        ep.get("summary", ""),
                        ep.get("description", ""),
                        ep.get("operationId", ""),
                    ],
                )
            ).lower()
            if term_lower in searchable:
                matches.append(
                    {
                        "method": ep["method"],
                        "path": ep["path"],
                        **({"summary": ep["summary"]} if "summary" in ep else {}),
                    }
                )
        if matches:
            results[api["name"]] = matches

    if not _use_rich(json_output):
        echo_utf8(_format_json(results, pretty))
        return

    console = Console()
    total = sum(len(eps) for eps in results.values())
    console.print(
        f"Found [bold]{total}[/] endpoints matching [cyan]'{term}'[/] across {len(results)} APIs\n"
    )

    for api_name, eps in results.items():
        table = Table(title=f"{api_name} ({len(eps)})", show_lines=False)
        table.add_column("Method", style="bold yellow", width=6)
        table.add_column("Path", style="cyan")
        table.add_column("Summary")
        for ep in eps:
            table.add_row(ep["method"], ep["path"], ep.get("summary", ""))
        console.print(table)
        console.print()


@app.command("schema")
def schema(
    api_name: str = typer.Argument(..., help="API name (e.g., 'members', 'bills')"),
    schema_name: str | None = typer.Argument(None, help="Schema name (omit to list all)"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output raw JSON"),
    pretty: bool = typer.Option(False, "--pretty", "-p", help="Pretty-print JSON output"),
) -> None:
    """Show schema definitions for an API.

    Without schema-name: lists all schemas with property counts.
    With schema-name: shows the full schema definition (case-insensitive).

    Examples:
      parliament api schema members
      parliament api schema members Member
      parliament api schema bills BillSummary
    """
    api = _find_api(api_name)
    if api is None:
        _print_api_not_found(api_name)
        raise typer.Exit(1)

    schemas = api.get("schemas", [])

    if schema_name is None:
        result = [
            {
                "name": s["name"],
                **({"type": s["type"]} if "type" in s else {}),
                "propertyCount": len(s.get("properties", [])),
                **({"enum": s["enum"]} if "enum" in s else {}),
            }
            for s in schemas
        ]

        if not _use_rich(json_output):
            echo_utf8(_format_json(result, pretty))
            return

        console = Console()
        table = Table(title=f"{api_name} schemas ({len(result)})")
        table.add_column("Name", style="cyan")
        table.add_column("Type", style="green")
        table.add_column("Properties", justify="right")
        table.add_column("Enum Values", style="dim", max_width=50)

        for s in result:
            enum_str = ", ".join(str(v) for v in s["enum"]) if "enum" in s else ""
            table.add_row(
                s["name"],
                s.get("type", ""),
                str(s["propertyCount"]),
                enum_str,
            )
        console.print(table)
        return

    name_lower = schema_name.lower()
    match = next((s for s in schemas if s["name"].lower() == name_lower), None)
    if match is None:
        typer.echo(f"Schema '{schema_name}' not found in {api_name}.", err=True)
        raise typer.Exit(1)

    if not _use_rich(json_output):
        echo_utf8(_format_json(match, pretty))
        return

    console = Console()
    console.print(f"\n[bold]{match['name']}[/]", end="")
    if match.get("type"):
        console.print(f" [dim]({match['type']})[/]", end="")
    console.print()
    if match.get("description"):
        console.print(f"  [dim]{match['description']}[/]")
    if match.get("enum"):
        console.print(f"  Enum: [green]{', '.join(str(v) for v in match['enum'])}[/]")

    props = match.get("properties", [])
    if props:
        console.print()
        table = Table(show_lines=False, padding=(0, 1))
        table.add_column("Property", style="cyan")
        table.add_column("Type", style="green")
        table.add_column("Nullable", width=4)
        table.add_column("Description", max_width=50)

        for p in props:
            ptype = p.get("type", "")
            if p.get("itemType"):
                ptype += f"<{p['itemType']}>"
            if p.get("format"):
                ptype += f" ({p['format']})"
            nullable = "[dim]?[/]" if p.get("nullable") else ""
            desc = p.get("description", "")
            if p.get("enum"):
                desc += f" [dim]enum: {p['enum']}[/dim]"
            table.add_row(p["name"], ptype, nullable, desc)
        console.print(table)


@app.command("params")
def params(
    api_name: str = typer.Argument(..., help="API name (e.g., 'members', 'bills')"),
    path: str = typer.Argument(..., help="Endpoint path (supports partial matching)"),
    method: str = typer.Option("GET", "--method", "-m", help="HTTP method"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output raw JSON"),
    pretty: bool = typer.Option(False, "--pretty", "-p", help="Pretty-print JSON output"),
) -> None:
    """Quick parameter reference for an endpoint.

    Shows parameters grouped by location (path/query) with required/optional counts.

    Examples:
      parliament api params members "/api/Members/Search"
      parliament api params bills "Amendments"
    """
    api = _find_api(api_name)
    if api is None:
        _print_api_not_found(api_name)
        raise typer.Exit(1)

    method_upper = method.upper()
    matches = [
        e for e in api["endpoints"] if e["method"] == method_upper and _match_path(e["path"], path)
    ]

    if not matches:
        typer.echo(f"No {method_upper} endpoint matching '{path}' in {api_name}.", err=True)
        raise typer.Exit(1)

    # Use first match
    endpoint = matches[0]
    all_params = endpoint.get("parameters", [])

    # Group by location
    grouped: dict[str, list[dict]] = {}
    for p in all_params:
        loc = p.get("in", "unknown")
        grouped.setdefault(loc, []).append(p)

    required_count = sum(1 for p in all_params if p.get("required"))
    optional_count = len(all_params) - required_count

    result = {
        "endpoint": f"{endpoint['method']} {endpoint['path']}",
        "totalParams": len(all_params),
        "required": required_count,
        "optional": optional_count,
        "byLocation": grouped,
    }

    if not _use_rich(json_output):
        echo_utf8(_format_json(result, pretty))
        return

    console = Console()
    console.print(f"\n[bold yellow]{endpoint['method']}[/] [cyan]{endpoint['path']}[/]")
    console.print(
        f"  {len(all_params)} parameters: "
        f"[bold red]{required_count} required[/], "
        f"[dim]{optional_count} optional[/]\n"
    )

    for loc, loc_params in grouped.items():
        table = Table(title=f"{loc} parameters", show_lines=False, padding=(0, 1))
        table.add_column("Name", style="cyan", no_wrap=True)
        table.add_column("Type", style="green")
        table.add_column("Req", width=3)
        table.add_column("Description", max_width=50)

        for p in loc_params:
            ptype = p.get("type", "")
            if p.get("format"):
                ptype += f" ({p['format']})"
            req = "[bold red]*[/]" if p.get("required") else ""
            desc = p.get("description", "")
            if p.get("default") is not None:
                desc += f" [dim](default: {p['default']})[/dim]"
            if p.get("enum"):
                desc += f" [dim]enum: {p['enum']}[/dim]"
            table.add_row(p["name"], ptype, req, desc)
        console.print(table)
        console.print()


def _print_api_not_found(name: str) -> None:
    """Print API not found error with available names."""
    meta = _load_metadata()
    available = ", ".join(api["name"] for api in meta["apis"])
    typer.echo(f"API '{name}' not found. Available: {available}", err=True)
