# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

UK Parliament MCP Server (Unofficial), a community project that is not affiliated with or endorsed by UK Parliament. One Python 3.11+ package (`uk-parliament-mcp`) ships two front ends over the public `*.parliament.uk` REST APIs:

- **MCP server** (`uk-parliament-mcp` / `python -m uk_parliament_mcp`): FastMCP over stdio, with 205 read-only tools plus prompts and resources.
- **CLI** (`parliament`): a Typer app with command groups (`members`, `bills`, `votes`, `committees`, `hansard`, `composite`, `live`, `digest`, `watch`, `api`, `guide`, …).

End-user usage of both is documented in `README.md`.

## Commands

```bash
pip install -e ".[dev]"                 # dev install (Python 3.11+)

# Validation (CI runs exactly these on 3.11 and 3.12)
ruff check src/ tests/ && ruff format --check src/ tests/ && mypy src/ && pytest

ruff check src/ tests/ --fix && ruff format src/ tests/   # auto-fix

# Tests (pytest adds --cov by default via pyproject addopts)
pytest tests/test_tools/                                  # MCP tool tests
pytest tests/test_cli/                                    # CLI tests
pytest tests/test_tools/test_members.py::TestMembersToolsRegistration -q
pytest -k "search_member" --no-cov                        # single test, skip coverage

python -m uk_parliament_mcp             # run MCP server (stdio)
parliament --help                       # run CLI
python scripts/generate_api_metadata.py # regenerate cli/api_metadata.json from context/*.json specs
```

mypy runs in `strict` mode. Ruff line length is 100, but E501 is ignored because tool docstrings are long single lines.

## Architecture

```
MCP client ──stdio──> server.py (FastMCP) ──> tools/*.py ─┐
                                                          ├─> http_client.py ──HTTP──> *.parliament.uk
terminal ──> cli/main.py (Typer) ──> cli/*.py ────────────┘
```

- **`config.py`**: the single source of every API base URL (`MEMBERS_API_BASE`, `BILLS_API_BASE`, …) and the house constants. Tools, CLI and tests all import from here, so don't hardcode base URLs.
- **`http_client.py`**: `build_url(base, params)` drops `None`/empty params. `get_result(url)` runs a shared `ParliamentHTTPClient` with a 30s timeout and 3 retries with backoff on 408/429/5xx. It always returns a JSON **string** shaped `{url, data}` or `{url, error, statusCode}` and never raises for HTTP errors. `get_result_cached(url, cache_key)` adds a 15-minute in-memory cache for reference data. Every URL called is recorded (`get_called_urls`) so the CLI can show its sources.
- **`pruning.py`**: applied inside the HTTP client to successful responses. It strips nulls and empties, flattens value wrappers and truncates arrays (`PARLIAMENT_MAX_ARRAY`, default 20) to save MCP context tokens. You can turn it off with `PARLIAMENT_PRUNING=false`. `cli/main.py:main()` calls `disable_pruning()`, so **CLI output is unpruned and MCP output is pruned**.
- **`server.py`**: `create_server()` calls `register_tools(mcp)` on each `tools/` module, then `core.register_prompts` (the `/parliament` prompt) and `resources.register_resources` (`parliament://…` resources). Server `instructions` is `core.SYSTEM_PROMPT`.
- **`tools/*.py`**: one module per API. Each defines `register_tools(mcp)` containing nested `@mcp.tool()` async functions that `build_url` → `return await get_result(url)` and pass raw API JSON through. `composite.py` combines several calls (MP profile, bill overview, my-MP by postcode, …). `core.py` holds the guidance text (`SYSTEM_PROMPT`, `QUICK_REFERENCE`, per-topic guides, workflows) and the guidance tools (`order_order`, `parliament_guide`, `parliament_workflow`, `get_cli_reference`).
- **`cli/*.py`**: these do **not** call the MCP tool functions. Each command builds its own URL with `config` + `build_url` and hands it to `cli/utils.py` (`output_result`, or `output_paginated` with a config from `cli/pagination.py`). Global flags (`--format/--fields/--raw/--pretty/--data-only`) are handled in `cli/utils.py` and `cli/formatters.py`. `renderers.py` does Rich output for composite results. `api.py`/`try_it.py` drive the API explorer from `api_metadata.json`, which is generated from the OpenAPI specs in `context/`.

## Adding or changing a tool

1. Add a nested `@mcp.tool()` async function in the matching `tools/<api>.py`. Import the base URL from `config.py` and use `build_url` + `get_result`.
2. Write the docstring in the 4-part semantic format `Action | keywords, synonyms | Use case | Returns`, followed by an `Args:` section. The docstring is the tool description the LLM sees.
3. Add the matching Typer command in `cli/<group>.py`. The CLI and the MCP tool are separate implementations. `tests/test_consistency.py` fails if an endpoint (`f"{X_API_BASE}/path"`) is called on one side only. Deliberate one-sided endpoints go in its `MCP_ONLY_ENDPOINTS`/`CLI_ONLY_ENDPOINTS` allowlists.
4. Add tests in `tests/test_tools/test_<api>.py` (mirrors the source layout). Tests patch the module-level name, e.g. `patch("uk_parliament_mcp.tools.members.get_result", new_callable=AsyncMock)`, and assert on the URL. Registration tests list the expected tool names per module.
5. **Tool count is hardcoded** ("205") in `tools/core.py` (`QUICK_REFERENCE`, the `all` guide, docstrings), `cli/main.py` help, `cli/guide.py`, `README.md`, this file and `tests/test_tools/test_core.py`. `tests/test_consistency.py` checks these files against the number of registered tools. Also update the per-topic counts in the guide text in `core.py`, which are not checked.

## Conventions

- House IDs: 1 = Commons, 2 = Lords (`config.HOUSE_COMMONS`/`HOUSE_LORDS`). Dates are `YYYY-MM-DD`. Pagination is `skip`/`take`.
- All tools are read-only and idempotent. Responses are API JSON passed through, not reshaped (apart from pruning).
- Logging goes to stderr; stdout is reserved for the MCP stdio protocol.
- Open work is listed in `ROADMAP.md`. Finished plans and specs are in `docs/archive/`.
- `AGENTS.md` is a short operational guide used by the `loop.sh`/`loop.ps1` autonomous build loop, which reads `PROMPT_plan.md`/`PROMPT_build.md` from the repo root. Past prompts are in `docs/archive/`.

## Release

The version lives in `src/uk_parliament_mcp/__init__.py` (hatch dynamic version). Publishing a GitHub Release (tag `vX.Y.Z`) triggers `publish.yml`, which pushes to PyPI via Trusted Publishing. `build-exe.yml` builds standalone `parliament` executables with PyInstaller (`parliament.spec`, `scripts/build-exe.py`).
