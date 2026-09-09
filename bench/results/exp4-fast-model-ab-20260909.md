# Experiment 4 — OpenCode FAST worker A/B

Date: 2026-09-09. Matrix: five seeded FAST tasks × three repeats × two usable OpenCode Go models = 30 fresh, plugin-free sessions. The tasks, decision rule, and boundaries were sealed in `docs/goals/GOAL-opencode-fast-model-ab.md` before these runs.

## Verdict

**PASS — use GPT-5.6 Luna for OpenCode FAST/Daily scouts and retain Kimi K2.7 Code for Deep/Critical implementation.** Both models passed every hidden check. On these FAST tasks, Luna used 76.8% less Go allowance-equivalent event cost and 48.2% less total wall time.

| Model | Pass | Input | Cache read | Cache write | Output | Reasoning | Event cost | Total wall | Median run |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `opencode-go/gpt-5.6-luna` | 15/15 | 129 | 596,266 | 326,676 | 2,493 | 635 | $0.09738 | 119.8 s | 7.8 s |
| `opencode-go/kimi-k2.7-code` | 15/15 | 280,685 | 726,528 | 0 | 1,798 | 2,124 | $0.42038 | 231.4 s | 15.1 s |
| Luna change vs Kimi | equal | — | — | — | +38.7% | **-70.1%** | **-76.8%** | **-48.2%** | **-48.3%** |

The reported input and cache shapes differ sharply because the providers use different APIs, tokenizers, and cache accounting. Adding the reported input/cache counters gives 923,071 for Luna and 1,007,213 for Kimi (-8.4%), but that total is descriptive rather than a portable model-quality score. Pass rate, event cost, and wall time are the decision metrics.

## Availability preflight

The configured `opencode-go/deepseek-v4-flash` scout failed before the A/B with unretryable HTTP 403: its latest serving path requires explicit opt-in to China hosting. The sanitized record is `exp4-deepseek-preflight-20260909.json`. No provider opt-in was performed.

After the configuration change, a real Kimi parent used OpenCode's `task` tool to invoke the
`explore` subagent. Tool metadata and exported sessions identified the child as
`opencode-go/gpt-5.6-luna`; both returned the expected project version `0.4.2`. The sanitized record
is `exp4-delegation-smoke-20260909.json`.

## Subscription boundary

Both tested IDs use the `opencode-go` provider. Their calls consume OpenCode Go's separate allowance, not a ChatGPT or Codex subscription quota. OpenCode documents Go as a separate $10/month subscription with dollar-valued five-hour, weekly, and monthly limits. At the published typical-request mix, it estimates 2,050 requests per five hours for Luna and 1,350 for Kimi K2.7 Code; actual usage varies.

## Catalog context at test time

OpenCode's current metadata listed Luna at $0.20 input / $0.02 cached read / $0.25 cached write / $1.20 output per million tokens with a 1.05M context window. Kimi K2.7 Code was $0.95 / $0.19 / no cache-write price / $4.00 with a 262,144-token context window. These catalog prices explain the event-cost direction but do not replace the same-task run.

Sources: [OpenCode Go limits and model prices](https://dev.opencode.ai/docs/go/), [OpenCode model selection and variants](https://opencode.ai/v2/docs/models), [official GPT-5.6 Luna specification](https://developers.openai.com/api/docs/models/gpt-5.6-luna).

## Boundary

This is a small FAST-task model A/B on one machine and one day. It does not show that Luna is better for Deep/Critical tasks, that a running parent can hot-swap models, or that the harness itself reduces ChatGPT/Codex subscription use. The quota saving comes from dispatching work to the separate OpenCode Go provider; the harness supplies the deterministic lane decision.

Raw rows: `exp4-fast-luna-20260909.jsonl` and `exp4-fast-kimi-20260909.jsonl`.
