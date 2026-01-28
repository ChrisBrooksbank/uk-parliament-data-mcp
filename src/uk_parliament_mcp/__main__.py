"""Entry point for the UK Parliament MCP Server."""
import logging
import sys

from uk_parliament_mcp.server import create_server


def main() -> None:
    """Run the MCP server with stdio transport."""
    # Configure logging to stderr (stdout is for MCP protocol)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        stream=sys.stderr,
    )

    server = create_server()
    server.run(transport="stdio")


if __name__ == "__main__":
    main()
