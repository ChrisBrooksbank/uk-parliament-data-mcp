# Roadmap

Open work. Finished plans and specs (the phase 1–5 improvement plan, the CLI build-out, the missing-endpoints gap analysis) are in [`docs/archive/`](docs/archive/), and what has shipped is in [`CHANGELOG.md`](CHANGELOG.md).

## Dependencies

- **Migrate to mcp 2.x.** `pyproject.toml` pins `mcp<2` because 2.x renamed `FastMCP` to `MCPServer` (`mcp.server.mcpserver`) and changed other APIs. See the [migration guide](https://py.sdk.modelcontextprotocol.io/v2/migration/#fastmcp-renamed-to-mcpserver).
