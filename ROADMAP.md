# Roadmap

Open work, roughly in priority order. Finished plans and specs (the phase 1–5 improvement plan, the CLI build-out, the missing-endpoints gap analysis) are in [`docs/archive/`](docs/archive/).

## Consistency

- **One `house` parameter type.** About half the tools take `house: int` (1 = Commons, 2 = Lords) and half take `house: str` ("Commons"/"Lords"), following whichever form each upstream API uses. Accepting either form everywhere would remove a common source of wrong calls by LLMs.
- **Merge `commons_votes.py` and `lords_votes.py`.** These two modules are near-identical (5 tools each). A shared factory with the house and API base as parameters would halve the code.
- **Check the per-topic tool counts in `core.py`.** `tests/test_consistency.py` checks the total tool count. The per-topic counts in the `parliament_guide` text ("Members Tools (39 tools)" and so on) are still unchecked.

## Capabilities

New composite tools, each combining existing endpoints:

- Compare two MPs' votes on a topic.
- Bills sponsored by a member.
- Committee ↔ bill cross-reference (which committees examined a bill, and the reverse).
- Cross-API search covering members, bills, committees and Hansard. A CLI version was built in 1.12.0 and then removed for a rethink.
- Suggest next steps when a composite tool finds nothing, e.g. "try the surname only" or "widen the date range".

## Discoverability

- Add "See also" cross-references to tool docstrings, and list the underlying tools in each composite tool's docstring.

## Tests

- CLI modules with the least unit coverage: `cli/guide.py`, `cli/watch.py`, `cli/api.py`, `cli/try_it.py`. `tests/test_cli/test_all_commands.py` smoke-tests every command, but not their output rendering.

## Side projects

- **Hansard semantic search PWA** (`pwa/`): plan and Vite scaffold only. See [`pwa/PLAN.md`](pwa/PLAN.md).

## Maybe

- Explicit httpx connection-pool limits and per-endpoint timeouts. The current setup (one shared client, 30 s timeout) hasn't caused problems so far.
