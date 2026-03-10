"""WhatsOn API tools for parliamentary calendar and sessions."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from uk_parliament_mcp.config import WHATSON_API_BASE
from uk_parliament_mcp.http_client import build_url, get_result


def register_tools(mcp: FastMCP) -> None:
    """Register whatson tools with the MCP server."""

    @mcp.tool()
    async def search_calendar(
        house: str,
        start_date: str,
        end_date: str,
    ) -> str:
        """Search parliamentary calendar for upcoming events and business in either chamber. Use when you want to know what's scheduled in Parliament, upcoming debates, or future parliamentary business. House: Commons/Lords.

        Args:
            house: House name: 'Commons' or 'Lords'.
            start_date: Start date in YYYY-MM-DD format.
            end_date: End date in YYYY-MM-DD format.

        Returns:
            Parliamentary calendar events in the date range.
        """
        url = build_url(
            f"{WHATSON_API_BASE}/events/list.json",
            {
                "queryParameters.house": house,
                "queryParameters.startDate": start_date,
                "queryParameters.endDate": end_date,
            },
        )
        return await get_result(url)

    @mcp.tool()
    async def get_sessions() -> str:
        """Get list of parliamentary sessions. Use when you need to understand parliamentary terms, session dates, or the parliamentary calendar structure.

        Returns:
            List of parliamentary sessions.
        """
        url = f"{WHATSON_API_BASE}/sessions/list.json"
        return await get_result(url)

    @mcp.tool()
    async def get_non_sitting_days(
        house: str,
        start_date: str,
        end_date: str,
    ) -> str:
        """Get periods when Parliament is not sitting (recesses, holidays). Use when you need to know when Parliament is on break, recess periods, or when no parliamentary business is scheduled.

        Args:
            house: House name: 'Commons' or 'Lords'.
            start_date: Start date in YYYY-MM-DD format.
            end_date: End date in YYYY-MM-DD format.

        Returns:
            Non-sitting days in the date range.
        """
        url = build_url(
            f"{WHATSON_API_BASE}/events/nonsitting.json",
            {
                "queryParameters.house": house,
                "queryParameters.startDate": start_date,
                "queryParameters.endDate": end_date,
            },
        )
        return await get_result(url)

    @mcp.tool()
    async def get_sitting_dates(
        house: str,
        start_date: str,
        end_date: str,
    ) -> str:
        """Get sitting dates | recess, sitting days, parliamentary calendar, when sitting |
        Get sitting dates for a house within a date range |
        Returns list of sitting dates

        Args:
            house: House name: 'Commons' or 'Lords'.
            start_date: Start date (YYYY-MM-DD).
            end_date: End date (YYYY-MM-DD).

        Returns:
            List of sitting dates for the specified house.
        """
        url = build_url(
            f"{WHATSON_API_BASE}/proceduraldates/{house}/sittingdates.json",
            {"startDate": start_date, "endDate": end_date},
        )
        return await get_result(url)

    @mcp.tool()
    async def get_next_sitting_date(house: str, date_to_check: str) -> str:
        """Get next sitting | parliament returns, next sitting day, when back |
        Get the next sitting date after a specified date |
        Returns next sitting date

        Args:
            house: House name: 'Commons' or 'Lords'.
            date_to_check: Date to find next sitting after (YYYY-MM-DD). Use today's date to find when Parliament next sits.

        Returns:
            Next sitting date for the specified house.
        """
        url = build_url(
            f"{WHATSON_API_BASE}/proceduraldates/{house}/nextsittingdate.json",
            {"dateToCheck": date_to_check},
        )
        return await get_result(url)

    @mcp.tool()
    async def get_tabling_deadline(house: str, requested_date: str) -> str:
        """Get tabling deadline | table questions, submission deadline, EDM deadline |
        Get the valid tabling date for a specified date (Commons only) |
        Returns tabling deadline date

        Args:
            house: House name: 'Commons' or 'Lords'.
            requested_date: Date to find tabling deadline for (YYYY-MM-DD).

        Returns:
            Tabling deadline date for the specified house.
        """
        url = build_url(
            f"{WHATSON_API_BASE}/proceduraldates/{house}/tablingdate.json",
            {"requestedDate": requested_date},
        )
        return await get_result(url)

    @mcp.tool()
    async def get_answer_deadline(
        house: str,
        question_type: str,
        tabled_date: str,
    ) -> str:
        """Get answer deadline | PQ answer date, response deadline, when answers due |
        Get the earliest answer date for a written question (Commons only) |
        Returns answer deadline date

        Args:
            house: House name: 'Commons' or 'Lords'.
            question_type: Type of written question: 'NamedDay' or 'Ordinary'.
            tabled_date: Date the question was tabled (YYYY-MM-DD).

        Returns:
            Answer deadline date for the question.
        """
        url = build_url(
            f"{WHATSON_API_BASE}/proceduraldates/{house}/answerdate.json",
            {"questionType": question_type, "tabledDate": tabled_date},
        )
        return await get_result(url)

    @mcp.tool()
    async def get_calendar_event(event_id: int) -> str:
        """Get calendar event by ID | specific event, event details | Use to get full details of a specific calendar event | Returns event details

        Args:
            event_id: The calendar event ID.

        Returns:
            Full details of the calendar event.
        """
        url = f"{WHATSON_API_BASE}/events/cal{event_id}"
        return await get_result(url)

    @mcp.tool()
    async def get_calendar_categories() -> str:
        """Get calendar event categories | categories, event types, calendar taxonomy | List all categories used to classify parliamentary calendar events | Returns list of categories

        Returns:
            List of calendar event categories.
        """
        url = f"{WHATSON_API_BASE}/categories/list.json"
        return await get_result(url)

    @mcp.tool()
    async def get_event_type_metadata(
        house: str | None = None,
        event_type_id: int | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        category_id: int | None = None,
        search_term: str | None = None,
    ) -> str:
        """Get event type metadata | event types, calendar metadata, event classification | Retrieve metadata about parliamentary event types with optional filtering | Returns event type metadata

        Args:
            house: Optional house filter: 'Commons' or 'Lords'.
            event_type_id: Optional event type ID to filter by.
            start_date: Optional start date filter (YYYY-MM-DD).
            end_date: Optional end date filter (YYYY-MM-DD).
            category_id: Optional category ID to filter by.
            search_term: Optional search term to filter events.

        Returns:
            Event type metadata matching the filter criteria.
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
        return await get_result(url)

    @mcp.tool()
    async def get_parliamentary_diary(
        house: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        date: str | None = None,
        category_id: int | None = None,
        search_term: str | None = None,
    ) -> str:
        """Get parliamentary diary | diary, schedule, events, business programme | Retrieve the parliamentary diary with upcoming business and events | Returns diary events

        Args:
            house: Optional house filter: 'Commons' or 'Lords'.
            start_date: Optional start date filter (YYYY-MM-DD).
            end_date: Optional end date filter (YYYY-MM-DD).
            date: Optional specific date filter (YYYY-MM-DD).
            category_id: Optional category ID to filter by.
            search_term: Optional search term to filter events.

        Returns:
            Parliamentary diary events matching the filter criteria.
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
        return await get_result(url)

    @mcp.tool()
    async def get_speaker_events(
        house: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        date: str | None = None,
        category_id: int | None = None,
        search_term: str | None = None,
    ) -> str:
        """Get speaker events | speakers, order paper, business items, speakers list | Retrieve parliamentary events with speaker information | Returns speaker event details

        Args:
            house: Optional house filter: 'Commons' or 'Lords'.
            start_date: Optional start date filter (YYYY-MM-DD).
            end_date: Optional end date filter (YYYY-MM-DD).
            date: Optional specific date filter (YYYY-MM-DD).
            category_id: Optional category ID to filter by.
            search_term: Optional search term to filter events.

        Returns:
            Parliamentary events with speaker information matching the filter criteria.
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
        return await get_result(url)

    @mcp.tool()
    async def get_calendar_locations() -> str:
        """Get calendar locations | venues, committee rooms, locations, where | List all locations used for parliamentary calendar events | Returns list of locations

        Returns:
            List of parliamentary calendar locations.
        """
        url = f"{WHATSON_API_BASE}/locations/list.json"
        return await get_result(url)

    @mcp.tool()
    async def get_annulment_date(
        date_laid: str,
        days_in_future: int,
        is_treaty: bool | None = None,
    ) -> str:
        """Get annulment date | SI annulment, negative SI, scrutiny period, 40 days | Calculate the annulment date for a negative statutory instrument | Returns annulment date

        Args:
            date_laid: Date the negative SI was laid (YYYY-MM-DD).
            days_in_future: Number of days from date_laid when the SI will be annulled (e.g. 40).
            is_treaty: Whether the SI is a treaty or agreement (default: false).

        Returns:
            Calculated annulment date for the statutory instrument.
        """
        url = build_url(
            f"{WHATSON_API_BASE}/proceduraldates/annulmentdate/forDate.json",
            {
                "dateLaid": date_laid,
                "daysInFuture": days_in_future,
                "isTreaty": is_treaty,
            },
        )
        return await get_result(url)

    @mcp.tool()
    async def get_last_sitting_date(
        house: str,
        date_to_check: str,
        include_weekend_sittings: bool | None = None,
    ) -> str:
        """Get last sitting date | previous sitting, last sat, before recess | Get the last sitting date prior to a specified date | Returns last sitting date

        Args:
            house: House name: 'Commons' or 'Lords'.
            date_to_check: Find last sitting date before this date (YYYY-MM-DD).
            include_weekend_sittings: Whether to include weekend sittings (default: false).

        Returns:
            Last sitting date prior to the specified date.
        """
        url = build_url(
            f"{WHATSON_API_BASE}/proceduraldates/{house}/lastsittingdate.json",
            {
                "dateToCheck": date_to_check,
                "includeWeekendSittings": include_weekend_sittings,
            },
        )
        return await get_result(url)

    @mcp.tool()
    async def get_session_by_id(session_id: int) -> str:
        """Get parliamentary session by ID | session details, parliamentary term, session lookup | Retrieve details of a specific parliamentary session by its ID | Returns session details

        Args:
            session_id: The unique session ID.

        Returns:
            Details of the specified parliamentary session.
        """
        url = f"{WHATSON_API_BASE}/sessions/byid.json/{session_id}"
        return await get_result(url)

    @mcp.tool()
    async def get_session_for_date(date: str) -> str:
        """Get parliamentary session for date | which session, session lookup by date | Find which parliamentary session a given date falls within | Returns session details

        Args:
            date: Date to find the session for (YYYY-MM-DD).

        Returns:
            Parliamentary session details for the specified date.
        """
        url = f"{WHATSON_API_BASE}/sessions/fordate.json/{date}"
        return await get_result(url)

    @mcp.tool()
    async def get_calendar_tags() -> str:
        """Get calendar tags | tags, labels, calendar taxonomy | List all tags used to label parliamentary calendar events | Returns list of tags

        Returns:
            List of calendar event tags.
        """
        url = f"{WHATSON_API_BASE}/tags/list.json"
        return await get_result(url)

    @mcp.tool()
    async def get_calendar_types() -> str:
        """Get calendar event types | event types, calendar classification | List all event types used in the parliamentary calendar | Returns list of event types

        Returns:
            List of parliamentary calendar event types.
        """
        url = f"{WHATSON_API_BASE}/types/list.json"
        return await get_result(url)
