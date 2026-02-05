"""Erskine May API tools for parliamentary procedure."""

from urllib.parse import quote

from mcp.server.fastmcp import FastMCP

from uk_parliament_mcp.config import ERSKINE_MAY_API_BASE
from uk_parliament_mcp.http_client import build_url, get_result


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

    @mcp.tool()
    async def get_erskine_may_parts() -> str:
        """List all parts of Erskine May | procedure structure, table of contents | Use to navigate the 6 major parts of parliamentary procedure | Returns list of all parts with titles and descriptions.

        Returns:
            List of all 6 parts of Erskine May with titles.
        """
        url = f"{ERSKINE_MAY_API_BASE}/Part"
        return await get_result(url)

    @mcp.tool()
    async def get_erskine_may_part(part_number: int) -> str:
        """Get a specific part of Erskine May | procedure structure, chapters | Use to explore chapters within a part | Returns part with title, description, and list of chapters.

        Args:
            part_number: Part number (1-6).

        Returns:
            Part details with chapter list.
        """
        url = f"{ERSKINE_MAY_API_BASE}/Part/{part_number}"
        return await get_result(url)

    @mcp.tool()
    async def get_erskine_may_chapter(chapter_number: int) -> str:
        """Get a specific chapter of Erskine May | procedure sections, chapter content | Use to explore sections within a chapter | Returns chapter with title, description, and list of sections.

        Args:
            chapter_number: Chapter number.

        Returns:
            Chapter details with section list.
        """
        url = f"{ERSKINE_MAY_API_BASE}/Chapter/{chapter_number}"
        return await get_result(url)

    @mcp.tool()
    async def get_erskine_may_section(section_id: int) -> str:
        """Get full content of an Erskine May section | procedure text, rules, precedents | Use to read the actual procedural content | Returns section with full text content and footnotes.

        Args:
            section_id: Section ID (from chapter or navigation).

        Returns:
            Section with full text content.
        """
        url = f"{ERSKINE_MAY_API_BASE}/Section/{section_id}"
        return await get_result(url)

    @mcp.tool()
    async def get_erskine_may_section_relative(section_id: int, step: int) -> str:
        """Navigate to a section relative to current position | procedure navigation, next section, previous section | Use to move through sections sequentially | Returns section at offset from current section.

        Args:
            section_id: Current section ID.
            step: Step offset (e.g. 1 for next, -1 for previous).

        Returns:
            Section at the relative position.
        """
        url = f"{ERSKINE_MAY_API_BASE}/Section/{section_id},{step}"
        return await get_result(url)

    @mcp.tool()
    async def get_erskine_may_paragraph(reference: str) -> str:
        """Look up a specific paragraph by reference number | paragraph citation, specific rule | Use when you have a paragraph reference like '4.5' | Returns the specific paragraph content.

        Args:
            reference: Paragraph reference (e.g. '4.5', '12.3').

        Returns:
            Paragraph content for the reference.
        """
        url = f"{ERSKINE_MAY_API_BASE}/Search/Paragraph/{quote(reference)}"
        return await get_result(url)

    @mcp.tool()
    async def browse_erskine_may_index(
        start_letter: str | None = None,
        skip: int = 0,
        take: int = 30,
    ) -> str:
        """Browse the Erskine May index alphabetically | index terms, procedure topics | Use to discover topics by browsing alphabetically | Returns index terms starting with given letter.

        Args:
            start_letter: Starting letter to browse from (A-Z), or None for all.
            skip: Number of results to skip for pagination (default 0).
            take: Number of results to return (default 30).

        Returns:
            Index terms starting with the given letter.
        """
        url = build_url(
            f"{ERSKINE_MAY_API_BASE}/IndexTerm/browse",
            {
                "startLetter": start_letter,
                "skip": skip,
                "take": take,
            },
        )
        return await get_result(url)

    @mcp.tool()
    async def get_erskine_may_index_term(index_term_id: int) -> str:
        """Get details of an index term | procedure topic, references | Use after browsing index to get term details | Returns index term with all paragraph references.

        Args:
            index_term_id: Index term ID (from browse_erskine_may_index).

        Returns:
            Index term with paragraph references.
        """
        url = f"{ERSKINE_MAY_API_BASE}/IndexTerm/{index_term_id}"
        return await get_result(url)

    @mcp.tool()
    async def search_erskine_may_index(
        search_term: str,
        skip: int = 0,
        take: int = 30,
    ) -> str:
        """Search the Erskine May index for terms | index search, find topics | Use to find index entries by keyword | Returns matching index terms.

        Args:
            search_term: Term to search for in the index.
            skip: Number of results to skip for pagination (default 0).
            take: Number of results to return (default 30).

        Returns:
            Index terms matching the search.
        """
        url = build_url(
            f"{ERSKINE_MAY_API_BASE}/Search/IndexTermSearchResults/{quote(search_term)}",
            {
                "skip": skip,
                "take": take,
            },
        )
        return await get_result(url)

    @mcp.tool()
    async def search_erskine_may_sections(
        search_term: str,
        skip: int = 0,
        take: int = 30,
    ) -> str:
        """Search Erskine May section titles | section search, find by title | Use to find sections by title rather than content | Returns sections with matching titles.

        Args:
            search_term: Term to search for in section titles.
            skip: Number of results to skip for pagination (default 0).
            take: Number of results to return (default 30).

        Returns:
            Sections with matching titles.
        """
        url = build_url(
            f"{ERSKINE_MAY_API_BASE}/Search/SectionSearchResults/{quote(search_term)}",
            {
                "skip": skip,
                "take": take,
            },
        )
        return await get_result(url)
