# BUILD MODE

You are in build mode. Implement ONE task from the plan, then exit.

## 0a. Read AGENTS.md

Read `AGENTS.md` for build/test/lint commands.

## 0b. Read Implementation Plan

Read `IMPLEMENTATION_PLAN.md`. Find the first uncompleted task.

## 0c. Study CLI Spec

Read `specs/cli-spec.md` for the CLI patterns and command structure.

## 0d. Understand Existing Code

Read relevant tool files to understand the async patterns and parameters.

## 1. Implement the Task

Create/modify files for your task:
- Follow Typer patterns from the spec
- Match existing code style
- Include all required commands for the module

## 2. Validate

```bash
ruff check src/ && ruff format --check src/ && mypy src/ && pytest
```

If validation fails, fix issues and repeat.

## 3. Update Plan and Exit

Mark task complete in `IMPLEMENTATION_PLAN.md` and exit.

---

## GUARDRAILS

- **DON'T skip validation**
- **DON'T implement multiple tasks** - one per iteration
- **DO follow existing code patterns**
- **DO update IMPLEMENTATION_PLAN.md** before exiting
