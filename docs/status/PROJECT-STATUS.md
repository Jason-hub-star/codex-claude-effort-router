# Project status

## Now
- v0.3.0 shipped 2026-09-08: five runtimes, ten skills, docs gate. Decision sheet archived under `docs/archive/`.

## Next action
- Restore or replace access to the blocked OpenCode Go account, prove it with one task, then resume benchmark experiment 2 unchanged. Do not interpret the 30 provider-failure rows as model results.

## Open decisions
- none

## Log
| Date | Change | Evidence |
|---|---|---|
| 2026-09-07 | Phase 1 router config file, project floor, `--json --runtime` output | 11 router tests |
| 2026-09-07 | Phase 2 OpenCode plugin | live run: model echoed `LANE=FAST EFFORT=MEDIUM` |
| 2026-09-07 | Phase 3 OpenClaw plugin | `openclaw plugins doctor` clean; `before_model_resolve` fired live |
| 2026-09-07 | Phase 4 Hermes plugin + shell hook | `hermes plugins doctor` OK; `hermes hooks test pre_llm_call` parsed context |
| 2026-09-07 | Phase 5 skills decision-sheet, absorb, harness-audit | audit script tests; real project smoke |
| 2026-09-07 | Phase 6 docs gate + scaffold; repo docs restructured | `tests/test_docs_gate.sh` |
| 2026-09-08 | Phase 7 installer for five runtimes, manifests, README, rename to effort-lanes, v0.3.0 | `bash scripts/check.sh` |
| 2026-09-08 | Benchmark pilot 1 (60 runs): P2 pass, P1/P3 fail; routing gaps fixed offline 15/15 | `bench/results/pilot-1.md` |
| 2026-09-08 | Benchmark experiment 2 stopped before evidence: 30/30 attempts hit unretryable OpenCode Go HTTP 401; runner now aborts account failures after one row | `bench/results/exp2-fastlane-BLOCKED.jsonl` |
| 2026-09-08 | Windows boundary fixed at WSL 2 Ubuntu/Debian; Git Bash/PowerShell/CMD unsupported. Clean Debian 12 + Node 22 full suite passed; Node 18 failure retained | `tests/test_wsl_container.sh`, `docs/evidence/VALIDATION.md` |
