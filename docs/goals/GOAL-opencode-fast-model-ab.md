# Goal — choose the OpenCode FAST worker with same-task evidence

One line: compare the two usable configured workers on the same five FAST tasks, then replace the unavailable global scout model only if the candidate preserves all hidden-check passes.

## Outcome

Run `F1`–`F5` three times each with fresh, plugin-free OpenCode sessions under GPT-5.6 Luna and Kimi K2.7 Code. Record pass rate, input/cache/output/reasoning tokens, event cost, and wall time.

## Verification

```bash
python3 bench/run.py run --model opencode-go/gpt-5.6-luna \
  --conditions none --tasks F1,F2,F3,F4,F5 --repeat 3 \
  --out bench/results/exp4-fast-luna-20260909.jsonl
python3 bench/run.py run --model opencode-go/kimi-k2.7-code \
  --conditions none --tasks F1,F2,F3,F4,F5 --repeat 3 \
  --out bench/results/exp4-fast-kimi-20260909.jsonl
bash scripts/check.sh
```

Each result must contain 15 completed rows and no timeout, fatal provider error, or malformed event stream. A preflight against the configured DeepSeek V4 Flash scout is retained as availability evidence even though it cannot enter the A/B after an unretryable HTTP 403.

## Decision rule

- Prefer Luna for `small_model`, `explore`, `handoff`, and the harness Fast/Daily worker only if Luna passes 15/15 and does not trail Kimi's pass count.
- Keep Kimi K2.7 Code for Deep/Critical and implementation; this experiment does not attempt to replace it there.
- If Luna and Kimi tie on correctness, compare event cost first and median wall time second. Token totals are descriptive, not the sole decision, because provider tokenizers and cache reporting differ.
- Do not add a production automatic-switch hook in this experiment.

## Constraints

- Same fixture, prompts, hidden checks, machine, OpenCode version, and `none` condition for both arms.
- Fresh session and fresh fixture copy per row.
- Do not tune prompts, checks, effort, models, or the decision rule after seeing results.
- OpenCode Go event `cost` is allowance-equivalent accounting, not a credit-card billing statement.

## Boundaries

- Allowed: benchmark results and summaries, status/evidence docs, and the user-level OpenCode model references if the sealed rule passes.
- Forbidden: provider opt-in, billing changes, Gemini/Grok credentials, production auto-switch hooks, or unrelated repository code.

## Blocked stop

Stop an arm on the first unretryable 401/402/403 or repeated timeout. Report the incomplete matrix instead of substituting another model.

## Execution log

- 2026-09-09: sealed before the Luna/Kimi A/B. Preflight evidence: configured `opencode-go/deepseek-v4-flash` failed again with unretryable HTTP 403 because the latest model requires explicit China-hosting opt-in.
- 2026-09-09: PASS. Luna and Kimi both passed 15/15. Luna reduced Go allowance-equivalent event cost 76.8% and total wall time 48.2%, so the sealed rule selects Luna for the OpenCode small/scout roles while retaining Kimi for implementation.
- 2026-09-09: Runtime configuration smoke passed. A Kimi parent delegated through the `task` tool to `explore`; OpenCode metadata and exported sessions reported the child model as Luna, and both returned `0.4.2`.
