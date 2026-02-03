"""Treaties API tools for international agreements."""

from urllib.parse import quote

from mcp.server.fastmcp import FastMCP

from uk_parliament_mcp.config import TREATIES_API_BASE
from uk_parliament_mcp.http_client import get_result


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
        url = f"{TREATIES_API_BASE}/Treaty?SearchText={quote(search_text)}"
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
