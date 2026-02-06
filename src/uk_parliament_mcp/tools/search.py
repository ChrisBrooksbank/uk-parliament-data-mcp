"""Universal search tool — search across all Parliament APIs at once."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP


def register_tools(mcp: FastMCP) -> None:
    """Register universal search tools with the MCP server."""

    @mcp.tool()
    async def universal_search(
        query: str, scope: str = "", limit: int = 5, days: int = 30
    ) -> str:
        """Search across all Parliament APIs at once | universal search, cross-API, find anything | Use when you need to search broadly across Parliament data without knowing which specific API to use | Returns results grouped by source with counts

        Args:
            query: Search term to query across all Parliament sources.
            scope: Optional comma-separated source names to search (default: all). Valid: members, bills, committees, commons-votes, lords-votes, written-questions, written-statements, edms, hansard, treaties, statutory-instruments, erskine-may. Aliases: votes, questions, legislation.
            limit: Max results per source (default: 5).
            days: Hansard lookback in days (default: 30).
        """
        from uk_parliament_mcp.cli.search import _universal_search_async

        scope_list = [s.strip() for s in scope.split(",") if s.strip()] or None
        return await _universal_search_async(query, scope_list, None, limit, days)
