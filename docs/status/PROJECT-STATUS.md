# Project status

## Now
- v0.3.0 shipped 2026-09-08: five runtimes, ten skills, docs gate. Decision sheet archived under `docs/archive/`.

## Next action
- Run the actual WSL 2 fresh-clone gate, then push and repeat the Claude marketplace install from the public GitHub source before a patch release. Experiment 2 is decided; do not rerun it to tune the same result.

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
| 2026-09-08 | OpenCode Go access restored: a pure `gpt-5.6-luna` smoke returned exactly `OK` in 5.3 s at $0.00528; sealed 75-run experiment 2 approved to resume without changing model or conditions | live OpenCode JSON event stream; `docs/goals/GOAL-fast-lane-effort.md` |
| 2026-09-08 | Experiment 2 completed 75/75 without errors. `enforce-low` cut mean reasoning 60.3→30.3 (-49.8%) versus medium with equal 15/15 pass rate; sealed Case A changed only the fast per-prompt effort default to low | `bench/results/exp2-fastlane-20260908.{jsonl,md}` |
| 2026-09-08 | README truth pass removed stale speed/size/demo claims, aligned the 47-case and 270-run counts, and made evidence limits explicit. A real Claude marketplace attempt found two manifest defects; standard-path auto-discovery fixed both, and an isolated local install loaded 10 skills, 4 agents, and 1 hook as enabled. Node 22 is now enforced before installer writes | `README.md`, `README.ko.md`, `.claude-plugin/plugin.json`, `tests/test_installer.sh`, `docs/evidence/VALIDATION.md` |
| 2026-09-08 | Token evidence moved to the README front: same-harness low cut input+cache 6.2% and cost 1.9%, but still cost 3.8% more than no router on the fast fixture. Auto compact/clear at finish was rejected: existing runtime compaction plus a persisted checkpoint is safer. A private Codex-log sample recorded 9/9 next-task completion after compact but did not grade fact retention | `bench/results/exp2-fastlane-20260908.{jsonl,md}`, `docs/evidence/CONTEXT-MANAGEMENT.md` |
