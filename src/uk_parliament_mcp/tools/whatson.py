"""WhatsOn API tools for parliamentary calendar and sessions."""

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
