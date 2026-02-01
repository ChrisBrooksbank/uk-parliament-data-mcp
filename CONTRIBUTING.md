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
