"""Universal search — query all Parliament data sources at once."""

from __future__ import annotations

import asyncio
import json
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any
from urllib.parse import quote

import typer

from uk_parliament_mcp.cli.formatters import OutputFormat
from uk_parliament_mcp.cli.renderers import _parse_api_response
from uk_parliament_mcp.cli.utils import (
    echo_utf8,
    experimental,
    format_output,
    run_async,
    should_render_rich,
)
from uk_parliament_mcp.config import (
    BILLS_API_BASE,
    COMMITTEES_API_BASE,
    COMMONS_VOTES_API_BASE,
    ERSKINE_MAY_API_BASE,
    HANSARD_API_BASE,
    LORDS_VOTES_API_BASE,
    MEMBERS_API_BASE,
    ORAL_QUESTIONS_API_BASE,
    STATUTORY_INSTRUMENTS_API_BASE,
    TREATIES_API_BASE,
    WRITTEN_QUESTIONS_API_BASE,
)
from uk_parliament_mcp.http_client import build_url, get_result

# Per-source timeout (seconds) to avoid one slow API blocking everything
_SOURCE_TIMEOUT = 15


# ---------------------------------------------------------------------------
# Search source registry
# ---------------------------------------------------------------------------


@dataclass
class SearchSource:
    """Maps a Parliament API search endpoint to a uniform interface."""

    name: str
    display_name: str
    build_url: Callable[[str, int], str]
    extract_items: Callable[[Any], list[Any]]
    extract_total: Callable[[Any], int | None]


def _extract_items_key(data: Any, *keys: str) -> list[Any]:
    """Extract a list from parsed data, trying each key in order."""
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for k in keys:
            if k in data and isinstance(data[k], list):
                return list(data[k])
    return []


def _extract_total_key(data: Any, key: str) -> int | None:
    """Extract a total-count integer from parsed data."""
    if isinstance(data, dict):
        val = data.get(key)
        if isinstance(val, int):
            return val
    return None


def _nested_get(data: Any, dotted_key: str) -> Any:
    """Traverse nested dicts using a dotted path like 'PagingInfo.Total'."""
    parts = dotted_key.split(".")
    current = data
    for part in parts:
        if isinstance(current, dict):
            current = current.get(part)
        else:
            return None
    return current


# ---- URL builders --------------------------------------------------------


def _members_url(query: str, take: int) -> str:
    return build_url(f"{MEMBERS_API_BASE}/Members/Search", {"Name": query, "take": take})


def _bills_url(query: str, take: int) -> str:
    return build_url(f"{BILLS_API_BASE}/Bills", {"SearchTerm": query, "Take": take})


def _committees_url(query: str, take: int) -> str:
    return build_url(f"{COMMITTEES_API_BASE}/Committees", {"SearchTerm": query, "Take": take})


def _commons_votes_url(query: str, take: int) -> str:
    return build_url(
        f"{COMMONS_VOTES_API_BASE}/divisions.json/search",
        {"queryParameters.searchTerm": query, "queryParameters.take": take},
    )


def _lords_votes_url(query: str, take: int) -> str:
    return build_url(
        f"{LORDS_VOTES_API_BASE}/Divisions/search",
        {"SearchTerm": query, "take": take},
    )


def _written_questions_url(query: str, take: int) -> str:
    return build_url(
        f"{WRITTEN_QUESTIONS_API_BASE}/writtenquestions/questions",
        {"searchTerm": query, "take": take},
    )


def _written_statements_url(query: str, take: int) -> str:
    return build_url(
        f"{WRITTEN_QUESTIONS_API_BASE}/writtenstatements/statements",
        {"searchTerm": query, "take": take},
    )


def _edms_url(query: str, take: int) -> str:
    return build_url(
        f"{ORAL_QUESTIONS_API_BASE}/EarlyDayMotions/list",
        {"parameters.searchTerm": query, "parameters.take": take},
    )


def _hansard_url(query: str, take: int, days: int = 30) -> str:
    end = date.today().isoformat()
    start = (date.today() - timedelta(days=days)).isoformat()
    return build_url(
        f"{HANSARD_API_BASE}/search.json",
        {
            "queryParameters.searchTerm": query,
            "queryParameters.startDate": start,
            "queryParameters.endDate": end,
            "queryParameters.take": take,
        },
    )


def _treaties_url(query: str, take: int) -> str:
    return build_url(f"{TREATIES_API_BASE}/Treaty", {"SearchText": query, "Take": take})


def _statutory_instruments_url(query: str, take: int) -> str:
    return build_url(
        f"{STATUTORY_INSTRUMENTS_API_BASE}/StatutoryInstrument",
        {"Name": query, "Take": take},
    )


def _erskine_may_url(query: str, take: int) -> str:
    return f"{ERSKINE_MAY_API_BASE}/Search/ParagraphSearchResults/{quote(query)}"


# ---- Item extractors -----------------------------------------------------


def _members_items(data: Any) -> list[Any]:
    """Members API: items[].value"""
    raw = _extract_items_key(data, "items")
    return [item.get("value", item) if isinstance(item, dict) else item for item in raw]


def _bills_items(data: Any) -> list[Any]:
    return _extract_items_key(data, "items")


def _committees_items(data: Any) -> list[Any]:
    return _extract_items_key(data, "items")


def _commons_votes_items(data: Any) -> list[Any]:
    return _extract_items_key(data, "items", "results")


def _lords_votes_items(data: Any) -> list[Any]:
    return _extract_items_key(data, "items", "results")


def _written_questions_items(data: Any) -> list[Any]:
    return _extract_items_key(data, "results", "items")


def _written_statements_items(data: Any) -> list[Any]:
    return _extract_items_key(data, "results", "items")


def _edms_items(data: Any) -> list[Any]:
    return _extract_items_key(data, "Response", "items", "results")


def _hansard_items(data: Any) -> list[Any]:
    return _extract_items_key(data, "Results", "results")


def _treaties_items(data: Any) -> list[Any]:
    return _extract_items_key(data, "items", "results")


def _statutory_instruments_items(data: Any) -> list[Any]:
    return _extract_items_key(data, "items", "results")


def _erskine_may_items(data: Any) -> list[Any]:
    return _extract_items_key(data, "items", "results")


# ---- Total extractors ----------------------------------------------------


def _edms_total(data: Any) -> int | None:
    val = _nested_get(data, "PagingInfo.Total")
    return int(val) if isinstance(val, (int, float)) else None


def _hansard_total(data: Any) -> int | None:
    return _extract_total_key(data, "TotalResultCount")


# ---- Registry ------------------------------------------------------------

SOURCES: list[SearchSource] = [
    SearchSource("members", "Members (MPs & Lords)", _members_url, _members_items, lambda d: _extract_total_key(d, "totalResults")),
    SearchSource("bills", "Bills", _bills_url, _bills_items, lambda d: _extract_total_key(d, "totalResults")),
    SearchSource("committees", "Committees", _committees_url, _committees_items, lambda d: _extract_total_key(d, "totalResults")),
    SearchSource("commons-votes", "Commons Divisions", _commons_votes_url, _commons_votes_items, lambda _: None),
    SearchSource("lords-votes", "Lords Divisions", _lords_votes_url, _lords_votes_items, lambda _: None),
    SearchSource("written-questions", "Written Questions", _written_questions_url, _written_questions_items, lambda d: _extract_total_key(d, "totalResults")),
    SearchSource("written-statements", "Written Statements", _written_statements_url, _written_statements_items, lambda d: _extract_total_key(d, "totalResults")),
    SearchSource("edms", "Early Day Motions", _edms_url, _edms_items, _edms_total),
    SearchSource("hansard", "Hansard", _hansard_url, _hansard_items, _hansard_total),
    SearchSource("treaties", "Treaties", _treaties_url, _treaties_items, lambda _: None),
    SearchSource("statutory-instruments", "Statutory Instruments", _statutory_instruments_url, _statutory_instruments_items, lambda _: None),
    SearchSource("erskine-may", "Erskine May", _erskine_may_url, _erskine_may_items, lambda _: None),
]

SOURCE_MAP: dict[str, SearchSource] = {s.name: s for s in SOURCES}

ALL_SOURCE_NAMES = list(SOURCE_MAP.keys())

# Scope aliases expand convenient shorthands to multiple source names
SCOPE_ALIASES: dict[str, list[str]] = {
    "votes": ["commons-votes", "lords-votes"],
    "questions": ["written-questions", "written-statements", "edms"],
    "legislation": ["bills", "statutory-instruments", "treaties"],
}


def _resolve_scope(scope: list[str] | None, exclude: list[str] | None) -> list[str]:
    """Resolve scope/exclude into final list of source names."""
    if scope:
        resolved: list[str] = []
        for name in scope:
            if name in SCOPE_ALIASES:
                resolved.extend(SCOPE_ALIASES[name])
            elif name in SOURCE_MAP:
                resolved.append(name)
            else:
                raise ValueError(f"Unknown source: '{name}'. Valid: {', '.join(ALL_SOURCE_NAMES + list(SCOPE_ALIASES.keys()))}")
        names = resolved
    else:
        names = list(ALL_SOURCE_NAMES)

    if exclude:
        for name in exclude:
            if name in SCOPE_ALIASES:
                for ex in SCOPE_ALIASES[name]:
                    if ex in names:
                        names.remove(ex)
            elif name in names:
                names.remove(name)
    return names


# ---------------------------------------------------------------------------
# Async core
# ---------------------------------------------------------------------------


async def _fetch_source(
    source: SearchSource, query: str, limit: int, days: int
) -> dict[str, Any]:
    """Fetch a single source, returning a uniform result dict."""
    try:
        # Hansard needs the days parameter
        if source.name == "hansard":
            url = source.build_url(query, limit, days)  # type: ignore[call-arg]
        else:
            url = source.build_url(query, limit)

        raw = await asyncio.wait_for(get_result(url), timeout=_SOURCE_TIMEOUT)
        data = _parse_api_response(raw)

        if data is None:
            return {
                "source": source.name,
                "display_name": source.display_name,
                "url": url,
                "items": [],
                "total": None,
                "error": "Failed to parse response",
            }

        items = source.extract_items(data)
        total = source.extract_total(data)
        # If total is None but we have items, use len as approximation
        if total is None and items:
            total = len(items)

        return {
            "source": source.name,
            "display_name": source.display_name,
            "url": url,
            "items": items[:limit],
            "total": total,
            "error": None,
        }
    except TimeoutError:
        return {
            "source": source.name,
            "display_name": source.display_name,
            "url": "",
            "items": [],
            "total": None,
            "error": "Request timed out",
        }
    except Exception as e:
        return {
            "source": source.name,
            "display_name": source.display_name,
            "url": "",
            "items": [],
            "total": None,
            "error": str(e),
        }


async def _universal_search_async(
    query: str,
    scope: list[str] | None = None,
    exclude: list[str] | None = None,
    limit: int = 5,
    days: int = 30,
) -> str:
    """Search across all (or scoped) Parliament data sources.

    Args:
        query: The search term.
        scope: Optional list of source names to include (None = all).
        exclude: Optional list of source names to exclude.
        limit: Max results per source.
        days: Hansard lookback period in days.

    Returns:
        JSON string with aggregated results.
    """
    names = _resolve_scope(scope, exclude)
    sources = [SOURCE_MAP[n] for n in names if n in SOURCE_MAP]

    tasks = [_fetch_source(s, query, limit, days) for s in sources]
    results_list = await asyncio.gather(*tasks, return_exceptions=True)

    results: dict[str, Any] = {}
    summary: dict[str, Any] = {}

    for r in results_list:
        if isinstance(r, BaseException):
            continue
        name = r["source"]
        results[name] = r
        summary[name] = {
            "total": r.get("total"),
            "returned": len(r.get("items", [])),
            "error": r.get("error"),
        }

    payload = {
        "query": query,
        "sources_queried": len(sources),
        "summary": summary,
        "results": results,
    }
    return json.dumps(payload, default=str)


# ---------------------------------------------------------------------------
# CLI command
# ---------------------------------------------------------------------------


@experimental
def search_command(
    query: str = typer.Argument(..., help="Search term to query across all Parliament sources"),
    scope: str | None = typer.Option(
        None,
        "--scope",
        "-s",
        help=(
            "Comma-separated source names to search. "
            "Aliases: votes, questions, legislation. "
            f"Sources: {', '.join(ALL_SOURCE_NAMES)}"
        ),
    ),
    exclude: str | None = typer.Option(
        None,
        "--exclude",
        "-x",
        help="Comma-separated source names to exclude",
    ),
    limit: int = typer.Option(5, "--limit", "-l", help="Max results per source"),
    days: int = typer.Option(30, "--days", help="Hansard lookback in days"),
    counts_only: bool = typer.Option(
        False, "--counts-only", "-c", help="Show summary counts only (no items)"
    ),
    pretty: bool = typer.Option(False, "--pretty", "-p", help="Pretty-print JSON output"),
    data_only: bool = typer.Option(
        True, "--data-only", "-d", help="Return data only (use --no-data-only for wrapper)"
    ),
    output_format: OutputFormat = typer.Option(  # noqa: B008
        OutputFormat.AUTO, "--format", "-f", help="Output format: json, table, auto"
    ),
    raw: bool = typer.Option(False, "--raw", help="Output full wrapper JSON"),
    fields: str | None = typer.Option(
        None, "--fields", help="Comma-separated field paths for columns"
    ),
) -> None:
    """
    Search across all Parliament data sources at once.

    Queries up to 12 APIs in parallel: members, bills, committees, votes,
    Hansard, written questions, written statements, EDMs, treaties,
    statutory instruments, and Erskine May.

    Examples:
      parliament search "NHS"
      parliament search "climate" --scope bills,votes
      parliament search "Brexit" --counts-only
      parliament search "education" --limit 10
      parliament search "NHS" --exclude erskine-may
    """
    scope_list = [s.strip() for s in scope.split(",") if s.strip()] if scope else None
    exclude_list = [s.strip() for s in exclude.split(",") if s.strip()] if exclude else None

    try:
        _resolve_scope(scope_list, exclude_list)
    except ValueError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from None

    result = run_async(_universal_search_async(query, scope_list, exclude_list, limit, days))

    if counts_only:
        parsed = json.loads(result)
        counts_payload = {
            "query": parsed["query"],
            "sources_queried": parsed["sources_queried"],
            "summary": parsed["summary"],
        }
        result = json.dumps(counts_payload, default=str)

    if should_render_rich(output_format, raw):
        from uk_parliament_mcp.cli.renderers import render_search

        render_search(result, counts_only)
    else:
        echo_utf8(format_output(result, pretty, data_only, output_format, fields, raw))
