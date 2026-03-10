"""Members API tools for MPs, Lords, constituencies, and parties."""

from urllib.parse import quote

from mcp.server.fastmcp import FastMCP

from uk_parliament_mcp.config import MEMBERS_API_BASE
from uk_parliament_mcp.http_client import build_url, get_result


def register_tools(mcp: FastMCP) -> None:
    """Register member tools with the MCP server."""

    @mcp.tool()
    async def get_member_by_name(name: str) -> str:
        """Search for MPs and Lords by name with comprehensive member details | find MP, search politician, lookup member, who is, member search, parliamentary representative | Use for identifying members, checking spellings, finding member IDs, or getting basic member information | Returns member profiles with names, parties, constituencies, and current status

        Args:
            name: Full or partial name to search for. Examples: 'Boris Johnson', 'Keir Starmer', 'Smith'. Searches current and former members.

        Returns:
            Member profiles with names, parties, constituencies, and current status.
        """
        url = f"{MEMBERS_API_BASE}/Members/Search?Name={quote(name)}"
        return await get_result(url)

    @mcp.tool()
    async def get_answering_bodies(
        name_contains: str | None = None,
    ) -> str:
        """Get government departments and their parliamentary responsibilities | government departments, ministries, answering bodies, policy areas, department structure, who answers questions | Use for understanding government structure, finding responsible departments, or determining who answers questions on specific topics | Returns department names, abbreviations, and policy responsibilities

        Args:
            name_contains: Filter by partial name match. Example: 'Treasury', 'Health'.

        Returns:
            Department names, abbreviations, and policy responsibilities.
        """
        url = build_url(
            f"{MEMBERS_API_BASE}/Reference/AnsweringBodies",
            {
                "nameContains": name_contains,
            },
        )
        return await get_result(url)

    @mcp.tool()
    async def get_member_by_id(member_id: int) -> str:
        """Get comprehensive member profile by ID with full parliamentary details | member details, MP profile, member information, parliamentary roles, constituency data | Use when you have a member ID and need complete biographical, political, and contact information | Returns detailed member data including roles, constituency, party, and career information

        Args:
            member_id: Parliament member ID. Required: get from member search first. Example: 1423

        Returns:
            Detailed member data including roles, constituency, party, and career information.
        """
        url = f"{MEMBERS_API_BASE}/Members/{member_id}"
        return await get_result(url)

    @mcp.tool()
    async def edms_for_member_id(member_id: int) -> str:
        """Get all Early Day Motions signed by a specific MP. Use when you want to see what issues a particular member has supported or their political priorities through EDM signatures.

        Args:
            member_id: Parliament member ID to get EDMs for.

        Returns:
            List of Early Day Motions signed by the member.
        """
        url = f"{MEMBERS_API_BASE}/Members/{member_id}/Edms"
        return await get_result(url)

    @mcp.tool()
    async def parties_list_by_house(house: int) -> str:
        """Get list of active political parties in either House of Commons (1) or House of Lords (2). Use when you need to know current party representation or party structures in Parliament.

        Args:
            house: House number: 1 for Commons, 2 for Lords.

        Returns:
            List of active political parties in the specified house.
        """
        url = f"{MEMBERS_API_BASE}/Parties/GetActive/{house}"
        return await get_result(url)

    @mcp.tool()
    async def get_departments(
        name_contains: str | None = None,
    ) -> str:
        """Get list of all government departments. Use when you need to know the structure of government or which department handles specific policy areas.

        Args:
            name_contains: Filter by partial name match. Example: 'Treasury', 'Health'.

        Returns:
            List of all government departments.
        """
        url = build_url(
            f"{MEMBERS_API_BASE}/Reference/Departments",
            {
                "nameContains": name_contains,
            },
        )
        return await get_result(url)

    @mcp.tool()
    async def get_contributions(member_id: int) -> str:
        """Get summary of parliamentary contributions (speeches, questions, interventions) made by a specific member. Use when analyzing an MP or Lord's parliamentary activity and participation levels.

        Args:
            member_id: Parliament member ID to get contribution summary for.

        Returns:
            Summary of parliamentary contributions for the member.
        """
        url = f"{MEMBERS_API_BASE}/Members/{member_id}/ContributionSummary?page=1"
        return await get_result(url)

    @mcp.tool()
    async def get_constituencies(
        search_text: str | None = None,
        skip: int | None = None,
        take: int | None = None,
    ) -> str:
        """Search and list UK parliamentary constituencies | constituency search, find constituency, browse constituencies | Use when you need constituency information, want to search by name, or need constituency data for analysis | Returns list of UK parliamentary constituencies

        Args:
            search_text: Optional filter by constituency name (partial match).
            skip: Number of constituencies to skip (for pagination).
            take: Number of constituencies to return (default 20, max 100).

        Returns:
            List of UK parliamentary constituencies.
        """
        url = build_url(
            f"{MEMBERS_API_BASE}/Location/Constituency/Search",
            {"searchText": search_text, "skip": skip, "take": take},
        )
        return await get_result(url)

    @mcp.tool()
    async def get_election_results_for_constituency(constituency_id: int) -> str:
        """Get historical election results for a specific constituency. Use when researching constituency voting patterns, election history, or past electoral outcomes for a particular area.

        Args:
            constituency_id: Unique constituency ID number.

        Returns:
            Historical election results for the constituency.
        """
        url = f"{MEMBERS_API_BASE}/Location/Constituency/{constituency_id}/ElectionResults"
        return await get_result(url)

    @mcp.tool()
    async def get_lords_interests_staff(search_term: str) -> str:
        """Search staff interests declared by Lords | Lords staff, staff conflicts, staff interests | Use to investigate potential conflicts of interest related to Lords' staff | Returns staff interests matching the search term

        Args:
            search_term: Search term for staff names or interests.

        Returns:
            Staff interests declared by Lords matching the search term.
        """
        url = f"{MEMBERS_API_BASE}/LordsInterests/Staff?searchTerm={quote(search_term)}"
        return await get_result(url)

    @mcp.tool()
    async def get_members_biography(member_id: int) -> str:
        """Get comprehensive member biography and personal history | MP background, life story, career details, education, personal info, political experience | Use for researching member backgrounds, writing profiles, understanding political journey | Returns detailed biographical data including education, career timeline, and political milestones

        Args:
            member_id: Parliament member ID. Required: get from member search first. Returns comprehensive biographical information.

        Returns:
            Detailed biographical data including education, career timeline, and political milestones.
        """
        url = f"{MEMBERS_API_BASE}/Members/{member_id}/Biography"
        return await get_result(url)

    @mcp.tool()
    async def get_members_contact(member_id: int) -> str:
        """Get member contact details and office information | MP contact, phone number, email, office address, constituency office | Use for contacting members, finding office locations, or getting official contact details | Returns phone numbers, addresses, and official contact information

        Args:
            member_id: Parliament member ID. Required: get from member search first. Returns official contact details.

        Returns:
            Phone numbers, addresses, and official contact information.
        """
        url = f"{MEMBERS_API_BASE}/Members/{member_id}/Contact"
        return await get_result(url)

    @mcp.tool()
    async def search_members(
        name: str | None = None,
        location: str | None = None,
        post_title: str | None = None,
        party_id: int | None = None,
        house: int | None = None,
        constituency_id: int | None = None,
        name_starts_with: str | None = None,
        gender: str | None = None,
        membership_started_since: str | None = None,
        membership_ended_since: str | None = None,
        was_member_on_or_after: str | None = None,
        was_member_on_or_before: str | None = None,
        was_member_of_house: int | None = None,
        is_eligible: bool | None = None,
        is_current_member: bool | None = None,
        policy_interest_id: int | None = None,
        experience: str | None = None,
        skip: int = 0,
        take: int = 20,
    ) -> str:
        """Search for current MPs and Lords with comprehensive filtering options. Use when you need to find members by name, location, party, constituency, gender, posts held, or policy interests. Supports advanced search criteria including membership dates and eligibility status.

        Args:
            name: Optional: full or partial name to search for.
            location: Optional: location or constituency name.
            post_title: Optional: post title (e.g. 'Minister', 'Secretary of State').
            party_id: Optional: party ID to filter by.
            house: Optional: house number (1=Commons, 2=Lords).
            constituency_id: Optional: constituency ID to filter by.
            name_starts_with: Optional: filter names starting with specific letter(s).
            gender: Optional: gender filter ('M' or 'F').
            membership_started_since: Optional: membership started since date in YYYY-MM-DD format.
            membership_ended_since: Optional: membership ended since date in YYYY-MM-DD format.
            was_member_on_or_after: Optional: was member on or after date in YYYY-MM-DD format.
            was_member_on_or_before: Optional: was member on or before date in YYYY-MM-DD format.
            was_member_of_house: Optional: was member of house (1=Commons, 2=Lords).
            is_eligible: Optional: filter by eligibility status.
            is_current_member: Optional: filter by current membership status.
            policy_interest_id: Optional: policy interest ID to filter by.
            experience: Optional: search term for professional experience.
            skip: Number of records to skip (for pagination).
            take: Number of records to return (default 20, max 100).

        Returns:
            Matching member profiles with comprehensive details.
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
        return await get_result(url)

    @mcp.tool()
    async def get_member_experience(member_id: int) -> str:
        """Get professional experience and career background of a member by ID. Use when researching a member's qualifications, previous employment, education, or professional history before entering Parliament.

        Args:
            member_id: Parliament member ID to get professional experience for.

        Returns:
            Professional experience and career background of the member.
        """
        url = f"{MEMBERS_API_BASE}/Members/{member_id}/Experience"
        return await get_result(url)

    @mcp.tool()
    async def get_member_focus(member_id: int) -> str:
        """Get areas of focus and policy interests of a member by ID. Use when understanding what issues and policy areas a member prioritizes or specializes in.

        Args:
            member_id: Parliament member ID to get policy focus areas for.

        Returns:
            Areas of focus and policy interests of the member.
        """
        url = f"{MEMBERS_API_BASE}/Members/{member_id}/Focus"
        return await get_result(url)

    @mcp.tool()
    async def get_member_registered_interests(
        member_id: int,
        house: int | None = None,
    ) -> str:
        """Get registered interests of a member by ID and house. Use when investigating potential conflicts of interest, financial interests, or external roles. Shows declared interests like directorships, consultancies, and gifts.

        Args:
            member_id: Parliament member ID to get registered interests for.
            house: Optional: house number (1=Commons, 2=Lords).

        Returns:
            Registered interests of the member.
        """
        url = build_url(
            f"{MEMBERS_API_BASE}/Members/{member_id}/RegisteredInterests",
            {"house": house},
        )
        return await get_result(url)

    @mcp.tool()
    async def get_member_staff(member_id: int) -> str:
        """Get staff members working for a specific MP or Lord by member ID. Use when researching parliamentary office staff, researchers, or support personnel.

        Args:
            member_id: Parliament member ID to get staff details for.

        Returns:
            Staff members working for the member.
        """
        url = f"{MEMBERS_API_BASE}/Members/{member_id}/Staff"
        return await get_result(url)

    @mcp.tool()
    async def get_member_synopsis(member_id: int) -> str:
        """Get a brief synopsis or summary about a member by ID. Use when you need a concise overview of a member's background, role, or key information.

        Args:
            member_id: Parliament member ID to get synopsis for.

        Returns:
            Brief synopsis or summary about the member.
        """
        url = f"{MEMBERS_API_BASE}/Members/{member_id}/Synopsis"
        return await get_result(url)

    @mcp.tool()
    async def get_member_voting(
        member_id: int,
        house: int,
        page: int | None = None,
    ) -> str:
        """Get voting records of a member by ID for a specific house. Use when analyzing how a member votes, their voting patterns, or their stance on particular issues through their voting history.

        Args:
            member_id: Parliament member ID to get voting record for.
            house: House number (1=Commons, 2=Lords).
            page: Optional: page number for pagination.

        Returns:
            Voting records of the member.
        """
        url = build_url(
            f"{MEMBERS_API_BASE}/Members/{member_id}/Voting",
            {"house": house, "page": page},
        )
        return await get_result(url)

    @mcp.tool()
    async def get_member_written_questions(
        member_id: int,
        page: int | None = None,
    ) -> str:
        """Get written questions submitted by a member by ID. Use when researching what questions a member has asked of government departments or their areas of parliamentary inquiry.

        Args:
            member_id: Parliament member ID to get written questions for.
            page: Optional: page number for pagination.

        Returns:
            Written questions submitted by the member.
        """
        url = build_url(
            f"{MEMBERS_API_BASE}/Members/{member_id}/WrittenQuestions",
            {"page": page},
        )
        return await get_result(url)

    @mcp.tool()
    async def get_members_history(member_ids: list[int]) -> str:
        """Get historical information for multiple members by their IDs. Returns name history, party affiliations, and membership details over time. Use when researching how members' details have changed throughout their careers.

        Args:
            member_ids: List of Parliament member IDs to get history for.

        Returns:
            Historical information for the specified members.
        """
        ids_str = ",".join(str(id) for id in member_ids)
        url = build_url(f"{MEMBERS_API_BASE}/Members/History", {"ids": ids_str})
        return await get_result(url)

    @mcp.tool()
    async def get_member_latest_election_result(member_id: int) -> str:
        """Get the latest election result for a member by ID. Use when researching how a member was elected, their constituency performance, vote share, or election margin.

        Args:
            member_id: Parliament member ID to get latest election result for.

        Returns:
            Latest election result for the member.
        """
        url = f"{MEMBERS_API_BASE}/Members/{member_id}/LatestElectionResult"
        return await get_result(url)

    @mcp.tool()
    async def get_member_portrait_url(member_id: int) -> str:
        """Get the portrait image URL for a member by ID. Use when you need a link to a member's official parliamentary portrait photograph.

        Args:
            member_id: Parliament member ID to get portrait URL for.

        Returns:
            Portrait image URL for the member.
        """
        url = f"{MEMBERS_API_BASE}/Members/{member_id}/PortraitUrl"
        return await get_result(url)

    @mcp.tool()
    async def get_member_thumbnail_url(member_id: int) -> str:
        """Get the thumbnail image URL for a member by ID. Use when you need a link to a smaller version of a member's parliamentary photograph for lists or compact displays.

        Args:
            member_id: Parliament member ID to get thumbnail URL for.

        Returns:
            Thumbnail image URL for the member.
        """
        url = f"{MEMBERS_API_BASE}/Members/{member_id}/ThumbnailUrl"
        return await get_result(url)

    @mcp.tool()
    async def get_government_posts() -> str:
        """Get government posts | ministers, cabinet, government positions, Home Secretary, Chancellor |
        List all current government ministerial positions with their holders |
        Returns list of posts with member details

        Returns:
            List of government ministerial positions with current holders.
        """
        url = f"{MEMBERS_API_BASE}/Posts/GovernmentPosts"
        return await get_result(url)

    @mcp.tool()
    async def get_opposition_posts() -> str:
        """Get opposition posts | shadow cabinet, shadow ministers, opposition frontbench |
        List all current opposition frontbench positions with their holders |
        Returns list of posts with member details

        Returns:
            List of opposition frontbench positions with current holders.
        """
        url = f"{MEMBERS_API_BASE}/Posts/OppositionPosts"
        return await get_result(url)

    @mcp.tool()
    async def get_state_of_parties(house: int, for_date: str) -> str:
        """Get party seat counts | party breakdown, seats, composition, majority |
        Get number of seats held by each party in a house |
        Returns party names with seat counts

        Args:
            house: 1 for Commons, 2 for Lords.
            for_date: Date for the party composition (YYYY-MM-DD). Use today's date for current.

        Returns:
            Party names with seat counts for the specified house.
        """
        url = f"{MEMBERS_API_BASE}/Parties/StateOfTheParties/{house}/{for_date}"
        return await get_result(url)

    @mcp.tool()
    async def get_lords_by_type(for_date: str) -> str:
        """Get Lords by peerage type | hereditary, life peers, bishops, crossbench |
        Breakdown of Lords by type of peerage |
        Returns counts by peerage type

        Args:
            for_date: Date for the composition (YYYY-MM-DD). Use today's date for current.

        Returns:
            Counts of Lords by peerage type.
        """
        url = f"{MEMBERS_API_BASE}/Parties/LordsByType/{for_date}"
        return await get_result(url)

    @mcp.tool()
    async def get_spokespersons(party_id: int) -> str:
        """Get party spokespersons | shadow ministers, opposition frontbench, party speakers | Use to find who speaks for a party on specific policy areas | Returns spokespersons with their portfolios

        Args:
            party_id: Party ID (required). Get party IDs from parties_list_by_house.

        Returns:
            List of party spokespersons with their portfolios.
        """
        url = build_url(
            f"{MEMBERS_API_BASE}/Posts/Spokespersons",
            {"partyId": party_id},
        )
        return await get_result(url)

    @mcp.tool()
    async def get_policy_interests() -> str:
        """Get policy interest reference data | policy areas, member interests categories | Use to get IDs for filtering member searches by policy interest | Returns list of policy interest categories

        Returns:
            List of policy interest categories with IDs for use in member searches.
        """
        url = f"{MEMBERS_API_BASE}/Reference/PolicyInterests"
        return await get_result(url)

    @mcp.tool()
    async def get_constituency_by_id(constituency_id: int) -> str:
        """Get a constituency by ID with full details | constituency lookup, find constituency, constituency info | Use when you have a constituency ID and need full details about it | Returns constituency name, boundaries, and related data

        Args:
            constituency_id: Unique constituency ID number.

        Returns:
            Constituency details including name and related information.
        """
        url = f"{MEMBERS_API_BASE}/Location/Constituency/{constituency_id}"
        return await get_result(url)

    @mcp.tool()
    async def get_constituency_latest_election(constituency_id: int) -> str:
        """Get the latest election result for a constituency | constituency election, latest vote, most recent election result | Use when you need the most recent election result for a specific constituency | Returns vote counts, winner, turnout, and candidate details

        Args:
            constituency_id: Unique constituency ID number.

        Returns:
            Latest election result with vote counts, winner, and turnout.
        """
        url = f"{MEMBERS_API_BASE}/Location/Constituency/{constituency_id}/ElectionResult/Latest"
        return await get_result(url)

    @mcp.tool()
    async def get_constituency_election_result(constituency_id: int, election_id: int) -> str:
        """Get a specific election result for a constituency by election ID | constituency election, historic vote, election result | Use when you need a particular election result for a constituency | Returns vote counts, winner, turnout, and candidate details for that election

        Args:
            constituency_id: Unique constituency ID number.
            election_id: Election ID number.

        Returns:
            Election result with vote counts, winner, and turnout for the specified election.
        """
        url = f"{MEMBERS_API_BASE}/Location/Constituency/{constituency_id}/ElectionResult/{election_id}"
        return await get_result(url)

    @mcp.tool()
    async def get_constituency_representations(constituency_id: int) -> str:
        """Get all MP representations for a constituency over time | constituency history, who represented, past MPs | Use when researching which MPs have represented a constituency historically | Returns list of representations with dates and member details

        Args:
            constituency_id: Unique constituency ID number.

        Returns:
            List of representations with member details and date ranges.
        """
        url = f"{MEMBERS_API_BASE}/Location/Constituency/{constituency_id}/Representations"
        return await get_result(url)

    @mcp.tool()
    async def get_constituency_synopsis(constituency_id: int) -> str:
        """Get a brief synopsis or summary for a constituency | constituency overview, constituency description, area summary | Use when you need a concise description or background information about a constituency | Returns text synopsis of the constituency

        Args:
            constituency_id: Unique constituency ID number.

        Returns:
            Text synopsis summarising the constituency.
        """
        url = f"{MEMBERS_API_BASE}/Location/Constituency/{constituency_id}/Synopsis"
        return await get_result(url)

    @mcp.tool()
    async def search_historical_members(
        name: str | None = None,
        date_to_search_for: str | None = None,
        skip: int | None = None,
        take: int | None = None,
    ) -> str:
        """Search historical members of the Commons or Lords | past MPs, historic members, former members, historical search | Use when researching members from historical periods or who were active on a specific date | Returns member profiles matching the historical search criteria

        Args:
            name: Optional name search term (partial match).
            date_to_search_for: Optional date to find members active on that date (YYYY-MM-DD).
            skip: Number of records to skip (for pagination).
            take: Number of records to return (default 20, max 20).

        Returns:
            Member profiles matching the historical search criteria.
        """
        url = build_url(
            f"{MEMBERS_API_BASE}/Members/SearchHistorical",
            {
                "name": name,
                "dateToSearchFor": date_to_search_for,
                "skip": skip,
                "take": take,
            },
        )
        return await get_result(url)

    @mcp.tool()
    async def get_speaker_and_deputies(for_date: str) -> str:
        """Get the Speaker of the Commons and Deputy Speakers for a date | Speaker, Deputy Speaker, House officers | Use when you need to know who was Speaker or a Deputy Speaker on a given date | Returns member details for the Speaker and Deputy Speakers

        Args:
            for_date: Date for which to return the Speaker and Deputy Speakers (YYYY-MM-DD).

        Returns:
            Member details for the Speaker and Deputy Speakers on the given date.
        """
        url = f"{MEMBERS_API_BASE}/Posts/SpeakerAndDeputies/{for_date}"
        return await get_result(url)

    @mcp.tool()
    async def browse_locations(location_type: str, location_name: str) -> str:
        """Browse locations by type and name, returning parent and child locations | location browse, constituency type, country region | Use when exploring the location hierarchy (e.g. countries, regions, constituencies) | Returns list of locations matching the type and name

        Args:
            location_type: Type of location (e.g. 'Constituency', 'Country', 'Region').
            location_name: Name of the location to browse.

        Returns:
            List of parent and child locations matching the criteria.
        """
        url = f"{MEMBERS_API_BASE}/Location/Browse/{quote(location_type)}/{quote(location_name)}"
        return await get_result(url)

    @mcp.tool()
    async def get_lords_interests_register(
        search_term: str | None = None,
        page: int | None = None,
        include_deleted: bool | None = None,
    ) -> str:
        """Search the Lords register of interests | Lords interests, peer interests, Lords declarations, register | Use when investigating Lords' declared interests, financial interests, or outside roles | Returns registered interests matching the search criteria

        Args:
            search_term: Optional search term to filter interests.
            page: Optional page number for pagination (default 0, 20 per page).
            include_deleted: Optional flag to include deleted interests (default False).

        Returns:
            Registered interests matching the search criteria.
        """
        url = build_url(
            f"{MEMBERS_API_BASE}/LordsInterests/Register",
            {
                "searchTerm": search_term,
                "page": page,
                "includeDeleted": include_deleted,
            },
        )
        return await get_result(url)
