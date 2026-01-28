"""Hansard API tools for searching the official parliamentary record."""

from mcp.server.fastmcp import FastMCP

from uk_parliament_mcp.http_client import build_url, get_result

HANSARD_API_BASE = "https://hansard-api.parliament.uk"


def register_tools(mcp: FastMCP) -> None:
    """Register Hansard tools with the MCP server."""

    @mcp.tool()
    async def search_hansard(
        house: int,
        start_date: str,
        end_date: str,
        search_term: str,
    ) -> str:
        """Search Hansard (official parliamentary record) for speeches and debates. Use when researching what was said in Parliament on specific topics, by specific members, or in specific time periods. House: 1=Commons, 2=Lords.

        Args:
            house: House number: 1 for Commons, 2 for Lords.
            start_date: Start date in YYYY-MM-DD format.
            end_date: End date in YYYY-MM-DD format.
            search_term: Search term for speeches or debates (e.g. 'climate change', 'NHS').

        Returns:
            Hansard records matching the search criteria.
        """
        url = build_url(
            f"{HANSARD_API_BASE}/search.json",
            {
                "queryParameters.house": house,
                "queryParameters.startDate": start_date,
                "queryParameters.endDate": end_date,
                "queryParameters.searchTerm": search_term,
            },
        )
        return await get_result(url)
