# PLANNING MODE

You are in planning mode. Your job is to analyze the missing tools specification and update the implementation plan. DO NOT write any code.

## 0a. Study Specifications

Read these files:
- `specs/missing-tools-spec.md` — the list of ~49 missing API endpoints to implement
- `AddMissingTools.md` — the full gap analysis with endpoint URLs and value assessments

## 0b. Review Current Plan

Read `IMPLEMENTATION_PLAN.md` to understand what tasks exist and their status.

## 0c. Examine Codebase

Explore the existing codebase to understand what's already implemented:
- Tool modules in `src/uk_parliament_mcp/tools/*.py` — check current tool functions
- CLI modules in `src/uk_parliament_mcp/cli/*.py` — check current CLI commands
- Tests in `tests/` — check test patterns
- OpenAPI specs in `context/` — reference for endpoint parameters

## 1. Gap Analysis

Compare the spec against the codebase:
- Which tools from the spec already exist? (mark complete)
- Which tools are partially implemented?
- Which tools have no implementation?
- Are the proposed tool names consistent with existing naming?
- Are the endpoint URLs correct per the OpenAPI specs?

## 2. Update Implementation Plan

Update `IMPLEMENTATION_PLAN.md` with:
- Mark any already-completed tools as done
- Refine tasks based on what you learned
- Add any missing details (parameter names, URL patterns)
- Keep tasks grouped by API module

## 3. Exit

After updating the plan, exit cleanly.

---

## GUARDRAILS

- **DON'T write implementation code** - planning mode only
- **DON'T modify source files** - only IMPLEMENTATION_PLAN.md
- **DO verify files exist** before marking tasks complete
- **DO check OpenAPI specs** in `context/` for accurate endpoint details
- **DO keep tasks grouped** by API module (one module per build iteration)
