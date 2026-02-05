"""Live CLI commands for current chamber activity and parliamentary calendar."""

from __future__ import annotations

import typer

from uk_parliament_mcp.cli.utils import format_output, run_async
from uk_parliament_mcp.config import NOW_API_BASE, WHATSON_API_BASE
from uk_parliament_mcp.http_client import build_url, get_result

app = typer.Typer(help="Live activity and parliamentary calendar")


@app.command("commons-now")
def happening_now_in_commons(
    pretty: bool = typer.Option(False, "--pretty", "-p", help="Pretty-print JSON output"),
    data_only: bool = typer.Option(False, "--data-only", "-d", help="Return data only"),
) -> None:
    """
    Get live information about what's currently happening in the House of Commons chamber.

    Use when you want real-time updates on parliamentary business, current debates,
    or voting activity.
    """
    url = f"{NOW_API_BASE}/Message/message/CommonsMain/current"
    result = run_async(get_result(url))
    typer.echo(format_output(result, pretty, data_only))


@app.command("lords-now")
def happening_now_in_lords(
    pretty: bool = typer.Option(False, "--pretty", "-p", help="Pretty-print JSON output"),
    data_only: bool = typer.Option(False, "--data-only", "-d", help="Return data only"),
) -> None:
    """
    Get live information about what's currently happening in the House of Lords chamber.

    Use when you want real-time updates on Lords business, current debates,
    or voting activity.
    """
    url = f"{NOW_API_BASE}/Message/message/LordsMain/current"
    result = run_async(get_result(url))
    typer.echo(format_output(result, pretty, data_only))


@app.command("calendar")
def search_calendar(
    house: str = typer.Argument(..., help="House name: 'Commons' or 'Lords'"),
    start_date: str = typer.Argument(..., help="Start date (YYYY-MM-DD)"),
    end_date: str = typer.Argument(..., help="End date (YYYY-MM-DD)"),
    pretty: bool = typer.Option(False, "--pretty", "-p", help="Pretty-print JSON output"),
    data_only: bool = typer.Option(False, "--data-only", "-d", help="Return data only"),
) -> None:
    """
    Search parliamentary calendar for upcoming events and business in either chamber.

    Use when you want to know what's scheduled in Parliament, upcoming debates,
    or future parliamentary business.
    """
    url = build_url(
        f"{WHATSON_API_BASE}/events/list.json",
        {
            "queryParameters.house": house,
            "queryParameters.startDate": start_date,
            "queryParameters.endDate": end_date,
        },
    )
    result = run_async(get_result(url))
    typer.echo(format_output(result, pretty, data_only))


@app.command("sessions")
def get_sessions(
    pretty: bool = typer.Option(False, "--pretty", "-p", help="Pretty-print JSON output"),
    data_only: bool = typer.Option(False, "--data-only", "-d", help="Return data only"),
) -> None:
    """
    Get list of parliamentary sessions.

    Use when you need to understand parliamentary terms, session dates,
    or the parliamentary calendar structure.
    """
    url = f"{WHATSON_API_BASE}/sessions/list.json"
    result = run_async(get_result(url))
    typer.echo(format_output(result, pretty, data_only))


@app.command("non-sitting-days")
def get_non_sitting_days(
    house: str = typer.Argument(..., help="House name: 'Commons' or 'Lords'"),
    start_date: str = typer.Argument(..., help="Start date (YYYY-MM-DD)"),
    end_date: str = typer.Argument(..., help="End date (YYYY-MM-DD)"),
    pretty: bool = typer.Option(False, "--pretty", "-p", help="Pretty-print JSON output"),
    data_only: bool = typer.Option(False, "--data-only", "-d", help="Return data only"),
) -> None:
    """
    Get periods when Parliament is not sitting (recesses, holidays).

    Use when you need to know when Parliament is on break, recess periods,
    or when no parliamentary business is scheduled.
    """
    url = build_url(
        f"{WHATSON_API_BASE}/events/nonsitting.json",
        {
            "queryParameters.house": house,
            "queryParameters.startDate": start_date,
            "queryParameters.endDate": end_date,
        },
    )
    result = run_async(get_result(url))
    typer.echo(format_output(result, pretty, data_only))


@app.command("sitting-dates")
def get_sitting_dates(
    house: str = typer.Argument(..., help="House name: 'Commons' or 'Lords'"),
    start_date: str = typer.Argument(..., help="Start date (YYYY-MM-DD)"),
    end_date: str = typer.Argument(..., help="End date (YYYY-MM-DD)"),
    pretty: bool = typer.Option(False, "--pretty", "-p", help="Pretty-print JSON output"),
    data_only: bool = typer.Option(False, "--data-only", "-d", help="Return data only"),
) -> None:
    """
    Get sitting dates for a house within a date range.

    Returns list of sitting dates. Use when you need to know when Parliament
    is actually sitting (not in recess).
    """
    url = build_url(
        f"{WHATSON_API_BASE}/proceduraldates/{house}/sittingdates.json",
        {"startDate": start_date, "endDate": end_date},
    )
    result = run_async(get_result(url))
    typer.echo(format_output(result, pretty, data_only))


@app.command("next-sitting-date")
def get_next_sitting_date(
    house: str = typer.Argument(..., help="House name: 'Commons' or 'Lords'"),
    date_to_check: str = typer.Argument(
        ...,
        help="Date to find next sitting after (YYYY-MM-DD). Use today's date to find when Parliament next sits.",
    ),
    pretty: bool = typer.Option(False, "--pretty", "-p", help="Pretty-print JSON output"),
    data_only: bool = typer.Option(False, "--data-only", "-d", help="Return data only"),
) -> None:
    """
    Get the next sitting date after a specified date.

    Use to find out when Parliament returns from recess or when the next
    sitting day is scheduled.
    """
    url = build_url(
        f"{WHATSON_API_BASE}/proceduraldates/{house}/nextsittingdate.json",
        {"dateToCheck": date_to_check},
    )
    result = run_async(get_result(url))
    typer.echo(format_output(result, pretty, data_only))


@app.command("tabling-deadline")
def get_tabling_deadline(
    house: str = typer.Argument(..., help="House name: 'Commons' or 'Lords'"),
    requested_date: str = typer.Argument(
        ..., help="Date to find tabling deadline for (YYYY-MM-DD)"
    ),
    pretty: bool = typer.Option(False, "--pretty", "-p", help="Pretty-print JSON output"),
    data_only: bool = typer.Option(False, "--data-only", "-d", help="Return data only"),
) -> None:
    """
    Get the valid tabling date for a specified date (Commons only).

    Use when you need to know the deadline for tabling questions, EDMs,
    or other parliamentary business.
    """
    url = build_url(
        f"{WHATSON_API_BASE}/proceduraldates/{house}/tablingdate.json",
        {"requestedDate": requested_date},
    )
    result = run_async(get_result(url))
    typer.echo(format_output(result, pretty, data_only))


@app.command("answer-deadline")
def get_answer_deadline(
    house: str = typer.Argument(..., help="House name: 'Commons' or 'Lords'"),
    question_type: str = typer.Argument(
        ..., help="Type of written question: 'NamedDay' or 'Ordinary'"
    ),
    tabled_date: str = typer.Argument(..., help="Date the question was tabled (YYYY-MM-DD)"),
    pretty: bool = typer.Option(False, "--pretty", "-p", help="Pretty-print JSON output"),
    data_only: bool = typer.Option(False, "--data-only", "-d", help="Return data only"),
) -> None:
    """
    Get the earliest answer date for a written question (Commons only).

    Use to determine when a Parliamentary Question is expected to be answered
    based on the question type and date tabled.
    """
    url = build_url(
        f"{WHATSON_API_BASE}/proceduraldates/{house}/answerdate.json",
        {"questionType": question_type, "tabledDate": tabled_date},
    )
    result = run_async(get_result(url))
    typer.echo(format_output(result, pretty, data_only))


@app.command("calendar-event")
def get_calendar_event(
    event_id: int = typer.Argument(..., help="The calendar event ID"),
    pretty: bool = typer.Option(False, "--pretty", "-p", help="Pretty-print JSON output"),
    data_only: bool = typer.Option(False, "--data-only", "-d", help="Return data only"),
) -> None:
    """
    Get calendar event by ID.

    Use to get full details of a specific calendar event when you already
    have its ID from another query.
    """
    url = f"{WHATSON_API_BASE}/events/cal{event_id}"
    result = run_async(get_result(url))
    typer.echo(format_output(result, pretty, data_only))
