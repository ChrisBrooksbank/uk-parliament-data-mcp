"""Live CLI commands for current chamber activity and parliamentary calendar."""

from __future__ import annotations

import typer

from uk_parliament_mcp.cli.formatters import OutputFormat
from uk_parliament_mcp.cli.renderers import render_calendar, render_chamber_now
from uk_parliament_mcp.cli.utils import (
    DataOnlyOpt,
    FieldsOpt,
    FormatOpt,
    PrettyOpt,
    RawOpt,
    echo_utf8,
    format_output,
    output_result,
    run_async,
    should_render_rich,
)
from uk_parliament_mcp.config import NOW_API_BASE, WHATSON_API_BASE
from uk_parliament_mcp.http_client import build_url, get_result

app = typer.Typer(help="Live activity and parliamentary calendar", no_args_is_help=True)


@app.command("commons-now")
def happening_now_in_commons(
    pretty: PrettyOpt = False,
    data_only: DataOnlyOpt = True,
    output_format: FormatOpt = OutputFormat.AUTO,
    raw: RawOpt = False,
    fields: FieldsOpt = None,
) -> None:
    """
    Get live information about what's currently happening in the House of Commons chamber.

    Use when you want real-time updates on parliamentary business, current debates,
    or voting activity.
    """
    url = f"{NOW_API_BASE}/Message/message/CommonsMain/current"
    result = run_async(get_result(url))
    if should_render_rich(output_format, raw):
        render_chamber_now(result, "House of Commons")
    else:
        echo_utf8(format_output(result, pretty, data_only, output_format, fields, raw))


@app.command("lords-now")
def happening_now_in_lords(
    pretty: PrettyOpt = False,
    data_only: DataOnlyOpt = True,
    output_format: FormatOpt = OutputFormat.AUTO,
    raw: RawOpt = False,
    fields: FieldsOpt = None,
) -> None:
    """
    Get live information about what's currently happening in the House of Lords chamber.

    Use when you want real-time updates on Lords business, current debates,
    or voting activity.
    """
    url = f"{NOW_API_BASE}/Message/message/LordsMain/current"
    result = run_async(get_result(url))
    if should_render_rich(output_format, raw):
        render_chamber_now(result, "House of Lords")
    else:
        echo_utf8(format_output(result, pretty, data_only, output_format, fields, raw))


@app.command("calendar")
def search_calendar(
    house: str = typer.Argument(..., help="House name: 'Commons' or 'Lords'"),
    start_date: str = typer.Argument(..., help="Start date (YYYY-MM-DD)"),
    end_date: str = typer.Argument(..., help="End date (YYYY-MM-DD)"),
    pretty: PrettyOpt = False,
    data_only: DataOnlyOpt = True,
    output_format: FormatOpt = OutputFormat.AUTO,
    raw: RawOpt = False,
    fields: FieldsOpt = None,
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
    if should_render_rich(output_format, raw):
        render_calendar(result)
    else:
        echo_utf8(format_output(result, pretty, data_only, output_format, fields, raw))


@app.command("sessions")
def get_sessions(
    pretty: PrettyOpt = False,
    data_only: DataOnlyOpt = True,
    output_format: FormatOpt = OutputFormat.AUTO,
    raw: RawOpt = False,
    fields: FieldsOpt = None,
) -> None:
    """
    Get list of parliamentary sessions.

    Use when you need to understand parliamentary terms, session dates,
    or the parliamentary calendar structure.
    """
    url = f"{WHATSON_API_BASE}/sessions/list.json"
    output_result(url, pretty, data_only, output_format, fields, raw)


@app.command("non-sitting-days")
def get_non_sitting_days(
    house: str = typer.Argument(..., help="House name: 'Commons' or 'Lords'"),
    start_date: str = typer.Argument(..., help="Start date (YYYY-MM-DD)"),
    end_date: str = typer.Argument(..., help="End date (YYYY-MM-DD)"),
    pretty: PrettyOpt = False,
    data_only: DataOnlyOpt = True,
    output_format: FormatOpt = OutputFormat.AUTO,
    raw: RawOpt = False,
    fields: FieldsOpt = None,
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
    output_result(url, pretty, data_only, output_format, fields, raw)


@app.command("sitting-dates")
def get_sitting_dates(
    house: str = typer.Argument(..., help="House name: 'Commons' or 'Lords'"),
    start_date: str = typer.Argument(..., help="Start date (YYYY-MM-DD)"),
    end_date: str = typer.Argument(..., help="End date (YYYY-MM-DD)"),
    pretty: PrettyOpt = False,
    data_only: DataOnlyOpt = True,
    output_format: FormatOpt = OutputFormat.AUTO,
    raw: RawOpt = False,
    fields: FieldsOpt = None,
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
    output_result(url, pretty, data_only, output_format, fields, raw)


@app.command("next-sitting-date")
def get_next_sitting_date(
    house: str = typer.Argument(..., help="House name: 'Commons' or 'Lords'"),
    date_to_check: str = typer.Argument(
        ...,
        help="Date to find next sitting after (YYYY-MM-DD). Use today's date to find when Parliament next sits.",
    ),
    pretty: PrettyOpt = False,
    data_only: DataOnlyOpt = True,
    output_format: FormatOpt = OutputFormat.AUTO,
    raw: RawOpt = False,
    fields: FieldsOpt = None,
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
    output_result(url, pretty, data_only, output_format, fields, raw)


@app.command("tabling-deadline")
def get_tabling_deadline(
    house: str = typer.Argument(..., help="House name: 'Commons' or 'Lords'"),
    requested_date: str = typer.Argument(
        ..., help="Date to find tabling deadline for (YYYY-MM-DD)"
    ),
    pretty: PrettyOpt = False,
    data_only: DataOnlyOpt = True,
    output_format: FormatOpt = OutputFormat.AUTO,
    raw: RawOpt = False,
    fields: FieldsOpt = None,
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
    output_result(url, pretty, data_only, output_format, fields, raw)


@app.command("answer-deadline")
def get_answer_deadline(
    house: str = typer.Argument(..., help="House name: 'Commons' or 'Lords'"),
    question_type: str = typer.Argument(
        ..., help="Type of written question: 'NamedDay' or 'Ordinary'"
    ),
    tabled_date: str = typer.Argument(..., help="Date the question was tabled (YYYY-MM-DD)"),
    pretty: PrettyOpt = False,
    data_only: DataOnlyOpt = True,
    output_format: FormatOpt = OutputFormat.AUTO,
    raw: RawOpt = False,
    fields: FieldsOpt = None,
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
    output_result(url, pretty, data_only, output_format, fields, raw)


@app.command("calendar-event")
def get_calendar_event(
    event_id: int = typer.Argument(..., help="The calendar event ID"),
    pretty: PrettyOpt = False,
    data_only: DataOnlyOpt = True,
    output_format: FormatOpt = OutputFormat.AUTO,
    raw: RawOpt = False,
    fields: FieldsOpt = None,
) -> None:
    """
    Get calendar event by ID.

    Use to get full details of a specific calendar event when you already
    have its ID from another query.
    """
    url = f"{WHATSON_API_BASE}/events/cal{event_id}"
    output_result(url, pretty, data_only, output_format, fields, raw)


@app.command("annunciator-by-date")
def get_annunciator_by_date(
    annunciator: str = typer.Argument(
        ..., help="Annunciator identifier: 'CommonsMain' or 'LordsMain'"
    ),
    date: str = typer.Argument(..., help="Date to retrieve annunciator message for (YYYY-MM-DD)"),
    pretty: PrettyOpt = False,
    data_only: DataOnlyOpt = True,
    output_format: FormatOpt = OutputFormat.AUTO,
    raw: RawOpt = False,
    fields: FieldsOpt = None,
) -> None:
    """
    Get annunciator message for a specific chamber and date.

    Use to retrieve what was displayed on the parliamentary annunciator
    board for a given date and chamber.
    """
    url = f"{NOW_API_BASE}/Message/message/{annunciator}/{date}"
    output_result(url, pretty, data_only, output_format, fields, raw)


@app.command("calendar-categories")
def get_calendar_categories(
    pretty: PrettyOpt = False,
    data_only: DataOnlyOpt = True,
    output_format: FormatOpt = OutputFormat.AUTO,
    raw: RawOpt = False,
    fields: FieldsOpt = None,
) -> None:
    """
    Get all calendar event categories.

    List all categories used to classify parliamentary calendar events.
    """
    url = f"{WHATSON_API_BASE}/categories/list.json"
    output_result(url, pretty, data_only, output_format, fields, raw)


@app.command("event-type-metadata")
def get_event_type_metadata(
    house: str | None = typer.Option(None, help="House filter: 'Commons' or 'Lords'"),
    event_type_id: int | None = typer.Option(None, help="Event type ID to filter by"),
    start_date: str | None = typer.Option(None, help="Start date filter (YYYY-MM-DD)"),
    end_date: str | None = typer.Option(None, help="End date filter (YYYY-MM-DD)"),
    category_id: int | None = typer.Option(None, help="Category ID to filter by"),
    search_term: str | None = typer.Option(None, help="Search term to filter events"),
    pretty: PrettyOpt = False,
    data_only: DataOnlyOpt = True,
    output_format: FormatOpt = OutputFormat.AUTO,
    raw: RawOpt = False,
    fields: FieldsOpt = None,
) -> None:
    """
    Get event type metadata with optional filtering.

    Retrieve metadata about parliamentary event types.
    """
    url = build_url(
        f"{WHATSON_API_BASE}/events/EventTypeMetaData.json",
        {
            "queryParameters.house": house,
            "queryParameters.eventTypeId": event_type_id,
            "queryParameters.startDate": start_date,
            "queryParameters.endDate": end_date,
            "queryParameters.categoryId": category_id,
            "queryParameters.searchTerm": search_term,
        },
    )
    output_result(url, pretty, data_only, output_format, fields, raw)


@app.command("parliamentary-diary")
def get_parliamentary_diary(
    house: str | None = typer.Option(None, help="House filter: 'Commons' or 'Lords'"),
    start_date: str | None = typer.Option(None, help="Start date filter (YYYY-MM-DD)"),
    end_date: str | None = typer.Option(None, help="End date filter (YYYY-MM-DD)"),
    date: str | None = typer.Option(None, help="Specific date filter (YYYY-MM-DD)"),
    category_id: int | None = typer.Option(None, help="Category ID to filter by"),
    search_term: str | None = typer.Option(None, help="Search term to filter events"),
    pretty: PrettyOpt = False,
    data_only: DataOnlyOpt = True,
    output_format: FormatOpt = OutputFormat.AUTO,
    raw: RawOpt = False,
    fields: FieldsOpt = None,
) -> None:
    """
    Get the parliamentary diary with upcoming business and events.

    Use to browse the full programme of parliamentary business across
    both chambers with optional date and house filtering.
    """
    url = build_url(
        f"{WHATSON_API_BASE}/events/diary.json",
        {
            "queryParameters.house": house,
            "queryParameters.startDate": start_date,
            "queryParameters.endDate": end_date,
            "queryParameters.date": date,
            "queryParameters.categoryId": category_id,
            "queryParameters.searchTerm": search_term,
        },
    )
    output_result(url, pretty, data_only, output_format, fields, raw)


@app.command("speaker-events")
def get_speaker_events(
    house: str | None = typer.Option(None, help="House filter: 'Commons' or 'Lords'"),
    start_date: str | None = typer.Option(None, help="Start date filter (YYYY-MM-DD)"),
    end_date: str | None = typer.Option(None, help="End date filter (YYYY-MM-DD)"),
    date: str | None = typer.Option(None, help="Specific date filter (YYYY-MM-DD)"),
    category_id: int | None = typer.Option(None, help="Category ID to filter by"),
    search_term: str | None = typer.Option(None, help="Search term to filter events"),
    pretty: PrettyOpt = False,
    data_only: DataOnlyOpt = True,
    output_format: FormatOpt = OutputFormat.AUTO,
    raw: RawOpt = False,
    fields: FieldsOpt = None,
) -> None:
    """
    Get parliamentary events with speaker information.

    Retrieve the speakers list for parliamentary business with optional
    date and house filtering.
    """
    url = build_url(
        f"{WHATSON_API_BASE}/events/speakers.json",
        {
            "queryParameters.house": house,
            "queryParameters.startDate": start_date,
            "queryParameters.endDate": end_date,
            "queryParameters.date": date,
            "queryParameters.categoryId": category_id,
            "queryParameters.searchTerm": search_term,
        },
    )
    output_result(url, pretty, data_only, output_format, fields, raw)


@app.command("calendar-locations")
def get_calendar_locations(
    pretty: PrettyOpt = False,
    data_only: DataOnlyOpt = True,
    output_format: FormatOpt = OutputFormat.AUTO,
    raw: RawOpt = False,
    fields: FieldsOpt = None,
) -> None:
    """
    Get all locations used for parliamentary calendar events.

    List committee rooms, chambers, and other venues.
    """
    url = f"{WHATSON_API_BASE}/locations/list.json"
    output_result(url, pretty, data_only, output_format, fields, raw)


@app.command("annulment-date")
def get_annulment_date(
    date_laid: str = typer.Argument(..., help="Date the negative SI was laid (YYYY-MM-DD)"),
    days_in_future: int = typer.Argument(
        ..., help="Number of days from date_laid when the SI will be annulled (e.g. 40)"
    ),
    is_treaty: bool | None = typer.Option(None, help="Whether the SI is a treaty (default: false)"),
    pretty: PrettyOpt = False,
    data_only: DataOnlyOpt = True,
    output_format: FormatOpt = OutputFormat.AUTO,
    raw: RawOpt = False,
    fields: FieldsOpt = None,
) -> None:
    """
    Calculate the annulment date for a negative statutory instrument.

    Use to find when a negative SI's 40-day scrutiny period expires.
    """
    url = build_url(
        f"{WHATSON_API_BASE}/proceduraldates/annulmentdate/forDate.json",
        {
            "dateLaid": date_laid,
            "daysInFuture": days_in_future,
            "isTreaty": is_treaty,
        },
    )
    output_result(url, pretty, data_only, output_format, fields, raw)


@app.command("last-sitting-date")
def get_last_sitting_date(
    house: str = typer.Argument(..., help="House name: 'Commons' or 'Lords'"),
    date_to_check: str = typer.Argument(
        ..., help="Find last sitting date before this date (YYYY-MM-DD)"
    ),
    include_weekend_sittings: bool | None = typer.Option(
        None, help="Include weekend sittings (default: false)"
    ),
    pretty: PrettyOpt = False,
    data_only: DataOnlyOpt = True,
    output_format: FormatOpt = OutputFormat.AUTO,
    raw: RawOpt = False,
    fields: FieldsOpt = None,
) -> None:
    """
    Get the last sitting date prior to a specified date.

    Use to find when Parliament last sat before a given date or period.
    """
    url = build_url(
        f"{WHATSON_API_BASE}/proceduraldates/{house}/lastsittingdate.json",
        {
            "dateToCheck": date_to_check,
            "includeWeekendSittings": include_weekend_sittings,
        },
    )
    output_result(url, pretty, data_only, output_format, fields, raw)


@app.command("session-by-id")
def get_session_by_id(
    session_id: int = typer.Argument(..., help="The unique session ID"),
    pretty: PrettyOpt = False,
    data_only: DataOnlyOpt = True,
    output_format: FormatOpt = OutputFormat.AUTO,
    raw: RawOpt = False,
    fields: FieldsOpt = None,
) -> None:
    """
    Get details of a specific parliamentary session by its ID.

    Use to look up session start/end dates and other details when you
    already have a session ID.
    """
    url = f"{WHATSON_API_BASE}/sessions/byid.json/{session_id}"
    output_result(url, pretty, data_only, output_format, fields, raw)


@app.command("session-for-date")
def get_session_for_date(
    date: str = typer.Argument(..., help="Date to find the session for (YYYY-MM-DD)"),
    pretty: PrettyOpt = False,
    data_only: DataOnlyOpt = True,
    output_format: FormatOpt = OutputFormat.AUTO,
    raw: RawOpt = False,
    fields: FieldsOpt = None,
) -> None:
    """
    Find which parliamentary session a given date falls within.

    Use to determine the current or historical session for any date.
    """
    url = f"{WHATSON_API_BASE}/sessions/fordate.json/{date}"
    output_result(url, pretty, data_only, output_format, fields, raw)


@app.command("calendar-tags")
def get_calendar_tags(
    pretty: PrettyOpt = False,
    data_only: DataOnlyOpt = True,
    output_format: FormatOpt = OutputFormat.AUTO,
    raw: RawOpt = False,
    fields: FieldsOpt = None,
) -> None:
    """
    Get all tags used to label parliamentary calendar events.

    Use to discover available tags for filtering calendar searches.
    """
    url = f"{WHATSON_API_BASE}/tags/list.json"
    output_result(url, pretty, data_only, output_format, fields, raw)


@app.command("calendar-types")
def get_calendar_types(
    pretty: PrettyOpt = False,
    data_only: DataOnlyOpt = True,
    output_format: FormatOpt = OutputFormat.AUTO,
    raw: RawOpt = False,
    fields: FieldsOpt = None,
) -> None:
    """
    Get all event types used in the parliamentary calendar.

    Use to discover available event type classifications for filtering.
    """
    url = f"{WHATSON_API_BASE}/types/list.json"
    output_result(url, pretty, data_only, output_format, fields, raw)
