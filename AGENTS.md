# AGENTS.md - Operational Guide

Keep this file under 60 lines. It's loaded every iteration.

## Build Commands

```bash
# Install dependencies (dev mode)
pip install -e ".[dev]"

# Run the MCP server
python -m uk_parliament_mcp
```

## Test Commands

```bash
pytest                              # Run all tests
pytest tests/test_tools/            # Run tool tests only
pytest --cov=uk_parliament_mcp      # Run with coverage
```

## Validation (run before committing)

```bash
ruff check src/                     # Lint check
ruff format --check src/            # Format check
mypy src/                           # Type check
pytest                              # Tests

# All at once:
ruff check src/ && ruff format --check src/ && mypy src/ && pytest
```

## Fixing Issues

```bash
ruff check src/ --fix               # Auto-fix lint issues
ruff format src/                    # Auto-format code
```

## Project Notes

- Python 3.11+ required
- Tool descriptions use semantic format: `Action | Keywords | Use case | Returns`
- House IDs: 1 = Commons, 2 = Lords
- Date format: YYYY-MM-DD
- API base URLs should be in `src/uk_parliament_mcp/config.py` (after Phase 2.1)
- Test files mirror source structure: `tools/members.py` -> `test_tools/test_members.py`

## Key Files

- `docs/IMPROVEMENT_PLAN.md` - Master improvement plan
- `docs/PHASE*.md` - Detailed phase specifications
- `IMPLEMENTATION_PLAN_IMPROVEMENTS.md` - Current task tracking
- `CLAUDE.md` - Project documentation for Claude Code
