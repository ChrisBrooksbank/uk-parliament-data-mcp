"""FastMCP server configuration and tool registration."""
from mcp.server.fastmcp import FastMCP

from uk_parliament_mcp.tools import (
    bills,
    committees,
    commons_votes,
    core,
    erskine_may,
    hansard,
    interests,
    lords_votes,
    members,
    now,
    oral_questions,
    statutory_instruments,
    treaties,
    whatson,
)


def create_server() -> FastMCP:
    """Create and configure the MCP server with all tools registered."""
    mcp = FastMCP(name="uk-parliament-mcp")

    # Register all tool modules
    core.register_tools(mcp)
    members.register_tools(mcp)
    bills.register_tools(mcp)
    committees.register_tools(mcp)
    commons_votes.register_tools(mcp)
    lords_votes.register_tools(mcp)
    hansard.register_tools(mcp)
    oral_questions.register_tools(mcp)
    interests.register_tools(mcp)
    now.register_tools(mcp)
    whatson.register_tools(mcp)
    statutory_instruments.register_tools(mcp)
    treaties.register_tools(mcp)
    erskine_may.register_tools(mcp)

    return mcp
