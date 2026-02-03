"""Written Questions API tools for questions and ministerial statements."""

from urllib.parse import quote

from mcp.server.fastmcp import FastMCP

from uk_parliament_mcp.config import WRITTEN_QUESTIONS_API_BASE
from uk_parliament_mcp.http_client import build_url, get_result


def register_tools(mcp: FastMCP) -> None:
    """Register written questions tools with the MCP server."""

    @mcp.tool()
    async def search_written_questions(
        search_term: str | None = None,
        asking_member_id: int | None = None,
        answering_body_id: int | None = None,
        answered: str | None = None,
        tabled_from: str | None = None,
        tabled_to: str | None = None,
        house: str | None = None,
        skip: int = 0,
        take: int = 20,
    ) -> str:
        """Search written parliamentary questions with comprehensive filtering | written questions, PQs, parliamentary questions, questions to ministers, government accountability | Use for researching MP activity, tracking government responses, analyzing ministerial accountability, or finding questions on specific topics | Returns questions with asking member, answering body, dates, and response status

        Args:
            search_term: Text to search for in question content.
            asking_member_id: Filter by the member ID who asked the question.
            answering_body_id: Filter by the government department that answered.
            answered: Filter by answer status: "Any", "Answered", or "Unanswered".
            tabled_from: Start date for when question was tabled (YYYY-MM-DD).
            tabled_to: End date for when question was tabled (YYYY-MM-DD).
            house: Filter by house: "Commons", "Lords", or "Bicameral".
            skip: Number of records to skip for pagination. Default: 0.
            take: Number of records to return. Default: 20.

        Returns:
            Written questions matching the search criteria with member, department, and answer details.
        """
        url = build_url(
            f"{WRITTEN_QUESTIONS_API_BASE}/writtenquestions/questions",
            {
                "searchTerm": search_term,
                "askingMemberId": asking_member_id,
                "answeringBodyId": answering_body_id,
                "answered": answered,
                "tabledWhenFrom": tabled_from,
                "tabledWhenTo": tabled_to,
                "house": house,
                "skip": skip,
                "take": take,
            },
        )
        return await get_result(url)

    @mcp.tool()
    async def get_written_question(
        question_id: int,
        expand_member: bool = True,
    ) -> str:
        """Get a specific written question by ID | written question details, PQ lookup, question by ID | Use when you have a question ID and need full details including the question text, answer, and member information | Returns complete question with asking member, answering body, question text, and answer

        Args:
            question_id: The unique ID of the written question.
            expand_member: Whether to include full member details. Default: True.

        Returns:
            Complete written question details including question text, answer, and member information.
        """
        url = build_url(
            f"{WRITTEN_QUESTIONS_API_BASE}/writtenquestions/questions/{question_id}",
            {"expandMember": expand_member},
        )
        return await get_result(url)

    @mcp.tool()
    async def get_written_question_by_uin(
        date: str,
        uin: str,
        expand_member: bool = True,
    ) -> str:
        """Get a written question by date and UIN (Unique Identification Number) | question by reference, UIN lookup, official question number | Use when you have a question's official UIN reference number to retrieve the full question details | Returns complete question with asking member, answering body, question text, and answer

        Args:
            date: Date the question was tabled in YYYY-MM-DD format.
            uin: The Unique Identification Number (UIN) of the question.
            expand_member: Whether to include full member details. Default: True.

        Returns:
            Complete written question details including question text, answer, and member information.
        """
        url = build_url(
            f"{WRITTEN_QUESTIONS_API_BASE}/writtenquestions/questions/{quote(date)}/{quote(uin)}",
            {"expandMember": expand_member},
        )
        return await get_result(url)

    @mcp.tool()
    async def search_written_statements(
        search_term: str | None = None,
        member_id: int | None = None,
        answering_body_id: int | None = None,
        made_from: str | None = None,
        made_to: str | None = None,
        house: str | None = None,
        skip: int = 0,
        take: int = 20,
    ) -> str:
        """Search written ministerial statements | written statements, ministerial statements, government announcements, policy statements | Use for tracking government announcements, researching policy statements, or finding ministerial communications on specific topics | Returns statements with minister, department, dates, and statement content

        Args:
            search_term: Text to search for in statement content.
            member_id: Filter by the minister ID who made the statement.
            answering_body_id: Filter by government department.
            made_from: Start date for when statement was made (YYYY-MM-DD).
            made_to: End date for when statement was made (YYYY-MM-DD).
            house: Filter by house: "Commons", "Lords", or "Bicameral".
            skip: Number of records to skip for pagination. Default: 0.
            take: Number of records to return. Default: 20.

        Returns:
            Written statements matching the search criteria with minister, department, and content.
        """
        url = build_url(
            f"{WRITTEN_QUESTIONS_API_BASE}/writtenstatements/statements",
            {
                "searchTerm": search_term,
                "memberId": member_id,
                "answeringBodyId": answering_body_id,
                "madeWhenFrom": made_from,
                "madeWhenTo": made_to,
                "house": house,
                "skip": skip,
                "take": take,
            },
        )
        return await get_result(url)

    @mcp.tool()
    async def get_written_statement(
        statement_id: int,
        expand_member: bool = True,
    ) -> str:
        """Get a specific written statement by ID | written statement details, statement lookup, ministerial statement by ID | Use when you have a statement ID and need full details including the statement text and minister information | Returns complete statement with minister, department, and full statement content

        Args:
            statement_id: The unique ID of the written statement.
            expand_member: Whether to include full member details. Default: True.

        Returns:
            Complete written statement details including statement text and minister information.
        """
        url = build_url(
            f"{WRITTEN_QUESTIONS_API_BASE}/writtenstatements/statements/{statement_id}",
            {"expandMember": expand_member},
        )
        return await get_result(url)

    @mcp.tool()
    async def get_written_statement_by_uin(
        date: str,
        uin: str,
        expand_member: bool = True,
    ) -> str:
        """Get a written statement by date and UIN (Unique Identification Number) | statement by reference, UIN lookup, official statement number | Use when you have a statement's official UIN reference number to retrieve the full statement details | Returns complete statement with minister, department, and full statement content

        Args:
            date: Date the statement was made in YYYY-MM-DD format.
            uin: The Unique Identification Number (UIN) of the statement.
            expand_member: Whether to include full member details. Default: True.

        Returns:
            Complete written statement details including statement text and minister information.
        """
        url = build_url(
            f"{WRITTEN_QUESTIONS_API_BASE}/writtenstatements/statements/{quote(date)}/{quote(uin)}",
            {"expandMember": expand_member},
        )
        return await get_result(url)

    @mcp.tool()
    async def get_daily_reports(
        date_from: str | None = None,
        date_to: str | None = None,
        house: str | None = None,
        skip: int = 0,
        take: int = 20,
    ) -> str:
        """Get daily reports of written questions and answers | daily reports, question reports, answer summaries, daily digest | Use for getting overview of parliamentary question activity on specific dates or date ranges | Returns daily reports with question and answer summaries

        Args:
            date_from: Start date for reports (YYYY-MM-DD).
            date_to: End date for reports (YYYY-MM-DD).
            house: Filter by house: "Commons", "Lords", or "Bicameral".
            skip: Number of records to skip for pagination. Default: 0.
            take: Number of records to return. Default: 20.

        Returns:
            Daily reports with question and answer activity summaries.
        """
        url = build_url(
            f"{WRITTEN_QUESTIONS_API_BASE}/dailyreports/dailyreports",
            {
                "dateFrom": date_from,
                "dateTo": date_to,
                "house": house,
                "skip": skip,
                "take": take,
            },
        )
        return await get_result(url)
