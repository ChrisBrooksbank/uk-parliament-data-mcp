"""Guide CLI commands for help and workflow guidance."""

from __future__ import annotations

import typer

from uk_parliament_mcp.cli.utils import run_async
from uk_parliament_mcp.tools.core import (
    GUIDANCE_CONTENT,
    QUICK_REFERENCE,
    SYSTEM_PROMPT,
    WORKFLOW_PATTERNS,
    _format_workflow,
    _suggest_general_approach,
)

app = typer.Typer(help="Help and guidance for UK Parliament research")


async def _order_order_async() -> str:
    """Start UK Parliament research session."""
    return f"{SYSTEM_PROMPT}\n\n---\n\n{QUICK_REFERENCE}"


async def _parliament_guide_async(topic: str) -> str:
    """Get detailed guidance for a specific Parliament data domain."""
    topic_lower = topic.lower().strip()

    if topic_lower not in GUIDANCE_CONTENT:
        available = ", ".join(sorted(GUIDANCE_CONTENT.keys()))
        return f"Topic '{topic}' not recognized.\n\nAvailable topics: {available}"

    return GUIDANCE_CONTENT[topic_lower]


async def _parliament_workflow_async(query: str) -> str:
    """Get step-by-step workflow guidance for a parliamentary research task."""
    query_lower = query.lower()

    # Find matching workflow pattern
    for pattern in WORKFLOW_PATTERNS:
        if any(keyword in query_lower for keyword in pattern["keywords"]):
            return _format_workflow(pattern)

    # No match - provide general guidance
    return _suggest_general_approach(query)


@app.command("tools")
def tools(
    pretty: bool = typer.Option(False, "--pretty", "-p", help="Pretty-print output"),
) -> None:
    """
    Start UK Parliament research session - list all available tools.

    Returns system prompt and quick reference of all 161 tool categories with
    entry points, key conventions, and common patterns.
    """
    result = run_async(_order_order_async())
    # For guide commands, output is plain text, not JSON
    # So we skip the format_output wrapper
    typer.echo(result)


@app.command("topic")
def topic(
    domain: str = typer.Argument(..., help="Domain to get guidance for"),
    pretty: bool = typer.Option(False, "--pretty", "-p", help="Pretty-print output"),
) -> None:
    """
    Get detailed guidance for a specific Parliament data domain.

    Available topics: members, bills, votes, committees, hansard, questions,
    interests, live, legislation, procedures, all, conventions, workflows.

    Returns comprehensive guidance including tool names, parameters, and
    typical workflows for the selected domain.
    """
    result = run_async(_parliament_guide_async(domain))
    typer.echo(result)


@app.command("workflow")
def workflow(
    query: str = typer.Argument(..., help="Research question or task description"),
    pretty: bool = typer.Option(False, "--pretty", "-p", help="Pretty-print output"),
) -> None:
    """
    Get step-by-step workflow guidance for a parliamentary research task.

    Matches queries to predefined patterns and returns recommended sequence
    of tools with parameters and expected data flow.

    Examples:
      - "How did my MP vote on X?"
      - "Track bill progress"
      - "What committee examined X?"
      - "Does MP have conflicts of interest?"
    """
    result = run_async(_parliament_workflow_async(query))
    typer.echo(result)
