"""Statutory Instruments API tools for secondary legislation."""
from urllib.parse import quote

from mcp.server.fastmcp import FastMCP

from uk_parliament_mcp.http_client import get_result

STATUTORY_INSTRUMENTS_API_BASE = "https://statutoryinstruments-api.parliament.uk/api/v2"


def register_tools(mcp: FastMCP) -> None:
    """Register statutory instruments tools with the MCP server."""

    @mcp.tool()
    async def search_statutory_instruments(name: str) -> str:
        """Search for Statutory Instruments (secondary legislation) by name. Use when researching government regulations, rules, or orders made under primary legislation. SIs are used to implement or modify laws.

        Args:
            name: Name or title of the statutory instrument to search for.

        Returns:
            Statutory Instruments matching the search term.
        """
        url = f"{STATUTORY_INSTRUMENTS_API_BASE}/StatutoryInstrument?Name={quote(name)}"
        return await get_result(url)

    @mcp.tool()
    async def search_acts_of_parliament(name: str) -> str:
        """Search for Acts of Parliament (primary legislation) by name or topic. Use when researching existing laws, finding legislation on specific subjects, or understanding the legal framework on particular issues.

        Args:
            name: Name or title of the Act to search for (e.g. 'Climate Change Act', 'Human Rights Act').

        Returns:
            Acts of Parliament matching the search term.
        """
        url = f"{STATUTORY_INSTRUMENTS_API_BASE}/ActOfParliament?Name={quote(name)}"
        return await get_result(url)
