# PLANNING MODE

You are in planning mode. Your job is to analyze the improvement specifications and update the implementation plan. DO NOT write any code.

## 0a. Study Specifications

Using parallel subagents, read and understand each file in the `docs/` directory:
- `docs/IMPROVEMENT_PLAN.md` - Master plan overview
- `docs/PHASE1_QUICK_WINS.md` - Badges, TOC, tool count verification
- `docs/PHASE2_CODE_QUALITY.md` - Centralized config, TypedDict, validators
- `docs/PHASE3_TESTING.md` - Test coverage expansion
- `docs/PHASE4_DOCUMENTATION.md` - README restructure, CHANGELOG, CONTRIBUTING
- `docs/PHASE5_ARCHITECTURE.md` - CI coverage, caching, pre-commit hooks

These define what needs to be implemented.

## 0b. Review Current Plan

Read `IMPLEMENTATION_PLAN_IMPROVEMENTS.md` to understand what tasks exist and their status.

## 0c. Examine Codebase

Using parallel subagents, explore the existing codebase to understand:
- What's already implemented
- Code patterns and conventions in `src/uk_parliament_mcp/`
- Test structure in `tests/`
- Current README.md and documentation state

## 1. Gap Analysis

Compare the improvement specifications against the existing codebase:
- What improvements are fully implemented?
- What improvements are partially implemented?
- What improvements have no implementation?

## 2. Update Implementation Plan

Update `IMPLEMENTATION_PLAN_IMPROVEMENTS.md` with:
- New tasks for unimplemented requirements
- Refined tasks based on what you learned
- Clear priority order (Phase 1 before Phase 2, etc.)
- Mark any completed tasks as done

Format tasks as:
```
- [ ] Task description (spec: PHASE#_NAME.md)
- [x] Completed task
```

## 3. Exit

After updating the plan, your work is done. Exit cleanly. The loop will restart with fresh context for the next iteration.

---

## 99999. GUARDRAILS - READ CAREFULLY

- **DON'T assume code doesn't exist** - always verify by reading files first
- **DON'T write any implementation code** - planning mode is for planning only
- **DON'T modify source files** - only modify `IMPLEMENTATION_PLAN_IMPROVEMENTS.md`
- **DO capture architectural decisions** in the plan
- **DO prioritize tasks logically** (Phase 1 before Phase 2, dependencies first)
- **DO keep tasks small** - one task = one iteration in build mode
