# Phase 2: Code Quality Improvements

Maintainability and consistency improvements.

## 2.1 Centralize API Base URLs

**New file:** `src/uk_parliament_mcp/config.py`

Currently API bases are scattered across 15+ files. Centralize them:

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

# Common constants
HOUSE_COMMONS = 1
HOUSE_LORDS = 2
```

**Files to update:**
- `composite.py` - remove lines 14-18, import from config
- `members.py` - update MEMBERS_API_BASE import
- `bills.py` - update BILLS_API_BASE import
- `committees.py` - update COMMITTEES_API_BASE import
- `commons_votes.py` - update COMMONS_VOTES_API_BASE import
- `lords_votes.py` - update LORDS_VOTES_API_BASE import
- `hansard.py` - update HANSARD_API_BASE import
- `interests.py` - update INTERESTS_API_BASE import
- `now.py` - update NOW_API_BASE import
- `whatson.py` - update WHATSON_API_BASE import
- `statutory_instruments.py` - update STATUTORY_INSTRUMENTS_API_BASE import
- `treaties.py` - update TREATIES_API_BASE import
- `erskine_may.py` - update ERSKINE_MAY_API_BASE import
- `oral_questions.py` - update ORAL_QUESTIONS_API_BASE import

**Benefits:**
- Single source of truth for API URLs
- Easier to update if APIs change
- Consistent naming across modules

---

## 2.2 Add Response TypedDict

**File:** `src/uk_parliament_mcp/http_client.py`

Add type definitions for the response format:

```python
from typing import TypedDict, NotRequired

class SuccessResponse(TypedDict):
    url: str
    data: str

class ErrorResponse(TypedDict):
    url: str
    error: str
    statusCode: NotRequired[int]

# Union type for return values
APIResponse = SuccessResponse | ErrorResponse
```

**Benefits:**
- Better IDE support
- Clearer API contracts
- Helps catch type errors

---

## 2.3 Fix Unsafe Dict Access

**File:** `src/uk_parliament_mcp/tools/composite.py` (line 78)

**Current (fragile):**
```python
house = 1 if basic_info.get("latestHouseMembership", {}).get("house") == 1 else 2
```

**Problem:** If `latestHouseMembership` is `None` (not missing), `.get()` on `None` fails.

**Improved:**
```python
latest_membership = basic_info.get("latestHouseMembership") or {}
house = latest_membership.get("house", 1)
```

**Why:** Handles both missing key AND explicit `None` value.

---

## 2.4 Add Parameter Validators (Optional)

**New file:** `src/uk_parliament_mcp/validators.py`

```python
"""Parameter validation helpers."""
import re
from typing import Literal

HouseId = Literal[1, 2]

def validate_house_id(house: int) -> HouseId:
    """Validate house ID is 1 (Commons) or 2 (Lords).

    Args:
        house: House identifier to validate

    Returns:
        Validated house ID

    Raises:
        ValueError: If house is not 1 or 2
    """
    if house not in (1, 2):
        raise ValueError(f"House must be 1 (Commons) or 2 (Lords), got {house}")
    return house  # type: ignore[return-value]

def validate_date(date_str: str) -> str:
    """Validate date is YYYY-MM-DD format.

    Args:
        date_str: Date string to validate

    Returns:
        Validated date string

    Raises:
        ValueError: If date format is invalid
    """
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", date_str):
        raise ValueError(f"Date must be YYYY-MM-DD format, got {date_str}")
    return date_str

def validate_positive_int(value: int, name: str) -> int:
    """Validate integer is positive.

    Args:
        value: Integer to validate
        name: Parameter name for error message

    Returns:
        Validated integer

    Raises:
        ValueError: If value is not positive
    """
    if value < 1:
        raise ValueError(f"{name} must be positive, got {value}")
    return value
```

**Usage in tools:**
```python
from uk_parliament_mcp.validators import validate_house_id, validate_date

async def some_tool(house: int, date: str) -> str:
    house = validate_house_id(house)
    date = validate_date(date)
    # ... rest of implementation
```

**Benefits:**
- Consistent validation across tools
- Clear error messages for users
- Type narrowing for mypy

---

## 2.5 Remove Unused tenacity Dependency

**File:** `pyproject.toml` (line 23)

`tenacity>=8.2.0` is listed but `http_client.py` uses manual retry logic.

**Option A: Remove (simpler)**
```diff
dependencies = [
    "mcp>=1.0.0",
    "httpx>=0.27.0",
-   "tenacity>=8.2.0",
]
```

**Option B: Use tenacity (cleaner retry logic)**
```python
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError))
)
async def get_result(self, url: str) -> str:
    # ... implementation
```

**Recommendation:** Option A (remove) since manual retry works fine and reduces dependencies.

---

## Checklist

- [ ] 2.1 Create `config.py` with centralized URLs
- [ ] 2.1 Update all tool modules to import from config
- [ ] 2.2 Add TypedDict to http_client.py
- [ ] 2.3 Fix unsafe dict access in composite.py
- [ ] 2.4 (Optional) Add validators.py
- [ ] 2.5 Remove tenacity from pyproject.toml

## Verification

```bash
# Type check
mypy src/

# Lint
ruff check src/

# Run tests to ensure nothing broke
pytest
```
