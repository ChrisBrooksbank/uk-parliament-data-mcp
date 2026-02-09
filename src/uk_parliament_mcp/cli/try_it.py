"""Interactive 'Try It' mode for exploring Parliament APIs.

Provides a guided, interactive flow: browse APIs, select endpoints,
fill in parameters, call the API, and view results — all in-terminal.
"""

from __future__ import annotations

import json
from typing import Any
from urllib.parse import quote, urlencode

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import IntPrompt, Prompt
from rich.table import Table

from uk_parliament_mcp.cli.api import (
    _find_api,
    _find_related_endpoints,
    _full_url,
    _load_metadata,
)
from uk_parliament_mcp.cli.formatters import CLIFormatter, OutputFormat
from uk_parliament_mcp.cli.utils import run_async
from uk_parliament_mcp.http_client import get_result


def _select_api(console: Console, metadata: dict[str, Any]) -> dict[str, Any]:
    """Show numbered API list and prompt the user to pick one."""
    apis: list[dict[str, Any]] = metadata["apis"]
    console.print()
    table = Table(title="Select an API", show_lines=False, padding=(0, 1))
    table.add_column("#", style="bold", justify="right", width=4)
    table.add_column("Name", style="cyan")
    table.add_column("Endpoints", justify="right", style="green")
    table.add_column("Description", max_width=50)

    for i, api in enumerate(apis, 1):
        table.add_row(str(i), api["name"], str(api["endpointCount"]), api["description"])
    console.print(table)

    choice = IntPrompt.ask(
        f"\n  API number [1-{len(apis)}]",
        console=console,
    )
    if choice < 1 or choice > len(apis):
        console.print("[red]Invalid selection.[/]")
        raise typer.Exit(1)
    return apis[choice - 1]


def _select_endpoint(
    console: Console,
    api: dict[str, Any],
    search_term: str | None = None,
) -> dict[str, Any]:
    """Show numbered endpoint list and prompt the user to pick one."""
    endpoints: list[dict[str, Any]] = api["endpoints"]
    if search_term:
        term_lower = search_term.lower()
        endpoints = [
            ep
            for ep in endpoints
            if term_lower in ep.get("path", "").lower()
            or term_lower in ep.get("summary", "").lower()
            or term_lower in ep.get("operationId", "").lower()
        ]
        if not endpoints:
            console.print(f"[yellow]No endpoints matching '{search_term}'.[/]")
            endpoints = api["endpoints"]

    console.print()
    console.print(f"[bold]{api['name']}[/] — {len(endpoints)} endpoints (enter 's' to search)")

    table = Table(show_lines=False, padding=(0, 1))
    table.add_column("#", style="bold", justify="right", width=4)
    table.add_column("Method", style="bold yellow", width=6)
    table.add_column("Path", style="cyan")
    table.add_column("Summary", max_width=50)

    for i, ep in enumerate(endpoints, 1):
        table.add_row(str(i), ep["method"], ep["path"], ep.get("summary", ""))
    console.print(table)

    answer = Prompt.ask(
        f"\n  Endpoint number [1-{len(endpoints)}] or 's' to search",
        console=console,
    )
    if answer.lower() == "s":
        term = Prompt.ask("  Search term", console=console)
        return _select_endpoint(console, api, term)

    try:
        idx = int(answer)
    except ValueError:
        console.print("[red]Invalid selection.[/]")
        raise typer.Exit(1) from None

    if idx < 1 or idx > len(endpoints):
        console.print("[red]Invalid selection.[/]")
        raise typer.Exit(1)
    return endpoints[idx - 1]


def _prompt_for_params(
    console: Console,
    endpoint: dict[str, Any],
    previous: dict[str, str] | None = None,
) -> tuple[dict[str, str], dict[str, str]]:
    """Prompt the user for endpoint parameters.

    Returns (path_params, query_params).
    When *previous* is supplied, its values are used as defaults (for Modify mode).
    """
    params = endpoint.get("parameters", [])
    if not params:
        return {}, {}

    path_params: dict[str, str] = {}
    query_params: dict[str, str] = {}

    console.print()
    console.print("[bold]Parameters[/] (Enter to skip optional, Ctrl+C to quit):")

    for p in params:
        name = p["name"]
        ptype = p.get("type", "string")
        required = p.get("required", False)
        location = p.get("in", "query")
        default_val = p.get("default")
        description = p.get("description", "")
        enum_values = p.get("enum")

        # Build prompt label
        label = f"  {name}"
        type_hint_parts: list[str] = []
        if ptype and ptype not in ("string",):
            type_hint_parts.append(ptype)
        if p.get("format"):
            type_hint_parts.append(p["format"])
        if type_hint_parts:
            label += f" ({', '.join(type_hint_parts)})"
        if description:
            # Truncate long descriptions
            short_desc = description[:60] + "..." if len(description) > 60 else description
            label += f" — {short_desc}"

        # Determine default for prompt
        prompt_default: str | None = None
        if previous and name in previous:
            prompt_default = previous[name]
        elif default_val is not None:
            prompt_default = str(default_val)

        # Prompt based on type
        if ptype == "boolean":
            choices = ["true", "false"]
            value = Prompt.ask(
                label,
                choices=choices,
                default=prompt_default or "",
                console=console,
                show_choices=True,
            )
        elif enum_values:
            choices = [str(v) for v in enum_values]
            value = Prompt.ask(
                label,
                choices=choices,
                default=prompt_default or "",
                console=console,
                show_choices=True,
            )
        elif required:
            if prompt_default:
                value = Prompt.ask(label, default=prompt_default, console=console)
            else:
                value = Prompt.ask(label, console=console)
        else:
            value = Prompt.ask(label, default=prompt_default or "", console=console)

        if value:
            if location == "path":
                path_params[name] = value
            else:
                query_params[name] = value

    return path_params, query_params


def _build_api_url(
    api: dict[str, Any],
    endpoint: dict[str, Any],
    path_params: dict[str, str],
    query_params: dict[str, str],
) -> str:
    """Build the full URL from API base, endpoint template, and params."""
    path = endpoint["path"]
    for param_name, param_value in path_params.items():
        path = path.replace(f"{{{param_name}}}", quote(str(param_value), safe=""))

    url = _full_url(api, path)

    if query_params:
        url += "?" + urlencode(query_params)

    return url


def _call_and_display(console: Console, url: str) -> dict[str, Any] | None:
    """Call the URL and display results. Returns the parsed response."""
    console.print()
    console.print(f"  Calling: [dim]{url}[/]")
    console.print()

    try:
        raw = run_async(get_result(url))
        parsed: dict[str, Any] | None = json.loads(raw)
    except Exception as exc:
        console.print(Panel(f"[bold red]Error:[/] {exc}", title="API Error"))
        return None

    # Check for error in response
    if isinstance(parsed, dict) and "error" in parsed:
        console.print(
            Panel(
                f"[bold red]{parsed['error']}[/]\nStatus: {parsed.get('statusCode', 'unknown')}",
                title="API Error",
            )
        )
        return parsed

    # Try to render as a table, fall back to pretty JSON
    data = parsed.get("data", parsed) if isinstance(parsed, dict) else parsed
    formatter = CLIFormatter(OutputFormat.TABLE, pretty=False, data_only=False)
    table_output = formatter.format_output(json.dumps(data))

    if table_output.startswith("(No data"):
        console.print("[yellow]No results returned.[/]")
        console.print()
        console.print("[bold]Raw response:[/]")
        console.print(json.dumps(data, indent=2, ensure_ascii=False)[:2000])
    else:
        console.print(table_output)

    return parsed


def _action_menu(console: Console) -> str:
    """Show the post-result action menu and return the user's choice."""
    console.print()
    console.print(
        "  [bold][T][/]ry again  "
        "[bold][M][/]odify params  "
        "[bold][R][/]elated endpoints  "
        "[bold][N][/]ew endpoint  "
        "[bold][Q][/]uit"
    )
    choice = Prompt.ask(
        "  Action",
        choices=["t", "m", "r", "n", "q"],
        default="q",
        console=console,
    )
    return choice.lower()


def _show_related(
    console: Console,
    api: dict[str, Any],
    endpoint: dict[str, Any],
) -> dict[str, Any] | None:
    """Show related endpoints and let the user pick one."""
    related = _find_related_endpoints(api, endpoint)
    if not related:
        console.print("[yellow]No related endpoints found.[/]")
        return None

    console.print()
    table = Table(title="Related Endpoints", show_lines=False, padding=(0, 1))
    table.add_column("#", style="bold", justify="right", width=4)
    table.add_column("Method", style="bold yellow", width=6)
    table.add_column("Path", style="cyan")
    table.add_column("Summary", max_width=50)

    for i, ep in enumerate(related, 1):
        table.add_row(str(i), ep["method"], ep["path"], ep.get("summary", ""))
    console.print(table)

    answer = Prompt.ask(
        f"  Select [1-{len(related)}] or Enter to go back",
        default="",
        console=console,
    )
    if not answer:
        return None

    try:
        idx = int(answer)
    except ValueError:
        return None

    if idx < 1 or idx > len(related):
        return None

    # Find the full endpoint object from the api
    picked = related[idx - 1]
    all_eps: list[dict[str, Any]] = api["endpoints"]
    for candidate in all_eps:
        if candidate["method"] == picked["method"] and candidate["path"] == picked["path"]:
            return candidate
    return None


def _find_endpoint_by_path(api: dict[str, Any], path: str) -> dict[str, Any] | None:
    """Find an endpoint by path (partial match)."""
    path_lower = path.lower()
    all_eps: list[dict[str, Any]] = api["endpoints"]
    for ep in all_eps:
        if path_lower in ep["path"].lower():
            return ep
    return None


def try_endpoint(
    api_name: str | None = typer.Argument(None, help="API name to jump to (e.g., 'members')"),
    path: str | None = typer.Argument(None, help="Endpoint path to jump to (partial match)"),
) -> None:
    """Interactively try Parliament API endpoints.

    Browse APIs, fill in parameters, call the API, and see results.

    Examples:
      parliament api try
      parliament api try members
      parliament api try members "Members/Search"
    """
    console = Console()
    metadata = _load_metadata()

    # Step 1: Select API (or use argument)
    if api_name:
        api = _find_api(api_name)
        if api is None:
            available = ", ".join(a["name"] for a in metadata["apis"])
            console.print(f"[red]API '{api_name}' not found.[/] Available: {available}")
            raise typer.Exit(1)
    else:
        api = _select_api(console, metadata)

    # Step 2: Select endpoint (or use argument)
    if path:
        endpoint = _find_endpoint_by_path(api, path)
        if endpoint is None:
            console.print(f"[red]No endpoint matching '{path}' in {api['name']}.[/]")
            raise typer.Exit(1)
    else:
        endpoint = _select_endpoint(console, api)

    # Interactive loop
    previous_params: dict[str, str] | None = None

    while True:
        # Show endpoint header
        console.print()
        console.print(f"[bold]━━━ {endpoint['method']} {endpoint['path']} ━━━[/]")
        if endpoint.get("summary"):
            console.print(f"  [dim]{endpoint['summary']}[/]")

        # Step 3: Prompt for params
        try:
            path_params, query_params = _prompt_for_params(console, endpoint, previous_params)
        except KeyboardInterrupt:
            console.print("\n[dim]Cancelled.[/]")
            raise typer.Exit(0) from None

        # Merge all params for Modify mode
        all_params = {**path_params, **query_params}

        # Step 4: Build URL and call
        url = _build_api_url(api, endpoint, path_params, query_params)
        _call_and_display(console, url)

        # Step 5: Action menu
        action = _action_menu(console)

        if action == "q":
            break
        elif action == "t":
            # Try again — re-prompt all params (no defaults from previous)
            previous_params = None
            continue
        elif action == "m":
            # Modify — use previous values as defaults
            previous_params = all_params
            continue
        elif action == "r":
            # Related endpoints
            picked = _show_related(console, api, endpoint)
            if picked:
                endpoint = picked
                previous_params = None
            continue
        elif action == "n":
            # New endpoint selection (same API)
            endpoint = _select_endpoint(console, api)
            previous_params = None
            continue
