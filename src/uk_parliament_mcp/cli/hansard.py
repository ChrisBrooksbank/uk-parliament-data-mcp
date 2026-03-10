"""Hansard CLI commands for searching the official parliamentary record."""

from __future__ import annotations

from urllib.parse import quote

import typer

from uk_parliament_mcp.cli.formatters import OutputFormat
from uk_parliament_mcp.cli.pagination import (
    HANSARD_MEMBER_SUMMARY_PAGINATION,
    HANSARD_PAGINATION,
)
from uk_parliament_mcp.cli.utils import (
    DataOnlyOpt,
    FieldsOpt,
    FormatOpt,
    PrettyOpt,
    RawOpt,
    output_paginated,
    output_result,
)
from uk_parliament_mcp.config import HANSARD_API_BASE
from uk_parliament_mcp.http_client import build_url

app = typer.Typer(help="Official parliamentary record search", no_args_is_help=True)


@app.command("search-debates")
def search_hansard(
    house: int = typer.Argument(..., help="House: 1=Commons, 2=Lords"),
    start_date: str = typer.Argument(..., help="Start date (YYYY-MM-DD)"),
    end_date: str = typer.Argument(..., help="End date (YYYY-MM-DD)"),
    search_term: str = typer.Argument(..., help="Search term (e.g., 'climate change', 'NHS')"),
    member_id: int | None = typer.Option(None, "--member-id", help="Filter by member ID"),
    skip: int = typer.Option(0, "--skip", help="Results to skip (pagination)"),
    take: int = typer.Option(20, "--take", help="Results to return"),
    pretty: PrettyOpt = False,
    data_only: DataOnlyOpt = True,
    output_format: FormatOpt = OutputFormat.AUTO,
    raw: RawOpt = False,
    fields: FieldsOpt = None,
) -> None:
    """
    Search Hansard debates for speeches and debates on specific topics.

    Use when researching what was said in Parliament on specific topics,
    by specific members, or in specific time periods.
    """
    url = build_url(
        f"{HANSARD_API_BASE}/search/debates.json",
        {
            "queryParameters.house": house,
            "queryParameters.startDate": start_date,
            "queryParameters.endDate": end_date,
            "queryParameters.searchTerm": search_term,
            "queryParameters.memberId": member_id,
            "queryParameters.skip": skip,
            "queryParameters.take": take,
        },
    )
    output_paginated(
        url, HANSARD_PAGINATION, take, skip, pretty, data_only, output_format, fields, raw
    )


@app.command("get-debate")
def get_debate_by_id(
    debate_section_id: str = typer.Argument(..., help="External ID from search results"),
    pretty: PrettyOpt = False,
    data_only: DataOnlyOpt = True,
    output_format: FormatOpt = OutputFormat.AUTO,
    raw: RawOpt = False,
    fields: FieldsOpt = None,
) -> None:
    """
    Get full debate transcript with all member speeches.

    Use after search-debates to get complete debate with all contributions.
    Returns debate title, date, house, and all contributions.
    """
    url = f"{HANSARD_API_BASE}/debates/debate/{debate_section_id}.json"
    output_result(url, pretty, data_only, output_format, fields, raw)


@app.command("member-contributions")
def get_member_hansard_contributions(
    member_id: int = typer.Argument(..., help="Parliament member ID"),
    debate_section_id: str = typer.Argument(..., help="Debate section ID"),
    pretty: PrettyOpt = False,
    data_only: DataOnlyOpt = True,
    output_format: FormatOpt = OutputFormat.AUTO,
    raw: RawOpt = False,
    fields: FieldsOpt = None,
) -> None:
    """
    Get all speeches by a specific MP/Lord in a debate.

    Use to extract just one member's contributions from a debate.
    """
    url = f"{HANSARD_API_BASE}/debates/memberdebatecontributions/{member_id}.json?debateSectionExtId={quote(debate_section_id)}"
    output_result(url, pretty, data_only, output_format, fields, raw)


@app.command("debate-divisions")
def get_debate_divisions(
    debate_section_id: str = typer.Argument(..., help="Debate section ID"),
    pretty: PrettyOpt = False,
    data_only: DataOnlyOpt = True,
    output_format: FormatOpt = OutputFormat.AUTO,
    raw: RawOpt = False,
    fields: FieldsOpt = None,
) -> None:
    """
    Get votes that occurred during a debate.

    Use to find divisions (votes) that took place in a specific debate.
    Returns list of divisions with aye/noe counts.
    """
    url = f"{HANSARD_API_BASE}/debates/divisions/{debate_section_id}.json"
    output_result(url, pretty, data_only, output_format, fields, raw)


@app.command("division-details")
def get_division_details(
    division_id: str = typer.Argument(..., help="Division ID"),
    is_evel: bool = typer.Option(False, "--evel", help="Filter to EVEL voters only"),
    pretty: PrettyOpt = False,
    data_only: DataOnlyOpt = True,
    output_format: FormatOpt = OutputFormat.AUTO,
    raw: RawOpt = False,
    fields: FieldsOpt = None,
) -> None:
    """
    Get full division details including how each member voted.

    Use to see individual voting records for a specific division.
    Returns division with debate title, counts, and member voting records.
    """
    url = build_url(
        f"{HANSARD_API_BASE}/debates/division/{division_id}.json",
        {"isEvel": is_evel if is_evel else None},
    )
    output_result(url, pretty, data_only, output_format, fields, raw)


@app.command("sitting-day")
def get_hansard_sitting_day(
    sitting_date: str = typer.Argument(..., help="Date (YYYY-MM-DD)"),
    house: int = typer.Argument(..., help="House: 1=Commons, 2=Lords"),
    pretty: PrettyOpt = False,
    data_only: DataOnlyOpt = True,
    output_format: FormatOpt = OutputFormat.AUTO,
    raw: RawOpt = False,
    fields: FieldsOpt = None,
) -> None:
    """
    Get full agenda/sections for a sitting day.

    Use to see all debates and business for a specific day.
    Returns all debate sections for that day.
    """
    url = build_url(
        f"{HANSARD_API_BASE}/overview/sectionsforday.json",
        {
            "date": sitting_date,
            "house": house,
        },
    )
    output_result(url, pretty, data_only, output_format, fields, raw)


@app.command("calendar")
def get_hansard_calendar(
    year: int = typer.Argument(..., help="Year (e.g., 2024)"),
    month: int = typer.Argument(..., help="Month (1-12)"),
    house: int = typer.Argument(..., help="House: 1=Commons, 2=Lords"),
    pretty: PrettyOpt = False,
    data_only: DataOnlyOpt = True,
    output_format: FormatOpt = OutputFormat.AUTO,
    raw: RawOpt = False,
    fields: FieldsOpt = None,
) -> None:
    """
    Get all sitting dates for a month.

    Use to discover which days have Hansard records available.
    Returns list of sitting dates with Hansard available.
    """
    url = build_url(
        f"{HANSARD_API_BASE}/overview/calendar.json",
        {
            "year": year,
            "month": month,
            "house": house,
        },
    )
    output_result(url, pretty, data_only, output_format, fields, raw)


@app.command("search-all")
def search_hansard_full(
    house: int | None = typer.Option(None, "--house", help="House: 1=Commons, 2=Lords"),
    start_date: str | None = typer.Option(None, "--start-date", help="Start date (YYYY-MM-DD)"),
    end_date: str | None = typer.Option(None, "--end-date", help="End date (YYYY-MM-DD)"),
    search_term: str | None = typer.Option(None, "--search-term", help="Search term"),
    member_id: int | None = typer.Option(None, "--member-id", help="Filter by member ID"),
    skip: int = typer.Option(0, "--skip", help="Results to skip (pagination)"),
    take: int = typer.Option(20, "--take", help="Results to return"),
    pretty: PrettyOpt = False,
    data_only: DataOnlyOpt = True,
    output_format: FormatOpt = OutputFormat.AUTO,
    raw: RawOpt = False,
    fields: FieldsOpt = None,
) -> None:
    """
    Full search across all Hansard content types.

    Use for broad searches across debates, statements, questions, and petitions.
    Returns mixed results from all Hansard content types.
    """
    url = build_url(
        f"{HANSARD_API_BASE}/search.json",
        {
            "queryParameters.house": house,
            "queryParameters.startDate": start_date,
            "queryParameters.endDate": end_date,
            "queryParameters.searchTerm": search_term,
            "queryParameters.memberId": member_id,
            "queryParameters.skip": skip,
            "queryParameters.take": take,
        },
    )
    output_paginated(
        url, HANSARD_PAGINATION, take, skip, pretty, data_only, output_format, fields, raw
    )


@app.command("search-contributions")
def search_hansard_contributions(
    contribution_type: str = typer.Argument(
        ..., help="Type: 'Spoken', 'Written', 'Intervention', 'Question', 'Answer'"
    ),
    house: int | None = typer.Option(None, "--house", help="House: 1=Commons, 2=Lords"),
    start_date: str | None = typer.Option(None, "--start-date", help="Start date (YYYY-MM-DD)"),
    end_date: str | None = typer.Option(None, "--end-date", help="End date (YYYY-MM-DD)"),
    search_term: str | None = typer.Option(None, "--search-term", help="Search term"),
    member_id: int | None = typer.Option(None, "--member-id", help="Filter by member ID"),
    skip: int = typer.Option(0, "--skip", help="Results to skip (pagination)"),
    take: int = typer.Option(20, "--take", help="Results to return"),
    pretty: PrettyOpt = False,
    data_only: DataOnlyOpt = True,
    output_format: FormatOpt = OutputFormat.AUTO,
    raw: RawOpt = False,
    fields: FieldsOpt = None,
) -> None:
    """
    Search Hansard by contribution type.

    Use to find specific types of parliamentary contributions
    (spoken, written, interventions, questions, answers).
    """
    url = build_url(
        f"{HANSARD_API_BASE}/search/contributions/{contribution_type}.json",
        {
            "queryParameters.house": house,
            "queryParameters.startDate": start_date,
            "queryParameters.endDate": end_date,
            "queryParameters.searchTerm": search_term,
            "queryParameters.memberId": member_id,
            "queryParameters.skip": skip,
            "queryParameters.take": take,
        },
    )
    output_paginated(
        url, HANSARD_PAGINATION, take, skip, pretty, data_only, output_format, fields, raw
    )


@app.command("search-members")
def search_hansard_members(
    search_term: str = typer.Argument(..., help="Name or partial name"),
    house: int | None = typer.Option(None, "--house", help="House: 1=Commons, 2=Lords"),
    include_former: bool = typer.Option(
        True, "--include-former/--no-include-former", help="Include former members"
    ),
    include_current: bool = typer.Option(
        True, "--include-current/--no-include-current", help="Include current members"
    ),
    skip: int = typer.Option(0, "--skip", help="Results to skip (pagination)"),
    take: int = typer.Option(20, "--take", help="Results to return"),
    pretty: PrettyOpt = False,
    data_only: DataOnlyOpt = True,
    output_format: FormatOpt = OutputFormat.AUTO,
    raw: RawOpt = False,
    fields: FieldsOpt = None,
) -> None:
    """
    Search for members who appear in Hansard.

    Use to find members who have spoken in Parliament by name.
    """
    url = build_url(
        f"{HANSARD_API_BASE}/search/members.json",
        {
            "queryParameters.searchTerm": search_term,
            "queryParameters.house": house,
            "queryParameters.includeFormer": include_former,
            "queryParameters.includeCurrent": include_current,
            "queryParameters.skip": skip,
            "queryParameters.take": take,
        },
    )
    output_paginated(
        url, HANSARD_PAGINATION, take, skip, pretty, data_only, output_format, fields, raw
    )


@app.command("search-divisions")
def search_hansard_divisions(
    house: int | None = typer.Option(None, "--house", help="House: 1=Commons, 2=Lords"),
    start_date: str | None = typer.Option(None, "--start-date", help="Start date (YYYY-MM-DD)"),
    end_date: str | None = typer.Option(None, "--end-date", help="End date (YYYY-MM-DD)"),
    search_term: str | None = typer.Option(None, "--search-term", help="Search term"),
    member_id: int | None = typer.Option(None, "--member-id", help="Filter by member ID"),
    skip: int = typer.Option(0, "--skip", help="Results to skip (pagination)"),
    take: int = typer.Option(20, "--take", help="Results to return"),
    pretty: PrettyOpt = False,
    data_only: DataOnlyOpt = True,
    output_format: FormatOpt = OutputFormat.AUTO,
    raw: RawOpt = False,
    fields: FieldsOpt = None,
) -> None:
    """
    Search for divisions (votes) in Hansard.

    Use to find recorded votes in Parliament.
    """
    url = build_url(
        f"{HANSARD_API_BASE}/search/divisions.json",
        {
            "queryParameters.house": house,
            "queryParameters.startDate": start_date,
            "queryParameters.endDate": end_date,
            "queryParameters.searchTerm": search_term,
            "queryParameters.memberId": member_id,
            "queryParameters.skip": skip,
            "queryParameters.take": take,
        },
    )
    output_paginated(
        url, HANSARD_PAGINATION, take, skip, pretty, data_only, output_format, fields, raw
    )


@app.command("member-summary")
def get_member_contribution_summary(
    member_id: int = typer.Argument(..., help="Parliament member ID"),
    skip: int = typer.Option(0, "--skip", help="Results to skip (pagination)"),
    take: int = typer.Option(20, "--take", help="Results to return"),
    pretty: PrettyOpt = False,
    data_only: DataOnlyOpt = True,
    output_format: FormatOpt = OutputFormat.AUTO,
    raw: RawOpt = False,
    fields: FieldsOpt = None,
) -> None:
    """
    Get summary of a member's Hansard contributions.

    Use to see an overview of how often and when a member has spoken.
    Returns summary of member's parliamentary contributions.
    """
    url = build_url(
        f"{HANSARD_API_BASE}/search/membercontributionsummary/{member_id}.json",
        {
            "skip": skip,
            "take": take,
        },
    )
    output_paginated(
        url,
        HANSARD_MEMBER_SUMMARY_PAGINATION,
        take,
        skip,
        pretty,
        data_only,
        output_format,
        fields,
        raw,
    )


@app.command("speakers")
def get_debate_speakers(
    debate_section_id: str = typer.Argument(..., help="Debate section ID"),
    pretty: PrettyOpt = False,
    data_only: DataOnlyOpt = True,
    output_format: FormatOpt = OutputFormat.AUTO,
    raw: RawOpt = False,
    fields: FieldsOpt = None,
) -> None:
    """
    Get list of speakers in a debate.

    Use to see who participated in a specific debate.
    """
    url = f"{HANSARD_API_BASE}/debates/speakerslist/{debate_section_id}.json"
    output_result(url, pretty, data_only, output_format, fields, raw)


@app.command("top-level-debate-id")
def get_top_level_debate_id(
    debate_section_id: str = typer.Argument(..., help="Debate section ID"),
    pretty: PrettyOpt = False,
    data_only: DataOnlyOpt = True,
    output_format: FormatOpt = OutputFormat.AUTO,
    raw: RawOpt = False,
    fields: FieldsOpt = None,
) -> None:
    """
    Get the top-level debate ID for a debate section.

    Use to navigate to the parent debate from a sub-section.
    """
    url = f"{HANSARD_API_BASE}/debates/topleveldebateid/{debate_section_id}.json"
    output_result(url, pretty, data_only, output_format, fields, raw)


@app.command("debate-by-title")
def get_debate_by_title(
    house: str = typer.Argument(..., help="House: 'Commons' or 'Lords'"),
    date: str = typer.Argument(..., help="Date (YYYY-MM-DD)"),
    section_title: str = typer.Argument(..., help="Title of the debate section"),
    pretty: PrettyOpt = False,
    data_only: DataOnlyOpt = True,
    output_format: FormatOpt = OutputFormat.AUTO,
    raw: RawOpt = False,
    fields: FieldsOpt = None,
) -> None:
    """
    Find a debate by title and date.

    Use when you know the debate title and date but not the ID.
    """
    url = build_url(
        f"{HANSARD_API_BASE}/debates/topleveldebatebytitle.json",
        {
            "house": house,
            "date": date,
            "sectionTitle": section_title,
        },
    )
    output_result(url, pretty, data_only, output_format, fields, raw)


@app.command("last-sitting-date")
def get_hansard_last_sitting_date(
    house: str = typer.Argument(..., help="House: 'Commons' or 'Lords'"),
    pretty: PrettyOpt = False,
    data_only: DataOnlyOpt = True,
    output_format: FormatOpt = OutputFormat.AUTO,
    raw: RawOpt = False,
    fields: FieldsOpt = None,
) -> None:
    """
    Get the most recent sitting date with Hansard.

    Use to find the most recent day Parliament sat.
    """
    url = f"{HANSARD_API_BASE}/overview/lastsittingdate.json?house={house}"
    output_result(url, pretty, data_only, output_format, fields, raw)


@app.command("linked-dates")
def get_hansard_linked_dates(
    house: str = typer.Argument(..., help="House: 'Commons' or 'Lords'"),
    date: str = typer.Argument(..., help="Date (YYYY-MM-DD)"),
    pretty: PrettyOpt = False,
    data_only: DataOnlyOpt = True,
    output_format: FormatOpt = OutputFormat.AUTO,
    raw: RawOpt = False,
    fields: FieldsOpt = None,
) -> None:
    """
    Get previous and next sitting dates.

    Use to navigate between sitting days.
    Returns previous and next sitting dates relative to given date.
    """
    url = build_url(
        f"{HANSARD_API_BASE}/overview/linkedsittingdates.json",
        {
            "house": house,
            "date": date,
        },
    )
    output_result(url, pretty, data_only, output_format, fields, raw)


@app.command("section-trees")
def get_hansard_section_trees(
    house: str = typer.Argument(..., help="House: 'Commons' or 'Lords'"),
    date: str = typer.Argument(..., help="Date (YYYY-MM-DD)"),
    section: str = typer.Argument(
        ..., help="Section (e.g., 'Debate', 'WestHall', 'Petitions', 'GEN')"
    ),
    pretty: PrettyOpt = False,
    data_only: DataOnlyOpt = True,
    output_format: FormatOpt = OutputFormat.AUTO,
    raw: RawOpt = False,
    fields: FieldsOpt = None,
) -> None:
    """
    Get hierarchical structure of debates for a day.

    Use to see the tree structure of all debates on a sitting day.
    Returns hierarchical tree of debate sections.
    """
    url = build_url(
        f"{HANSARD_API_BASE}/overview/sectiontrees.json",
        {
            "house": house,
            "date": date,
            "section": section,
        },
    )
    output_result(url, pretty, data_only, output_format, fields, raw)


@app.command("historic-sitting-days")
def search_historic_sitting_days(
    house: str | None = typer.Option(None, "--house", help="House: 'Commons' or 'Lords'"),
    start_date: str | None = typer.Option(None, "--start-date", help="Start date (YYYY-MM-DD)"),
    end_date: str | None = typer.Option(None, "--end-date", help="End date (YYYY-MM-DD)"),
    has_sitting_sections: bool | None = typer.Option(
        None,
        "--has-sitting-sections/--no-has-sitting-sections",
        help="Filter to days with available sitting sections",
    ),
    pretty: PrettyOpt = False,
    data_only: DataOnlyOpt = True,
    output_format: FormatOpt = OutputFormat.AUTO,
    raw: RawOpt = False,
    fields: FieldsOpt = None,
) -> None:
    """
    Search historic sitting days.

    Use to find which days Parliament sat historically.
    Returns list of sitting days in date range.
    """
    url = build_url(
        f"{HANSARD_API_BASE}/historicsittingdays",
        {
            "queryParams.house": house,
            "queryParams.startDate": start_date,
            "queryParams.endDate": end_date,
            "queryParams.hasSittingSections": has_sitting_sections,
        },
    )
    output_result(url, pretty, data_only, output_format, fields, raw)


@app.command("historic-sitting-day")
def get_historic_sitting_day(
    house: str = typer.Argument(..., help="House: 'Commons' or 'Lords'"),
    sitting_date: str = typer.Argument(..., help="Date (YYYY-MM-DD)"),
    pretty: PrettyOpt = False,
    data_only: DataOnlyOpt = True,
    output_format: FormatOpt = OutputFormat.AUTO,
    raw: RawOpt = False,
    fields: FieldsOpt = None,
) -> None:
    """
    Get details of a historic sitting day.

    Use to get details of a specific historic sitting day.
    Returns sitting day details with sections.
    """
    url = f"{HANSARD_API_BASE}/historicsittingdays/{house}/{sitting_date}"
    output_result(url, pretty, data_only, output_format, fields, raw)


@app.command("currently-processing")
def get_hansard_currently_processing(
    pretty: PrettyOpt = False,
    data_only: DataOnlyOpt = True,
    output_format: FormatOpt = OutputFormat.AUTO,
    raw: RawOpt = False,
    fields: FieldsOpt = None,
) -> None:
    """
    Get Hansard content currently being processed.

    Use to check what Hansard content is currently being transcribed or indexed.
    """
    url = f"{HANSARD_API_BASE}/overview/currentlyprocessing.json"
    output_result(url, pretty, data_only, output_format, fields, raw)


@app.command("first-year")
def get_hansard_first_year(
    pretty: PrettyOpt = False,
    data_only: DataOnlyOpt = True,
    output_format: FormatOpt = OutputFormat.AUTO,
    raw: RawOpt = False,
    fields: FieldsOpt = None,
) -> None:
    """
    Get the earliest year Hansard records are available.

    Use to determine the historical range of available Hansard data.
    """
    url = f"{HANSARD_API_BASE}/overview/firstyear.json"
    output_result(url, pretty, data_only, output_format, fields, raw)


@app.command("pdfs-for-day")
def get_hansard_pdfs_for_day(
    date: str = typer.Argument(..., help="Date (YYYY-MM-DD)"),
    house: int = typer.Argument(..., help="House: 1=Commons, 2=Lords"),
    pretty: PrettyOpt = False,
    data_only: DataOnlyOpt = True,
    output_format: FormatOpt = OutputFormat.AUTO,
    raw: RawOpt = False,
    fields: FieldsOpt = None,
) -> None:
    """
    Get PDF documents for a specific sitting day.

    Use to retrieve official PDF transcripts for a parliamentary sitting day.
    """
    url = build_url(
        f"{HANSARD_API_BASE}/overview/pdfsforday.json",
        {
            "date": date,
            "house": house,
        },
    )
    output_result(url, pretty, data_only, output_format, fields, raw)


@app.command("speakers-for-day")
def get_hansard_speakers_for_day(
    date: str = typer.Argument(..., help="Date (YYYY-MM-DD)"),
    house: int = typer.Argument(..., help="House: 1=Commons, 2=Lords"),
    section: str = typer.Argument(
        ..., help="Section (e.g., 'Debate', 'WestHall', 'Petitions', 'GEN')"
    ),
    pretty: PrettyOpt = False,
    data_only: DataOnlyOpt = True,
    output_format: FormatOpt = OutputFormat.AUTO,
    raw: RawOpt = False,
    fields: FieldsOpt = None,
) -> None:
    """
    Get list of speakers for a specific sitting day section.

    Use to find who spoke in a particular section of parliamentary business on a given day.
    """
    url = build_url(
        f"{HANSARD_API_BASE}/overview/speakerslist/{date}/{house}.json",
        {"section": section},
    )
    output_result(url, pretty, data_only, output_format, fields, raw)


@app.command("search-committee-debates")
def search_committee_debates(
    house: int | None = typer.Option(None, "--house", help="House: 1=Commons, 2=Lords"),
    start_date: str | None = typer.Option(None, "--start-date", help="Start date (YYYY-MM-DD)"),
    end_date: str | None = typer.Option(None, "--end-date", help="End date (YYYY-MM-DD)"),
    search_term: str | None = typer.Option(None, "--search-term", help="Search term"),
    committee_title: str | None = typer.Option(
        None, "--committee-title", help="Filter by committee title"
    ),
    skip: int = typer.Option(0, "--skip", help="Results to skip (pagination)"),
    take: int = typer.Option(20, "--take", help="Results to return"),
    pretty: PrettyOpt = False,
    data_only: DataOnlyOpt = True,
    output_format: FormatOpt = OutputFormat.AUTO,
    raw: RawOpt = False,
    fields: FieldsOpt = None,
) -> None:
    """
    Search committee debates in Hansard.

    Use to find debates and discussions from parliamentary committees.
    """
    url = build_url(
        f"{HANSARD_API_BASE}/search/committeedebates.json",
        {
            "queryParameters.house": house,
            "queryParameters.startDate": start_date,
            "queryParameters.endDate": end_date,
            "queryParameters.searchTerm": search_term,
            "queryParameters.committeeTitle": committee_title,
            "queryParameters.skip": skip,
            "queryParameters.take": take,
        },
    )
    output_paginated(
        url, HANSARD_PAGINATION, take, skip, pretty, data_only, output_format, fields, raw
    )


@app.command("search-committees")
def search_hansard_committees(
    house: int | None = typer.Option(None, "--house", help="House: 1=Commons, 2=Lords"),
    start_date: str | None = typer.Option(None, "--start-date", help="Start date (YYYY-MM-DD)"),
    end_date: str | None = typer.Option(None, "--end-date", help="End date (YYYY-MM-DD)"),
    search_term: str | None = typer.Option(None, "--search-term", help="Search term"),
    skip: int = typer.Option(0, "--skip", help="Results to skip (pagination)"),
    take: int = typer.Option(20, "--take", help="Results to return"),
    pretty: PrettyOpt = False,
    data_only: DataOnlyOpt = True,
    output_format: FormatOpt = OutputFormat.AUTO,
    raw: RawOpt = False,
    fields: FieldsOpt = None,
) -> None:
    """
    Search committees that appear in Hansard.

    Use to find committees by name or keyword in Hansard records.
    """
    url = build_url(
        f"{HANSARD_API_BASE}/search/committees.json",
        {
            "queryParameters.house": house,
            "queryParameters.startDate": start_date,
            "queryParameters.endDate": end_date,
            "queryParameters.searchTerm": search_term,
            "queryParameters.skip": skip,
            "queryParameters.take": take,
        },
    )
    output_paginated(
        url, HANSARD_PAGINATION, take, skip, pretty, data_only, output_format, fields, raw
    )


@app.command("debate-by-column")
def get_debate_by_column(
    house: int | None = typer.Option(None, "--house", help="House: 1=Commons, 2=Lords"),
    column_number: int | None = typer.Option(None, "--column", help="Hansard column number"),
    volume_number: int | None = typer.Option(None, "--volume", help="Hansard volume number"),
    series_number: int | None = typer.Option(None, "--series", help="Hansard series number"),
    pretty: PrettyOpt = False,
    data_only: DataOnlyOpt = True,
    output_format: FormatOpt = OutputFormat.AUTO,
    raw: RawOpt = False,
    fields: FieldsOpt = None,
) -> None:
    """
    Get a debate by Hansard column number.

    Use when you have a Hansard column reference (e.g. from a citation).
    """
    url = build_url(
        f"{HANSARD_API_BASE}/search/debatebycolumn.json",
        {
            "queryParameters.house": house,
            "queryParameters.columnNumber": column_number,
            "queryParameters.volumeNumber": volume_number,
            "queryParameters.seriesNumber": series_number,
        },
    )
    output_result(url, pretty, data_only, output_format, fields, raw)


@app.command("debate-by-external-id")
def get_debate_by_external_id(
    content_item_external_id: str = typer.Argument(..., help="External content item ID"),
    house: int = typer.Argument(..., help="House: 1=Commons, 2=Lords"),
    pretty: PrettyOpt = False,
    data_only: DataOnlyOpt = True,
    output_format: FormatOpt = OutputFormat.AUTO,
    raw: RawOpt = False,
    fields: FieldsOpt = None,
) -> None:
    """
    Get a debate by its external content item ID.

    Use when you have an external content item ID to retrieve the specific debate.
    """
    url = build_url(
        f"{HANSARD_API_BASE}/search/debatebyexternalid.json",
        {
            "contentItemExternalId": content_item_external_id,
            "house": house,
        },
    )
    output_result(url, pretty, data_only, output_format, fields, raw)


@app.command("search-petitions")
def search_hansard_petitions(
    house: int | None = typer.Option(None, "--house", help="House: 1=Commons, 2=Lords"),
    start_date: str | None = typer.Option(None, "--start-date", help="Start date (YYYY-MM-DD)"),
    end_date: str | None = typer.Option(None, "--end-date", help="End date (YYYY-MM-DD)"),
    search_term: str | None = typer.Option(None, "--search-term", help="Search term"),
    skip: int = typer.Option(0, "--skip", help="Results to skip (pagination)"),
    take: int = typer.Option(20, "--take", help="Results to return"),
    pretty: PrettyOpt = False,
    data_only: DataOnlyOpt = True,
    output_format: FormatOpt = OutputFormat.AUTO,
    raw: RawOpt = False,
    fields: FieldsOpt = None,
) -> None:
    """
    Search petitions in Hansard.

    Use to find petitions presented in Parliament.
    """
    url = build_url(
        f"{HANSARD_API_BASE}/search/petitions.json",
        {
            "queryParameters.house": house,
            "queryParameters.startDate": start_date,
            "queryParameters.endDate": end_date,
            "queryParameters.searchTerm": search_term,
            "queryParameters.skip": skip,
            "queryParameters.take": take,
        },
    )
    output_paginated(
        url, HANSARD_PAGINATION, take, skip, pretty, data_only, output_format, fields, raw
    )


@app.command("timeline-stats")
def get_hansard_timeline_stats(
    contribution_type: str | None = typer.Option(
        None, "--contribution-type", help="Type of contribution to filter by"
    ),
    is_debates_search: bool | None = typer.Option(
        None,
        "--debates-search/--no-debates-search",
        help="Search debates only",
    ),
    house: int | None = typer.Option(None, "--house", help="House: 1=Commons, 2=Lords"),
    start_date: str | None = typer.Option(None, "--start-date", help="Start date (YYYY-MM-DD)"),
    end_date: str | None = typer.Option(None, "--end-date", help="End date (YYYY-MM-DD)"),
    search_term: str | None = typer.Option(None, "--search-term", help="Search term"),
    member_id: int | None = typer.Option(None, "--member-id", help="Filter by member ID"),
    pretty: PrettyOpt = False,
    data_only: DataOnlyOpt = True,
    output_format: FormatOpt = OutputFormat.AUTO,
    raw: RawOpt = False,
    fields: FieldsOpt = None,
) -> None:
    """
    Get Hansard timeline statistics.

    Use to get aggregate stats showing contribution activity over time.
    """
    url = build_url(
        f"{HANSARD_API_BASE}/timeline-stats.json",
        {
            "contributionType": contribution_type,
            "isDebatesSearch": is_debates_search,
            "queryParameters.house": house,
            "queryParameters.startDate": start_date,
            "queryParameters.endDate": end_date,
            "queryParameters.searchTerm": search_term,
            "queryParameters.memberId": member_id,
        },
    )
    output_result(url, pretty, data_only, output_format, fields, raw)
