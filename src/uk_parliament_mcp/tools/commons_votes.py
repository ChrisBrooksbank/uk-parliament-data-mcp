"""Commons Votes API tools for House of Commons divisions and voting records."""
from mcp.server.fastmcp import FastMCP

from uk_parliament_mcp.http_client import build_url, get_result

COMMONS_VOTES_API_BASE = "http://commonsvotes-api.parliament.uk/data"


def register_tools(mcp: FastMCP) -> None:
    """Register Commons votes tools with the MCP server."""

    @mcp.tool()
    async def search_commons_divisions(
        search_term: str,
        member_id: int | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        division_number: int | None = None,
    ) -> str:
        """Search House of Commons voting records (divisions). Use when you want to find how MPs voted on specific issues, bills, or amendments. Can filter by member, date range, or division number.

        Args:
            search_term: Search term for division topics (e.g. 'brexit', 'climate', 'NHS').
            member_id: Optional: specific member ID to filter votes.
            start_date: Optional: start date in YYYY-MM-DD format.
            end_date: Optional: end date in YYYY-MM-DD format.
            division_number: Optional: specific division number.

        Returns:
            Commons divisions matching the search criteria.
        """
        url = build_url(
            f"{COMMONS_VOTES_API_BASE}/divisions.json/search",
            {
                "queryParameters.searchTerm": search_term,
                "memberId": member_id,
                "queryParameters.startDate": start_date,
                "queryParameters.endDate": end_date,
                "queryParameters.divisionNumber": division_number,
            },
        )
        return await get_result(url)

    @mcp.tool()
    async def get_commons_voting_record_for_member(member_id: int) -> str:
        """Get complete voting record of an MP in House of Commons divisions. Use when analyzing how a specific MP votes, their voting patterns, or their stance on particular issues through their voting history.

        Args:
            member_id: Parliament member ID to get Commons voting record for.

        Returns:
            Complete Commons voting record for the member.
        """
        url = f"{COMMONS_VOTES_API_BASE}/divisions.json/membervoting?queryParameters.memberId={member_id}"
        return await get_result(url)

    @mcp.tool()
    async def get_commons_division_by_id(division_id: int) -> str:
        """Get detailed information about a specific House of Commons division by ID. Use when you need complete details about a particular vote including who voted for/against, tellers, and voting totals.

        Args:
            division_id: Unique Commons division ID number.

        Returns:
            Detailed information about the Commons division.
        """
        url = f"{COMMONS_VOTES_API_BASE}/division/{division_id}.json"
        return await get_result(url)

    @mcp.tool()
    async def get_commons_divisions_grouped_by_party(
        search_term: str | None = None,
        member_id: int | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        division_number: int | None = None,
        include_when_member_was_teller: bool | None = None,
    ) -> str:
        """Get House of Commons divisions grouped by party voting patterns. Use when analyzing how different parties voted on issues or understanding party-line voting behavior. Shows vote counts by party rather than individual MPs.

        Args:
            search_term: Optional: search term to filter divisions.
            member_id: Optional: member ID to filter divisions.
            start_date: Optional: start date in YYYY-MM-DD format.
            end_date: Optional: end date in YYYY-MM-DD format.
            division_number: Optional: specific division number.
            include_when_member_was_teller: Optional: include when member was a teller.

        Returns:
            Commons divisions grouped by party.
        """
        url = build_url(
            f"{COMMONS_VOTES_API_BASE}/divisions.json/groupedbyparty",
            {
                "queryParameters.searchTerm": search_term,
                "queryParameters.memberId": member_id,
                "queryParameters.startDate": start_date,
                "queryParameters.endDate": end_date,
                "queryParameters.divisionNumber": division_number,
                "queryParameters.includeWhenMemberWasTeller": include_when_member_was_teller,
            },
        )
        return await get_result(url)

    @mcp.tool()
    async def get_commons_divisions_search_count(
        search_term: str | None = None,
        member_id: int | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        division_number: int | None = None,
        include_when_member_was_teller: bool | None = None,
    ) -> str:
        """Get total count of House of Commons divisions matching search criteria. Use when you need to know how many divisions match your search parameters before retrieving the actual results.

        Args:
            search_term: Optional: search term to filter divisions.
            member_id: Optional: member ID to filter divisions.
            start_date: Optional: start date in YYYY-MM-DD format.
            end_date: Optional: end date in YYYY-MM-DD format.
            division_number: Optional: specific division number.
            include_when_member_was_teller: Optional: include when member was a teller.

        Returns:
            Total count of matching Commons divisions.
        """
        url = build_url(
            f"{COMMONS_VOTES_API_BASE}/divisions.json/searchTotalResults",
            {
                "queryParameters.searchTerm": search_term,
                "queryParameters.memberId": member_id,
                "queryParameters.startDate": start_date,
                "queryParameters.endDate": end_date,
                "queryParameters.divisionNumber": division_number,
                "queryParameters.includeWhenMemberWasTeller": include_when_member_was_teller,
            },
        )
        return await get_result(url)
