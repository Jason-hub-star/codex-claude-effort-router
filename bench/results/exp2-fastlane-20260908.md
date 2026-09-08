# Experiment 2 — fast-lane effort

`opencode-go/gpt-5.6-luna`, OpenCode 1.18.18, one machine: 5 fast tasks × 5 conditions × 3 repeats =
75 runs. All 75 passed. Raw rows are in `exp2-fastlane-20260908.jsonl`; the earlier blocked 30-row
file contains provider failures only and is not part of this result.

## Result

| Condition | Pass | Mean reasoning | Median reasoning | Total cost | Median wall |
|---|---:|---:|---:|---:|---:|
| none | 15/15 | 46.3 | 37 | $0.09519 | 9.3 s |
| always-low | 15/15 | 32.7 | 24 | $0.09475 | 8.2 s |
| advisory | 15/15 | 53.4 | 43 | $0.09993 | 8.7 s |
| enforce (medium) | 15/15 | 60.3 | 48 | $0.10076 | 8.7 s |
| enforce-low | 15/15 | 30.3 | 30 | $0.09882 | 7.9 s |

All 30 plugin-routed rows agreed with the fast label. There were no timeouts, fatal provider errors,
or verification failures. The matrix cost $0.48945 and used 752.9 seconds of summed wall time.

## Sealed decision

**Case A applies.** `enforce-low` reasoning was 49.8% lower than `enforce=medium`, and both passed
15/15. The fast per-prompt effort default therefore changes from `medium` to `low`.

- Case D does not apply: advisory was 15% above none, below the sealed >25% context-cost threshold.
- Case E applies: always-low used 32.7 mean reasoning tokens versus none at 46.3, so this provider's
  default sat above low during the experiment.

## Limits

- One provider, model, machine, day, and deliberately small fast-task fixture.
- Reasoning fell 49.8%, but total condition cost fell only 1.9%; do not market this as a 50% bill cut.
- This does not justify lowering Codex or Claude profile effort. Their targets remain medium pending
  separate same-model workload A/B.
- The decision rule was sealed before data in `docs/goals/GOAL-fast-lane-effort.md`.

## Next

Do not tune against these same results. Complete the README truth pass and actual WSL 2 fresh-clone
verification before a patch release.
