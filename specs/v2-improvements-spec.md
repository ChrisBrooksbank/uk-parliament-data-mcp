# UK Parliament MCP v2.0 Improvements Specification

## Overview

This specification covers the v2.0 improvements for the UK Parliament MCP Server, focusing on performance, consistency, discoverability, and new capabilities.

## User Stories

- As an AI assistant, I want consistent house parameters so that I don't need to remember which tools use integers vs strings
- As a developer, I want validated inputs so that errors are caught early with helpful messages
- As an AI assistant, I want cached reference data so that repeated calls are fast
- As an AI assistant, I want to compare MPs' voting records so that I can answer comparative questions
- As an AI assistant, I want to search across all data types so that I can quickly find relevant information

---

## Phase 1: Foundation (P1 Items)

### 1.1 Standardize House Parameter Type
**Files:** `validators.py`, all tools with house parameters

Create a normalizing helper that accepts both formats:
```python
def normalize_house(house: int | str) -> int:
    """Normalize house to integer format (1=Commons, 2=Lords)."""
    if isinstance(house, str):
        house_lower = house.lower()
        if house_lower == "commons":
            return 1
        elif house_lower == "lords":
            return 2
        raise ValueError(f"Invalid house string: {house}. Use 'Commons' or 'Lords'")
    if house not in (1, 2):
        raise ValueError(f"Invalid house ID: {house}. Use 1 (Commons) or 2 (Lords)")
    return house
```

Update these tools to use the normalizer:
- `members.py`: `parties_list_by_house()`, `search_members()`, `get_member_registered_interests()`, `get_member_voting()`
- `hansard.py`: `search_hansard()`
- `whatson.py`: `search_calendar()`, `get_non_sitting_days()`
- `bills.py`: `get_sittings()`

### 1.2 Enable Caching for Reference Data
**Files:** `tools/bills.py`, `tools/members.py`

Replace `get_result()` with `get_result_cached()` for these tools:
- [ ] `bill_types()` - cache_key: "bill_types"
- [ ] `bill_stages()` - cache_key: "bill_stages"
- [ ] `parties_list_by_house(house)` - cache_key: f"parties_{house}"
- [ ] `get_publication_types()` - cache_key: "publication_types"
- [ ] `get_answering_bodies()` - cache_key: "answering_bodies"

### 1.3 Add Input Validation
**Files:** `validators.py`, all tool modules

Expand `validators.py` with:
```python
def validate_date(date: str, param_name: str = "date") -> str:
    """Validate YYYY-MM-DD format."""

def validate_positive_int(value: int, param_name: str = "id") -> int:
    """Validate positive integer (for IDs)."""

def validate_pagination(skip: int, take: int) -> tuple[int, int]:
    """Validate skip >= 0 and 0 < take <= 100."""
```

Apply validation in tools with:
- Date parameters: `start_date`, `end_date`, `from_date`, `to_date`
- ID parameters: `member_id`, `bill_id`, `committee_id`, `division_id`
- Pagination: `skip`, `take`

---

## Phase 2: Discoverability (P2 Items)

### 2.1 Add Cross-References in Docstrings
**Files:** All tool modules

Add "See also" section to related tools. Examples:
- `get_member_by_name()` → See also: `get_member_by_id`, `get_members_biography`, `get_mp_profile`
- `search_bills()` → See also: `get_bill_by_id`, `get_bill_stages`, `get_bill_overview`
- `search_commons_divisions()` → See also: `get_commons_division_by_id`, `check_mp_vote`

### 2.2 Update Composite Tools with "Uses" Section
**File:** `tools/composite.py`

Add documentation showing which tools each composite calls:
```python
"""Get comprehensive MP profile...

Uses:
- get_member_by_name() - Find member ID
- get_members_biography() - Biography details
- get_member_registered_interests() - Financial interests
- get_member_voting() - Recent votes
"""
```

---

## Phase 3: New Capabilities (P2 Items)

### 3.1 Add Member Comparison Tool
**File:** `tools/composite.py`

```python
async def compare_mp_voting(
    mp1_name: str,
    mp2_name: str,
    topic: str | None = None
) -> str:
    """Compare voting patterns between two MPs | voting comparison, MP differences, voting record comparison | Use when comparing how two members voted on issues | Returns voting records for both MPs with overlap analysis"""
```

Implementation:
1. Search for both members in parallel
2. Get voting records for both
3. If topic provided, filter divisions by topic
4. Return comparison with: matching votes, opposing votes, abstentions

### 3.2 Add Aggregated Search Tool
**File:** `tools/composite.py`

```python
async def search_parliament(
    query: str,
    types: list[str] | None = None
) -> str:
    """Search across all Parliament data | universal search, find anything, cross-search | Use for broad searches across members, bills, committees, Hansard | Returns categorized results from multiple data sources"""
```

Implementation:
1. Default types: ["members", "bills", "committees", "hansard"]
2. Run searches in parallel using `asyncio.gather()`
3. Return aggregated results with source labels
4. Limit each type to top 5 results

### 3.3 Add Bill Sponsor Lookup
**File:** `tools/composite.py`

```python
async def get_bills_by_sponsor(member_name: str) -> str:
    """Find bills sponsored by a member | member bills, sponsored legislation, MP bills | Use to see what legislation a member has introduced | Returns list of bills with sponsor details"""
```

---

## Phase 4: Code Quality (P3 Items)

### 4.1 Standardize Docstring Format
**Files:** `oral_questions.py`, `erskine_may.py`, `interests.py`

Ensure all tools follow: `Action | Keywords | Use case | Returns`

### 4.2 Add Error Recovery Guidance
**File:** `tools/composite.py`

When no results found, return helpful suggestions:
```python
{
    "error": "No members found",
    "suggestions": [
        "Try searching by first name only",
        "Check spelling of the name",
        "Use get_member_by_id if you have the ID"
    ],
    "query": original_query
}
```

### 4.3 Consolidate Voting Modules (Optional)
**Files:** `commons_votes.py`, `lords_votes.py` → `votes.py`

Create shared implementation with house parameter. This is optional as it changes the API surface.

---

## Phase 5: Project Quality (P4 Items)

### 5.1 Add LICENSE File
**File:** Create `LICENSE`

MIT License with correct copyright year and author.

### 5.2 Add CHANGELOG
**File:** Create `CHANGELOG.md`

Document v1.0.0, v1.0.1, and upcoming v2.0.0 changes.

### 5.3 Add Pre-commit Hooks
**File:** Create `.pre-commit-config.yaml`

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.3.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
      - id: mypy
        additional_dependencies: [mcp, httpx]
```

---

## Acceptance Criteria

- [ ] All tests pass: `pytest`
- [ ] Type checking passes: `mypy src/`
- [ ] Linting passes: `ruff check src/`
- [ ] House parameter works with both int and string in all tools
- [ ] Cached tools respond faster on second call
- [ ] Input validation provides clear error messages
- [ ] New composite tools work correctly
- [ ] Docstrings have consistent format

## Out of Scope

- Breaking changes to existing tool signatures (except house parameter normalization)
- New Parliament API integrations
- Authentication/authorization features
- Rate limiting implementation
