"""Members CLI commands for MPs, Lords, constituencies, and parties."""

from __future__ import annotations

import typer

from uk_parliament_mcp.cli.completion import complete_house
from uk_parliament_mcp.cli.formatters import OutputFormat
from uk_parliament_mcp.cli.pagination import MEMBERS_PAGINATION
from uk_parliament_mcp.cli.utils import (
    DataOnlyOpt,
    FieldsOpt,
    FormatOpt,
    PrettyOpt,
    RawOpt,
    output_paginated,
    output_result,
)
from uk_parliament_mcp.config import MEMBERS_API_BASE
from uk_parliament_mcp.http_client import build_url

app = typer.Typer(help="MP and Lords member tools", no_args_is_help=True)


@app.command("search")
def search_member(
    name: str = typer.Argument(..., help="Full or partial name to search"),
    location: str | None = typer.Option(None, "--location", help="Location or constituency name"),
    post_title: str | None = typer.Option(
        None, "--post-title", help="Post title (e.g. 'Minister')"
    ),
    party_id: int | None = typer.Option(None, "--party-id", help="Party ID"),
    house: int | None = typer.Option(
        None, "--house", help="House number (1=Commons, 2=Lords)", autocompletion=complete_house
    ),
    constituency_id: int | None = typer.Option(None, "--constituency-id", help="Constituency ID"),
    name_starts_with: str | None = typer.Option(
        None, "--name-starts-with", help="Name starting letter(s)"
    ),
    gender: str | None = typer.Option(None, "--gender", help="Gender filter (M or F)"),
    membership_started_since: str | None = typer.Option(
        None, "--membership-started-since", help="Membership started since (YYYY-MM-DD)"
    ),
    membership_ended_since: str | None = typer.Option(
        None, "--membership-ended-since", help="Membership ended since (YYYY-MM-DD)"
    ),
    membership_end_reason_ids: str | None = typer.Option(
        None, "--end-reason-ids", help="Comma-separated reason IDs for leaving"
    ),
    was_member_on_or_after: str | None = typer.Option(
        None, "--was-member-on-or-after", help="Was member on or after (YYYY-MM-DD)"
    ),
    was_member_on_or_before: str | None = typer.Option(
        None, "--was-member-on-or-before", help="Was member on or before (YYYY-MM-DD)"
    ),
    was_member_of_house: int | None = typer.Option(
        None, "--was-member-of-house", help="Was member of house (1=Commons, 2=Lords)"
    ),
    is_eligible: bool | None = typer.Option(
        None, "--is-eligible", help="Filter by eligibility status"
    ),
    is_current_member: bool | None = typer.Option(
        None, "--is-current-member", help="Filter by current membership"
    ),
    policy_interest_id: int | None = typer.Option(
        None, "--policy-interest-id", help="Policy interest ID"
    ),
    experience: str | None = typer.Option(
        None, "--experience", help="Professional experience search term"
    ),
    skip: int = typer.Option(0, "--skip", help="Number of records to skip"),
    take: int = typer.Option(20, "--take", help="Number of records to return"),
    pretty: PrettyOpt = False,
    data_only: DataOnlyOpt = True,
    output_format: FormatOpt = OutputFormat.AUTO,
    raw: RawOpt = False,
    fields: FieldsOpt = None,
) -> None:
    """
    Search for MPs and Lords by name, with optional filters.

    Returns member profiles with names, parties, constituencies, and current status.
    Supports pagination and advanced filtering by house, party, location, and more.
    """
    url = build_url(
        f"{MEMBERS_API_BASE}/Members/Search",
        {
            "Name": name,
            "Location": location,
            "PostTitle": post_title,
            "PartyId": party_id,
            "House": house,
            "ConstituencyId": constituency_id,
            "NameStartsWith": name_starts_with,
            "Gender": gender,
            "MembershipStartedSince": membership_started_since,
            "MembershipEnded.MembershipEndedSince": membership_ended_since,
            "MembershipEnded.MembershipEndReasonIds": membership_end_reason_ids,
            "MembershipInDateRange.WasMemberOnOrAfter": was_member_on_or_after,
            "MembershipInDateRange.WasMemberOnOrBefore": was_member_on_or_before,
            "MembershipInDateRange.WasMemberOfHouse": was_member_of_house,
            "IsEligible": is_eligible,
            "IsCurrentMember": is_current_member,
            "PolicyInterestId": policy_interest_id,
            "Experience": experience,
            "skip": skip,
            "take": take,
        },
    )
    output_paginated(
        url, MEMBERS_PAGINATION, take, skip, pretty, data_only, output_format, fields, raw
    )


@app.command("get")
def get_member(
    member_id: int = typer.Argument(..., help="Parliament member ID"),
    details_for_date: str | None = typer.Option(
        None, "--details-for-date", help="Populate details as of this date (YYYY-MM-DD)"
    ),
    pretty: PrettyOpt = False,
    data_only: DataOnlyOpt = True,
    output_format: FormatOpt = OutputFormat.AUTO,
    raw: RawOpt = False,
    fields: FieldsOpt = None,
) -> None:
    """
    Get comprehensive member profile by ID.

    Returns detailed member data including roles, constituency, party, and career information.
    """
    url = build_url(
        f"{MEMBERS_API_BASE}/Members/{member_id}",
        {"detailsForDate": details_for_date},
    )
    output_result(url, pretty, data_only, output_format, fields, raw)


@app.command("biography")
def get_biography(
    member_id: int = typer.Argument(..., help="Parliament member ID"),
    pretty: PrettyOpt = False,
    data_only: DataOnlyOpt = True,
    output_format: FormatOpt = OutputFormat.AUTO,
    raw: RawOpt = False,
    fields: FieldsOpt = None,
) -> None:
    """
    Get comprehensive member biography and personal history.

    Returns biographical data including education, career timeline, and political milestones.
    """
    url = f"{MEMBERS_API_BASE}/Members/{member_id}/Biography"
    output_result(url, pretty, data_only, output_format, fields, raw)


@app.command("contact")
def get_contact(
    member_id: int = typer.Argument(..., help="Parliament member ID"),
    pretty: PrettyOpt = False,
    data_only: DataOnlyOpt = True,
    output_format: FormatOpt = OutputFormat.AUTO,
    raw: RawOpt = False,
    fields: FieldsOpt = None,
) -> None:
    """
    Get member contact details and office information.

    Returns phone numbers, addresses, and official contact information.
    """
    url = f"{MEMBERS_API_BASE}/Members/{member_id}/Contact"
    output_result(url, pretty, data_only, output_format, fields, raw)


@app.command("experience")
def get_experience(
    member_id: int = typer.Argument(..., help="Parliament member ID"),
    pretty: PrettyOpt = False,
    data_only: DataOnlyOpt = True,
    output_format: FormatOpt = OutputFormat.AUTO,
    raw: RawOpt = False,
    fields: FieldsOpt = None,
) -> None:
    """
    Get professional experience and career background.

    Returns professional experience before entering Parliament.
    """
    url = f"{MEMBERS_API_BASE}/Members/{member_id}/Experience"
    output_result(url, pretty, data_only, output_format, fields, raw)


@app.command("focus")
def get_focus(
    member_id: int = typer.Argument(..., help="Parliament member ID"),
    pretty: PrettyOpt = False,
    data_only: DataOnlyOpt = True,
    output_format: FormatOpt = OutputFormat.AUTO,
    raw: RawOpt = False,
    fields: FieldsOpt = None,
) -> None:
    """
    Get areas of focus and policy interests.

    Returns policy areas a member prioritizes or specializes in.
    """
    url = f"{MEMBERS_API_BASE}/Members/{member_id}/Focus"
    output_result(url, pretty, data_only, output_format, fields, raw)


@app.command("interests")
def get_registered_interests(
    member_id: int = typer.Argument(..., help="Parliament member ID"),
    house: int | None = typer.Option(
        None,
        "--house",
        "-h",
        help="House number (1=Commons, 2=Lords)",
        autocompletion=complete_house,
    ),
    pretty: PrettyOpt = False,
    data_only: DataOnlyOpt = True,
    output_format: FormatOpt = OutputFormat.AUTO,
    raw: RawOpt = False,
    fields: FieldsOpt = None,
) -> None:
    """
    Get registered interests of a member.

    Returns declared interests like directorships, consultancies, and gifts.
    """
    url = build_url(
        f"{MEMBERS_API_BASE}/Members/{member_id}/RegisteredInterests",
        {"house": house},
    )
    output_result(url, pretty, data_only, output_format, fields, raw)


@app.command("staff")
def get_staff(
    member_id: int = typer.Argument(..., help="Parliament member ID"),
    pretty: PrettyOpt = False,
    data_only: DataOnlyOpt = True,
    output_format: FormatOpt = OutputFormat.AUTO,
    raw: RawOpt = False,
    fields: FieldsOpt = None,
) -> None:
    """
    Get staff members working for a specific MP or Lord.

    Returns parliamentary office staff, researchers, or support personnel.
    """
    url = f"{MEMBERS_API_BASE}/Members/{member_id}/Staff"
    output_result(url, pretty, data_only, output_format, fields, raw)


@app.command("synopsis")
def get_synopsis(
    member_id: int = typer.Argument(..., help="Parliament member ID"),
    pretty: PrettyOpt = False,
    data_only: DataOnlyOpt = True,
    output_format: FormatOpt = OutputFormat.AUTO,
    raw: RawOpt = False,
    fields: FieldsOpt = None,
) -> None:
    """
    Get a brief synopsis or summary about a member.

    Returns concise overview of member's background, role, or key information.
    """
    url = f"{MEMBERS_API_BASE}/Members/{member_id}/Synopsis"
    output_result(url, pretty, data_only, output_format, fields, raw)


@app.command("voting")
def get_voting(
    member_id: int = typer.Argument(..., help="Parliament member ID"),
    house: int = typer.Option(
        ...,
        "--house",
        "-h",
        help="House number (1=Commons, 2=Lords)",
        autocompletion=complete_house,
    ),
    page: int | None = typer.Option(None, "--page", help="Page number for pagination"),
    pretty: PrettyOpt = False,
    data_only: DataOnlyOpt = True,
    output_format: FormatOpt = OutputFormat.AUTO,
    raw: RawOpt = False,
    fields: FieldsOpt = None,
) -> None:
    """
    Get voting records of a member.

    Returns voting history and voting patterns for the specified house.
    """
    url = build_url(
        f"{MEMBERS_API_BASE}/Members/{member_id}/Voting",
        {"house": house, "page": page},
    )
    output_result(url, pretty, data_only, output_format, fields, raw)


@app.command("written-questions")
def get_written_questions(
    member_id: int = typer.Argument(..., help="Parliament member ID"),
    page: int | None = typer.Option(None, "--page", help="Page number for pagination"),
    pretty: PrettyOpt = False,
    data_only: DataOnlyOpt = True,
    output_format: FormatOpt = OutputFormat.AUTO,
    raw: RawOpt = False,
    fields: FieldsOpt = None,
) -> None:
    """
    Get written questions submitted by a member.

    Returns questions asked of government departments.
    """
    url = build_url(
        f"{MEMBERS_API_BASE}/Members/{member_id}/WrittenQuestions",
        {"page": page},
    )
    output_result(url, pretty, data_only, output_format, fields, raw)


@app.command("edms")
def get_edms(
    member_id: int = typer.Argument(..., help="Parliament member ID"),
    page: int | None = typer.Option(None, "--page", help="Page number for pagination"),
    pretty: PrettyOpt = False,
    data_only: DataOnlyOpt = True,
    output_format: FormatOpt = OutputFormat.AUTO,
    raw: RawOpt = False,
    fields: FieldsOpt = None,
) -> None:
    """
    Get all Early Day Motions signed by a member.

    Returns EDMs to see what issues a member has supported.
    """
    url = build_url(
        f"{MEMBERS_API_BASE}/Members/{member_id}/Edms",
        {"page": page},
    )
    output_result(url, pretty, data_only, output_format, fields, raw)


@app.command("contributions")
def get_contributions(
    member_id: int = typer.Argument(..., help="Parliament member ID"),
    page: int = typer.Option(1, "--page", help="Page number for pagination"),
    pretty: PrettyOpt = False,
    data_only: DataOnlyOpt = True,
    output_format: FormatOpt = OutputFormat.AUTO,
    raw: RawOpt = False,
    fields: FieldsOpt = None,
) -> None:
    """
    Get summary of parliamentary contributions.

    Returns speeches, questions, and interventions made by a member.
    """
    url = build_url(
        f"{MEMBERS_API_BASE}/Members/{member_id}/ContributionSummary",
        {"page": page},
    )
    output_result(url, pretty, data_only, output_format, fields, raw)


@app.command("history")
def get_history(
    member_ids: str = typer.Argument(..., help="Comma-separated member IDs (e.g., '123,456,789')"),
    pretty: PrettyOpt = False,
    data_only: DataOnlyOpt = True,
    output_format: FormatOpt = OutputFormat.AUTO,
    raw: RawOpt = False,
    fields: FieldsOpt = None,
) -> None:
    """
    Get historical information for multiple members.

    Returns name history, party affiliations, and membership details over time.
    """
    url = build_url(f"{MEMBERS_API_BASE}/Members/History", {"ids": member_ids})
    output_result(url, pretty, data_only, output_format, fields, raw)


@app.command("latest-election")
def get_latest_election(
    member_id: int = typer.Argument(..., help="Parliament member ID"),
    pretty: PrettyOpt = False,
    data_only: DataOnlyOpt = True,
    output_format: FormatOpt = OutputFormat.AUTO,
    raw: RawOpt = False,
    fields: FieldsOpt = None,
) -> None:
    """
    Get the latest election result for a member.

    Returns constituency performance, vote share, and election margin.
    """
    url = f"{MEMBERS_API_BASE}/Members/{member_id}/LatestElectionResult"
    output_result(url, pretty, data_only, output_format, fields, raw)


@app.command("portrait")
def get_portrait_url(
    member_id: int = typer.Argument(..., help="Parliament member ID"),
    pretty: PrettyOpt = False,
    data_only: DataOnlyOpt = True,
    output_format: FormatOpt = OutputFormat.AUTO,
    raw: RawOpt = False,
    fields: FieldsOpt = None,
) -> None:
    """
    Get the portrait image URL for a member.

    Returns link to official parliamentary portrait photograph.
    """
    url = f"{MEMBERS_API_BASE}/Members/{member_id}/PortraitUrl"
    output_result(url, pretty, data_only, output_format, fields, raw)


@app.command("thumbnail")
def get_thumbnail_url(
    member_id: int = typer.Argument(..., help="Parliament member ID"),
    pretty: PrettyOpt = False,
    data_only: DataOnlyOpt = True,
    output_format: FormatOpt = OutputFormat.AUTO,
    raw: RawOpt = False,
    fields: FieldsOpt = None,
) -> None:
    """
    Get the thumbnail image URL for a member.

    Returns link to smaller version of parliamentary photograph.
    """
    url = f"{MEMBERS_API_BASE}/Members/{member_id}/ThumbnailUrl"
    output_result(url, pretty, data_only, output_format, fields, raw)


@app.command("constituencies")
def list_constituencies(
    search_text: str | None = typer.Option(
        None, "--search", "-s", help="Filter constituencies by name"
    ),
    skip: int | None = typer.Option(None, "--skip", help="Number to skip (pagination)"),
    take: int | None = typer.Option(None, "--take", help="Number to return (max 100)"),
    pretty: PrettyOpt = False,
    data_only: DataOnlyOpt = True,
    output_format: FormatOpt = OutputFormat.AUTO,
    raw: RawOpt = False,
    fields: FieldsOpt = None,
) -> None:
    """
    Get list of UK parliamentary constituencies.

    Returns constituency information with pagination support.
    """
    url = build_url(
        f"{MEMBERS_API_BASE}/Location/Constituency/Search",
        {"searchText": search_text, "skip": skip, "take": take},
    )
    output_paginated(
        url, MEMBERS_PAGINATION, take, skip or 0, pretty, data_only, output_format, fields, raw
    )


@app.command("constituency-elections")
def get_constituency_elections(
    constituency_id: int = typer.Argument(..., help="Constituency ID"),
    pretty: PrettyOpt = False,
    data_only: DataOnlyOpt = True,
    output_format: FormatOpt = OutputFormat.AUTO,
    raw: RawOpt = False,
    fields: FieldsOpt = None,
) -> None:
    """
    Get historical election results for a constituency.

    Returns voting patterns and electoral history for the area.
    """
    url = f"{MEMBERS_API_BASE}/Location/Constituency/{constituency_id}/ElectionResults"
    output_result(url, pretty, data_only, output_format, fields, raw)


@app.command("parties")
def list_parties(
    house: int = typer.Argument(
        ..., help="House number (1=Commons, 2=Lords)", autocompletion=complete_house
    ),
    pretty: PrettyOpt = False,
    data_only: DataOnlyOpt = True,
    output_format: FormatOpt = OutputFormat.AUTO,
    raw: RawOpt = False,
    fields: FieldsOpt = None,
) -> None:
    """
    Get list of active political parties in a house.

    Returns current party representation for Commons or Lords.
    """
    url = f"{MEMBERS_API_BASE}/Parties/GetActive/{house}"
    output_result(url, pretty, data_only, output_format, fields, raw)


@app.command("party-state")
def get_party_state(
    house: int = typer.Argument(
        ..., help="House number (1=Commons, 2=Lords)", autocompletion=complete_house
    ),
    for_date: str = typer.Argument(..., help="Date for composition (YYYY-MM-DD)"),
    pretty: PrettyOpt = False,
    data_only: DataOnlyOpt = True,
    output_format: FormatOpt = OutputFormat.AUTO,
    raw: RawOpt = False,
    fields: FieldsOpt = None,
) -> None:
    """
    Get party seat counts for a house on a specific date.

    Returns number of seats held by each party.
    """
    url = f"{MEMBERS_API_BASE}/Parties/StateOfTheParties/{house}/{for_date}"
    output_result(url, pretty, data_only, output_format, fields, raw)


@app.command("lords-by-type")
def get_lords_by_type(
    for_date: str = typer.Argument(..., help="Date for composition (YYYY-MM-DD)"),
    pretty: PrettyOpt = False,
    data_only: DataOnlyOpt = True,
    output_format: FormatOpt = OutputFormat.AUTO,
    raw: RawOpt = False,
    fields: FieldsOpt = None,
) -> None:
    """
    Get Lords breakdown by peerage type.

    Returns counts by type: hereditary, life peers, bishops, etc.
    """
    url = f"{MEMBERS_API_BASE}/Parties/LordsByType/{for_date}"
    output_result(url, pretty, data_only, output_format, fields, raw)


@app.command("spokespersons")
def get_spokespersons(
    party_id: int = typer.Argument(..., help="Party ID"),
    pretty: PrettyOpt = False,
    data_only: DataOnlyOpt = True,
    output_format: FormatOpt = OutputFormat.AUTO,
    raw: RawOpt = False,
    fields: FieldsOpt = None,
) -> None:
    """
    Get party spokespersons and their portfolios.

    Returns shadow ministers or party speakers on policy areas.
    """
    url = build_url(
        f"{MEMBERS_API_BASE}/Posts/Spokespersons",
        {"partyId": party_id},
    )
    output_result(url, pretty, data_only, output_format, fields, raw)


@app.command("government-posts")
def get_government_posts(
    pretty: PrettyOpt = False,
    data_only: DataOnlyOpt = True,
    output_format: FormatOpt = OutputFormat.AUTO,
    raw: RawOpt = False,
    fields: FieldsOpt = None,
) -> None:
    """
    Get all current government ministerial positions.

    Returns cabinet and government positions with current holders.
    """
    url = f"{MEMBERS_API_BASE}/Posts/GovernmentPosts"
    output_result(url, pretty, data_only, output_format, fields, raw)


@app.command("opposition-posts")
def get_opposition_posts(
    pretty: PrettyOpt = False,
    data_only: DataOnlyOpt = True,
    output_format: FormatOpt = OutputFormat.AUTO,
    raw: RawOpt = False,
    fields: FieldsOpt = None,
) -> None:
    """
    Get all current opposition frontbench positions.

    Returns shadow cabinet positions with current holders.
    """
    url = f"{MEMBERS_API_BASE}/Posts/OppositionPosts"
    output_result(url, pretty, data_only, output_format, fields, raw)


@app.command("answering-bodies")
def get_answering_bodies(
    name: str | None = typer.Option(None, "--name", "-n", help="Filter by name (partial match)"),
    pretty: PrettyOpt = False,
    data_only: DataOnlyOpt = True,
    output_format: FormatOpt = OutputFormat.AUTO,
    raw: RawOpt = False,
    fields: FieldsOpt = None,
) -> None:
    """
    Get government departments and parliamentary responsibilities.

    Returns department names, abbreviations, and policy responsibilities.
    """
    url = build_url(
        f"{MEMBERS_API_BASE}/Reference/AnsweringBodies",
        {
            "nameContains": name,
        },
    )
    output_result(url, pretty, data_only, output_format, fields, raw)


@app.command("departments")
def get_departments(
    name: str | None = typer.Option(None, "--name", "-n", help="Filter by name (partial match)"),
    pretty: PrettyOpt = False,
    data_only: DataOnlyOpt = True,
    output_format: FormatOpt = OutputFormat.AUTO,
    raw: RawOpt = False,
    fields: FieldsOpt = None,
) -> None:
    """
    Get list of all government departments.

    Returns government structure and department information.
    """
    url = build_url(
        f"{MEMBERS_API_BASE}/Reference/Departments",
        {
            "nameContains": name,
        },
    )
    output_result(url, pretty, data_only, output_format, fields, raw)


@app.command("policy-interests")
def get_policy_interests(
    pretty: PrettyOpt = False,
    data_only: DataOnlyOpt = True,
    output_format: FormatOpt = OutputFormat.AUTO,
    raw: RawOpt = False,
    fields: FieldsOpt = None,
) -> None:
    """
    Get policy interest reference data.

    Returns policy areas and categories for filtering member searches.
    """
    url = f"{MEMBERS_API_BASE}/Reference/PolicyInterests"
    output_result(url, pretty, data_only, output_format, fields, raw)


@app.command("lords-staff-interests")
def search_lords_staff_interests(
    search_term: str = typer.Argument(..., help="Search term for staff names or interests"),
    page: int | None = typer.Option(None, "--page", help="Page number for pagination"),
    pretty: PrettyOpt = False,
    data_only: DataOnlyOpt = True,
    output_format: FormatOpt = OutputFormat.AUTO,
    raw: RawOpt = False,
    fields: FieldsOpt = None,
) -> None:
    """
    Search staff interests declared by Lords.

    Returns staff interests matching the search term.
    """
    url = build_url(
        f"{MEMBERS_API_BASE}/LordsInterests/Staff",
        {"searchTerm": search_term, "page": page},
    )
    output_result(url, pretty, data_only, output_format, fields, raw)
