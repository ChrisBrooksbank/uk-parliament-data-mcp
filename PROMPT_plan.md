# PROMPT_plan.md - Planning Phase

You are migrating the UK Parliament MCP Server from C# .NET 9.0 to Python. This is the PLANNING phase - you must NOT implement anything. Your job is to analyze gaps and generate a prioritized task list.

## Phase 0: Orientation

Study these files using parallel subagents:

1. **Specification subagent**: Study `specs/python-migration-spec.md` - understand target architecture, code patterns, all 86 tools
2. **C# Reference subagent**: Study `OpenData.Mcp.Server/Tools/*.cs` - understand current implementation, exact API endpoints, parameter handling
3. **Current State subagent**: Study existing Python files in `src/` (if any) - understand what's already implemented

Don't assume anything is or isn't implemented. Study the actual files.

## Phase 1: Gap Analysis

After orientation, compare:
- What the spec requires (86 tools, http_client, server setup)
- What currently exists in Python

For each component, determine:
- NOT_STARTED: No Python file exists
- PARTIAL: File exists but incomplete
- COMPLETE: File exists and matches spec

## Phase 2: Generate Implementation Plan

Write to `IMPLEMENTATION_PLAN.md` with this structure:

```markdown
# Implementation Plan

## Status Summary
- Total tools required: 86
- Tools implemented: [count]
- Core infrastructure: [status]

## Priority 1: Core Infrastructure
- [ ] Create pyproject.toml
- [ ] Create src/uk_parliament_mcp/__init__.py
- [ ] Create src/uk_parliament_mcp/__main__.py
- [ ] Create src/uk_parliament_mcp/server.py
- [ ] Create src/uk_parliament_mcp/http_client.py

## Priority 2: Core Tools (2 tools)
- [ ] tools/core.py - hello_parliament
- [ ] tools/core.py - goodbye_parliament

## Priority 3: Members Tools (24 tools)
- [ ] tools/members.py - get_member_by_name
- [ ] tools/members.py - get_member_by_id
... (list each tool)

## Priority 4-14: Remaining Modules
... (list each module and its tools)

## Priority 15: Testing
- [ ] tests/test_http_client.py
- [ ] tests/test_tools/test_core.py
...

## Priority 16: Documentation
- [ ] Update CLAUDE.md for Python
- [ ] Update README.md for Python
```

## Guardrails

999. DO NOT write any code or create any files except IMPLEMENTATION_PLAN.md
1000. DO NOT delete any files
1001. Every task must be specific and actionable
1002. Reference exact C# tool names and methods
1003. Keep IMPLEMENTATION_PLAN.md up to date with current state

## Output

After generating the plan, report:
- Total tasks identified
- Current completion status
- Recommended next action for build phase
