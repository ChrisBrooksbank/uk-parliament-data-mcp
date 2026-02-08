# UK Parliament MCP CLI Implementation Plan

## Overview

Add a CLI to the existing `uk-parliament-mcp` package, enabling direct terminal access to all 161 Parliament API tools without requiring an MCP client.

**Benefits:**
1. Works on locked-down systems without MCP client access
2. LLMs can use via Bash tool with standard Unix piping (`| jq`, `| grep`)
3. Easier debugging and API exploration
4. Scriptable for automation

## Design Decisions

### Framework: Typer

Using [Typer](https://typer.tiangolo.com/) because:
- Modern, type-hint based (matches existing codebase style)
- Auto-generates `--help` at every level
- Recommended by [Python Packaging Guide](https://packaging.python.org/en/latest/guides/creating-command-line-tools/)
- Lightweight (~100KB with Click dependency)

### Command Structure

```
parliament <group> <command> [options]
```

**Top-level groups** (matching tool modules):
```
parliament members     # 24 tools - MPs, Lords, constituencies
parliament bills       # 21 tools - legislation, amendments
parliament votes       # 10 tools - Commons + Lords divisions (combined)
parliament committees  # 26 tools - committee info, evidence
parliament hansard     # 20 tools - parliamentary record
parliament questions   # 12 tools - oral, written, EDMs (combined)
parliament interests   # 3 tools - register of interests
parliament live        # 10 tools - now + whatson (combined)
parliament legislation # 11 tools - SIs, treaties (combined)
parliament procedures  # 11 tools - Erskine May
parliament composite   # 4 tools - high-level combined queries
parliament guide       # Help/guidance commands
```

**Example commands:**
```bash
# Search for an MP
parliament members search "Keir Starmer"

# Get bill details
parliament bills get 123

# Check how MP voted on topic
parliament composite check-vote "Boris Johnson" "climate"

# Get comprehensive MP profile
parliament composite mp-profile "Rishi Sunak"

# List available tools
parliament guide tools

# Get help on a specific domain
parliament guide topic members
```

### Output Modes

```bash
# Default: compact JSON (for piping)
parliament members search "Starmer" | jq '.data[0].id'

# Pretty-printed JSON
parliament members search "Starmer" --pretty

# Just the data (strips url wrapper)
parliament members search "Starmer" --data-only
```

Global flags:
- `--pretty` / `-p`: Pretty-print JSON output
- `--data-only` / `-d`: Return only the `data` field, not the `{url, data}` wrapper
- `--no-color`: Disable colored output (for piping)

## Architecture

### New Files

```
src/uk_parliament_mcp/
├── cli/
│   ├── __init__.py      # CLI app creation, global options
│   ├── main.py          # Entry point, app assembly
│   ├── members.py       # members subcommands
│   ├── bills.py         # bills subcommands
│   ├── votes.py         # votes subcommands (commons + lords)
│   ├── committees.py    # committees subcommands
│   ├── hansard.py       # hansard subcommands
│   ├── questions.py     # questions subcommands (oral + written + edms)
│   ├── interests.py     # interests subcommands
│   ├── live.py          # live subcommands (now + whatson)
│   ├── legislation.py   # legislation subcommands (SIs + treaties)
│   ├── procedures.py    # procedures subcommands (erskine may)
│   ├── composite.py     # composite high-level commands
│   ├── guide.py         # help/guidance commands
│   └── utils.py         # shared utilities (output formatting, async runner)
```

### Key Implementation Pattern

```python
# cli/utils.py
import asyncio
import json
import typer
from typing import Optional

def run_async(coro):
    """Run async function synchronously for CLI."""
    return asyncio.run(coro)

def format_output(result: str, pretty: bool = False, data_only: bool = False) -> str:
    """Format JSON output based on flags."""
    if data_only:
        parsed = json.loads(result)
        result = json.dumps(parsed.get("data", parsed))
    if pretty:
        parsed = json.loads(result)
        return json.dumps(parsed, indent=2)
    return result

# cli/members.py
import typer
from uk_parliament_mcp.http_client import get_result, build_url
from uk_parliament_mcp.config import MEMBERS_API_BASE
from uk_parliament_mcp.cli.utils import run_async, format_output
from urllib.parse import quote

app = typer.Typer(help="MP and Lords member tools")

@app.command("search")
def search_member(
    name: str = typer.Argument(..., help="Full or partial name to search"),
    pretty: bool = typer.Option(False, "--pretty", "-p", help="Pretty-print output"),
    data_only: bool = typer.Option(False, "--data-only", "-d", help="Return data only"),
):
    """Search for MPs and Lords by name."""
    url = f"{MEMBERS_API_BASE}/Members/Search?Name={quote(name)}"
    result = run_async(get_result(url))
    typer.echo(format_output(result, pretty, data_only))

@app.command("get")
def get_member(
    member_id: int = typer.Argument(..., help="Member ID"),
    pretty: bool = typer.Option(False, "--pretty", "-p"),
    data_only: bool = typer.Option(False, "--data-only", "-d"),
):
    """Get member details by ID."""
    url = f"{MEMBERS_API_BASE}/Members/{member_id}"
    result = run_async(get_result(url))
    typer.echo(format_output(result, pretty, data_only))
```

### Entry Point Configuration

```toml
# pyproject.toml additions
[project.scripts]
uk-parliament-mcp = "uk_parliament_mcp.__main__:main"  # existing
parliament = "uk_parliament_mcp.cli.main:app"          # new CLI

[project.dependencies]
# Add typer
typer = ">=0.9.0"
```

### CLI Main Assembly

```python
# cli/main.py
import typer
from uk_parliament_mcp.cli import (
    members, bills, votes, committees, hansard,
    questions, interests, live, legislation,
    procedures, composite, guide
)

app = typer.Typer(
    name="parliament",
    help="UK Parliament data CLI - Access 161 Parliament API tools from the terminal.",
    no_args_is_help=True,
)

# Register subcommand groups
app.add_typer(members.app, name="members")
app.add_typer(bills.app, name="bills")
app.add_typer(votes.app, name="votes")
app.add_typer(committees.app, name="committees")
app.add_typer(hansard.app, name="hansard")
app.add_typer(questions.app, name="questions")
app.add_typer(interests.app, name="interests")
app.add_typer(live.app, name="live")
app.add_typer(legislation.app, name="legislation")
app.add_typer(procedures.app, name="procedures")
app.add_typer(composite.app, name="composite")
app.add_typer(guide.app, name="guide")

if __name__ == "__main__":
    app()
```

## Command Mapping

### Priority 1: Composite Commands (Most Useful)

| CLI Command | MCP Tool | Description |
|-------------|----------|-------------|
| `parliament composite mp-profile <name>` | `get_mp_profile` | Full MP profile in one call |
| `parliament composite check-vote <mp> <topic>` | `check_mp_vote` | How did MP vote on topic |
| `parliament composite bill-overview <search>` | `get_bill_overview` | Comprehensive bill info |
| `parliament composite committee-summary <topic>` | `get_committee_summary` | Full committee details |

### Priority 2: Members (Most Common Queries)

| CLI Command | MCP Tool |
|-------------|----------|
| `parliament members search <name>` | `get_member_by_name` |
| `parliament members get <id>` | `get_member_by_id` |
| `parliament members biography <id>` | `get_member_biography` |
| `parliament members contact <id>` | `get_member_contact` |
| `parliament members photo <id>` | `get_member_photo` |
| `parliament members current [--house N]` | `get_current_members` |
| `parliament members constituency <name>` | `search_constituency` |
| `parliament members parties [--house N]` | `get_parties` |
| ... | (24 total) |

### Priority 3: Bills

| CLI Command | MCP Tool |
|-------------|----------|
| `parliament bills search <term>` | `search_bills` |
| `parliament bills get <id>` | `get_bill` |
| `parliament bills stages <id>` | `get_bill_stages` |
| `parliament bills amendments <id>` | `get_bill_amendments` |
| ... | (21 total) |

### Full Command List

All 161 tools will be mapped. See `tools/*.py` for complete function signatures.

## Implementation Phases

### Phase 1: Foundation
1. Add `typer>=0.9.0` to dependencies
2. Create `cli/` directory structure
3. Implement `cli/utils.py` with async runner and output formatting
4. Implement `cli/main.py` app assembly
5. Add entry point to `pyproject.toml`

### Phase 2: Core Commands
1. `cli/composite.py` - 4 high-level commands
2. `cli/members.py` - 24 member commands
3. `cli/bills.py` - 21 bill commands
4. `cli/guide.py` - Help and guidance

### Phase 3: Remaining Domains
1. `cli/votes.py` - 10 commands (commons + lords)
2. `cli/committees.py` - 26 commands
3. `cli/hansard.py` - 20 commands
4. `cli/questions.py` - 12 commands
5. `cli/interests.py` - 3 commands
6. `cli/live.py` - 10 commands
7. `cli/legislation.py` - 11 commands
8. `cli/procedures.py` - 11 commands

### Phase 4: Polish
1. Add CLI usage examples to documentation
3. Add CLI-specific tests
4. Update CLAUDE.md with CLI info

## Testing Strategy

```python
# tests/test_cli/test_members.py
from typer.testing import CliRunner
from uk_parliament_mcp.cli.main import app

runner = CliRunner()

def test_members_search_returns_json():
    result = runner.invoke(app, ["members", "search", "Test"])
    assert result.exit_code == 0
    assert '"url"' in result.stdout

def test_members_search_pretty_formats_output():
    result = runner.invoke(app, ["members", "search", "Test", "--pretty"])
    assert result.exit_code == 0
    assert "  " in result.stdout  # indentation present

def test_members_search_data_only_strips_wrapper():
    result = runner.invoke(app, ["members", "search", "Test", "--data-only"])
    assert result.exit_code == 0
    assert '"url"' not in result.stdout
```

## Verification Plan

After implementation, verify:

1. **Installation works:**
   ```bash
   pip install -e .
   parliament --help
   ```

2. **Commands execute:**
   ```bash
   parliament members search "Keir Starmer"
   parliament composite mp-profile "Rishi Sunak" --pretty
   parliament bills search "Online Safety" --data-only | jq '.items[0]'
   ```

3. **Help is comprehensive:**
   ```bash
   parliament --help
   parliament members --help
   parliament members search --help
   ```

4. **Tests pass:**
   ```bash
   pytest tests/test_cli/
   ```

5. **Type checking passes:**
   ```bash
   mypy src/uk_parliament_mcp/cli/
   ```

## Files to Modify

| File | Change |
|------|--------|
| `pyproject.toml` | Add typer dependency, add `parliament` entry point |
| `CLAUDE.md` | Document CLI usage |
| `README.md` | Add CLI section |

## Files to Create

| File | Purpose |
|------|---------|
| `src/uk_parliament_mcp/cli/__init__.py` | Package init |
| `src/uk_parliament_mcp/cli/main.py` | App assembly and entry point |
| `src/uk_parliament_mcp/cli/utils.py` | Shared utilities |
| `src/uk_parliament_mcp/cli/composite.py` | Composite commands |
| `src/uk_parliament_mcp/cli/members.py` | Member commands |
| `src/uk_parliament_mcp/cli/bills.py` | Bill commands |
| `src/uk_parliament_mcp/cli/votes.py` | Votes commands |
| `src/uk_parliament_mcp/cli/committees.py` | Committee commands |
| `src/uk_parliament_mcp/cli/hansard.py` | Hansard commands |
| `src/uk_parliament_mcp/cli/questions.py` | Questions commands |
| `src/uk_parliament_mcp/cli/interests.py` | Interests commands |
| `src/uk_parliament_mcp/cli/live.py` | Live/calendar commands |
| `src/uk_parliament_mcp/cli/legislation.py` | SI/treaty commands |
| `src/uk_parliament_mcp/cli/procedures.py` | Erskine May commands |
| `src/uk_parliament_mcp/cli/guide.py` | Help/guidance commands |
| `tests/test_cli/__init__.py` | Test package |
| `tests/test_cli/test_main.py` | Main app tests |
| `tests/test_cli/test_members.py` | Member command tests |
| `tests/test_cli/conftest.py` | CLI test fixtures |

## Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| 161 commands is a lot to maintain | Generate from tool definitions where possible |
| Async/sync boundary issues | Centralize in `utils.py`, test thoroughly |
| Breaking MCP server | CLI is additive, existing code untouched |
| Large dependency footprint | Typer is small (~100KB with Click) |

## Success Criteria

1. `parliament --help` shows all command groups
2. All 161 tools accessible via CLI
3. Output pipes cleanly to `jq`, `grep`, etc.
4. No regressions in MCP server functionality
5. Tests pass, type checking clean
