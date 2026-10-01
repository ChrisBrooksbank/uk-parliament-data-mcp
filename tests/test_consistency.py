"""Guards against drift between the MCP tools, the CLI and the docs.

The tool count is written by hand in several docs and help strings, and each
MCP tool's endpoint has a hand-written CLI twin. These tests fail when one side
changes without the other.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from uk_parliament_mcp.server import create_server

REPO_ROOT = Path(__file__).resolve().parents[1]
PACKAGE = REPO_ROOT / "src" / "uk_parliament_mcp"

# Files that state the total number of MCP tools.
TOOL_COUNT_FILES = [
    PACKAGE / "tools" / "core.py",
    PACKAGE / "cli" / "main.py",
    PACKAGE / "cli" / "guide.py",
    REPO_ROOT / "README.md",
    REPO_ROOT / "CLAUDE.md",
]

# A three-digit number followed within a few words by "tool(s)", e.g.
# "209 tools", "209 available tools", "209 Parliament API tools".
TOOL_COUNT_RE = re.compile(r"\b(\d{3})\b(?:[ \w-]{0,30}?)\btools?\b")

# f"{MEMBERS_API_BASE}/Members/{member_id}/Biography" -> (MEMBERS_API_BASE, /Members/{}/Biography)
ENDPOINT_RE = re.compile(r'f"\{([A-Z0-9_]+_API_BASE\w*)\}(/[^"?]*)')

# Endpoints deliberately exposed on only one side.
MCP_ONLY_ENDPOINTS = {
    # Removed from the CLI: the API returns broken blob URLs (see CHANGELOG 1.13.0).
    ("WRITTEN_QUESTIONS_API_BASE", "/dailyreports/dailyreports"),
}
CLI_ONLY_ENDPOINTS: set[tuple[str, str]] = set()


def _endpoints(directory: Path) -> set[tuple[str, str]]:
    found = set()
    for path in directory.glob("*.py"):
        for base, route in ENDPOINT_RE.findall(path.read_text(encoding="utf-8")):
            found.add((base, re.sub(r"\{[^}]*\}", "{}", route).rstrip("/")))
    return found


@pytest.fixture(scope="module")
async def registered_tool_count() -> int:
    return len(await create_server().list_tools())


@pytest.mark.parametrize("path", TOOL_COUNT_FILES, ids=lambda p: p.name)
async def test_documented_tool_count_matches_registered(path: Path, registered_tool_count: int):
    text = path.read_text(encoding="utf-8")
    counts = {int(n) for n in TOOL_COUNT_RE.findall(text)}
    assert counts, f"no tool count found in {path.name}; update TOOL_COUNT_FILES"
    assert counts == {registered_tool_count}, (
        f"{path.name} mentions {sorted(counts)} tools but {registered_tool_count} are registered"
    )


def test_cli_covers_every_mcp_endpoint():
    mcp = _endpoints(PACKAGE / "tools")
    cli = _endpoints(PACKAGE / "cli")
    assert mcp, "no MCP endpoints found; has the URL-building pattern changed?"

    missing_from_cli = mcp - cli - MCP_ONLY_ENDPOINTS
    missing_from_mcp = cli - mcp - CLI_ONLY_ENDPOINTS
    assert not missing_from_cli, f"MCP endpoints with no CLI command: {sorted(missing_from_cli)}"
    assert not missing_from_mcp, f"CLI endpoints with no MCP tool: {sorted(missing_from_mcp)}"


def test_parity_allowlists_are_not_stale():
    mcp = _endpoints(PACKAGE / "tools")
    cli = _endpoints(PACKAGE / "cli")
    stale = (MCP_ONLY_ENDPOINTS - (mcp - cli)) | (CLI_ONLY_ENDPOINTS - (cli - mcp))
    assert not stale, f"allowlisted endpoints now on both sides or gone: {sorted(stale)}"
