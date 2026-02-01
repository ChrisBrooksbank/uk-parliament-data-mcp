"""Oral Questions API tools for EDMs and question times."""

from urllib.parse import quote

from mcp.server.fastmcp import FastMCP

from uk_parliament_mcp.config import ORAL_QUESTIONS_API_BASE
from uk_parliament_mcp.http_client import get_result


def register_tools(mcp: FastMCP) -> None:
    """Register oral questions tools with the MCP server."""

    @mcp.tool()
    async def get_recently_tabled_edms(take: int = 10) -> str:
        """Get recently tabled Early Day Motions - formal political statements | EDMs, political motions, backbench initiatives, MP opinions, parliamentary statements, political positions, cross-party support | Use for tracking political sentiment, finding MP stances on issues, monitoring backbench activity, or researching political movements | Returns recent EDMs with titles, sponsors, supporters, and tabling dates | Data freshness: updated daily

        Args:
            take: Number of EDMs to return. Default: 10, recommended max: 50. Recent motions returned first.

        Returns:
            Recent EDMs with titles, sponsors, supporters, and tabling dates.
        """
        url = f"{ORAL_QUESTIONS_API_BASE}/EarlyDayMotions/list?parameters.orderBy=DateTabledDesc&skip=0&take={take}"
        return await get_result(url)

    @mcp.tool()
    async def search_early_day_motions(search_term: str) -> str:
        """Search Early Day Motions by topic or keyword. Use when researching MP opinions on specific issues or finding motions related to particular subjects. EDMs often reflect backbench MP concerns.

        Args:
            search_term: Search term for EDM topics or content (e.g. 'climate change', 'NHS funding').

        Returns:
            EDMs matching the search term.
        """
        url = f"{ORAL_QUESTIONS_API_BASE}/EarlyDayMotions/list?parameters.searchTerm={quote(search_term)}"
        return await get_result(url)

    @mcp.tool()
    async def search_oral_question_times(
        answering_date_start: str,
        answering_date_end: str,
    ) -> str:
        """Get scheduled oral question times for ministers in Parliament. Use when you want to know when specific departments will answer questions or when particular topics will be discussed.

        Args:
            answering_date_start: Start date for question times in YYYY-MM-DD format.
            answering_date_end: End date for question times in YYYY-MM-DD format.

        Returns:
            Scheduled oral question times in the date range.
        """
        url = f"{ORAL_QUESTIONS_API_BASE}/oralquestiontimes/list?parameters.answeringDateStart={quote(answering_date_start)}&parameters.answeringDateEnd={quote(answering_date_end)}"
        return await get_result(url)
