# Validation evidence

Last updated: 2026-09-09 (Asia/Seoul). Local versions at the time: OpenCode 1.18.18 (plugin SDK 1.17.11), OpenClaw 2026.3.13, Hermes Agent v0.21.0 (2026.8.31), Python 3.14, Node 24.

## Automated checks (`bash scripts/check.sh`)

| Check | Result | Evidence |
|---|---|---|
| Classification matrix | PASS | 47 English/Korean prompts across four lanes |
| Hook contracts | PASS | `UserPromptSubmit` → `additionalContext`; `pre_llm_call` (Hermes shell hook shape) → `{"context"}`; other events emit nothing |
| Fail-open boundary | PASS | malformed JSON, `null`, string, array, empty object exit 0 with no output |
| Config boundary | PASS | malformed config, unknown lane names, non-integer limits are ignored; global config overridden by project config; keywords merge |
| Project floor | PASS | raises `explain` to deep; never lowers; explicit lane request wins; safety wins over both |
| Plugin CLI shape | PASS | `--classify --json --runtime openclaw` carries lane, effort, targets, context; legacy `--classify` output unchanged |
| OpenCode plugin contract | PASS | plain Node: synthetic part appended, not re-classified, enforcement off by default, `reasoningEffort` set only when enabled, missing router fails open |
| OpenClaw plugin contract | PASS | plain Node: `prependContext` returned, override only with `enforce` and a lane model, `provider/model` split, missing router fails open |
| Hermes plugin contract | PASS | `register` binds `pre_llm_call`; context injected; empty message and missing router return `None` |
| Harness audit script | PASS | fixture project: ALIVE/LINKED/DEAD verdicts, archived skills excluded, subdirectory sessions counted, idle project flagged |
| Installer | PASS | five runtime homes, shared router, installed OpenCode plugin resolves it without env, pre-rename hook entries converge to one Model Orchestrator handler, skill trees copied whole, scaffold never overwrites, unknown skill/runtime, malformed settings, missing Node, and Node 18 abort before any write; idempotent; paths with spaces |
| WSL userland boundary | PASS | current branch copied into a clean `node:22-bookworm-slim` container; Debian 12, Bash 5.2, Python 3.11, Node 22.23 ran all 28 tests, plugin contracts, five-runtime installer, and docs gates |
| Docs gate | PASS | ten break tests; the gate also runs on this repository and the scaffold copy must be byte-identical |
| Skill schemas | PASS | ten `SKILL.md` folders: frontmatter, `## Next` baton, no TODO, single-line `metadata` rule for OpenClaw |

## Live-runtime evidence (2026-09-07/08, one machine)

| Runtime | What ran | Result |
|---|---|---|
| Claude Code | isolated `CLAUDE_CONFIG_DIR` and plugin cache; `claude plugin validate --strict .`, local marketplace add, install, list, and details | Validation passed; plugin status **enabled**; inventory reported 10 skills, 4 agents, and 1 `UserPromptSubmit` hook. No subscription or model call was needed |
| OpenCode | 2026-09-09 renamed plugin installed at `~/.config/opencode/plugins/model-orchestrator.js`; `opencode run -m opencode-go/gpt-5.6-luna` with `MODEL_ORCHESTRATOR_DEBUG` | model returned exactly **`MODEL ORCHESTRATOR LIVE`**; `chat.message` recorded lane=fast and `chat.params` recorded effort=low, enforcement off |
| OpenCode | pre-rename v0.3 live context run on `opencode-go/kimi-k2.7-code` | `chat.message` and `chat.params` fired, and the model echoed `LANE=FAST EFFORT=MEDIUM`; retained as historical evidence for the unchanged adapter contract |
| OpenCode | same with `MODEL_ORCHESTRATOR_ENFORCE=1` | `chat.params` set `reasoningEffort`; the provider accepted the call without error. Whether that provider honors the field is not measured here |
| OpenClaw | renamed global plugin install followed by `openclaw plugins doctor` | Model Orchestrator discovered from one global path; **No plugin issues detected** after the stale pre-rename entry and duplicate local load path were removed |
| OpenClaw | `openclaw agent --local --agent main -m "lane=fast reply OK"` | `before_model_resolve` fired with lane=fast; the turn then failed at the model (no provider credentials on this machine), so `before_prompt_build` was verified offline only |
| Hermes | plugin copied to `~/.hermes/plugins/model-orchestrator`, `hermes plugins enable`, `hermes plugins doctor model-orchestrator --ci` | "runtime discovery, manifest parsing, import, and registration passed; 1 hook(s)" |
| Hermes | shell hook `hooks.pre_llm_call` → router, `hermes hooks test pre_llm_call` | exit 0 in 0.106 s; Hermes parsed `{"context": "[MODEL ORCHESTRATOR] lane=DAILY …"}` as its wire shape |
| Codex | persisted threads with `-p effort-daily` / `-p effort-deep`; built-in `explorer` delegation | `gpt-5.6-terra/medium`, `gpt-5.6-sol/high`; `BUILTIN_EXPLORER_OK` (v0.1 evidence, unchanged) |

## Benchmark pilot (2026-09-08)

`bench/run.py`, `opencode-go/gpt-5.6-luna`, 15 tasks × 4 conditions, one repeat. Full table and interpretation in `bench/results/pilot-1.md`.

| Prediction | Verdict |
|---|---|
| P1 fast lane saves reasoning under enforce vs always-high | FAIL — router added reasoning tokens on this provider (46 → 153) |
| P2 critical pass rate does not drop under enforce | PASS — 5/5, matching always-high, 4% cheaper |
| P3 ≥85% of tasks routed to the labeled lane | FAIL at 10/15; keyword fix and precedence rule brought the offline check to 15/15 and 47 matrix cases pass |

## Benchmark experiment 2 (2026-09-08)

After an unchanged `opencode-go/gpt-5.6-luna` access smoke returned `OK`, the sealed fast-lane
experiment ran 5 tasks × 5 conditions × 3 repeats. All 75 rows passed with no timeout, fatal provider
error, or malformed event stream.

| Condition | Pass | Mean reasoning | Total cost | Median wall |
|---|---:|---:|---:|---:|
| none | 15/15 | 46.3 | $0.09519 | 9.3 s |
| always-low | 15/15 | 32.7 | $0.09475 | 8.2 s |
| advisory | 15/15 | 53.4 | $0.09993 | 8.7 s |
| enforce (medium) | 15/15 | 60.3 | $0.10076 | 8.7 s |
| enforce-low | 15/15 | 30.3 | $0.09882 | 7.9 s |

The pre-sealed rule selected Case A: `enforce-low` reduced mean reasoning 49.8% with no pass loss,
so the fast per-prompt effort default changed from `medium` to `low`. Total cost fell 1.9%; the result
does not establish a universal saving outside this model, provider, fixture, and day. Raw evidence and
the full interpretation are in `bench/results/exp2-fastlane-20260908.jsonl` and `.md`.

Across the 15 `enforce=medium` and 15 `enforce-low` rows, input plus cache-read counters fell 6.2%,
output fell 11.7%, reasoning fell 49.8%, cost fell 1.9%, and median wall time fell 9.2%. Against no
router, however, `enforce-low` used 17.7% more input plus cache-read and cost 3.8% more. All sides
passed 15/15. This is why the README exposes both comparisons instead of a reasoning-only headline.

## Fresh-worker selection experiment (2026-09-09)

After Gemini CLI and OpenCode Zen Gemini were unavailable through the user's existing credentials,
the fallback used two confirmed OpenCode Go workers. The deterministic classifier selected
`gpt-5.6-luna` for Fast and `kimi-k2.7-code` for Deep/Critical, then launched a fresh isolated session.
The Fast → Deep → Critical sequence ran three times: 9/9 hidden checks passed, with zero event error,
timeout, or fatal provider error. This verifies lane-selected fresh workers, not a hot parent-model
swap or a cost advantage. Raw rows and totals are in
`bench/results/exp3-opencode-worker-switch-20260909.{jsonl,md}`.

## Same-task OpenCode FAST model A/B (2026-09-09)

Five FAST tasks ran three times each in fresh plugin-free sessions on both GPT-5.6 Luna and Kimi
K2.7 Code. Both passed 15/15. Luna's OpenCode Go event cost was $0.09738 versus Kimi's $0.42038
(-76.8%), and total wall time was 119.8 versus 231.4 seconds (-48.2%). Reasoning tokens were 635
versus 2,124, but cross-provider token counters are descriptive because tokenizers and cache
accounting differ. A preflight of the previously configured DeepSeek V4 Flash scout failed with an
unretryable region-opt-in HTTP 403, so the user-level OpenCode small/explore/handoff references were
changed to Luna; Kimi remains the default and implementation worker. See
`bench/results/exp4-fast-model-ab-20260909.md`.

A post-change runtime smoke then used a real Kimi parent to call the `explore` subagent. OpenCode
task metadata and both exported sessions identified the child as Luna, and parent/child both returned
the expected `0.4.2`. The sanitized record is
`bench/results/exp4-delegation-smoke-20260909.json`.

## Context compaction assessment (2026-09-08)

No automatic finish hook was added. Claude Code already has auto/manual compact and clear boundaries.
In one private Codex thread, nine compact events reduced median next-call input from 228,079 to 23,392
tokens (-89.7%), and all nine next tasks completed without a recorded error. The events do not label
manual versus automatic triggers, the transcript stays private, fact retention was not graded, and no
billing reduction is claimed. Method, limits, and the compact/clear decision rule are in
`docs/evidence/CONTEXT-MANAGEMENT.md`.

## Failures kept as evidence

1. (v0.1) The first live large-task trial selected Critical and attempted a custom Codex agent that the running CLI reported unavailable; built-in fallback agents worked. Automatic hints now use built-in roles.
2. (v0.1) Non-object JSON could crash the original hook; duplicate malformed handlers could survive installation. Both have regression coverage.
3. (v0.3) The first `opencode run` against `opencode-go/deepseek-v4-flash` died with a region opt-in error before the model answered — the hooks had already fired, which is how the plugin's fail-open path was first observed for real.
4. (v0.3) A foreground `opencode run` produced no output for two minutes; the same command detached with `nohup` completed in 8 s. Cause not identified; recorded so the next person does not chase it.
5. (v0.3) Loading the router with `importlib.util.spec_from_file_location` on Python 3.14 raised inside `@dataclass` until the module was placed in `sys.modules` first. The Hermes loader now does this; the unit tests already did.
6. (v0.3) The docs gate, on its first run against this repository, failed on a real stray file in `docs/`. It was moved, not whitelisted.
7. (bench) The first pilot was stopped at 4/60 because this machine's personal global config (default lane deep) leaked into the runs. The router gained `MODEL_ORCHESTRATOR_CONFIG` so the benchmark isolates itself; the 4 contaminated rows were discarded.
8. (bench) Prediction P1 failed: on `gpt-5.6-luna` the fast lane's `reasoningEffort=medium` and the injected guidance both cost more reasoning than the provider default. Recorded as a hypothesis for the next single-axis run, not patched on the same data.
9. (platform) A clean Ubuntu 24.04 container with its default Node 18 passed the Python tests but failed loading the installed OpenCode ESM plugin. Repeating the same source and checks with Node 22 passed, so Node 22 is now an explicit prerequisite rather than a guessed compatibility floor.
10. (bench) Experiment 2 first produced 30 unusable HTTP 401 rows. After a separate one-task access smoke succeeded, the original conditions and model were resumed in a new file; blocked rows remain excluded.
11. (distribution) A fresh public GitHub marketplace add succeeded, but install rejected `agents: "./claude/agents/"`: the current CLI requires manifest entries to end in `.md`. Pointing at individual files passed schema validation but exposed a second defect: explicitly declaring the standard `hooks/hooks.json` loaded it twice and disabled the plugin.
12. (distribution) Both custom declarations were removed in favor of Claude's standard `agents/` and `hooks/hooks.json` auto-discovery. A fresh isolated local marketplace install then loaded as enabled with the exact 10-skill, 4-agent, 1-hook inventory.

## What this does not prove

- That the lane→effort mapping is optimal for any workload. Defaults are starting points.
- That a hook changes the active parent model in Codex or Claude Code; it does not.
- That OpenClaw's `before_prompt_build` injects in a live turn on this machine; no model credentials were available. The hook type and return shape were verified from the SDK typings and in plain Node.
- That the public GitHub marketplace path contains the fixes before this branch is pushed and checked from a fresh clone. The equivalent local-source marketplace path is verified end to end without a model call.
- That any provider changes its reasoning when OpenCode passes `reasoningEffort`; only that the call is accepted.
- That native Git Bash, PowerShell, Command Prompt, or Windows-host path interoperability works. The supported Windows boundary is the Linux userland inside WSL 2.
- That OpenCode can hot-swap the model used by the current provider turn; experiment 3 launched a fresh session after classification.

Future measurements should record task fixture, model version, effort, wall time, token use, pass/fail rubric, and repeated trials.
