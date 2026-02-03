"""Hansard API tools for searching the official parliamentary record."""

from mcp.server.fastmcp import FastMCP

from uk_parliament_mcp.config import HANSARD_API_BASE
from uk_parliament_mcp.http_client import build_url, get_result


def register_tools(mcp: FastMCP) -> None:
    """Register Hansard tools with the MCP server."""

    @mcp.tool()
    async def search_hansard(
        house: int,
        start_date: str,
        end_date: str,
        search_term: str,
        member_id: int | None = None,
        skip: int = 0,
        take: int = 20,
    ) -> str:
        """Search Hansard (official parliamentary record) for speeches and debates. Use when researching what was said in Parliament on specific topics, by specific members, or in specific time periods. House: 1=Commons, 2=Lords.

        Args:
            house: House number: 1 for Commons, 2 for Lords.
            start_date: Start date in YYYY-MM-DD format.
            end_date: End date in YYYY-MM-DD format.
            search_term: Search term for speeches or debates (e.g. 'climate change', 'NHS').
            member_id: Optional member ID to filter results to a specific MP/Lord.
            skip: Number of results to skip for pagination (default 0).
            take: Number of results to return (default 20, max varies by endpoint).

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
                "queryParameters.memberId": member_id,
                "queryParameters.skip": skip,
                "queryParameters.take": take,
            },
        )
        return await get_result(url)

    @mcp.tool()
    async def get_debate_by_id(debate_section_id: str) -> str:
        """Get full debate transcript | Hansard, speeches, contributions |
        Use after search_hansard to get complete debate with all member speeches.
        Returns debate title, date, house, and all contributions.

        Args:
            debate_section_id: External ID from search_hansard results.

        Returns:
            Full debate with all member contributions.
        """
        url = f"{HANSARD_API_BASE}/debates/debate/{debate_section_id}.json"
        return await get_result(url)

    @mcp.tool()
    async def get_member_hansard_contributions(
        member_id: int,
        debate_section_id: str,
    ) -> str:
        """Get all speeches by a specific MP/Lord in a debate | Hansard, member speeches |
        Use to extract just one member's contributions from a debate.
        Returns all contributions by that member in the specified debate.

        Args:
            member_id: Parliament member ID (from members API).
            debate_section_id: External ID of debate section (from search_hansard).

        Returns:
            All contributions by that member in the debate.
        """
        url = f"{HANSARD_API_BASE}/debates/memberdebatecontributions/{member_id}.json?debateSectionExtId={debate_section_id}"
        return await get_result(url)

    @mcp.tool()
    async def get_debate_divisions(debate_section_id: str) -> str:
        """Get votes that occurred during a debate | Hansard, divisions, voting |
        Use to find divisions (votes) that took place in a specific debate.
        Returns list of divisions with aye/noe counts.

        Args:
            debate_section_id: External ID of debate section (from search_hansard).

        Returns:
            List of divisions with vote counts.
        """
        url = f"{HANSARD_API_BASE}/debates/divisions/{debate_section_id}.json"
        return await get_result(url)

    @mcp.tool()
    async def get_division_details(
        division_id: str,
        is_evel: bool = False,
    ) -> str:
        """Get full division details including how each member voted | Hansard, division, voting records |
        Use to see individual voting records for a specific division.
        Returns division with debate title, counts, and member voting records.

        Args:
            division_id: External ID of division (from get_debate_divisions).
            is_evel: Filter to EVEL (English Votes for English Laws) voters only.

        Returns:
            Division details with member voting records.
        """
        url = build_url(
            f"{HANSARD_API_BASE}/debates/division/{division_id}.json",
            {"isEvel": is_evel if is_evel else None},
        )
        return await get_result(url)

    @mcp.tool()
    async def get_hansard_sitting_day(
        sitting_date: str,
        house: int,
    ) -> str:
        """Get full agenda/sections for a sitting day | Hansard, daily business, agenda |
        Use to see all debates and business for a specific day.
        Returns all debate sections for that day.

        Args:
            sitting_date: Date in YYYY-MM-DD format.
            house: House number: 1 for Commons, 2 for Lords.

        Returns:
            All debate sections for that day.
        """
        url = build_url(
            f"{HANSARD_API_BASE}/overview/sectionsforday.json",
            {
                "date": sitting_date,
                "house": house,
            },
        )
        return await get_result(url)

    @mcp.tool()
    async def get_hansard_calendar(
        year: int,
        month: int,
        house: int,
    ) -> str:
        """Get all sitting dates for a month | Hansard, calendar, sitting days |
        Use to discover which days have Hansard records available.
        Returns list of sitting dates with Hansard available.

        Args:
            year: Year (e.g. 2024).
            month: Month number (1-12).
            house: House number: 1 for Commons, 2 for Lords.

        Returns:
            List of sitting dates for the month.
        """
        url = build_url(
            f"{HANSARD_API_BASE}/overview/calendar.json",
            {
                "year": year,
                "month": month,
                "house": house,
            },
        )
        return await get_result(url)
