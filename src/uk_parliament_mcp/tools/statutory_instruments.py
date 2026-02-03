"""Statutory Instruments API tools for secondary legislation."""

from urllib.parse import quote

from mcp.server.fastmcp import FastMCP

from uk_parliament_mcp.config import STATUTORY_INSTRUMENTS_API_BASE
from uk_parliament_mcp.http_client import get_result


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

    @mcp.tool()
    async def get_statutory_instrument(instrument_id: str) -> str:
        """Get SI details | statutory instrument, secondary legislation, regulations |
        Get full details of a specific Statutory Instrument |
        Returns SI details including laying info, procedure, status

        Args:
            instrument_id: The SI ID (alphanumeric string from search results).

        Returns:
            Full SI details including laying info, procedure, and status.
        """
        url = f"{STATUTORY_INSTRUMENTS_API_BASE}/StatutoryInstrument/{instrument_id}"
        return await get_result(url)

    @mcp.tool()
    async def get_si_business_items(instrument_id: str) -> str:
        """Get SI business items | SI progress, scrutiny, debates, motions |
        Get business items (debates, motions) for an SI |
        Returns list of business items with dates and outcomes

        Args:
            instrument_id: The SI ID (alphanumeric string from search results).

        Returns:
            Business items for the SI with dates and outcomes.
        """
        url = f"{STATUTORY_INSTRUMENTS_API_BASE}/StatutoryInstrument/{instrument_id}/BusinessItems"
        return await get_result(url)

    @mcp.tool()
    async def get_act_of_parliament(act_id: str) -> str:
        """Get Act details | primary legislation, act of parliament, law |
        Get full details of an Act of Parliament |
        Returns Act details

        Args:
            act_id: The Act ID (alphanumeric string from search results).

        Returns:
            Full Act details.
        """
        url = f"{STATUTORY_INSTRUMENTS_API_BASE}/ActOfParliament/{act_id}"
        return await get_result(url)
