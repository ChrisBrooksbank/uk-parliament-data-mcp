# PLANNING MODE

You are in planning mode. Your job is to analyze the CLI specification and update the implementation plan. DO NOT write any code.

## 0a. Study Specifications

Read `specs/cli-spec.md` - the complete CLI implementation specification.

## 0b. Review Current Plan

Read `IMPLEMENTATION_PLAN.md` to understand what tasks exist and their status.

## 0c. Examine Codebase

Explore the existing codebase to understand:
- Tool patterns in `src/uk_parliament_mcp/tools/*.py`
- HTTP client in `src/uk_parliament_mcp/http_client.py`
- Config in `src/uk_parliament_mcp/config.py`

## 1. Gap Analysis

Compare the CLI spec against the implementation plan:
- What CLI modules are fully implemented?
- What CLI modules are partially implemented?
- What CLI modules have no implementation?

## 2. Update Implementation Plan

Update `IMPLEMENTATION_PLAN.md` with:
- New tasks for unimplemented CLI modules
- Mark completed tasks as done
- Keep tasks small (one module per task)

## 3. Exit

After updating the plan, exit cleanly.

---

## GUARDRAILS

- **DON'T write implementation code** - planning mode only
- **DON'T modify source files** - only IMPLEMENTATION_PLAN.md
- **DO verify files exist** before marking tasks complete
- **DO keep tasks small** - one CLI module per build iteration
