"""Committees API tools for committee info, meetings, and evidence."""

from urllib.parse import quote

from mcp.server.fastmcp import FastMCP

from uk_parliament_mcp.config import COMMITTEES_API_BASE
from uk_parliament_mcp.http_client import build_url, get_result


def register_tools(mcp: FastMCP) -> None:
    """Register committees tools with the MCP server."""

    @mcp.tool()
    async def get_committee_meetings(from_date: str, to_date: str) -> str:
        """Find committee meetings and hearings by date range | committee meetings, parliamentary hearings, committee schedule, committee calendar, when committees meet | Use for finding committee schedules, planning attendance, or researching past committee activity | Returns meeting details including committees, dates, times, and topics | Covers both Commons and Lords committees

        Args:
            from_date: Start date. Format: YYYY-MM-DD. Example: 2024-01-15
            to_date: End date. Format: YYYY-MM-DD. Must be after start date.

        Returns:
            Meeting details including committees, dates, times, and topics.
        """
        url = f"{COMMITTEES_API_BASE}/Broadcast/Meetings?FromDate={quote(from_date)}&ToDate={quote(to_date)}"
        return await get_result(url)

    @mcp.tool()
    async def search_committees(search_term: str) -> str:
        """Search for parliamentary committees by name or subject area. Use when you need to find which committee covers a specific policy area or when researching committee work.

        Args:
            search_term: Search term for committee names or subject areas (e.g. 'Treasury', 'Health', 'Defence').

        Returns:
            Matching committees with details.
        """
        url = f"{COMMITTEES_API_BASE}/Committees?SearchTerm={quote(search_term)}"
        return await get_result(url)

    @mcp.tool()
    async def get_committee_types() -> str:
        """Get all types of parliamentary committees (e.g., Select Committee, Public Bill Committee, Delegated Legislation Committee). Use when understanding committee structures or finding the right committee type.

        Returns:
            All committee types with descriptions.
        """
        url = f"{COMMITTEES_API_BASE}/CommitteeType"
        return await get_result(url)

    @mcp.tool()
    async def get_committee_by_id(
        committee_id: int,
        include_banners: bool = False,
        show_on_website_only: bool = True,
    ) -> str:
        """Get comprehensive committee profile and membership details | committee information, committee members, committee purpose, parliamentary committee, scrutiny committee | Use for understanding committee roles, finding committee members, or researching committee activities | Returns full committee details including purpose, members, departments scrutinized, and contact information

        Args:
            committee_id: Committee ID. Required: get from committee search first. Example: 739
            include_banners: Include banner images. Default: false. May increase response size.
            show_on_website_only: Show only public committees. Default: true. Recommended for general use.

        Returns:
            Full committee details including purpose, members, and contact information.
        """
        url = build_url(
            f"{COMMITTEES_API_BASE}/Committees/{committee_id}",
            {
                "includeBanners": include_banners,
                "showOnWebsiteOnly": show_on_website_only,
            },
        )
        return await get_result(url)

    @mcp.tool()
    async def get_events(
        committee_id: int | None = None,
        committee_business_id: int | None = None,
        search_term: str | None = None,
        start_date_from: str | None = None,
        start_date_to: str | None = None,
        end_date_from: str | None = None,
        location_id: int | None = None,
        exclude_cancelled_events: bool | None = None,
        sort_ascending: bool | None = None,
        event_type_id: int | None = None,
        include_event_attendees: bool = False,
        show_on_website_only: bool = True,
        skip: int = 0,
        take: int = 30,
    ) -> str:
        """Search for committee events with flexible filtering options. Use when you need to find meetings, hearings, or other committee activities by date, location, or committee. Supports filtering by start/end dates, house, event type, and location.

        Args:
            committee_id: Optional: filter by specific committee ID.
            committee_business_id: Optional: filter by committee business ID.
            search_term: Optional: search term for event titles or content.
            start_date_from: Optional: start date from in YYYY-MM-DD format.
            start_date_to: Optional: start date to in YYYY-MM-DD format.
            end_date_from: Optional: end date from in YYYY-MM-DD format.
            location_id: Optional: location ID to filter events.
            exclude_cancelled_events: Optional: exclude cancelled events.
            sort_ascending: Optional: sort ascending by date.
            event_type_id: Optional: filter by event type ID.
            include_event_attendees: Include event attendees in response.
            show_on_website_only: Show only events visible on website.
            skip: Number of records to skip (for pagination).
            take: Number of records to return (default 30, max 100).

        Returns:
            Committee events matching the criteria.
        """
        url = build_url(
            f"{COMMITTEES_API_BASE}/Events",
            {
                "CommitteeId": committee_id,
                "CommitteeBusinessId": committee_business_id,
                "SearchTerm": search_term,
                "StartDateFrom": start_date_from,
                "StartDateTo": start_date_to,
                "EndDateFrom": end_date_from,
                "LocationId": location_id,
                "ExcludeCancelledEvents": exclude_cancelled_events,
                "SortAscending": sort_ascending,
                "EventTypeId": event_type_id,
                "IncludeEventAttendees": include_event_attendees,
                "ShowOnWebsiteOnly": show_on_website_only,
                "Skip": skip,
                "Take": take,
            },
        )
        return await get_result(url)

    @mcp.tool()
    async def get_event_by_id(
        event_id: int,
        show_on_website_only: bool = True,
    ) -> str:
        """Get detailed information about a specific committee event by ID. Use when you need complete event details including activities, attendees, committees involved, and related business.

        Args:
            event_id: Unique event ID number.
            show_on_website_only: Show only events visible on website.

        Returns:
            Detailed information about the event.
        """
        url = build_url(
            f"{COMMITTEES_API_BASE}/Events/{event_id}",
            {"showOnWebsiteOnly": show_on_website_only},
        )
        return await get_result(url)

    @mcp.tool()
    async def get_committee_events(
        committee_id: int,
        committee_business_id: int | None = None,
        search_term: str | None = None,
        start_date_from: str | None = None,
        start_date_to: str | None = None,
        end_date_from: str | None = None,
        location_id: int | None = None,
        exclude_cancelled_events: bool | None = None,
        sort_ascending: bool | None = None,
        event_type_id: int | None = None,
        include_event_attendees: bool = False,
        show_on_website_only: bool = True,
        skip: int = 0,
        take: int = 30,
    ) -> str:
        """Get events for a specific committee by committee ID. Use when you want to see all meetings and activities for a particular committee, with options to filter by date range, business, and event type.

        Args:
            committee_id: Committee ID to get events for.
            committee_business_id: Optional: filter by committee business ID.
            search_term: Optional: search term for event titles or content.
            start_date_from: Optional: start date from in YYYY-MM-DD format.
            start_date_to: Optional: start date to in YYYY-MM-DD format.
            end_date_from: Optional: end date from in YYYY-MM-DD format.
            location_id: Optional: location ID to filter events.
            exclude_cancelled_events: Optional: exclude cancelled events.
            sort_ascending: Optional: sort ascending by date.
            event_type_id: Optional: filter by event type ID.
            include_event_attendees: Include event attendees in response.
            show_on_website_only: Show only events visible on website.
            skip: Number of records to skip (for pagination).
            take: Number of records to return (default 30, max 100).

        Returns:
            Events for the specified committee.
        """
        url = build_url(
            f"{COMMITTEES_API_BASE}/Committees/{committee_id}/Events",
            {
                "CommitteeBusinessId": committee_business_id,
                "SearchTerm": search_term,
                "StartDateFrom": start_date_from,
                "StartDateTo": start_date_to,
                "EndDateFrom": end_date_from,
                "LocationId": location_id,
                "ExcludeCancelledEvents": exclude_cancelled_events,
                "SortAscending": sort_ascending,
                "EventTypeId": event_type_id,
                "IncludeEventAttendees": include_event_attendees,
                "ShowOnWebsiteOnly": show_on_website_only,
                "Skip": skip,
                "Take": take,
            },
        )
        return await get_result(url)

    @mcp.tool()
    async def get_committee_members(
        committee_id: int,
        membership_status: str | None = None,
        show_on_website_only: bool = True,
        skip: int = 0,
        take: int = 30,
    ) -> str:
        """Get members and staff of a specific committee by committee ID. Use when you need to know who serves on a committee, their roles, and membership status (current/former). Returns both elected members and lay members.

        Args:
            committee_id: Committee ID to get members for.
            membership_status: Optional: filter by membership status (e.g. 'Current', 'Former').
            show_on_website_only: Show only members visible on website.
            skip: Number of records to skip (for pagination).
            take: Number of records to return (default 30, max 100).

        Returns:
            Members and staff of the committee.
        """
        url = build_url(
            f"{COMMITTEES_API_BASE}/Committees/{committee_id}/Members",
            {
                "MembershipStatus": membership_status,
                "ShowOnWebsiteOnly": show_on_website_only,
                "Skip": skip,
                "Take": take,
            },
        )
        return await get_result(url)

    @mcp.tool()
    async def get_publications(
        search_term: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        committee_business_id: int | None = None,
        committee_id: int | None = None,
        show_on_website_only: bool = True,
        skip: int = 0,
        take: int = 30,
    ) -> str:
        """Search for committee publications including reports, government responses, and other documents. Use when researching committee outputs, finding reports on specific topics, or tracking publication dates and paper numbers.

        Args:
            search_term: Optional: search term for publication titles or content.
            start_date: Optional: start date in YYYY-MM-DD format.
            end_date: Optional: end date in YYYY-MM-DD format.
            committee_business_id: Optional: committee business ID to filter by.
            committee_id: Optional: committee ID to filter by.
            show_on_website_only: Show only publications visible on website.
            skip: Number of records to skip (for pagination).
            take: Number of records to return (default 30, max 100).

        Returns:
            Committee publications matching the criteria.
        """
        url = build_url(
            f"{COMMITTEES_API_BASE}/Publications",
            {
                "SearchTerm": search_term,
                "StartDate": start_date,
                "EndDate": end_date,
                "CommitteeBusinessId": committee_business_id,
                "CommitteeId": committee_id,
                "ShowOnWebsiteOnly": show_on_website_only,
                "Skip": skip,
                "Take": take,
            },
        )
        return await get_result(url)

    @mcp.tool()
    async def get_publication_by_id(
        publication_id: int,
        show_on_website_only: bool = True,
    ) -> str:
        """Get detailed information about a specific committee publication by ID. Use when you need complete publication details including documents, HC numbers, government responses, and associated committee business.

        Args:
            publication_id: Unique publication ID number.
            show_on_website_only: Show only publications visible on website.

        Returns:
            Detailed information about the publication.
        """
        url = build_url(
            f"{COMMITTEES_API_BASE}/Publications/{publication_id}",
            {"showOnWebsiteOnly": show_on_website_only},
        )
        return await get_result(url)

    @mcp.tool()
    async def get_written_evidence(
        committee_business_id: int | None = None,
        committee_id: int | None = None,
        search_term: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        show_on_website_only: bool = True,
        skip: int = 0,
        take: int = 30,
    ) -> str:
        """Search for written evidence submissions to committees. Use when researching stakeholder submissions, witness statements, or public input to committee inquiries. Can filter by committee, business, witness names, or publication dates.

        Args:
            committee_business_id: Optional: committee business ID to filter by.
            committee_id: Optional: committee ID to filter by.
            search_term: Optional: search term for evidence content or witness names.
            start_date: Optional: start date in YYYY-MM-DD format.
            end_date: Optional: end date in YYYY-MM-DD format.
            show_on_website_only: Show only evidence visible on website.
            skip: Number of records to skip (for pagination).
            take: Number of records to return (default 30, max 100).

        Returns:
            Written evidence submissions matching the criteria.
        """
        url = build_url(
            f"{COMMITTEES_API_BASE}/WrittenEvidence",
            {
                "CommitteeBusinessId": committee_business_id,
                "CommitteeId": committee_id,
                "SearchTerm": search_term,
                "StartDate": start_date,
                "EndDate": end_date,
                "ShowOnWebsiteOnly": show_on_website_only,
                "Skip": skip,
                "Take": take,
            },
        )
        return await get_result(url)

    @mcp.tool()
    async def get_oral_evidence(
        committee_business_id: int | None = None,
        committee_id: int | None = None,
        search_term: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        show_on_website_only: bool = True,
        skip: int = 0,
        take: int = 30,
    ) -> str:
        """Search for oral evidence sessions from committee hearings. Use when researching witness testimonies, committee hearings, or transcripts from evidence sessions. Can filter by committee, business, witness names, or meeting dates.

        Args:
            committee_business_id: Optional: committee business ID to filter by.
            committee_id: Optional: committee ID to filter by.
            search_term: Optional: search term for evidence content or witness names.
            start_date: Optional: start date in YYYY-MM-DD format.
            end_date: Optional: end date in YYYY-MM-DD format.
            show_on_website_only: Show only evidence visible on website.
            skip: Number of records to skip (for pagination).
            take: Number of records to return (default 30, max 100).

        Returns:
            Oral evidence sessions matching the criteria.
        """
        url = build_url(
            f"{COMMITTEES_API_BASE}/OralEvidence",
            {
                "CommitteeBusinessId": committee_business_id,
                "CommitteeId": committee_id,
                "SearchTerm": search_term,
                "StartDate": start_date,
                "EndDate": end_date,
                "ShowOnWebsiteOnly": show_on_website_only,
                "Skip": skip,
                "Take": take,
            },
        )
        return await get_result(url)

    @mcp.tool()
    async def get_committee_business(
        search_term: str | None = None,
        committee_id: int | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        business_type_id: int | None = None,
        status: str | None = None,
        currently_accepting_evidence: bool | None = None,
        show_on_website_only: bool = True,
        skip: int = 0,
        take: int = 30,
    ) -> str:
        """Search for committee business (inquiries, investigations) | committee inquiries, investigations, call for evidence |
        Use to find committee inquiries by topic, status, or whether accepting evidence.
        Returns committee business items matching the criteria.

        Args:
            search_term: Optional: search term for business titles or content.
            committee_id: Optional: committee ID to filter by.
            date_from: Optional: start date in YYYY-MM-DD format.
            date_to: Optional: end date in YYYY-MM-DD format.
            business_type_id: Optional: business type ID (from get_committee_business_types).
            status: Optional: status filter (e.g. 'Open', 'Closed').
            currently_accepting_evidence: Optional: filter to inquiries accepting evidence.
            show_on_website_only: Show only items visible on website.
            skip: Number of records to skip (for pagination).
            take: Number of records to return (default 30, max 100).

        Returns:
            Committee business items matching the criteria.
        """
        url = build_url(
            f"{COMMITTEES_API_BASE}/CommitteeBusiness",
            {
                "SearchTerm": search_term,
                "CommitteeId": committee_id,
                "DateFrom": date_from,
                "DateTo": date_to,
                "BusinessTypeId": business_type_id,
                "Status": status,
                "CurrentlyAcceptingEvidence": currently_accepting_evidence,
                "ShowOnWebsiteOnly": show_on_website_only,
                "Skip": skip,
                "Take": take,
            },
        )
        return await get_result(url)

    @mcp.tool()
    async def get_committee_business_by_id(
        business_id: int,
        show_on_website_only: bool = True,
    ) -> str:
        """Get detailed information about a specific committee business item | inquiry details, investigation details |
        Use when you need complete details about a specific inquiry or investigation.
        Returns full business details including evidence calls and reports.

        Args:
            business_id: Committee business ID.
            show_on_website_only: Show only items visible on website.

        Returns:
            Detailed information about the committee business.
        """
        url = build_url(
            f"{COMMITTEES_API_BASE}/CommitteeBusiness/{business_id}",
            {"showOnWebsiteOnly": show_on_website_only},
        )
        return await get_result(url)

    @mcp.tool()
    async def get_committee_business_types() -> str:
        """Get all types of committee business | business types, inquiry types |
        Use to understand different types of committee work (inquiries, debates, etc.).
        Returns list of business types with descriptions.

        Returns:
            All committee business types with descriptions.
        """
        url = f"{COMMITTEES_API_BASE}/CommitteeBusinessType"
        return await get_result(url)

    @mcp.tool()
    async def get_committees_next_events(
        house: int | None = None,
        event_from_date: str | None = None,
        skip: int = 0,
        take: int = 30,
    ) -> str:
        """Get upcoming events for all committees | next meetings, upcoming hearings |
        Use to see what committee meetings are scheduled.
        Returns list of committees with their next scheduled event.

        Args:
            house: Optional: filter by house (1 = Commons, 2 = Lords).
            event_from_date: Optional: start date in YYYY-MM-DD format (default today).
            skip: Number of records to skip (for pagination).
            take: Number of records to return (default 30).

        Returns:
            Committees with their next scheduled events.
        """
        url = build_url(
            f"{COMMITTEES_API_BASE}/Committees/NextEvent",
            {
                "House": house,
                "EventFromDate": event_from_date,
                "Skip": skip,
                "Take": take,
            },
        )
        return await get_result(url)

    @mcp.tool()
    async def get_committee_staff(
        committee_id: int,
        membership_status: str | None = None,
        show_on_website_only: bool = True,
        skip: int = 0,
        take: int = 30,
    ) -> str:
        """Get staff members of a committee | committee staff, clerks, advisers |
        Use to find who supports a committee's work.
        Returns staff members with their roles.

        Args:
            committee_id: Committee ID.
            membership_status: Optional: filter by status (e.g. 'Current', 'Former').
            show_on_website_only: Show only staff visible on website.
            skip: Number of records to skip (for pagination).
            take: Number of records to return (default 30).

        Returns:
            Staff members of the committee.
        """
        url = build_url(
            f"{COMMITTEES_API_BASE}/Committees/{committee_id}/Staff",
            {
                "MembershipStatus": membership_status,
                "ShowOnWebsiteOnly": show_on_website_only,
                "Skip": skip,
                "Take": take,
            },
        )
        return await get_result(url)

    @mcp.tool()
    async def get_committee_publications_summary(committee_id: int) -> str:
        """Get summary of publications grouped by type | publication overview, report counts |
        Use to get an overview of a committee's publication output.
        Returns publication counts by type.

        Args:
            committee_id: Committee ID.

        Returns:
            Summary of publications grouped by type.
        """
        url = f"{COMMITTEES_API_BASE}/Committees/{committee_id}/Publications/Summary"
        return await get_result(url)

    @mcp.tool()
    async def get_event_activities(event_id: int) -> str:
        """Get activities scheduled for an event | meeting agenda, event schedule |
        Use to see what's on the agenda for a committee meeting.
        Returns activities planned for the event.

        Args:
            event_id: Event ID.

        Returns:
            Activities scheduled for the event.
        """
        url = f"{COMMITTEES_API_BASE}/Events/{event_id}/Activities"
        return await get_result(url)

    @mcp.tool()
    async def get_event_attendance(event_id: int) -> str:
        """Get attendance record for an event | who attended, meeting attendance |
        Use to see which members attended a committee meeting.
        Returns attendance list for the event.

        Args:
            event_id: Event ID.

        Returns:
            Attendance record for the event.
        """
        url = f"{COMMITTEES_API_BASE}/Events/{event_id}/Attendance"
        return await get_result(url)

    @mcp.tool()
    async def get_member_committee_memberships(
        member_ids: str,
        membership_status: str | None = None,
        committee_category: str | None = None,
    ) -> str:
        """Get committee memberships for one or more members | member committees, MP committees |
        Use to find which committees a member serves on.
        Returns committee memberships for the specified members.

        Args:
            member_ids: Comma-separated list of member IDs (e.g. '4514' or '4514,172').
            membership_status: Optional: filter by status (e.g. 'Current', 'Former').
            committee_category: Optional: filter by committee category.

        Returns:
            Committee memberships for the members.
        """
        url = build_url(
            f"{COMMITTEES_API_BASE}/Members",
            {
                "Members": member_ids,
                "MembershipStatus": membership_status,
                "CommitteeCategory": committee_category,
            },
        )
        return await get_result(url)

    @mcp.tool()
    async def get_oral_evidence_by_id(
        evidence_id: int,
        show_on_website_only: bool = True,
    ) -> str:
        """Get detailed oral evidence by ID | witness testimony details |
        Use to get full details of a specific oral evidence session.
        Returns complete oral evidence record.

        Args:
            evidence_id: Oral evidence ID.
            show_on_website_only: Show only evidence visible on website.

        Returns:
            Detailed oral evidence record.
        """
        url = build_url(
            f"{COMMITTEES_API_BASE}/OralEvidence/{evidence_id}",
            {"showOnWebsiteOnly": show_on_website_only},
        )
        return await get_result(url)

    @mcp.tool()
    async def get_written_evidence_by_id(
        evidence_id: int,
        show_on_website_only: bool = True,
    ) -> str:
        """Get detailed written evidence by ID | written submission details |
        Use to get full details of a specific written evidence submission.
        Returns complete written evidence record.

        Args:
            evidence_id: Written evidence ID.
            show_on_website_only: Show only evidence visible on website.

        Returns:
            Detailed written evidence record.
        """
        url = build_url(
            f"{COMMITTEES_API_BASE}/WrittenEvidence/{evidence_id}",
            {"showOnWebsiteOnly": show_on_website_only},
        )
        return await get_result(url)

    @mcp.tool()
    async def get_committee_publication_types() -> str:
        """Get all types of committee publications | report types, document types |
        Use to understand different types of committee publications.
        Returns list of publication types with descriptions.

        Returns:
            All committee publication types with descriptions.
        """
        url = f"{COMMITTEES_API_BASE}/PublicationType"
        return await get_result(url)

    @mcp.tool()
    async def search_bill_petitions(
        committee_business_id: int | None = None,
        committee_id: int | None = None,
        search_term: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        show_on_website_only: bool = True,
        skip: int = 0,
        take: int = 30,
    ) -> str:
        """Search petitions on Private Bills | private bill petitions, public petitions | Use to find public petitions submitted on Private Bills | Returns petitions with details

        Args:
            committee_business_id: Optional: filter by committee business ID.
            committee_id: Optional: filter by committee ID.
            search_term: Optional: search term for petition content.
            start_date: Optional: start date in YYYY-MM-DD format.
            end_date: Optional: end date in YYYY-MM-DD format.
            show_on_website_only: Show only petitions visible on website.
            skip: Number of records to skip (for pagination).
            take: Number of records to return (default 30).

        Returns:
            Bill petitions matching the criteria.
        """
        url = build_url(
            f"{COMMITTEES_API_BASE}/BillPetitions",
            {
                "CommitteeBusinessId": committee_business_id,
                "CommitteeId": committee_id,
                "SearchTerm": search_term,
                "StartDate": start_date,
                "EndDate": end_date,
                "ShowOnWebsiteOnly": show_on_website_only,
                "Skip": skip,
                "Take": take,
            },
        )
        return await get_result(url)

    @mcp.tool()
    async def get_committee_business_publications_summary(business_id: int) -> str:
        """Get publication summary for an inquiry | inquiry publications, report groups | Use to see publication types for a committee business/inquiry | Returns publication groups with counts

        Args:
            business_id: Committee business ID.

        Returns:
            Summary of publications grouped by type for the inquiry.
        """
        url = f"{COMMITTEES_API_BASE}/CommitteeBusiness/{business_id}/Publications/Summary"
        return await get_result(url)
