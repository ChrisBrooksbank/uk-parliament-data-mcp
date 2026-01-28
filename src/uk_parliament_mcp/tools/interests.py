"""Interests API tools for Register of Interests."""
from mcp.server.fastmcp import FastMCP

from uk_parliament_mcp.http_client import get_result

INTERESTS_API_BASE = "https://interests-api.parliament.uk/api/v1"


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
