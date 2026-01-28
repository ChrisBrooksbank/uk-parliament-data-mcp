# AGENTS.md - Operational Reference

## Project: UK Parliament MCP Server (Python Migration)

### Quick Reference

```bash
# Create virtual environment
uv venv
.venv\Scripts\activate     # Windows
source .venv/bin/activate  # Linux/Mac

# Install dependencies
uv pip install -e ".[dev]"

# Run MCP server
python -m uk_parliament_mcp

# Run tests
pytest

# Type checking
mypy src/

# Linting
ruff check src/
ruff format src/

# All checks (must pass before commit)
pytest && mypy src/ && ruff check src/
```

### Project Structure

```
uk-parliament-mcp-lab/
├── specs/python-migration-spec.md    # Migration specification
├── src/uk_parliament_mcp/            # Python package
│   ├── __main__.py                   # Entry point
│   ├── server.py                     # FastMCP setup
│   ├── http_client.py                # HTTP with retry
│   └── tools/                        # 14 tool modules
├── tests/                            # pytest tests
├── context/                          # API spec JSONs
└── OpenData.Mcp.Server/              # C# reference (DO NOT DELETE)
```

### Key Conventions

- House IDs: 1 = Commons, 2 = Lords
- Date format: YYYY-MM-DD
- All tools are read-only and idempotent
- Tool response format: `{"url": "...", "data": "..."}` or `{"url": "...", "error": "...", "statusCode": N}`

### Tool Count Target

86 tools across 14 modules. Verify with:
```python
server = create_server()
assert len(list(server.list_tools())) == 86
```

### C# Reference

Keep `OpenData.Mcp.Server/` as reference during migration. Only delete after all 86 tools verified working.

### Commit Format

```
feat: Add {module} tools ({count} tools)
fix: Correct {issue} in {module}
test: Add tests for {module}
```
