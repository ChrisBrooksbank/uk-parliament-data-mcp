"""Tool names mentioned in tool descriptions ("See also:", "Combines:") all exist."""

from __future__ import annotations

import re

from uk_parliament_mcp.server import create_server

SEGMENT_RE = re.compile(r"(?:See also|Combines):([^.]*)")
TOOL_NAME_RE = re.compile(r"\b[a-z][a-z0-9]*(?:_[a-z0-9]+)+\b")


async def test_cross_references_name_registered_tools() -> None:
    tools = await create_server().list_tools()
    names = {t.name for t in tools}
    unknown = {}
    referencing = 0
    for tool in tools:
        segments = SEGMENT_RE.findall(tool.description or "")
        referencing += bool(segments)
        for segment in segments:
            for name in TOOL_NAME_RE.findall(segment):
                if name not in names:
                    unknown.setdefault(tool.name, []).append(name)
    assert not unknown, unknown
    assert referencing >= 60
