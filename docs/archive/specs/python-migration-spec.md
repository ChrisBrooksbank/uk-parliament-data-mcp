# UK Parliament MCP Server: C# to Python Migration Specification

## 1. Executive Summary

This specification details the complete migration of the UK Parliament MCP Server from C# .NET 9.0 to Python. The server bridges AI assistants (Claude, Copilot) with official UK Parliament APIs, providing 86 tools across 14 modules for querying parliamentary data.

### Objectives
- Full feature parity with all 86 existing tools
- Maintain HTTP retry logic and error handling patterns
- Use modern Python async patterns
- Clean, maintainable project structure
- Equivalent configuration for Claude Desktop and VS Code

---

## 2. Target Technology Stack

| Component | Technology | Version |
|-----------|------------|---------|
| Language | Python | 3.11+ |
| MCP Library | `mcp` (Anthropic official) | ≥1.0.0 |
| HTTP Client | `httpx` | ≥0.27.0 |
| Retry Logic | `tenacity` | ≥8.2.0 |
| Package Manager | `uv` or `pip` | Latest |
| Build System | `hatchling` | Latest |
| Testing | `pytest`, `pytest-asyncio`, `pytest-httpx` | Latest |
| Linting | `ruff` | ≥0.3.0 |
| Type Checking | `mypy` | ≥1.8.0 |

---

## 3. Project Structure

```
uk-parliament-mcp-python/
├── pyproject.toml              # Project configuration and dependencies
├── README.md                   # User documentation (updated for Python)
├── CLAUDE.md                   # Claude Code guidance (updated for Python)
├── .python-version             # Python version: 3.11
├── src/
│   └── uk_parliament_mcp/
│       ├── __init__.py         # Package initialization
│       ├── __main__.py         # Entry point: python -m uk_parliament_mcp
│       ├── server.py           # FastMCP server setup and tool registration
│       ├── http_client.py      # HTTP client with retry logic
│       └── tools/
│           ├── __init__.py     # Tools package initialization
│           ├── core.py         # CoreTools (2 tools)
│           ├── members.py      # MembersTools (24 tools)
│           ├── bills.py        # BillsTools (19 tools)
│           ├── committees.py   # CommitteesTools (10 tools)
│           ├── commons_votes.py    # CommonsVotesTools (6 tools)
│           ├── lords_votes.py  # LordsVotesTools (5 tools)
│           ├── hansard.py      # HansardTools (1 tool)
│           ├── oral_questions.py   # OralQuestionsTools (3 tools)
│           ├── interests.py    # InterestsTools (3 tools)
│           ├── now.py          # NowTools (2 tools)
│           ├── whatson.py      # WhatsOnTools (3 tools)
│           ├── statutory_instruments.py  # StatutoryInstrumentsTools (2 tools)
│           ├── treaties.py     # TreatiesTools (1 tool)
│           └── erskine_may.py  # ErskineMayTools (1 tool)
├── context/                    # OpenAPI spec JSON files (copied from C#)
│   ├── bills-api.json
│   ├── members-api.json
│   ├── committees-api.json
│   └── ... (other API specs)
├── tests/
│   ├── __init__.py
│   ├── conftest.py             # Pytest fixtures
│   ├── test_http_client.py     # HTTP client tests
│   └── test_tools/
│       ├── __init__.py
│       ├── test_core.py
│       ├── test_members.py
│       └── ... (test for each tool module)
└── config/
    ├── claude_desktop_config.json.example
    └── vscode_mcp_config.json.example
```

---

## 4. Dependencies (pyproject.toml)

```toml
[project]
name = "uk-parliament-mcp"
version = "1.0.0"
description = "UK Parliament MCP Server - bridges AI assistants with UK Parliament APIs"
readme = "README.md"
license = { text = "MIT" }
requires-python = ">=3.11"
authors = [
    { name = "Chris Brooksbank" }
]
keywords = ["mcp", "parliament", "uk", "api", "claude", "ai"]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
]

dependencies = [
    "mcp>=1.0.0",
    "httpx>=0.27.0",
    "tenacity>=8.2.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "pytest-httpx>=0.30.0",
    "ruff>=0.3.0",
    "mypy>=1.8.0",
]

[project.scripts]
uk-parliament-mcp = "uk_parliament_mcp.__main__:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/uk_parliament_mcp"]

[tool.ruff]
line-length = 100
target-version = "py311"
select = ["E", "F", "I", "N", "W", "UP", "B", "C4", "SIM"]

[tool.ruff.isort]
known-first-party = ["uk_parliament_mcp"]

[tool.mypy]
python_version = "3.11"
strict = true
warn_return_any = true
warn_unused_ignores = true

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

---

## 5. Core Components

### 5.1 Entry Point (`__main__.py`)

```python
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
```

### 5.2 Server Setup (`server.py`)

```python
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
    mcp = FastMCP(
        name="uk-parliament-mcp",
        version="1.0.0",
    )

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
```

### 5.3 HTTP Client with Retry Logic (`http_client.py`)

This is the Python equivalent of C# `BaseTools.cs`:

```python
"""HTTP client with retry logic for Parliament API requests."""
from __future__ import annotations

import json
import logging
from typing import Any
from urllib.parse import urlencode

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

logger = logging.getLogger(__name__)

# Configuration constants (matching C# implementation)
HTTP_TIMEOUT = 30.0  # seconds
MAX_RETRY_ATTEMPTS = 3
RETRY_DELAY_BASE = 1.0  # seconds

# HTTP status codes that should trigger a retry
TRANSIENT_STATUS_CODES = frozenset({408, 429, 500, 502, 503, 504})


def build_url(base_url: str, parameters: dict[str, Any]) -> str:
    """
    Build URL with query parameters, filtering out None and empty values.

    Equivalent to C# BaseTools.BuildUrl()

    Args:
        base_url: The base URL without query parameters
        parameters: Dictionary of parameter names to values

    Returns:
        URL with query string, or just base_url if no valid parameters
    """
    valid_params = {
        k: str(v).lower() if isinstance(v, bool) else str(v)
        for k, v in parameters.items()
        if v is not None and v != ""
    }

    if not valid_params:
        return base_url

    return f"{base_url}?{urlencode(valid_params)}"


def _is_retryable_status(status_code: int) -> bool:
    """Check if HTTP status code is transient and should be retried."""
    return status_code in TRANSIENT_STATUS_CODES


class ParliamentHTTPClient:
    """Async HTTP client with retry logic for Parliament APIs."""

    def __init__(self) -> None:
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=HTTP_TIMEOUT)
        return self._client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def get_result(self, url: str) -> str:
        """
        Make HTTP GET request with retry logic.

        Returns JSON serialized response matching C# format:
        - Success: {"url": "...", "data": "..."}
        - Error: {"url": "...", "error": "...", "statusCode": N}

        Equivalent to C# BaseTools.GetResult()
        """
        client = await self._get_client()

        for attempt in range(MAX_RETRY_ATTEMPTS):
            try:
                logger.info(
                    "Making HTTP request to %s (attempt %d/%d)",
                    url, attempt + 1, MAX_RETRY_ATTEMPTS
                )

                response = await client.get(url)

                if response.is_success:
                    data = response.text
                    logger.info("Successfully retrieved data from %s", url)
                    return json.dumps({"url": url, "data": data})

                if _is_retryable_status(response.status_code):
                    logger.warning(
                        "Transient failure for %s: %d. Attempt %d/%d",
                        url, response.status_code, attempt + 1, MAX_RETRY_ATTEMPTS
                    )
                    if attempt < MAX_RETRY_ATTEMPTS - 1:
                        import asyncio
                        await asyncio.sleep(RETRY_DELAY_BASE * (attempt + 1))
                        continue

                # Non-retryable error or final attempt
                error_message = (
                    f"HTTP request failed with status {response.status_code}: "
                    f"{response.reason_phrase}"
                )
                logger.error("Final failure for %s: %d", url, response.status_code)
                return json.dumps({
                    "url": url,
                    "error": error_message,
                    "statusCode": response.status_code
                })

            except httpx.TimeoutException:
                logger.warning(
                    "Request to %s timed out. Attempt %d/%d",
                    url, attempt + 1, MAX_RETRY_ATTEMPTS
                )
                if attempt == MAX_RETRY_ATTEMPTS - 1:
                    return json.dumps({
                        "url": url,
                        "error": "Request timed out after multiple attempts"
                    })
                import asyncio
                await asyncio.sleep(RETRY_DELAY_BASE * (attempt + 1))

            except httpx.NetworkError as e:
                logger.warning(
                    "Network error for %s: %s. Attempt %d/%d",
                    url, str(e), attempt + 1, MAX_RETRY_ATTEMPTS
                )
                if attempt == MAX_RETRY_ATTEMPTS - 1:
                    return json.dumps({
                        "url": url,
                        "error": f"Network error: {str(e)}"
                    })
                import asyncio
                await asyncio.sleep(RETRY_DELAY_BASE * (attempt + 1))

            except Exception as e:
                logger.error("Unexpected error for %s: %s", url, str(e))
                return json.dumps({
                    "url": url,
                    "error": f"Unexpected error: {str(e)}"
                })

        return json.dumps({"url": url, "error": "Maximum retry attempts exceeded"})


# Global client instance for reuse across tools
_client = ParliamentHTTPClient()


async def get_result(url: str) -> str:
    """Convenience function using global client."""
    return await _client.get_result(url)
```

---

## 6. Tool Implementation Patterns

### 6.1 C# to Python Translation Rules

| C# Pattern | Python Equivalent |
|------------|-------------------|
| `[McpServerToolType]` class | Module with `register_tools(mcp)` function |
| `[McpServerTool(ReadOnly=true, Idempotent=true)]` | `@mcp.tool()` decorator |
| `[Description("...")]` on method | Docstring |
| `[Description("...")]` on parameter | Type hint + Args section in docstring |
| `async Task<string>` | `async def ... -> str` |
| `Uri.EscapeDataString(param)` | `urllib.parse.quote(param)` |
| `BuildUrl(base, dict)` | `build_url(base, dict)` |
| `await GetResult(url)` | `await get_result(url)` |
| Nullable `int?` | `int | None = None` |
| Nullable `string` | `str | None = None` |
| `bool` with default | `bool = False` |
| Array `int[]` | `list[int]` |

### 6.2 Example: Core Tools (`tools/core.py`)

```python
"""Core tools for Parliament data assistant session management."""
from mcp.server.fastmcp import FastMCP

SYSTEM_PROMPT = """You are a helpful assistant that answers questions using only data from UK Parliament MCP servers.
When the session begins, introduce yourself with a brief message such as:
"Hello! I'm a parliamentary data assistant. I can help answer questions using official data from the UK Parliament MCP APIs. Just ask me something, and I'll fetch what I can — and I'll always show you which sources I used."
When responding to user queries, you must:
Only retrieve and use data from the MCP API endpoints this server provides.
Avoid using any external sources or inferred knowledge.
After every response, append a list of all MCP API URLs used to generate the answer.
If no relevant data is available via the MCP API, state that clearly and do not attempt to fabricate a response.
Convert raw data into human-readable summaries while preserving accuracy, but always list the raw URLs used."""

GOODBYE_PROMPT = """You are now interacting as a normal assistant. There are no special restrictions or requirements for using UK Parliament MCP data. You may answer questions using any available data or knowledge, and you do not need to append MCP API URLs or limit yourself to MCP sources. Resume normal assistant behavior."""


def register_tools(mcp: FastMCP) -> None:
    """Register core tools with the MCP server."""

    @mcp.tool()
    async def hello_parliament() -> str:
        """Initialize Parliament data assistant with system prompt.

        Use FIRST when beginning parliamentary research to get proper assistant
        behavior and data handling guidelines.

        Returns:
            System prompt for optimal parliamentary data interaction.
        """
        return SYSTEM_PROMPT

    @mcp.tool()
    async def goodbye_parliament() -> str:
        """End Parliament session and restore normal assistant behavior.

        Use when finished with parliamentary research to return to standard
        assistant behavior.

        Returns:
            Prompt to restore normal assistant behavior.
        """
        return GOODBYE_PROMPT
```

### 6.3 Example: Members Tools (`tools/members.py`)

```python
"""Members API tools for MPs, Lords, constituencies, and parties."""
from urllib.parse import quote

from mcp.server.fastmcp import FastMCP

from uk_parliament_mcp.http_client import build_url, get_result

MEMBERS_API_BASE = "https://members-api.parliament.uk/api"


def register_tools(mcp: FastMCP) -> None:
    """Register member tools with the MCP server."""

    @mcp.tool()
    async def get_member_by_name(name: str) -> str:
        """Search for MPs and Lords by name with comprehensive member details.

        Use for identifying members, checking spellings, finding member IDs,
        or getting basic member information.

        Args:
            name: Full or partial name to search for. Examples: 'Boris Johnson',
                  'Keir Starmer', 'Smith'. Searches current and former members.

        Returns:
            Member profiles with names, parties, constituencies, and current status.
        """
        url = f"{MEMBERS_API_BASE}/Members/Search?Name={quote(name)}"
        return await get_result(url)

    @mcp.tool()
    async def get_member_by_id(member_id: int) -> str:
        """Get comprehensive member profile by Parliament member ID.

        Use when you have a member ID and need complete biographical, political,
        and contact information.

        Args:
            member_id: Parliament member ID. Get from member search first.

        Returns:
            Detailed member data including roles, constituency, party, and career.
        """
        url = f"{MEMBERS_API_BASE}/Members/{member_id}"
        return await get_result(url)

    @mcp.tool()
    async def get_constituencies(
        skip: int | None = None,
        take: int | None = None,
    ) -> str:
        """Get list of UK parliamentary constituencies with pagination.

        Use when you need constituency information or want to browse all
        constituencies.

        Args:
            skip: Number of constituencies to skip (for pagination).
            take: Number of constituencies to return (default 20, max 100).

        Returns:
            Constituency data with names, regions, and current MPs.
        """
        url = build_url(f"{MEMBERS_API_BASE}/Location/Constituency/Search", {
            "skip": skip,
            "take": take,
        })
        return await get_result(url)

    @mcp.tool()
    async def search_members(
        name: str | None = None,
        location: str | None = None,
        post_title: str | None = None,
        party_id: int | None = None,
        house: int | None = None,
        constituency_id: int | None = None,
        name_starts_with: str | None = None,
        gender: str | None = None,
        membership_started_since: str | None = None,
        membership_ended_since: str | None = None,
        was_member_on_or_after: str | None = None,
        was_member_on_or_before: str | None = None,
        was_member_of_house: int | None = None,
        is_eligible: bool | None = None,
        is_current_member: bool | None = None,
        policy_interest_id: int | None = None,
        experience: str | None = None,
        skip: int = 0,
        take: int = 20,
    ) -> str:
        """Search for MPs and Lords with comprehensive filtering options.

        Use when you need to find members by name, location, party, constituency,
        gender, posts held, or policy interests.

        Args:
            name: Full or partial name to search for.
            location: Location or constituency name.
            post_title: Post title (e.g. 'Minister', 'Secretary of State').
            party_id: Party ID to filter by.
            house: House number (1=Commons, 2=Lords).
            constituency_id: Constituency ID to filter by.
            name_starts_with: Filter names starting with specific letter(s).
            gender: Gender filter ('M' or 'F').
            membership_started_since: Date in YYYY-MM-DD format.
            membership_ended_since: Date in YYYY-MM-DD format.
            was_member_on_or_after: Date in YYYY-MM-DD format.
            was_member_on_or_before: Date in YYYY-MM-DD format.
            was_member_of_house: House number (1=Commons, 2=Lords).
            is_eligible: Filter by eligibility status.
            is_current_member: Filter by current membership status.
            policy_interest_id: Policy interest ID to filter by.
            experience: Search term for professional experience.
            skip: Number of records to skip (pagination).
            take: Number of records to return (default 20, max 100).

        Returns:
            Matching member profiles with comprehensive details.
        """
        url = build_url(f"{MEMBERS_API_BASE}/Members/Search", {
            "Name": name,
            "Location": location,
            "PostTitle": post_title,
            "PartyId": party_id,
            "House": house,
            "ConstituencyId": constituency_id,
            "NameStartsWith": name_starts_with,
            "Gender": gender,
            "MembershipStartedSince": membership_started_since,
            "MembershipEnded.MembershipEndedSince": membership_ended_since,
            "MembershipInDateRange.WasMemberOnOrAfter": was_member_on_or_after,
            "MembershipInDateRange.WasMemberOnOrBefore": was_member_on_or_before,
            "MembershipInDateRange.WasMemberOfHouse": was_member_of_house,
            "IsEligible": is_eligible,
            "IsCurrentMember": is_current_member,
            "PolicyInterestId": policy_interest_id,
            "Experience": experience,
            "skip": skip,
            "take": take,
        })
        return await get_result(url)

    # ... Additional 20 member tools following the same pattern
```

---

## 7. Complete Tool Inventory

### 7.1 Summary by Module

| Module | C# Class | Tool Count | API Base URL |
|--------|----------|------------|--------------|
| core.py | CoreTools | 2 | N/A (local prompts) |
| members.py | MembersTools | 24 | https://members-api.parliament.uk/api |
| bills.py | BillsTools | 19 | https://bills-api.parliament.uk/api/v1 |
| committees.py | CommitteesTools | 10 | https://committees-api.parliament.uk/api |
| commons_votes.py | CommonsVotesTools | 6 | http://commonsvotes-api.parliament.uk/data |
| lords_votes.py | LordsVotesTools | 5 | http://lordsvotes-api.parliament.uk/data |
| hansard.py | HansardTools | 1 | https://hansard-api.parliament.uk |
| oral_questions.py | OralQuestionsTools | 3 | https://oralquestionsandmotions-api.parliament.uk |
| interests.py | InterestsTools | 3 | https://interests-api.parliament.uk/api/v1 |
| now.py | NowTools | 2 | https://now-api.parliament.uk/api |
| whatson.py | WhatsOnTools | 3 | https://whatson-api.parliament.uk/calendar |
| statutory_instruments.py | StatutoryInstrumentsTools | 2 | https://statutoryinstruments-api.parliament.uk/api/v2 |
| treaties.py | TreatiesTools | 1 | https://treaties-api.parliament.uk/api |
| erskine_may.py | ErskineMayTools | 1 | https://erskinemay-api.parliament.uk/api |
| **Total** | **14 classes** | **86 tools** | |

### 7.2 Detailed Tool List

#### CoreTools (2 tools)
- `hello_parliament()` - Initialize session with system prompt
- `goodbye_parliament()` - End session, restore normal behavior

#### MembersTools (24 tools)
- `get_member_by_name(name)` - Search members by name
- `get_answering_bodies()` - Get government departments
- `get_member_by_id(member_id)` - Get member by ID
- `edms_for_member_id(member_id)` - Get EDMs for member
- `parties_list_by_house(house)` - Get parties by house
- `get_departments()` - Get departments list
- `get_contributions(member_id)` - Get member contributions
- `get_constituencies(skip, take)` - Get constituencies
- `get_election_results_for_constituency(constituency_id)` - Get election results
- `get_lords_interests_staff(search_term)` - Get Lords staff interests
- `get_members_biography(member_id)` - Get member biography
- `get_members_contact(member_id)` - Get member contact info
- `search_members(...)` - Advanced member search (19 params)
- `search_members_historical(name, date, skip, take)` - Historical search
- `get_member_experience(member_id)` - Get member experience
- `get_member_focus(member_id)` - Get member focus areas
- `get_member_registered_interests(member_id, house)` - Get interests
- `get_member_staff(member_id)` - Get member staff
- `get_member_synopsis(member_id)` - Get member synopsis
- `get_member_voting(member_id, house, page)` - Get voting record
- `get_member_written_questions(member_id, page)` - Get written questions
- `get_members_history(member_ids)` - Get history for multiple members
- `get_member_latest_election_result(member_id)` - Get latest election
- `get_member_portrait_url(member_id)` - Get portrait URL
- `get_member_thumbnail_url(member_id)` - Get thumbnail URL

#### BillsTools (19 tools)
- `get_recently_updated_bills(take)` - Get recent bills
- `search_bills(search_term, member_id)` - Search bills
- `bill_types()` - Get bill types
- `bill_stages()` - Get bill stages
- `get_bill_by_id(bill_id)` - Get bill details
- `get_bill_stages(bill_id, skip, take)` - Get stages for bill
- `get_bill_stage_details(bill_id, bill_stage_id)` - Get stage details
- `get_bill_stage_amendments(...)` - Get amendments (8 params)
- `get_amendment_by_id(bill_id, bill_stage_id, amendment_id)` - Get amendment
- `get_bill_stage_ping_pong_items(...)` - Get ping pong items (8 params)
- `get_ping_pong_item_by_id(bill_id, bill_stage_id, ping_pong_item_id)` - Get item
- `get_bill_publications(bill_id)` - Get bill publications
- `get_bill_stage_publications(bill_id, stage_id)` - Get stage publications
- `get_publication_document(publication_id, document_id)` - Get document
- `get_bill_news_articles(bill_id, skip, take)` - Get news articles
- `get_all_bills_rss()` - Get all bills RSS
- `get_public_bills_rss()` - Get public bills RSS
- `get_private_bills_rss()` - Get private bills RSS
- `get_bill_rss(bill_id)` - Get bill-specific RSS
- `get_publication_types(skip, take)` - Get publication types
- `get_sittings(house, date_from, date_to, skip, take)` - Get sittings

#### CommitteesTools (10 tools)
- `get_committee_meetings(from_date, to_date)` - Get meetings
- `search_committees(search_term)` - Search committees
- `get_committee_types()` - Get committee types
- `get_committee_by_id(committee_id, include_banners, show_on_website_only)` - Get committee
- `get_events(...)` - Get events (14 params)
- `get_event_by_id(event_id, show_on_website_only)` - Get event
- `get_committee_events(...)` - Get committee events (14 params)
- `get_committee_members(committee_id, membership_status, show_on_website_only, skip, take)` - Get members
- `get_publications(...)` - Get publications (10 params)
- `get_publication_by_id(publication_id, show_on_website_only)` - Get publication
- `get_written_evidence(...)` - Get written evidence (8 params)
- `get_oral_evidence(...)` - Get oral evidence (8 params)

#### CommonsVotesTools (6 tools)
- `search_commons_divisions(search_term, member_id, start_date, end_date, division_number)` - Search divisions
- `get_commons_voting_record_for_member(member_id)` - Get voting record
- `get_commons_division_by_id(division_id)` - Get division details
- `get_commons_divisions_grouped_by_party(...)` - Get by party (6 params)
- `get_commons_divisions_search_count(...)` - Get count (6 params)

#### LordsVotesTools (5 tools)
- `search_lords_divisions(search_term)` - Search divisions
- `get_lords_voting_record_for_member(...)` - Get voting record (8 params)
- `get_lords_division_by_id(division_id)` - Get division details
- `get_lords_divisions_grouped_by_party(...)` - Get by party (6 params)
- `get_lords_divisions_search_count(...)` - Get count (6 params)

#### HansardTools (1 tool)
- `search_hansard(house, start_date, end_date, search_term)` - Search Hansard

#### OralQuestionsTools (3 tools)
- `get_recently_tabled_edms(take)` - Get recent EDMs
- `search_early_day_motions(search_term)` - Search EDMs
- `search_oral_question_times(answering_date_start, answering_date_end)` - Search question times

#### InterestsTools (3 tools)
- `search_roi(member_id)` - Search register of interests
- `interests_categories()` - Get interest categories
- `get_registers_of_interests()` - Get registers

#### NowTools (2 tools)
- `happening_now_in_commons()` - Get live Commons activity
- `happening_now_in_lords()` - Get live Lords activity

#### WhatsOnTools (3 tools)
- `search_calendar(house, start_date, end_date)` - Search calendar
- `get_sessions()` - Get sessions
- `get_non_sitting_days(house, start_date, end_date)` - Get non-sitting days

#### StatutoryInstrumentsTools (2 tools)
- `search_statutory_instruments(name)` - Search SIs
- `search_acts_of_parliament(name)` - Search Acts

#### TreatiesTools (1 tool)
- `search_treaties(search_text)` - Search treaties

#### ErskineMayTools (1 tool)
- `search_erskine_may(search_term)` - Search Erskine May

---

## 8. Configuration Examples

### 8.1 Claude Desktop Configuration (Windows)

File: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "uk-parliament": {
      "command": "python",
      "args": ["-m", "uk_parliament_mcp"],
      "cwd": "C:\\code\\uk-parliament-mcp-python"
    }
  }
}
```

With `uv` (recommended):

```json
{
  "mcpServers": {
    "uk-parliament": {
      "command": "uv",
      "args": ["run", "uk-parliament-mcp"],
      "cwd": "C:\\code\\uk-parliament-mcp-python"
    }
  }
}
```

### 8.2 VS Code MCP Configuration

File: `.vscode/mcp.json`

```json
{
  "mcpServers": {
    "uk-parliament": {
      "command": "python",
      "args": ["-m", "uk_parliament_mcp"],
      "transport": "stdio"
    }
  }
}
```

---

## 9. Testing Strategy

### 9.1 Unit Tests (`tests/test_http_client.py`)

```python
"""Tests for HTTP client with retry logic."""
import json

import pytest
from pytest_httpx import HTTPXMock

from uk_parliament_mcp.http_client import build_url, get_result


class TestBuildUrl:
    def test_no_params(self):
        result = build_url("https://api.example.com/test", {})
        assert result == "https://api.example.com/test"

    def test_filters_none_values(self):
        result = build_url("https://api.example.com/test", {
            "param1": "value1",
            "param2": None,
            "param3": "value3",
        })
        assert result == "https://api.example.com/test?param1=value1&param3=value3"

    def test_filters_empty_strings(self):
        result = build_url("https://api.example.com/test", {
            "param1": "value1",
            "param2": "",
        })
        assert result == "https://api.example.com/test?param1=value1"

    def test_converts_booleans_to_lowercase(self):
        result = build_url("https://api.example.com/test", {"flag": True})
        assert result == "https://api.example.com/test?flag=true"

    def test_url_encodes_special_characters(self):
        result = build_url("https://api.example.com/test", {"q": "hello world"})
        assert "hello+world" in result or "hello%20world" in result


class TestGetResult:
    @pytest.mark.asyncio
    async def test_successful_request(self, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            url="https://api.example.com/test",
            json={"items": []},
        )

        result = await get_result("https://api.example.com/test")
        parsed = json.loads(result)

        assert parsed["url"] == "https://api.example.com/test"
        assert "data" in parsed
        assert "error" not in parsed

    @pytest.mark.asyncio
    async def test_returns_error_on_404(self, httpx_mock: HTTPXMock):
        httpx_mock.add_response(status_code=404)

        result = await get_result("https://api.example.com/test")
        parsed = json.loads(result)

        assert "error" in parsed
        assert parsed["statusCode"] == 404
```

### 9.2 Integration Tests (`tests/integration/test_server.py`)

```python
"""Integration tests for MCP server."""
import pytest

from uk_parliament_mcp.server import create_server


class TestServerIntegration:
    def test_server_creates_successfully(self):
        server = create_server()
        assert server is not None

    def test_has_expected_tool_count(self):
        server = create_server()
        tools = list(server.list_tools())
        assert len(tools) == 86, f"Expected 86 tools, got {len(tools)}"

    def test_core_tools_registered(self):
        server = create_server()
        tool_names = {t.name for t in server.list_tools()}

        assert "hello_parliament" in tool_names
        assert "goodbye_parliament" in tool_names

    def test_member_tools_registered(self):
        server = create_server()
        tool_names = {t.name for t in server.list_tools()}

        assert "get_member_by_name" in tool_names
        assert "search_members" in tool_names
```

---

## 10. Migration Execution Steps

### Phase 1: Project Setup
1. Create Python project structure alongside existing C# code (keep C# as reference!)
2. Create `pyproject.toml` with dependencies
3. Create package structure under `src/uk_parliament_mcp/`
4. Create `__init__.py` files
5. **DO NOT delete C# files yet** - they are the reference for migration

### Phase 2: Core Infrastructure
1. Implement `http_client.py` with full retry logic
2. Implement `__main__.py` entry point
3. Implement `server.py` with FastMCP setup
4. Test basic server startup: `python -m uk_parliament_mcp`

### Phase 3: Tool Migration (by priority)
1. `tools/core.py` (2 tools) - test session management
2. `tools/members.py` (24 tools) - largest module, establishes patterns
3. `tools/bills.py` (19 tools) - second largest
4. Remaining 11 modules (40 tools)

### Phase 4: Testing
1. Write unit tests for `http_client.py`
2. Write integration tests for server
3. Run full test suite: `pytest`
4. Type check: `mypy src/`
5. Lint: `ruff check src/`

### Phase 5: Documentation
1. Update `README.md` for Python installation
2. Update `CLAUDE.md` for Python development
3. Copy `context/` folder (API specs)
4. Create example config files

### Phase 6: Final Verification (before deleting C# code)
1. Run: `python -m uk_parliament_mcp`
2. Configure Claude Desktop
3. Test: `hello_parliament` tool
4. Test: `get_member_by_name` with "Keir Starmer"
5. Verify all 86 tools in tool list
6. Test a tool from each module
7. Compare Python output with C# output for same queries

### Phase 7: Cleanup (only after verification passes)
1. Delete C# artifacts (`OpenData.Mcp.Server/`, `*.sln`)
2. Remove any C#-specific files from `.gitignore`
3. Final commit with clean Python-only project

---

## 11. Files to Delete (C# Artifacts)

**IMPORTANT**: Only delete these files AFTER Phase 7 verification is complete. The C# code serves as the definitive reference during migration for:
- Exact API endpoints and query parameters
- Tool descriptions and parameter documentation
- Error handling patterns
- Response format specifications

After successful migration verification:

```
OpenData.Mcp.Server/           # Entire folder
├── OpenData.Mcp.Server.csproj
├── Program.cs
├── README.md
├── Tools/
│   ├── BaseTools.cs
│   ├── BillsTools.cs
│   ├── CommitteesTools.cs
│   ├── CommonsVotesTools.cs
│   ├── CoreTools.cs
│   ├── ErskineMayTools.cs
│   ├── HansardTools.cs
│   ├── InterestsTools.cs
│   ├── LordsVotesTools.cs
│   ├── MembersTools.cs
│   ├── NowTools.cs
│   ├── OralQuestionsTools.cs
│   ├── StatutoryInstrumentsTools.cs
│   ├── TreatiesTools.cs
│   └── WhatsOnTools.cs
└── Context/                   # Keep - copy to Python project

OpenDataMcpServer.sln          # Delete
```

---

## 12. Verification Checklist

- [ ] Server starts without errors: `python -m uk_parliament_mcp`
- [ ] All 86 tools registered (check tool list)
- [ ] `hello_parliament` returns system prompt
- [ ] `goodbye_parliament` returns goodbye prompt
- [ ] `get_member_by_name("Keir Starmer")` returns valid JSON
- [ ] `search_bills("climate")` returns valid JSON
- [ ] HTTP retry logic works (test with flaky endpoint)
- [ ] Error responses have correct format (`{url, error, statusCode}`)
- [ ] Claude Desktop configuration works
- [ ] All tests pass: `pytest`
- [ ] Type checking passes: `mypy src/`
- [ ] Linting passes: `ruff check src/`

---

## Appendix A: Key Differences from C# Implementation

| Aspect | C# | Python |
|--------|-----|--------|
| Tool Discovery | `[McpServerToolType]` + assembly scan | Explicit `register_tools(mcp)` |
| DI | Constructor injection | Module-level imports |
| Async HTTP | `HttpClient` | `httpx.AsyncClient` |
| Retry | Manual loop | `tenacity` or manual |
| Type System | Nullable `T?` | `T \| None` |
| Logging | `ILogger<T>` | `logging` module |
| Packages | NuGet | pip/uv |

---

## Appendix B: Helpful Commands

```bash
# Create virtual environment
uv venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# Install dependencies
uv pip install -e ".[dev]"

# Run server
python -m uk_parliament_mcp

# Run tests
pytest

# Type check
mypy src/

# Lint
ruff check src/
ruff format src/
```
