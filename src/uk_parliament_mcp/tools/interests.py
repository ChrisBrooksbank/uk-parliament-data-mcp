"""Interests API tools for Register of Interests."""

from mcp.server.fastmcp import FastMCP

from uk_parliament_mcp.config import INTERESTS_API_BASE
from uk_parliament_mcp.http_client import get_result


def register_tools(mcp: FastMCP) -> None:
    """Register interests tools with the MCP server."""

    @mcp.tool()
    async def search_roi(member_id: int) -> str:
        """Search member's Register of Interests for financial and business declarations | register of interests, ROI, financial interests, conflicts of interest, directorships, consultancies, gifts, external roles, transparency | Use for investigating potential conflicts, researching member finances, or checking declared interests | Returns declared interests including directorships, consultancies, gifts, and other financial interests

        Args:
            member_id: Parliament member ID. Required: get from member search first. Returns all declared interests.

        Returns:
            Declared interests including directorships, consultancies, gifts, and other financial interests.
        """
        url = f"{INTERESTS_API_BASE}/Interests/?MemberId={member_id}"
        return await get_result(url)

    @mcp.tool()
    async def interests_categories() -> str:
        """Get categories of interests that MPs and Lords must declare in the Register of Interests. Use when you need to understand what types of financial or other interests parliamentarians must declare.

        Returns:
            Categories of interests that must be declared.
        """
        url = f"{INTERESTS_API_BASE}/Categories"
        return await get_result(url)

    @mcp.tool()
    async def get_registers_of_interests() -> str:
        """Get list of published Registers of Interests. Use when you need to see all available interest registers or understand the transparency framework for parliamentary interests.

        Returns:
            List of published Registers of Interests.
        """
        url = f"{INTERESTS_API_BASE}/Registers"
        return await get_result(url)

    @mcp.tool()
    async def get_interest_category(category_id: int) -> str:
        """Get a specific interest category by ID | register of interests, interest category, declaration type | Use to get details of a specific interest category | Returns category details

        Args:
            category_id: Interest category ID.

        Returns:
            Details of the specified interest category.
        """
        url = f"{INTERESTS_API_BASE}/Categories/{category_id}"
        return await get_result(url)

    @mcp.tool()
    async def get_interest_by_id(interest_id: int) -> str:
        """Get a specific registered interest by ID | register of interests, financial interest, declaration | Use to retrieve a specific interest declaration by its ID | Returns interest details

        Args:
            interest_id: Interest record ID.

        Returns:
            Details of the specified interest declaration.
        """
        url = f"{INTERESTS_API_BASE}/Interests/{interest_id}"
        return await get_result(url)

    @mcp.tool()
    async def get_register_by_id(register_id: int) -> str:
        """Get a specific Register of Interests by ID | register of interests, published register, transparency | Use to retrieve a specific published interest register by its ID | Returns register details

        Args:
            register_id: Register ID.

        Returns:
            Details of the specified Register of Interests.
        """
        url = f"{INTERESTS_API_BASE}/Registers/{register_id}"
        return await get_result(url)
