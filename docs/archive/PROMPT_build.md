# BUILD MODE

You are in build mode. Implement ONE task from the plan, then exit.

## 0a. Read AGENTS.md

Read `AGENTS.md` for build/test/lint commands.

## 0b. Read Implementation Plan

Read `IMPLEMENTATION_PLAN.md`. Find the first uncompleted task (a task group like "Task 1.1: Members API").

## 0c. Study the Spec and Gap Analysis

Read `specs/missing-tools-spec.md` and `AddMissingTools.md` for endpoint URLs and details.

## 0d. Check OpenAPI Specs

Read the relevant OpenAPI spec in `context/` directory to understand exact endpoint parameters, query strings, and response shapes.

## 0e. Understand Existing Code

Read the existing tool file (`tools/<module>.py`) and CLI file (`cli/<module>.py`) to understand patterns. New tools must follow the exact same style.

## 1. Implement the Task

For each tool in the task:
1. Add `@mcp.tool()` function in `tools/<module>.py` — follow existing patterns exactly
2. Add `@app.command()` function in `cli/<module>.py` — follow existing patterns exactly
3. Add test(s) in `tests/` — follow existing test patterns

Key patterns:
- Tool descriptions use 4-part format: `Action | Keywords | Use case | Returns`
- Use `build_url(base, params)` for URL construction
- Use `await get_result(url)` for HTTP requests
- CLI commands use `run_async(get_result(url))` + `echo_utf8(format_output(...))`
- CLI commands with pagination use `paginate_request()` instead

## 2. Validate

```bash
ruff check src/ && ruff format --check src/ && mypy src/ && pytest
```

If validation fails:
- Run `ruff format src/` to auto-fix formatting
- Run `ruff check src/ --fix` to auto-fix lint issues
- Fix any remaining issues manually
- Repeat validation

## 3. Update Plan and Exit

Mark the task complete in `IMPLEMENTATION_PLAN.md` and exit.

---

## GUARDRAILS

- **DON'T skip validation** - always run all checks before finishing
- **DON'T implement multiple tasks** - one task (one API module) per iteration
- **DON'T change unrelated code** - stay focused on the current task
- **DO follow existing code patterns** exactly - consistency matters
- **DO write tests** for new tools
- **DO update IMPLEMENTATION_PLAN.md** before exiting
- **DO check `context/` OpenAPI specs** for accurate endpoint parameters
