# Phase 4: Documentation Improvements

README restructuring and new documentation files.

## 4.1 Restructure Example Prompts

**File:** `README.md` (lines 226-318)

Currently 80+ example prompts in a flat list are overwhelming. Organize into collapsible sections:

```markdown
## Example Prompts

<details>
<summary><strong>Live Parliamentary Activity</strong> (3 examples)</summary>

- What is happening now in both Houses?
- What's currently happening in the House of Commons?
- What's currently happening in the House of Lords?

</details>

<details>
<summary><strong>Members of Parliament</strong> (14 examples)</summary>

- Show me the interests of Sir Keir Starmer
- Who is Boris Johnson?
- Who is the member with ID 1471?
- Get the biography of member 172
- Show me contact details for member 4129
- What are the registered interests of member 3743?
- Show recent contributions from member 172
- What is the Commons voting record for member 4129?
- What is the Lords voting record for member 3743?
- Show the professional experience of member 1471
- What policy areas does member 172 focus on?
- Show early day motions submitted by member 1471
- Get the constituency election results for member 4129
- Show me the portrait and thumbnail images for member 172

</details>

<details>
<summary><strong>Bills and Legislation</strong> (14 examples)</summary>

- What recent bills are about fishing?
- What bills were updated recently?
- Show me details of bill 425
- What stages has bill 425 been through?
- What amendments were proposed for bill 425 at stage 15?
- Show me amendment 1234 for bill 425 stage 15
- What publications exist for bill 425?
- What news articles are there about bill 425?
- Show me all bill types available
- What are the different stages a bill can go through?
- Search for bills containing the word "environment"
- Get the RSS feed for all bills
- Get the RSS feed for public bills only
- Get the RSS feed for bill 425

</details>

<details>
<summary><strong>Voting and Divisions</strong> (6 examples)</summary>

- Search Commons Divisions for the keyword "refugee"
- Show details of Commons division 1234
- Show details of Lords division 5678
- Get Commons divisions grouped by party for keyword "climate"
- Get Lords divisions grouped by party for member 3743
- How many divisions match the search term "brexit"?

</details>

<details>
<summary><strong>Committees and Inquiries</strong> (9 examples)</summary>

- Which committees are focused on women's issues?
- List committee meetings scheduled for November 2024
- Show me details of committee 789
- What events has committee 789 held?
- Who are the members of committee 789?
- Search for committee publications about healthcare
- Show me written evidence submitted to committee 789
- Show me oral evidence from committee 789 hearings
- What are all the committee types?

</details>

<details>
<summary><strong>Parliamentary Procedures</strong> (9 examples)</summary>

- Search Erskine May for references to the Mace
- Show oral question times for questions tabled in November 2024
- Search Hansard for contributions on Brexit from November 2024
- What government departments exist?
- What are the answering bodies in Parliament?
- What parties are represented in the House of Commons?
- What parties are represented in the House of Lords?
- Show parliamentary calendar events for Commons in December 2024
- When is Parliament not sitting in January 2025?

</details>

<details>
<summary><strong>Constituencies and Elections</strong> (3 examples)</summary>

- List all UK constituencies
- Show the election results for constituency 4359
- Search for constituencies containing "london"

</details>

<details>
<summary><strong>Transparency and Interests</strong> (4 examples)</summary>

- List all categories of members' interests
- Get published registers of interests
- Show staff interests for Lords members
- Search the register of interests for member 1471

</details>

<details>
<summary><strong>Official Documents and Publications</strong> (5 examples)</summary>

- Are there any statutory instruments about harbours?
- Search Acts of Parliament that mention roads
- What treaties involve Spain?
- What publication types are available for bills?
- Show me document 123 from publication 456

</details>

<details>
<summary><strong>Advanced Queries</strong> (5 examples)</summary>

- Show the full data from this pasted API result: {PasteApiResultHere}
- Show me the JSON returned from the last MCP call
- Show me the API URL you just used
- Search for bills sponsored by member 172 from the Environment department
- Find all committee meetings about climate change between November and December 2024

</details>
```

**Benefits:**
- Easier to scan
- Users find relevant examples faster
- Page loads feel lighter

---

## 4.2 Add Configuration Decision Matrix

**File:** `README.md` (before configuration examples)

Add this section to help users choose:

```markdown
### Which Configuration Should I Use?

| Method | Best For | Pros | Cons |
|--------|----------|------|------|
| `uvx uk-parliament-mcp` | Most users | No install needed, always latest version | Requires uvx installed |
| `pip install uk-parliament-mcp` | Production use | Stable, version locked | Requires pip, manual updates |
| Local development install | Contributors | Full source access, can modify | More complex setup |

**Quick recommendation:**
- **New users:** Use `uvx` method
- **Developers:** Use local install
- **Production deployments:** Use `pip install` with pinned version
```

---

## 4.3 Add Composite Tools to README

**File:** `README.md` (new section after "What Can I Ask?")

Currently composite tools are only documented in CLAUDE.md. Add to README:

```markdown
## Power Tools

These high-level tools combine multiple API calls for common research tasks:

| Tool | What it does |
|------|--------------|
| `get_mp_profile(name)` | Complete MP/Lord profile: bio, interests, voting record |
| `check_mp_vote(mp_name, topic)` | How an MP voted on a specific topic |
| `get_bill_overview(search_term)` | Full bill info: details, stages, publications |
| `get_committee_summary(topic)` | Committee overview: evidence, publications |

**Example:**
```
Tell me everything about Keir Starmer
```
The AI will use `get_mp_profile` to fetch biography, registered interests, and voting history in a single efficient call.
```

---

## 4.4 Create CHANGELOG.md

**New file:** `CHANGELOG.md`

```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Centralized API configuration
- Parameter validators
- Expanded test coverage

### Changed
- Restructured README with collapsible sections

### Removed
- Unused tenacity dependency

## [1.0.1] - 2024-XX-XX

### Added
- Server-level instructions for automatic context
- Composite tools documentation in CLAUDE.md

### Fixed
- Documentation clarity improvements

## [1.0.0] - 2024-XX-XX

### Added
- Initial release
- 94 tools covering 15 Parliament APIs
- Support for Claude Desktop and VS Code
- Composite tools for common workflows
- Agent guidance system with `/parliament` prompt
```

---

## 4.5 Create CONTRIBUTING.md

**New file:** `CONTRIBUTING.md`

```markdown
# Contributing to UK Parliament MCP

Thank you for your interest in contributing! This document provides guidelines and instructions.

## Development Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/ChrisBrooksbank/uk-parliament-mcp-lab.git
   cd uk-parliament-mcp-lab
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Linux/Mac
   .venv\Scripts\activate     # Windows
   ```

3. **Install with dev dependencies:**
   ```bash
   pip install -e ".[dev]"
   ```

## Code Style

We use automated tools to maintain consistency:

- **Ruff** for linting and formatting
- **MyPy** for type checking

Run before committing:
```bash
ruff check src/
ruff format src/
mypy src/
```

## Adding New Tools

1. Create or update a module in `src/uk_parliament_mcp/tools/`
2. Follow the established pattern:

```python
"""Description of API tools."""
from mcp.server.fastmcp import FastMCP
from uk_parliament_mcp.config import API_BASE
from uk_parliament_mcp.http_client import build_url, get_result

def register_tools(mcp: FastMCP) -> None:
    """Register tools with the MCP server."""

    @mcp.tool()
    async def my_new_tool(param: str) -> str:
        """Action | keywords | Use case | Returns format

        Args:
            param: Description.

        Returns:
            What is returned.
        """
        url = f"{API_BASE}/endpoint?param={param}"
        return await get_result(url)
```

3. Register in `server.py`:
```python
from uk_parliament_mcp.tools import my_module
my_module.register_tools(mcp)
```

4. Add tests in `tests/test_tools/test_my_module.py`

5. Update documentation in `CLAUDE.md`

## Testing

Run the test suite:
```bash
pytest
```

With coverage:
```bash
pytest --cov=uk_parliament_mcp --cov-report=term-missing
```

**Requirements:**
- All new tools must have tests
- Tests should verify URL construction
- Target 80%+ coverage

## Pull Request Process

1. Create a feature branch from `main`
2. Make your changes
3. Ensure all checks pass:
   ```bash
   ruff check src/
   ruff format --check src/
   mypy src/
   pytest
   ```
4. Update documentation if needed
5. Submit PR with clear description

## Reporting Issues

Please include:
- Python version
- OS and version
- Steps to reproduce
- Expected vs actual behavior
- Error messages if applicable

## Questions?

Open an issue with the "question" label.
```

---

## Checklist

- [ ] 4.1 Restructure example prompts into collapsible sections
- [ ] 4.2 Add configuration decision matrix
- [ ] 4.3 Add composite tools section to README
- [ ] 4.4 Create CHANGELOG.md
- [ ] 4.5 Create CONTRIBUTING.md

## Verification

- Preview README.md on GitHub to check rendering
- Verify all links work
- Check collapsible sections expand/collapse properly
