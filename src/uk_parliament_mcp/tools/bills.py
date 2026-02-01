"""Bills API tools for legislation, amendments, and stages."""

from urllib.parse import quote

from mcp.server.fastmcp import FastMCP

from uk_parliament_mcp.config import BILLS_API_BASE
from uk_parliament_mcp.http_client import build_url, get_result


def register_tools(mcp: FastMCP) -> None:
    """Register bills tools with the MCP server."""

    @mcp.tool()
    async def get_recently_updated_bills(take: int = 10) -> str:
        """Get most recently updated bills and current legislative activity | recent bills, new legislation, latest laws, parliamentary bills, legislative updates, current proposals | Use for tracking new legislation, monitoring bill progress, or finding recently introduced/updated laws | Returns bill titles, stages, sponsors, dates, and current status | Data freshness: updated frequently

        Args:
            take: Number of bills to return. Default: 10, recommended max: 50. Higher numbers may slow response.

        Returns:
            Bill titles, stages, sponsors, dates, and current status.
        """
        url = f"{BILLS_API_BASE}/Bills?SortOrder=DateUpdatedDescending&skip=0&take={take}"
        return await get_result(url)

    @mcp.tool()
    async def search_bills(
        search_term: str,
        member_id: int | None = None,
    ) -> str:
        """Search for parliamentary bills by title, subject, or keyword. Use when researching proposed legislation, finding bills on specific topics, or tracking legislative progress.

        Args:
            search_term: Search term for bill titles or content (e.g. 'environment', 'health', 'finance').
            member_id: Optional: member ID to filter bills sponsored by specific member.

        Returns:
            Matching bills with titles, stages, and sponsors.
        """
        url = f"{BILLS_API_BASE}/Bills?SearchTerm={quote(search_term)}"
        return await get_result(url)

    @mcp.tool()
    async def bill_types() -> str:
        """Get all types of bills that can be introduced in Parliament (e.g., Government Bill, Private Member's Bill). Use when you need to understand different categories of legislation.

        Returns:
            All bill types with descriptions.
        """
        url = f"{BILLS_API_BASE}/BillTypes"
        return await get_result(url)

    @mcp.tool()
    async def bill_stages() -> str:
        """Get all possible stages a bill can go through in its legislative journey. Use when tracking bill progress or understanding the legislative process (e.g., First Reading, Committee Stage, Royal Assent).

        Returns:
            All bill stages with descriptions.
        """
        url = f"{BILLS_API_BASE}/Stages"
        return await get_result(url)

    @mcp.tool()
    async def get_bill_by_id(bill_id: int) -> str:
        """Get detailed information about a specific bill by ID. Use when you need comprehensive bill details including title, sponsors, stages, summary, and current status.

        Args:
            bill_id: Unique bill ID number.

        Returns:
            Comprehensive bill details.
        """
        url = f"{BILLS_API_BASE}/Bills/{bill_id}"
        return await get_result(url)

    @mcp.tool()
    async def get_bill_stages(
        bill_id: int,
        skip: int | None = None,
        take: int | None = None,
    ) -> str:
        """Get all stages of a specific bill by bill ID. Use when tracking a bill's progress through Parliament, understanding its legislative journey, or finding specific stages like Committee Stage or Third Reading.

        Args:
            bill_id: Bill ID to get stages for.
            skip: Optional: number of records to skip (for pagination).
            take: Optional: number of records to return.

        Returns:
            All stages for the specified bill.
        """
        url = build_url(
            f"{BILLS_API_BASE}/Bills/{bill_id}/Stages",
            {"Skip": skip, "Take": take},
        )
        return await get_result(url)

    @mcp.tool()
    async def get_bill_stage_details(bill_id: int, bill_stage_id: int) -> str:
        """Get detailed information about a specific stage of a bill. Use when you need complete details about a particular stage including timings, committee involvement, and related activities.

        Args:
            bill_id: Bill ID.
            bill_stage_id: Bill stage ID to get details for.

        Returns:
            Detailed information about the bill stage.
        """
        url = f"{BILLS_API_BASE}/Bills/{bill_id}/Stages/{bill_stage_id}"
        return await get_result(url)

    @mcp.tool()
    async def get_bill_stage_amendments(
        bill_id: int,
        bill_stage_id: int,
        search_term: str | None = None,
        amendment_number: str | None = None,
        decision: str | None = None,
        member_id: int | None = None,
        skip: int | None = None,
        take: int | None = None,
    ) -> str:
        """Get all amendments for a specific bill stage. Use when researching proposed changes to legislation, tracking amendment activity, or understanding what modifications are being suggested to a bill.

        Args:
            bill_id: Bill ID.
            bill_stage_id: Bill stage ID to get amendments for.
            search_term: Optional: search term for amendment content.
            amendment_number: Optional: specific amendment number.
            decision: Optional: amendment decision status.
            member_id: Optional: member ID who proposed amendment.
            skip: Optional: number of records to skip (for pagination).
            take: Optional: number of records to return.

        Returns:
            Amendments for the specified bill stage.
        """
        url = build_url(
            f"{BILLS_API_BASE}/Bills/{bill_id}/Stages/{bill_stage_id}/Amendments",
            {
                "SearchTerm": search_term,
                "AmendmentNumber": amendment_number,
                "Decision": decision,
                "MemberId": member_id,
                "Skip": skip,
                "Take": take,
            },
        )
        return await get_result(url)

    @mcp.tool()
    async def get_amendment_by_id(
        bill_id: int,
        bill_stage_id: int,
        amendment_id: int,
    ) -> str:
        """Get detailed information about a specific amendment. Use when you need complete amendment details including text, sponsors, decision, and explanatory notes.

        Args:
            bill_id: Bill ID.
            bill_stage_id: Bill stage ID.
            amendment_id: Amendment ID to get details for.

        Returns:
            Detailed information about the amendment.
        """
        url = f"{BILLS_API_BASE}/Bills/{bill_id}/Stages/{bill_stage_id}/Amendments/{amendment_id}"
        return await get_result(url)

    @mcp.tool()
    async def get_bill_stage_ping_pong_items(
        bill_id: int,
        bill_stage_id: int,
        search_term: str | None = None,
        amendment_number: str | None = None,
        decision: str | None = None,
        member_id: int | None = None,
        skip: int | None = None,
        take: int | None = None,
    ) -> str:
        """Get ping pong items (amendments and motions) for a bill stage. Use when researching the final stages of bills passing between Commons and Lords, including disagreements and agreements on amendments.

        Args:
            bill_id: Bill ID.
            bill_stage_id: Bill stage ID to get ping pong items for.
            search_term: Optional: search term for ping pong item content.
            amendment_number: Optional: specific amendment number.
            decision: Optional: ping pong item decision status.
            member_id: Optional: member ID who proposed item.
            skip: Optional: number of records to skip (for pagination).
            take: Optional: number of records to return.

        Returns:
            Ping pong items for the specified bill stage.
        """
        url = build_url(
            f"{BILLS_API_BASE}/Bills/{bill_id}/Stages/{bill_stage_id}/PingPongItems",
            {
                "SearchTerm": search_term,
                "AmendmentNumber": amendment_number,
                "Decision": decision,
                "MemberId": member_id,
                "Skip": skip,
                "Take": take,
            },
        )
        return await get_result(url)

    @mcp.tool()
    async def get_ping_pong_item_by_id(
        bill_id: int,
        bill_stage_id: int,
        ping_pong_item_id: int,
    ) -> str:
        """Get detailed information about a specific ping pong item (amendment or motion). Use when you need complete details about final stage amendments or motions in the legislative process.

        Args:
            bill_id: Bill ID.
            bill_stage_id: Bill stage ID.
            ping_pong_item_id: Ping pong item ID to get details for.

        Returns:
            Detailed information about the ping pong item.
        """
        url = f"{BILLS_API_BASE}/Bills/{bill_id}/Stages/{bill_stage_id}/PingPongItems/{ping_pong_item_id}"
        return await get_result(url)

    @mcp.tool()
    async def get_bill_publications(bill_id: int) -> str:
        """Get all publications for a specific bill. Use when researching bill documents, impact assessments, explanatory notes, or tracking document versions throughout the legislative process.

        Args:
            bill_id: Bill ID to get publications for.

        Returns:
            Publications for the specified bill.
        """
        url = f"{BILLS_API_BASE}/Bills/{bill_id}/Publications"
        return await get_result(url)

    @mcp.tool()
    async def get_bill_stage_publications(bill_id: int, stage_id: int) -> str:
        """Get publications for a specific bill stage. Use when you need documents related to a particular stage of legislation, such as committee reports or stage-specific amendments.

        Args:
            bill_id: Bill ID.
            stage_id: Stage ID to get publications for.

        Returns:
            Publications for the specified bill stage.
        """
        url = f"{BILLS_API_BASE}/Bills/{bill_id}/Stages/{stage_id}/Publications"
        return await get_result(url)

    @mcp.tool()
    async def get_publication_document(publication_id: int, document_id: int) -> str:
        """Get information about a specific publication document. Use when you need metadata about bill documents including filename, content type, and size.

        Args:
            publication_id: Publication ID.
            document_id: Document ID to get details for.

        Returns:
            Metadata about the publication document.
        """
        url = f"{BILLS_API_BASE}/Publications/{publication_id}/Documents/{document_id}"
        return await get_result(url)

    @mcp.tool()
    async def get_bill_news_articles(
        bill_id: int,
        skip: int | None = None,
        take: int | None = None,
    ) -> str:
        """Get news articles related to a specific bill. Use when researching media coverage, press releases, or official communications about legislation.

        Args:
            bill_id: Bill ID to get news articles for.
            skip: Optional: number of records to skip (for pagination).
            take: Optional: number of records to return.

        Returns:
            News articles related to the bill.
        """
        url = build_url(
            f"{BILLS_API_BASE}/Bills/{bill_id}/NewsArticles",
            {"Skip": skip, "Take": take},
        )
        return await get_result(url)

    @mcp.tool()
    async def get_all_bills_rss() -> str:
        """Get RSS feed of all bills. Use when you want to stay updated on all legislative activity through RSS feeds.

        Returns:
            RSS feed of all bills.
        """
        url = f"{BILLS_API_BASE}/Rss/allbills.rss"
        return await get_result(url)

    @mcp.tool()
    async def get_public_bills_rss() -> str:
        """Get RSS feed of public bills only. Use when you want to monitor government and public bills through RSS feeds, excluding private bills.

        Returns:
            RSS feed of public bills.
        """
        url = f"{BILLS_API_BASE}/Rss/publicbills.rss"
        return await get_result(url)

    @mcp.tool()
    async def get_private_bills_rss() -> str:
        """Get RSS feed of private bills only. Use when you want to monitor private member bills and private bills through RSS feeds.

        Returns:
            RSS feed of private bills.
        """
        url = f"{BILLS_API_BASE}/Rss/privatebills.rss"
        return await get_result(url)

    @mcp.tool()
    async def get_bill_rss(bill_id: int) -> str:
        """Get RSS feed for a specific bill by ID. Use when you want to track updates and changes to a particular piece of legislation through RSS feeds.

        Args:
            bill_id: Bill ID to get RSS feed for.

        Returns:
            RSS feed for the specified bill.
        """
        url = f"{BILLS_API_BASE}/Rss/Bills/{bill_id}.rss"
        return await get_result(url)

    @mcp.tool()
    async def get_publication_types(
        skip: int | None = None,
        take: int | None = None,
    ) -> str:
        """Get all publication types available for bills. Use when you need to understand the different types of documents that can be associated with legislation.

        Args:
            skip: Optional: number of records to skip (for pagination).
            take: Optional: number of records to return.

        Returns:
            All publication types with descriptions.
        """
        url = build_url(
            f"{BILLS_API_BASE}/PublicationTypes",
            {"Skip": skip, "Take": take},
        )
        return await get_result(url)

    @mcp.tool()
    async def get_sittings(
        house: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        skip: int | None = None,
        take: int | None = None,
    ) -> str:
        """Get parliamentary sittings with optional filtering by house and date range. Use when researching when Parliament was in session, finding specific sitting dates, or tracking parliamentary activity.

        Args:
            house: Optional: house name ('Commons' or 'Lords').
            date_from: Optional: start date in YYYY-MM-DD format.
            date_to: Optional: end date in YYYY-MM-DD format.
            skip: Optional: number of records to skip (for pagination).
            take: Optional: number of records to return.

        Returns:
            Parliamentary sittings matching the criteria.
        """
        url = build_url(
            f"{BILLS_API_BASE}/Sittings",
            {
                "House": house,
                "DateFrom": date_from,
                "DateTo": date_to,
                "Skip": skip,
                "Take": take,
            },
        )
        return await get_result(url)
