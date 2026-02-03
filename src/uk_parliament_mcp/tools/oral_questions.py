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

    @mcp.tool()
    async def get_early_day_motion(edm_id: int) -> str:
        """Get EDM details | early day motion, signatures, sponsors, full text |
        Get full text and signature details for an Early Day Motion |
        Returns EDM text, primary sponsor, supporters, signature count

        Args:
            edm_id: The EDM ID number.

        Returns:
            Full EDM details including text, sponsors, and signature count.
        """
        url = f"{ORAL_QUESTIONS_API_BASE}/EarlyDayMotion/{edm_id}"
        return await get_result(url)

    @mcp.tool()
    async def search_oral_questions(
        answering_body_id: int = 0,
        asking_member_id: int = 0,
        question_status: str = "",
        skip: int = 0,
        take: int = 20,
    ) -> str:
        """Search oral questions | PQs, question time, oral PQs, minister questions |
        Search oral parliamentary questions (not EDMs) |
        Returns list of oral questions with details

        Args:
            answering_body_id: Filter by department/body answering (0 for all).
            asking_member_id: Filter by member asking (0 for all).
            question_status: Filter by status (empty for all).
            skip: Number of results to skip.
            take: Number of results to return.

        Returns:
            List of oral questions matching the filters.
        """
        params = []
        if answering_body_id:
            params.append(f"parameters.answeringBodyId={answering_body_id}")
        if asking_member_id:
            params.append(f"parameters.askingMemberId={asking_member_id}")
        if question_status:
            params.append(f"parameters.questionStatus={quote(question_status)}")
        params.append(f"parameters.skip={skip}")
        params.append(f"parameters.take={take}")
        query = "&".join(params)
        url = f"{ORAL_QUESTIONS_API_BASE}/oralquestions/list?{query}"
        return await get_result(url)
