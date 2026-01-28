# PROMPT_build.md - Build Phase

You are migrating the UK Parliament MCP Server from C# .NET 9.0 to Python. This is the BUILD phase - implement one task at a time with full validation.

## Phase 0: Orientation

Study the project state:

1. Read `AGENTS.md` for build commands and conventions
2. Read `IMPLEMENTATION_PLAN.md` for current task status
3. Read `specs/python-migration-spec.md` if you need implementation details

## Phase 1: Select Task

From `IMPLEMENTATION_PLAN.md`, select the FIRST unchecked task (`- [ ]`) in the highest priority section.

If no tasks remain, report completion and stop.

## Phase 2: Investigate

Before implementing, study:

1. The C# reference implementation in `OpenData.Mcp.Server/Tools/` for:
   - Exact API endpoints
   - Query parameter names
   - Tool description text
   - Error handling patterns

2. Existing Python code for:
   - Import patterns
   - How other tools are structured
   - Shared utilities in http_client.py

Use only 1 subagent for investigation to preserve context.

## Phase 3: Implement

Write the code following the spec patterns:

```python
@mcp.tool()
async def tool_name(param: str) -> str:
    """Description from C# [Description] attribute.

    Args:
        param: Description from C# parameter attribute.

    Returns:
        Response format description.
    """
    url = build_url(f"{API_BASE}/endpoint", {"param": param})
    return await get_result(url)
```

Key requirements:
- Match C# tool descriptions exactly
- Use `build_url()` for query parameters
- Use `quote()` from urllib.parse for path segments
- Return type is always `str`

## Phase 4: Validate

Run ALL checks. ALL must pass before proceeding:

```bash
# 1. Type check
mypy src/

# 2. Lint
ruff check src/

# 3. Tests (if they exist)
pytest

# 4. Server starts
python -m uk_parliament_mcp
```

If any check fails, fix the issue before continuing.

## Phase 5: Update Plan

Mark the completed task in `IMPLEMENTATION_PLAN.md`:

```markdown
- [x] tools/members.py - get_member_by_name
```

## Phase 6: Commit

Create a commit with a descriptive message:

```bash
git add .
git commit -m "feat: Add get_member_by_name tool to members module"
```

## Guardrails

999. Only implement ONE task per iteration
1000. NEVER skip validation - all checks must pass
1001. NEVER delete C# reference code
1002. If stuck on a task for 2+ attempts, mark it as blocked and move to next
1003. Keep IMPLEMENTATION_PLAN.md accurate

## Blocked Tasks

If a task is blocked, update the plan:

```markdown
- [ ] ~tools/foo.py - blocked_tool~ BLOCKED: [reason]
```

## Output

After each iteration, report:
- Task completed (or blocked reason)
- Validation results
- Next task to attempt
