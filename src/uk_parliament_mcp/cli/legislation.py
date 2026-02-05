"""Legislation CLI commands for Statutory Instruments and Treaties."""

from __future__ import annotations

from urllib.parse import quote

import typer

from uk_parliament_mcp.cli.utils import format_output, run_async
from uk_parliament_mcp.config import STATUTORY_INSTRUMENTS_API_BASE, TREATIES_API_BASE
from uk_parliament_mcp.http_client import build_url, get_result

app = typer.Typer(
    help="Statutory Instruments and Treaties - secondary legislation and international agreements"
)


@app.command("search-si")
def search_statutory_instruments(
    name: str = typer.Argument(..., help="Name or title of the statutory instrument"),
    pretty: bool = typer.Option(False, "--pretty", "-p", help="Pretty-print JSON output"),
    data_only: bool = typer.Option(False, "--data-only", "-d", help="Return data only"),
) -> None:
    """
    Search for Statutory Instruments (secondary legislation) by name.

    Use when researching government regulations, rules, or orders made under
    primary legislation. SIs are used to implement or modify laws.
    """
    url = f"{STATUTORY_INSTRUMENTS_API_BASE}/StatutoryInstrument?Name={quote(name)}"
    result = run_async(get_result(url))
    typer.echo(format_output(result, pretty, data_only))


@app.command("search-acts")
def search_acts_of_parliament(
    name: str = typer.Argument(..., help="Name or title of the Act (e.g. 'Climate Change Act')"),
    pretty: bool = typer.Option(False, "--pretty", "-p", help="Pretty-print JSON output"),
    data_only: bool = typer.Option(False, "--data-only", "-d", help="Return data only"),
) -> None:
    """
    Search for Acts of Parliament (primary legislation) by name or topic.

    Use when researching existing laws, finding legislation on specific subjects,
    or understanding the legal framework on particular issues.
    """
    url = f"{STATUTORY_INSTRUMENTS_API_BASE}/ActOfParliament?Name={quote(name)}"
    result = run_async(get_result(url))
    typer.echo(format_output(result, pretty, data_only))


@app.command("get-si")
def get_statutory_instrument(
    instrument_id: str = typer.Argument(
        ..., help="The SI ID (alphanumeric string from search results)"
    ),
    pretty: bool = typer.Option(False, "--pretty", "-p", help="Pretty-print JSON output"),
    data_only: bool = typer.Option(False, "--data-only", "-d", help="Return data only"),
) -> None:
    """
    Get full details of a specific Statutory Instrument.

    Returns SI details including laying info, procedure, and status.
    """
    url = f"{STATUTORY_INSTRUMENTS_API_BASE}/StatutoryInstrument/{instrument_id}"
    result = run_async(get_result(url))
    typer.echo(format_output(result, pretty, data_only))


@app.command("si-business")
def get_si_business_items(
    instrument_id: str = typer.Argument(
        ..., help="The SI ID (alphanumeric string from search results)"
    ),
    pretty: bool = typer.Option(False, "--pretty", "-p", help="Pretty-print JSON output"),
    data_only: bool = typer.Option(False, "--data-only", "-d", help="Return data only"),
) -> None:
    """
    Get business items (debates, motions) for a Statutory Instrument.

    Returns list of business items with dates and outcomes. Use when tracking
    SI progress, scrutiny, debates, or motions.
    """
    url = f"{STATUTORY_INSTRUMENTS_API_BASE}/StatutoryInstrument/{instrument_id}/BusinessItems"
    result = run_async(get_result(url))
    typer.echo(format_output(result, pretty, data_only))


@app.command("get-act")
def get_act_of_parliament(
    act_id: str = typer.Argument(..., help="The Act ID (alphanumeric string from search results)"),
    pretty: bool = typer.Option(False, "--pretty", "-p", help="Pretty-print JSON output"),
    data_only: bool = typer.Option(False, "--data-only", "-d", help="Return data only"),
) -> None:
    """
    Get full details of an Act of Parliament.

    Returns Act details including primary legislation information.
    """
    url = f"{STATUTORY_INSTRUMENTS_API_BASE}/ActOfParliament/{act_id}"
    result = run_async(get_result(url))
    typer.echo(format_output(result, pretty, data_only))


@app.command("search-treaties")
def search_treaties(
    search_text: str = typer.Argument(
        ..., help="Search term (e.g. 'trade', 'EU', 'climate', 'Brexit')"
    ),
    pretty: bool = typer.Option(False, "--pretty", "-p", help="Pretty-print JSON output"),
    data_only: bool = typer.Option(False, "--data-only", "-d", help="Return data only"),
) -> None:
    """
    Search UK international treaties and agreements under parliamentary scrutiny.

    Use for researching international relations, trade agreements, or diplomatic
    commitments. Returns treaty details including titles, countries involved,
    and parliamentary scrutiny status.
    """
    url = build_url(f"{TREATIES_API_BASE}/Treaty", {"SearchText": search_text})
    result = run_async(get_result(url))
    typer.echo(format_output(result, pretty, data_only))


@app.command("search-treaties-advanced")
def search_treaties_advanced(
    search_text: str | None = typer.Option(
        None, "--search", help="Search term for treaty titles/content"
    ),
    government_organisation_id: int | None = typer.Option(
        None, "--org-id", help="Filter by laying department ID"
    ),
    series: str | None = typer.Option(
        None,
        "--series",
        help="Treaty series type (CountrySeriesMembership, EuropeanUnionSeriesMembership, MiscellaneousSeriesMembership)",
    ),
    parliamentary_process: str | None = typer.Option(
        None, "--process", help="NotConcluded or Concluded"
    ),
    debate_scheduled: bool | None = typer.Option(
        None, "--debate-scheduled", help="Filter to treaties with scheduled debate"
    ),
    motions_tabled: bool | None = typer.Option(
        None, "--motions-tabled", help="Filter to treaties with tabled motions"
    ),
    committee_raised_concerns: bool | None = typer.Option(
        None, "--concerns", help="Filter to treaties with committee concerns"
    ),
    house: str | None = typer.Option(None, "--house", help="Commons or Lords"),
    skip: int = typer.Option(0, "--skip", help="Number of records to skip (pagination)"),
    take: int = typer.Option(20, "--take", help="Number of records to return"),
    pretty: bool = typer.Option(False, "--pretty", "-p", help="Pretty-print JSON output"),
    data_only: bool = typer.Option(False, "--data-only", "-d", help="Return data only"),
) -> None:
    """
    Advanced treaty search with full filtering.

    Use to find treaties by department, scrutiny status, or with parliamentary
    concerns. Returns treaties matching all specified filters.
    """
    url = build_url(
        f"{TREATIES_API_BASE}/Treaty",
        {
            "SearchText": search_text,
            "GovernmentOrganisationId": government_organisation_id,
            "Series": series,
            "ParliamentaryProcess": parliamentary_process,
            "DebateScheduled": debate_scheduled,
            "MotionsTabledAboutATreaty": motions_tabled,
            "CommitteeRaisedConcerns": committee_raised_concerns,
            "House": house,
            "Skip": skip,
            "Take": take,
        },
    )
    result = run_async(get_result(url))
    typer.echo(format_output(result, pretty, data_only))


@app.command("treaty-departments")
def get_treaty_government_organisations(
    pretty: bool = typer.Option(False, "--pretty", "-p", help="Pretty-print JSON output"),
    data_only: bool = typer.Option(False, "--data-only", "-d", help="Return data only"),
) -> None:
    """
    Get departments that lay treaties.

    Use to get organisation IDs for filtering treaty searches. Returns list of
    government organisations with IDs (e.g., Foreign Office).
    """
    url = f"{TREATIES_API_BASE}/GovernmentOrganisation"
    result = run_async(get_result(url))
    typer.echo(format_output(result, pretty, data_only))


@app.command("treaty-series")
def get_treaty_series_memberships(
    pretty: bool = typer.Option(False, "--pretty", "-p", help="Pretty-print JSON output"),
    data_only: bool = typer.Option(False, "--data-only", "-d", help="Return data only"),
) -> None:
    """
    Get treaty series types.

    Use to understand treaty classification categories. Returns list of treaty
    series membership types (Country, EU, Miscellaneous).
    """
    url = f"{TREATIES_API_BASE}/SeriesMembership"
    result = run_async(get_result(url))
    typer.echo(format_output(result, pretty, data_only))


@app.command("get-treaty")
def get_treaty(
    treaty_id: str = typer.Argument(
        ..., help="The treaty ID (alphanumeric string from search results)"
    ),
    pretty: bool = typer.Option(False, "--pretty", "-p", help="Pretty-print JSON output"),
    data_only: bool = typer.Option(False, "--data-only", "-d", help="Return data only"),
) -> None:
    """
    Get full details of a specific treaty.

    Returns treaty details including status, dates, and parties involved.
    """
    url = f"{TREATIES_API_BASE}/Treaty/{treaty_id}"
    result = run_async(get_result(url))
    typer.echo(format_output(result, pretty, data_only))


@app.command("treaty-business")
def get_treaty_business_items(
    treaty_id: str = typer.Argument(
        ..., help="The treaty ID (alphanumeric string from search results)"
    ),
    pretty: bool = typer.Option(False, "--pretty", "-p", help="Pretty-print JSON output"),
    data_only: bool = typer.Option(False, "--data-only", "-d", help="Return data only"),
) -> None:
    """
    Get parliamentary business items for treaty scrutiny.

    Returns list of business items with dates. Use when tracking treaty progress,
    CRaG (Constitutional Reform and Governance Act) procedures, debates, or
    parliamentary scrutiny.
    """
    url = f"{TREATIES_API_BASE}/Treaty/{treaty_id}/BusinessItems"
    result = run_async(get_result(url))
    typer.echo(format_output(result, pretty, data_only))
