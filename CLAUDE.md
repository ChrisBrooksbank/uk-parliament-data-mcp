# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

UK Parliament MCP Server (Unofficial) - A community-built Model Context Protocol server that bridges AI assistants with UK Parliament data APIs. Not affiliated with or endorsed by UK Parliament. Built with Python 3.11+, it provides 163 tools covering MPs/Lords, bills, votes, committees, Hansard, and more.

## Installation

```bash
# From PyPI (recommended)
pip install uk-parliament-mcp

# Or run without installing
uvx uk-parliament-mcp
```

## CLI Usage

The package includes a `parliament` CLI tool for terminal access to all 163 Parliament API tools:

```bash
# Search for an MP
parliament members search "Keir Starmer"

# Get comprehensive MP profile
parliament composite mp-profile "Rishi Sunak" --pretty

# Search bills
parliament bills search "Online Safety"

# Check how an MP voted on a topic
parliament composite check-vote "Boris Johnson" "climate"

# Get live chamber activity
parliament live commons-now

# Search Hansard debates
parliament hansard search-debates "NHS" --house 1

# Find your MP by postcode
parliament my-mp "SW1A 1AA"

# Browse the API catalogue
parliament api list
```

### Command Structure

```
parliament <group> <command> [options]
```

**Available command groups:**
- `api` - 6 commands for browsing the Parliament API catalogue
- `composite` - 5 high-level tools combining multiple API calls
- `members` - 29 commands for MPs, Lords, constituencies, parties
- `bills` - 21 commands for legislation, amendments, stages
- `votes` - 5 commands for Commons and Lords divisions
- `committees` - 26 commands for committee info, evidence
- `hansard` - 20 commands for parliamentary record
- `questions` - 11 commands for oral, written questions, and EDMs
- `interests` - 3 commands for register of interests
- `live` - 10 commands for live activity and calendar
- `legislation` - 10 commands for SIs and treaties
- `procedures` - 11 commands for Erskine May procedure rules
- `digest` - Daily/weekly parliamentary summary (aggregates 9 APIs)
- `watch` - Live Parliament dashboard with auto-refresh
- `guide` - Help and guidance commands

### Output Modes

```bash
# Default: auto (rich table in terminal, JSON when piped)
parliament members search "Starmer"

# Explicit format selection
parliament members search "Starmer" --format table
parliament members search "Starmer" --format markdown
parliament members search "Starmer" --format csv
parliament members search "Starmer" --format json

# Select specific fields (case-insensitive)
parliament members search "Starmer" --fields "id,nameDisplayAs,latestParty.name"

# Raw JSON with full {url, data} wrapper
parliament members search "Starmer" --raw

# Pretty-printed JSON
parliament members search "Starmer" --pretty

# Just the data (strips url wrapper)
parliament members search "Starmer" --data-only | jq '.items[0]'
```

**Global flags:**
- `--format` / `-f` - Output format: `json`, `table`, `markdown`, `csv`, `auto` (default: `auto`)
- `--fields` - Comma-separated field paths for column selection (case-insensitive)
- `--raw` - Output full wrapper JSON (url + data), disabling auto-formatting
- `--pretty` / `-p` - Pretty-print JSON output
- `--data-only` / `-d` - Return only the data field, not the {url, data} wrapper

### Common Use Cases

**MP research:**
```bash
# Full profile in one call
parliament composite mp-profile "Keir Starmer" --pretty

# Search by name
parliament members search "Sunak"

# Get biography
parliament members biography 4514

# Check registered interests
parliament interests search "Starmer"
```

**Bill tracking:**
```bash
# Comprehensive bill overview
parliament composite bill-overview "Online Safety" --pretty

# Search bills
parliament bills search "education"

# Get bill stages
parliament bills stages 123

# Check amendments
parliament bills amendments 123
```

**Voting records:**
```bash
# Check MP's vote on topic
parliament composite check-vote "Johnson" "climate" --pretty

# Search Commons divisions
parliament votes search "environment" --house 1

# Get specific division
parliament votes get-division 12345 --house 1
```

**Committee research:**
```bash
# Full committee summary
parliament composite committee-summary "Treasury" --pretty

# Search committees
parliament committees search "Health"

# Get committee evidence
parliament committees oral-evidence 456
```

**Live activity:**
```bash
# What's happening now in Commons
parliament live commons-now --pretty

# Today's calendar
parliament live calendar

# Next sitting date
parliament live next-sitting-date --house 1
```

**Daily/weekly digest:**
```bash
# Today's summary across all data sources
parliament digest --pretty

# Specific date
parliament digest --date 2025-01-15

# Weekly summary (Mon-Fri)
parliament digest --period week

# Commons only
parliament digest --house 1

# JSON output for piping
parliament digest --format json | jq '.commons_divisions | length'
```

### Help System

```bash
# Show all command groups
parliament --help

# Show commands in a group
parliament members --help

# Show command details
parliament members search --help

# Get tool reference
parliament guide tools

# Get detailed domain guidance
parliament guide topic members

# Get research workflow
parliament guide workflow "How did my MP vote on X?"
```

### Piping and Scripting

The CLI outputs raw JSON by default, making it easy to pipe to tools like `jq` and `grep`:

```bash
# Extract specific fields
parliament members search "Starmer" | jq '.data[0].id'

# Filter results
parliament bills search "education" | jq '.items[] | select(.currentStage == "Royal Assent")'

# Count results
parliament votes search "climate" --house 1 | jq '.data | length'

# Save to file
parliament composite mp-profile "Sunak" --pretty > profile.json

# Chain multiple commands
MP_ID=$(parliament members search "Starmer" | jq -r '.data[0].id')
parliament members biography $MP_ID --pretty
```

## Development Setup

```bash
# Create virtual environment and install dependencies
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

pip install -e ".[dev]"

# Run the MCP server (stdio transport)
python -m uk_parliament_mcp

# Run tests
pytest

# Type checking
mypy src/

# Linting
ruff check src/
ruff format src/
```

## CI/CD

GitHub Actions workflows in `.github/workflows/`:

- **ci.yml**: Runs on push/PR - linting (ruff), type checking (mypy), tests (pytest)
- **publish.yml**: Runs on GitHub Release - builds and publishes to PyPI via Trusted Publishing

**Release process:**
1. Update version in `src/uk_parliament_mcp/__init__.py`
2. Commit and push
3. Create GitHub Release with tag (e.g., `v1.0.1`)
4. Package auto-publishes to PyPI

## Architecture

```
AI Assistant ──(MCP/stdio)──> uk_parliament_mcp ──(HTTP)──> UK Parliament APIs
```

**Key Components:**

- **`__main__.py`**: Entry point. Configures logging to stderr (stdout reserved for MCP protocol), creates and runs the FastMCP server.

- **`server.py`**: FastMCP server setup. Creates the MCP server with server-level instructions and registers all tool modules.

- **`http_client.py`**: HTTP client with retry logic. Provides:
  - HTTP request handling with 3-retry exponential backoff
  - 30-second timeout protection
  - URL building with parameter filtering (`build_url`)
  - Consistent response format: `{url, data}` or `{url, error, statusCode}`

- **`tools/*.py`**: 16 tool modules (163 total tools) each targeting a specific Parliament API:
  | Module | API Domain | Purpose |
  |--------|------------|---------|
  | composite.py | Multiple APIs | High-level tools combining multiple API calls |
  | members.py | members-api.parliament.uk | MPs, Lords, constituencies, parties |
  | bills.py | bills-api.parliament.uk | Legislation, amendments, stages |
  | commons_votes.py | commonsvotes-api.parliament.uk | Commons divisions |
  | lords_votes.py | lordsvotes-api.parliament.uk | Lords divisions |
  | committees.py | committees-api.parliament.uk | Committee info, evidence |
  | hansard.py | hansard-api.parliament.uk | Parliamentary record |
  | oral_questions.py | oralquestionsandmotions-api.parliament.uk | EDMs, questions |
  | written_questions.py | writtenquestions-api.parliament.uk | Written PQs, statements |
  | interests.py | interests-api.parliament.uk | Register of interests |
  | now.py | now-api.parliament.uk | Live chamber activity |
  | whatson.py | whatson-api.parliament.uk | Calendar, sessions |
  | statutory_instruments.py | statutoryinstruments-api.parliament.uk | Acts, SIs |
  | treaties.py | treaties-api.parliament.uk | International treaties |
  | erskine_may.py | erskinemay-api.parliament.uk | Procedure rules |
  | core.py | N/A | Session management & agent guidance |

- **`context/`**: OpenAPI spec JSON files for each Parliament API (reference documentation)

## Adding New Tools

Follow the established pattern in any `tools/*.py` file:

```python
"""New API tools for [description]."""
from urllib.parse import quote

from mcp.server.fastmcp import FastMCP

from uk_parliament_mcp.http_client import build_url, get_result

NEW_API_BASE = "https://api.parliament.uk"


def register_tools(mcp: FastMCP) -> None:
    """Register new tools with the MCP server."""

    @mcp.tool()
    async def get_something(param: str) -> str:
        """Action | keywords, synonyms | Use case | Returns format

        Args:
            param: Description of the parameter.

        Returns:
            Description of what is returned.
        """
        url = f"{NEW_API_BASE}/endpoint?param={quote(param)}"
        return await get_result(url)
```

Tool descriptions use a 4-part semantic format: `Action | Keywords | Use case | Returns`

Then register in `server.py`:
```python
from uk_parliament_mcp.tools import new_api
# ...
new_api.register_tools(mcp)
```

## Key Conventions

- **House IDs**: 1 = Commons, 2 = Lords
- **Date format**: YYYY-MM-DD throughout
- **Pagination**: `skip`/`take` parameters where supported
- All tools are read-only and idempotent
- Raw JSON responses from Parliament APIs are passed through (not transformed)
- Use `build_url(base, params)` for URL construction with parameter filtering
- Use `await get_result(url)` for HTTP requests with retry logic

## Server Instructions (Automatic Context)

The server provides automatic context to MCP clients via the `instructions` parameter in FastMCP. This means:

- **No initialization required**: Clients receive guidance during MCP handshake without needing to call `order_order()` or `/parliament` first
- **Automatic behavior**: Per MCP spec, clients may add these instructions to the system prompt
- **Consistent sessions**: Every session starts with proper guidance about data sources and citation requirements

The instructions use the same `SYSTEM_PROMPT` from `core.py`, ensuring consistency across all initialization methods.

**How clients receive context:**
1. Client connects to MCP server
2. Server responds with `instructions` in initialize response
3. Client incorporates instructions (implementation varies by client)
4. Assistant automatically knows to use Parliament tools and cite sources

## Agent Skill (MCP Prompt)

The server also provides a `/parliament` agent skill that appears in the "/" command menu in MCP clients like Claude Desktop:

### `/parliament` (or `parliament` prompt)
Initialize a UK Parliament research session. Invocable as a slash command in Claude Desktop.

**Parameters:**
- `topic` (optional) - Jump directly to detailed guidance for a specific domain

**Example usage in Claude Desktop:**
```
/parliament              # Start session with quick reference
/parliament members      # Start session + detailed members guidance
```

This prompt is separate from the guidance **tools** below - prompts appear in the "/" menu and provide session context, while tools are called explicitly during research.

## Composite Tools

High-level tools that combine multiple API calls for common research tasks. Use these first for efficiency:

### `get_mp_profile(name)`
Get comprehensive MP/Lord profile in one call. Combines member search + biography + interests + voting.
- Returns: Basic info, biography, registered interests, recent votes
- Example: `get_mp_profile("Keir Starmer")`

### `check_mp_vote(mp_name, topic)`
Check how an MP voted on a specific topic. Combines member search + division lookup.
- Returns: MP info and divisions on the topic where they voted
- Example: `check_mp_vote("Boris Johnson", "climate")`

### `get_bill_overview(search_term)`
Get comprehensive bill overview. Combines bill search + details + stages + publications.
- Returns: Bill details, legislative stages, associated documents
- Example: `get_bill_overview("Online Safety")`

### `get_committee_summary(topic)`
Get comprehensive committee summary. Combines committee search + details + evidence + publications.
- Returns: Committee info, witness testimonies, written submissions, reports
- Example: `get_committee_summary("Treasury")`

### `get_my_mp(postcode, topic)`
Find MP by UK postcode. Combines constituency lookup + member search + biography + interests + votes.
- Returns: Constituency, MP profile, biography, registered interests, election result, recent votes
- Example: `get_my_mp("SW1A 1AA", "climate")`

## Agent Guidance Tools

The server also includes guidance **tools** to help AI assistants navigate the 163 available tools:

### `order_order()`
Start a UK Parliament research session. Say "Order Order" (like the Speaker) to activate. Returns:
- System prompt with data source transparency requirements
- Quick reference of all tool categories with entry points
- Key conventions (house IDs, date formats, pagination)

### `parliament_guide(topic)`
Get detailed guidance for a specific domain. Available topics:
- `composite` - 5 high-level tools combining multiple API calls
- `members` - 30 tools for MPs, Lords, constituencies, parties
- `bills` - 21 tools for legislation, amendments, stages
- `votes` - 10 tools for Commons and Lords divisions
- `committees` - 26 tools for committee info, meetings, evidence
- `hansard` - 20 tools for parliamentary record search
- `questions` - EDMs, oral questions
- `interests` - Register of Interests
- `live` - Current activity, calendar (now + whatson)
- `legislation` - SIs, treaties
- `procedures` - 13 tools for Erskine May, bill types, stage definitions
- `all` - Condensed reference of all 163 tools
- `conventions` - Date formats, house IDs, pagination
- `workflows` - Overview of common research patterns

### `parliament_workflow(query)`
Get step-by-step workflow for a research task. Matches queries to predefined patterns:
- "How did my MP vote on X?" → MP voting workflow
- "Track bill progress" → Bill tracking workflow
- "What committee examined X?" → Committee research workflow
- "Does MP have conflicts of interest?" → Interests workflow
- "What's happening now?" → Live activity workflow
- And more (backgrounds, Hansard, elections, EDMs, treaties)

### `get_cli_reference(group, search)`
Get CLI command reference. Returns all command groups, or details for a specific group, or search results matching a keyword.
- Example: `get_cli_reference()`, `get_cli_reference(group="members")`, `get_cli_reference(search="vote")`

Example usage:
```
# Start session
order_order()

# Get detailed guidance
parliament_guide("members")

# Plan a research task
parliament_workflow("How did my MP vote on climate?")
```

## Dependencies

- mcp (>=1.0.0) - Anthropic's official MCP library
- httpx (>=0.27.0) - Async HTTP client
- tenacity (>=8.2.0) - Retry logic (available but manual retry used)
- typer (>=0.9.0) - CLI framework for the parliament command

### Dev Dependencies

- pytest (>=8.0.0) - Testing
- pytest-asyncio (>=0.23.0) - Async test support
- pytest-httpx (>=0.30.0) - HTTP mocking
- ruff (>=0.3.0) - Linting and formatting
- mypy (>=1.8.0) - Type checking

## Project Structure

```
src/uk_parliament_mcp/
├── __init__.py
├── __main__.py         # MCP server entry point
├── server.py           # FastMCP server setup
├── http_client.py      # HTTP client with retry
├── cli/                # CLI tool (parliament command)
│   ├── __init__.py
│   ├── main.py         # CLI entry point and app assembly
│   ├── utils.py        # Output formatting, async runner
│   ├── formatters.py   # Output format handling (table, markdown, csv)
│   ├── pagination.py   # Auto-pagination for CLI commands
│   ├── renderers.py    # Rich terminal rendering for composite results
│   ├── api.py          # API explorer commands (6 commands)
│   ├── api_metadata.json # API catalogue metadata
│   ├── composite.py    # Composite commands (5 commands)
│   ├── members.py      # Member commands (29 commands)
│   ├── bills.py        # Bill commands (21 commands)
│   ├── votes.py        # Votes commands (5 commands)
│   ├── committees.py   # Committee commands (26 commands)
│   ├── hansard.py      # Hansard commands (20 commands)
│   ├── questions.py    # Questions commands (11 commands)
│   ├── interests.py    # Interests commands (3 commands)
│   ├── live.py         # Live/calendar commands (10 commands)
│   ├── legislation.py  # SI/treaty commands (10 commands)
│   ├── procedures.py   # Erskine May commands (11 commands)
│   ├── digest.py       # Daily/weekly digest (aggregates 9 APIs)
│   ├── watch.py        # Live dashboard with auto-refresh
│   └── guide.py        # Help/guidance commands (4 commands)
└── tools/              # MCP tool modules
    ├── __init__.py
    ├── core.py         # Session management & guidance (4 tools)
    ├── composite.py    # High-level composite tools (5 tools)
    ├── members.py      # Member tools (30 tools)
    ├── bills.py        # Bills tools (21 tools)
    ├── committees.py   # Committees tools (26 tools)
    ├── commons_votes.py    # Commons votes (5 tools)
    ├── lords_votes.py      # Lords votes (5 tools)
    ├── hansard.py          # Hansard (20 tools)
    ├── oral_questions.py   # EDMs & oral questions (5 tools)
    ├── written_questions.py # Written PQs & statements (7 tools)
    ├── interests.py        # Interests (3 tools)
    ├── now.py              # Live activity (2 tools)
    ├── whatson.py          # Calendar & procedural dates (8 tools)
    ├── statutory_instruments.py  # SIs & Acts (5 tools)
    ├── treaties.py         # Treaties (6 tools)
    └── erskine_may.py      # Procedure (11 tools)
```
