# Pilot 1 — 2026-09-08

`opencode-go/gpt-5.6-luna`, OpenCode 1.18.18, one machine, one repeat: 15 tasks × 4 conditions = 60 runs, 58 passed. Raw rows in `pilot-1.jsonl`. Predictions were written in `bench/README.md` before the first run.

| lane | condition | pass | input+cache | output | reasoning | cost $ | wall s |
|---|---|---:|---:|---:|---:|---:|---:|
| fast | none | 5/5 | 38040 | 161 | 46 | 0.0064 | 8.7 |
| fast | always-high | 5/5 | 42280 | 181 | 80 | 0.0065 | 9.9 |
| fast | advisory | 5/5 | 42585 | 207 | 102 | 0.0067 | 11.1 |
| fast | enforce | 5/5 | 42559 | 208 | 153 | 0.0069 | 10.8 |
| deep | none | 5/5 | 209019 | 1667 | 429 | 0.0132 | 37.0 |
| deep | always-high | 5/5 | 215527 | 1853 | 1075 | 0.0148 | 46.0 |
| deep | advisory | 5/5 | 209991 | 1774 | 376 | 0.0134 | 36.1 |
| deep | enforce | 4/5 | 186748 | 1588 | 866 | 0.0134 | 40.2 |
| critical | none | 4/5 | 191411 | 1675 | 488 | 0.0129 | 38.4 |
| critical | always-high | 5/5 | 262115 | 2342 | 1506 | 0.0172 | 64.8 |
| critical | advisory | 5/5 | 270482 | 2219 | 679 | 0.0162 | 49.3 |
| critical | enforce | 5/5 | 243404 | 2167 | 1487 | 0.0165 | 55.5 |

Cost per full task set: none 0.0325, advisory 0.0363, enforce 0.0368, always-high 0.0385.

## Predictions

| # | Prediction | Verdict | Evidence |
|---|---|---|---|
| P1 | fast/daily: `enforce` reasons less than `always-high`, no pass loss | **FAIL** | fast reasoning: none 46 < always-high 80 < advisory 102 < enforce 153. Pass 5/5 everywhere |
| P2 | critical: `enforce` passes at least as often as any condition | PASS | critical 5/5 under enforce, advisory, always-high; 4/5 under none (C5 file-mode task) |
| P3 | ≥85% of tasks routed to the labeled lane | **FAIL** | 10/15 (advisory and enforce identical, 20/30 rows) |

## What the failures say

**P1 — on this model the fast lane is a cost, not a saving.** The provider default already reasons very little on trivial prompts (46 tokens). Two things add on top: the injected routing context itself (advisory: +56 reasoning tokens, +$0.0003) and an explicit `reasoningEffort=medium` (enforce: +107). "Medium" is not the provider's default here; the default is below medium. The router's value on easy prompts was assumed, not measured, and the assumption was wrong for this provider.

Hypotheses for the next single-axis experiments, not applied yet:
1. Fast lane enforces `low` (or `minimal`) instead of `medium`.
2. The fast lane injects a one-line context without the delegation guidance.

**P3 — the keyword tables missed 5 of 15 short English task prompts.** Misses: F1 "How many .py files" → daily, F3 "Fix the typo" → deep (`fix` outranks `typo`), F5 "Which file defines" → daily, D3 "Make it raise ValueError, add a test" → daily, D5 "`todo.cli list` crashes" → fast (`list` matched). Routing is deterministic, so this axis is fixed and re-measured offline (`python3 bench/run.py route`), without model runs.

**Two single failures, n=1 each, recorded not interpreted:** D4 (refactor) failed only under `enforce` — the model left two `json.dump` call sites; C5 (0600 file mode) failed only under `none`. Three repeats are needed before either says anything about effort.

## What held

- Enforce behaves as designed: deep/critical reasoning under `enforce` (866 / 1487) tracks `always-high` (1075 / 1506), fast tracks the medium setting.
- Critical tasks under `enforce` matched `always-high` on pass rate at 4% lower cost; versus `none`, enforce fixed the one critical miss for 13% more cost on that lane.
- Every critical prompt routed to critical (5/5): the safety keywords are the strongest part of the table.

## Next

1. Fix P3 offline (keywords + precedence), add the 15 prompts to `tests/cases.json`, re-run `route`.
2. Run `--repeat 3` with the fast lane at `low` to test hypothesis 1 — one axis.
3. Only then compare against `claude-model-router-hook` on the same 15 prompts (lane agreement) and consider a second model.
