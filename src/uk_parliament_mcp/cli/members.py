"""Members CLI commands for MPs, Lords, constituencies, and parties."""

from __future__ import annotations

from urllib.parse import quote

import typer

from uk_parliament_mcp.cli.formatters import OutputFormat
from uk_parliament_mcp.cli.utils import echo_utf8, format_output, run_async
from uk_parliament_mcp.config import MEMBERS_API_BASE
from uk_parliament_mcp.http_client import build_url, get_result

app = typer.Typer(help="MP and Lords member tools")


@app.command("search")
def search_member(
    name: str = typer.Argument(..., help="Full or partial name to search"),
    pretty: bool = typer.Option(False, "--pretty", "-p", help="Pretty-print JSON output"),
    data_only: bool = typer.Option(False, "--data-only", "-d", help="Return data only"),
    output_format: OutputFormat = typer.Option(
        OutputFormat.JSON, "--format", "-f", help="Output format: json, table, markdown"
    ),
) -> None:
    """
    Search for MPs and Lords by name.

    Returns member profiles with names, parties, constituencies, and current status.
    """
    url = f"{MEMBERS_API_BASE}/Members/Search?Name={quote(name)}"
    result = run_async(get_result(url))
    echo_utf8(format_output(result, pretty, data_only, output_format))


@app.command("get")
def get_member(
    member_id: int = typer.Argument(..., help="Parliament member ID"),
    pretty: bool = typer.Option(False, "--pretty", "-p", help="Pretty-print JSON output"),
    data_only: bool = typer.Option(False, "--data-only", "-d", help="Return data only"),
    output_format: OutputFormat = typer.Option(
        OutputFormat.JSON, "--format", "-f", help="Output format: json, table, markdown"
    ),
) -> None:
    """
    Get comprehensive member profile by ID.

    Returns detailed member data including roles, constituency, party, and career information.
    """
    url = f"{MEMBERS_API_BASE}/Members/{member_id}"
    result = run_async(get_result(url))
    echo_utf8(format_output(result, pretty, data_only, output_format))


@app.command("biography")
def get_biography(
    member_id: int = typer.Argument(..., help="Parliament member ID"),
    pretty: bool = typer.Option(False, "--pretty", "-p", help="Pretty-print JSON output"),
    data_only: bool = typer.Option(False, "--data-only", "-d", help="Return data only"),
    output_format: OutputFormat = typer.Option(
        OutputFormat.JSON, "--format", "-f", help="Output format: json, table, markdown"
    ),
) -> None:
    """
    Get comprehensive member biography and personal history.

    Returns biographical data including education, career timeline, and political milestones.
    """
    url = f"{MEMBERS_API_BASE}/Members/{member_id}/Biography"
    result = run_async(get_result(url))
    echo_utf8(format_output(result, pretty, data_only, output_format))


@app.command("contact")
def get_contact(
    member_id: int = typer.Argument(..., help="Parliament member ID"),
    pretty: bool = typer.Option(False, "--pretty", "-p", help="Pretty-print JSON output"),
    data_only: bool = typer.Option(False, "--data-only", "-d", help="Return data only"),
    output_format: OutputFormat = typer.Option(
        OutputFormat.JSON, "--format", "-f", help="Output format: json, table, markdown"
    ),
) -> None:
    """
    Get member contact details and office information.

    Returns phone numbers, addresses, and official contact information.
    """
    url = f"{MEMBERS_API_BASE}/Members/{member_id}/Contact"
    result = run_async(get_result(url))
    echo_utf8(format_output(result, pretty, data_only, output_format))


@app.command("experience")
def get_experience(
    member_id: int = typer.Argument(..., help="Parliament member ID"),
    pretty: bool = typer.Option(False, "--pretty", "-p", help="Pretty-print JSON output"),
    data_only: bool = typer.Option(False, "--data-only", "-d", help="Return data only"),
    output_format: OutputFormat = typer.Option(
        OutputFormat.JSON, "--format", "-f", help="Output format: json, table, markdown"
    ),
) -> None:
    """
    Get professional experience and career background.

    Returns professional experience before entering Parliament.
    """
    url = f"{MEMBERS_API_BASE}/Members/{member_id}/Experience"
    result = run_async(get_result(url))
    echo_utf8(format_output(result, pretty, data_only, output_format))


@app.command("focus")
def get_focus(
    member_id: int = typer.Argument(..., help="Parliament member ID"),
    pretty: bool = typer.Option(False, "--pretty", "-p", help="Pretty-print JSON output"),
    data_only: bool = typer.Option(False, "--data-only", "-d", help="Return data only"),
    output_format: OutputFormat = typer.Option(
        OutputFormat.JSON, "--format", "-f", help="Output format: json, table, markdown"
    ),
) -> None:
    """
    Get areas of focus and policy interests.

    Returns policy areas a member prioritizes or specializes in.
    """
    url = f"{MEMBERS_API_BASE}/Members/{member_id}/Focus"
    result = run_async(get_result(url))
    echo_utf8(format_output(result, pretty, data_only, output_format))


@app.command("interests")
def get_registered_interests(
    member_id: int = typer.Argument(..., help="Parliament member ID"),
    house: int | None = typer.Option(
        None, "--house", "-h", help="House number (1=Commons, 2=Lords)"
    ),
    pretty: bool = typer.Option(False, "--pretty", "-p", help="Pretty-print JSON output"),
    data_only: bool = typer.Option(False, "--data-only", "-d", help="Return data only"),
    output_format: OutputFormat = typer.Option(
        OutputFormat.JSON, "--format", "-f", help="Output format: json, table, markdown"
    ),
) -> None:
    """
    Get registered interests of a member.

    Returns declared interests like directorships, consultancies, and gifts.
    """
    url = build_url(
        f"{MEMBERS_API_BASE}/Members/{member_id}/RegisteredInterests",
        {"house": house},
    )
    result = run_async(get_result(url))
    echo_utf8(format_output(result, pretty, data_only, output_format))


@app.command("staff")
def get_staff(
    member_id: int = typer.Argument(..., help="Parliament member ID"),
    pretty: bool = typer.Option(False, "--pretty", "-p", help="Pretty-print JSON output"),
    data_only: bool = typer.Option(False, "--data-only", "-d", help="Return data only"),
    output_format: OutputFormat = typer.Option(
        OutputFormat.JSON, "--format", "-f", help="Output format: json, table, markdown"
    ),
) -> None:
    """
    Get staff members working for a specific MP or Lord.

    Returns parliamentary office staff, researchers, or support personnel.
    """
    url = f"{MEMBERS_API_BASE}/Members/{member_id}/Staff"
    result = run_async(get_result(url))
    echo_utf8(format_output(result, pretty, data_only, output_format))


@app.command("synopsis")
def get_synopsis(
    member_id: int = typer.Argument(..., help="Parliament member ID"),
    pretty: bool = typer.Option(False, "--pretty", "-p", help="Pretty-print JSON output"),
    data_only: bool = typer.Option(False, "--data-only", "-d", help="Return data only"),
    output_format: OutputFormat = typer.Option(
        OutputFormat.JSON, "--format", "-f", help="Output format: json, table, markdown"
    ),
) -> None:
    """
    Get a brief synopsis or summary about a member.

    Returns concise overview of member's background, role, or key information.
    """
    url = f"{MEMBERS_API_BASE}/Members/{member_id}/Synopsis"
    result = run_async(get_result(url))
    echo_utf8(format_output(result, pretty, data_only, output_format))


@app.command("voting")
def get_voting(
    member_id: int = typer.Argument(..., help="Parliament member ID"),
    house: int = typer.Option(..., "--house", "-h", help="House number (1=Commons, 2=Lords)"),
    page: int | None = typer.Option(None, "--page", help="Page number for pagination"),
    pretty: bool = typer.Option(False, "--pretty", "-p", help="Pretty-print JSON output"),
    data_only: bool = typer.Option(False, "--data-only", "-d", help="Return data only"),
    output_format: OutputFormat = typer.Option(
        OutputFormat.JSON, "--format", "-f", help="Output format: json, table, markdown"
    ),
) -> None:
    """
    Get voting records of a member.

    Returns voting history and voting patterns for the specified house.
    """
    url = build_url(
        f"{MEMBERS_API_BASE}/Members/{member_id}/Voting",
        {"house": house, "page": page},
    )
    result = run_async(get_result(url))
    echo_utf8(format_output(result, pretty, data_only, output_format))


@app.command("written-questions")
def get_written_questions(
    member_id: int = typer.Argument(..., help="Parliament member ID"),
    page: int | None = typer.Option(None, "--page", help="Page number for pagination"),
    pretty: bool = typer.Option(False, "--pretty", "-p", help="Pretty-print JSON output"),
    data_only: bool = typer.Option(False, "--data-only", "-d", help="Return data only"),
    output_format: OutputFormat = typer.Option(
        OutputFormat.JSON, "--format", "-f", help="Output format: json, table, markdown"
    ),
) -> None:
    """
    Get written questions submitted by a member.

    Returns questions asked of government departments.
    """
    url = build_url(
        f"{MEMBERS_API_BASE}/Members/{member_id}/WrittenQuestions",
        {"page": page},
    )
    result = run_async(get_result(url))
    echo_utf8(format_output(result, pretty, data_only, output_format))


@app.command("edms")
def get_edms(
    member_id: int = typer.Argument(..., help="Parliament member ID"),
    pretty: bool = typer.Option(False, "--pretty", "-p", help="Pretty-print JSON output"),
    data_only: bool = typer.Option(False, "--data-only", "-d", help="Return data only"),
    output_format: OutputFormat = typer.Option(
        OutputFormat.JSON, "--format", "-f", help="Output format: json, table, markdown"
    ),
) -> None:
    """
    Get all Early Day Motions signed by a member.

    Returns EDMs to see what issues a member has supported.
    """
    url = f"{MEMBERS_API_BASE}/Members/{member_id}/Edms"
    result = run_async(get_result(url))
    echo_utf8(format_output(result, pretty, data_only, output_format))


@app.command("contributions")
def get_contributions(
    member_id: int = typer.Argument(..., help="Parliament member ID"),
    pretty: bool = typer.Option(False, "--pretty", "-p", help="Pretty-print JSON output"),
    data_only: bool = typer.Option(False, "--data-only", "-d", help="Return data only"),
    output_format: OutputFormat = typer.Option(
        OutputFormat.JSON, "--format", "-f", help="Output format: json, table, markdown"
    ),
) -> None:
    """
    Get summary of parliamentary contributions.

    Returns speeches, questions, and interventions made by a member.
    """
    url = f"{MEMBERS_API_BASE}/Members/{member_id}/ContributionSummary?page=1"
    result = run_async(get_result(url))
    echo_utf8(format_output(result, pretty, data_only, output_format))


@app.command("history")
def get_history(
    member_ids: str = typer.Argument(..., help="Comma-separated member IDs (e.g., '123,456,789')"),
    pretty: bool = typer.Option(False, "--pretty", "-p", help="Pretty-print JSON output"),
    data_only: bool = typer.Option(False, "--data-only", "-d", help="Return data only"),
    output_format: OutputFormat = typer.Option(
        OutputFormat.JSON, "--format", "-f", help="Output format: json, table, markdown"
    ),
) -> None:
    """
    Get historical information for multiple members.

    Returns name history, party affiliations, and membership details over time.
    """
    url = build_url(f"{MEMBERS_API_BASE}/Members/History", {"ids": member_ids})
    result = run_async(get_result(url))
    echo_utf8(format_output(result, pretty, data_only, output_format))


@app.command("latest-election")
def get_latest_election(
    member_id: int = typer.Argument(..., help="Parliament member ID"),
    pretty: bool = typer.Option(False, "--pretty", "-p", help="Pretty-print JSON output"),
    data_only: bool = typer.Option(False, "--data-only", "-d", help="Return data only"),
    output_format: OutputFormat = typer.Option(
        OutputFormat.JSON, "--format", "-f", help="Output format: json, table, markdown"
    ),
) -> None:
    """
    Get the latest election result for a member.

    Returns constituency performance, vote share, and election margin.
    """
    url = f"{MEMBERS_API_BASE}/Members/{member_id}/LatestElectionResult"
    result = run_async(get_result(url))
    echo_utf8(format_output(result, pretty, data_only, output_format))


@app.command("portrait")
def get_portrait_url(
    member_id: int = typer.Argument(..., help="Parliament member ID"),
    pretty: bool = typer.Option(False, "--pretty", "-p", help="Pretty-print JSON output"),
    data_only: bool = typer.Option(False, "--data-only", "-d", help="Return data only"),
    output_format: OutputFormat = typer.Option(
        OutputFormat.JSON, "--format", "-f", help="Output format: json, table, markdown"
    ),
) -> None:
    """
    Get the portrait image URL for a member.

    Returns link to official parliamentary portrait photograph.
    """
    url = f"{MEMBERS_API_BASE}/Members/{member_id}/PortraitUrl"
    result = run_async(get_result(url))
    echo_utf8(format_output(result, pretty, data_only, output_format))


@app.command("thumbnail")
def get_thumbnail_url(
    member_id: int = typer.Argument(..., help="Parliament member ID"),
    pretty: bool = typer.Option(False, "--pretty", "-p", help="Pretty-print JSON output"),
    data_only: bool = typer.Option(False, "--data-only", "-d", help="Return data only"),
    output_format: OutputFormat = typer.Option(
        OutputFormat.JSON, "--format", "-f", help="Output format: json, table, markdown"
    ),
) -> None:
    """
    Get the thumbnail image URL for a member.

    Returns link to smaller version of parliamentary photograph.
    """
    url = f"{MEMBERS_API_BASE}/Members/{member_id}/ThumbnailUrl"
    result = run_async(get_result(url))
    echo_utf8(format_output(result, pretty, data_only, output_format))


@app.command("search-advanced")
def search_members_advanced(
    name: str | None = typer.Option(None, "--name", help="Full or partial name"),
    location: str | None = typer.Option(None, "--location", help="Location or constituency name"),
    post_title: str | None = typer.Option(
        None, "--post-title", help="Post title (e.g. 'Minister')"
    ),
    party_id: int | None = typer.Option(None, "--party-id", help="Party ID"),
    house: int | None = typer.Option(None, "--house", help="House number (1=Commons, 2=Lords)"),
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
    pretty: bool = typer.Option(False, "--pretty", "-p", help="Pretty-print JSON output"),
    data_only: bool = typer.Option(False, "--data-only", "-d", help="Return data only"),
    output_format: OutputFormat = typer.Option(
        OutputFormat.JSON, "--format", "-f", help="Output format: json, table, markdown"
    ),
) -> None:
    """
    Advanced search for members with comprehensive filtering.

    Returns matching member profiles with all specified filters applied.
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
    result = run_async(get_result(url))
    echo_utf8(format_output(result, pretty, data_only, output_format))


@app.command("constituencies")
def list_constituencies(
    skip: int | None = typer.Option(None, "--skip", help="Number to skip (pagination)"),
    take: int | None = typer.Option(None, "--take", help="Number to return (max 100)"),
    pretty: bool = typer.Option(False, "--pretty", "-p", help="Pretty-print JSON output"),
    data_only: bool = typer.Option(False, "--data-only", "-d", help="Return data only"),
    output_format: OutputFormat = typer.Option(
        OutputFormat.JSON, "--format", "-f", help="Output format: json, table, markdown"
    ),
) -> None:
    """
    Get list of UK parliamentary constituencies.

    Returns constituency information with pagination support.
    """
    url = build_url(
        f"{MEMBERS_API_BASE}/Location/Constituency/Search",
        {"skip": skip, "take": take},
    )
    result = run_async(get_result(url))
    echo_utf8(format_output(result, pretty, data_only, output_format))


@app.command("constituency-elections")
def get_constituency_elections(
    constituency_id: int = typer.Argument(..., help="Constituency ID"),
    pretty: bool = typer.Option(False, "--pretty", "-p", help="Pretty-print JSON output"),
    data_only: bool = typer.Option(False, "--data-only", "-d", help="Return data only"),
    output_format: OutputFormat = typer.Option(
        OutputFormat.JSON, "--format", "-f", help="Output format: json, table, markdown"
    ),
) -> None:
    """
    Get historical election results for a constituency.

    Returns voting patterns and electoral history for the area.
    """
    url = f"{MEMBERS_API_BASE}/Location/Constituency/{constituency_id}/ElectionResults"
    result = run_async(get_result(url))
    echo_utf8(format_output(result, pretty, data_only, output_format))


@app.command("parties")
def list_parties(
    house: int = typer.Argument(..., help="House number (1=Commons, 2=Lords)"),
    pretty: bool = typer.Option(False, "--pretty", "-p", help="Pretty-print JSON output"),
    data_only: bool = typer.Option(False, "--data-only", "-d", help="Return data only"),
    output_format: OutputFormat = typer.Option(
        OutputFormat.JSON, "--format", "-f", help="Output format: json, table, markdown"
    ),
) -> None:
    """
    Get list of active political parties in a house.

    Returns current party representation for Commons or Lords.
    """
    url = f"{MEMBERS_API_BASE}/Parties/GetActive/{house}"
    result = run_async(get_result(url))
    echo_utf8(format_output(result, pretty, data_only, output_format))


@app.command("party-state")
def get_party_state(
    house: int = typer.Argument(..., help="House number (1=Commons, 2=Lords)"),
    for_date: str = typer.Argument(..., help="Date for composition (YYYY-MM-DD)"),
    pretty: bool = typer.Option(False, "--pretty", "-p", help="Pretty-print JSON output"),
    data_only: bool = typer.Option(False, "--data-only", "-d", help="Return data only"),
    output_format: OutputFormat = typer.Option(
        OutputFormat.JSON, "--format", "-f", help="Output format: json, table, markdown"
    ),
) -> None:
    """
    Get party seat counts for a house on a specific date.

    Returns number of seats held by each party.
    """
    url = f"{MEMBERS_API_BASE}/Parties/StateOfTheParties/{house}/{for_date}"
    result = run_async(get_result(url))
    echo_utf8(format_output(result, pretty, data_only, output_format))


@app.command("lords-by-type")
def get_lords_by_type(
    for_date: str = typer.Argument(..., help="Date for composition (YYYY-MM-DD)"),
    pretty: bool = typer.Option(False, "--pretty", "-p", help="Pretty-print JSON output"),
    data_only: bool = typer.Option(False, "--data-only", "-d", help="Return data only"),
    output_format: OutputFormat = typer.Option(
        OutputFormat.JSON, "--format", "-f", help="Output format: json, table, markdown"
    ),
) -> None:
    """
    Get Lords breakdown by peerage type.

    Returns counts by type: hereditary, life peers, bishops, etc.
    """
    url = f"{MEMBERS_API_BASE}/Parties/LordsByType/{for_date}"
    result = run_async(get_result(url))
    echo_utf8(format_output(result, pretty, data_only, output_format))


@app.command("spokespersons")
def get_spokespersons(
    party_id: int = typer.Argument(..., help="Party ID"),
    pretty: bool = typer.Option(False, "--pretty", "-p", help="Pretty-print JSON output"),
    data_only: bool = typer.Option(False, "--data-only", "-d", help="Return data only"),
    output_format: OutputFormat = typer.Option(
        OutputFormat.JSON, "--format", "-f", help="Output format: json, table, markdown"
    ),
) -> None:
    """
    Get party spokespersons and their portfolios.

    Returns shadow ministers or party speakers on policy areas.
    """
    url = build_url(
        f"{MEMBERS_API_BASE}/Posts/Spokespersons",
        {"partyId": party_id},
    )
    result = run_async(get_result(url))
    echo_utf8(format_output(result, pretty, data_only, output_format))


@app.command("government-posts")
def get_government_posts(
    pretty: bool = typer.Option(False, "--pretty", "-p", help="Pretty-print JSON output"),
    data_only: bool = typer.Option(False, "--data-only", "-d", help="Return data only"),
    output_format: OutputFormat = typer.Option(
        OutputFormat.JSON, "--format", "-f", help="Output format: json, table, markdown"
    ),
) -> None:
    """
    Get all current government ministerial positions.

    Returns cabinet and government positions with current holders.
    """
    url = f"{MEMBERS_API_BASE}/Posts/GovernmentPosts"
    result = run_async(get_result(url))
    echo_utf8(format_output(result, pretty, data_only, output_format))


@app.command("opposition-posts")
def get_opposition_posts(
    pretty: bool = typer.Option(False, "--pretty", "-p", help="Pretty-print JSON output"),
    data_only: bool = typer.Option(False, "--data-only", "-d", help="Return data only"),
    output_format: OutputFormat = typer.Option(
        OutputFormat.JSON, "--format", "-f", help="Output format: json, table, markdown"
    ),
) -> None:
    """
    Get all current opposition frontbench positions.

    Returns shadow cabinet positions with current holders.
    """
    url = f"{MEMBERS_API_BASE}/Posts/OppositionPosts"
    result = run_async(get_result(url))
    echo_utf8(format_output(result, pretty, data_only, output_format))


@app.command("answering-bodies")
def get_answering_bodies(
    pretty: bool = typer.Option(False, "--pretty", "-p", help="Pretty-print JSON output"),
    data_only: bool = typer.Option(False, "--data-only", "-d", help="Return data only"),
    output_format: OutputFormat = typer.Option(
        OutputFormat.JSON, "--format", "-f", help="Output format: json, table, markdown"
    ),
) -> None:
    """
    Get government departments and parliamentary responsibilities.

    Returns department names, abbreviations, and policy responsibilities.
    """
    url = f"{MEMBERS_API_BASE}/Reference/AnsweringBodies"
    result = run_async(get_result(url))
    echo_utf8(format_output(result, pretty, data_only, output_format))


@app.command("departments")
def get_departments(
    pretty: bool = typer.Option(False, "--pretty", "-p", help="Pretty-print JSON output"),
    data_only: bool = typer.Option(False, "--data-only", "-d", help="Return data only"),
    output_format: OutputFormat = typer.Option(
        OutputFormat.JSON, "--format", "-f", help="Output format: json, table, markdown"
    ),
) -> None:
    """
    Get list of all government departments.

    Returns government structure and department information.
    """
    url = f"{MEMBERS_API_BASE}/Reference/Departments"
    result = run_async(get_result(url))
    echo_utf8(format_output(result, pretty, data_only, output_format))


@app.command("policy-interests")
def get_policy_interests(
    pretty: bool = typer.Option(False, "--pretty", "-p", help="Pretty-print JSON output"),
    data_only: bool = typer.Option(False, "--data-only", "-d", help="Return data only"),
    output_format: OutputFormat = typer.Option(
        OutputFormat.JSON, "--format", "-f", help="Output format: json, table, markdown"
    ),
) -> None:
    """
    Get policy interest reference data.

    Returns policy areas and categories for filtering member searches.
    """
    url = f"{MEMBERS_API_BASE}/Reference/PolicyInterests"
    result = run_async(get_result(url))
    echo_utf8(format_output(result, pretty, data_only, output_format))


@app.command("lords-staff-interests")
def search_lords_staff_interests(
    search_term: str = typer.Argument(..., help="Search term for staff names or interests"),
    pretty: bool = typer.Option(False, "--pretty", "-p", help="Pretty-print JSON output"),
    data_only: bool = typer.Option(False, "--data-only", "-d", help="Return data only"),
    output_format: OutputFormat = typer.Option(
        OutputFormat.JSON, "--format", "-f", help="Output format: json, table, markdown"
    ),
) -> None:
    """
    Search staff interests declared by Lords.

    Returns staff interests matching the search term.
    """
    url = f"{MEMBERS_API_BASE}/LordsInterests/Staff?searchTerm={quote(search_term)}"
    result = run_async(get_result(url))
    echo_utf8(format_output(result, pretty, data_only, output_format))
