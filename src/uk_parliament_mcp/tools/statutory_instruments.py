"""Statutory Instruments API tools for secondary legislation."""

from urllib.parse import quote

from mcp.server.fastmcp import FastMCP

from uk_parliament_mcp.config import STATUTORY_INSTRUMENTS_API_BASE, house_name
from uk_parliament_mcp.http_client import build_url, get_result, get_result_cached


def register_tools(mcp: FastMCP) -> None:
    """Register statutory instruments tools with the MCP server."""

    @mcp.tool()
    async def search_statutory_instruments(
        name: str | None = None,
        procedure_id: str | None = None,
        recommended_for_procedure_change: bool | None = None,
        laying_body_id: str | None = None,
        department_id: int | None = None,
        house: int | str | None = None,
        skip: int = 0,
        take: int = 20,
    ) -> str:
        """Search for Statutory Instruments (secondary legislation), including proposed negative SIs (PNSIs) under sifting. Use when researching government regulations, rules, or orders made under primary legislation. SIs are used to implement or modify laws. See also: get_statutory_instrument, get_si_business_items, get_annulment_date.

        Args:
            name: Optional. Name or title of the statutory instrument to search for.
            procedure_id: Optional. Procedure ID from get_si_procedures() (e.g. the "Proposed negative statutory instrument" procedure to list PNSIs).
            recommended_for_procedure_change: Optional. Only PNSIs a sifting committee recommended for the affirmative procedure.
            laying_body_id: Optional. Laying body ID from get_laying_bodies().
            department_id: Optional. Government department ID.
            house: Optional: 'Commons' or 'Lords' (1 or 2 also accepted).
            skip: Number of records to skip (pagination, default 0).
            take: Number of records to return (default 20).

        Returns:
            Statutory Instruments matching the filters.
        """
        house = house_name(house)
        url = build_url(
            f"{STATUTORY_INSTRUMENTS_API_BASE}/StatutoryInstrument",
            {
                "Name": name,
                "Procedure": procedure_id,
                "RecommendedForProcedureChange": recommended_for_procedure_change,
                "LayingBodyId": laying_body_id,
                "DepartmentId": department_id,
                "House": house,
                "Skip": skip,
                "Take": take,
            },
        )
        return await get_result(url)

    @mcp.tool()
    async def search_acts_of_parliament(name: str) -> str:
        """Search for Acts of Parliament (primary legislation) by name or topic. Use when researching existing laws, finding legislation on specific subjects, or understanding the legal framework on particular issues. See also: get_act_of_parliament, search_bills.

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

    @mcp.tool()
    async def get_laying_bodies() -> str:
        """List SI laying bodies | laying body, department, government organisation, JCSI |
        Get all bodies that can lay statutory instruments before Parliament |
        Returns list of laying bodies with IDs and names

        Returns:
            List of all laying bodies with IDs and names.
        """
        url = f"{STATUTORY_INSTRUMENTS_API_BASE}/LayingBody"
        return await get_result_cached(url, cache_key=url)

    @mcp.tool()
    async def get_si_procedures() -> str:
        """List SI procedures | statutory instrument procedure, affirmative, negative, made affirmative |
        Get all statutory instrument procedures |
        Returns list of SI procedures with IDs and names

        Returns:
            List of all SI procedures with IDs and names.
        """
        url = f"{STATUTORY_INSTRUMENTS_API_BASE}/Procedure"
        return await get_result_cached(url, cache_key=url)

    @mcp.tool()
    async def get_si_procedure(procedure_id: str) -> str:
        """Get SI procedure details | statutory instrument procedure, affirmative, negative |
        Get details of a specific SI procedure |
        Returns procedure details including workflow steps

        Args:
            procedure_id: The procedure ID (alphanumeric string from get_si_procedures).

        Returns:
            Procedure details including workflow steps.
        """
        url = f"{STATUTORY_INSTRUMENTS_API_BASE}/Procedure/{quote(procedure_id)}"
        return await get_result(url)

    @mcp.tool()
    async def get_si_timeline_business_items(timeline_id: str) -> str:
        """Get SI timeline business items | statutory instrument timeline, workflow, procedure steps |
        Get business items for an SI workflow timeline |
        Returns all business items in the SI procedure timeline

        Args:
            timeline_id: The timeline ID (alphanumeric string from SI details).

        Returns:
            All business items in the SI procedure timeline.
        """
        url = f"{STATUTORY_INSTRUMENTS_API_BASE}/Timeline/{quote(timeline_id)}/BusinessItems"
        return await get_result(url)
