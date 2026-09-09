# Routing-axis benchmark

Same tasks, same model, one axis changed: how the prompt's effort is chosen. Numbers from other people's benchmarks do not transfer between harnesses, so this measures the router in the only way that means anything — against baselines on the same machine.

## Design

- **Fixture:** `fixtures/todo`, a 7-file Python project with seeded defects (wrong date math, missing guard, hardcoded secret, path traversal, SQL injection, world-readable store).
- **Tasks:** `tasks.json`, 15 prompts — 5 fast (lookups, a typo), 5 deep (fix, implement, refactor), 5 critical (security fixes). Each has a hidden check in `verify/<id>.py` that fails on the untouched fixture; the agent never sees those checks.
- **Conditions** (`run.py`): `none` (plugins off, provider default effort), `always-low` / `always-high` (plugins off, one fixed effort), `advisory` (effort-lanes context only), `enforce` (normal lane efforts), and `enforce-low` (only fast changes from medium to low).
- **Runtime:** OpenCode, because it is the runtime where the router can actually change effort. Default model `opencode-go/gpt-5.6-luna` — an OpenAI reasoning model, so `reasoningEffort` is honored.
- **Measured per run:** pass/fail from the hidden check, input/output/reasoning tokens and cost summed from `step_finish` events, wall time, the lane the plugin chose.

```bash
python3 bench/run.py run --tasks F2 --conditions none,enforce          # smoke
python3 bench/run.py run --tasks F1,F2,F3,F4,F5 --conditions none,always-low,advisory,enforce,enforce-low --repeat 3  # exp2: 75 runs
python3 bench/run.py run --repeat 3                                    # all current conditions: 15 × 6 × 3 = 270 runs
python3 bench/run.py worker-switch --out bench/results/worker-switch.jsonl  # fresh worker chosen by lane
python3 bench/run.py summarize bench/results/<file>.jsonl
```

## Predictions — written before the first run (2026-09-08)

If the router earns its place, these hold. If they do not, the router is not worth its hook.

| # | Prediction | Why |
|---|---|---|
| P1 | On fast and daily tasks, `enforce` uses fewer reasoning tokens than `always-high`, with no pass-rate loss | That saving is the router's entire value on easy prompts |
| P2 | On critical tasks, `enforce` passes at least as often as any other condition | Critical maps to high; the router must never make security work worse |
| P3 | The plugin routes at least 85% of tasks to the labeled lane | 15 short English prompts; the keyword tables were built for this shape |

Expected non-results, stated up front: on fast/daily tasks `enforce` should look like `none` (both medium); on deep/critical tasks `enforce` should look like `always-high`. `advisory` differs from `none` only by the injected context, so any token difference there is context cost, not routing.

## Experiment 2 result — fast default decided

The sealed 75-run experiment completed on 2026-09-08: 5 fast tasks × 5 conditions × 3 repeats,
75/75 passed. `enforce-low` reduced mean reasoning from 60.3 to 30.3 tokens (-49.8%) versus the
then-current `enforce=medium`, with equal 15/15 pass rates. Case A changed the product's fast
per-prompt default to `low`; Codex and Claude profile targets remain medium because this experiment
covered one OpenCode provider. `enforce-low` remains in the runner as the historical experiment
condition and is now equivalent to the product default. See `results/exp2-fastlane-20260908.md`.

## Experiment 3 result — fresh-worker selection

The sealed worker-switch smoke ran Fast, Deep, and Critical tasks three times each. The classifier
selected Luna for all three Fast runs and Kimi for all six Deep/Critical runs; all 9/9 hidden checks
passed with no provider error or timeout. This proves selection across fresh sessions, not hot-swapping
a running parent, and it is not a same-task model-performance A/B. See
`results/exp3-opencode-worker-switch-20260909.md`.

## Experiment 4 result — same-task FAST model A/B

Five FAST tasks ran three times each on both usable configured workers. Luna and Kimi both passed
15/15; Luna used 76.8% less OpenCode Go allowance-equivalent event cost and 48.2% less total wall
time. The configured DeepSeek scout was excluded after an unretryable region-opt-in 403. Token
totals are descriptive because provider tokenizers and cache accounting differ. See
`results/exp4-fast-model-ab-20260909.md`.

## What this does not measure

Other harnesses' skills, long multi-turn sessions, models that ignore `reasoningEffort`, or Codex/Claude Code (where the hook is advisory by design). Results are one machine, one model version, one day; the results file records all three.
