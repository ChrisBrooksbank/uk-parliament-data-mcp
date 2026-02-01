# Phase 5: Architecture & CI/CD Improvements

Performance and CI/CD enhancements.

## 5.1 Add CI Code Coverage

**File:** `.github/workflows/ci.yml`

Add coverage reporting to CI:

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.11", "3.12"]

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
          cache: 'pip'  # ADD: pip caching

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e ".[dev]"

      - name: Lint with ruff
        run: |
          ruff check src/
          ruff format --check src/

      - name: Type check with mypy
        run: mypy src/

      - name: Run tests with coverage
        run: pytest --cov=uk_parliament_mcp --cov-report=xml --cov-report=term-missing

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v4
        with:
          files: ./coverage.xml
          fail_ci_if_error: false
        env:
          CODECOV_TOKEN: ${{ secrets.CODECOV_TOKEN }}
```

**Setup required:**
1. Create Codecov account and link repository
2. Add `CODECOV_TOKEN` to repository secrets
3. Add coverage badge to README (optional):
   ```markdown
   [![codecov](https://codecov.io/gh/ChrisBrooksbank/uk-parliament-mcp-lab/branch/main/graph/badge.svg)](https://codecov.io/gh/ChrisBrooksbank/uk-parliament-mcp-lab)
   ```

---

## 5.2 Add pip Caching

**File:** `.github/workflows/ci.yml`

Already included in 5.1 above. The key addition:

```yaml
- uses: actions/setup-python@v5
  with:
    python-version: ${{ matrix.python-version }}
    cache: 'pip'  # Caches pip packages
```

**Benefits:**
- Faster CI runs (skip downloading packages)
- Reduced load on PyPI
- More reliable builds

---

## 5.3 Add Optional Response Caching (Future)

**File:** `src/uk_parliament_mcp/http_client.py`

For frequently accessed reference data that rarely changes:

```python
from datetime import datetime, timedelta
from typing import TypedDict

class CacheEntry(TypedDict):
    data: str
    expires: datetime

# In-memory cache for reference data
_cache: dict[str, CacheEntry] = {}
CACHE_TTL = timedelta(minutes=15)

async def get_result_cached(url: str, cache_key: str | None = None) -> str:
    """
    Get result with optional caching for reference data.

    Args:
        url: API URL to fetch
        cache_key: Optional cache key. If None, no caching.

    Returns:
        JSON response string
    """
    key = cache_key or url

    # Check cache
    if key in _cache:
        entry = _cache[key]
        if datetime.now() < entry["expires"]:
            logger.debug("Cache hit for %s", key)
            return entry["data"]
        else:
            del _cache[key]

    # Fetch fresh data
    result = await get_result(url)

    # Cache if successful and cache_key provided
    if cache_key and '"error"' not in result:
        _cache[key] = {
            "data": result,
            "expires": datetime.now() + CACHE_TTL
        }
        logger.debug("Cached result for %s", key)

    return result

def clear_cache() -> None:
    """Clear all cached data."""
    _cache.clear()
```

**Good candidates for caching:**
- `bill_types()` - List of bill types (rarely changes)
- `bill_stages()` - List of bill stages (rarely changes)
- `get_departments()` - Government departments (rarely changes)
- `parties_list_by_house()` - Party lists (changes with elections)
- `get_committee_types()` - Committee type definitions

**Usage:**
```python
# In tools module
async def bill_types() -> str:
    """Get all bill types."""
    url = f"{BILLS_API_BASE}/BillTypes"
    return await get_result_cached(url, cache_key="bill_types")
```

**Benefits:**
- Faster repeated lookups
- Reduced API load
- Better user experience

**Caution:**
- Only cache truly static reference data
- Keep TTL short (15 min) to avoid stale data
- Never cache user-specific or time-sensitive queries

---

## 5.4 (Optional) Add Pre-commit Hooks

**New file:** `.pre-commit-config.yaml`

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
        additional_dependencies: [types-all]
        args: [--strict]
```

**Setup:**
```bash
pip install pre-commit
pre-commit install
```

**Benefits:**
- Catches issues before commit
- Consistent code style
- Reduces CI failures

---

## 5.5 (Optional) Add Dependabot

**New file:** `.github/dependabot.yml`

```yaml
version: 2
updates:
  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 5

  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
```

**Benefits:**
- Automatic dependency updates
- Security patches applied quickly
- Reduces maintenance burden

---

## Checklist

- [ ] 5.1 Update ci.yml with coverage reporting
- [ ] 5.1 Set up Codecov (optional)
- [ ] 5.2 Add pip caching to ci.yml
- [ ] 5.3 (Future) Implement response caching
- [ ] 5.4 (Optional) Add pre-commit hooks
- [ ] 5.5 (Optional) Add Dependabot

## Verification

```bash
# Test CI locally with act (optional)
act -j test

# Verify caching works
# Run workflow twice, second should be faster

# Check coverage report
pytest --cov=uk_parliament_mcp --cov-report=html
# Open htmlcov/index.html
```

---

## Implementation Priority

1. **5.1 & 5.2** - CI improvements (do together)
2. **5.5** - Dependabot (quick setup)
3. **5.4** - Pre-commit hooks (developer convenience)
4. **5.3** - Response caching (performance, but requires careful consideration)
