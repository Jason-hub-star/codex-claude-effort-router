# Experiment 3 — lane-selected fresh OpenCode workers

Date: 2026-09-09. Matrix: three seeded tasks × three repeats = nine fresh OpenCode sessions. The model map and gates were sealed in `docs/goals/GOAL-opencode-worker-switch.md` before these runs.

## Verdict

**PASS — the classifier selected and launched the sealed worker for all nine runs.** Every hidden task check passed; there were no provider errors, malformed event streams, or timeouts.

| Lane / task | Selected worker | Runs | Pass | Input | Cache read | Cache write | Output | Reasoning | Cost | Median wall |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Fast / F2 | `opencode-go/gpt-5.6-luna` | 3 | 3/3 | 27 | 127,085 | 64,200 | 347 | 81 | $0.01911 | 8.3 s |
| Deep / D1 | `opencode-go/kimi-k2.7-code` | 3 | 3/3 | 71,924 | 322,816 | 0 | 2,559 | 460 | $0.14174 | 31.4 s |
| Critical / C1 | `opencode-go/kimi-k2.7-code` | 3 | 3/3 | 78,967 | 787,712 | 0 | 4,358 | 1,925 | $0.24981 | 66.2 s |
| **Total** | — | **9** | **9/9** | **150,918** | **1,237,613** | **64,200** | **7,264** | **2,466** | **$0.41066** | — |

The sequence was Fast → Deep → Critical, repeated three times. Each Fast task returned to Luna and each Deep/Critical task selected Kimi. Selection used the router's classification result, not the benchmark label.

## Boundary

This proves **fresh-worker selection**, not a hot model swap inside a running parent session. The three tasks have different difficulty, so their costs must not be compared as a model-performance A/B. A cost or quality claim needs the same task under fixed-worker and routed-worker conditions.

Gemini was excluded after infrastructure probes: Gemini CLI 0.46.0 returned `UNSUPPORTED_CLIENT`, and OpenCode Zen Gemini returned HTTP 401 for insufficient balance. Grok was not called because no subscription or API budget was authorized.
