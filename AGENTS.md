# AGENTS.md - Operational Guide

Keep this file under 80 lines. It's loaded every iteration.

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
pytest tests/test_cli/              # Run CLI tests only
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

## CLI Commands

```bash
parliament --help                   # Show all command groups
parliament members --help           # Show member commands
parliament members search "Starmer" # Execute search
parliament composite mp-profile "Sunak" --pretty  # Pretty output
parliament bills search "Online Safety" --data-only | jq '.'  # Pipe to jq
```

## CLI Validation

```bash
# After CLI implementation
pip install -e .
parliament --help
parliament members search "Test" --pretty
```

## Project Notes

- Python 3.11+ required
- Tool descriptions use semantic format: `Action | Keywords | Use case | Returns`
- House IDs: 1 = Commons, 2 = Lords
- Date format: YYYY-MM-DD
- API base URLs in `src/uk_parliament_mcp/config.py`
- Test files mirror source structure: `tools/members.py` -> `test_tools/test_members.py`

## Key Files

- CLI specification: `specs/cli-spec.md`
- Implementation plan: `IMPLEMENTATION_PLAN.md`
- Project documentation: `CLAUDE.md`
