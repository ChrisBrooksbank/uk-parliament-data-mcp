"""Smoke test every CLI command against a mocked HTTP client.

Each command is invoked with placeholder values for its required arguments and
options. The test checks that it exits cleanly and that every URL it requests is
a well-formed Parliament API URL (known base, no unfilled path placeholders).
Command-specific URL and output assertions live in the per-group test files.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from typing import Any

import pytest
import typer.main
from typer.testing import CliRunner

from uk_parliament_mcp import config, http_client
from uk_parliament_mcp.cli.main import app

API_BASES = tuple(v for k, v in vars(config).items() if "_API_BASE" in k)

# Interactive, long-running, or offline-only commands covered elsewhere.
SKIP_PREFIXES = {
    ("watch",),  # auto-refreshing dashboard loop (test_watch.py)
    ("api",),  # reads bundled spec metadata, needs real API names (test_api.py)
}


def _leaf_commands(cmd: Any, path: tuple[str, ...] = ()) -> Iterator[tuple[tuple[str, ...], Any]]:
    if getattr(cmd, "commands", None):  # groups with only a callback (digest) are leaves
        for name, sub in cmd.commands.items():
            yield from _leaf_commands(sub, (*path, name))
    else:
        yield path, cmd


def _placeholder(param: Any) -> str:
    kind = type(param.type).__name__
    if kind == "Choice":
        return str(param.type.choices[0])
    if kind in ("IntParamType", "FloatParamType", "IntRange", "FloatRange", "BoolParamType"):
        return "1" if kind != "BoolParamType" else "true"
    name = param.name.lower()
    if "date" in name or kind == "DateTime":
        return "2025-01-15"
    if "postcode" in name:
        return "SW1A 1AA"
    return "test"


def _required_args(cmd: Any) -> list[str]:
    args: list[str] = []
    for param in cmd.params:
        if not param.required:
            continue
        if param.param_type_name == "argument":
            args.append(_placeholder(param))
        else:
            args += [param.opts[0], _placeholder(param)]
    return args


COMMANDS = [
    (path, _required_args(cmd))
    for path, cmd in _leaf_commands(typer.main.get_command(app))
    if not any(path[: len(prefix)] == prefix for prefix in SKIP_PREFIXES)
]


@pytest.fixture
def requested_urls(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    urls: list[str] = []

    async def fake_get_result(url: str) -> str:
        urls.append(url)
        return json.dumps({"url": url, "data": {"items": [], "totalResults": 0}})

    monkeypatch.setattr(http_client._client, "get_result", fake_get_result)
    http_client.clear_cache()
    return urls


def test_command_discovery_finds_all_groups():
    groups = {path[0] for path, _ in COMMANDS}
    assert {"members", "bills", "votes", "committees", "hansard", "questions"} <= groups
    assert {"interests", "live", "legislation", "procedures", "guide", "digest"} <= groups
    assert len(COMMANDS) > 150


@pytest.mark.parametrize(("path", "args"), COMMANDS, ids=lambda v: " ".join(v) or "-")
def test_command_runs(
    path: tuple[str, ...], args: list[str], cli_runner: CliRunner, requested_urls: list[str]
):
    result = cli_runner.invoke(app, [*path, *args])

    assert result.exit_code == 0, result.output or repr(result.exception)
    for url in requested_urls:
        assert url.startswith(API_BASES), f"unexpected host: {url}"
        assert "{" not in url and "}" not in url, f"unfilled placeholder: {url}"
        assert "/None" not in url, f"None in path: {url}"
