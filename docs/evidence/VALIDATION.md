# Validation evidence

Last updated: 2026-09-08 (Asia/Seoul). Local versions at the time: OpenCode 1.18.18 (plugin SDK 1.17.11), OpenClaw 2026.3.13, Hermes Agent v0.21.0 (2026.8.31), Python 3.14, Node 24.

## Automated checks (`bash scripts/check.sh`)

| Check | Result | Evidence |
|---|---|---|
| Classification matrix | PASS | 32 English/Korean prompts across four lanes |
| Hook contracts | PASS | `UserPromptSubmit` → `additionalContext`; `pre_llm_call` (Hermes shell hook shape) → `{"context"}`; other events emit nothing |
| Fail-open boundary | PASS | malformed JSON, `null`, string, array, empty object exit 0 with no output |
| Config boundary | PASS | malformed config, unknown lane names, non-integer limits are ignored; global config overridden by project config; keywords merge |
| Project floor | PASS | raises `explain` to deep; never lowers; explicit lane request wins; safety wins over both |
| Plugin CLI shape | PASS | `--classify --json --runtime openclaw` carries lane, effort, targets, context; legacy `--classify` output unchanged |
| OpenCode plugin contract | PASS | plain Node: synthetic part appended, not re-classified, enforcement off by default, `reasoningEffort` set only when enabled, missing router fails open |
| OpenClaw plugin contract | PASS | plain Node: `prependContext` returned, override only with `enforce` and a lane model, `provider/model` split, missing router fails open |
| Hermes plugin contract | PASS | `register` binds `pre_llm_call`; context injected; empty message and missing router return `None` |
| Harness audit script | PASS | fixture project: ALIVE/LINKED/DEAD verdicts, archived skills excluded, subdirectory sessions counted, idle project flagged |
| Installer | PASS | five runtime homes, shared router, installed OpenCode plugin resolves it without env, skill trees copied whole, scaffold never overwrites, unknown skill/runtime and malformed settings abort before any write, idempotent, paths with spaces |
| Docs gate | PASS | ten break tests; the gate also runs on this repository and the scaffold copy must be byte-identical |
| Skill schemas | PASS | ten `SKILL.md` folders: frontmatter, `## Next` baton, no TODO, single-line `metadata` rule for OpenClaw |

## Live-runtime evidence (2026-09-07/08, one machine)

| Runtime | What ran | Result |
|---|---|---|
| OpenCode | `opencode run -m opencode-go/kimi-k2.7-code` with the plugin installed and `EFFORT_LANES_DEBUG` set; prompt asked the model to repeat any `[EFFORT LANES]` line it received | `chat.message` fired (lane=fast, explicit request), `chat.params` fired (effort=medium), the model answered **`LANE=FAST EFFORT=MEDIUM`** — the injected context reached the model |
| OpenCode | same with `EFFORT_LANES_ENFORCE=1` | `chat.params` set `reasoningEffort`; the provider accepted the call without error. Whether that provider honors the field is not measured here |
| OpenClaw | `openclaw plugins install --link ./openclaw`, `plugins info`, `plugins doctor` | Status `loaded`, "No plugin issues detected". A package-name/id mismatch warning was found and fixed (unscoped npm name must equal the manifest id) |
| OpenClaw | `openclaw agent --local --agent main -m "lane=fast reply OK"` | `before_model_resolve` fired with lane=fast; the turn then failed at the model (no provider credentials on this machine), so `before_prompt_build` was verified offline only |
| Hermes | plugin copied to `~/.hermes/plugins/effort-lanes`, `hermes plugins enable`, `hermes plugins doctor effort-lanes --ci` | "runtime discovery, manifest parsing, import, and registration passed; 1 hook(s)" |
| Hermes | shell hook `hooks.pre_llm_call` → router, `hermes hooks test pre_llm_call` | exit 0 in 0.106 s; Hermes parsed `{"context": "[EFFORT LANES] lane=DAILY …"}` as its wire shape |
| Codex | persisted threads with `-p effort-daily` / `-p effort-deep`; built-in `explorer` delegation | `gpt-5.6-terra/medium`, `gpt-5.6-sol/high`; `BUILTIN_EXPLORER_OK` (v0.1 evidence, unchanged) |

## Benchmark pilot (2026-09-08)

`bench/run.py`, `opencode-go/gpt-5.6-luna`, 15 tasks × 4 conditions, one repeat. Full table and interpretation in `bench/results/pilot-1.md`.

| Prediction | Verdict |
|---|---|
| P1 fast lane saves reasoning under enforce vs always-high | FAIL — router added reasoning tokens on this provider (46 → 153) |
| P2 critical pass rate does not drop under enforce | PASS — 5/5, matching always-high, 4% cheaper |
| P3 ≥85% of tasks routed to the labeled lane | FAIL at 10/15; keyword fix and precedence rule brought the offline check to 15/15 and 47 matrix cases pass |

## Failures kept as evidence

1. (v0.1) The first live large-task trial selected Critical and attempted a custom Codex agent that the running CLI reported unavailable; built-in fallback agents worked. Automatic hints now use built-in roles.
2. (v0.1) Non-object JSON could crash the original hook; duplicate malformed handlers could survive installation. Both have regression coverage.
3. (v0.3) The first `opencode run` against `opencode-go/deepseek-v4-flash` died with a region opt-in error before the model answered — the hooks had already fired, which is how the plugin's fail-open path was first observed for real.
4. (v0.3) A foreground `opencode run` produced no output for two minutes; the same command detached with `nohup` completed in 8 s. Cause not identified; recorded so the next person does not chase it.
5. (v0.3) Loading the router with `importlib.util.spec_from_file_location` on Python 3.14 raised inside `@dataclass` until the module was placed in `sys.modules` first. The Hermes loader now does this; the unit tests already did.
6. (v0.3) The docs gate, on its first run against this repository, failed on a real stray file in `docs/`. It was moved, not whitelisted.
7. (bench) The first pilot was stopped at 4/60 because this machine's personal global config (default lane deep) leaked into the runs. The router gained `EFFORT_LANES_CONFIG` so the benchmark isolates itself; the 4 contaminated rows were discarded.
8. (bench) Prediction P1 failed: on `gpt-5.6-luna` the fast lane's `reasoningEffort=medium` and the injected guidance both cost more reasoning than the provider default. Recorded as a hypothesis for the next single-axis run, not patched on the same data.

## What this does not prove

- That the lane→effort mapping is optimal for any workload. Defaults are starting points.
- That a hook changes the active parent model in Codex or Claude Code; it does not.
- That OpenClaw's `before_prompt_build` injects in a live turn on this machine; no model credentials were available. The hook type and return shape were verified from the SDK typings and in plain Node.
- That the Claude Code marketplace install path works end to end; the manifests follow the documented schema but were not exercised through `/plugin install`.
- That any provider changes its reasoning when OpenCode passes `reasoningEffort`; only that the call is accepted.

Future measurements should record task fixture, model version, effort, wall time, token use, pass/fail rubric, and repeated trials.
