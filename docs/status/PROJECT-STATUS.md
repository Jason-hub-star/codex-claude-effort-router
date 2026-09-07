# Project status

## Now
- v0.3.0 shipped 2026-09-08: five runtimes, ten skills, docs gate. Decision sheet archived under `docs/archive/`.

## Next action
- Launch: publish the OpenCode enforcement demo GIF and post once (HN, r/ClaudeAI, X); first gate is 100 stars in 30 days.

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
