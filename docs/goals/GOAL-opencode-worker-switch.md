# Goal — verify lane-selected OpenCode workers

One line: prove that the repository classifier can select and launch a fresh OpenCode worker per lane, with the selected model recorded and every seeded task passing its hidden check.

## Outcome

Run `F2`, `D1`, and `C1` three times each. The classifier must select Luna for Fast and Kimi for Deep/Critical, and all nine fresh workers must pass.

## Verification

```bash
python3 bench/run.py worker-switch \
  --tasks F2,D1,C1 --repeat 3 \
  --out bench/results/exp3-opencode-worker-switch-20260909.jsonl
python3 tests/test_bench.py
bash scripts/check.sh
```

The JSONL must contain nine rows, zero timeouts/fatal errors, the sealed lane/model pairs, and token, cost, wall-time, and pass fields.

## Constraints

- The router classifies the prompt; task labels do not choose the worker.
- Each task starts a fresh OpenCode session. This experiment does not claim hot parent-model switching.
- Do not change the experiment map after seeing results.
- Do not interpret subscription-equivalent cost as a billing statement.

## Boundaries

- Allowed: `bench/run.py`, its focused test, this goal, result and status/evidence documents.
- Forbidden: production plugins, global runtime config, target repositories, Gemini/Grok billing or credentials.
- Sealed map: Fast/Daily → `opencode-go/gpt-5.6-luna`; Deep/Critical → `opencode-go/kimi-k2.7-code`.

## Iteration policy

Fix only runner or parser defects that prevent measurement. Preserve model failures as data; do not tune prompts, models, lanes, or checks against this run.

## Blocked stop

Stop on the first 401/402/403 provider failure, malformed event stream, or repeated timeout. Report the incomplete matrix instead of substituting a model.

## Execution log

- 2026-09-09: sealed before model runs. Gemini CLI returned `UNSUPPORTED_CLIENT`; OpenCode Zen Gemini returned HTTP 401 insufficient balance. Those infrastructure probes are excluded. OpenCode Go Luna and Kimi exact-response smokes both passed.
- 2026-09-09: PASS. Nine of nine fresh workers passed their hidden checks with the sealed lane/model pairs, zero event errors, zero timeout, and zero fatal provider error. Raw rows and totals are in `bench/results/exp3-opencode-worker-switch-20260909.{jsonl,md}`.
