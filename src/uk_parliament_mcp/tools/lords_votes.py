"""Lords Votes API tools for House of Lords divisions and voting records."""
from urllib.parse import quote

from mcp.server.fastmcp import FastMCP

from uk_parliament_mcp.http_client import build_url, get_result

LORDS_VOTES_API_BASE = "http://lordsvotes-api.parliament.uk/data"


def register_tools(mcp: FastMCP) -> None:
    """Register Lords votes tools with the MCP server."""

    @mcp.tool()
    async def search_lords_divisions(search_term: str) -> str:
        """Search House of Lords voting records (divisions). Use when you want to find how Lords voted on specific issues, bills, or amendments in the upper chamber.

        Args:
            search_term: Search term for Lords division topics (e.g. 'brexit', 'climate', 'NHS').

        Returns:
            Lords divisions matching the search term.
        """
        url = f"{LORDS_VOTES_API_BASE}/divisions/search?queryParameters.searchTerm={quote(search_term)}"
        return await get_result(url)

    @mcp.tool()
    async def get_lords_voting_record_for_member(
        member_id: int,
        search_term: str | None = None,
        include_when_member_was_teller: bool | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        division_number: int | None = None,
        skip: int = 0,
        take: int = 25,
    ) -> str:
        """Get complete voting record of a Lord in House of Lords divisions. Use when analyzing how a specific Lord votes, their voting patterns, or their stance on particular issues through their voting history.

        Args:
            member_id: Parliament member ID to get Lords voting record for.
            search_term: Optional: search term to filter divisions.
            include_when_member_was_teller: Optional: include votes where member was a teller.
            start_date: Optional: start date in YYYY-MM-DD format.
            end_date: Optional: end date in YYYY-MM-DD format.
            division_number: Optional: specific division number.
            skip: Number of records to skip (for pagination).
            take: Number of records to return (default 25, max 100).

        Returns:
            Complete Lords voting record for the member.
        """
        url = build_url(
            f"{LORDS_VOTES_API_BASE}/Divisions/membervoting",
            {
                "MemberId": member_id,
                "SearchTerm": search_term,
                "IncludeWhenMemberWasTeller": include_when_member_was_teller,
                "StartDate": start_date,
                "EndDate": end_date,
                "DivisionNumber": division_number,
                "skip": skip,
                "take": take,
            },
        )
        return await get_result(url)

    @mcp.tool()
    async def get_lords_division_by_id(division_id: int) -> str:
        """Get detailed information about a specific House of Lords division by ID. Use when you need complete details about a particular Lords vote including who voted content/not content, tellers, and voting totals.

        Args:
            division_id: Unique Lords division ID number.

        Returns:
            Detailed information about the Lords division.
        """
        url = f"{LORDS_VOTES_API_BASE}/Divisions/{division_id}"
        return await get_result(url)

    @mcp.tool()
    async def get_lords_divisions_grouped_by_party(
        search_term: str | None = None,
        member_id: int | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        division_number: int | None = None,
        include_when_member_was_teller: bool | None = None,
    ) -> str:
        """Get House of Lords divisions grouped by party voting patterns. Use when analyzing how different parties voted on issues in the Lords or understanding party-line voting behavior. Shows vote counts by party rather than individual Lords.

        Args:
            search_term: Optional: search term to filter divisions.
            member_id: Optional: member ID to filter divisions.
            start_date: Optional: start date in YYYY-MM-DD format.
            end_date: Optional: end date in YYYY-MM-DD format.
            division_number: Optional: specific division number.
            include_when_member_was_teller: Optional: include when member was a teller.

        Returns:
            Lords divisions grouped by party.
        """
        url = build_url(
            f"{LORDS_VOTES_API_BASE}/Divisions/groupedbyparty",
            {
                "SearchTerm": search_term,
                "MemberId": member_id,
                "StartDate": start_date,
                "EndDate": end_date,
                "DivisionNumber": division_number,
                "IncludeWhenMemberWasTeller": include_when_member_was_teller,
            },
        )
        return await get_result(url)

    @mcp.tool()
    async def get_lords_divisions_search_count(
        search_term: str | None = None,
        member_id: int | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        division_number: int | None = None,
        include_when_member_was_teller: bool | None = None,
    ) -> str:
        """Get total count of House of Lords divisions matching search criteria. Use when you need to know how many Lords divisions match your search parameters before retrieving the actual results.

        Args:
            search_term: Optional: search term to filter divisions.
            member_id: Optional: member ID to filter divisions.
            start_date: Optional: start date in YYYY-MM-DD format.
            end_date: Optional: end date in YYYY-MM-DD format.
            division_number: Optional: specific division number.
            include_when_member_was_teller: Optional: include when member was a teller.

        Returns:
            Total count of matching Lords divisions.
        """
        url = build_url(
            f"{LORDS_VOTES_API_BASE}/Divisions/searchTotalResults",
            {
                "SearchTerm": search_term,
                "MemberId": member_id,
                "StartDate": start_date,
                "EndDate": end_date,
                "DivisionNumber": division_number,
                "IncludeWhenMemberWasTeller": include_when_member_was_teller,
            },
        )
        return await get_result(url)
