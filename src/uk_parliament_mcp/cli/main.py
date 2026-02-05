"""CLI entry point for UK Parliament data access."""

from __future__ import annotations

import typer

from uk_parliament_mcp.cli import (
    bills,
    committees,
    composite,
    guide,
    hansard,
    interests,
    legislation,
    live,
    members,
    procedures,
    questions,
    votes,
)

app = typer.Typer(
    name="parliament",
    help="UK Parliament data CLI - Access 161 Parliament API tools from the terminal.",
    no_args_is_help=True,
)

# Register subcommand groups
app.add_typer(composite.app, name="composite")
app.add_typer(members.app, name="members")
app.add_typer(bills.app, name="bills")
app.add_typer(votes.app, name="votes")
app.add_typer(committees.app, name="committees")
app.add_typer(hansard.app, name="hansard")
app.add_typer(questions.app, name="questions")
app.add_typer(interests.app, name="interests")
app.add_typer(live.app, name="live")
app.add_typer(legislation.app, name="legislation")
app.add_typer(procedures.app, name="procedures")
app.add_typer(guide.app, name="guide")


@app.callback()
def callback() -> None:
    """
    UK Parliament CLI - query Parliament APIs from the terminal.

    Access MPs, bills, votes, committees, Hansard, and more.
    All data sourced from official parliament.uk APIs.
    """
    pass


def main() -> None:
    """Entry point for the CLI application."""
    app()


if __name__ == "__main__":
    main()
