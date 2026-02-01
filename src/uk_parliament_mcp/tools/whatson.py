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
