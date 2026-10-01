"""Commons and Lords Votes API tools for divisions and voting records.

The two votes APIs expose the same five endpoints with different paths and
parameter spellings, so one factory registers both sets of tools from a
per-house spec.
"""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from mcp.server.fastmcp import FastMCP

from uk_parliament_mcp.config import COMMONS_VOTES_API_BASE, LORDS_VOTES_API_BASE
from uk_parliament_mcp.http_client import build_url, get_result


@dataclass(frozen=True)
class VotesApi:
    """Where one house's votes API lives and how it spells its parameters."""

    house: str  # "Commons" or "Lords", used in tool names and descriptions
    member: str  # "MP" or "Lord"
    vote_words: str  # how a vote is described in the division detail
    search_url: str
    member_voting_url: str
    grouped_by_party_url: str
    search_count_url: str
    division_url: Callable[[int], str]
    param: Callable[[str], str]  # canonical camelCase name -> API query parameter
    # Lords only: filter by majority size or total votes cast (find close votes)
    has_vote_filters: bool = False

    @property
    def prefix(self) -> str:
        return self.house.lower()

    def params(self, **values: Any) -> dict[str, Any]:
        return {self.param(name): value for name, value in values.items()}


COMMONS = VotesApi(
    house="Commons",
    member="MP",
    vote_words="aye/no",
    search_url=f"{COMMONS_VOTES_API_BASE}/divisions.json/search",
    member_voting_url=f"{COMMONS_VOTES_API_BASE}/divisions.json/membervoting",
    grouped_by_party_url=f"{COMMONS_VOTES_API_BASE}/divisions.json/groupedbyparty",
    search_count_url=f"{COMMONS_VOTES_API_BASE}/divisions.json/searchTotalResults",
    division_url=lambda division_id: f"{COMMONS_VOTES_API_BASE}/division/{division_id}.json",
    param=lambda name: f"queryParameters.{name}",
)

LORDS = VotesApi(
    house="Lords",
    member="Lord",
    vote_words="content/not content",
    search_url=f"{LORDS_VOTES_API_BASE}/Divisions/search",
    member_voting_url=f"{LORDS_VOTES_API_BASE}/Divisions/membervoting",
    grouped_by_party_url=f"{LORDS_VOTES_API_BASE}/Divisions/groupedbyparty",
    search_count_url=f"{LORDS_VOTES_API_BASE}/Divisions/searchTotalResults",
    division_url=lambda division_id: f"{LORDS_VOTES_API_BASE}/Divisions/{division_id}",
    param=lambda name: name if name in ("skip", "take") else name[0].upper() + name[1:],
    has_vote_filters=True,
)

_SEARCH_TERM_ARG = """
            search_term: Optional: search term for division topics (e.g. 'brexit', 'climate', 'NHS')."""
_MEMBER_ARG = """
            member_id: Optional: only divisions this member voted in."""
_DATE_ARGS = """
            start_date: Optional: start date in YYYY-MM-DD format.
            end_date: Optional: end date in YYYY-MM-DD format.
            division_number: Optional: specific division number.
            include_when_member_was_teller: Optional: include divisions where the member was a teller."""
_FILTER_ARGS = _SEARCH_TERM_ARG + _MEMBER_ARG + _DATE_ARGS

_VOTE_FILTER_ARGS = """
            majority_comparator: Optional: compare majority - 'LessThan', 'LessThanOrEqualTo', 'EqualTo', 'GreaterThanOrEqualTo', 'GreaterThan'. Use with majority_value to find close votes.
            majority_value: Optional: majority threshold to compare against (e.g., 10 to find votes with margin < 10).
            total_votes_comparator: Optional: compare total votes - same options as majority_comparator.
            total_votes_value: Optional: total votes threshold to compare against."""

_PAGING_ARGS = """
            skip: Number of records to skip (for pagination).
            take: Number of records to return (default 25, max 100)."""


def _search_description(api: VotesApi) -> str:
    close_votes = " or find close/contested votes" if api.has_vote_filters else ""
    see_also = "search_lords_divisions" if api.house == "Commons" else "search_commons_divisions"
    vote_filters = _VOTE_FILTER_ARGS if api.has_vote_filters else ""
    return f"""Search {api.house} divisions | House of {api.house} votes, {api.house} voting records, how {api.member}s voted | Use to find how {api.member}s voted on bills, amendments or issues{close_votes}; filter by member, date range or division number | Returns matching divisions with vote counts. See also: {see_also}, get_{api.prefix}_division_by_id, compare_member_votes.

        Args:{_FILTER_ARGS}{vote_filters}{_PAGING_ARGS}
        """


def register_house_tools(mcp: FastMCP, api: VotesApi) -> None:
    """Register the five votes tools for one house."""
    p = api.prefix

    async def _search(**values: Any) -> str:
        url = build_url(api.search_url, api.params(**values))
        return await get_result(url)

    if api.has_vote_filters:

        @mcp.tool(name=f"search_{p}_divisions", description=_search_description(api))
        async def search_divisions_with_vote_filters(
            search_term: str | None = None,
            member_id: int | None = None,
            start_date: str | None = None,
            end_date: str | None = None,
            division_number: int | None = None,
            include_when_member_was_teller: bool | None = None,
            majority_comparator: str | None = None,
            majority_value: int | None = None,
            total_votes_comparator: str | None = None,
            total_votes_value: int | None = None,
            skip: int = 0,
            take: int = 25,
        ) -> str:
            return await _search(
                searchTerm=search_term,
                memberId=member_id,
                startDate=start_date,
                endDate=end_date,
                divisionNumber=division_number,
                includeWhenMemberWasTeller=include_when_member_was_teller,
                **{
                    "majority.Comparator": majority_comparator,
                    "majority.ValueToCompare": majority_value,
                    "totalVotesCast.Comparator": total_votes_comparator,
                    "totalVotesCast.ValueToCompare": total_votes_value,
                },
                skip=skip,
                take=take,
            )

    else:

        @mcp.tool(name=f"search_{p}_divisions", description=_search_description(api))
        async def search_divisions(
            search_term: str | None = None,
            member_id: int | None = None,
            start_date: str | None = None,
            end_date: str | None = None,
            division_number: int | None = None,
            include_when_member_was_teller: bool | None = None,
            skip: int = 0,
            take: int = 25,
        ) -> str:
            return await _search(
                searchTerm=search_term,
                memberId=member_id,
                startDate=start_date,
                endDate=end_date,
                divisionNumber=division_number,
                includeWhenMemberWasTeller=include_when_member_was_teller,
                skip=skip,
                take=take,
            )

    @mcp.tool(
        name=f"get_{p}_voting_record_for_member",
        description=f"""Get the voting record of a {api.member} in House of {api.house} divisions | {api.member} votes, voting history, voting pattern | Use when analyzing how a specific {api.member} votes or their stance on issues through their voting history | Returns the divisions the member voted in, newest first. See also: get_member_voting, compare_member_votes.

        Args:
            member_id: Parliament member ID.{_SEARCH_TERM_ARG}{_DATE_ARGS}{_PAGING_ARGS}
        """,
    )
    async def get_voting_record_for_member(
        member_id: int,
        search_term: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        division_number: int | None = None,
        include_when_member_was_teller: bool | None = None,
        skip: int = 0,
        take: int = 25,
    ) -> str:
        url = build_url(
            api.member_voting_url,
            api.params(
                memberId=member_id,
                searchTerm=search_term,
                startDate=start_date,
                endDate=end_date,
                divisionNumber=division_number,
                includeWhenMemberWasTeller=include_when_member_was_teller,
                skip=skip,
                take=take,
            ),
        )
        return await get_result(url)

    @mcp.tool(
        name=f"get_{p}_division_by_id",
        description=f"""Get one House of {api.house} division by ID | {api.house} vote details, division list, tellers | Use when you need complete details of a particular vote | Returns who voted {api.vote_words}, tellers and vote totals.

        Args:
            division_id: Unique {api.house} division ID number.
        """,
    )
    async def get_division_by_id(division_id: int) -> str:
        return await get_result(api.division_url(division_id))

    @mcp.tool(
        name=f"get_{p}_divisions_grouped_by_party",
        description=f"""Get House of {api.house} divisions grouped by party | party-line voting, how parties voted, rebellions | Use when analyzing how different parties voted on issues | Returns vote counts by party rather than individual members.

        Args:{_FILTER_ARGS}
        """,
    )
    async def get_divisions_grouped_by_party(
        search_term: str | None = None,
        member_id: int | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        division_number: int | None = None,
        include_when_member_was_teller: bool | None = None,
    ) -> str:
        url = build_url(
            api.grouped_by_party_url,
            api.params(
                searchTerm=search_term,
                memberId=member_id,
                startDate=start_date,
                endDate=end_date,
                divisionNumber=division_number,
                includeWhenMemberWasTeller=include_when_member_was_teller,
            ),
        )
        return await get_result(url)

    @mcp.tool(
        name=f"get_{p}_divisions_search_count",
        description=f"""Count House of {api.house} divisions matching search criteria | number of votes, how many divisions | Use to size a search before fetching results with search_{p}_divisions | Returns the total count.

        Args:{_FILTER_ARGS}
        """,
    )
    async def get_divisions_search_count(
        search_term: str | None = None,
        member_id: int | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        division_number: int | None = None,
        include_when_member_was_teller: bool | None = None,
    ) -> str:
        url = build_url(
            api.search_count_url,
            api.params(
                searchTerm=search_term,
                memberId=member_id,
                startDate=start_date,
                endDate=end_date,
                divisionNumber=division_number,
                includeWhenMemberWasTeller=include_when_member_was_teller,
            ),
        )
        return await get_result(url)


def register_tools(mcp: FastMCP) -> None:
    """Register Commons and Lords votes tools with the MCP server."""
    register_house_tools(mcp, COMMONS)
    register_house_tools(mcp, LORDS)
