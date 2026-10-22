"""Web Search API tools for searching the parliament.uk website."""

from mcp.server.fastmcp import FastMCP

from uk_parliament_mcp.config import WEBSEARCH_API_BASE
from uk_parliament_mcp.http_client import build_url, get_result


def register_tools(mcp: FastMCP) -> None:
    """Register Web Search tools with the MCP server."""

    @mcp.tool()
    async def search_parliament_website(
        search_terms: str, start: int | None = None, take: int | None = None
    ) -> str:
        """Search the parliament.uk website | site-wide search, web pages, research briefings, Commons Library, POST, publications, guides | Use for free-text discovery of any parliament.uk content that the structured APIs don't cover, such as Commons Library briefings or explainers | Returns total result count and a page of results with title, description (matches in <strong> tags), url and tags. See also: search_parliament, search_hansard.

        Args:
            search_terms: Terms to search for (e.g. 'climate change', 'sitting hours').
            start: Position of the first result to return (default 1). Page by adding take to it.
            take: Number of results per page (default and maximum 20).

        Returns:
            Search results from the parliament.uk website with title, description, url and tags.
        """
        url = build_url(
            f"{WEBSEARCH_API_BASE}/WebSearch",
            {"searchTerms": search_terms, "start": start, "take": take},
        )
        return await get_result(url)
