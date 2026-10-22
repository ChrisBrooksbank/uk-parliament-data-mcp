"""Lords Business API tools for House of Lords business papers, journals and sittings."""

from urllib.parse import quote

from mcp.server.fastmcp import FastMCP

from uk_parliament_mcp.config import LORDS_BUSINESS_API_BASE
from uk_parliament_mcp.http_client import build_url, get_result, get_result_cached


def register_tools(mcp: FastMCP) -> None:
    """Register Lords Business tools with the MCP server."""

    # Business papers and sections

    @mcp.tool()
    async def get_lords_business_sections() -> str:
        """List Lords business paper sections | order paper, future business, minutes, section types | Use to find section_id values for get_lords_business_section_data | Returns every section of the Lords business paper with id, name and display order. See also: get_lords_business_sections_for_date, get_lords_business_section_data.

        Returns:
            All Lords business sections with SectionId, Name and DisplayOrder.
        """
        url = f"{LORDS_BUSINESS_API_BASE}/GetSections.json"
        return await get_result_cached(url, cache_key=url)

    @mcp.tool()
    async def get_lords_business_sections_for_date(business_paper_date: str) -> str:
        """List the Lords business sections published for a date | business paper contents, what is on the Lords order paper that day | Use to see which sections of the Lords business paper exist for a sitting day | Returns a list of section ids. See also: get_lords_business_sections, get_lords_business_section_data.

        Args:
            business_paper_date: Business paper date (YYYY-MM-DD).

        Returns:
            List of SectionId values published for the date.
        """
        url = build_url(
            f"{LORDS_BUSINESS_API_BASE}/GetSectionsForDate.json",
            {"businessPaperDate": business_paper_date},
        )
        return await get_result(url)

    @mcp.tool()
    async def get_lords_business_section_data(
        business_paper_date: str | None = None, section_id: int | None = None
    ) -> str:
        """Get the content of a Lords business paper section | order paper items, Lords agenda, items of business, motions, bills | Use to read what the House of Lords is scheduled to consider on a day | Returns the section's items of business for the date. See also: get_lords_business_sections_for_date, get_lords_item_of_business_summary.

        Args:
            business_paper_date: Business paper date (YYYY-MM-DD).
            section_id: Section id from get_lords_business_sections or get_lords_business_sections_for_date.

        Returns:
            Items of business for the section and date.
        """
        url = build_url(
            f"{LORDS_BUSINESS_API_BASE}/GetData.json",
            {"BusinessPaperDate": business_paper_date, "SectionId": section_id},
        )
        return await get_result(url)

    @mcp.tool()
    async def get_lords_item_of_business_summary(
        item_of_business_id: int, business_paper_date: str
    ) -> str:
        """Get a summary of one Lords item of business | business item, motion, bill, statutory instrument, written question | Use to drill into a single item found in a Lords business paper section | Returns the item's summary details. See also: get_lords_business_section_data.

        Args:
            item_of_business_id: Id of the item of business.
            business_paper_date: Date the item was published in the business paper (YYYY-MM-DD).

        Returns:
            Summary of the item of business.
        """
        url = build_url(
            f"{LORDS_BUSINESS_API_BASE}/ItemOfBusinessSummary.json",
            {"itemOfBusinessId": item_of_business_id, "businessPaperDate": business_paper_date},
        )
        return await get_result(url)

    @mcp.tool()
    async def get_lords_business_documents_for_date(day_date: str) -> str:
        """List Lords business documents for a day | order paper PDF, HL business papers, daily documents | Use to find the published documents for a Lords sitting day | Returns document filenames, type ids and DocumentForDayId values. See also: get_lords_business_document.

        Args:
            day_date: Date to list documents for (YYYY-MM-DD).

        Returns:
            Documents published for the day.
        """
        url = f"{LORDS_BUSINESS_API_BASE}/Day/DocumentForDay.json/{quote(day_date)}"
        return await get_result(url)

    @mcp.tool()
    async def get_lords_business_document(document_day_id: int) -> str:
        """Get a Lords business document for a day | download business paper, document by id | Use after get_lords_business_documents_for_date to fetch one document | Returns the document for the DocumentForDayId. See also: get_lords_business_documents_for_date.

        Args:
            document_day_id: DocumentForDayId from get_lords_business_documents_for_date.

        Returns:
            The document record. For a PDF this is a descriptor (binary, contentType, sizeBytes, downloadUrl); fetch downloadUrl to get the file.
        """
        url = f"{LORDS_BUSINESS_API_BASE}/DocumentForDay/{document_day_id}"
        return await get_result(url)

    # Sitting days and divisions

    @mcp.tool()
    async def check_lords_divisions_exist(date: str) -> str:
        """Check whether the Lords held divisions on a date | did the Lords vote, division day check | Use before searching Lords divisions for a specific day | Returns true or false. See also: search_lords_divisions.

        Args:
            date: Date to check (YYYY-MM-DD).

        Returns:
            true if divisions exist for the date, otherwise false.
        """
        url = build_url(f"{LORDS_BUSINESS_API_BASE}/DivisionsExistForDate.json", {"date": date})
        return await get_result(url)

    @mcp.tool()
    async def get_lords_non_sitting_days(
        month: int, year: int, data_source: str | None = None
    ) -> str:
        """List Lords non-sitting days in a month | recess, days the Lords does not sit, no business | Use to check whether the Lords sits on a given day or in a given month | Returns the non-sitting dates (MM-DD-YYYY). See also: get_lords_next_prev_business_days, get_non_sitting_days.

        Args:
            month: Month number (1-12).
            year: Year (e.g. 2025).
            data_source: 'Calendar' (default) or 'PublishedBusiness' to return days with no published business instead.

        Returns:
            List of non-sitting days in the month.
        """
        url = build_url(
            f"{LORDS_BUSINESS_API_BASE}/NonSittingDays.json/{month}/{year}",
            {"dataSource": data_source},
        )
        return await get_result(url)

    @mcp.tool()
    async def get_lords_next_prev_business_days(initial_date: str) -> str:
        """Get the next and previous Lords days with business | next sitting day, previous sitting day, business papers | Use to step between Lords days that have published business | Returns the previous and next business dates. See also: get_lords_non_sitting_days, get_next_sitting_date.

        Args:
            initial_date: Date to search from (YYYY-MM-DD).

        Returns:
            PreviousBusinessDay and FutureBusinessDay.
        """
        url = build_url(
            f"{LORDS_BUSINESS_API_BASE}/GetNextPrevDaysWithItemsOfBusiness.json",
            {"initialDate": initial_date},
        )
        return await get_result(url)

    # Lords Journal

    @mcp.tool()
    async def get_lords_journal_volumes(skip: int | None = None, take: int | None = None) -> str:
        """List Lords Journal volumes | Journal of the House of Lords, session volumes, minutes archive | Use to browse the Journal by session and find volume ids | Returns volumes with id, name, publication status and PDF link. See also: get_lords_journal_volume.

        Args:
            skip: Number of volumes to skip.
            take: Number of volumes to return.

        Returns:
            List of Journal volumes.
        """
        url = build_url(f"{LORDS_BUSINESS_API_BASE}/journal-volumes", {"Skip": skip, "Take": take})
        return await get_result(url)

    @mcp.tool()
    async def get_lords_journal_volume(volume_id: int) -> str:
        """Get a Lords Journal volume | Journal volume details, session | Use to read one Journal volume's details | Returns the volume record. See also: get_lords_journal_volumes, get_lords_journal_general_index.

        Args:
            volume_id: Journal volume id.

        Returns:
            Journal volume details.
        """
        url = f"{LORDS_BUSINESS_API_BASE}/journal-volumes/{volume_id}"
        return await get_result(url)

    @mcp.tool()
    async def get_lords_journal_general_index(
        volume_id: int, starting_with: str | None = None
    ) -> str:
        """Get the general index of a Lords Journal volume | Journal subject index, topics, bills, alphabetical | Use to look up subjects and references in a Journal volume (large response, filter with starting_with) | Returns index items. See also: get_lords_journal_membership_index, get_lords_journal_index_items.

        Args:
            volume_id: Journal volume id.
            starting_with: Only return index items starting with this letter or text.

        Returns:
            General index items for the volume.
        """
        url = build_url(
            f"{LORDS_BUSINESS_API_BASE}/journal-volumes/{volume_id}/general-index",
            {"StartingWith": starting_with},
        )
        return await get_result(url)

    @mcp.tool()
    async def get_lords_journal_membership_index(
        volume_id: int, starting_with: str | None = None
    ) -> str:
        """Get the membership index of a Lords Journal volume | Journal members index, peers, attendance by name | Use to find where a Lord appears in a Journal volume | Returns membership index items. See also: get_lords_journal_general_index.

        Args:
            volume_id: Journal volume id.
            starting_with: Only return index items starting with this letter or text.

        Returns:
            Membership index items for the volume.
        """
        url = build_url(
            f"{LORDS_BUSINESS_API_BASE}/journal-volumes/{volume_id}/membership-index",
            {"StartingWith": starting_with},
        )
        return await get_result(url)

    @mcp.tool()
    async def get_lords_journal_index_items(index_item_guid: str, journal_volume_id: int) -> str:
        """Get a Lords Journal index item | Journal index entry, references, sub-items | Use to expand one index item found in a general index | Returns the index item and its references. See also: get_lords_journal_general_index.

        Args:
            index_item_guid: GUID of the Journal index item.
            journal_volume_id: Journal volume id the item belongs to.

        Returns:
            The index item with its references.
        """
        url = build_url(
            f"{LORDS_BUSINESS_API_BASE}/index-items/{quote(index_item_guid)}",
            {"journalVolumeId": journal_volume_id},
        )
        return await get_result(url)

    @mcp.tool()
    async def get_lords_journal_content_dates(
        start_date: str | None = None, end_date: str | None = None
    ) -> str:
        """List dates that have Lords Journal data | Journal sitting dates, minutes of proceedings dates | Use to find which sitting dates have Journal content before calling get_lords_journal_sittings | Returns dates with Journal data. See also: get_lords_journal_sittings.

        Args:
            start_date: Start of the date range (YYYY-MM-DD).
            end_date: End of the date range (YYYY-MM-DD).

        Returns:
            Dates for which Journal data exists.
        """
        url = build_url(
            f"{LORDS_BUSINESS_API_BASE}/sittings/journalContentDates",
            {"startDate": start_date, "endDate": end_date},
        )
        return await get_result(url)

    @mcp.tool()
    async def get_lords_journal_sittings(sitting_date: str, content_type: str) -> str:
        """Get Lords Journal content for a sitting date | minutes of proceedings, attendance, papers laid, appendix, divisions | Use to read what the Journal records for a Lords sitting | Returns sittings with the requested content. See also: get_lords_journal_content_dates.

        Args:
            sitting_date: Sitting date (YYYY-MM-DD).
            content_type: One of Attendance, MinutesOfProceedings, Papers, Appendix, Divisions.

        Returns:
            Journal sittings for the date and content type.
        """
        url = f"{LORDS_BUSINESS_API_BASE}/sittings/{quote(sitting_date)}/{quote(content_type)}"
        return await get_result(url)

    @mcp.tool()
    async def get_lords_journal_attachment(attachment_id: int) -> str:
        """Get a Lords Journal attachment | Journal attachment, appendix document | Use to fetch an attachment referenced from the Journal | Returns the attachment record. See also: get_lords_journal_sittings.

        Args:
            attachment_id: Journal attachment id.

        Returns:
            The Journal attachment.
        """
        url = f"{LORDS_BUSINESS_API_BASE}/journal-attachments/{attachment_id}"
        return await get_result(url)

    @mcp.tool()
    async def get_lords_legacy_business(day_date: str) -> str:
        """List legacy Lords business documents for a date | historic business papers, old order papers | Use for older Lords business papers from before the current system | Returns legacy business documents for the date. See also: get_lords_business_documents_for_date.

        Args:
            day_date: Date to list legacy documents for (YYYY-MM-DD).

        Returns:
            Legacy business documents for the date.
        """
        url = f"{LORDS_BUSINESS_API_BASE}/legacybusiness/{quote(day_date)}"
        return await get_result(url)

    # Lords written questions

    @mcp.tool()
    async def search_lords_written_questions(
        member_id: int | None = None,
        uin: str | None = None,
        status: str | None = None,
        tabled_start_date: str | None = None,
        tabled_end_date: str | None = None,
        order_by: str | None = None,
        skip: int | None = None,
        take: int | None = None,
    ) -> str:
        """Search House of Lords written questions | Lords questions, HL questions, peers' questions, tabled, answered, withdrawn | Use for Lords written questions as published in the Lords business system; always give a date range as unfiltered requests are slow | Returns questions with text, dates, status, member and answering body. See also: search_written_questions, get_lords_written_question.

        Args:
            member_id: Filter by the asking Lord's member id.
            uin: Filter by question UIN (e.g. '4578').
            status: Tabled, Answered or Withdrawn.
            tabled_start_date: Tabled on or after (YYYY-MM-DD).
            tabled_end_date: Tabled on or before (YYYY-MM-DD).
            order_by: DateTabledAsc or DateTabledDesc.
            skip: Number of results to skip.
            take: Number of results to return.

        Returns:
            Paged list of Lords written questions.
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
        return await get_result(url)

    @mcp.tool()
    async def get_lords_written_question(question_id: int) -> str:
        """Get a single House of Lords written question | Lords question by id, HL question and answer | Use after search_lords_written_questions to read one question | Returns the question and its answer. See also: search_lords_written_questions, get_written_question.

        Args:
            question_id: Question id from search_lords_written_questions.

        Returns:
            The Lords written question.
        """
        url = f"{LORDS_BUSINESS_API_BASE}/WrittenQuestions/{question_id}.json"
        return await get_result(url)
