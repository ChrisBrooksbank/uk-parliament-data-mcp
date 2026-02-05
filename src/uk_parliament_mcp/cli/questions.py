"""Questions CLI commands for EDMs, oral questions, and written questions."""

from __future__ import annotations

from urllib.parse import quote

import typer

from uk_parliament_mcp.cli.formatters import OutputFormat
from uk_parliament_mcp.cli.utils import echo_utf8, format_output, run_async
from uk_parliament_mcp.config import ORAL_QUESTIONS_API_BASE, WRITTEN_QUESTIONS_API_BASE
from uk_parliament_mcp.http_client import build_url, get_result

app = typer.Typer(help="Parliamentary questions, EDMs, and statements")


# EDM Commands (Early Day Motions)
@app.command("recent-edms")
def get_recently_tabled_edms(
    take: int = typer.Option(10, "--take", help="Number of EDMs to return"),
    pretty: bool = typer.Option(False, "--pretty", "-p", help="Pretty-print JSON output"),
    data_only: bool = typer.Option(False, "--data-only", "-d", help="Return data only"),
    output_format: OutputFormat = typer.Option(
        OutputFormat.JSON, "--format", "-f", help="Output format: json, table, markdown"
    ),
) -> None:
    """
    Get recently tabled Early Day Motions (EDMs).

    Early Day Motions are formal political statements used by MPs to express opinions,
    build cross-party support, and raise issues. Use for tracking political sentiment.
    """
    url = f"{ORAL_QUESTIONS_API_BASE}/EarlyDayMotions/list?parameters.orderBy=DateTabledDesc&skip=0&take={take}"
    result = run_async(get_result(url))
    echo_utf8(format_output(result, pretty, data_only, output_format))


@app.command("search-edms")
def search_early_day_motions(
    search_term: str | None = typer.Option(None, "--search", help="Search term for EDM content"),
    member_id: int | None = typer.Option(None, "--member-id", help="Filter by member ID"),
    include_sponsored_by_member: bool | None = typer.Option(
        None, "--include-sponsored", help="Include EDMs where member is sponsor"
    ),
    statuses: str | None = typer.Option(
        None, "--status", help="Status: 'Published' or 'Withdrawn'"
    ),
    tabled_start_date: str | None = typer.Option(
        None, "--tabled-from", help="Tabled on/after (YYYY-MM-DD)"
    ),
    tabled_end_date: str | None = typer.Option(
        None, "--tabled-to", help="Tabled on/before (YYYY-MM-DD)"
    ),
    is_prayer: bool | None = typer.Option(None, "--prayer", help="Filter to prayers against SIs"),
    order_by: str | None = typer.Option(
        None,
        "--order-by",
        help="Order: DateTabledAsc/Desc, TitleAsc/Desc, SignatureCountAsc/Desc",
    ),
    skip: int = typer.Option(0, "--skip", help="Results to skip (pagination)"),
    take: int = typer.Option(25, "--take", help="Results to return"),
    pretty: bool = typer.Option(False, "--pretty", "-p", help="Pretty-print JSON output"),
    data_only: bool = typer.Option(False, "--data-only", "-d", help="Return data only"),
    output_format: OutputFormat = typer.Option(
        OutputFormat.JSON, "--format", "-f", help="Output format: json, table, markdown"
    ),
) -> None:
    """
    Search Early Day Motions by topic, member, or status.

    Use to find motions on specific issues, by specific members, or to track
    withdrawn motions or prayers against Statutory Instruments.
    """
    url = build_url(
        f"{ORAL_QUESTIONS_API_BASE}/EarlyDayMotions/list",
        {
            "parameters.searchTerm": search_term,
            "parameters.memberId": member_id,
            "parameters.includeSponsoredByMember": include_sponsored_by_member,
            "parameters.statuses": statuses,
            "parameters.tabledStartDate": tabled_start_date,
            "parameters.tabledEndDate": tabled_end_date,
            "parameters.isPrayer": is_prayer,
            "parameters.orderBy": order_by,
            "parameters.skip": skip,
            "parameters.take": take,
        },
    )
    result = run_async(get_result(url))
    echo_utf8(format_output(result, pretty, data_only, output_format))


@app.command("get-edm")
def get_early_day_motion(
    edm_id: int = typer.Argument(..., help="EDM ID number"),
    pretty: bool = typer.Option(False, "--pretty", "-p", help="Pretty-print JSON output"),
    data_only: bool = typer.Option(False, "--data-only", "-d", help="Return data only"),
    output_format: OutputFormat = typer.Option(
        OutputFormat.JSON, "--format", "-f", help="Output format: json, table, markdown"
    ),
) -> None:
    """
    Get full details of an Early Day Motion by ID.

    Returns complete EDM text, primary sponsor, supporters, and signature count.
    """
    url = f"{ORAL_QUESTIONS_API_BASE}/EarlyDayMotion/{edm_id}"
    result = run_async(get_result(url))
    echo_utf8(format_output(result, pretty, data_only, output_format))


# Oral Questions Commands
@app.command("oral-question-times")
def search_oral_question_times(
    answering_date_start: str = typer.Argument(..., help="Start date (YYYY-MM-DD)"),
    answering_date_end: str = typer.Argument(..., help="End date (YYYY-MM-DD)"),
    pretty: bool = typer.Option(False, "--pretty", "-p", help="Pretty-print JSON output"),
    data_only: bool = typer.Option(False, "--data-only", "-d", help="Return data only"),
    output_format: OutputFormat = typer.Option(
        OutputFormat.JSON, "--format", "-f", help="Output format: json, table, markdown"
    ),
) -> None:
    """
    Get scheduled oral question times for ministers.

    Use to know when specific departments will answer questions or when
    particular topics will be discussed.
    """
    url = f"{ORAL_QUESTIONS_API_BASE}/oralquestiontimes/list?parameters.answeringDateStart={quote(answering_date_start)}&parameters.answeringDateEnd={quote(answering_date_end)}"
    result = run_async(get_result(url))
    echo_utf8(format_output(result, pretty, data_only, output_format))


@app.command("search-oral")
def search_oral_questions(
    answering_body_id: int = typer.Option(0, "--body-id", help="Department/body answering (0=all)"),
    asking_member_id: int = typer.Option(0, "--member-id", help="Member asking (0=all)"),
    question_status: str = typer.Option("", "--status", help="Question status (empty=all)"),
    skip: int = typer.Option(0, "--skip", help="Results to skip (pagination)"),
    take: int = typer.Option(20, "--take", help="Results to return"),
    pretty: bool = typer.Option(False, "--pretty", "-p", help="Pretty-print JSON output"),
    data_only: bool = typer.Option(False, "--data-only", "-d", help="Return data only"),
    output_format: OutputFormat = typer.Option(
        OutputFormat.JSON, "--format", "-f", help="Output format: json, table, markdown"
    ),
) -> None:
    """
    Search oral parliamentary questions (not EDMs).

    Use to find oral questions by department, member, or status.
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
    result = run_async(get_result(url))
    echo_utf8(format_output(result, pretty, data_only, output_format))


# Written Questions Commands
@app.command("search-written")
def search_written_questions(
    search_term: str | None = typer.Option(None, "--search", help="Search question content"),
    asking_member_id: int | None = typer.Option(
        None, "--asking-member", help="Filter by asking member ID"
    ),
    answering_body_id: int | None = typer.Option(
        None, "--answering-body", help="Filter by department"
    ),
    answered: str | None = typer.Option(None, "--answered", help="Any/Answered/Unanswered"),
    tabled_from: str | None = typer.Option(None, "--tabled-from", help="Tabled from (YYYY-MM-DD)"),
    tabled_to: str | None = typer.Option(None, "--tabled-to", help="Tabled to (YYYY-MM-DD)"),
    house: str | None = typer.Option(None, "--house", help="Commons/Lords/Bicameral"),
    skip: int = typer.Option(0, "--skip", help="Results to skip (pagination)"),
    take: int = typer.Option(20, "--take", help="Results to return"),
    pretty: bool = typer.Option(False, "--pretty", "-p", help="Pretty-print JSON output"),
    data_only: bool = typer.Option(False, "--data-only", "-d", help="Return data only"),
    output_format: OutputFormat = typer.Option(
        OutputFormat.JSON, "--format", "-f", help="Output format: json, table, markdown"
    ),
) -> None:
    """
    Search written parliamentary questions.

    Use for researching MP activity, tracking government responses,
    analyzing ministerial accountability, or finding questions on topics.
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
    result = run_async(get_result(url))
    echo_utf8(format_output(result, pretty, data_only, output_format))


@app.command("get-written-question")
def get_written_question(
    question_id: int = typer.Argument(..., help="Written question ID"),
    expand_member: bool = typer.Option(
        True, "--expand-member/--no-expand", help="Include member details"
    ),
    pretty: bool = typer.Option(False, "--pretty", "-p", help="Pretty-print JSON output"),
    data_only: bool = typer.Option(False, "--data-only", "-d", help="Return data only"),
    output_format: OutputFormat = typer.Option(
        OutputFormat.JSON, "--format", "-f", help="Output format: json, table, markdown"
    ),
) -> None:
    """
    Get a specific written question by ID.

    Returns complete question with asking member, answering body, question text, and answer.
    """
    url = build_url(
        f"{WRITTEN_QUESTIONS_API_BASE}/writtenquestions/questions/{question_id}",
        {"expandMember": expand_member},
    )
    result = run_async(get_result(url))
    echo_utf8(format_output(result, pretty, data_only, output_format))


@app.command("get-written-question-by-uin")
def get_written_question_by_uin(
    date: str = typer.Argument(..., help="Date question was tabled (YYYY-MM-DD)"),
    uin: str = typer.Argument(..., help="Unique Identification Number (UIN)"),
    expand_member: bool = typer.Option(
        True, "--expand-member/--no-expand", help="Include member details"
    ),
    pretty: bool = typer.Option(False, "--pretty", "-p", help="Pretty-print JSON output"),
    data_only: bool = typer.Option(False, "--data-only", "-d", help="Return data only"),
    output_format: OutputFormat = typer.Option(
        OutputFormat.JSON, "--format", "-f", help="Output format: json, table, markdown"
    ),
) -> None:
    """
    Get a written question by date and UIN.

    Use when you have a question's official UIN reference number.
    """
    url = build_url(
        f"{WRITTEN_QUESTIONS_API_BASE}/writtenquestions/questions/{quote(date)}/{quote(uin)}",
        {"expandMember": expand_member},
    )
    result = run_async(get_result(url))
    echo_utf8(format_output(result, pretty, data_only, output_format))


# Written Statements Commands
@app.command("search-statements")
def search_written_statements(
    search_term: str | None = typer.Option(None, "--search", help="Search statement content"),
    member_id: int | None = typer.Option(None, "--member-id", help="Filter by minister ID"),
    answering_body_id: int | None = typer.Option(None, "--body-id", help="Filter by department"),
    made_from: str | None = typer.Option(None, "--made-from", help="Made from (YYYY-MM-DD)"),
    made_to: str | None = typer.Option(None, "--made-to", help="Made to (YYYY-MM-DD)"),
    house: str | None = typer.Option(None, "--house", help="Commons/Lords/Bicameral"),
    skip: int = typer.Option(0, "--skip", help="Results to skip (pagination)"),
    take: int = typer.Option(20, "--take", help="Results to return"),
    pretty: bool = typer.Option(False, "--pretty", "-p", help="Pretty-print JSON output"),
    data_only: bool = typer.Option(False, "--data-only", "-d", help="Return data only"),
    output_format: OutputFormat = typer.Option(
        OutputFormat.JSON, "--format", "-f", help="Output format: json, table, markdown"
    ),
) -> None:
    """
    Search written ministerial statements.

    Use for tracking government announcements, researching policy statements,
    or finding ministerial communications on specific topics.
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
    result = run_async(get_result(url))
    echo_utf8(format_output(result, pretty, data_only, output_format))


@app.command("get-statement")
def get_written_statement(
    statement_id: int = typer.Argument(..., help="Written statement ID"),
    expand_member: bool = typer.Option(
        True, "--expand-member/--no-expand", help="Include member details"
    ),
    pretty: bool = typer.Option(False, "--pretty", "-p", help="Pretty-print JSON output"),
    data_only: bool = typer.Option(False, "--data-only", "-d", help="Return data only"),
    output_format: OutputFormat = typer.Option(
        OutputFormat.JSON, "--format", "-f", help="Output format: json, table, markdown"
    ),
) -> None:
    """
    Get a specific written statement by ID.

    Returns complete statement with minister, department, and full statement content.
    """
    url = build_url(
        f"{WRITTEN_QUESTIONS_API_BASE}/writtenstatements/statements/{statement_id}",
        {"expandMember": expand_member},
    )
    result = run_async(get_result(url))
    echo_utf8(format_output(result, pretty, data_only, output_format))


@app.command("get-statement-by-uin")
def get_written_statement_by_uin(
    date: str = typer.Argument(..., help="Date statement was made (YYYY-MM-DD)"),
    uin: str = typer.Argument(..., help="Unique Identification Number (UIN)"),
    expand_member: bool = typer.Option(
        True, "--expand-member/--no-expand", help="Include member details"
    ),
    pretty: bool = typer.Option(False, "--pretty", "-p", help="Pretty-print JSON output"),
    data_only: bool = typer.Option(False, "--data-only", "-d", help="Return data only"),
    output_format: OutputFormat = typer.Option(
        OutputFormat.JSON, "--format", "-f", help="Output format: json, table, markdown"
    ),
) -> None:
    """
    Get a written statement by date and UIN.

    Use when you have a statement's official UIN reference number.
    """
    url = build_url(
        f"{WRITTEN_QUESTIONS_API_BASE}/writtenstatements/statements/{quote(date)}/{quote(uin)}",
        {"expandMember": expand_member},
    )
    result = run_async(get_result(url))
    echo_utf8(format_output(result, pretty, data_only, output_format))


@app.command("daily-reports")
def get_daily_reports(
    date_from: str | None = typer.Option(None, "--from", help="Start date (YYYY-MM-DD)"),
    date_to: str | None = typer.Option(None, "--to", help="End date (YYYY-MM-DD)"),
    house: str | None = typer.Option(None, "--house", help="Commons/Lords/Bicameral"),
    skip: int = typer.Option(0, "--skip", help="Results to skip (pagination)"),
    take: int = typer.Option(20, "--take", help="Results to return"),
    pretty: bool = typer.Option(False, "--pretty", "-p", help="Pretty-print JSON output"),
    data_only: bool = typer.Option(False, "--data-only", "-d", help="Return data only"),
    output_format: OutputFormat = typer.Option(
        OutputFormat.JSON, "--format", "-f", help="Output format: json, table, markdown"
    ),
) -> None:
    """
    Get daily reports of written questions and answers.

    Use for overview of parliamentary question activity on specific dates or ranges.
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
    result = run_async(get_result(url))
    echo_utf8(format_output(result, pretty, data_only, output_format))
