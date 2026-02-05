"""Treaties API tools for international agreements."""

from mcp.server.fastmcp import FastMCP

from uk_parliament_mcp.config import TREATIES_API_BASE
from uk_parliament_mcp.http_client import build_url, get_result


def register_tools(mcp: FastMCP) -> None:
    """Register treaties tools with the MCP server."""

    @mcp.tool()
    async def search_treaties(search_text: str) -> str:
        """Search UK international treaties and agreements under parliamentary scrutiny | treaties, international agreements, trade deals, diplomatic treaties, international law, bilateral agreements | Use for researching international relations, trade agreements, or diplomatic commitments | Returns treaty details including titles, countries involved, and parliamentary scrutiny status

        Args:
            search_text: Search term for treaties. Examples: 'trade', 'EU', 'climate', 'Brexit'. Searches titles and content.

        Returns:
            Treaty details including titles, countries involved, and parliamentary scrutiny status.
        """
        url = build_url(f"{TREATIES_API_BASE}/Treaty", {"SearchText": search_text})
        return await get_result(url)

    @mcp.tool()
    async def search_treaties_advanced(
        search_text: str | None = None,
        government_organisation_id: int | None = None,
        series: str | None = None,
        parliamentary_process: str | None = None,
        debate_scheduled: bool | None = None,
        motions_tabled: bool | None = None,
        committee_raised_concerns: bool | None = None,
        house: str | None = None,
        skip: int = 0,
        take: int = 20,
    ) -> str:
        """Advanced treaty search with full filtering | treaties, controversial treaties, committee concerns, scrutiny status | Use to find treaties by department, scrutiny status, or with parliamentary concerns | Returns treaties matching all specified filters

        Args:
            search_text: Optional: search term for treaty titles/content.
            government_organisation_id: Optional: filter by laying department ID (get IDs from get_treaty_government_organisations).
            series: Optional: treaty series type - 'CountrySeriesMembership', 'EuropeanUnionSeriesMembership', or 'MiscellaneousSeriesMembership'.
            parliamentary_process: Optional: 'NotConcluded' or 'Concluded'.
            debate_scheduled: Optional: filter to treaties where debate has been scheduled.
            motions_tabled: Optional: filter to treaties where motions have been tabled.
            committee_raised_concerns: Optional: filter to treaties where a committee has raised concerns.
            house: Optional: 'Commons' or 'Lords'.
            skip: Number of records to skip (for pagination).
            take: Number of records to return (default 20).

        Returns:
            Treaties matching the specified filters with scrutiny status.
        """
        url = build_url(
            f"{TREATIES_API_BASE}/Treaty",
            {
                "SearchText": search_text,
                "GovernmentOrganisationId": government_organisation_id,
                "Series": series,
                "ParliamentaryProcess": parliamentary_process,
                "DebateScheduled": debate_scheduled,
                "MotionsTabledAboutATreaty": motions_tabled,
                "CommitteeRaisedConcerns": committee_raised_concerns,
                "House": house,
                "Skip": skip,
                "Take": take,
            },
        )
        return await get_result(url)

    @mcp.tool()
    async def get_treaty_government_organisations() -> str:
        """Get departments that lay treaties | treaty departments, laying bodies, Foreign Office | Use to get organisation IDs for filtering treaty searches | Returns list of government organisations with IDs

        Returns:
            List of government organisations that can lay treaties, with their IDs.
        """
        url = f"{TREATIES_API_BASE}/GovernmentOrganisation"
        return await get_result(url)

    @mcp.tool()
    async def get_treaty_series_memberships() -> str:
        """Get treaty series types | treaty categories, Country series, EU series | Use to understand treaty classification categories | Returns list of treaty series types

        Returns:
            List of treaty series membership types (Country, EU, Miscellaneous).
        """
        url = f"{TREATIES_API_BASE}/SeriesMembership"
        return await get_result(url)

    @mcp.tool()
    async def get_treaty(treaty_id: str) -> str:
        """Get treaty details | international agreement, treaty, diplomatic |
        Get full details of a specific treaty |
        Returns treaty details including status, dates, parties

        Args:
            treaty_id: The treaty ID (alphanumeric string from search results).

        Returns:
            Full treaty details including status, dates, and parties.
        """
        url = f"{TREATIES_API_BASE}/Treaty/{treaty_id}"
        return await get_result(url)

    @mcp.tool()
    async def get_treaty_business_items(treaty_id: str) -> str:
        """Get treaty scrutiny | treaty progress, CRaG, debates, parliamentary scrutiny |
        Get parliamentary business items for treaty scrutiny |
        Returns list of business items with dates

        Args:
            treaty_id: The treaty ID (alphanumeric string from search results).

        Returns:
            Business items for the treaty with dates.
        """
        url = f"{TREATIES_API_BASE}/Treaty/{treaty_id}/BusinessItems"
        return await get_result(url)
