"""Erskine May API tools for parliamentary procedure."""

from urllib.parse import quote

from mcp.server.fastmcp import FastMCP

from uk_parliament_mcp.config import ERSKINE_MAY_API_BASE
from uk_parliament_mcp.http_client import get_result


def register_tools(mcp: FastMCP) -> None:
    """Register Erskine May tools with the MCP server."""

    @mcp.tool()
    async def search_erskine_may(search_term: str) -> str:
        """Search Erskine May parliamentary procedure manual. Use when you need to understand parliamentary rules, procedures, or precedents. Erskine May is the authoritative guide to parliamentary procedure.

        Args:
            search_term: Search term for parliamentary procedure rules (e.g. 'Speaker', 'amendment', 'division').

        Returns:
            Erskine May paragraphs matching the search term.
        """
        url = f"{ERSKINE_MAY_API_BASE}/Search/ParagraphSearchResults/{quote(search_term)}"
        return await get_result(url)
