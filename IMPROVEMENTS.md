# UK Parliament MCP Server - Recommended Improvements

## Summary

After analyzing the codebase (92 tools, 15 modules, ~3000 lines), I've identified improvements across four categories. The project is well-structured with excellent test coverage (1.43:1 ratio) and strong typing (MyPy strict). Main opportunities are in consistency, performance, and expanded capabilities.

---

## 1. PERFORMANCE

### 1.1 Enable Caching for Reference Data
**Impact: High | Effort: Low**

The `get_result_cached()` function exists in `http_client.py` but is unused. Reference data that rarely changes should use it:

- `bill_types()` - Bill type definitions
- `bill_stages()` - Stage definitions
- `parties_list_by_house()` - Party listings
- `get_publication_types()` - Publication type listings
- `get_answering_bodies()` - Government department listings

**Files:** `tools/bills.py`, `tools/members.py`

### 1.2 Add Connection Pooling Limits
**Impact: Medium | Effort: Low**

The global httpx client uses default limits. For high-volume usage, explicitly configure:
```python
httpx.AsyncClient(limits=httpx.Limits(max_connections=100, max_keepalive_connections=20))
```

**File:** `http_client.py:93-97`

### 1.3 Per-Endpoint Timeout Configuration
**Impact: Low | Effort: Medium**

Current 30-second global timeout may be excessive for fast endpoints and insufficient for slow ones. Consider endpoint-specific timeouts.

---

## 2. DISCOVERABILITY

### 2.1 Add Cross-References in Tool Docstrings
**Impact: High | Effort: Medium**

Tool docstrings should reference related tools. Example:
```python
"""Search for MPs... | See also: get_member_by_id, get_member_biography"""
```

**Files:** All tool modules in `tools/`

### 2.2 Add "See Also" Section to Composite Tools
**Impact: Medium | Effort: Low**

Composite tools like `get_mp_profile()` should list the underlying tools they call, helping users understand they can call lower-level tools directly when needed.

**File:** `tools/composite.py`

### 2.3 Standardize All Tool Docstrings to 4-Part Format
**Impact: Medium | Effort: Medium**

Most tools use the semantic format `Action | Keywords | Use case | Returns`, but some in smaller modules don't:

- `tools/oral_questions.py` - Needs reformatting
- `tools/erskine_may.py` - Needs reformatting
- `tools/interests.py` - Partially formatted

---

## 3. EASE OF USE

### 3.1 Standardize House Parameter Type
**Impact: High | Effort: Medium**

Current inconsistency causes confusion:
- `int` (1=Commons, 2=Lords): `members.py`, `hansard.py`, `commons_votes.py`
- `str` ("Commons"/"Lords"): `whatson.py`, `bills.py:get_sittings()`

**Recommendation:** Accept both types in all tools using a normalizing helper:
```python
def normalize_house(house: int | str) -> int:
    if isinstance(house, str):
        return 1 if house.lower() == "commons" else 2
    return house
```

**Files:** All tools with house parameters

### 3.2 Add Input Validation to All Tools
**Impact: High | Effort: Medium**

`validators.py` exists but is barely used. Add validation for:
- Date format (YYYY-MM-DD)
- House IDs (1 or 2)
- Member IDs, Bill IDs (positive integers)
- Pagination (skip >= 0, take > 0)

**File:** `validators.py` + all tool modules

### 3.3 Consolidate Commons/Lords Voting Modules
**Impact: Medium | Effort: Medium**

`commons_votes.py` and `lords_votes.py` are 95% identical (5 tools each with same logic). Create a generic voting module with house parameter:

```python
def _create_voting_tools(mcp: FastMCP, house: int, api_base: str) -> None:
    # Generic implementation for both houses
```

**Files:** `tools/commons_votes.py`, `tools/lords_votes.py` → `tools/votes.py`

### 3.4 Add Error Recovery Guidance
**Impact: Medium | Effort: Low**

When searches return no results, include suggestions in composite tool responses:
- "No members found. Try searching by first name only, or check spelling."
- "No divisions found. Try broader date range or different search terms."

**File:** `tools/composite.py`

---

## 4. CAPABILITIES

### 4.1 Add Member Comparison Tool
**Impact: High | Effort: Medium**

New composite tool to compare two MPs:
```python
async def compare_mp_voting(mp1_name: str, mp2_name: str, topic: str | None = None) -> str:
    """Compare voting patterns between two MPs on a topic."""
```

**File:** `tools/composite.py`

### 4.2 Add Bill Sponsor Lookup
**Impact: Medium | Effort: Low**

New tool to find all bills sponsored by a specific member:
```python
async def get_bills_by_sponsor(member_name: str) -> str:
    """Find all bills sponsored or co-sponsored by a member."""
```

**File:** `tools/composite.py`

### 4.3 Add Committee-Bill Cross-Reference
**Impact: Medium | Effort: Medium**

Tool to find which committees examined a bill and vice versa:
```python
async def get_committees_for_bill(bill_id: int) -> str:
async def get_bills_examined_by_committee(committee_id: int) -> str:
```

**File:** `tools/composite.py`

### 4.4 Add Aggregated Search Tool
**Impact: High | Effort: Medium**

Single search across multiple data types:
```python
async def search_parliament(query: str, types: list[str] | None = None) -> str:
    """Search across members, bills, committees, and Hansard."""
```

**File:** `tools/composite.py`

---

## 5. PROJECT QUALITY

### 5.1 Add LICENSE File
**Impact: Low | Effort: Trivial**

`pyproject.toml` declares MIT but no LICENSE file exists.

**File:** Create `LICENSE`

### 5.2 Add CHANGELOG
**Impact: Medium | Effort: Low**

Document changes between versions for users upgrading.

**File:** Create `CHANGELOG.md`

### 5.3 Add Pre-commit Hooks
**Impact: Medium | Effort: Low**

Automate ruff/mypy before commits:
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    hooks: [ruff, ruff-format]
```

**File:** Create `.pre-commit-config.yaml`

### 5.4 Make Codecov Required in CI
**Impact: Low | Effort: Trivial**

Change `fail_ci_if_error: false` to `true` in CI workflow.

**File:** `.github/workflows/ci.yml:45`

---

## Priority Summary

| Priority | Item | Impact | Effort |
|----------|------|--------|--------|
| **P1** | 3.1 Standardize house parameter | High | Medium |
| **P1** | 1.1 Enable caching for reference data | High | Low |
| **P1** | 3.2 Add input validation | High | Medium |
| **P2** | 2.1 Add cross-references in docstrings | High | Medium |
| **P2** | 4.4 Aggregated search tool | High | Medium |
| **P2** | 4.1 Member comparison tool | High | Medium |
| **P2** | 3.3 Consolidate voting modules | Medium | Medium |
| **P3** | 2.3 Standardize docstring format | Medium | Medium |
| **P3** | 3.4 Error recovery guidance | Medium | Low |
| **P3** | 5.3 Pre-commit hooks | Medium | Low |
| **P4** | 5.1 LICENSE file | Low | Trivial |
| **P4** | 5.2 CHANGELOG | Medium | Low |
