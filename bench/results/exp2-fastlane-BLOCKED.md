# Experiment 2 — blocked before measurement

Date: 2026-09-08  
Planned matrix: 5 fast tasks × 5 conditions × 3 repeats = 75 runs  
Usable rows: 0

The run did not measure fast-lane performance. All 30 attempted rows ended before a model step
with an unretryable HTTP 401 from the OpenCode Go provider (`account blocked`). Every row has
zero input, output, and reasoning tokens, so none may be used in the sealed decision rule.

Two early attempts also exposed the old timeout defect: a descendant kept the captured output
pipe open, allowing individual rows to last 165.1 and 843.5 seconds. Commit `8bc80a7` replaced
the pipe with a log file and kills the whole process group at the deadline. The follow-up guard
now aborts the full matrix on the first 401, 402, or 403 instead of producing more invalid rows.

Resume only after this one-task smoke produces a real model step:

```bash
python3 bench/run.py run --tasks F2 --conditions none --out bench/results/exp2-provider-smoke.jsonl
```

Then rerun the sealed command with the same model and conditions:

```bash
python3 bench/run.py run --tasks F1,F2,F3,F4,F5 \
  --conditions none,always-low,advisory,enforce,enforce-low --repeat 3 \
  --out bench/results/exp2-fastlane.jsonl
```

Changing the provider or model is a new experiment, not a continuation of experiment 2.
