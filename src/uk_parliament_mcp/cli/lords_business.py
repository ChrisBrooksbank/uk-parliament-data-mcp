"""Lords Business CLI commands for House of Lords business papers, journals and sittings."""

from __future__ import annotations

from urllib.parse import quote

import typer

from uk_parliament_mcp.cli.formatters import OutputFormat
from uk_parliament_mcp.cli.utils import (
    DataOnlyOpt,
    FieldsOpt,
    FormatOpt,
    PrettyOpt,
    RawOpt,
    output_result,
)
from uk_parliament_mcp.config import LORDS_BUSINESS_API_BASE
from uk_parliament_mcp.http_client import build_url

app = typer.Typer(
    help="House of Lords business - order papers, sittings, Journal and Lords written questions",
    no_args_is_help=True,
)


@app.command("sections")
def get_lords_business_sections(
    pretty: PrettyOpt = False,
    data_only: DataOnlyOpt = True,
    output_format: FormatOpt = OutputFormat.AUTO,
    raw: RawOpt = False,
    fields: FieldsOpt = None,
) -> None:
    """
    List all sections of the Lords business paper.

    Use to find section IDs for the section-data command.
    """
    url = f"{LORDS_BUSINESS_API_BASE}/GetSections.json"
    output_result(url, pretty, data_only, output_format, fields, raw)


@app.command("sections-for-date")
def get_lords_business_sections_for_date(
    business_paper_date: str = typer.Argument(..., help="Business paper date (YYYY-MM-DD)"),
    pretty: PrettyOpt = False,
    data_only: DataOnlyOpt = True,
    output_format: FormatOpt = OutputFormat.AUTO,
    raw: RawOpt = False,
    fields: FieldsOpt = None,
) -> None:
    """
    List the Lords business sections published for a date.
    """
    url = build_url(
        f"{LORDS_BUSINESS_API_BASE}/GetSectionsForDate.json",
        {"businessPaperDate": business_paper_date},
    )
    output_result(url, pretty, data_only, output_format, fields, raw)


@app.command("section-data")
def get_lords_business_section_data(
    business_paper_date: str | None = typer.Option(
        None, "--date", help="Business paper date (YYYY-MM-DD)"
    ),
    section_id: int | None = typer.Option(None, "--section-id", help="Section ID"),
    pretty: PrettyOpt = False,
    data_only: DataOnlyOpt = True,
    output_format: FormatOpt = OutputFormat.AUTO,
    raw: RawOpt = False,
    fields: FieldsOpt = None,
) -> None:
    """
    Get the content of a Lords business paper section for a date.

    Shows the items of business the House of Lords is scheduled to consider.
    """
    url = build_url(
        f"{LORDS_BUSINESS_API_BASE}/GetData.json",
        {"BusinessPaperDate": business_paper_date, "SectionId": section_id},
    )
    output_result(url, pretty, data_only, output_format, fields, raw)


@app.command("item-summary")
def get_lords_item_of_business_summary(
    item_of_business_id: int = typer.Argument(..., help="Item of business ID"),
    business_paper_date: str = typer.Argument(..., help="Date the item was published (YYYY-MM-DD)"),
    pretty: PrettyOpt = False,
    data_only: DataOnlyOpt = True,
    output_format: FormatOpt = OutputFormat.AUTO,
    raw: RawOpt = False,
    fields: FieldsOpt = None,
) -> None:
    """
    Get a summary of one Lords item of business.
    """
    url = build_url(
        f"{LORDS_BUSINESS_API_BASE}/ItemOfBusinessSummary.json",
        {"itemOfBusinessId": item_of_business_id, "businessPaperDate": business_paper_date},
    )
    output_result(url, pretty, data_only, output_format, fields, raw)


@app.command("documents")
def get_lords_business_documents_for_date(
    day_date: str = typer.Argument(..., help="Date (YYYY-MM-DD)"),
    pretty: PrettyOpt = False,
    data_only: DataOnlyOpt = True,
    output_format: FormatOpt = OutputFormat.AUTO,
    raw: RawOpt = False,
    fields: FieldsOpt = None,
) -> None:
    """
    List Lords business documents (order paper, HL business) for a day.
    """
    url = f"{LORDS_BUSINESS_API_BASE}/Day/DocumentForDay.json/{quote(day_date)}"
    output_result(url, pretty, data_only, output_format, fields, raw)


@app.command("document")
def get_lords_business_document(
    document_day_id: int = typer.Argument(..., help="DocumentForDayId from the documents command"),
    pretty: PrettyOpt = False,
    data_only: DataOnlyOpt = True,
    output_format: FormatOpt = OutputFormat.AUTO,
    raw: RawOpt = False,
    fields: FieldsOpt = None,
) -> None:
    """
    Get a Lords business document for a day by its DocumentForDayId.
    """
    url = f"{LORDS_BUSINESS_API_BASE}/DocumentForDay/{document_day_id}"
    output_result(url, pretty, data_only, output_format, fields, raw)


@app.command("divisions-exist")
def check_lords_divisions_exist(
    date: str = typer.Argument(..., help="Date to check (YYYY-MM-DD)"),
    pretty: PrettyOpt = False,
    data_only: DataOnlyOpt = True,
    output_format: FormatOpt = OutputFormat.AUTO,
    raw: RawOpt = False,
    fields: FieldsOpt = None,
) -> None:
    """
    Check whether the Lords held divisions on a date.
    """
    url = build_url(f"{LORDS_BUSINESS_API_BASE}/DivisionsExistForDate.json", {"date": date})
    output_result(url, pretty, data_only, output_format, fields, raw)


@app.command("non-sitting-days")
def get_lords_non_sitting_days(
    month: int = typer.Argument(..., help="Month number (1-12)"),
    year: int = typer.Argument(..., help="Year (e.g. 2025)"),
    data_source: str | None = typer.Option(
        None, "--source", help="'Calendar' (default) or 'PublishedBusiness'"
    ),
    pretty: PrettyOpt = False,
    data_only: DataOnlyOpt = True,
    output_format: FormatOpt = OutputFormat.AUTO,
    raw: RawOpt = False,
    fields: FieldsOpt = None,
) -> None:
    """
    List Lords non-sitting days in a month.
    """
    url = build_url(
        f"{LORDS_BUSINESS_API_BASE}/NonSittingDays.json/{month}/{year}",
        {"dataSource": data_source},
    )
    output_result(url, pretty, data_only, output_format, fields, raw)


@app.command("next-prev-days")
def get_lords_next_prev_business_days(
    initial_date: str = typer.Argument(..., help="Date to search from (YYYY-MM-DD)"),
    pretty: PrettyOpt = False,
    data_only: DataOnlyOpt = True,
    output_format: FormatOpt = OutputFormat.AUTO,
    raw: RawOpt = False,
    fields: FieldsOpt = None,
) -> None:
    """
    Get the next and previous Lords days with items of business.
    """
    url = build_url(
        f"{LORDS_BUSINESS_API_BASE}/GetNextPrevDaysWithItemsOfBusiness.json",
        {"initialDate": initial_date},
    )
    output_result(url, pretty, data_only, output_format, fields, raw)


@app.command("journal-volumes")
def get_lords_journal_volumes(
    skip: int | None = typer.Option(None, "--skip", help="Number of volumes to skip"),
    take: int | None = typer.Option(None, "--take", help="Number of volumes to return"),
    pretty: PrettyOpt = False,
    data_only: DataOnlyOpt = True,
    output_format: FormatOpt = OutputFormat.AUTO,
    raw: RawOpt = False,
    fields: FieldsOpt = None,
) -> None:
    """
    List Lords Journal volumes.
    """
    url = build_url(f"{LORDS_BUSINESS_API_BASE}/journal-volumes", {"Skip": skip, "Take": take})
    output_result(url, pretty, data_only, output_format, fields, raw)


@app.command("journal-volume")
def get_lords_journal_volume(
    volume_id: int = typer.Argument(..., help="Journal volume ID"),
    pretty: PrettyOpt = False,
    data_only: DataOnlyOpt = True,
    output_format: FormatOpt = OutputFormat.AUTO,
    raw: RawOpt = False,
    fields: FieldsOpt = None,
) -> None:
    """
    Get a Lords Journal volume.
    """
    url = f"{LORDS_BUSINESS_API_BASE}/journal-volumes/{volume_id}"
    output_result(url, pretty, data_only, output_format, fields, raw)


@app.command("journal-general-index")
def get_lords_journal_general_index(
    volume_id: int = typer.Argument(..., help="Journal volume ID"),
    starting_with: str | None = typer.Option(
        None, "--starting-with", help="Only index items starting with this text"
    ),
    pretty: PrettyOpt = False,
    data_only: DataOnlyOpt = True,
    output_format: FormatOpt = OutputFormat.AUTO,
    raw: RawOpt = False,
    fields: FieldsOpt = None,
) -> None:
    """
    Get the general (subject) index of a Lords Journal volume.

    The response is large; use --starting-with to narrow it.
    """
    url = build_url(
        f"{LORDS_BUSINESS_API_BASE}/journal-volumes/{volume_id}/general-index",
        {"StartingWith": starting_with},
    )
    output_result(url, pretty, data_only, output_format, fields, raw)


@app.command("journal-membership-index")
def get_lords_journal_membership_index(
    volume_id: int = typer.Argument(..., help="Journal volume ID"),
    starting_with: str | None = typer.Option(
        None, "--starting-with", help="Only index items starting with this text"
    ),
    pretty: PrettyOpt = False,
    data_only: DataOnlyOpt = True,
    output_format: FormatOpt = OutputFormat.AUTO,
    raw: RawOpt = False,
    fields: FieldsOpt = None,
) -> None:
    """
    Get the membership index of a Lords Journal volume.
    """
    url = build_url(
        f"{LORDS_BUSINESS_API_BASE}/journal-volumes/{volume_id}/membership-index",
        {"StartingWith": starting_with},
    )
    output_result(url, pretty, data_only, output_format, fields, raw)


@app.command("journal-index-item")
def get_lords_journal_index_items(
    index_item_guid: str = typer.Argument(..., help="GUID of the Journal index item"),
    journal_volume_id: int = typer.Argument(..., help="Journal volume ID"),
    pretty: PrettyOpt = False,
    data_only: DataOnlyOpt = True,
    output_format: FormatOpt = OutputFormat.AUTO,
    raw: RawOpt = False,
    fields: FieldsOpt = None,
) -> None:
    """
    Get a Lords Journal index item and its references.
    """
    url = build_url(
        f"{LORDS_BUSINESS_API_BASE}/index-items/{quote(index_item_guid)}",
        {"journalVolumeId": journal_volume_id},
    )
    output_result(url, pretty, data_only, output_format, fields, raw)


@app.command("journal-dates")
def get_lords_journal_content_dates(
    start_date: str | None = typer.Option(None, "--from", help="Start date (YYYY-MM-DD)"),
    end_date: str | None = typer.Option(None, "--to", help="End date (YYYY-MM-DD)"),
    pretty: PrettyOpt = False,
    data_only: DataOnlyOpt = True,
    output_format: FormatOpt = OutputFormat.AUTO,
    raw: RawOpt = False,
    fields: FieldsOpt = None,
) -> None:
    """
    List dates that have Lords Journal data.
    """
    url = build_url(
        f"{LORDS_BUSINESS_API_BASE}/sittings/journalContentDates",
        {"startDate": start_date, "endDate": end_date},
    )
    output_result(url, pretty, data_only, output_format, fields, raw)


@app.command("journal-sittings")
def get_lords_journal_sittings(
    sitting_date: str = typer.Argument(..., help="Sitting date (YYYY-MM-DD)"),
    content_type: str = typer.Argument(
        ..., help="Attendance, MinutesOfProceedings, Papers, Appendix or Divisions"
    ),
    pretty: PrettyOpt = False,
    data_only: DataOnlyOpt = True,
    output_format: FormatOpt = OutputFormat.AUTO,
    raw: RawOpt = False,
    fields: FieldsOpt = None,
) -> None:
    """
    Get Lords Journal content for a sitting date and content type.
    """
    url = f"{LORDS_BUSINESS_API_BASE}/sittings/{quote(sitting_date)}/{quote(content_type)}"
    output_result(url, pretty, data_only, output_format, fields, raw)


@app.command("journal-attachment")
def get_lords_journal_attachment(
    attachment_id: int = typer.Argument(..., help="Journal attachment ID"),
    pretty: PrettyOpt = False,
    data_only: DataOnlyOpt = True,
    output_format: FormatOpt = OutputFormat.AUTO,
    raw: RawOpt = False,
    fields: FieldsOpt = None,
) -> None:
    """
    Get a Lords Journal attachment.
    """
    url = f"{LORDS_BUSINESS_API_BASE}/journal-attachments/{attachment_id}"
    output_result(url, pretty, data_only, output_format, fields, raw)


@app.command("legacy-business")
def get_lords_legacy_business(
    day_date: str = typer.Argument(..., help="Date (YYYY-MM-DD)"),
    pretty: PrettyOpt = False,
    data_only: DataOnlyOpt = True,
    output_format: FormatOpt = OutputFormat.AUTO,
    raw: RawOpt = False,
    fields: FieldsOpt = None,
) -> None:
    """
    List legacy Lords business documents for a date.
    """
    url = f"{LORDS_BUSINESS_API_BASE}/legacybusiness/{quote(day_date)}"
    output_result(url, pretty, data_only, output_format, fields, raw)


@app.command("search-written-questions")
def search_lords_written_questions(
    member_id: int | None = typer.Option(None, "--member-id", help="Asking Lord's member ID"),
    uin: str | None = typer.Option(None, "--uin", help="Question UIN"),
    status: str | None = typer.Option(None, "--status", help="Tabled, Answered or Withdrawn"),
    tabled_start_date: str | None = typer.Option(
        None, "--tabled-from", help="Tabled on or after (YYYY-MM-DD)"
    ),
    tabled_end_date: str | None = typer.Option(
        None, "--tabled-to", help="Tabled on or before (YYYY-MM-DD)"
    ),
    order_by: str | None = typer.Option(None, "--order-by", help="DateTabledAsc or DateTabledDesc"),
    skip: int | None = typer.Option(None, "--skip", help="Number of results to skip"),
    take: int | None = typer.Option(None, "--take", help="Number of results to return"),
    pretty: PrettyOpt = False,
    data_only: DataOnlyOpt = True,
    output_format: FormatOpt = OutputFormat.AUTO,
    raw: RawOpt = False,
    fields: FieldsOpt = None,
) -> None:
    """
    Search House of Lords written questions.

    Give a date range: unfiltered requests are slow.
    """
    url = build_url(
        f"{LORDS_BUSINESS_API_BASE}/WrittenQuestions/list.json",
        {
            "MemberId": member_id,
            "Uin": uin,
            "Statuses": status,
            "TabledStartDate": tabled_start_date,
            "TabledEndDate": tabled_end_date,
            "OrderBy": order_by,
            "Skip": skip,
            "Take": take,
        },
    )
    output_result(url, pretty, data_only, output_format, fields, raw)


@app.command("written-question")
def get_lords_written_question(
    question_id: int = typer.Argument(..., help="Question ID"),
    pretty: PrettyOpt = False,
    data_only: DataOnlyOpt = True,
    output_format: FormatOpt = OutputFormat.AUTO,
    raw: RawOpt = False,
    fields: FieldsOpt = None,
) -> None:
    """
    Get a single House of Lords written question.
    """
    url = f"{LORDS_BUSINESS_API_BASE}/WrittenQuestions/{question_id}.json"
    output_result(url, pretty, data_only, output_format, fields, raw)
