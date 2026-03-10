"""API spec explorer CLI commands.

Lets users query the 14 Parliament OpenAPI specs directly:
discover endpoints, parameters, schemas, and search across all APIs.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

import typer
from rich.console import Console
from rich.table import Table

from uk_parliament_mcp.cli.formatters import OutputFormat
from uk_parliament_mcp.cli.utils import echo_utf8
from uk_parliament_mcp.cli.utils import should_render_rich as _should_render_rich

app = typer.Typer(
    name="api",
    help="Explore Parliament API specs — endpoints, parameters, schemas.",
    no_args_is_help=True,
)


def _get_data_path(filename: str) -> Path:
    """Resolve a data file path, supporting PyInstaller frozen bundles."""
    if getattr(sys, "frozen", False):
        base = Path(sys._MEIPASS)  # type: ignore[attr-defined]
        return base / "uk_parliament_mcp" / "cli" / filename
    return Path(__file__).parent / filename


_METADATA_PATH = _get_data_path("api_metadata.json")
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
    api_entry: dict[str, Any]
    for api_entry in meta["apis"]:
        if api_entry["name"].lower() == name_lower:
            return api_entry
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


def _full_url(api: dict[str, Any], path: str) -> str:
    """Combine API baseUrl with endpoint path to form the full URL."""
    return str(api["baseUrl"]).rstrip("/") + path


@app.command("list")
def list_apis(
    output_format: OutputFormat = typer.Option(
        OutputFormat.AUTO, "--format", "-f", help="Output format: json, table, markdown, csv, auto"
    ),
    pretty: bool = typer.Option(False, "--pretty", "-p", help="Pretty-print JSON output"),
) -> None:
    """List all 14 Parliament APIs with endpoint and schema counts.

    Examples:
      parliament api list
      parliament api list --format json
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

    if not _should_render_rich(output_format, raw=False):
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
    output_format: OutputFormat = typer.Option(
        OutputFormat.AUTO, "--format", "-f", help="Output format: json, table, markdown, csv, auto"
    ),
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
            "url": _full_url(api, e["path"]),
            **({"summary": e["summary"]} if "summary" in e else {}),
            **({"tags": e["tags"]} if "tags" in e else {}),
        }
        for e in eps
    ]

    if not _should_render_rich(output_format, raw=False):
        echo_utf8(_format_json(result, pretty))
        return

    console = Console()
    table = Table(title=f"{api_name} endpoints ({len(result)})")
    table.add_column("Method", style="bold yellow", no_wrap=True, width=6)
    table.add_column("Path", style="cyan")
    table.add_column("URL", style="dim")
    table.add_column("Summary")
    table.add_column("Tags", style="dim")

    for ep in result:
        table.add_row(
            ep["method"],
            ep["path"],
            ep["url"],
            ep.get("summary", ""),
            ", ".join(ep.get("tags", [])),
        )
    console.print(table)


@app.command("detail")
def detail(
    api_name: str = typer.Argument(..., help="API name (e.g., 'members', 'bills')"),
    path: str = typer.Argument(..., help="Endpoint path (supports partial matching)"),
    method: str = typer.Option("GET", "--method", "-m", help="HTTP method"),
    output_format: OutputFormat = typer.Option(
        OutputFormat.AUTO, "--format", "-f", help="Output format: json, table, markdown, csv, auto"
    ),
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

    for ep in matches:
        ep["url"] = _full_url(api, ep["path"])

    if not _should_render_rich(output_format, raw=False):
        if len(matches) == 1:
            echo_utf8(_format_json(matches[0], pretty))
        else:
            echo_utf8(_format_json(matches, pretty))
        return

    console = Console()
    for ep in matches:
        console.print()
        console.print(f"[bold yellow]{ep['method']}[/] [cyan]{ep['path']}[/]")
        console.print(f"  URL: [dim]{ep['url']}[/]")
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
    output_format: OutputFormat = typer.Option(
        OutputFormat.AUTO, "--format", "-f", help="Output format: json, table, markdown, csv, auto"
    ),
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
    results: dict[str, list[dict[str, Any]]] = {}

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
                        "url": _full_url(api, ep["path"]),
                        **({"summary": ep["summary"]} if "summary" in ep else {}),
                    }
                )
        if matches:
            results[api["name"]] = matches

    if not _should_render_rich(output_format, raw=False):
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
        table.add_column("URL", style="dim")
        table.add_column("Summary")
        for ep in eps:
            table.add_row(ep["method"], ep["path"], ep["url"], ep.get("summary", ""))
        console.print(table)
        console.print()


@app.command("schema")
def schema(
    api_name: str = typer.Argument(..., help="API name (e.g., 'members', 'bills')"),
    schema_name: str | None = typer.Argument(None, help="Schema name (omit to list all)"),
    output_format: OutputFormat = typer.Option(
        OutputFormat.AUTO, "--format", "-f", help="Output format: json, table, markdown, csv, auto"
    ),
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

        if not _should_render_rich(output_format, raw=False):
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

    if not _should_render_rich(output_format, raw=False):
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
    output_format: OutputFormat = typer.Option(
        OutputFormat.AUTO, "--format", "-f", help="Output format: json, table, markdown, csv, auto"
    ),
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
    grouped: dict[str, list[dict[str, Any]]] = {}
    for p in all_params:
        loc = p.get("in", "unknown")
        grouped.setdefault(loc, []).append(p)

    required_count = sum(1 for p in all_params if p.get("required"))
    optional_count = len(all_params) - required_count

    url = _full_url(api, endpoint["path"])

    result = {
        "endpoint": f"{endpoint['method']} {endpoint['path']}",
        "url": url,
        "totalParams": len(all_params),
        "required": required_count,
        "optional": optional_count,
        "byLocation": grouped,
    }

    if not _should_render_rich(output_format, raw=False):
        echo_utf8(_format_json(result, pretty))
        return

    console = Console()
    console.print(f"\n[bold yellow]{endpoint['method']}[/] [cyan]{endpoint['path']}[/]")
    console.print(f"  URL: [dim]{url}[/]")
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


# ── Explore helpers ──────────────────────────────────────────────────

_API_CLI_GROUP: dict[str, str] = {
    "members": "members",
    "bills": "bills",
    "committees": "committees",
    "hansard": "hansard",
    "commonsvotes": "votes",
    "lordsvotes": "votes",
    "interests": "interests",
    "parliamentnow": "live",
    "whatson": "live",
    "statutoryinstruments": "legislation",
    "treaties": "legislation",
    "erskinemay": "procedures",
    "oralquestions": "questions",
    "writtenquestions": "questions",
}


def _parse_parliament_url(
    url: str,
) -> tuple[dict[str, Any], str, dict[str, list[str]]] | None:
    """Parse a URL and match it to a known Parliament API.

    Returns (api_dict, relative_path, query_params) or None.
    """
    parsed = urlparse(url)
    hostname = parsed.hostname or ""
    meta = _load_metadata()

    for api in meta["apis"]:
        base_parsed = urlparse(api["baseUrl"])
        if hostname == base_parsed.hostname:
            query_params = parse_qs(parsed.query)
            return api, parsed.path, query_params

    return None


def _match_url_to_endpoint(
    api: dict[str, Any], path: str
) -> tuple[dict[str, Any], dict[str, str]] | None:
    """Match a URL path against endpoint templates using regex.

    Returns (endpoint_dict, extracted_path_params) or None.
    """
    for ep in api["endpoints"]:
        template = ep["path"]
        # Convert template params like {id} to named regex groups
        regex = re.sub(r"\{([^}]+)\}", r"(?P<\1>[^/]+)", template)
        match = re.fullmatch(regex, path)
        if match:
            return ep, match.groupdict()

    # Fall back to substring matching
    for ep in api["endpoints"]:
        if _match_path(ep["path"], path):
            return ep, {}

    return None


def _find_related_endpoints(
    api: dict[str, Any], matched_endpoint: dict[str, Any], limit: int = 10
) -> list[dict[str, Any]]:
    """Find other endpoints sharing tags with the matched endpoint."""
    matched_tags = set(matched_endpoint.get("tags", []))
    if not matched_tags:
        return []

    matched_path = matched_endpoint["path"]
    matched_method = matched_endpoint["method"]
    related = []
    for ep in api["endpoints"]:
        if ep["path"] == matched_path and ep["method"] == matched_method:
            continue
        ep_tags = set(ep.get("tags", []))
        if ep_tags & matched_tags:
            related.append(
                {
                    "method": ep["method"],
                    "path": ep["path"],
                    **({"summary": ep["summary"]} if "summary" in ep else {}),
                }
            )
            if len(related) >= limit:
                break
    return related


@app.command("explore")
def explore(
    url: str = typer.Argument(..., help="A Parliament API URL to explore"),
    call: bool = typer.Option(
        False, "--call", "-c", help="Also call the URL and show the response"
    ),
    output_format: OutputFormat = typer.Option(
        OutputFormat.AUTO, "--format", "-f", help="Output format: json, table, markdown, csv, auto"
    ),
    pretty: bool = typer.Option(False, "--pretty", "-p", help="Pretty-print JSON output"),
) -> None:
    """Explore a Parliament API URL — identify the API, endpoint, and parameters.

    Parses a pasted URL and shows what API it belongs to, which endpoint
    template it matches, extracted path/query parameters, the matching CLI
    group, and related endpoints.

    Examples:
      parliament api explore "https://members-api.parliament.uk/api/Members/4514"
      parliament api explore "https://bills-api.parliament.uk/api/v1/Bills?SearchTerm=Online+Safety" --pretty
      parliament api explore "https://members-api.parliament.uk/api/Members/4514" --call
    """
    parsed = _parse_parliament_url(url)
    if parsed is None:
        meta = _load_metadata()
        domains = [urlparse(a["baseUrl"]).hostname for a in meta["apis"]]
        typer.echo(
            f"URL does not match any known Parliament API domain.\n"
            f"Supported domains: {', '.join(d for d in domains if d)}",
            err=True,
        )
        raise typer.Exit(1)

    api, rel_path, query_params = parsed
    # Flatten single-value query params
    flat_query: dict[str, str | list[str]] = {
        k: v[0] if len(v) == 1 else v for k, v in query_params.items()
    }

    result: dict[str, Any] = {
        "url": url,
        "api": {
            "name": api["name"],
            "title": api["title"],
            "description": api["description"],
        },
    }

    endpoint_match = _match_url_to_endpoint(api, rel_path)
    cli_group = _API_CLI_GROUP.get(api["name"])
    related: list[dict[str, Any]] = []

    if endpoint_match:
        ep, extracted = endpoint_match
        result["endpoint"] = {
            "method": ep["method"],
            "path": ep["path"],
            **({"summary": ep["summary"]} if "summary" in ep else {}),
            **({"parameters": ep["parameters"]} if ep.get("parameters") else {}),
            **({"responseSchema": ep["responseSchema"]} if "responseSchema" in ep else {}),
        }
        result["extractedParams"] = extracted
        related = _find_related_endpoints(api, ep)
    else:
        result["endpoint"] = None
        result["extractedParams"] = {}

    result["queryParams"] = flat_query
    if cli_group:
        result["cliGroup"] = cli_group
        result["cliHint"] = f"parliament {cli_group} --help"
    result["related"] = related

    if call:
        from uk_parliament_mcp.cli.utils import run_async
        from uk_parliament_mcp.http_client import get_result

        try:
            raw_response = run_async(get_result(url))
            result["response"] = json.loads(raw_response)
        except Exception as exc:
            result["response"] = {"error": str(exc)}

    if not _should_render_rich(output_format, raw=False):
        echo_utf8(_format_json(result, pretty))
        return

    # Rich terminal output
    console = Console()
    console.print()
    console.print(f"[bold]API:[/] [cyan]{api['title']}[/] ({api['name']})")
    console.print(f"  [dim]{api['description']}[/]")
    console.print(f"  Base: [dim]{api['baseUrl']}[/]")

    if endpoint_match:
        ep, extracted = endpoint_match
        console.print()
        console.print(f"[bold]Endpoint:[/] [bold yellow]{ep['method']}[/] [cyan]{ep['path']}[/]")
        if ep.get("summary"):
            console.print(f"  [bold]{ep['summary']}[/]")
        if ep.get("responseSchema"):
            console.print(f"  Response: [green]{ep['responseSchema']}[/]")

        if extracted:
            console.print()
            table = Table(title="Extracted Path Parameters", show_lines=False, padding=(0, 1))
            table.add_column("Parameter", style="cyan")
            table.add_column("Value", style="bold green")
            for k, v in extracted.items():
                table.add_row(k, v)
            console.print(table)

        if flat_query:
            console.print()
            table = Table(title="Query Parameters", show_lines=False, padding=(0, 1))
            table.add_column("Parameter", style="cyan")
            table.add_column("Value", style="green")
            for k, qv in flat_query.items():
                table.add_row(k, str(qv))
            console.print(table)

        params = ep.get("parameters", [])
        if params:
            console.print()
            table = Table(title="Endpoint Parameters", show_lines=False, padding=(0, 1))
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
                table.add_row(p["name"], p.get("in", ""), ptype, req, desc)
            console.print(table)
    else:
        console.print()
        console.print("[yellow]No matching endpoint template found for this path.[/]")
        console.print(
            f"  Try: [cyan]parliament api endpoints {api['name']}[/] to browse all endpoints"
        )

    if cli_group:
        console.print()
        console.print(f"[bold]CLI group:[/] [cyan]parliament {cli_group}[/]")
        console.print(f"  Run [cyan]parliament {cli_group} --help[/] for available commands")

    if related:
        console.print()
        table = Table(title="Related Endpoints", show_lines=False)
        table.add_column("Method", style="bold yellow", width=6)
        table.add_column("Path", style="cyan")
        table.add_column("Summary")
        for ep in related:
            table.add_row(ep["method"], ep["path"], ep.get("summary", ""))
        console.print(table)

    if call and "response" in result:
        console.print()
        if "error" in result["response"]:
            console.print(f"[bold red]Call error:[/] {result['response']['error']}")
        else:
            console.print("[bold]Response:[/]")
            console.print(json.dumps(result["response"], indent=2, ensure_ascii=False))


# Register the interactive "try" command from its own module
from uk_parliament_mcp.cli.try_it import try_endpoint  # noqa: E402

app.command("try")(try_endpoint)
