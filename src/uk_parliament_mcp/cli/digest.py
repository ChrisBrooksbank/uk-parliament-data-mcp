"""Daily/weekly parliamentary digest — aggregates 9 data sources."""

from __future__ import annotations

import asyncio
import json
from datetime import date, datetime, timedelta
from typing import Any

import typer

from uk_parliament_mcp.cli.formatters import OutputFormat
from uk_parliament_mcp.cli.pagination import (
    BILLS_PAGINATION,
    COMMITTEES_PAGINATION,
    HANSARD_PAGINATION,
    LORDS_VOTES_PAGINATION,
    ORAL_QUESTIONS_PAGINATION,
    WRITTEN_STATEMENTS_PAGINATION,
    paginate_request,
)
from uk_parliament_mcp.cli.renderers import _parse_api_response
from uk_parliament_mcp.cli.utils import echo_utf8, format_output, run_async, should_render_rich
from uk_parliament_mcp.config import (
    BILLS_API_BASE,
    COMMITTEES_API_BASE,
    COMMONS_VOTES_API_BASE,
    HANSARD_API_BASE,
    LORDS_VOTES_API_BASE,
    ORAL_QUESTIONS_API_BASE,
    WRITTEN_QUESTIONS_API_BASE,
)
from uk_parliament_mcp.http_client import build_url, get_result

# Digest-specific cap: a single day rarely exceeds 100 items per section.
# Keep low to avoid 50+ sequential HTTP requests per API source.
_DIGEST_MAX_ITEMS = 100

app = typer.Typer(
    help="Daily/weekly parliamentary digest — debates, votes, bills, committees, questions, and more",
)


# ---------------------------------------------------------------------------
# Date helpers
# ---------------------------------------------------------------------------


def _today() -> str:
    """Return today's date as YYYY-MM-DD."""
    return date.today().isoformat()


def _week_range(target: str) -> tuple[str, str]:
    """Return (Monday, Friday) of the ISO week containing *target*.

    Args:
        target: Date string in YYYY-MM-DD format.

    Returns:
        Tuple of (monday, friday) as YYYY-MM-DD strings.
    """
    d = date.fromisoformat(target)
    monday = d - timedelta(days=d.weekday())
    friday = monday + timedelta(days=4)
    return monday.isoformat(), friday.isoformat()


def _calculate_dates(target: str | None, period: str) -> tuple[str, str]:
    """Calculate start/end dates from target date and period.

    Args:
        target: Optional date string. Defaults to today.
        period: "day" or "week".

    Returns:
        Tuple of (start_date, end_date) as YYYY-MM-DD strings.
    """
    target = target or _today()
    if period == "week":
        return _week_range(target)
    return target, target


# ---------------------------------------------------------------------------
# Async fetchers — each returns parsed data or an error dict
# ---------------------------------------------------------------------------


async def _fetch_hansard(start_date: str, end_date: str, house: int | None) -> dict[str, Any]:
    """Fetch Hansard debates for the date range."""
    params: dict[str, Any] = {
        "queryParameters.startDate": start_date,
        "queryParameters.endDate": end_date,
    }
    if house is not None:
        params["queryParameters.house"] = "Commons" if house == 1 else "Lords"
    url = build_url(f"{HANSARD_API_BASE}/search/debates.json", params)
    data = _parse_api_response(
        await paginate_request(url, HANSARD_PAGINATION, desired_total=_DIGEST_MAX_ITEMS)
    )
    return data if data is not None else {}


async def _fetch_commons_votes(start_date: str, end_date: str) -> list[dict[str, Any]]:
    """Fetch Commons divisions for the date range."""
    url = build_url(
        f"{COMMONS_VOTES_API_BASE}/divisions.json/search",
        {
            "queryParameters.startDate": start_date,
            "queryParameters.endDate": end_date,
        },
    )
    data = _parse_api_response(await get_result(url))
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("items", "results", "data"):
            if key in data and isinstance(data[key], list):
                return list(data[key])
    return []


async def _fetch_lords_votes(start_date: str, end_date: str) -> list[dict[str, Any]]:
    """Fetch Lords divisions for the date range."""
    url = build_url(
        f"{LORDS_VOTES_API_BASE}/Divisions/search",
        {"StartDate": start_date, "EndDate": end_date},
    )
    data = _parse_api_response(
        await paginate_request(url, LORDS_VOTES_PAGINATION, desired_total=_DIGEST_MAX_ITEMS)
    )
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("items", "results", "data"):
            if key in data and isinstance(data[key], list):
                return list(data[key])
    return []


async def _fetch_bill_detail(bill_id: str) -> dict[str, Any]:
    """Fetch a single bill's details (title, stage, etc.)."""
    url = f"{BILLS_API_BASE}/Bills/{bill_id}"
    data = _parse_api_response(await get_result(url))
    if isinstance(data, dict):
        return data
    return {}


async def _fetch_bills(start_date: str, end_date: str, house: int | None) -> dict[str, Any]:
    """Fetch bill sittings for the date range, enriched with bill details."""
    params: dict[str, Any] = {"DateFrom": start_date, "DateTo": end_date}
    if house == 1:
        params["House"] = "Commons"
    elif house == 2:
        params["House"] = "Lords"
    url = build_url(f"{BILLS_API_BASE}/Sittings", params)
    data = _parse_api_response(
        await paginate_request(url, BILLS_PAGINATION, desired_total=_DIGEST_MAX_ITEMS)
    )
    if data is None:
        return {}

    # Extract unique bill IDs from sittings
    items: list[Any] = []
    if isinstance(data, list):
        items = data
    elif isinstance(data, dict):
        for key in ("items", "results"):
            if key in data and isinstance(data[key], list):
                items = data[key]
                break

    bill_ids: set[str] = set()
    for item in items:
        if isinstance(item, dict):
            val = item.get("value", item)
            if not isinstance(val, dict):
                val = item
            bid = str(val.get("billId", item.get("billId", "")))
            if bid:
                bill_ids.add(bid)

    # Fetch bill details in parallel (cap at 20 to avoid flooding)
    bill_details: dict[str, dict[str, Any]] = {}
    if bill_ids:
        detail_tasks = {bid: _fetch_bill_detail(bid) for bid in sorted(bill_ids)[:20]}
        detail_keys = list(detail_tasks.keys())
        detail_results = await asyncio.gather(*detail_tasks.values(), return_exceptions=True)
        for bid, detail in zip(detail_keys, detail_results, strict=True):
            if isinstance(detail, dict) and not isinstance(detail, BaseException):
                bill_details[bid] = detail

    result: dict[str, Any] = data if isinstance(data, dict) else {"items": data}
    result["_bill_details"] = bill_details
    return result


async def _fetch_committees(start_date: str, end_date: str) -> dict[str, Any]:
    """Fetch committee events for the date range."""
    url = build_url(
        f"{COMMITTEES_API_BASE}/Events",
        {
            "StartDateFrom": start_date,
            "StartDateTo": end_date,
            "ExcludeCancelledEvents": True,
        },
    )
    data = _parse_api_response(
        await paginate_request(url, COMMITTEES_PAGINATION, desired_total=_DIGEST_MAX_ITEMS)
    )
    return data if data is not None else {}


async def _fetch_statements(start_date: str, end_date: str) -> dict[str, Any]:
    """Fetch written statements for the date range."""
    url = build_url(
        f"{WRITTEN_QUESTIONS_API_BASE}/writtenstatements/statements",
        {"madeWhenFrom": start_date, "madeWhenTo": end_date},
    )
    data = _parse_api_response(
        await paginate_request(url, WRITTEN_STATEMENTS_PAGINATION, desired_total=_DIGEST_MAX_ITEMS)
    )
    return data if data is not None else {}


async def _fetch_oral_qs(start_date: str, end_date: str) -> dict[str, Any]:
    """Fetch oral question times for the date range."""
    url = build_url(
        f"{ORAL_QUESTIONS_API_BASE}/oralquestiontimes/list",
        {
            "parameters.answeringDateStart": start_date,
            "parameters.answeringDateEnd": end_date,
        },
    )
    data = _parse_api_response(
        await paginate_request(url, ORAL_QUESTIONS_PAGINATION, desired_total=_DIGEST_MAX_ITEMS)
    )
    return data if data is not None else {}


async def _fetch_edms(start_date: str, end_date: str) -> dict[str, Any]:
    """Fetch Early Day Motions tabled in the date range."""
    url = build_url(
        f"{ORAL_QUESTIONS_API_BASE}/EarlyDayMotions/list",
        {
            "parameters.tabledStartDate": start_date,
            "parameters.tabledEndDate": end_date,
        },
    )
    data = _parse_api_response(
        await paginate_request(url, ORAL_QUESTIONS_PAGINATION, desired_total=_DIGEST_MAX_ITEMS)
    )
    return data if data is not None else {}


async def _fetch_written_qs(start_date: str, end_date: str) -> dict[str, Any]:
    """Fetch written questions for the date range.

    Uses a higher cap than other sections because the digest groups by
    department (not individual rows), so we need all items for accurate counts.
    A busy day can have 200+ written questions.
    """
    url = build_url(
        f"{WRITTEN_QUESTIONS_API_BASE}/writtenquestions/questions",
        {"tabledWhenFrom": start_date, "tabledWhenTo": end_date, "take": 500},
    )
    data = _parse_api_response(await get_result(url))
    return data if data is not None else {}


# ---------------------------------------------------------------------------
# Parallel aggregator
# ---------------------------------------------------------------------------


async def _fetch_digest_data(start_date: str, end_date: str, house: int | None) -> dict[str, Any]:
    """Fetch all 9 data sources in parallel.

    Args:
        start_date: Start date YYYY-MM-DD.
        end_date: End date YYYY-MM-DD.
        house: 1=Commons, 2=Lords, None=both.

    Returns:
        Dict keyed by section name with parsed data or error dicts.
    """
    task_map: dict[str, Any] = {
        "hansard": _fetch_hansard(start_date, end_date, house),
        "bills": _fetch_bills(start_date, end_date, house),
        "committees": _fetch_committees(start_date, end_date),
        "written_statements": _fetch_statements(start_date, end_date),
        "oral_questions": _fetch_oral_qs(start_date, end_date),
        "edms": _fetch_edms(start_date, end_date),
        "written_questions": _fetch_written_qs(start_date, end_date),
    }

    # Votes: filter by house
    if house is None or house == 1:
        task_map["commons_divisions"] = _fetch_commons_votes(start_date, end_date)
    if house is None or house == 2:
        task_map["lords_divisions"] = _fetch_lords_votes(start_date, end_date)

    keys = list(task_map.keys())
    gathered = await asyncio.gather(*task_map.values(), return_exceptions=True)

    results: dict[str, Any] = {}
    for key, result in zip(keys, gathered, strict=True):
        if isinstance(result, Exception):
            results[key] = {"error": str(result)}
        else:
            results[key] = result
    return results


# ---------------------------------------------------------------------------
# Main async entry point
# ---------------------------------------------------------------------------


async def _get_digest_async(target_date: str | None, period: str, house: int | None) -> str:
    """Build the digest JSON string.

    Args:
        target_date: Target date or None for today.
        period: "day" or "week".
        house: House filter (1, 2, or None).

    Returns:
        JSON string with digest data.
    """
    start_date, end_date = _calculate_dates(target_date, period)
    data = await _fetch_digest_data(start_date, end_date, house)

    house_label: str | None = None
    if house == 1:
        house_label = "Commons"
    elif house == 2:
        house_label = "Lords"

    payload: dict[str, Any] = {
        "date": target_date or _today(),
        "start_date": start_date,
        "end_date": end_date,
        "period": period,
        "house": house_label,
        **data,
    }
    return json.dumps(payload, default=str)


# ---------------------------------------------------------------------------
# CLI command
# ---------------------------------------------------------------------------


@app.callback(invoke_without_command=True)
def digest(
    target_date: str | None = typer.Option(
        None,
        "--date",
        "-d",
        help="Target date (YYYY-MM-DD). Defaults to today.",
    ),
    period: str = typer.Option(
        "day",
        "--period",
        help="Period to cover: 'day' or 'week'.",
    ),
    house: int | None = typer.Option(
        None,
        "--house",
        "-h",
        help="House filter: 1=Commons, 2=Lords. Omit for both.",
    ),
    pretty: bool = typer.Option(False, "--pretty", "-p", help="Pretty-print JSON output"),
    data_only: bool = typer.Option(
        True, "--data-only", help="Return data only (use --no-data-only for wrapper)"
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
    Daily or weekly parliamentary digest.

    Aggregates Hansard debates, divisions, bills, committee meetings,
    written statements, oral questions, EDMs, and written questions
    into a single summary.

    Examples:
      parliament digest                          # Today's digest
      parliament digest --date 2025-01-15        # Specific date
      parliament digest --period week            # This week (Mon-Fri)
      parliament digest --house 1                # Commons only
      parliament digest --format json            # JSON output
      parliament digest --pretty                 # Pretty-printed
    """
    # Validate date format
    if target_date is not None:
        try:
            datetime.strptime(target_date, "%Y-%m-%d")
        except ValueError:
            typer.echo(f"Error: Invalid date format '{target_date}'. Use YYYY-MM-DD.", err=True)
            raise typer.Exit(1) from None

    # Validate period
    if period not in ("day", "week"):
        typer.echo(f"Error: Invalid period '{period}'. Use 'day' or 'week'.", err=True)
        raise typer.Exit(1)

    # Validate house
    if house is not None and house not in (1, 2):
        typer.echo(f"Error: Invalid house '{house}'. Use 1 (Commons) or 2 (Lords).", err=True)
        raise typer.Exit(1)

    result = run_async(_get_digest_async(target_date, period, house))

    if should_render_rich(output_format, raw):
        from uk_parliament_mcp.cli.renderers import render_digest

        render_digest(result)
    else:
        echo_utf8(format_output(result, pretty, data_only, output_format, fields, raw))
