# UK Parliament MCP - Improvement Plan

A detailed plan for code quality improvements and README.md enhancements.

---

## Overview

This plan addresses improvements across 5 areas:
1. **Quick Wins** - Low effort, immediate value
2. **Code Quality** - Maintainability and consistency
3. **Testing** - Expand coverage from 3 to 15+ test files
4. **Documentation** - README restructuring and new docs
5. **Architecture** - Performance and CI/CD improvements

---

## Phase 1: Quick Wins

### 1.1 Add README Badges
**File:** `README.md` (line 1)

Add after title:
```markdown
[![PyPI version](https://badge.fury.io/py/uk-parliament-mcp.svg)](https://badge.fury.io/py/uk-parliament-mcp)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![CI](https://github.com/ChrisBrooksbank/uk-parliament-mcp-lab/actions/workflows/ci.yml/badge.svg)](https://github.com/ChrisBrooksbank/uk-parliament-mcp-lab/actions/workflows/ci.yml)
```

### 1.2 Add README Table of Contents
**File:** `README.md` (after badges)

The README is 325 lines with no navigation. Add TOC linking to major sections.

### 1.3 Verify Tool Count Consistency
**Files:** `README.md`, `CLAUDE.md`, `src/uk_parliament_mcp/tools/core.py`

README says "94 tools". Verify actual count and ensure consistency across all docs.

### 1.4 Remove Unused Import
**File:** `src/uk_parliament_mcp/tools/commons_votes.py`

Remove `from urllib.parse import quote` if unused (verify first).

---

## Phase 2: Code Quality Improvements

### 2.1 Centralize API Base URLs
**New file:** `src/uk_parliament_mcp/config.py`

Currently API bases are defined in 15+ files:
- `composite.py` lines 14-18
- `members.py`, `bills.py`, `committees.py`, etc.

Create centralized config:
```python
"""Centralized configuration for UK Parliament MCP Server."""

# API Base URLs
MEMBERS_API_BASE = "https://members-api.parliament.uk/api"
BILLS_API_BASE = "https://bills-api.parliament.uk/api/v1"
COMMONS_VOTES_API_BASE = "http://commonsvotes-api.parliament.uk/data"
LORDS_VOTES_API_BASE = "https://lordsvotes-api.parliament.uk/data"
COMMITTEES_API_BASE = "https://committees-api.parliament.uk/api"
HANSARD_API_BASE = "https://hansard-api.parliament.uk/api/v1"
INTERESTS_API_BASE = "https://interests-api.parliament.uk/api/v1"
NOW_API_BASE = "https://now-api.parliament.uk/api"
WHATSON_API_BASE = "https://whatson-api.parliament.uk/api"
STATUTORY_INSTRUMENTS_API_BASE = "https://statutoryinstruments-api.parliament.uk/api/v1"
TREATIES_API_BASE = "https://treaties-api.parliament.uk/api"
ERSKINE_MAY_API_BASE = "https://erskinemay-api.parliament.uk/api"
ORAL_QUESTIONS_API_BASE = "https://oralquestionsandmotions-api.parliament.uk/api/v1"
```

Update all tool modules to import from config.

### 2.2 Add Response TypedDict
**File:** `src/uk_parliament_mcp/http_client.py`

Add type definitions for response format:
```python
from typing import TypedDict

class SuccessResponse(TypedDict):
    url: str
    data: str

class ErrorResponse(TypedDict):
    url: str
    error: str
    statusCode: int | None
```

### 2.3 Fix Unsafe Dict Access
**File:** `src/uk_parliament_mcp/tools/composite.py` (line 78)

Current:
```python
house = 1 if basic_info.get("latestHouseMembership", {}).get("house") == 1 else 2
```

Improved:
```python
latest_membership = basic_info.get("latestHouseMembership") or {}
house = latest_membership.get("house", 1)
```

### 2.4 Add Parameter Validators (Optional)
**New file:** `src/uk_parliament_mcp/validators.py`

```python
"""Parameter validation helpers."""
import re

def validate_house_id(house: int) -> int:
    """Validate house ID is 1 (Commons) or 2 (Lords)."""
    if house not in (1, 2):
        raise ValueError(f"House must be 1 or 2, got {house}")
    return house

def validate_date(date_str: str) -> str:
    """Validate date is YYYY-MM-DD format."""
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", date_str):
        raise ValueError(f"Date must be YYYY-MM-DD, got {date_str}")
    return date_str
```

### 2.5 Remove Unused tenacity Dependency
**File:** `pyproject.toml` (line 23)

`tenacity>=8.2.0` is listed but `http_client.py` uses manual retry logic. Either:
- Remove from dependencies (simpler)
- Refactor to use tenacity (cleaner but more work)

---

## Phase 3: Testing Improvements

### Current State
Only 4 test files exist:
- `tests/test_http_client.py` (HTTP client tests)
- `tests/test_tools/test_core.py` (guidance tools)
- `tests/test_tools/test_composite.py` (composite tools)
- `tests/conftest.py` (fixtures)

**13 of 15 tool modules have zero test coverage.**

### 3.1 Add Members Module Tests
**New file:** `tests/test_tools/test_members.py`

Test coverage:
- URL construction for all 26 tools
- Parameter filtering (None values)
- Special character encoding

### 3.2 Add Bills Module Tests
**New file:** `tests/test_tools/test_bills.py`

Test coverage:
- URL construction for all 21 tools
- Pagination parameters
- RSS feed URLs

### 3.3 Add Votes Module Tests
**New files:**
- `tests/test_tools/test_commons_votes.py`
- `tests/test_tools/test_lords_votes.py`

### 3.4 Add Remaining Module Tests
**New files:**
- `tests/test_tools/test_committees.py`
- `tests/test_tools/test_hansard.py`
- `tests/test_tools/test_interests.py`
- `tests/test_tools/test_now.py`
- `tests/test_tools/test_whatson.py`
- `tests/test_tools/test_statutory_instruments.py`
- `tests/test_tools/test_treaties.py`
- `tests/test_tools/test_erskine_may.py`
- `tests/test_tools/test_oral_questions.py`

### 3.5 Add Coverage Configuration
**File:** `pyproject.toml`

Add to dev dependencies:
```toml
"pytest-cov>=4.1.0",
```

Add pytest config:
```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
addopts = "--cov=uk_parliament_mcp --cov-report=term-missing"
```

---

## Phase 4: Documentation Improvements

### 4.1 Restructure Example Prompts
**File:** `README.md` (lines 226-318)

Currently 80+ example prompts are overwhelming. Organize into collapsible sections:

```markdown
## Example Prompts

<details>
<summary>Live Parliamentary Activity (3 examples)</summary>

- What is happening now in both Houses?
- What's currently happening in the House of Commons?

</details>

<details>
<summary>Members of Parliament (14 examples)</summary>

...

</details>
```

### 4.2 Add Configuration Decision Matrix
**File:** `README.md` (before config examples)

```markdown
### Which Configuration Should I Use?

| Method | Best For | Pros | Cons |
|--------|----------|------|------|
| `uvx uk-parliament-mcp` | Most users | No install, always latest | Requires uvx |
| `pip install` | Production | Stable, version locked | Requires pip |
| Local development | Contributors | Full source access | Complex setup |
```

### 4.3 Add Composite Tools to README
**File:** `README.md`

Currently composite tools (`get_mp_profile`, `check_mp_vote`, `get_bill_overview`, `get_committee_summary`) are only documented in CLAUDE.md. Add quick reference to README.

### 4.4 Create CHANGELOG.md
**New file:** `CHANGELOG.md`

```markdown
# Changelog

## [1.0.1] - 2024-XX-XX

### Added
- Server-level instructions for automatic context
- Composite tools documentation

## [1.0.0] - 2024-XX-XX

### Added
- Initial release with 94 tools
- Support for 15 Parliament APIs
```

### 4.5 Create CONTRIBUTING.md
**New file:** `CONTRIBUTING.md`

Include:
- Development setup
- Code style (ruff, mypy)
- How to add new tools
- Testing requirements
- PR process

---

## Phase 5: Architecture & CI/CD

### 5.1 Add CI Code Coverage
**File:** `.github/workflows/ci.yml`

```yaml
- name: Run tests with coverage
  run: pytest --cov=uk_parliament_mcp --cov-report=xml

- name: Upload coverage
  uses: codecov/codecov-action@v4
```

### 5.2 Add pip Caching
**File:** `.github/workflows/ci.yml`

```yaml
- uses: actions/setup-python@v5
  with:
    python-version: ${{ matrix.python-version }}
    cache: 'pip'
```

### 5.3 Add Optional Response Caching (Future)
**File:** `src/uk_parliament_mcp/http_client.py`

For frequently accessed reference data:
```python
_cache: dict[str, tuple[str, datetime]] = {}
CACHE_TTL = timedelta(minutes=15)

async def get_result_cached(url: str, cache_key: str | None = None) -> str:
    # Implementation for caching static reference data
```

Use for: `bill_types()`, `bill_stages()`, `get_departments()`, `parties_list_by_house()`

---

## Implementation Order

```
Phase 1 (Quick Wins) ─────────────────── Start here
  ├── 1.1 Add badges
  ├── 1.2 Add TOC
  ├── 1.3 Verify tool count
  └── 1.4 Remove unused import

Phase 2 (Code Quality) ───────────────── After Phase 1
  ├── 2.1 Centralize URLs ─────┐
  ├── 2.2 Add TypedDict        │
  ├── 2.3 Fix unsafe dict      │
  ├── 2.4 Add validators       │
  └── 2.5 Remove tenacity      │
                               │
Phase 3 (Testing) ─────────────┘─────── After 2.1
  ├── 3.1-3.4 Add module tests
  └── 3.5 Coverage config

Phase 4 (Documentation) ──────────────── Parallel with 2-3
  ├── 4.1 Restructure prompts
  ├── 4.2 Decision matrix
  ├── 4.3 Composite tools to README
  ├── 4.4 CHANGELOG.md
  └── 4.5 CONTRIBUTING.md

Phase 5 (Architecture) ───────────────── After Phase 2-3
  ├── 5.1 CI coverage
  ├── 5.2 pip caching
  └── 5.3 Response caching (optional)
```

---

## Critical Files

| File | Changes |
|------|---------|
| `README.md` | Badges, TOC, restructure prompts, add composite tools |
| `CLAUDE.md` | Verify tool count consistency |
| `src/uk_parliament_mcp/config.py` | **New** - Centralize API URLs |
| `src/uk_parliament_mcp/http_client.py` | Add TypedDict |
| `src/uk_parliament_mcp/tools/composite.py` | Fix unsafe dict access |
| `pyproject.toml` | Remove tenacity, add pytest-cov |
| `.github/workflows/ci.yml` | Add coverage, pip caching |
| `tests/test_tools/*.py` | **New** - Add 11 test files |
| `CHANGELOG.md` | **New** |
| `CONTRIBUTING.md` | **New** |

---

## Verification

After implementation:

1. **Run tests:** `pytest --cov=uk_parliament_mcp`
2. **Type check:** `mypy src/`
3. **Lint:** `ruff check src/ && ruff format --check src/`
4. **Manual test:** Start server with `python -m uk_parliament_mcp` and verify tools work
5. **Documentation review:** Check README renders correctly on GitHub
