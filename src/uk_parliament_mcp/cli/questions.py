"""Questions CLI commands for EDMs, oral questions, and written questions."""

from __future__ import annotations

from urllib.parse import quote

import typer

from uk_parliament_mcp.cli.formatters import OutputFormat
from uk_parliament_mcp.cli.pagination import (
    DAILY_REPORTS_PAGINATION,
    ORAL_QUESTIONS_PAGINATION,
    WRITTEN_QUESTIONS_PAGINATION,
    WRITTEN_STATEMENTS_PAGINATION,
    paginate_request,
)
from uk_parliament_mcp.cli.utils import echo_utf8, format_output, run_async
from uk_parliament_mcp.config import ORAL_QUESTIONS_API_BASE, WRITTEN_QUESTIONS_API_BASE
from uk_parliament_mcp.http_client import build_url, get_result

app = typer.Typer(help="Parliamentary questions, EDMs, and statements", no_args_is_help=True)


# EDM Commands (Early Day Motions)
@app.command("recent-edms")
def get_recently_tabled_edms(
    take: int = typer.Option(10, "--take", help="Number of EDMs to return"),
    pretty: bool = typer.Option(False, "--pretty", "-p", help="Pretty-print JSON output"),
    data_only: bool = typer.Option(
        True, "--data-only", "-d", help="Return data only (use --no-data-only for wrapper)"
    ),
    output_format: OutputFormat = typer.Option(
        OutputFormat.AUTO, "--format", "-f", help="Output format: json, table, markdown, csv, auto"
    ),
    raw: bool = typer.Option(False, "--raw", help="Output full wrapper JSON (url + data)"),
    fields: str | None = typer.Option(
        None, "--fields", help="Comma-separated field paths for columns"
    ),
) -> None:
    """
    Get recently tabled Early Day Motions (EDMs).

    Early Day Motions are formal political statements used by MPs to express opinions,
    build cross-party support, and raise issues. Use for tracking political sentiment.
    """
    url = f"{ORAL_QUESTIONS_API_BASE}/EarlyDayMotions/list?parameters.orderBy=DateTabledDesc&skip=0&take={take}"
    result = run_async(get_result(url))
    echo_utf8(format_output(result, pretty, data_only, output_format, fields, raw))


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
    edm_ids: str | None = typer.Option(
        None, "--edm-ids", help="Comma-separated EDM IDs to filter by"
    ),
    uin_with_amendment_suffix: str | None = typer.Option(
        None, "--uin", help="EDM UIN with optional amendment suffix"
    ),
    current_status_date_start: str | None = typer.Option(
        None, "--status-date-from", help="Current status date from (YYYY-MM-DD)"
    ),
    current_status_date_end: str | None = typer.Option(
        None, "--status-date-to", help="Current status date to (YYYY-MM-DD)"
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
    data_only: bool = typer.Option(
        True, "--data-only", "-d", help="Return data only (use --no-data-only for wrapper)"
    ),
    output_format: OutputFormat = typer.Option(
        OutputFormat.AUTO, "--format", "-f", help="Output format: json, table, markdown, csv, auto"
    ),
    raw: bool = typer.Option(False, "--raw", help="Output full wrapper JSON (url + data)"),
    fields: str | None = typer.Option(
        None, "--fields", help="Comma-separated field paths for columns"
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
            "parameters.edmIds": edm_ids,
            "parameters.uINWithAmendmentSuffix": uin_with_amendment_suffix,
            "parameters.currentStatusDateStart": current_status_date_start,
            "parameters.currentStatusDateEnd": current_status_date_end,
            "parameters.tabledStartDate": tabled_start_date,
            "parameters.tabledEndDate": tabled_end_date,
            "parameters.isPrayer": is_prayer,
            "parameters.orderBy": order_by,
            "parameters.skip": skip,
            "parameters.take": take,
        },
    )
    result = run_async(
        paginate_request(url, ORAL_QUESTIONS_PAGINATION, desired_total=take, start_skip=skip)
    )
    echo_utf8(format_output(result, pretty, data_only, output_format, fields, raw))


@app.command("get-edm")
def get_early_day_motion(
    edm_id: int = typer.Argument(..., help="EDM ID number"),
    pretty: bool = typer.Option(False, "--pretty", "-p", help="Pretty-print JSON output"),
    data_only: bool = typer.Option(
        True, "--data-only", "-d", help="Return data only (use --no-data-only for wrapper)"
    ),
    output_format: OutputFormat = typer.Option(
        OutputFormat.AUTO, "--format", "-f", help="Output format: json, table, markdown, csv, auto"
    ),
    raw: bool = typer.Option(False, "--raw", help="Output full wrapper JSON (url + data)"),
    fields: str | None = typer.Option(
        None, "--fields", help="Comma-separated field paths for columns"
    ),
) -> None:
    """
    Get full details of an Early Day Motion by ID.

    Returns complete EDM text, primary sponsor, supporters, and signature count.
    """
    url = f"{ORAL_QUESTIONS_API_BASE}/EarlyDayMotion/{edm_id}"
    result = run_async(get_result(url))
    echo_utf8(format_output(result, pretty, data_only, output_format, fields, raw))


# Oral Questions Commands
@app.command("oral-question-times")
def search_oral_question_times(
    answering_date_start: str = typer.Argument(..., help="Start date (YYYY-MM-DD)"),
    answering_date_end: str = typer.Argument(..., help="End date (YYYY-MM-DD)"),
    deadline_date_start: str | None = typer.Option(
        None, "--deadline-from", help="Deadline start date (YYYY-MM-DD)"
    ),
    deadline_date_end: str | None = typer.Option(
        None, "--deadline-to", help="Deadline end date (YYYY-MM-DD)"
    ),
    oral_question_time_id: int | None = typer.Option(
        None, "--question-time-id", help="Filter by oral question time ID"
    ),
    answering_body_ids: str | None = typer.Option(
        None, "--body-ids", help="Comma-separated answering body IDs"
    ),
    pretty: bool = typer.Option(False, "--pretty", "-p", help="Pretty-print JSON output"),
    data_only: bool = typer.Option(
        True, "--data-only", "-d", help="Return data only (use --no-data-only for wrapper)"
    ),
    output_format: OutputFormat = typer.Option(
        OutputFormat.AUTO, "--format", "-f", help="Output format: json, table, markdown, csv, auto"
    ),
    raw: bool = typer.Option(False, "--raw", help="Output full wrapper JSON (url + data)"),
    fields: str | None = typer.Option(
        None, "--fields", help="Comma-separated field paths for columns"
    ),
) -> None:
    """
    Get scheduled oral question times for ministers.

    Use to know when specific departments will answer questions or when
    particular topics will be discussed.
    """
    url = build_url(
        f"{ORAL_QUESTIONS_API_BASE}/oralquestiontimes/list",
        {
            "parameters.answeringDateStart": answering_date_start,
            "parameters.answeringDateEnd": answering_date_end,
            "parameters.deadlineDateStart": deadline_date_start,
            "parameters.deadlineDateEnd": deadline_date_end,
            "parameters.oralQuestionTimeId": oral_question_time_id,
            "parameters.answeringBodyIds": answering_body_ids,
        },
    )
    result = run_async(get_result(url))
    echo_utf8(format_output(result, pretty, data_only, output_format, fields, raw))


@app.command("search-oral")
def search_oral_questions(
    answering_body_id: int | None = typer.Option(
        None, "--body-id", help="Department/body answering"
    ),
    asking_member_id: int | None = typer.Option(None, "--member-id", help="Member asking"),
    question_status: str | None = typer.Option(None, "--status", help="Question status"),
    question_type: str | None = typer.Option(
        None, "--question-type", help="Question type: Substantive or Topical"
    ),
    answering_date_start: str | None = typer.Option(
        None, "--answering-from", help="Answering date from (YYYY-MM-DD)"
    ),
    answering_date_end: str | None = typer.Option(
        None, "--answering-to", help="Answering date to (YYYY-MM-DD)"
    ),
    oral_question_time_id: int | None = typer.Option(
        None, "--question-time-id", help="Filter by oral question time ID"
    ),
    skip: int = typer.Option(0, "--skip", help="Results to skip (pagination)"),
    take: int = typer.Option(20, "--take", help="Results to return"),
    pretty: bool = typer.Option(False, "--pretty", "-p", help="Pretty-print JSON output"),
    data_only: bool = typer.Option(
        True, "--data-only", "-d", help="Return data only (use --no-data-only for wrapper)"
    ),
    output_format: OutputFormat = typer.Option(
        OutputFormat.AUTO, "--format", "-f", help="Output format: json, table, markdown, csv, auto"
    ),
    raw: bool = typer.Option(False, "--raw", help="Output full wrapper JSON (url + data)"),
    fields: str | None = typer.Option(
        None, "--fields", help="Comma-separated field paths for columns"
    ),
) -> None:
    """
    Search oral parliamentary questions (not EDMs).

    Use to find oral questions by department, member, or status.
    """
    url = build_url(
        f"{ORAL_QUESTIONS_API_BASE}/oralquestions/list",
        {
            "parameters.answeringBodyId": answering_body_id,
            "parameters.askingMemberId": asking_member_id,
            "parameters.questionStatus": question_status,
            "parameters.questionType": question_type,
            "parameters.answeringDateStart": answering_date_start,
            "parameters.answeringDateEnd": answering_date_end,
            "parameters.oralQuestionTimeId": oral_question_time_id,
            "parameters.skip": skip,
            "parameters.take": take,
        },
    )
    result = run_async(
        paginate_request(url, ORAL_QUESTIONS_PAGINATION, desired_total=take, start_skip=skip)
    )
    echo_utf8(format_output(result, pretty, data_only, output_format, fields, raw))


# Written Questions Commands
@app.command("search-written")
def search_written_questions(
    search_term: str | None = typer.Option(None, "--search", help="Search question content"),
    asking_member_id: int | None = typer.Option(
        None, "--asking-member", help="Filter by asking member ID"
    ),
    answering_member_id: int | None = typer.Option(
        None, "--answering-member", help="Filter by answering member ID"
    ),
    answering_body_id: int | None = typer.Option(
        None, "--answering-body", help="Filter by department"
    ),
    answered: str | None = typer.Option(None, "--answered", help="Any/Answered/Unanswered"),
    question_status: str | None = typer.Option(
        None,
        "--question-status",
        help="Status: Tabled/Answered/Withdrawn/AnswerCorrected/HoldingAnswer",
    ),
    include_withdrawn: bool | None = typer.Option(
        None, "--include-withdrawn", help="Include withdrawn questions"
    ),
    expand_member: bool | None = typer.Option(
        None, "--expand-member", help="Expand member details in results"
    ),
    tabled_from: str | None = typer.Option(None, "--tabled-from", help="Tabled from (YYYY-MM-DD)"),
    tabled_to: str | None = typer.Option(None, "--tabled-to", help="Tabled to (YYYY-MM-DD)"),
    date_for_answer_from: str | None = typer.Option(
        None, "--answer-due-from", help="Answer due from (YYYY-MM-DD)"
    ),
    date_for_answer_to: str | None = typer.Option(
        None, "--answer-due-to", help="Answer due to (YYYY-MM-DD)"
    ),
    answered_from: str | None = typer.Option(
        None, "--answered-from", help="Answered from (YYYY-MM-DD)"
    ),
    answered_to: str | None = typer.Option(None, "--answered-to", help="Answered to (YYYY-MM-DD)"),
    corrected_from: str | None = typer.Option(
        None, "--corrected-from", help="Corrected from (YYYY-MM-DD)"
    ),
    corrected_to: str | None = typer.Option(
        None, "--corrected-to", help="Corrected to (YYYY-MM-DD)"
    ),
    uin: str | None = typer.Option(None, "--uin", help="Unique Identification Number"),
    house: str | None = typer.Option(None, "--house", help="Commons/Lords/Bicameral"),
    skip: int = typer.Option(0, "--skip", help="Results to skip (pagination)"),
    take: int = typer.Option(20, "--take", help="Results to return"),
    pretty: bool = typer.Option(False, "--pretty", "-p", help="Pretty-print JSON output"),
    data_only: bool = typer.Option(
        True, "--data-only", "-d", help="Return data only (use --no-data-only for wrapper)"
    ),
    output_format: OutputFormat = typer.Option(
        OutputFormat.AUTO, "--format", "-f", help="Output format: json, table, markdown, csv, auto"
    ),
    raw: bool = typer.Option(False, "--raw", help="Output full wrapper JSON (url + data)"),
    fields: str | None = typer.Option(
        None, "--fields", help="Comma-separated field paths for columns"
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
            "answeringMemberId": answering_member_id,
            "answeringBodyId": answering_body_id,
            "answered": answered,
            "questionStatus": question_status,
            "includeWithdrawn": include_withdrawn,
            "expandMember": expand_member,
            "tabledWhenFrom": tabled_from,
            "tabledWhenTo": tabled_to,
            "dateForAnswerWhenFrom": date_for_answer_from,
            "dateForAnswerWhenTo": date_for_answer_to,
            "answeredWhenFrom": answered_from,
            "answeredWhenTo": answered_to,
            "correctedWhenFrom": corrected_from,
            "correctedWhenTo": corrected_to,
            "uIN": uin,
            "house": house,
            "skip": skip,
            "take": take,
        },
    )
    result = run_async(
        paginate_request(url, WRITTEN_QUESTIONS_PAGINATION, desired_total=take, start_skip=skip)
    )
    echo_utf8(format_output(result, pretty, data_only, output_format, fields, raw))


@app.command("get-written-question")
def get_written_question(
    question_id: int = typer.Argument(..., help="Written question ID"),
    expand_member: bool = typer.Option(
        True, "--expand-member/--no-expand", help="Include member details"
    ),
    pretty: bool = typer.Option(False, "--pretty", "-p", help="Pretty-print JSON output"),
    data_only: bool = typer.Option(
        True, "--data-only", "-d", help="Return data only (use --no-data-only for wrapper)"
    ),
    output_format: OutputFormat = typer.Option(
        OutputFormat.AUTO, "--format", "-f", help="Output format: json, table, markdown, csv, auto"
    ),
    raw: bool = typer.Option(False, "--raw", help="Output full wrapper JSON (url + data)"),
    fields: str | None = typer.Option(
        None, "--fields", help="Comma-separated field paths for columns"
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
    echo_utf8(format_output(result, pretty, data_only, output_format, fields, raw))


@app.command("get-written-question-by-uin")
def get_written_question_by_uin(
    date: str = typer.Argument(..., help="Date question was tabled (YYYY-MM-DD)"),
    uin: str = typer.Argument(..., help="Unique Identification Number (UIN)"),
    expand_member: bool = typer.Option(
        True, "--expand-member/--no-expand", help="Include member details"
    ),
    pretty: bool = typer.Option(False, "--pretty", "-p", help="Pretty-print JSON output"),
    data_only: bool = typer.Option(
        True, "--data-only", "-d", help="Return data only (use --no-data-only for wrapper)"
    ),
    output_format: OutputFormat = typer.Option(
        OutputFormat.AUTO, "--format", "-f", help="Output format: json, table, markdown, csv, auto"
    ),
    raw: bool = typer.Option(False, "--raw", help="Output full wrapper JSON (url + data)"),
    fields: str | None = typer.Option(
        None, "--fields", help="Comma-separated field paths for columns"
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
    echo_utf8(format_output(result, pretty, data_only, output_format, fields, raw))


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
    data_only: bool = typer.Option(
        True, "--data-only", "-d", help="Return data only (use --no-data-only for wrapper)"
    ),
    output_format: OutputFormat = typer.Option(
        OutputFormat.AUTO, "--format", "-f", help="Output format: json, table, markdown, csv, auto"
    ),
    raw: bool = typer.Option(False, "--raw", help="Output full wrapper JSON (url + data)"),
    fields: str | None = typer.Option(
        None, "--fields", help="Comma-separated field paths for columns"
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
    result = run_async(
        paginate_request(url, WRITTEN_STATEMENTS_PAGINATION, desired_total=take, start_skip=skip)
    )
    echo_utf8(format_output(result, pretty, data_only, output_format, fields, raw))


@app.command("get-statement")
def get_written_statement(
    statement_id: int = typer.Argument(..., help="Written statement ID"),
    expand_member: bool = typer.Option(
        True, "--expand-member/--no-expand", help="Include member details"
    ),
    pretty: bool = typer.Option(False, "--pretty", "-p", help="Pretty-print JSON output"),
    data_only: bool = typer.Option(
        True, "--data-only", "-d", help="Return data only (use --no-data-only for wrapper)"
    ),
    output_format: OutputFormat = typer.Option(
        OutputFormat.AUTO, "--format", "-f", help="Output format: json, table, markdown, csv, auto"
    ),
    raw: bool = typer.Option(False, "--raw", help="Output full wrapper JSON (url + data)"),
    fields: str | None = typer.Option(
        None, "--fields", help="Comma-separated field paths for columns"
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
    echo_utf8(format_output(result, pretty, data_only, output_format, fields, raw))


@app.command("get-statement-by-uin")
def get_written_statement_by_uin(
    date: str = typer.Argument(..., help="Date statement was made (YYYY-MM-DD)"),
    uin: str = typer.Argument(..., help="Unique Identification Number (UIN)"),
    expand_member: bool = typer.Option(
        True, "--expand-member/--no-expand", help="Include member details"
    ),
    pretty: bool = typer.Option(False, "--pretty", "-p", help="Pretty-print JSON output"),
    data_only: bool = typer.Option(
        True, "--data-only", "-d", help="Return data only (use --no-data-only for wrapper)"
    ),
    output_format: OutputFormat = typer.Option(
        OutputFormat.AUTO, "--format", "-f", help="Output format: json, table, markdown, csv, auto"
    ),
    raw: bool = typer.Option(False, "--raw", help="Output full wrapper JSON (url + data)"),
    fields: str | None = typer.Option(
        None, "--fields", help="Comma-separated field paths for columns"
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
    echo_utf8(format_output(result, pretty, data_only, output_format, fields, raw))


@app.command("daily-reports")
def get_daily_reports(
    date_from: str | None = typer.Option(None, "--from", help="Start date (YYYY-MM-DD)"),
    date_to: str | None = typer.Option(None, "--to", help="End date (YYYY-MM-DD)"),
    house: str | None = typer.Option(None, "--house", help="Commons/Lords/Bicameral"),
    skip: int = typer.Option(0, "--skip", help="Results to skip (pagination)"),
    take: int = typer.Option(20, "--take", help="Results to return"),
    pretty: bool = typer.Option(False, "--pretty", "-p", help="Pretty-print JSON output"),
    data_only: bool = typer.Option(
        True, "--data-only", "-d", help="Return data only (use --no-data-only for wrapper)"
    ),
    output_format: OutputFormat = typer.Option(
        OutputFormat.AUTO, "--format", "-f", help="Output format: json, table, markdown, csv, auto"
    ),
    raw: bool = typer.Option(False, "--raw", help="Output full wrapper JSON (url + data)"),
    fields: str | None = typer.Option(
        None, "--fields", help="Comma-separated field paths for columns"
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
    result = run_async(
        paginate_request(url, DAILY_REPORTS_PAGINATION, desired_total=take, start_skip=skip)
    )
    echo_utf8(format_output(result, pretty, data_only, output_format, fields, raw))
