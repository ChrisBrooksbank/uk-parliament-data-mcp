"""Now API tools for live chamber activity."""
from mcp.server.fastmcp import FastMCP

from uk_parliament_mcp.http_client import get_result

NOW_API_BASE = "https://now-api.parliament.uk/api"


def register_tools(mcp: FastMCP) -> None:
    """Register now tools with the MCP server."""

    @mcp.tool()
    async def happening_now_in_commons() -> str:
        """Get live information about what's currently happening in the House of Commons chamber. Use when you want real-time updates on parliamentary business, current debates, or voting activity.

        Returns:
            Live information about current Commons chamber activity.
        """
        url = f"{NOW_API_BASE}/Message/message/CommonsMain/current"
        return await get_result(url)

    @mcp.tool()
    async def happening_now_in_lords() -> str:
        """Get live information about what's currently happening in the House of Lords chamber. Use when you want real-time updates on Lords business, current debates, or voting activity.

        Returns:
            Live information about current Lords chamber activity.
        """
        url = f"{NOW_API_BASE}/Message/message/LordsMain/current"
        return await get_result(url)
