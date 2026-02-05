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
            f"{HANSARD_API_BASE}/search/debates.json",
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

    @mcp.tool()
    async def search_hansard_full(
        house: int | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        search_term: str | None = None,
        member_id: int | None = None,
        skip: int = 0,
        take: int = 20,
    ) -> str:
        """Full search across all Hansard content types | Hansard, comprehensive search |
        Use for broad searches across debates, statements, questions, and petitions.
        Returns mixed results from all Hansard content types.

        Args:
            house: House number: 1 for Commons, 2 for Lords (optional).
            start_date: Start date in YYYY-MM-DD format (optional).
            end_date: End date in YYYY-MM-DD format (optional).
            search_term: Search term for speeches or debates (optional).
            member_id: Optional member ID to filter results to a specific MP/Lord.
            skip: Number of results to skip for pagination (default 0).
            take: Number of results to return (default 20).

        Returns:
            Hansard records matching the search criteria across all types.
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
    async def search_hansard_contributions(
        contribution_type: str,
        house: int | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        search_term: str | None = None,
        member_id: int | None = None,
        skip: int = 0,
        take: int = 20,
    ) -> str:
        """Search Hansard by contribution type | Hansard, spoken, written, interventions |
        Use to find specific types of parliamentary contributions.
        Returns contributions of the specified type.

        Args:
            contribution_type: Type of contribution: 'Spoken', 'Written', 'Intervention', 'Question', 'Answer'.
            house: House number: 1 for Commons, 2 for Lords (optional).
            start_date: Start date in YYYY-MM-DD format (optional).
            end_date: End date in YYYY-MM-DD format (optional).
            search_term: Search term (optional).
            member_id: Optional member ID to filter results.
            skip: Number of results to skip for pagination (default 0).
            take: Number of results to return (default 20).

        Returns:
            Contributions of the specified type.
        """
        url = build_url(
            f"{HANSARD_API_BASE}/search/contributions/{contribution_type}.json",
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
    async def search_hansard_members(
        search_term: str,
        house: int | None = None,
        include_former: bool = True,
        include_current: bool = True,
        skip: int = 0,
        take: int = 20,
    ) -> str:
        """Search for members who appear in Hansard | Hansard, member search, speakers |
        Use to find members who have spoken in Parliament by name.
        Returns members matching the search term.

        Args:
            search_term: Name or partial name to search for.
            house: House number: 1 for Commons, 2 for Lords (optional).
            include_former: Include former members (default true).
            include_current: Include current members (default true).
            skip: Number of results to skip for pagination (default 0).
            take: Number of results to return (default 20).

        Returns:
            Members matching the search term.
        """
        url = build_url(
            f"{HANSARD_API_BASE}/search/members.json",
            {
                "queryParameters.searchTerm": search_term,
                "queryParameters.house": house,
                "queryParameters.includeFormer": include_former,
                "queryParameters.includeCurrent": include_current,
                "queryParameters.skip": skip,
                "queryParameters.take": take,
            },
        )
        return await get_result(url)

    @mcp.tool()
    async def search_hansard_divisions(
        house: int | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        search_term: str | None = None,
        member_id: int | None = None,
        skip: int = 0,
        take: int = 20,
    ) -> str:
        """Search for divisions (votes) in Hansard | Hansard, divisions, votes |
        Use to find recorded votes in Parliament.
        Returns divisions matching the search criteria.

        Args:
            house: House number: 1 for Commons, 2 for Lords (optional).
            start_date: Start date in YYYY-MM-DD format (optional).
            end_date: End date in YYYY-MM-DD format (optional).
            search_term: Search term (optional).
            member_id: Optional member ID to filter results.
            skip: Number of results to skip for pagination (default 0).
            take: Number of results to return (default 20).

        Returns:
            Divisions matching the search criteria.
        """
        url = build_url(
            f"{HANSARD_API_BASE}/search/divisions.json",
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
    async def get_member_contribution_summary(
        member_id: int,
        skip: int = 0,
        take: int = 20,
    ) -> str:
        """Get summary of a member's Hansard contributions | Hansard, speaking record, member activity |
        Use to see an overview of how often and when a member has spoken.
        Returns summary of member's parliamentary contributions.

        Args:
            member_id: Parliament member ID.
            skip: Number of results to skip for pagination (default 0).
            take: Number of results to return (default 20).

        Returns:
            Summary of member's speaking record.
        """
        url = build_url(
            f"{HANSARD_API_BASE}/search/membercontributionsummary/{member_id}.json",
            {
                "skip": skip,
                "take": take,
            },
        )
        return await get_result(url)

    @mcp.tool()
    async def get_debate_speakers(debate_section_id: str) -> str:
        """Get list of speakers in a debate | Hansard, debate speakers, who spoke |
        Use to see who participated in a specific debate.
        Returns list of members who spoke in the debate.

        Args:
            debate_section_id: External ID of debate section (from search_hansard).

        Returns:
            List of speakers in the debate.
        """
        url = f"{HANSARD_API_BASE}/debates/speakerslist/{debate_section_id}.json"
        return await get_result(url)

    @mcp.tool()
    async def get_top_level_debate_id(debate_section_id: str) -> str:
        """Get the top-level debate ID for a debate section | Hansard, debate navigation, parent debate |
        Use to navigate to the parent debate from a sub-section.
        Returns the top-level debate ID.

        Args:
            debate_section_id: External ID of debate section.

        Returns:
            Top-level debate ID.
        """
        url = f"{HANSARD_API_BASE}/debates/topleveldebateid/{debate_section_id}.json"
        return await get_result(url)

    @mcp.tool()
    async def get_debate_by_title(
        house: str,
        date: str,
        section_title: str,
    ) -> str:
        """Find a debate by title and date | Hansard, find debate, debate lookup |
        Use when you know the debate title and date but not the ID.
        Returns the debate matching the title and date.

        Args:
            house: House name: 'Commons' or 'Lords'.
            date: Date in YYYY-MM-DD format.
            section_title: Title of the debate section.

        Returns:
            Debate matching the title and date.
        """
        url = build_url(
            f"{HANSARD_API_BASE}/debates/topleveldebatebytitle.json",
            {
                "house": house,
                "date": date,
                "sectionTitle": section_title,
            },
        )
        return await get_result(url)

    @mcp.tool()
    async def get_hansard_last_sitting_date(house: str) -> str:
        """Get the most recent sitting date with Hansard | Hansard, latest, most recent |
        Use to find the most recent day Parliament sat.
        Returns the last sitting date.

        Args:
            house: House name: 'Commons' or 'Lords'.

        Returns:
            Most recent sitting date.
        """
        url = f"{HANSARD_API_BASE}/overview/lastsittingdate.json?house={house}"
        return await get_result(url)

    @mcp.tool()
    async def get_hansard_linked_dates(house: str, date: str) -> str:
        """Get previous and next sitting dates | Hansard, navigation, sitting dates |
        Use to navigate between sitting days.
        Returns previous and next sitting dates relative to given date.

        Args:
            house: House name: 'Commons' or 'Lords'.
            date: Date in YYYY-MM-DD format.

        Returns:
            Previous and next sitting dates.
        """
        url = build_url(
            f"{HANSARD_API_BASE}/overview/linkedsittingdates.json",
            {
                "house": house,
                "date": date,
            },
        )
        return await get_result(url)

    @mcp.tool()
    async def get_hansard_section_trees(
        house: str,
        date: str,
        section: str,
    ) -> str:
        """Get hierarchical structure of debates for a day | Hansard, debate hierarchy, structure |
        Use to see the tree structure of all debates on a sitting day.
        Returns hierarchical tree of debate sections.

        Args:
            house: House name: 'Commons' or 'Lords'.
            date: Date in YYYY-MM-DD format.
            section: Section name (e.g. 'Debate', 'WestHall', 'Petitions', 'GEN'). Get valid names from get_hansard_sitting_day.

        Returns:
            Hierarchical structure of debates.
        """
        url = build_url(
            f"{HANSARD_API_BASE}/overview/sectiontrees.json",
            {
                "house": house,
                "date": date,
                "section": section,
            },
        )
        return await get_result(url)
