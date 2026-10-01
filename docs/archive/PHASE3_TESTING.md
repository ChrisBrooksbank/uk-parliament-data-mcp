# Phase 3: Testing Improvements

Expand test coverage from 4 to 15+ test files.

## Current State

Only 4 test files exist:
- `tests/test_http_client.py` - HTTP client tests
- `tests/test_tools/test_core.py` - Guidance tools
- `tests/test_tools/test_composite.py` - Composite tools
- `tests/conftest.py` - Fixtures

**13 of 15 tool modules have zero test coverage.**

---

## 3.1 Add Members Module Tests

**New file:** `tests/test_tools/test_members.py`

```python
"""Tests for members tools."""
import pytest
from unittest.mock import patch, AsyncMock

# Test URL construction
@pytest.mark.asyncio
async def test_search_members_url():
    """Test search_members builds correct URL."""
    with patch('uk_parliament_mcp.http_client.get_result', new_callable=AsyncMock) as mock:
        mock.return_value = '{"url": "...", "data": "{}"}'
        from uk_parliament_mcp.tools.members import search_members
        # ... test implementation

@pytest.mark.asyncio
async def test_search_members_special_characters():
    """Test URL encoding of special characters."""
    # Test names like "O'Brien", spaces, etc.

@pytest.mark.asyncio
async def test_member_by_id_url():
    """Test member_by_id builds correct URL."""

@pytest.mark.asyncio
async def test_member_biography_url():
    """Test member_biography builds correct URL."""

# ... tests for all 26 member tools
```

**Coverage targets:**
- URL construction for all 26 tools
- Parameter filtering (None values excluded)
- Special character encoding (quotes, spaces, ampersands)
- Pagination parameters (skip, take)

---

## 3.2 Add Bills Module Tests

**New file:** `tests/test_tools/test_bills.py`

```python
"""Tests for bills tools."""
import pytest

@pytest.mark.asyncio
async def test_search_bills_url():
    """Test search_bills builds correct URL."""

@pytest.mark.asyncio
async def test_bill_by_id_url():
    """Test bill_by_id builds correct URL."""

@pytest.mark.asyncio
async def test_bill_stages_url():
    """Test bill_stages builds correct URL."""

@pytest.mark.asyncio
async def test_rss_feed_urls():
    """Test RSS feed URLs are correct."""

# ... tests for all 21 bill tools
```

**Coverage targets:**
- URL construction for all 21 tools
- RSS feed URL formats
- Pagination and filtering parameters

---

## 3.3 Add Votes Module Tests

**New files:**
- `tests/test_tools/test_commons_votes.py`
- `tests/test_tools/test_lords_votes.py`

```python
"""Tests for commons_votes tools."""
import pytest

@pytest.mark.asyncio
async def test_search_commons_divisions_url():
    """Test search URL construction."""

@pytest.mark.asyncio
async def test_commons_division_by_id_url():
    """Test division lookup URL."""

# ... tests for all 5 commons vote tools
```

```python
"""Tests for lords_votes tools."""
import pytest

@pytest.mark.asyncio
async def test_search_lords_divisions_url():
    """Test search URL construction."""

# ... tests for all 5 lords vote tools
```

---

## 3.4 Add Remaining Module Tests

**New files to create:**

| File | Module | Tools |
|------|--------|-------|
| `test_committees.py` | committees.py | 12 |
| `test_hansard.py` | hansard.py | 1 |
| `test_interests.py` | interests.py | 3 |
| `test_now.py` | now.py | 2 |
| `test_whatson.py` | whatson.py | 3 |
| `test_statutory_instruments.py` | statutory_instruments.py | 2 |
| `test_treaties.py` | treaties.py | 1 |
| `test_erskine_may.py` | erskine_may.py | 1 |
| `test_oral_questions.py` | oral_questions.py | 3 |

**Test template:**
```python
"""Tests for {module} tools."""
import pytest
from unittest.mock import patch, AsyncMock

@pytest.fixture
def mock_http():
    """Mock HTTP client."""
    with patch('uk_parliament_mcp.http_client.get_result', new_callable=AsyncMock) as mock:
        mock.return_value = '{"url": "test", "data": "{}"}'
        yield mock

@pytest.mark.asyncio
async def test_{tool_name}_url(mock_http):
    """Test {tool_name} builds correct URL."""
    # Call tool
    # Assert mock was called with expected URL
```

---

## 3.5 Add Coverage Configuration

**File:** `pyproject.toml`

Add to dev dependencies:
```toml
[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "pytest-httpx>=0.30.0",
    "pytest-cov>=4.1.0",  # ADD THIS
    "ruff>=0.3.0",
    "mypy>=1.8.0",
]
```

Update pytest config:
```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
addopts = "--cov=uk_parliament_mcp --cov-report=term-missing"
```

Add coverage config:
```toml
[tool.coverage.run]
source = ["src/uk_parliament_mcp"]
branch = true

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "if TYPE_CHECKING:",
    "raise NotImplementedError",
]
show_missing = true
```

---

## Test Structure After Implementation

```
tests/
├── conftest.py
├── test_http_client.py
└── test_tools/
    ├── __init__.py
    ├── test_core.py
    ├── test_composite.py
    ├── test_members.py          # NEW
    ├── test_bills.py            # NEW
    ├── test_commons_votes.py    # NEW
    ├── test_lords_votes.py      # NEW
    ├── test_committees.py       # NEW
    ├── test_hansard.py          # NEW
    ├── test_interests.py        # NEW
    ├── test_now.py              # NEW
    ├── test_whatson.py          # NEW
    ├── test_statutory_instruments.py  # NEW
    ├── test_treaties.py         # NEW
    ├── test_erskine_may.py      # NEW
    └── test_oral_questions.py   # NEW
```

---

## Checklist

- [ ] 3.1 Create test_members.py with 26 tool tests
- [ ] 3.2 Create test_bills.py with 21 tool tests
- [ ] 3.3 Create test_commons_votes.py with 5 tool tests
- [ ] 3.3 Create test_lords_votes.py with 5 tool tests
- [ ] 3.4 Create test_committees.py with 12 tool tests
- [ ] 3.4 Create test_hansard.py with 1 tool test
- [ ] 3.4 Create test_interests.py with 3 tool tests
- [ ] 3.4 Create test_now.py with 2 tool tests
- [ ] 3.4 Create test_whatson.py with 3 tool tests
- [ ] 3.4 Create test_statutory_instruments.py with 2 tool tests
- [ ] 3.4 Create test_treaties.py with 1 tool test
- [ ] 3.4 Create test_erskine_may.py with 1 tool test
- [ ] 3.4 Create test_oral_questions.py with 3 tool tests
- [ ] 3.5 Add pytest-cov to dev dependencies
- [ ] 3.5 Update pytest config with coverage

## Verification

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests with coverage
pytest --cov=uk_parliament_mcp --cov-report=term-missing

# Target: 80%+ coverage
```
