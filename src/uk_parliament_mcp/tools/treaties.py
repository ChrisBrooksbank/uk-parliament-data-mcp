"""Treaties API tools for international agreements."""
from urllib.parse import quote

from mcp.server.fastmcp import FastMCP

from uk_parliament_mcp.http_client import get_result

TREATIES_API_BASE = "https://treaties-api.parliament.uk/api"


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
