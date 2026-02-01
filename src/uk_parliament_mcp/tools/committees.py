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
