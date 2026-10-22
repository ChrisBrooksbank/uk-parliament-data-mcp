"""Deposited Papers API tools for papers deposited in the Libraries of both Houses."""

from mcp.server.fastmcp import FastMCP

from uk_parliament_mcp.config import DEPOSITED_PAPERS_API_BASE, house_name
from uk_parliament_mcp.http_client import build_url, get_result


def register_tools(mcp: FastMCP) -> None:
    """Register Deposited Papers tools with the MCP server."""

    @mcp.tool()
    async def search_deposited_papers(
        terms: str | None = None,
        house: int | str | None = None,
        deposited_from: str | None = None,
        deposited_to: str | None = None,
        department_ses_id: int | None = None,
        order_by: str | None = None,
        skip: int | None = None,
        take: int | None = None,
    ) -> str:
        """Search deposited papers | papers deposited in the Libraries, departmental reports, command papers, government documents, DEP numbers | Use to find documents ministers have deposited for Parliament by topic, department, house or date | Returns paged deposited papers with paper number, title, dates, houses and depositing departments. See also: get_deposited_paper, get_departments.

        Args:
            terms: Words to match against depositing department, paper number and summary (e.g. 'defence', 'DEP2026-0590').
            house: Papers relating to a house: 1/'Commons' or 2/'Lords'. Omit for both.
            deposited_from: Deposited after this date (YYYY-MM-DD).
            deposited_to: Deposited before this date (YYYY-MM-DD).
            department_ses_id: Depositing department id (see get_departments).
            order_by: Relevance, CommitmentDateAsc or CommitmentDateDesc.
            skip: Number of results to skip (default 0).
            take: Number of results to return (default 20).

        Returns:
            Paged list of deposited papers with a total result count.
        """
        url = build_url(
            f"{DEPOSITED_PAPERS_API_BASE}/DepositedPapers",
            {
                "Terms": terms,
                "House": house_name(house),
                "DepositedFrom": deposited_from,
                "DepositedTo": deposited_to,
                "DepartmentSesId": department_ses_id,
                "OrderBy": order_by,
                "Skip": skip,
                "Take": take,
            },
        )
        return await get_result(url)

    @mcp.tool()
    async def get_deposited_paper(paper_id: int) -> str:
        """Get a deposited paper by id | deposited paper details, notes, attached documents, corporate authors | Use after search_deposited_papers to read one paper in full | Returns the paper with notes, attached document names, dates, authors and departments. See also: search_deposited_papers.

        Args:
            paper_id: Deposited paper id (paperId from search_deposited_papers).

        Returns:
            The deposited paper's full details.
        """
        url = f"{DEPOSITED_PAPERS_API_BASE}/DepositedPapers/{paper_id}"
        return await get_result(url)
