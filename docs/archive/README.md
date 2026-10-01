# Archive

Finished or superseded plans and specs, kept for history. Nothing here is current. Open work is in [`ROADMAP.md`](../../ROADMAP.md).

| File | What it was |
|------|-------------|
| `specs/python-migration-spec.md` | C# → Python port (1.0.0) |
| `IMPROVEMENT_PLAN.md`, `PHASE1–5_*.md`, `IMPLEMENTATION_PLAN_IMPROVEMENTS.md`, `specs/improvement-spec.md` | Docs, config, testing and CI improvements (1.1.0). The phase files still have unticked checkboxes, but every item was done. |
| `IMPROVEMENTS.md`, `specs/v2-improvements-spec.md` | The "v2" ideas: reference-data caching (done, see CHANGELOG), validation (dropped), and others still open in `ROADMAP.md`. |
| `specs/agent-guidance-spec.md` | `order_order` / `parliament_guide` / `/parliament` prompt |
| `CLI_PLAN.md`, `specs/cli-spec.md` | The `parliament` CLI (1.5.0) |
| `AddMissingTools.md`, `specs/missing-tools-spec.md`, `IMPLEMENTATION_PLAN.md` | Gap analysis and the 46 tools added in 1.17.0 |
| `PROMPT_plan.md`, `PROMPT_build.md` | Prompts the `loop.sh` / `loop.ps1` autonomous loop used for the 1.17.0 build-out |

## Running the loop again

`loop.sh` and `loop.ps1` read `PROMPT_plan.md` / `PROMPT_build.md` from the repo root, and the prompts read `AGENTS.md` for commands. To start a new campaign, write a spec and fresh prompts at the root. The archived prompts are a working template.
