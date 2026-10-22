"""Deposited papers CLI commands for papers deposited in the Libraries of both Houses."""

from __future__ import annotations

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
from uk_parliament_mcp.config import DEPOSITED_PAPERS_API_BASE, house_name
from uk_parliament_mcp.http_client import build_url

app = typer.Typer(
    help="Deposited papers - documents ministers deposit in the Libraries of both Houses",
    no_args_is_help=True,
)


@app.command("search")
def search_deposited_papers(
    terms: str | None = typer.Argument(
        None, help="Words to match against department, paper number and summary"
    ),
    house: str | None = typer.Option(None, "--house", help="Commons/Lords (or 1/2); default both"),
    deposited_from: str | None = typer.Option(
        None, "--from", help="Deposited after this date (YYYY-MM-DD)"
    ),
    deposited_to: str | None = typer.Option(
        None, "--to", help="Deposited before this date (YYYY-MM-DD)"
    ),
    department_ses_id: int | None = typer.Option(
        None, "--department-id", help="Depositing department ID"
    ),
    order_by: str | None = typer.Option(
        None, "--order-by", help="Relevance, CommitmentDateAsc or CommitmentDateDesc"
    ),
    skip: int | None = typer.Option(None, "--skip", help="Number of results to skip"),
    take: int | None = typer.Option(None, "--take", help="Number of results to return"),
    pretty: PrettyOpt = False,
    data_only: DataOnlyOpt = True,
    output_format: FormatOpt = OutputFormat.AUTO,
    raw: RawOpt = False,
    fields: FieldsOpt = None,
) -> None:
    """
    Search deposited papers.

    Finds departmental reports, command papers and other documents deposited for
    Parliament, by topic, department, house or deposit date.
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
    output_result(url, pretty, data_only, output_format, fields, raw)


@app.command("get")
def get_deposited_paper(
    paper_id: int = typer.Argument(..., help="Deposited paper ID (paperId from search)"),
    pretty: PrettyOpt = False,
    data_only: DataOnlyOpt = True,
    output_format: FormatOpt = OutputFormat.AUTO,
    raw: RawOpt = False,
    fields: FieldsOpt = None,
) -> None:
    """
    Get a deposited paper by ID.

    Returns notes, attached document names, dates, corporate authors and departments.
    """
    url = f"{DEPOSITED_PAPERS_API_BASE}/DepositedPapers/{paper_id}"
    output_result(url, pretty, data_only, output_format, fields, raw)
