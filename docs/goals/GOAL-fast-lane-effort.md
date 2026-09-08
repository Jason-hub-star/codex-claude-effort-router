# Goal — settle the fast lane's effort setting

Sealed 2026-09-08 before any run. Written by the night shift; the decision rule below is fixed and must not be edited after data exists.

One line: `the fast lane's default effort is decided by measured reasoning cost and pass rate on the bench fast tasks, verified by bench/results/exp2-*.jsonl and scripts/check.sh, while every other lane and the public API stay unchanged.`

## 1. Outcome

Pilot 1 showed the fast lane costs reasoning tokens instead of saving them on `gpt-5.6-luna` (none 46 → advisory 102 → enforce 153). Two causes are confounded: the injected context, and `reasoningEffort=medium`. This goal separates them, applies the decision rule, and leaves the fast lane's default either changed with evidence or kept with evidence.

## 2. Verification

- `python3 bench/run.py run --tasks F1,F2,F3,F4,F5 --conditions none,always-low,advisory,enforce,enforce-low --repeat 3` produces 75 rows.
- `python3 bench/run.py summarize <file>` prints the per-condition table.
- `bash scripts/check.sh` is green before and after any code change.
- The morning report quotes real command output, not claims.

## 3. Constraints

- No other lane's effort changes. Deep and critical stay `high`.
- The router stays dependency-free; no LLM in the routing path.
- Enforcement stays opt-in; the default install must not start enforcing.
- Existing tests keep passing; new behaviour gets a new test.
- Public behaviour that other people already installed (`[EFFORT LANES]` tag, hook contract, CLI flags) is not renamed.

## 4. Boundaries

Allowed: `router/effort_router.py`, `router/config.example.json`, `bench/**`, `tests/**`, `docs/**`, `README*.md`, `CHANGELOG.md`.
Forbidden: pushing, the five runtime homes outside a temp dir, anything under `~/.claude`, `~/.codex`, `~/.config/opencode`, `~/.openclaw`, `~/.hermes`, and this machine's personal `~/.config/effort-lanes/config.json`.

## 5. Iteration policy

One axis per run. If a condition errors at the provider (region opt-in, auth), record it and drop that condition rather than switching model mid-experiment. Two failed attempts at the same wall → stop and write it down.

## 6. Blocked stop

Stop and report if: the provider rejects `reasoningEffort: "low"`; more than 20% of runs error; the gate goes red for a reason not introduced here; or the decision rule below lands in a case it does not cover.

## Decision rule — sealed before data

Compare mean reasoning tokens and pass rate over the 5 fast tasks × 3 repeats.

| Case | Condition | Action |
|---|---|---|
| A | `enforce-low` reasoning < `enforce`, pass rate not lower (≥ enforce − 1 run) | Fast lane default becomes `low` |
| B | `enforce-low` ≈ `enforce` (within 15%) | Keep `medium`; the effort knob is not the cause. Record |
| C | `enforce-low` pass rate lower than `enforce` by ≥ 2 runs | Keep `medium`. Record the trade |
| D | `advisory` reasoning still ≫ `none` (> 25% higher) after A or B | The injected context is itself the cost on fast prompts. Do **not** silently drop it; write the finding and propose a short-context option as the next single-axis experiment |
| E | `always-low` < `none` | The provider default is above `low`; note that "fast = cheapest" needs `low`, not `medium` |

A and B are mutually exclusive with C. D and E are reported regardless.

## 7. Execution log

- 2026-09-08 baseline: `bash scripts/check.sh` green on `야근/2026-09-08-fast-lane-low` at 3d449c6.
- 2026-09-08: config already supports `lanes.fast.effort`; no router change needed to run the experiment.
- 2026-09-08: experiment stopped without a decision. All 30 attempted rows had zero model steps and an unretryable OpenCode Go HTTP 401 account block; they are preserved in `bench/results/exp2-fastlane-BLOCKED.jsonl` and must not enter comparisons.
- 2026-09-08: the runner now kills a hung process group at the per-run deadline and aborts the matrix after the first 401/402/403 provider error. Resume the original 75-run command only after a one-task provider smoke succeeds; changing model would invalidate the sealed comparison.
