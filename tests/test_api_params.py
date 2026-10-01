"""Every query parameter a tool sends is one its API's OpenAPI spec accepts.

The Parliament APIs silently ignore unknown query parameters, so a misspelt
filter (e.g. ``memberId`` where the API wants ``queryParameters.memberId``)
returns unfiltered results instead of an error. This calls every MCP tool with
every argument filled in, captures the URLs it builds, and checks each query
parameter against the spec in ``context/``.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any
from unittest.mock import patch
from urllib.parse import parse_qsl, urlsplit

import pytest

from uk_parliament_mcp.server import create_server

CONTEXT = Path(__file__).resolve().parent.parent / "context"

SPEC_FOR_HOST = {
    "bills-api.parliament.uk": "bills",
    "committees-api.parliament.uk": "committees",
    "commonsvotes-api.parliament.uk": "commonsvotes",
    "erskinemay-api.parliament.uk": "erskinemay",
    "hansard-api.parliament.uk": "hansard",
    "interests-api.parliament.uk": "interests",
    "lordsvotes-api.parliament.uk": "lordsvotes",
    "members-api.parliament.uk": "members",
    "oralquestionsandmotions-api.parliament.uk": "oralquestions",
    "now-api.parliament.uk": "parliamentnow",
    "statutoryinstruments-api.parliament.uk": "statutoryinstruments",
    "treaties-api.parliament.uk": "treaties",
    "whatson-api.parliament.uk": "whatson",
    "questions-statements-api.parliament.uk": "writtenquestions",
}

Route = tuple[re.Pattern[str], str, set[str], int]


def _load_routes() -> dict[str, list[Route]]:
    routes: dict[str, list[Route]] = {}
    for spec in set(SPEC_FOR_HOST.values()):
        data = json.loads((CONTEXT / f"{spec}-api.json").read_text(encoding="utf-8"))
        spec_routes = []
        for path, ops in data["paths"].items():
            op = ops.get("get")
            if not op:
                continue
            pattern = re.compile("^" + re.sub(r"\\\{[^}]+\\\}", "[^/]+", re.escape(path)) + "$")
            params = {p["name"].lower() for p in op.get("parameters", []) if p.get("in") == "query"}
            spec_routes.append((pattern, path, params, path.count("{")))
        routes[spec] = spec_routes
    return routes


def _argument(name: str, prop: dict[str, Any]) -> Any:
    types = [prop.get("type")] + [s.get("type") for s in prop.get("anyOf", [])]
    kind = next((t for t in types if t and t != "null"), "string")
    if "house" in name:
        return 1
    if kind == "string" and ("date" in name or name.endswith(("_from", "_to"))):
        return "2024-01-01"
    return {"integer": 1, "number": 1, "boolean": True, "array": [1]}.get(kind, "x")


def _recorder(captured: list[str]) -> Any:
    async def fake_get_result(url: str, *args: Any, **kwargs: Any) -> str:
        captured.append(url)
        return json.dumps({"url": url, "data": {}})

    return fake_get_result


@pytest.fixture(scope="module")
async def tool_urls() -> dict[str, list[str]]:
    """URLs each tool builds when called with every argument set."""
    server = create_server()
    urls: dict[str, list[str]] = {}
    for tool in await server.list_tools():
        captured: list[str] = []
        fake_get_result = _recorder(captured)

        patches = [
            patch.object(module, fn, fake_get_result)
            for name, module in list(sys.modules.items())
            if name.startswith("uk_parliament_mcp.tools.")
            for fn in ("get_result", "get_result_cached")
            if hasattr(module, fn)
        ]
        for p in patches:
            p.start()
        try:
            arguments = {
                name: _argument(name, prop)
                for name, prop in tool.inputSchema.get("properties", {}).items()
            }
            await server.call_tool(tool.name, arguments)
        finally:
            for p in patches:
                p.stop()
        urls[tool.name] = captured
    return urls


async def test_every_tool_makes_a_request(tool_urls: dict[str, list[str]]) -> None:
    silent = sorted(name for name, urls in tool_urls.items() if not urls)
    # Guidance tools return static text
    assert set(silent) <= {
        "order_order",
        "parliament_guide",
        "parliament_workflow",
        "get_cli_reference",
    }


async def test_query_parameters_match_openapi_specs(tool_urls: dict[str, list[str]]) -> None:
    routes = _load_routes()
    problems = []
    for tool, urls in tool_urls.items():
        for url in urls:
            parts = urlsplit(url)
            spec = SPEC_FOR_HOST.get(parts.hostname or "")
            if spec is None:
                problems.append(f"{tool}: unknown host in {url}")
                continue
            path = parts.path.rstrip("/") or "/"
            matches = sorted((r for r in routes[spec] if r[0].match(path)), key=lambda r: r[3])
            if not matches:
                problems.append(f"{tool}: {path} is not in the {spec} spec")
                continue
            _, spec_path, allowed, _ = matches[0]
            unknown = [k for k, _ in parse_qsl(parts.query) if k.lower() not in allowed]
            if unknown:
                problems.append(f"{tool}: {spec_path} does not accept {unknown}")
    assert not problems, "\n".join(problems)
