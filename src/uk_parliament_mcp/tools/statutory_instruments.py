"""Statutory Instruments API tools for secondary legislation."""

from urllib.parse import quote

from mcp.server.fastmcp import FastMCP

from uk_parliament_mcp.config import STATUTORY_INSTRUMENTS_API_BASE
from uk_parliament_mcp.http_client import build_url, get_result

STATUTORY_INSTRUMENTS_API_BASE_V1 = "https://statutoryinstruments-api.parliament.uk/api/v1"


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

    @mcp.tool()
    async def get_si_business_item(
        item_id: str,
        laid_paper: bool | None = None,
    ) -> str:
        """Get SI business item details | statutory instrument scrutiny, business item, JCSI, SLSC |
        Get details of a specific business item for an SI |
        Returns business item details including scrutiny outcomes

        Args:
            item_id: The business item ID (alphanumeric string).
            laid_paper: Optional. If True, treat ID as a laid paper ID.

        Returns:
            Business item details including scrutiny outcomes.
        """
        url = build_url(
            f"{STATUTORY_INSTRUMENTS_API_BASE_V1}/BusinessItem/{quote(item_id)}",
            {"laidPaper": laid_paper},
        )
        return await get_result(url)

    @mcp.tool()
    async def get_laying_bodies() -> str:
        """List SI laying bodies | laying body, department, government organisation, JCSI |
        Get all bodies that can lay statutory instruments before Parliament |
        Returns list of laying bodies with IDs and names

        Returns:
            List of all laying bodies with IDs and names.
        """
        url = f"{STATUTORY_INSTRUMENTS_API_BASE_V1}/LayingBody"
        return await get_result(url)

    @mcp.tool()
    async def get_si_procedures() -> str:
        """List SI procedures | statutory instrument procedure, affirmative, negative, made affirmative |
        Get all statutory instrument procedures |
        Returns list of SI procedures with IDs and names

        Returns:
            List of all SI procedures with IDs and names.
        """
        url = f"{STATUTORY_INSTRUMENTS_API_BASE_V1}/Procedure"
        return await get_result(url)

    @mcp.tool()
    async def get_si_procedure(procedure_id: int) -> str:
        """Get SI procedure details | statutory instrument procedure, affirmative, negative |
        Get details of a specific SI procedure |
        Returns procedure details including workflow steps

        Args:
            procedure_id: The procedure ID (integer from list_si_procedures).

        Returns:
            Procedure details including workflow steps.
        """
        url = f"{STATUTORY_INSTRUMENTS_API_BASE_V1}/Procedure/{procedure_id}"
        return await get_result(url)

    @mcp.tool()
    async def search_proposed_negative_sis(
        name: str | None = None,
        recommended_for_procedure_change: bool | None = None,
        department_id: int | None = None,
        laying_body_id: int | None = None,
        skip: int = 0,
        take: int = 20,
    ) -> str:
        """Search proposed negative SIs | PNSI, proposed negative statutory instrument, sifting |
        Search proposed negative statutory instruments under parliamentary sifting |
        Returns list of PNSIs with details and sifting status

        Args:
            name: Optional. Filter by SI name.
            recommended_for_procedure_change: Optional. Filter to those recommended for procedure change.
            department_id: Optional. Filter by department ID.
            laying_body_id: Optional. Filter by laying body ID.
            skip: Number of records to skip (pagination, default 0).
            take: Number of records to return (default 20).

        Returns:
            List of proposed negative statutory instruments.
        """
        url = build_url(
            f"{STATUTORY_INSTRUMENTS_API_BASE_V1}/ProposedNegativeStatutoryInstrument",
            {
                "Name": name,
                "RecommendedForProcedureChange": recommended_for_procedure_change,
                "DepartmentId": department_id,
                "LayingBodyId": laying_body_id,
                "Skip": skip,
                "Take": take,
            },
        )
        return await get_result(url)

    @mcp.tool()
    async def get_proposed_negative_si(pnsi_id: str) -> str:
        """Get proposed negative SI details | PNSI, proposed negative statutory instrument, sifting |
        Get full details of a specific proposed negative SI |
        Returns PNSI details including sifting committee recommendations

        Args:
            pnsi_id: The PNSI ID (alphanumeric string from search results).

        Returns:
            Full PNSI details including sifting committee recommendations.
        """
        url = f"{STATUTORY_INSTRUMENTS_API_BASE_V1}/ProposedNegativeStatutoryInstrument/{quote(pnsi_id)}"
        return await get_result(url)

    @mcp.tool()
    async def get_proposed_negative_si_business_items(pnsi_id: str) -> str:
        """Get PNSI business items | proposed negative SI scrutiny, sifting committee, business items |
        Get business items for a proposed negative statutory instrument |
        Returns business items with dates and sifting outcomes

        Args:
            pnsi_id: The PNSI ID (alphanumeric string from search results).

        Returns:
            Business items with dates and sifting outcomes.
        """
        url = f"{STATUTORY_INSTRUMENTS_API_BASE_V1}/ProposedNegativeStatutoryInstrument/{quote(pnsi_id)}/BusinessItems"
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
